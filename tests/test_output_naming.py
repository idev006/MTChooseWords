from datetime import datetime

from app.core.output_naming import build_pdf_filename


def test_generated_pdf_name_contains_word_count_and_windows_safe_datetime():
    stamp = datetime(2026, 7, 26, 15, 30, 45)
    assert build_pdf_filename(100, stamp) == "mt_choose_words-100-20260726-153045.pdf"
    assert build_pdf_filename(100, stamp, set_number=2) == "mt_choose_words-set02-100-20260726-153045.pdf"
