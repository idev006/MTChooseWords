from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Return writable application root in source and PyInstaller modes."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class PathManager:
    """Centralize project-relative paths so packaged builds stay portable."""

    def __init__(self, root: Path | None = None):
        self.root = (root or application_root()).resolve()

    def resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def to_config_value(self, value: str | Path) -> str:
        path = Path(value)
        if not path.is_absolute():
            return path.as_posix()
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def display(self, value: str | Path) -> str:
        return self.to_config_value(self.resolve(value))

    def config_file(self) -> Path:
        return self.root / "config.toml"

    def reviewed_suspicions_file(self) -> Path:
        return self.root / "app/assets/words/reviewed_suspicions.json"

    def word_source_audit_report(self) -> Path:
        return self.root / "app/doc/evidence/word_source_audit_report.json"

    def word_import_report(self) -> Path:
        return self.root / "app/doc/evidence/word_import_report.json"
