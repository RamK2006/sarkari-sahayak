# Government Scheme Assistant

A voice-first, multilingual counselor that helps Indian citizens find central government schemes they may be eligible for, understand their documents, and complete forms, in 22 languages plus English. Built on Sarvam AI.

For a plain-language overview (the problem, what the assistant does for a citizen, what is in progress), read [GUIDE_TO_USE.md](GUIDE_TO_USE.md).

## What is in the product

| Page | What it does | Sarvam services used |
| --- | --- | --- |
| `/` | Home: choose a language, start a voice call or text chat | Translate |
| `/talk` | Counselor conversation. Voice call (hands-free, interruptible) or opt-in text chat | Saaras (speech to text), Bulbul (text to speech), Sarvam 105B (chat, tool calling), Translate |
| `/khoj` | Scheme finder: keyword search plus filters for state, age, gender, income, category, land | Translate |
| `/check` | Quick check: five short steps, then personalised results | none (rule engine) |
| `/schemes`, `/schemes/[id]` | Results grouped by status, and a detail page with reasons, required documents (matched to your vault), apply steps | Translate |
| `/vault` | Upload KYC documents; read, validity review, renewal reminders, "where I keep it" notes | Sarvam Vision (Doc AI), Sarvam 105B |
| `/guide` | Step-by-step form guide, each field spoken, voice confirmation ("done", "repeat", "back") | Sarvam 105B, Bulbul, Saaras |
| `/help`, `/privacy` | Short FAQ; what is stored where, and a button to delete all local data | Translate |

## How it works

- **Counselor, not a questionnaire.** The citizen can say anything. The model calls tools: `search_schemes`
  (BM25 retrieval over official scheme records, `backend/services/rag.py`), `check_eligibility` and
  `record_profile`. Personal details are asked only when an answer needs them.
- **Eligibility is deterministic.** `backend/services/eligibility.py` evaluates typed criteria per scheme and returns
  one of: eligible, potentially eligible, more information needed, not assessed (search-only record), not eligible,
  each with a reason per criterion. There are no scores or percentages, and the model never decides eligibility.
- **Documents.** Sarvam Vision reads the upload; the model extracts document type, name, dates and only the last four
  characters of the ID number; date arithmetic reviews validity (`EXPIRING_SOON_DAYS`, `UPCOMING_DAYS`). Scheme
  document requirements are matched against the vault through `backend/data/doc_types.json`. The citizen can note where
  each original is kept and what it is used for, and search by that. Renewals appear as reminders and, if permitted,
  browser notifications. Nothing is stored on the server.
- **Form guide.** The model drafts steps in the citizen's language. A field value is kept only if it appears verbatim in
  the citizen's own document data, so nothing is invented. Guides for a scheme are grounded in its record; guides for
  other goals (for example opening a bank account) are labelled as general AI guidance.
- **Avatar.** One illustrated look per language in `frontend/src/lib/avatars.ts` (skin tone, attire, bindi, turban or
  cap, greeting gesture). The assistant's reply selects mood and gesture; listening, waiting and speaking come from real
  activity, and the mouth follows the audio signal. Change a look by editing that table only.
- **One language everywhere.** UI text comes from `frontend/src/locales/<lang>.json`. Any string missing from a language
  file is translated by Sarvam on demand (retried on rate limits) and cached in the browser. Criteria and reasons are
  returned by the API as codes and rendered from those files. Scheme text is translated by Sarvam and cached on disk.
  Earlier assistant replies are translated when the language changes mid-conversation.
- **Translation details.** Sarvam-Translate (all 22 languages) is used with an explicit source language. When the source
  is unknown, the backend detects it first with Sarvam language identification. Strings are sent in batches, at most 3
  calls at once, with retry and backoff on rate limits. A partial failure returns what succeeded.
- **Speech coverage.** Sarvam can speak 11 languages (English, Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati,
  Kannada, Malayalam, Punjabi, Odia). The other 12 get text replies and spoken input; the app says so.
- **Stateless backend.** The profile, conversation and vault live in the browser. Rate limiting is per process.
- **Theme.** Light and dark, saved per browser.

## Run locally

```bash
cp .env.example .env                        # set SARVAM_API_KEY
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn backend.main:app --port 8000
```

On Windows run uvicorn as `python -m uvicorn`; the bare `uvicorn` command is usually not on PATH. Avoid `--reload` there
unless you need it, because a stale process can keep port 8000.

```bash
cd frontend
npm install
npm run dev                                 # http://localhost:3000, proxies /api to BACKEND_URL
```

Or run both with `docker compose up --build`.

One-time content generation (needs the Sarvam key, takes a while, safe to re-run, keeps existing strings):

```bash
python -m backend.scripts.translate_locales        # UI strings for all languages
python -m backend.scripts.prewarm_translations     # scheme text for all languages
```

## Deploy for free (Vercel + Render)

The browser only calls the frontend's own `/api/*`, which proxies to the backend, so the API key never reaches the
client and no CORS setup is needed between them.

**1. Push to GitHub.** `.env` is git-ignored.

**2. Backend on Render** (New, Web Service, pick the repo):

| Field | Docker (simplest) | Python, no Docker |
| --- | --- | --- |
| Root Directory | empty (repo root) | empty (repo root) |
| Dockerfile Path | `backend/Dockerfile` | not used |
| Build Command | empty | `pip install -r backend/requirements.txt` |
| Start Command | empty | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/healthz` | `/healthz` |
| Instance Type | Free | Free |

Environment: `SARVAM_API_KEY`, `WEB_CONCURRENCY=1` (512 MB memory), `CORS_ORIGINS` (your Vercel URL; edit it under the
service's Environment tab). Python option also needs `PYTHON_VERSION=3.12.3`. Check `https://<service>.onrender.com/readyz`.

**3. Frontend on Vercel** (Add New, Project, same repo): Root Directory `frontend`, everything else default.
Environment: `BACKEND_URL=https://<service>.onrender.com` (no trailing slash).

Free-tier limits to know:

- Render's free service sleeps after 15 minutes idle; the next request takes 30 to 60 seconds. A free uptime monitor
  calling `/healthz` every 5 minutes keeps it awake.
- Vercel's free plan limits request bodies to about 4.5 MB, so larger document uploads fail even though the page says 8 MB.
- Render's free disk resets on each deploy. Run both generation commands above locally and commit the output so
  translations ship with the code.

## Scaling the catalog to thousands of schemes

`python -m backend.scripts.ingest_schemes export.json` merges records from a registry export into
`backend/data/schemes_extra.json`. They become searchable and state-filterable immediately. Records without typed
`criteria` show as "not assessed" and are never reported as eligible; add criteria to make them checkable. The shipped
catalog has 15 central schemes compiled from published guidelines. They have not been re-verified against live sources
(`last_verified` is empty), so review amounts and limits before launch. The integration boundary is `SchemeSource` in
`backend/services/catalog.py`.

## Tests

```bash
python -m pytest backend/tests                      # engine, intake, retrieval, documents, API contract (no network)
cd frontend && npm run typecheck && npm run audit:locales
```

## Status

**Done:** everything in the table above; backend tests pass (26) and the frontend typechecks and builds. Translation
for all 22 languages was verified live against Sarvam after the batching and source-detection fix.

**Not yet verified in a browser after the latest rebuild:** the hands-free voice loop and interruption, the avatar's
expressions and gestures, document upload through Sarvam Vision, and the form guide's voice confirmation.

**In progress:**

- Generating interface files for the 12 newer languages and finishing Odia and the few missing strings in Tamil,
  Malayalam and Punjabi (until then the page translates them live on first use).
- Reviewing machine translations with native speakers.
- Verifying the scheme catalog against official sources.

**Upcoming:**

- Sign-in (the next phase), saved history and sync across devices.
- Importing a registry export to cover thousands of schemes, including state schemes.
- Scheme-specific deadlines for reminders (today reminders come from document expiry dates).
- A lighter, more expressive avatar, and true two-way streaming audio (today the call is turn-based with interruption).
