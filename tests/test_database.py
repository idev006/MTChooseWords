from app.db.database import WordRepository
from app.core.contracts import WordEntry


def test_replace_words_is_unique_and_reloads(tmp_path):
    repo = WordRepository(tmp_path / "words.sqlite3")
    assert repo.replace_words([("กัน", "a.pdf"), ("กัน", "a.pdf"), ("กระดาษ", "a.pdf")]) == 2
    assert repo.count() == 2
    assert repo.replace_words([("ใหม่", "b.pdf")]) == 1
    assert repo.count() == 1
    assert repo.random_words(1, __import__("random").Random(1)) == ["ใหม่"]


def test_words_are_filtered_by_grade(tmp_path):
    repo = WordRepository(tmp_path / "words.sqlite3")
    rows = [
        WordEntry("กา", "p1.docx", 1, 1),
        WordEntry("ขา", "p1.docx", 1, 2),
        WordEntry("กา", "p2.docx", 2, 1),
    ]
    assert repo.replace_words(rows) == 3
    assert repo.count([1]) == 2
    assert repo.count([2]) == 1
    assert repo.count([1, 2]) == 3
    assert set(repo.random_words(3, __import__("random").Random(1), [1])) == {"กา", "ขา"}


def test_append_words_without_clearing(tmp_path):
    repo = WordRepository(tmp_path / "words.sqlite3")
    assert repo.replace_words([WordEntry("กา", "p1.docx", 1, 1)]) == 1
    assert repo.add_words([
        WordEntry("กา", "p1.docx", 1, 1),
        WordEntry("กา", "p2.docx", 2, 1),
    ]) == 1

    assert repo.count([1]) == 1
    assert repo.count([2]) == 1
