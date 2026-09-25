from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import quote

import requests

from .http import request_with_retry

LOGGER = logging.getLogger(__name__)
API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_ROOT = "https://generativelanguage.googleapis.com/upload/v1beta"


class GeminiFileSearch:
    def __init__(self, settings):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini upload")
        self.settings = settings
        self.api_key = settings.gemini_api_key
        self.session = requests.Session()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.settings.request_timeout)
        return request_with_retry(
            lambda: self.session.request(method, url, **kwargs),
            retries=self.settings.request_retries,
            timeout=self.settings.request_timeout,
            operation=f"Gemini {method} {url}",
        )

    def ensure_store(self, configured_store: str | None) -> str:
        if configured_store:
            response = self._request(
                "GET", f"{API_ROOT}/{configured_store}", params={"key": self.api_key}
            )
            return response.json()["name"]
        response = self._request(
            "POST",
            f"{API_ROOT}/fileSearchStores",
            params={"key": self.api_key},
            json={
                "displayName": self.settings.gemini_store_display_name,
                "embeddingModel": self.settings.gemini_embedding_model,
            },
        )
        store_name = response.json().get("name")
        if not store_name:
            raise RuntimeError("Gemini store creation returned no store name")
        LOGGER.warning(
            "Created Gemini File Search Store %s; persist it as GEMINI_FILE_SEARCH_STORE",
            store_name,
        )
        return store_name

    def delete_document(self, document_name: str | None) -> None:
        if not document_name:
            return
        response = self.session.delete(
            f"{API_ROOT}/{document_name}",
            params={"key": self.api_key, "force": "true"},
            timeout=self.settings.request_timeout,
        )
        if response.status_code not in {200, 204, 404}:
            response.raise_for_status()

    def upload(self, store_name: str, path: Path, source_url: str) -> str:
        data = path.read_bytes()
        start = self._request(
            "POST",
            f"{UPLOAD_ROOT}/{store_name}:uploadToFileSearchStore",
            params={"key": self.api_key},
            headers={
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(len(data)),
                "X-Goog-Upload-Header-Content-Type": "text/markdown",
                "Content-Type": "application/json",
            },
            json={
                "displayName": path.name,
                "mimeType": "text/markdown",
                "customMetadata": [{"key": "source_url", "stringValue": source_url}],
                "chunkingConfig": {
                    "whiteSpaceConfig": {
                        "maxTokensPerChunk": self.settings.chunk_max_tokens,
                        "maxOverlapTokens": self.settings.chunk_overlap_tokens,
                    }
                },
            },
        )
        upload_url = start.headers.get("X-Goog-Upload-URL") or start.headers.get(
            "x-goog-upload-url"
        )
        if not upload_url:
            raise RuntimeError("Gemini did not return a resumable upload URL")

        finalized = self._request(
            "POST",
            upload_url,
            headers={
                "Content-Length": str(len(data)),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize",
            },
            data=data,
        )
        operation = finalized.json()
        if operation.get("name") and not operation.get("done", False):
            operation = self._poll_operation(operation["name"])
        if operation.get("error"):
            raise RuntimeError(f"Gemini upload failed: {operation['error']}")
        document_name = _find_document_name(operation)
        if not document_name:
            raise RuntimeError("Gemini upload completed without a document name")
        return document_name

    def _poll_operation(self, operation_name: str) -> dict:
        deadline = time.monotonic() + self.settings.gemini_poll_timeout
        while time.monotonic() < deadline:
            time.sleep(self.settings.gemini_poll_seconds)
            response = self._request(
                "GET",
                f"{API_ROOT}/{operation_name}",
                params={"key": self.api_key},
            )
            operation = response.json()
            if operation.get("done"):
                return operation
        raise TimeoutError(f"Timed out waiting for Gemini operation {operation_name}")


def _find_document_name(value: object) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "document" and isinstance(child, dict) and child.get("name"):
                return str(child["name"])
            if key in {"documentName", "document_name"} and isinstance(child, str):
                return child
            found = _find_document_name(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_document_name(child)
            if found:
                return found
    return None
