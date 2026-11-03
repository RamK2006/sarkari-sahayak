"""Add schemes from a larger official registry export (for example a MyScheme dump) to the searchable catalog.

    python -m backend.scripts.ingest_schemes export.json

The input is a JSON list of objects with: id, name, ministry, summary, benefits, documents (list),
categories (list), states (list of state names, or ["central"]), apply_url, source_url, and optionally
`criteria` (same typed format as schemes.json). Records without criteria are searchable and shown as
"not assessed": they are never reported as eligible. Output: backend/data/schemes_extra.json, merged with
schemes.json at startup (core records win on id clashes).
"""

from __future__ import annotations

import json
import sys

from backend.config import get_settings

REQUIRED = ("id", "name", "summary", "source_url")


def normalise(r: dict) -> dict:
    return {
        "id": str(r["id"]), "name": r["name"], "ministry": r.get("ministry", ""), "summary": r["summary"],
        "benefits": r.get("benefits", ""), "categories": r.get("categories", []),
        "states": r.get("states") or ["central"], "criteria": r.get("criteria", []),
        "documents": r.get("documents", []), "apply": {"url": r.get("apply_url"), "channel": r.get("apply_channel")},
        "source_url": r["source_url"], "notes": r.get("notes", []), "last_verified": r.get("last_verified"),
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    records = json.loads(open(argv[0], encoding="utf-8").read())
    good, bad = [], 0
    for r in records:
        if all(r.get(k) for k in REQUIRED):
            good.append(normalise(r))
        else:
            bad += 1
    out = get_settings().DATA_DIR / "schemes_extra.json"
    out.write_text(json.dumps(good, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(good)} schemes to {out} ({bad} skipped for missing fields)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
