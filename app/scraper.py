from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin

import requests

from .http import request_with_retry
from .markdown import article_markdown, content_hash

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Article:
    article_id: int
    title: str
    url: str
    markdown: str
    content_hash: str
    filename: str


def _filename(article_id: int, title: str) -> str:
    slug = "-".join("".join(char.lower() if char.isalnum() else " " for char in title).split())
    return f"{slug[:80] or 'article'}-{article_id}.md"


def _canonical_url(url: str) -> str:
    without_fragment = urldefrag(url.strip())[0]
    return without_fragment.rstrip("/") or without_fragment


def scrape_articles(settings) -> list[Article]:
    session = requests.Session()
    page_url: str | None = settings.support_api_url
    found: list[Article] = []
    skipped = 0
    duplicates = 0
    seen_ids: set[int] = set()
    seen_urls: set[str] = set()

    while page_url and len(found) < settings.max_articles:
        response = request_with_retry(
            lambda: session.get(page_url, timeout=settings.request_timeout),
            retries=settings.request_retries,
            timeout=settings.request_timeout,
            operation=f"scrape {page_url}",
        )
        payload = response.json()
        for raw in payload.get("articles", []):
            if len(found) >= settings.max_articles:
                break
            raw_id = raw.get("id")
            title = (raw.get("title") or "").strip()
            url = (raw.get("html_url") or raw.get("url") or "").strip()
            html = raw.get("body") or ""
            if not raw_id or not title or not url or not html:
                skipped += 1
                continue
            url = _canonical_url(urljoin(settings.support_api_url, url))
            try:
                article_id = int(raw_id)
            except (TypeError, ValueError):
                skipped += 1
                continue
            if article_id in seen_ids or url in seen_urls:
                duplicates += 1
                continue
            markdown = article_markdown(title, url, html)
            found.append(
                Article(
                    article_id=article_id,
                    title=title,
                    url=url,
                    markdown=markdown,
                    content_hash=content_hash(markdown),
                    filename=_filename(article_id, title),
                )
            )
            seen_ids.add(article_id)
            seen_urls.add(url)
        page_url = payload.get("next_page")

    if skipped:
        LOGGER.warning("Skipped %s incomplete article records", skipped)
    if duplicates:
        LOGGER.info("Skipped %s duplicate article records", duplicates)
    if len(found) < settings.min_articles:
        raise RuntimeError(
            f"Only scraped {len(found)} valid articles; expected at least "
            f"{settings.min_articles}."
        )
    LOGGER.info("Scraped %s valid articles", len(found))
    return found
