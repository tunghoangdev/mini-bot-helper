from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.config import load_settings
from app.scraper import scrape_articles
from app.state import load_state
from app.sync import sync_articles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync OptiSigns support articles to Gemini File Search")
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="scrape and update local Markdown/state without calling Gemini",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    settings = load_settings()
    articles = scrape_articles(settings)
    state = load_state(Path("data/state.json"))
    result = sync_articles(settings, articles, state, upload=not args.no_upload)
    summary = {
        "scraped": len(articles),
        "added": len(result["added"]),
        "updated": len(result["updated"]),
        "skipped": len(result["skipped"]),
        "uploaded": not args.no_upload,
    }
    summary_path = Path("data/last-run.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    logging.info("Run summary: %s", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
