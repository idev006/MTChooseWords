"""Read PDF word cells with OCR and produce an ACCEPT/REVIEW queue."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymupdf


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR-read PDF word sources into review evidence without importing.")
    parser.add_argument("source", type=Path, help="PDF file or directory.")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages-per-file", type=int, default=0, help="0 means all pages.")
    parser.add_argument("--max-cells-per-page", type=int, default=120)
    parser.add_argument("--page-timeout-seconds", type=int, default=45)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--evidence-mode", choices=["review", "all", "none"], default="review")
    return parser.parse_args()


def _pdf_sources(source: Path) -> list[Path]:
    if source.is_dir():
        return sorted(
            [path for path in source.glob("*.pdf") if not path.name.startswith("~$")],
            key=lambda path: path.stat().st_size,
        )
    if source.suffix.lower() == ".pdf" and source.is_file():
        return [source]
    raise ValueError(f"ไม่พบ PDF source: {source}")


def _candidate_key(record: dict) -> tuple:
    return (
        record.get("source_file"),
        record.get("page"),
        record.get("table_index"),
        record.get("row_index"),
        record.get("pair_index"),
    )


def _page_count(pdf: Path) -> int:
    with pymupdf.open(pdf) as document:
        return len(document)


def _run_page_reader(script: Path, pdf: Path, page_number: int, args: argparse.Namespace, output: Path, evidence_dir: Path) -> dict:
    command = [
        sys.executable,
        str(script),
        str(pdf),
        "--page", str(page_number),
        "--max-cells", str(args.max_cells_per_page),
        "--evidence-mode", args.evidence_mode,
        "--output", str(output),
        "--evidence-dir", str(evidence_dir),
    ]
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        subprocess.run(
            command,
            cwd=script.parents[1],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.page_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {"page": page_number, "status": "TIMEOUT_REVIEW", "candidate_count": 0, "candidates": []}
    except subprocess.CalledProcessError as exc:
        return {
            "page": page_number,
            "status": "ERROR_REVIEW",
            "candidate_count": 0,
            "error": (exc.stderr or exc.stdout or str(exc))[-2000:],
            "candidates": [],
        }
    return json.loads(output.read_text(encoding="utf-8"))


def _write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "status", "source_file", "page", "source_index", "source_index_text",
        "word_text", "confidence", "reasons", "evidence_image",
        "table_index", "row_index", "pair_index",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["reasons"] = ";".join(row.get("reasons") or [])
            writer.writerow(row)


def _page_review_record(pdf: Path, page_number: int, status: str, reason: str, error: str | None = None) -> dict:
    return {
        "status": status,
        "source_file": str(pdf),
        "page": page_number,
        "source_index": None,
        "source_index_text": "",
        "word_text": "",
        "confidence": 0,
        "reasons": [reason],
        "evidence_image": None,
        "table_index": None,
        "row_index": None,
        "pair_index": None,
        "error": error,
    }


def _word_records(records: list[dict]) -> list[dict]:
    return [record for record in records if record.get("word_text")]


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output or root / "app/doc/evidence/pdf_ocr_folder_read_report.json"
    csv_output = args.csv_output or root / "app/doc/evidence/pdf_ocr_review_queue.csv"
    evidence_dir = args.evidence_dir or root / "app/doc/evidence/pdf_ocr_cells"
    max_pages = None if args.max_pages_per_file == 0 else args.max_pages_per_file
    page_report_dir = root / "app/doc/evidence/pdf_ocr_page_reports"
    page_reader = root / "scripts/diagnose_pdf_ocr_cells.py"

    files = []
    all_records: list[dict] = []
    seen: set[tuple] = set()
    for pdf in _pdf_sources(args.source):
        print(f"Reading {pdf.name}", flush=True)
        total_pages = _page_count(pdf)
        first_page = max(args.start_page, 1)
        last_page = min(total_pages, first_page + max_pages - 1) if max_pages else total_pages
        file_records = []
        page_results = []
        for page_number in range(first_page, last_page + 1):
            if page_number == first_page or page_number == last_page or (page_number - first_page) % 5 == 0:
                print(f"OCR page {page_number}/{total_pages}: {pdf.name}", flush=True)
            page_output = page_report_dir / pdf.stem / f"page-{page_number:03d}.json"
            page_output.parent.mkdir(parents=True, exist_ok=True)
            page_payload = _run_page_reader(page_reader, pdf, page_number, args, page_output, evidence_dir)
            page_results.append({
                "page": page_number,
                "status": page_payload.get("status", "DONE"),
                "candidate_count": page_payload.get("candidate_count", 0),
                "accept_count": page_payload.get("accept_count", 0),
                "review_count": page_payload.get("review_count", 0),
                "error": page_payload.get("error"),
            })
            if page_payload.get("status") == "TIMEOUT_REVIEW":
                file_records.append(_page_review_record(pdf, page_number, "REVIEW", "page_timeout_review"))
            elif page_payload.get("status") == "ERROR_REVIEW":
                file_records.append(_page_review_record(pdf, page_number, "REVIEW", "page_error_review", page_payload.get("error")))
            for record in page_payload.get("candidates", []):
                record["source_file"] = str(pdf)
                record["page"] = page_number
                key = _candidate_key(record)
                if key in seen:
                    record["status"] = "REVIEW"
                    record.setdefault("reasons", []).append("duplicate_cell_candidate")
                seen.add(key)
                file_records.append(record)
        word_records = _word_records(file_records)
        files.append({
            "source_file": str(pdf),
            "pages_checked": len(page_results),
            "timeout_review_pages": sum(1 for item in page_results if item["status"] == "TIMEOUT_REVIEW"),
            "error_review_pages": sum(1 for item in page_results if item["status"] == "ERROR_REVIEW"),
            "word_candidate_count": len(word_records),
            "review_queue_count": len(file_records),
            "accept_count": sum(1 for record in file_records if record["status"] == "ACCEPT"),
            "review_count": sum(1 for record in file_records if record["status"] == "REVIEW"),
            "pages": page_results,
        })
        all_records.extend(file_records)

    all_word_records = _word_records(all_records)
    payload = {
        "source": str(args.source),
        "source_count": len(files),
        "summary": {
            "word_candidate_count": len(all_word_records),
            "review_queue_count": len(all_records),
            "accept_count": sum(1 for record in all_records if record["status"] == "ACCEPT"),
            "review_count": sum(1 for record in all_records if record["status"] == "REVIEW"),
            "timeout_review_pages": sum(item["timeout_review_pages"] for item in files),
            "error_review_pages": sum(item["error_review_pages"] for item in files),
        },
        "files": files,
        "records": all_records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(csv_output, all_records)
    print(f"PDF OCR report: {output}")
    print(f"Review CSV: {csv_output}")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
