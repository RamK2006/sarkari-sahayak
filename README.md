# Government Scheme Assistant

A multilingual assistant that helps citizens find central government schemes they may be eligible for. It asks a few
questions (typed, tapped or spoken), checks the answers against each scheme's published criteria, and explains every
result in the citizen's own language.

Built on Sarvam AI: chat and tool calling (`sarvam-105b-conversations`), translation (`sarvam-translate:v1`),
speech-to-text (`saaras:v4`) and text-to-speech (`bulbul:v4-flash`, `bulbul:v3` for Odia and Malayalam).

## How it works

- **No recommendation without information.** Results are withheld until the core questions (age, gender, area,
  occupation, household income) are answered or skipped. Further questions are chosen adaptively: only fields that
  schemes still in contention are waiting on.
- **Deterministic eligibility.** `backend/services/eligibility.py` evaluates typed criteria from the catalog and returns
  one of four statuses (eligible, potentially eligible, more information needed, not eligible) with a per-criterion
  reason. There are no scores or percentages, and the language model never decides eligibility.
- **The model understands, it does not decide.** Sarvam chat extracts profile facts from free text or transcribed
  speech via tool calling, and answers questions about schemes using only catalog records returned by a tool.
- **One language everywhere.** UI text comes from `frontend/src/locales/<lang>.json`; criteria and reasons are returned by
  the API as codes and rendered from those files; scheme text is translated by Sarvam and cached; model replies are
  generated in the selected language and translated when the language changes mid-conversation.
- **Stateless backend.** The profile and conversation live in the browser. Nothing is stored server-side.
- **Real voice.** Recording goes to Sarvam STT; replies are synthesised by Sarvam TTS. The avatar's mouth follows the
  actual audio signal, and its other states map to recording, a pending request and playback.

## Run locally

```bash
cp .env.example .env            # set SARVAM_API_KEY
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev                     # http://localhost:3000 (proxies /api to BACKEND_URL, default http://localhost:8000)
```

Or run both with Docker: `docker compose up --build`.

## Deploy

| Part     | How                                                                                                   |
| -------- | ----------------------------------------------------------------------------------------------------- |
| Backend  | `docker build -f backend/Dockerfile .` on any container host. Env: `SARVAM_API_KEY`, `CORS_ORIGINS`.   |
| Frontend | Vercel (root directory `frontend`) or `frontend/Dockerfile`. Env: `BACKEND_URL` = the backend's URL.  |

The browser only talks to the frontend's own `/api/*`, which proxies to `BACKEND_URL`, so the API key never reaches the
client and no CORS setup is needed between them. `GET /healthz` is the liveness probe; `GET /readyz` reports whether the
Sarvam key is configured. The in-memory rate limiter is per process; put a shared limiter in front when running several
replicas.

## Content and localization

- **Catalog:** `backend/data/schemes.json` (15 central schemes). The integration boundary is `SchemeSource` in
  `backend/services/catalog.py`; replace `JsonSchemeSource` with a feed from an authoritative registry to cover more
  schemes. Each record carries its official `source_url`, and `last_verified` is `null` until a maintainer verifies the
  record. The catalog was compiled from published scheme guidelines and has **not** been re-verified against the live
  sources, so review amounts, limits and criteria before production use.
- **UI strings:** edit `frontend/src/locales/en.json`, then regenerate the other languages with Sarvam translation:
  `python -m backend.scripts.translate_locales` (keeps existing translations; `--force` redoes all). Check
  completeness with `npm run audit:locales`. Machine translations should be reviewed by native speakers.
- **Scheme text:** `python -m backend.scripts.prewarm_translations` translates the catalog for every language and stores
  it in `backend/data/translations/`.

## Tests

```bash
python -m pytest backend/tests        # eligibility engine, intake flow, API contract (no network)
cd frontend && npm run typecheck && npm run audit:locales
```

## Scope

Not included yet: accounts and saved history (next phase), state-level schemes, and document upload.
