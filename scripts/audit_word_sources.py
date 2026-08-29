"""Audit production DOCX/TXT word sources and write review evidence without importing."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.import_audit import audit_word_sources, write_audit_report
from app.core.paths import PathManager


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit DOCX/TXT word sources before import.")
    parser.add_argument("sources", nargs="*", type=Path, help="Optional .docx/.txt files or source directories.")
    parser.add_argument("--output", type=Path, default=None, help="Audit report JSON path.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    paths = PathManager(Path(__file__).resolve().parents[1])
    config = AppConfig.load(paths.config_file())
    selected = args.sources or [paths.resolve(value) for value in config.word_source_files] or [paths.resolve(config.words_dir)]
    output = args.output or paths.word_source_audit_report()
    try:
        result = audit_word_sources(selected, paths.reviewed_suspicions_file(), path_manager=paths)
    except ValueError as exc:
        print(f"Audit blocked: {exc}")
        return 1
    write_audit_report(output, result, paths)
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
