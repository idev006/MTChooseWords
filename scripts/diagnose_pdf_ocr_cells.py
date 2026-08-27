"""OCR PDF table cells for one page without importing into SQLite."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.pdf_ocr_diagnostic import diagnose_pdf_ocr_cells


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR one PDF page cell by cell for extraction diagnosis.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="1-based page number.")
    parser.add_argument("--max-cells", type=int, default=80)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    rows = diagnose_pdf_ocr_cells(args.pdf, args.page, args.max_cells)
    output = args.output or root / "app/doc/evidence/pdf_ocr_cell_diagnosis.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_file": str(args.pdf),
        "page": args.page,
        "candidate_count": len(rows),
        "candidates": [asdict(row) for row in rows],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OCR cell report: {output}")
    print(json.dumps({"candidate_count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
