from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.assistant import GeminiAssistant
from app.config import load_settings
from app.state import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask OptiBot about OptiSigns support docs")
    parser.add_argument(
        "question",
        nargs="*",
        default=["How do I add a YouTube video?"],
        help="question to ask; defaults to the take-home sanity-check question",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    settings = load_settings()
    state = load_state(Path("data/state.json"))
    store_name = settings.gemini_store or state.get("gemini_store")
    if not store_name:
        raise SystemExit(
            "No Gemini File Search Store configured. Run `python main.py` after setting "
            "GEMINI_API_KEY first."
        )
    answer = GeminiAssistant(settings).answer(" ".join(args.question), store_name)
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
