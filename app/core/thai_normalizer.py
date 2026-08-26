from __future__ import annotations

import unicodedata
from functools import lru_cache

from pythainlp.corpus import thai_words


# The worksheet PDF has a damaged ToUnicode map and a few clipped text cells.
# These are exact source-profile repairs, not general-purpose spell correction.
_SOURCE_REPAIRS = {
    "กาน้า": "กาน้ำ",
    "แม่เฒำ": "แม่เฒ่า",
    "แม่เฒํา": "แม่เฒ่า",
    "ตำงประเทศ": "ต่างประเทศ",
    "ตํางประเทศ": "ต่างประเทศ",
    "พระราชดาเนิน": "พระราชดำเนิน",
    "พระราชดาริ": "พระราชดำริ",
    "ความสาคัญ": "ความสำคัญ",
    "สานักงาน": "สำนักงาน",
    "บาเพ็ญ": "บำเพ็ญ",
    "รุน": "รุนแรง",
    "ที่นง": "ที่นั่ง",
    "\u0e17\u0e35\u0e48\u0e19\u0e07\u0e31\u0e48": "\u0e17\u0e35\u0e48\u0e19\u0e31\u0e48\u0e07",
    "เตาแกส๊": "เตาแก๊ส",
    "ซีอว": "ซีอิ๊ว",
}


@lru_cache(maxsize=1)
def _thai_dictionary() -> frozenset[str]:
    return frozenset(thai_words())


def normalize_thai_word(value: str) -> str:
    """Repair common malformed Thai PDF Unicode mappings conservatively.

    Some source glyphs visually represent SARA AM but their ToUnicode map
    emits SARA AA. We only change a word when the original is not in the
    dictionary and exactly one SARA-AM candidate is a dictionary word.
    """
    word = unicodedata.normalize("NFC", value).strip(" ●•·|_")
    # This source PDF maps several visible Thai marks to unrelated Thai
    # code points. These replacements are scoped to the known worksheet
    # profile and are applied before dictionary validation.
    word = word.translate(str.maketrans({
        "๎": "้",  # visible mai tho
        "๑": "์",  # visible karan
        "๐": "๋",  # visible mai chattawa
        "๏": "๊",  # visible mai tri
    }))
    chars: list[str] = []
    index = 0
    while index < len(word):
        if word[index] == "ํ":
            if index + 1 < len(word) and word[index + 1] == "า":
                chars.append("ำ")
                index += 2
                continue
            chars.append("่")
        else:
            chars.append(word[index])
        index += 1
    word = "".join(chars)
    if word in _SOURCE_REPAIRS:
        return _SOURCE_REPAIRS[word]
    dictionary = _thai_dictionary()
    if word in dictionary:
        return word
    candidates = {
        word[:index] + "\u0e33" + word[index + 1:]
        for index, char in enumerate(word)
        if char == "\u0e32"
    }
    candidates.update(
        word[:index] + "\u0e48\u0e32" + word[index + 1:]
        for index, char in enumerate(word)
        if char == "\u0e33"
    )
    valid = candidates & dictionary
    return next(iter(valid)) if len(valid) == 1 else word
