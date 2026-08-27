from app.core.pdf_ocr_diagnostic import _candidate_review_reasons, clean_ocr_word


def test_clean_ocr_word_collapses_spaced_thai_characters():
    assert clean_ocr_word("ก ะ พ ร ิ บ") == "กะพริบ"
    assert clean_ocr_word("ผ อ บ ( ผ ะ - อ บ )") == "ผอบ (ผะ-อบ)"


def test_ocr_candidate_review_reasons_flag_low_confidence_and_bad_index():
    assert _candidate_review_reasons("๒ อ", "ผอบ", 92) == ["source_index_needs_review"]
    assert "low_ocr_confidence" in _candidate_review_reasons("๑", "aD)", 28)
