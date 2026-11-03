"""Translate the whole scheme catalog into every supported language and store it in
backend/data/translations/, so users never wait on first-time translation.

    python -m backend.scripts.prewarm_translations [hi ta ...]
"""

from __future__ import annotations

import sys

from backend.config import LANGUAGES
from backend.services.catalog import get_catalog
from backend.services.translation import localize_scheme


def main(argv: list[str]) -> int:
    failed = 0
    for lang in (l["code"] for l in LANGUAGES if l["code"] != "en"):
        if argv and lang not in argv:
            continue
        for scheme in get_catalog().all():
            _, ok = localize_scheme(scheme, lang, detail=True)
            if not ok:
                failed += 1
                print(f"[{lang}] incomplete: {scheme['id']}")
        print(f"[{lang}] done")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
