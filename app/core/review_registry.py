from __future__ import annotations

import json
from pathlib import Path


def load_reviewed_suspicions(path: Path) -> set[tuple[int, str, str]]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    approved = payload.get("approved_suspicions", [])
    return {
        (int(item["grade"]), " ".join(str(item["text"]).split()).casefold(), str(item["reason"]))
        for item in approved
    }
