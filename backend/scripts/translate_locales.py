"""Generate frontend UI locale files from frontend/src/locales/en.json using Sarvam translation.

Usage (from the repository root):
    python -m backend.scripts.translate_locales            # translate missing keys for all languages
    python -m backend.scripts.translate_locales hi ta      # only these languages
    python -m backend.scripts.translate_locales --force    # retranslate everything

Existing translations are kept unless --force is passed, so hand corrections are preserved. Every
translated string must contain exactly the same {placeholders} as the English source; otherwise it
is retried and, if it still differs, reported and left out (the UI then falls back to English for
that key, which is logged by the locale audit in the frontend tests).
"""

from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.config import LANGUAGES
from backend.services.sarvam_client import SarvamUnavailable, get_sarvam

LOCALES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "locales"
_PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def _protect(text: str) -> tuple[str, dict[str, str]]:
    """Swap {name} for numbered tokens that survive translation more reliably."""
    mapping: dict[str, str] = {}

    def repl(m: re.Match) -> str:
        token = f"[[{len(mapping) + 1}]]"
        mapping[token] = m.group(0)
        return token

    return _PLACEHOLDER.sub(repl, text), mapping


def _translate_one(text: str, lang: str) -> str | None:
    client = get_sarvam()
    want = sorted(_PLACEHOLDER.findall(text))
    protected, mapping = _protect(text)
    for attempt in range(4):
        try:
            out = client.translate(protected, lang)
        except SarvamUnavailable:
            time.sleep(1.5 * (attempt + 1))
            continue
        for token, original in mapping.items():
            out = out.replace(token, original)
        if sorted(_PLACEHOLDER.findall(out)) == want:
            return out
    return None


def main(argv: list[str]) -> int:
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    source: dict[str, str] = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    failures = 0
    for lang in (l["code"] for l in LANGUAGES if l["code"] != "en"):
        if wanted and lang not in wanted:
            continue
        path = LOCALES / f"{lang}.json"
        existing: dict[str, str] = {}
        if path.exists() and not force:
            existing = json.loads(path.read_text(encoding="utf-8"))
        todo = [k for k in source if k not in existing]
        with ThreadPoolExecutor(max_workers=6) as pool:
            done = list(pool.map(lambda k: _translate_one(source[k], lang), todo))
        for k, v in zip(todo, done):
            if v is None:
                failures += 1
                print(f"[{lang}] FAILED {k}")
            else:
                existing[k] = v
        ordered = {k: existing[k] for k in source if k in existing}
        path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{lang}] {len(ordered)}/{len(source)} keys")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
