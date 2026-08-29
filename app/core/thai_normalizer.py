from __future__ import annotations

import unicodedata


def normalize_thai_word(value: str) -> str:
    """Normalize DOCX/TXT source text without guessing spelling."""
    word = unicodedata.normalize("NFC", value).strip(" ●•·|_")
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
    return "".join(chars)
