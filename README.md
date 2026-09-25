# OptiSigns support → Gemini File Search

This job scrapes the public Zendesk Help Center API, converts at least 30 valid articles to clean Markdown, and syncs only added/changed files to a Gemini File Search Store. It uses Google AI Studio/Gemini API; no API key is stored in the repository.

## Setup and local run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.sample .env
# put GEMINI_API_KEY in .env locally
python main.py
```

Use `python main.py --no-upload` for a local scrape smoke test. Markdown is written to `data/articles/`; hashes and Gemini document names are stored in `data/state.json`. Keep that state directory persistent for a daily job. On the first upload, the script creates a File Search Store if `GEMINI_FILE_SEARCH_STORE` is empty; copy the logged store name into `.env` afterward. Never commit `.env`, `data/state.json`, or an API key.

For a direct upload outside the delta sync, use `python upload.py data/articles/<file>.md` or `python upload.py data/articles/`. After a successful upload, test the required assistant question with `python assistant.py "How do I add a YouTube video?"`. The assistant sends the brief's exact system prompt and uses Gemini File Search citations.

Environment variables are documented in `.env.sample`: Gemini key/store/model (default `gemini-2.5-flash` for the free-tier-oriented setup), support API URL, `MAX_ARTICLES` (default 30), request retry/timeout, minimum article count, and chunk settings. The scraper stops after the limit and deduplicates by stable Zendesk article ID plus canonical URL. The public Zendesk API is used, so no support-site credential is needed.

## Docker

```bash
docker build -t optisigns-sync .
docker run --rm --env-file .env -v "${PWD}/data:/app/data" optisigns-sync
```

The container runs one sync and exits with status 0 on success. A ready-to-run GitHub Actions workflow is in `.github/workflows/daily-sync.yml`; it runs daily at 02:17 UTC, restores/persists `data/state.json` through the Actions cache, captures stdout in `data/last-run.log`, and uploads a `optisigns-sync-last-run` artifact containing the log, summary, and state. Add `GEMINI_API_KEY` and `GEMINI_FILE_SEARCH_STORE` as repository secrets after pushing the repository. Cloud Run Jobs, ECS scheduled tasks, or cron are also valid alternatives, but must persist `data/state.json`.

## Chunking and API note

Each Markdown article remains one source document. Gemini File Search performs server-side whitespace chunking with a 400-token maximum and 40-token overlap, while the job logs an estimated chunk count. Headings and the `Article URL:` line remain in source text, relative links are preserved, and navigation/ads/scripts are removed. Updated articles delete the previous Gemini document and upload the replacement; unchanged articles are skipped. File Search is the practical Gemini knowledge-base equivalent; it is not a self-managed vector database, and Google’s current API/plan pricing and limits still apply.

## Evidence

- [AI Studio grounded answer](evidence/ai-studio-grounded-answer.png)
- [Initial upload](evidence/daily-job-initial-upload.png)
- [No-change daily run](evidence/daily-job-no-change.png)

Add a real screenshot of `python assistant.py "How do I add a YouTube video?"` showing cited `Article URL:` lines and link the GitHub Actions run or `optisigns-sync-last-run` artifact here after deployment. Do not invent either artifact. You still need to create the local Google AI Studio key, set repository secrets, verify the File Search Store, and push/enable the daily workflow yourself.
