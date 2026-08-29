from app.core.thai_normalizer import normalize_thai_word


def test_normalizer_strips_source_noise_and_repairs_sara_am_order():
    assert normalize_thai_word(" ●กระบุง| ") == "กระบุง"
    assert normalize_thai_word("กํานัน") == "กำนัน"


def test_normalizer_does_not_change_known_word():
    assert normalize_thai_word("กระบุง") == "กระบุง"


def test_requested_thai_words_are_preserved():
    for word in ("ล้ำเส้น", "รามเกียรติ์", "กู้เกียรติ์"):
        assert normalize_thai_word(word) == word


def test_normalizer_does_not_guess_removed_pdf_repairs():
    assert normalize_thai_word("ตาลึง") == "ตาลึง"
    assert normalize_thai_word("กานัน") == "กานัน"
