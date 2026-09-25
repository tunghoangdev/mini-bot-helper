from __future__ import annotations

import logging
from pathlib import Path

from .gemini import GeminiFileSearch
from .markdown import estimated_chunk_count
from .scraper import Article
from .state import save_state

LOGGER = logging.getLogger(__name__)


def sync_articles(settings, articles: list[Article], state: dict, *, upload: bool) -> dict:
    articles_dir = Path("data/articles")
    articles_dir.mkdir(parents=True, exist_ok=True)
    previous = state.setdefault("articles", {})
    current: dict = {}
    previous_keys: dict[str, str] = {}
    added: list[Article] = []
    updated: list[Article] = []
    skipped: list[Article] = []

    for article in articles:
        old_key = article.url
        old = previous.get(article.url)
        if not old:
            for key, record in previous.items():
                if record.get("article_id") == article.article_id:
                    old_key, old = key, record
                    break
        previous_keys[article.url] = old_key
        path = articles_dir / article.filename
        path.write_text(article.markdown, encoding="utf-8")
        current[article.url] = {
            "article_id": article.article_id,
            "title": article.title,
            "filename": article.filename,
            "content_hash": article.content_hash,
            "gemini_document": old.get("gemini_document") if old else None,
        }
        if not old or (upload and not old.get("gemini_document")):
            added.append(article)
        elif old.get("content_hash") == article.content_hash:
            skipped.append(article)
        else:
            updated.append(article)

    LOGGER.info("Delta: added=%s updated=%s skipped=%s", len(added), len(updated), len(skipped))
    merged = dict(previous)
    for article in articles:
        old_key = previous_keys[article.url]
        if old_key != article.url:
            merged.pop(old_key, None)
    merged.update(current)
    if not upload or not (added or updated):
        state["articles"] = merged
        save_state(Path("data/state.json"), state)
        if not upload:
            LOGGER.info("Gemini upload disabled (--no-upload)")
        LOGGER.info(
            "Sync complete: added=%s updated=%s skipped=%s",
            len(added),
            len(updated),
            len(skipped),
        )
        return {"added": added, "updated": updated, "skipped": skipped}

    client = GeminiFileSearch(settings)
    store_name = client.ensure_store(settings.gemini_store or state.get("gemini_store"))
    state["gemini_store"] = store_name
    checkpoint = dict(previous)
    save_state(Path("data/state.json"), state)
    updated_urls = {article.url for article in updated}
    for article in [*added, *updated]:
        item = dict(current[article.url])
        old_key = previous_keys[article.url]
        if article.url in updated_urls:
            client.delete_document(previous[old_key].get("gemini_document"))
        document_name = client.upload(store_name, articles_dir / article.filename, article.url)
        item["gemini_document"] = document_name
        if old_key != article.url:
            checkpoint.pop(old_key, None)
        checkpoint[article.url] = item
        state["articles"] = checkpoint
        save_state(Path("data/state.json"), state)
        LOGGER.info(
            "Uploaded %s (%s estimated chunks)",
            article.filename,
            estimated_chunk_count(
                article.markdown, settings.chunk_max_tokens, settings.chunk_overlap_tokens
            ),
        )

    state["articles"] = checkpoint
    save_state(Path("data/state.json"), state)
    LOGGER.info(
        "Gemini processed files=%s chunks_estimated=%s",
        len(added) + len(updated),
        sum(
            estimated_chunk_count(
                article.markdown, settings.chunk_max_tokens, settings.chunk_overlap_tokens
            )
            for article in [*added, *updated]
        ),
    )
    LOGGER.info(
        "Sync complete: added=%s updated=%s skipped=%s",
        len(added),
        len(updated),
        len(skipped),
    )
    return {"added": added, "updated": updated, "skipped": skipped}
