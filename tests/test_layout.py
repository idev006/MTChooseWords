import random
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.core.config import AppConfig
from app.core.pdf_generator import _intersects, _rect_for, place_words


def test_layout_returns_requested_words_without_duplicate_rectangles():
    cfg = AppConfig(font_min_pt=12, font_max_pt=18, colors=["#123456"])
    placements = place_words(["ก", "ข", "ค", "ง"], 595, 841, cfg, "Helvetica", random.Random(7))
    assert len(placements) == 4
    assert all(item.color == "#123456" for item in placements)


def test_layout_bounding_boxes_do_not_intersect():
    cfg = AppConfig(font_min_pt=8, font_max_pt=12, colors=["#123456"])
    words = list("กขคงจฉชซฌญฎฏฐฑฒณดตถ")
    placements = place_words(words, 595, 841, cfg, "Helvetica", random.Random(11))
    boxes = [_rect_for(item.text, item.x, item.y, item.size, item.angle, "Helvetica") for item in placements]
    assert all(not _intersects(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:])


def test_layout_handles_thirty_words_with_project_font():
    root = Path(__file__).parents[1]
    font = next((root / "app/assets/fonts").glob("*.ttf"))
    pdfmetrics.registerFont(TTFont("LayoutSmokeFont", str(font)))
    cfg = AppConfig(font_min_pt=20, font_max_pt=60, colors=["#123456"])
    words = [f"คำ{i}" for i in range(30)]
    placements = place_words(words, 595.27, 841, cfg, "LayoutSmokeFont", random.Random(7))
    assert len(placements) == 30


def test_layout_handles_one_hundred_words_in_landscape():
    root = Path(__file__).parents[1]
    font = next((root / "app/assets/fonts").glob("*.ttf"))
    pdfmetrics.registerFont(TTFont("DenseLayoutSmokeFont", str(font)))
    cfg = AppConfig(
        font_min_pt=20,
        font_max_pt=60,
        rotation_min=-30,
        rotation_max=30,
        colors=["#123456"],
    )
    words = [f"คำ{i}" for i in range(100)]
    placements = place_words(words, 841.89, 595.27, cfg, "DenseLayoutSmokeFont", random.Random(1))
    assert len(placements) == 100
    assert min(item.size for item in placements) >= cfg.font_min_pt


def test_dense_layout_keeps_font_sizes_varied_when_space_allows():
    root = Path(__file__).parents[1]
    font = next((root / "app/assets/fonts").glob("*.ttf"))
    pdfmetrics.registerFont(TTFont("VariedDenseLayoutFont", str(font)))
    cfg = AppConfig(font_min_pt=25, font_max_pt=70, rotation_min=-30, rotation_max=30, colors=["#123456"])
    placements = place_words([f"คำ{i}" for i in range(50)], 841.89, 595.27, cfg, "VariedDenseLayoutFont", random.Random(1))
    assert len({round(item.size, 2) for item in placements}) > 1
    assert any(abs(item.angle) > 0.5 for item in placements)


def test_production_font_path_uses_ink_layout_with_variation():
    root = Path(__file__).parents[1]
    font = next((root / "app/assets/fonts").glob("*.ttf"))
    cfg = AppConfig(font_min_pt=20, font_max_pt=60, rotation_min=-30, rotation_max=30, colors=["#123456"])
    placements = place_words([f"คำ{i}" for i in range(20)], 841.89, 595.27, cfg, "Unused", random.Random(3), font_path=font)
    assert len(placements) == 20
    assert len({round(item.size, 2) for item in placements}) > 1
    assert any(abs(item.angle) > 0.5 for item in placements)
