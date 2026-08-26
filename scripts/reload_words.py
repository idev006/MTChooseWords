"""Reload worksheet words from supported table sources into SQLite."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import AppConfig
from app.core.source_contract import validate_word_entries, write_import_report
from app.core.word_source_extractor import TableWordSourceExtractor
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
    rows = TableWordSourceExtractor().extract(sources)
    report = validate_word_entries(rows)
    repository = WordRepository(config.resolve(config.database))
    if args.append:
        count = repository.add_words(rows)
        mode = "append"
    else:
        count = repository.replace_words(rows)
        mode = "clear-all"
    write_import_report(root / "app/doc/evidence/word_import_report.json", report)
    print(f"Reload complete ({mode}): {count} unique words")
    print(f"Source cells: {report.total_cells}; duplicates removed: {report.duplicate_cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
