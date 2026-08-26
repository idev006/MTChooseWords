from __future__ import annotations

from datetime import datetime


def build_pdf_filename(words_per_page: int, timestamp: datetime | None = None, set_number: int | None = None) -> str:
    """Return a Windows-safe name containing optional set number and timestamp."""
    moment = timestamp or datetime.now()
    prefix = f"mt_choose_words-set{set_number:02d}-" if set_number is not None else "mt_choose_words-"
    return f"{prefix}{words_per_page}-{moment:%Y%m%d-%H%M%S}.pdf"
