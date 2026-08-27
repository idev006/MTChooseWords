# PDF Source Probe — 2026-08-26

Source folder:

```text
app/assets/words/pdf
```

Files found:

- `_ บัญชีคำพื้นฐาน ป.๒ (ฉบับสมบูรณ์).pdf`
- `_บัญชีคำพื้นฐาน ป.๑ (ฉบับสมบูรณ์).pdf`
- `_บัญชีคำพื้นฐาน ป๓ ฉบับสมบูรณ์.pdf`
- `_บัญชีคำพื้นฐาน ป๔ (ฉบับสมบูรณ์)).pdf`
- `_บัญชีคำพื้นฐาน ป๕ฉบับสมบูรณ์CMYK.pdf`
- `_บัญชีคำพื้นฐาน ป๖ (สมบูรณ์).pdf`

Finding:

- Files contain table-like pages with 8+ columns matching the `ลำดับ/คำ` structure.
- Several early pages are preface/table-of-contents pages and must not be imported.
- Some PDFs expose corrupted Thai text-layer characters from the PDF extractor, similar to the prior Thai PDF incident documented in `08-thai-pdf-extraction.md`.
- Full-folder PDF extraction is expensive because the files are large.
- Current fail-closed behavior rejects the PDF batch before database import when a page/table cannot be interpreted as valid word cells.

Latest diagnostic run:

```text
2026-08-27
Command: scripts/diagnose_pdf_sources.py app/assets/words/pdf --start-page 1 --max-pages 5
Result: PASS 0, REVIEW 4, NO_WORDS_IN_SAMPLE 2, FAIL 0
Report: app/doc/evidence/pdf_source_diagnosis.json
```

Observed examples from the PDF text layer include corrupted output such as `วิสรรชนียຏ`, `ล้ๅา฽ทຌ`, and `ามประ฼ภทของค้า`. These are not safe for production import.

OCR cell diagnostic:

```text
2026-08-27
Command: scripts/diagnose_pdf_ocr_cells.py "app/assets/words/pdf/_บัญชีคำพื้นฐาน ป๖ (สมบูรณ์).pdf" --page 10 --max-cells 40 --expected-count 15
Result: 15 candidates from 15 expected visible word cells, coverage 100%, ACCEPT 10, REVIEW 5
Report: app/doc/evidence/pdf_ocr_cell_diagnosis.json
```

OCR cell extraction can read several word cells correctly with high confidence, for example `กะพริบ`, `ขยิบตา`, `พระสนับเพลา`, `อับเฉา`, `กุหลาบ`, `ประทับ`, `พลับพลา`, `ขยับ`, and `ผอบ (ผะ-อบ)`.

The representative page now exceeds the 90% read-coverage target, but OCR still misreads some source indexes and one low-confidence candidate. Therefore OCR is currently a diagnostic/review path with evidence images, not an approved production import path for the whole PDF batch.

Folder OCR read command:

```text
2026-08-27
Command: scripts/read_pdf_ocr_folder.py app/assets/words/pdf --start-page 10 --max-pages-per-file 1 --max-cells-per-page 80 --page-timeout-seconds 45
Result: word candidates 15, review queue 18, ACCEPT 10, REVIEW 8, timeout-review pages 3, error-review pages 0
Report: app/doc/evidence/pdf_ocr_folder_read_report.json
Review CSV: app/doc/evidence/pdf_ocr_review_queue.csv
```

This folder run is a controlled one-page-per-file development probe, not a full-folder certification. Page timeout rows are intentionally sent to REVIEW instead of being imported.

Current certification status:

```text
PDF batch is supported by adapter contract, but this specific PDF folder is NOT certified for 100% production import yet.
```

Required before production use:

1. Add per-file PDF fixtures or known-good expected counts.
2. Add visual review evidence for pages whose text layer contains corrupted characters.
3. Prefer DOCX source for production word-bank import when available.
4. Use PDF only when text layer and table geometry pass the source contract without unresolved issues.
5. Add an OCR-backed PDF adapter only after establishing a human-reviewed expected output set for at least one representative PDF.
