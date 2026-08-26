from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

from app.core.config import AppConfig
from app.core.geometry import intersects, rotated_rect
from app.core.grid_packer import pack_words
from app.core.ink_packer import pack_words_with_ink, render_word_image


@dataclass(frozen=True)
class Placement:
    text: str
    x: float
    y: float
    size: float
    angle: float
    color: str


def _rect_for(text: str, x: float, y: float, size: float, angle: float, font: str, pad: float = 2):
    width = pdfmetrics.stringWidth(text, font, size)
    return rotated_rect(width, size * 1.25, x, y, angle, pad)


_intersects = intersects


def place_words(words: list[str], width: float, height: float, cfg: AppConfig, font_name: str, rng: random.Random, progress=None, font_path: Path | None = None) -> list[Placement]:
    top_reserved = (cfg.title_margin_top_px + cfg.title_margin_bottom_px + cfg.title_padding_px * 2) * 0.75 + cfg.title_font_size * 1.35 + cfg.page_margin_pt
    safe = (cfg.page_margin_pt, cfg.page_margin_pt, width - cfg.page_margin_pt, height - top_reserved)
    if font_path is not None:
        packed = pack_words_with_ink(words, safe, cfg, font_path, rng, progress)
        return [Placement(item.text, item.x, item.y, item.size, item.angle, rng.choice(cfg.colors)) for item in packed]
    packed = pack_words(words, safe, cfg, font_name, rng, progress)
    return [Placement(item.text, item.x, item.y, item.size, item.angle, rng.choice(cfg.colors)) for item in packed]


def generate_pdf(words_by_page: list[list[str]], output: Path, cfg: AppConfig, font_path: Path, progress=None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    font_name = "MTChooseWordsFont"
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    page_size = A4 if cfg.orientation == "portrait" else landscape(A4)
    canvas = Canvas(str(output), pagesize=page_size)
    width, height = page_size
    rng = random.Random(cfg.seed or None)
    for words in words_by_page:
        if font_path:
            title_image = render_word_image(font_path, cfg.title, cfg.title_font_size, 0, cfg.title_color)
            title_width, title_height = title_image.size[0] / 4, title_image.size[1] / 4
            top_margin = cfg.title_margin_top_px * 0.75
            bottom_margin = cfg.title_margin_bottom_px * 0.75
            padding = cfg.title_padding_px * 0.75
            title_y = height - cfg.page_margin_pt - top_margin - padding - title_height / 2
            canvas.setFillColor(colors.HexColor(cfg.title_bgcolor))
            canvas.roundRect(width / 2 - title_width / 2 - padding, title_y - title_height / 2 - padding, title_width + padding * 2, title_height + padding * 2, min(8, padding), fill=1, stroke=0)
            canvas.drawImage(ImageReader(title_image), width / 2 - title_width / 2, title_y - title_height / 2, title_width, title_height, mask="auto")
        else:
            top_margin = cfg.title_margin_top_px * 0.75
            bottom_margin = cfg.title_margin_bottom_px * 0.75
            padding = cfg.title_padding_px * 0.75
            title_y = height - cfg.page_margin_pt - top_margin - padding - cfg.title_font_size * 0.5
            title_width = pdfmetrics.stringWidth(cfg.title, font_name, cfg.title_font_size)
            title_height = cfg.title_font_size * 1.15
            canvas.setFillColor(colors.HexColor(cfg.title_bgcolor))
            canvas.roundRect(width / 2 - title_width / 2 - padding, title_y - cfg.title_font_size * 0.35 - padding, title_width + padding * 2, title_height + padding * 2, min(8, padding), fill=1, stroke=0)
            canvas.setFillColor(colors.HexColor(cfg.title_color))
            canvas.setFont(font_name, cfg.title_font_size)
            canvas.drawCentredString(width / 2, title_y - cfg.title_font_size * 0.35, cfg.title)
        placements = place_words(words, width, height, cfg, font_name, rng, progress, font_path)
        for item in placements:
            if font_path:
                word_image = render_word_image(font_path, item.text, item.size, item.angle, item.color)
                word_width, word_height = word_image.size[0] / 4, word_image.size[1] / 4
                canvas.drawImage(ImageReader(word_image), item.x - word_width / 2, item.y - word_height / 2, word_width, word_height, mask="auto")
            else:
                canvas.saveState()
                canvas.translate(item.x, item.y)
                canvas.rotate(item.angle)
                canvas.setFillColor(colors.HexColor(item.color))
                canvas.setFont(font_name, item.size)
                canvas.drawCentredString(0, -item.size * 0.35, item.text)
                canvas.restoreState()
        canvas.showPage()
    canvas.save()


class ReportLabPdfExporter:
    """Production adapter behind the PdfExporter contract."""

    def export(self, words_by_page, output, config, font_path, progress=None) -> None:
        generate_pdf(words_by_page, output, config, font_path, progress)
