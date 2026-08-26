from __future__ import annotations

import random


def select_document_batches(repository, document_sets: int, pages_per_set: int, words_per_page: int, rng: random.Random, grades: list[int] | None = None):
    """Select unique words within each PDF; different PDFs may overlap."""
    words_per_document = pages_per_set * words_per_page
    available = repository.count(grades)
    if words_per_document > available:
        raise ValueError(
            f"ต้องการ {words_per_document} คำต่อไฟล์ แต่มีคำไม่ซ้ำ {available} คำ"
        )
    documents = []
    for _ in range(document_sets):
        words = repository.random_words(words_per_document, rng, grades)
        documents.append([
            words[index:index + words_per_page]
            for index in range(0, words_per_document, words_per_page)
        ])
    return documents
