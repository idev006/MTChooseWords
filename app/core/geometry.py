from __future__ import annotations

import math
from typing import TypeAlias

Rect: TypeAlias = tuple[float, float, float, float]
Point: TypeAlias = tuple[float, float]


def rotated_rect(text_width: float, text_height: float, x: float, y: float, angle: float, pad: float = 2) -> Rect:
    width = text_width + pad * 2
    height = text_height + pad * 2
    radians = math.radians(angle)
    rotated_width = abs(width * math.cos(radians)) + abs(height * math.sin(radians))
    rotated_height = abs(width * math.sin(radians)) + abs(height * math.cos(radians))
    return (x - rotated_width / 2, y - rotated_height / 2,
            x + rotated_width / 2, y + rotated_height / 2)


def intersects(first: Rect, second: Rect) -> bool:
    return first[0] < second[2] and first[2] > second[0] and first[1] < second[3] and first[3] > second[1]


def inside(rect: Rect, area: Rect) -> bool:
    return rect[0] >= area[0] and rect[1] >= area[1] and rect[2] <= area[2] and rect[3] <= area[3]


def grid_span(rect: Rect, area: Rect, cell_size: float) -> tuple[int, int, int, int]:
    """Convert a rectangle to inclusive grid coordinates."""
    left = math.floor((rect[0] - area[0]) / cell_size)
    right = math.ceil((rect[2] - area[0]) / cell_size) - 1
    bottom = math.floor((rect[1] - area[1]) / cell_size)
    top = math.ceil((rect[3] - area[1]) / cell_size) - 1
    return left, bottom, max(left, right), max(bottom, top)
