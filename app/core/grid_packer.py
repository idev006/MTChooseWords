from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from reportlab.pdfbase import pdfmetrics

from app.core.config import AppConfig
from app.core.geometry import Point, Rect, grid_span, inside, intersects, rotated_rect

Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class PackedWord:
    text: str
    x: float
    y: float
    size: float
    angle: float
    rect: Rect


class GridIndex:
    """Grid occupancy plus exact rectangle checks for safe, fast packing."""

    def __init__(self, area: Rect, cell_size: float):
        self.area = area
        self.cell_size = cell_size
        self.occupied: dict[tuple[int, int], set[int]] = {}
        self.rectangles: list[Rect] = []

    def can_place(self, rect: Rect) -> bool:
        if not inside(rect, self.area):
            return False
        left, bottom, right, top = grid_span(rect, self.area, self.cell_size)
        nearby: set[int] = set()
        for row in range(bottom, top + 1):
            for column in range(left, right + 1):
                nearby.update(self.occupied.get((column, row), set()))
        return not any(intersects(rect, self.rectangles[index]) for index in nearby)

    def reserve(self, rect: Rect) -> None:
        left, bottom, right, top = grid_span(rect, self.area, self.cell_size)
        index = len(self.rectangles)
        self.rectangles.append(rect)
        for row in range(bottom, top + 1):
            for column in range(left, right + 1):
                self.occupied.setdefault((column, row), set()).add(index)


def _points(area: Rect, cell_size: float, rng: random.Random) -> list[Point]:
    points: list[Point] = []
    x = area[0] + cell_size / 2
    while x <= area[2]:
        y = area[1] + cell_size / 2
        while y <= area[3]:
            points.append((x, y))
            y += cell_size
        x += cell_size
    rng.shuffle(points)
    return points


def _attempts(cfg: AppConfig) -> list[tuple[float, float, float]]:
    attempts = []
    for index in range(24):
        size_max = max(cfg.font_min_pt, cfg.font_max_pt - index * 2)
        rotation_scale = max(0.0, 1.0 - index / 23)
        attempts.append((size_max, cfg.rotation_min * rotation_scale, cfg.rotation_max * rotation_scale))
    return attempts


def _size_levels(start: float, minimum: float):
    size = start
    while size > minimum:
        yield size
        size -= 3
    yield minimum


def pack_words(words: list[str], area: Rect, cfg: AppConfig, font_name: str, rng: random.Random, progress: Progress | None = None) -> list[PackedWord]:
    ordered = sorted(words, key=lambda word: pdfmetrics.stringWidth(word, font_name, cfg.font_max_pt), reverse=True)
    # PDF points are used internally: 3 px at 96 DPI is approximately 2.25 pt.
    grid_size = 3 * 72 / 96
    candidate_step = max(cfg.font_min_pt * 0.9, 16)
    candidates = _points(area, candidate_step, rng)

    attempts = _attempts(cfg)
    # Dense pages should try the compact mode first; this avoids spending time
    # on artistic layouts before the worker can report progress to the UI.
    if len(words) >= 40:
        compact_max = min(cfg.font_max_pt, cfg.font_min_pt + 6)
        compact_angle = min(max(abs(cfg.rotation_min), abs(cfg.rotation_max)) * 0.3, 10)
        # Keep dense pages fast, but retain visible size and angle variation.
        attempts.insert(0, (compact_max, -compact_angle, compact_angle))
        # Compact fallback keeps a visible, small rotation before using 0 degrees.
        fallback_angle = min(max(abs(cfg.rotation_min), abs(cfg.rotation_max)) * 0.1, 3)
        attempts.insert(1, (cfg.font_min_pt, -fallback_angle, fallback_angle))
        # Zero degrees remains the last-resort safety fallback for impossible density.
        attempts.insert(2, (cfg.font_min_pt, 0.0, 0.0))
    for size_max, angle_min, angle_max in attempts:
        attempt_rng = random.Random(rng.random())
        grid = GridIndex(area, grid_size)
        packed: list[PackedWord] = []
        failed = False
        for word in ordered:
            base_size = attempt_rng.uniform(cfg.font_min_pt, size_max)
            accepted = None
            for size in _size_levels(base_size, cfg.font_min_pt):
                text_width = pdfmetrics.stringWidth(word, font_name, size)
                for x, y in candidates:
                    angle = attempt_rng.uniform(angle_min, angle_max)
                    rect = rotated_rect(text_width, size * 1.25, x, y, angle)
                    if grid.can_place(rect):
                        accepted = PackedWord(word, x, y, size, angle, rect)
                        break
                if accepted:
                    break
            if accepted is None:
                failed = True
                break
            grid.reserve(accepted.rect)
            packed.append(accepted)
        if not failed:
            if progress:
                for index in range(1, len(packed) + 1):
                    progress(index, len(packed))
            return packed
    raise ValueError("วางคำไม่ครบตามจำนวนที่กำหนด พื้นที่หน้าไม่เพียงพอภายในช่วงฟอนต์ที่ตั้งไว้")
