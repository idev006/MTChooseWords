from app.core.thai_normalizer import normalize_thai_word


def test_repairs_sara_am_mapping_from_source_pdf():
    assert normalize_thai_word("ตาลึง") == "ตำลึง"
    assert normalize_thai_word("กานัน") == "กำนัน"


def test_normalizer_does_not_change_known_word():
    assert normalize_thai_word("กระบุง") == "กระบุง"


def test_requested_thai_words_are_preserved_when_pdf_mapping_is_correct():
    for word in ("ล้ำเส้น", "รามเกียรติ์", "กู้เกียรติ์"):
        assert normalize_thai_word(word) == word


def test_repairs_source_pdf_mapped_tone_and_karan_glyphs():
    assert normalize_thai_word("ต๎นองุํน") == "ต้นองุ่น"
    assert normalize_thai_word("หุํนยนต๑") == "หุ่นยนต์"
    assert normalize_thai_word("ต๎นพุทรา") == "ต้นพุทรา"


def test_repairs_source_profile_compound_and_clipped_words():
    repairs = {
        "กาน้า": "กาน้ำ",
        "แม่เฒำ": "แม่เฒ่า",
        "ตำงประเทศ": "ต่างประเทศ",
        "พระราชดาเนิน": "พระราชดำเนิน",
        "รุน": "รุนแรง",
        "ที่นง": "ที่นั่ง",
        "\u0e17\u0e35\u0e48\u0e19\u0e07\u0e31\u0e48": "\u0e17\u0e35\u0e48\u0e19\u0e31\u0e48\u0e07",
        "เตาแก๏ส": "เตาแก๊ส",
        "เตาแกส๊": "เตาแก๊ส",
        "ซีอว": "ซีอิ๊ว",
    }
    for source, expected in repairs.items():
        assert normalize_thai_word(source) == expected
