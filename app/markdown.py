from __future__ import annotations

import hashlib
import re

from bs4 import BeautifulSoup
from markdownify import markdownify


REMOVE_SELECTORS = (
    "nav",
    "footer",
    "aside",
    "script",
    "style",
    "noscript",
    "form",
    ".breadcrumbs",
    ".article-footer",
    ".related-articles",
    ".lt-related-articles",
    ".advertisement",
    ".ads",
    '[role="navigation"]',
    '[aria-label="advertisement"]',
)


def clean_html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    text = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def article_markdown(title: str, url: str, html: str) -> str:
    body = clean_html_to_markdown(html)
    return f"# {title.strip()}\n\nArticle URL: {url}\n\n{body}\n"


def content_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def estimated_chunk_count(markdown: str, max_tokens: int, overlap: int) -> int:
    if max_tokens <= overlap:
        raise ValueError("CHUNK_MAX_TOKENS must be greater than CHUNK_OVERLAP_TOKENS")
    token_count = len(markdown.split())
    if not token_count:
        return 0
    step = max_tokens - overlap
    return max(1, (max(0, token_count - overlap) + step - 1) // step)
