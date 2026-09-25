from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.config import load_settings
from app.gemini import GeminiFileSearch
from app.markdown import estimated_chunk_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Markdown files to Gemini File Search")
    parser.add_argument("path", type=Path, help="a Markdown file or directory of Markdown files")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    settings = load_settings()
    client = GeminiFileSearch(settings)
    store = client.ensure_store(settings.gemini_store)
    files = [args.path] if args.path.is_file() else sorted(args.path.glob("*.md"))
    if not files:
        raise SystemExit(f"No Markdown files found at {args.path}")

    total_chunks = 0
    for path in files:
        content = path.read_text(encoding="utf-8")
        source_url = next(
            (line.removeprefix("Article URL:").strip() for line in content.splitlines()
             if line.startswith("Article URL:")),
            "",
        )
        document = client.upload(store, path, source_url)
        chunks = estimated_chunk_count(
            content, settings.chunk_max_tokens, settings.chunk_overlap_tokens
        )
        total_chunks += chunks
        logging.info("Uploaded %s document=%s estimated_chunks=%s", path.name, document, chunks)
    logging.info("Gemini processed files=%s chunks_estimated=%s", len(files), total_chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
