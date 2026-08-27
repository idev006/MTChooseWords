"""Inspect PDF word sources page by page without importing into SQLite."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.extractor import diagnose_pdf_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose PDF table extraction without importing words.")
    parser.add_argument("sources", nargs="*", type=Path, help="Optional .pdf files or directories.")
    parser.add_argument("--start-page", type=int, default=1, help="First page to inspect, 1-based.")
    parser.add_argument("--max-pages", type=int, default=12, help="Maximum pages to inspect per PDF. Use 0 for all pages.")
    parser.add_argument("--output", type=Path, default=None, help="Diagnosis report JSON path.")
    return parser.parse_args()


def _pdf_sources(sources: list[Path]) -> list[Path]:
    files: list[Path] = []
    for source in sources:
        if source.is_dir():
            files.extend(sorted(source.glob("*.pdf")))
        elif source.suffix.lower() == ".pdf" and source.is_file():
            files.append(source)
    return [path for path in files if not path.name.startswith("~$")]


def _status_for_pages(pages: list) -> str:
    if any(page.error for page in pages):
        return "FAIL"
    samples = [word for page in pages for word in page.sample_words]
    if any(re.search(r"[຀-໿฼฽]", word) for word in samples):
        return "REVIEW"
    if any(page.indexed_word_count or page.legacy_word_count for page in pages):
        return "PASS"
    return "NO_WORDS_IN_SAMPLE"


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    config = AppConfig.load(root / "config.toml")
    configured_sources = [config.resolve(value) for value in config.word_source_files]
    selected = args.sources or configured_sources or [config.resolve(config.words_dir)]
    pdfs = _pdf_sources(selected)
    if not pdfs:
        raise SystemExit("No PDF sources found.")

    max_pages = None if args.max_pages == 0 else args.max_pages
    files = []
    for pdf in pdfs:
        print(f"Diagnosing {pdf.name}", flush=True)
        try:
            pages = diagnose_pdf_file(pdf, max_pages=max_pages, start_page=args.start_page)
            files.append({
                "source_file": str(pdf),
                "status": _status_for_pages(pages),
                "pages_checked": len(pages),
                "pages": [asdict(page) for page in pages],
            })
        except Exception as exc:
            files.append({"source_file": str(pdf), "status": "FAIL", "error": str(exc), "pages_checked": 0, "pages": []})

    output = args.output or root / "app/doc/evidence/pdf_source_diagnosis.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_count": len(pdfs),
        "summary": {
            "pass": sum(1 for item in files if item["status"] == "PASS"),
            "review": sum(1 for item in files if item["status"] == "REVIEW"),
            "no_words_in_sample": sum(1 for item in files if item["status"] == "NO_WORDS_IN_SAMPLE"),
            "fail": sum(1 for item in files if item["status"] == "FAIL"),
        },
        "files": files,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Diagnosis report: {output}")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
