# Thai PDF Extraction Incident: ตำลึง → ตาลึง

## Root cause

The source PDF has an incorrect `/ToUnicode` mapping for some embedded Thai glyphs. The glyph rendered on screen is correct, but the text layer may return a different Unicode code point. This is why a normal `pypdf`/`pdfplumber` extraction can produce `ตาลึง` even though the page visibly says `ตำลึง`.

The issue is not caused only by column detection or character sorting. Sorting fixes some combining-mark order, but cannot recover a glyph whose Unicode mapping is wrong or missing.

## Fix

`app/core/thai_normalizer.py` now performs a conservative repair:

1. Normalize Unicode and compose `ํา` into `ำ`.
2. Keep words already present in the Thai dictionary unchanged.
3. For an unknown word, generate candidates by replacing `า` with `ำ`.
4. Apply the replacement only when exactly one candidate is a known Thai word.
5. Otherwise preserve the extracted value for review instead of guessing.

For this specific source PDF, the normalizer also repairs known glyph-map substitutions: `๎→้`, `๑→์`, `๐→๋`, `๏→๊`, and interprets `ํ` as `ำ` before `า` or as `่` in tone-mark positions.

The source profile also contains verified compound-word and clipped-cell repairs, including `กาน้า→กาน้ำ`, `แม่เฒำ→แม่เฒ่า`, `ตำงประเทศ→ต่างประเทศ`, `พระราชดาเนิน→พระราชดำเนิน`, `รุน→รุนแรง`, `ที่นงั่→ที่นั่ง`, and `เตาแกส๊→เตาแก๊ส`. These are exact repairs for this worksheet profile and are covered by regression tests; they are not general-purpose Thai spell correction.

This repairs examples such as:

```text
ตาลึง  → ตำลึง
กานัน  → กำนัน
```

คำที่มีการันต์ เช่น `รามเกียรติ์` และ `กู้เกียรติ์` จะถูกเก็บถูกต้องเมื่อ PDF ส่ง glyph `์` ออกมาใน text layer หาก PDF ต้นฉบับลบ glyph นี้ไปเลย ระบบจะไม่เดาเติมเอง เพราะอาจทำให้คำอื่นผิด จำเป็นต้องเพิ่ม source-specific correction หรือยืนยันด้วยภาพต้นฉบับ

## Limitation and quality rule

No text extractor can promise 100% semantic recovery from a PDF with a corrupt character map. The production-safe approach is dictionary-backed conservative repair plus visual review for unresolved words. OCR may be used as an additional review signal, but it must not silently overwrite the text layer because OCR can also misread Thai tone marks and vowels.
