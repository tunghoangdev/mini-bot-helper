from __future__ import annotations

import requests

from .http import request_with_retry

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
SYSTEM_PROMPT = (
    "You are OptiBot, the customer-support bot for OptiSigns.com. "
    "• Tone: helpful, factual, concise. "
    "• Only answer using the uploaded docs. "
    "• Max 5 bullet points; else link to the doc. "
    '• Cite up to 3 "Article URL:" lines per reply.'
)


class GeminiAssistant:
    def __init__(self, settings):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for the assistant")
        self.settings = settings
        self.session = requests.Session()

    def answer(self, question: str, store_name: str) -> str:
        response = request_with_retry(
            lambda: self.session.post(
                API_URL,
                headers={
                    "x-goog-api-key": self.settings.gemini_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.gemini_model,
                    "system_instruction": SYSTEM_PROMPT,
                    "input": question,
                    "tools": [
                        {
                            "type": "file_search",
                            "file_search_store_names": [store_name],
                        }
                    ],
                    "store": False,
                },
                timeout=self.settings.request_timeout,
            ),
            retries=self.settings.request_retries,
            timeout=self.settings.request_timeout,
            operation="Gemini assistant interaction",
        )
        payload = response.json()
        if payload.get("status") in {"failed", "cancelled", "incomplete"}:
            raise RuntimeError(f"Gemini assistant did not complete: {payload}")
        text = _output_text(payload)
        if not text:
            raise RuntimeError("Gemini assistant returned no text output")
        return text


def _output_text(payload: dict) -> str:
    parts: list[str] = []
    for step in payload.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for block in step.get("content", []):
            if block.get("type") == "text" and block.get("text"):
                parts.append(block["text"])
    if parts:
        return "\n".join(parts).strip()

    output = payload.get("output", [])
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, list):
        return "\n".join(
            block.get("text", "")
            for block in output
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    return ""
