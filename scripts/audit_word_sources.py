"""Audit DOCX/PDF word sources and write review evidence without importing."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.docx_extractor import extract_docx_words
from app.core.extractor import extract_pdf_file_words
from app.core.review_registry import load_reviewed_suspicions
from app.core.source_contract import collect_word_suspicions, validate_word_entries
from app.core.word_source_extractor import TableWordSourceExtractor


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit DOCX/PDF table word sources before import.")
    parser.add_argument("sources", nargs="*", type=Path, help="Optional .docx/.pdf files or source directories.")
    parser.add_argument("--output", type=Path, default=None, help="Audit report JSON path.")
    return parser.parse_args()


def _extract_file(path: Path):
    if path.suffix.lower() == ".docx":
        return extract_docx_words(path)
    if path.suffix.lower() == ".pdf":
        return extract_pdf_file_words(path)
    return []


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    config = AppConfig.load(root / "config.toml")
    reviewed = load_reviewed_suspicions(root / "app/assets/words/reviewed_suspicions.json")
    selected = args.sources or [config.resolve(value) for value in config.word_source_files] or [config.resolve(config.words_dir)]
    sources = TableWordSourceExtractor()._sources(selected)
    if not sources:
        raise SystemExit("No supported .docx/.pdf sources found.")

    files = []
    all_rows = []
    for source in sources:
        record = {"source_file": str(source), "status": "PASS", "error": None, "total_cells": 0, "unique_words": 0, "suspicions": []}
        try:
            rows = _extract_file(source)
            report = validate_word_entries(rows)
            suspicions = collect_word_suspicions(rows)
            unresolved = [
                item for item in suspicions
                if (item.grade, item.text.casefold(), item.reason) not in reviewed
            ]
            record.update({
                "total_cells": report.total_cells,
                "unique_words": report.unique_words,
                "suspicions": [asdict(item) for item in suspicions],
                "unresolved_suspicions": [asdict(item) for item in unresolved],
                "status": "REVIEW" if unresolved else "PASS",
            })
            all_rows.extend(rows)
        except Exception as exc:
            record["status"] = "FAIL"
            record["error"] = str(exc)
        files.append(record)

    output = args.output or root / "app/doc/evidence/word_source_audit_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_count": len(sources),
        "summary": {
            "pass": sum(1 for item in files if item["status"] == "PASS"),
            "review": sum(1 for item in files if item["status"] == "REVIEW"),
            "fail": sum(1 for item in files if item["status"] == "FAIL"),
            "total_cells": sum(item["total_cells"] for item in files),
        },
        "files": files,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audit report: {output}")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 1 if payload["summary"]["fail"] or payload["summary"]["review"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
