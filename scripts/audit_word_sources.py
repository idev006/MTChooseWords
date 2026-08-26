"""Audit DOCX/PDF word sources and write review evidence without importing."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.import_audit import audit_word_sources, write_audit_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit DOCX/PDF table word sources before import.")
    parser.add_argument("sources", nargs="*", type=Path, help="Optional .docx/.pdf files or source directories.")
    parser.add_argument("--output", type=Path, default=None, help="Audit report JSON path.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    config = AppConfig.load(root / "config.toml")
    selected = args.sources or [config.resolve(value) for value in config.word_source_files] or [config.resolve(config.words_dir)]
    output = args.output or root / "app/doc/evidence/word_source_audit_report.json"
    result = audit_word_sources(selected, root / "app/assets/words/reviewed_suspicions.json")
    write_audit_report(output, result)
    print(f"Audit report: {output}")
    print(json.dumps({
        "pass": result.summary.pass_count,
        "review": result.summary.review_count,
        "fail": result.summary.fail_count,
        "total_cells": result.summary.total_cells,
        "unique_words": result.summary.unique_words,
    }, ensure_ascii=False))
    return 0 if result.can_import else 1


if __name__ == "__main__":
    raise SystemExit(main())
