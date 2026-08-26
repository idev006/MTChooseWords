"""Reload worksheet words from supported table sources into SQLite."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.import_audit import audit_word_sources, write_audit_report
from app.core.source_contract import write_import_report
from app.db.database import WordRepository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reload DOCX/PDF table word sources.")
    parser.add_argument("sources", nargs="*", type=Path, help="Optional .docx/.pdf files or source directories.")
    parser.add_argument("--append", action="store_true", help="Add words without clearing the existing database.")
    parser.add_argument("--clear-all", action="store_true", help="Clear all words before importing. This is the default.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    config = AppConfig.load(root / "config.toml")
    configured_sources = [config.resolve(value) for value in config.word_source_files]
    sources = args.sources or configured_sources or [config.resolve(config.words_dir)]
    audit = audit_word_sources(sources, root / "app/assets/words/reviewed_suspicions.json")
    write_audit_report(root / "app/doc/evidence/word_source_audit_report.json", audit)
    if not audit.can_import or audit.import_report is None:
        print(f"Reload blocked: {audit.blocking_message()}")
        print("Review app/doc/evidence/word_source_audit_report.json before importing.")
        return 1

    repository = WordRepository(config.resolve(config.database))
    if args.append:
        count = repository.add_words(audit.rows)
        mode = "append"
    else:
        count = repository.replace_words(audit.rows)
        mode = "clear-all"
    write_import_report(root / "app/doc/evidence/word_import_report.json", audit.import_report)
    print(f"Reload complete ({mode}): {count} unique words")
    print(f"Source cells: {audit.import_report.total_cells}; duplicates removed: {audit.import_report.duplicate_cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
