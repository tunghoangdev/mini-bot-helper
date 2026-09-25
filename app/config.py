from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    support_api_url: str
    gemini_api_key: str | None
    gemini_store: str | None
    gemini_store_display_name: str
    gemini_embedding_model: str
    gemini_model: str
    min_articles: int
    max_articles: int
    request_timeout: int
    request_retries: int
    chunk_max_tokens: int
    chunk_overlap_tokens: int
    gemini_poll_seconds: int
    gemini_poll_timeout: int


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        support_api_url=os.getenv(
            "SUPPORT_API_URL",
            "https://support.optisigns.com/api/v2/help_center/en-us/articles.json",
        ),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_store=os.getenv("GEMINI_FILE_SEARCH_STORE") or None,
        gemini_store_display_name=os.getenv(
            "GEMINI_STORE_DISPLAY_NAME", "optisigns-support"
        ),
        gemini_embedding_model=os.getenv(
            "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-2"
        ),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        min_articles=_int_env("MIN_ARTICLES", 30),
        max_articles=_int_env("MAX_ARTICLES", 30),
        request_timeout=_int_env("REQUEST_TIMEOUT_SECONDS", 30),
        request_retries=_int_env("REQUEST_RETRIES", 3),
        chunk_max_tokens=_int_env("CHUNK_MAX_TOKENS", 400),
        chunk_overlap_tokens=_int_env("CHUNK_OVERLAP_TOKENS", 40),
        gemini_poll_seconds=_int_env("GEMINI_POLL_SECONDS", 5),
        gemini_poll_timeout=_int_env("GEMINI_POLL_TIMEOUT_SECONDS", 600),
    )
