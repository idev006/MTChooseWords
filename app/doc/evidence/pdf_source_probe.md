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

Current certification status:

```text
PDF batch is supported by adapter contract, but this specific PDF folder is NOT certified for 100% production import yet.
```

Required before production use:

1. Add per-file PDF fixtures or known-good expected counts.
2. Add visual review evidence for pages whose text layer contains corrupted characters.
3. Prefer DOCX source for production word-bank import when available.
4. Use PDF only when text layer and table geometry pass the source contract without unresolved issues.
