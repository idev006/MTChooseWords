import random

from app.core.document_batch import select_document_batches


class FakeRepository:
    def count(self, grades=None):
        return 4

    def random_words(self, amount, rng, grades=None):
        values = ["ก", "ข", "ค", "ง"]
        rng.shuffle(values)
        return values[:amount]


def test_words_are_unique_inside_each_document_but_can_repeat_between_documents():
    documents = select_document_batches(FakeRepository(), 2, 1, 4, random.Random(7))

    assert len(documents) == 2
    assert len(set(documents[0][0])) == 4
    assert len(set(documents[1][0])) == 4
    assert set(documents[0][0]) == set(documents[1][0])
