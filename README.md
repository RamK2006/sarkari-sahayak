# Government Scheme Assistant

A voice-first, multilingual counselor for central government schemes and paperwork, built on Sarvam AI.

| Capability | Where | Sarvam service |
| --- | --- | --- |
| Voice call: hands-free loop with barge-in, or opt-in text chat | `/talk` | Saaras (speech-to-text), Bulbul (text-to-speech), Sarvam 105B |
| Scheme discovery by retrieval over official records, with explained eligibility | `/talk`, `/khoj`, `/schemes` | Sarvam 105B tool calling |
| KYC document reading, validity review, missing-document check | `/vault`, scheme pages | Sarvam Vision (Doc AI) + Sarvam 105B |
| Step-by-step form guide with spoken fields and voice confirmation | `/guide` | Sarvam 105B, Bulbul, Saaras |
| 22 languages plus English across UI, replies and scheme text | everywhere | Sarvam Translate |
| Quick check in five short steps | `/check` | none (deterministic engine) |

## How it works

- **Counselor, not a form.** The citizen says anything. The model calls tools: `search_schemes` (BM25 retrieval over
  catalog records, `backend/services/rag.py`), `check_eligibility`, `record_profile`. Personal details are asked only
  when an answer needs them. Eligibility is decided by the deterministic engine
  (`backend/services/eligibility.py`), never by the model: eligible, potentially eligible, more information needed,
  not assessed (search-only record), not eligible, each with per-criterion reasons.
- **Documents.** Sarvam Vision reads the upload, the model extracts type, name, dates and the last four ID characters
  (never the full number), and date arithmetic reviews validity (thresholds: `EXPIRING_SOON_DAYS`, `UPCOMING_DAYS`).
  Scheme document requirements are matched to the vault through `backend/data/doc_types.json`. The vault keeps the
  citizen's note on where each original is kept and what it is used for, and drives renewal reminders (in-app and
  browser notifications). Everything is stored in the browser; the server is stateless.
- **Form guide.** The model drafts steps in the citizen's language. A field value is kept only if it appears verbatim in
  the citizen's own document data, so nothing is invented. Scheme guides are grounded in the scheme record; other goals
  are labelled as general AI guidance.
- **Avatar.** `frontend/src/lib/avatars.ts` holds one look per language (skin tone, attire, bindi, turban or cap,
  greeting gesture). Mood and gesture come from the assistant's reply; listening, waiting and speaking come from real
  activity; the mouth follows the audio signal. Change a look by editing that table.
- **Languages.** Shipped UI files in `frontend/src/locales/`; any missing string is translated by Sarvam on demand and
  cached in the browser. Sarvam speaks 11 of the languages (text-to-speech); the other 12 get text replies and spoken
  input.
- **Theme.** Light and dark, saved per browser.

## Run

```bash
cp .env.example .env                        # set SARVAM_API_KEY
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev                                 # http://localhost:3000, proxies /api to BACKEND_URL
```

Or `docker compose up --build`.

One-time content generation (needs the Sarvam key; takes a while, safe to re-run, keeps existing strings):

```bash
python -m backend.scripts.translate_locales        # UI strings for all languages
python -m backend.scripts.prewarm_translations     # scheme text for all languages
```

## Scaling the catalog to thousands of schemes

`python -m backend.scripts.ingest_schemes export.json` merges records from a registry export into
`backend/data/schemes_extra.json`. They become searchable and filterable by state immediately. Records without typed
`criteria` are shown as "not assessed" and are never reported as eligible; add criteria to make them checkable. The
shipped catalog has 15 central schemes, compiled from published guidelines and not re-verified against live sources
(`last_verified` is empty), so review amounts and limits before launch.

## Deploy

Backend: `docker build -f backend/Dockerfile .` (env `SARVAM_API_KEY`, `CORS_ORIGINS`). Frontend: Vercel with root
directory `frontend`, or `frontend/Dockerfile` (env `BACKEND_URL`). The browser only calls the frontend's own `/api`,
which proxies to the backend, so the key never reaches the client. Probes: `/healthz`, `/readyz`. The rate limiter is
per process.

## Tests

```bash
python -m pytest backend/tests
cd frontend && npm run typecheck && npm run audit:locales
```

## Not included yet

Accounts and cross-device sync (next phase), AR/3D avatar, live streaming of audio in both directions (the call is
turn-based with interruption).
