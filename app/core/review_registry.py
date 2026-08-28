from __future__ import annotations

import json
import re
from pathlib import Path

from app.core.source_contract import THAI_DIGITS


GRADE_VALUE_RE = re.compile(r"(?:ป\.?|p)\s*([1-6๑-๖])", re.IGNORECASE)


def _grade_number(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    match = GRADE_VALUE_RE.search(text)
    if not match:
        raise ValueError(f"ไม่พบระดับชั้น ป.1-ป.6 ใน reviewed suspicion: {value}")
    digit = match.group(1).translate(THAI_DIGITS)
    return int(digit)


def load_reviewed_suspicions(path: Path) -> set[tuple[int, str, str]]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    approved = payload.get("approved_suspicions", [])
    return {
        (_grade_number(item["grade"]), " ".join(str(item["text"]).split()).casefold(), str(item["reason"]))
        for item in approved
    }
