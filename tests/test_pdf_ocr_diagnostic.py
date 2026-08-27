from app.core.pdf_ocr_diagnostic import clean_ocr_word


def test_clean_ocr_word_collapses_spaced_thai_characters():
    assert clean_ocr_word("ก ะ พ ร ิ บ") == "กะพริบ"
    assert clean_ocr_word("ผ อ บ ( ผ ะ - อ บ )") == "ผอบ (ผะ-อบ)"
