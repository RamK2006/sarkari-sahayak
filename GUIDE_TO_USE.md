# Government Scheme Assistant: summary and guide

## The problem

Many citizens miss benefits they are entitled to. Official portals are long and written in formal language. People do
not know which of the thousands of schemes apply to them, which documents to bring, whether a document is still valid,
or how to fill in the form. Many are more comfortable speaking than typing, and in a language other than English or
Hindi. Questionnaires that ask for personal details up front put people off, and results that say "90% match" without
explaining why cannot be trusted.

## What we made

A counselor that talks with the citizen in their own language, finds schemes from official records, explains why a
scheme does or does not apply, reads and checks their documents, and walks them through the form step by step.

### What the assistant does for a citizen

| The citizen says or does | What the assistant does |
| --- | --- |
| "Which schemes can a farmer get?" | Searches the official scheme records and answers only from what it finds, with a link to the source |
| "I have a BPL card and a daughter" | Notes those facts, then explains which schemes fit and which conditions are still unknown |
| "Am I eligible for this scheme?" | Runs fixed rules (not the AI's opinion) and shows each condition as met, not met, unknown, or needing an official check |
| "How do I get an Aadhaar card?" or "I want to open a bank account" | Gives general step-by-step guidance, says it is general advice to confirm with the official office, and offers a form guide |
| Uploads an Aadhaar, licence or certificate | Reads it, says who it was issued to and until when it is valid, warns if renewal is due, and asks where the original is kept so it can be found later |
| Opens a scheme | Shows which required documents are already in their vault and which are missing or expired |
| "Guide me through the form" | Goes field by field, speaks each one aloud, fills values from their own documents when available, and waits for "done", "repeat" or "back" |
| Switches language mid-conversation | The whole page, earlier replies and scheme details change to the new language |

### Ways to use it

- **Talk (`/talk`):** press Start call and speak normally. The assistant answers aloud, then listens again. Speak over it
  to interrupt. Switch to Text chat if you cannot hear or prefer typing.
- **Scheme finder (`/khoj`):** search and narrow by state, age, gender, income, category and land.
- **Quick check (`/check`):** five short steps, then a list of schemes grouped by how well you fit.
- **My documents (`/vault`):** upload, review validity, set renewal reminders, note where each original is kept.
- **Form guide (`/guide`):** from a scheme page, or by asking the assistant.
- **Help and Privacy (`/help`, `/privacy`):** short answers, and a button that deletes everything stored in the browser.

### What makes it trustworthy

- Eligibility comes from fixed rules over scheme records, never from the AI's guess. No percentages.
- Every scheme shows its official source link, and the app reminds the user to confirm on the official website.
- The assistant never invents scheme names, amounts, links or form values. Form values are copied only from the user's
  own documents.
- Your data stays in your browser. Messages, recordings and documents are sent only to process a request and are not
  stored on the server. Only the last four characters of an ID number are kept from a document.
- Guidance that is not tied to a scheme is labelled as general AI guidance.

### Languages and the avatar

- Interface, replies and scheme details are available in 22 Indian languages plus English.
- Spoken replies are available in 11 of them (English, Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada,
  Malayalam, Punjabi, Odia). The other languages get text replies and can still be spoken to; the app says so.
- The on-screen assistant changes with the language: attire, bindi, turban or cap, and greeting gesture (palms together,
  or a hand to the forehead). It tilts its head while listening, raises its brows, looks serious for deadlines and
  empathetic for hardship, and its mouth follows the real audio. It has no name or invented backstory.
- Light and dark themes.

## How to run it

```bash
cp .env.example .env                  # add your SARVAM_API_KEY
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn backend.main:app --port 8000
```
In a second terminal:
```bash
cd frontend
npm install
npm run dev                           # open http://localhost:3000
```
On Windows use `python -m uvicorn` (the plain `uvicorn` command is usually not on PATH). To deploy for free, follow
"Deploy for free" in [README.md](README.md).

## Honest limits today

- The catalog has 15 central schemes. It was compiled from published guidelines and has not been re-checked against live
  sources; review amounts and limits before launch.
- State-level schemes are not included yet.
- Machine translations should be reviewed by native speakers.
- Spoken replies exist for 11 of the 23 languages.
- Reminders come from document expiry dates only.

## Under work

- Generating interface files for the 12 newer languages, and finishing Odia and a few missing strings in Tamil, Malayalam
  and Punjabi. Until then those pages are translated live on first use, which takes up to a minute once.
- Checking the voice loop, avatar expressions, document upload and the form guide in a real browser, now that the
  latest rebuild is complete.
- Reviewing translations with native speakers and verifying the scheme catalog.

## Upcoming

- **Sign-in:** accounts, saved history and the same documents and reminders on every device (the next phase).
- **Thousands of schemes:** import a registry export (a script is ready) to cover 4,700+ schemes including state
  schemes, then add eligibility rules to the most-used ones.
- **Scheme deadlines:** reminders for application windows, not only document expiry.
- **Richer avatar and call:** more expressive animation and true two-way streaming audio, so the assistant and the
  citizen can talk at the same time. Today the call is turn-based with interruption.
- **More ways in:** SMS or phone-call access for people without smartphones, and help centre or community-worker mode.
