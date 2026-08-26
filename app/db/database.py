from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, delete, inspect, select
from sqlalchemy.orm import Session
from app.core.contracts import WordEntry
from app.db.models import Base, Word


class WordRepository:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{path.as_posix()}", future=True)
        self._ensure_schema()
        Base.metadata.create_all(self.engine)

    def _ensure_schema(self) -> None:
        inspector = inspect(self.engine)
        if not inspector.has_table("words"):
            return
        columns = {column["name"] for column in inspector.get_columns("words")}
        primary_key = tuple(inspector.get_pk_constraint("words").get("constrained_columns", []))
        expected_columns = {"text", "source_file", "normalized", "grade", "source_index"}
        if not expected_columns.issubset(columns) or primary_key != ("grade", "normalized"):
            Base.metadata.drop_all(self.engine)

    def _coerce_entry(self, row: WordEntry | tuple[str, str]) -> tuple[str, str, int, int | None]:
        if isinstance(row, WordEntry):
            return row.text, row.source_file, row.grade, row.source_index
        text, source = row
        return text, source, 1, None

    def clear_all(self) -> None:
        with Session(self.engine) as session, session.begin():
            session.execute(delete(Word))

    def add_words(self, rows: list[WordEntry] | list[tuple[str, str]]) -> int:
        added = 0
        with Session(self.engine) as session, session.begin():
            seen: set[tuple[int, str]] = set()
            for row in rows:
                text, source, grade, source_index = self._coerce_entry(row)
                normalized = " ".join(text.split()).casefold()
                key = (grade, normalized)
                if normalized and key not in seen and session.get(Word, key) is None:
                    session.add(Word(grade=grade, normalized=normalized, text=text, source_file=source, source_index=source_index))
                    seen.add(key)
                    added += 1
        return added

    def replace_words(self, rows: list[WordEntry] | list[tuple[str, str]]) -> int:
        self.clear_all()
        return self.add_words(rows)

    def count(self, grades: list[int] | None = None) -> int:
        with Session(self.engine) as session:
            statement = select(Word.normalized)
            if grades:
                statement = statement.where(Word.grade.in_(grades))
            return len(session.scalars(statement).all())

    def count_by_grade(self) -> dict[int, int]:
        with Session(self.engine) as session:
            result: dict[int, int] = {}
            for grade in range(1, 7):
                statement = select(Word.normalized).where(Word.grade == grade)
                result[grade] = len(session.scalars(statement).all())
            return result

    def random_words(self, amount: int, rng, grades: list[int] | None = None) -> list[str]:
        with Session(self.engine) as session:
            statement = select(Word.text)
            if grades:
                statement = statement.where(Word.grade.in_(grades))
            values = list(dict.fromkeys(session.scalars(statement).all()))
        rng.shuffle(values)
        return values[:amount]
