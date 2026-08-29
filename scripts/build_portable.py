from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD_APP = DIST / "MTChooseWords"
EXE = BUILD_APP / "MTChooseWords.exe"
PORTABLE = DIST / "MTChooseWords_Portable"
PORTABLE_ZIP = DIST / "MTChooseWords_Portable.zip"


def _copy_file(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(
    source: Path,
    target: Path,
    excluded_parts: set[str] | None = None,
) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    target.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        if excluded_parts and any(part in excluded_parts for part in relative.parts):
            continue
        destination = target / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            _copy_file(item, destination)


def _copy_tree_filtered(
    source: Path,
    target: Path,
    allowed_suffixes: set[str] | None = None,
    excluded_parts: set[str] | None = None,
) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    target.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        if excluded_parts and any(part in excluded_parts for part in relative.parts):
            continue
        destination = target / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if allowed_suffixes is not None and item.suffix.lower() not in allowed_suffixes:
            continue
        _copy_file(item, destination)


def _run_pyinstaller() -> None:
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "mt_choose_words.spec"],
        cwd=ROOT,
        check=True,
    )


def _remove_tree_with_retry(path: Path, attempts: int = 5) -> None:
    for attempt in range(1, attempts + 1):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as exc:
            if attempt == attempts:
                raise RuntimeError(
                    f"Cannot rebuild portable folder because a file is still in use: {exc.filename}. "
                    "Close MTChooseWords.exe and run the portable build again."
                ) from exc
            time.sleep(1)


def build_portable(skip_build: bool = False) -> Path:
    if not skip_build:
        _run_pyinstaller()
    if not EXE.exists():
        raise FileNotFoundError(f"Executable not found: {EXE}")

    if PORTABLE.exists():
        resolved = PORTABLE.resolve()
        if resolved.parent != DIST.resolve():
            raise RuntimeError(f"Refusing to delete unexpected path: {resolved}")
        _remove_tree_with_retry(PORTABLE)

    _copy_tree(BUILD_APP, PORTABLE)
    _copy_file(ROOT / "Run_MTChooseWords_Portable.bat", PORTABLE / "Run_MTChooseWords.bat")
    _copy_file(ROOT / "config.toml", PORTABLE / "config.toml")
    _copy_file(ROOT / "app/mtchoosewords.sqlite3", PORTABLE / "app/mtchoosewords.sqlite3")
    _copy_file(ROOT / "app/assets/words/reviewed_suspicions.json", PORTABLE / "app/assets/words/reviewed_suspicions.json")

    _copy_tree_filtered(ROOT / "app/assets/fonts", PORTABLE / "app/assets/fonts")
    _copy_tree_filtered(ROOT / "app/assets/words/lot1", PORTABLE / "app/assets/words/lot1", {".docx", ".json"})
    _copy_tree_filtered(ROOT / "app/assets/words/text", PORTABLE / "app/assets/words/text", {".txt", ".json"})
    _copy_tree_filtered(
        ROOT / "app/doc",
        PORTABLE / "app/doc",
        excluded_parts={"pdf_ocr_cells", "pdf_ocr_page_reports"},
    )

    (PORTABLE / "app/output").mkdir(parents=True, exist_ok=True)
    if PORTABLE_ZIP.exists():
        PORTABLE_ZIP.unlink()
    shutil.make_archive(str(PORTABLE), "zip", root_dir=DIST, base_dir=PORTABLE.name)
    return PORTABLE


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the MT Choose Words portable Windows folder.")
    parser.add_argument("--skip-build", action="store_true", help="Reuse dist/MTChooseWords.exe instead of running PyInstaller.")
    args = parser.parse_args()

    target = build_portable(skip_build=args.skip_build)
    print(f"Portable package: {target}")
    print(f"Portable zip: {PORTABLE_ZIP}")
    print("Included: PyInstaller runtime folder, config.toml, SQLite database, fonts, DOCX/TXT word sources, documentation, output folder")
    print("Excluded: PDF source files, .doc source files, virtual environment, build cache")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
