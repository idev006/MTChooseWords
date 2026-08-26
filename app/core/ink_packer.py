from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from app.core.config import AppConfig


@dataclass(frozen=True)
class InkPlacement:
    text: str
    x: float
    y: float
    size: float
    angle: float


@dataclass(frozen=True)
class InkShape:
    cells: frozenset[tuple[int, int]]
    width: float
    height: float
    min_dx: int = 0
    max_dx: int = 0
    min_dy: int = 0
    max_dy: int = 0


def render_word_image(font_path: Path, word: str, size: float, angle: float, color: str, scale: int = 4):
    """Render shaped Thai glyphs for both layout preview and final PDF output."""
    font = ImageFont.truetype(str(font_path), max(1, round(size * scale)))
    probe = Image.new("RGBA", (max(128, round(size * scale * 16)), max(128, round(size * scale * 4))), (0, 0, 0, 0))
    bbox = ImageDraw.Draw(probe).textbbox((0, 0), word, font=font)
    width = max(8, bbox[2] - bbox[0] + 16 * scale)
    height = max(8, bbox[3] - bbox[1] + 16 * scale)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rgb = ImageColor.getrgb(color)
    ImageDraw.Draw(image).text((8 * scale - bbox[0], 8 * scale - bbox[1]), word, font=font, fill=(*rgb, 255))
    rotated = image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    ink = rotated.getbbox()
    return rotated.crop(ink) if ink else rotated


class InkOccupancy:
    def __init__(self, area, cell_size: float):
        self.left, self.bottom, self.right, self.top = area
        self.cell_size = cell_size
        self.occupied: set[tuple[int, int]] = set()

    def cells_for(self, shape: InkShape, x: float, y: float):
        origin_x = round((x - self.left) / self.cell_size)
        origin_y = round((y - self.bottom) / self.cell_size)
        return {(origin_x + dx, origin_y + dy) for dx, dy in shape.cells}

    def can_place(self, shape: InkShape, x: float, y: float) -> tuple[bool, set[tuple[int, int]]]:
        # Broad-phase checks happen while translating the mask.  The old
        # implementation built a full set and then scanned it again for
        # every candidate, which dominated generation time for 25+ words.
        origin_x = round((x - self.left) / self.cell_size)
        origin_y = round((y - self.bottom) / self.cell_size)
        if not shape.cells:
            return False, set()
        if (self.left + (origin_x + shape.min_dx) * self.cell_size < self.left
                or self.left + (origin_x + shape.max_dx) * self.cell_size > self.right
                or self.bottom + (origin_y + shape.min_dy) * self.cell_size < self.bottom
                or self.bottom + (origin_y + shape.max_dy) * self.cell_size > self.top):
            return False, set()
        cells_list: list[tuple[int, int]] = []
        for dx, dy in shape.cells:
            cx, cy = origin_x + dx, origin_y + dy
            cell = (cx, cy)
            if cell in self.occupied:
                return False, set()
            cells_list.append(cell)
        cells = set(cells_list)
        return True, cells

    def reserve(self, cells: set[tuple[int, int]]) -> None:
        self.occupied.update(cells)

    def release(self, cells: set[tuple[int, int]]) -> None:
        self.occupied.difference_update(cells)


def _render_shape(font_path: Path, word: str, size: float, angle: float, scale: int, cell_size: float) -> InkShape:
    font = ImageFont.truetype(str(font_path), max(1, round(size * scale)))
    probe = Image.new("L", (max(64, round(size * scale * 12)), max(64, round(size * scale * 3))), 0)
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), word, font=font, stroke_width=0)
    width = max(4, bbox[2] - bbox[0] + 12 * scale)
    height = max(4, bbox[3] - bbox[1] + 12 * scale)
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).text((6 * scale - bbox[0], 6 * scale - bbox[1]), word, font=font, fill=255)
    rotated = image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    ink = rotated.getbbox()
    if not ink:
        return InkShape(frozenset(), 0, 0)
    cropped = rotated.crop(ink)
    pixels = cropped.load()
    center_x, center_y = cropped.width / 2, cropped.height / 2
    cells: set[tuple[int, int]] = set()
    for py in range(cropped.height):
        for px in range(cropped.width):
            if pixels[px, py] > 32:
                dx = math.floor(((px - center_x) / scale) / cell_size)
                dy = math.floor(((cropped.height - py - center_y) / scale) / cell_size)
                cells.add((dx, dy))
    # Small dilation compensates for rasterizer/baseline differences between
    # Pillow's layout mask and ReportLab's final vector rendering. This is
    # still based on the ink shape, not on a rectangular bounding box.
    padded = {
        (x + dx, y + dy)
        for x, y in cells
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
    }
    padded_cells = frozenset(padded)
    min_dx = min((item[0] for item in padded_cells), default=0)
    max_dx = max((item[0] for item in padded_cells), default=0)
    min_dy = min((item[1] for item in padded_cells), default=0)
    max_dy = max((item[1] for item in padded_cells), default=0)
    return InkShape(padded_cells, cropped.width / scale, cropped.height / scale, min_dx, max_dx, min_dy, max_dy)


def _candidate_points(area, rng: random.Random, step: float = 14) -> list[tuple[float, float]]:
    """Create natural starting positions using the sunflower golden angle."""
    left, bottom, right, top = area
    center_x, center_y = (left + right) / 2, (bottom + top) / 2
    max_radius = math.hypot(right - left, top - bottom) / 2
    count = min(2200, max(600, round((right - left) * (top - bottom) / (step * step))))
    golden_angle = math.radians(137.507764)
    points = []
    for index in range(count):
        fraction = math.sqrt((index + .5) / count)
        radius = max_radius * fraction
        angle = index * golden_angle + rng.uniform(-.06, .06)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        if left < x < right and bottom < y < top:
            points.append((x + rng.uniform(-step * .2, step * .2), y + rng.uniform(-step * .2, step * .2)))
    # Keep a small boundary supplement so long rotated words can use corners.
    for x in (left + step, right - step):
        for y in (bottom + step, top - step):
            points.append((x, y))
    rng.shuffle(points)
    return points


def _score(x, y, area, centers, target_size: float, size_high: float) -> float:
    left, bottom, right, top = area
    center_x, center_y = (left + right) / 2, (bottom + top) / 2
    center_bias = abs(x - center_x) / max(1, right - left) + abs(y - center_y) / max(1, top - bottom)
    edge = min(x - left, right - x, y - bottom, top - y) / max(1, min(right - left, top - bottom))
    nearest = min((math.hypot(x - cx, y - cy) for cx, cy in centers), default=0)
    spread = min(nearest / max(1, min(right - left, top - bottom)), 1.0)
    # Larger glyphs are intentional focal points.  The previous sign made
    # the optimizer prefer smaller candidates, which was the main source of
    # excessive white space on pages with only 20-30 words.
    size_bonus = (size_high - target_size) / max(1, size_high)
    return center_bias * .06 + (1 - min(edge, 1)) * .12 - spread * 1.25 + size_bonus * .55


def _grow_placements(placements, placement_cells, occupancy, points, area, cfg, size_high, shape_cache, font_path, rng):
    """Enlarge existing words into available local space without overlap."""
    order = sorted(range(len(placements)), key=lambda item: placements[item].size)
    for item_index in order:
        original = placements[item_index]
        occupancy.release(placement_cells[item_index])
        best = (original, placement_cells[item_index])
        # Give every word its own random ceiling so the grow pass does not
        # converge all words toward one dominant font size.
        random_ceiling = rng.uniform(max(original.size, size_high * 0.62), size_high)
        upper = min(random_ceiling, original.size + 30)
        sizes = range(round(upper), round(original.size) + 1, -2)
        for size in sizes:
            if size <= original.size:
                break
            key = (original.text, size, round(original.angle))
            shape = shape_cache.get(key)
            if shape is None:
                shape = _render_shape(font_path, original.text, size, original.angle, 1, occupancy.cell_size)
                shape_cache[key] = shape
            candidates = [(original.x, original.y), *points[:100]]
            valid_choice = None
            for x, y in candidates:
                valid, cells = occupancy.can_place(shape, x, y)
                if valid:
                    score = _score(x, y, area, [(p.x, p.y) for p in placements], size, size_high)
                    valid_choice = (score, InkPlacement(original.text, x, y, size, original.angle), cells)
            if valid_choice is not None:
                best = (valid_choice[1], valid_choice[2])
                break
        placements[item_index] = best[0]
        placement_cells[item_index] = best[1]
        occupancy.reserve(best[1])


def _pack_words_once(words: list[str], area, cfg: AppConfig, font_path: Path, rng: random.Random, progress=None) -> list[InkPlacement]:
    scale = 1
    cell_size = 2.25
    ordered = sorted(words, key=len, reverse=True)
    # A finer candidate field gives the scorer enough options to use the
    # corners and edges instead of forming a compact central cluster.
    points = _candidate_points(area, rng, step=11)
    occupancy = InkOccupancy(area, cell_size)
    placements: list[InkPlacement] = []
    placement_cells: list[set[tuple[int, int]]] = []
    centers: list[tuple[float, float]] = []
    shape_cache: dict[tuple[str, int, int], InkShape] = {}
    # Scale the visual hierarchy continuously with the requested count.  Do
    # not use a hard threshold such as "40 words": users may choose any
    # count, and the same algorithm must remain stable at 10, 37, or 200.
    density_scale = min(1.0, math.sqrt(25 / max(1, len(words))))
    # Keep a real focal hierarchy even on 50-word pages.  The previous
    # linear density cap reduced the upper range too aggressively.
    size_high = min(cfg.font_max_pt, cfg.font_min_pt + 55 * density_scale)
    angle_limit = max(8, round(25 * density_scale))
    angle_high = min(max(abs(cfg.rotation_min), abs(cfg.rotation_max)), angle_limit)

    for index, word in enumerate(ordered, 1):
        choices = []
        rank_ratio = (index - 1) / max(1, len(ordered) - 1)
        word_high = size_high - (size_high - cfg.font_min_pt) * 0.45 * rank_ratio
        for _ in range(5 if len(words) >= 100 else 6):
            size = round(rng.uniform(cfg.font_min_pt, word_high))
            angle = round(rng.uniform(-angle_high, angle_high))
            if angle_high and abs(angle) < 1:
                angle = 1 if rng.random() > .5 else -1
            key = (word, round(size), round(angle))
            shape = shape_cache.get(key)
            if shape is None:
                shape = _render_shape(font_path, word, size, angle, scale, cell_size)
                shape_cache[key] = shape
            for x, y in points[:240]:
                valid, cells = occupancy.can_place(shape, x, y)
                if valid:
                    choices.append((_score(x, y, area, centers, size, size_high), InkPlacement(word, x, y, size, angle), cells))
        if not choices:
            # Last-resort adaptive fit for arbitrary user counts.  Existing
            # placements are preserved, but this word is retried at the
            # configured minimum size and neutral rotation before reporting
            # that the physical page capacity was exceeded.
            for fallback_size in (cfg.font_min_pt, max(cfg.font_min_pt, round(cfg.font_min_pt * 0.9))):
                key = (word, round(fallback_size), 0)
                shape = shape_cache.get(key)
                if shape is None:
                    shape = _render_shape(font_path, word, fallback_size, 0, scale, cell_size)
                    shape_cache[key] = shape
                for x, y in points[:500]:
                    valid, cells = occupancy.can_place(shape, x, y)
                    if valid:
                        choices.append((_score(x, y, area, centers, fallback_size, size_high), InkPlacement(word, x, y, fallback_size, 0), cells))
                if choices:
                    break
        if not choices:
            raise ValueError(f"ไม่สามารถจัดวางคำลำดับที่ {index} ได้")
        _, placement, cells = min(choices, key=lambda item: item[0])
        occupancy.reserve(cells)
        placements.append(placement)
        placement_cells.append(cells)
        centers.append((placement.x, placement.y))
        if progress:
            progress(index, len(words))
    _grow_placements(placements, placement_cells, occupancy, points, area, cfg, size_high, shape_cache, font_path, rng)
    return placements


def _pack_minimum_fit(words: list[str], area, cfg: AppConfig, font_path: Path, rng: random.Random, progress=None) -> list[InkPlacement]:
    """Feasibility pass: restart the whole page at the configured minimum."""
    cell_size = 2.25
    points = _candidate_points(area, rng, step=8)
    occupancy = InkOccupancy(area, cell_size)
    shape_cache: dict[str, InkShape] = {}
    shapes: dict[str, InkShape] = {}
    for word in set(words):
        shapes[word] = _render_shape(font_path, word, cfg.font_min_pt, 0, 1, cell_size)
    ordered = sorted(words, key=lambda word: len(shapes[word].cells), reverse=True)
    placements: list[InkPlacement] = []
    centers: list[tuple[float, float]] = []
    for index, word in enumerate(ordered, 1):
        shape = shapes[word]
        candidates = []
        for x, y in points:
            valid, cells = occupancy.can_place(shape, x, y)
            if valid:
                candidates.append((_score(x, y, area, centers, cfg.font_min_pt, cfg.font_min_pt), x, y, cells))
        if not candidates:
            raise ValueError(f"ไม่สามารถจัดวางคำลำดับที่ {index} แม้ใช้ขนาดฟอนท์ขั้นต่ำ")
        _, x, y, cells = min(candidates, key=lambda item: item[0])
        occupancy.reserve(cells)
        placements.append(InkPlacement(word, x, y, cfg.font_min_pt, 0))
        centers.append((x, y))
        if progress:
            progress(index, len(words))
    return placements


def _pack_varied_fit(words: list[str], area, cfg: AppConfig, font_path: Path, rng: random.Random, progress=None) -> list[InkPlacement]:
    """Reliable fallback that keeps a deliberate large/medium/small hierarchy."""
    cell_size = 2.25
    points = _candidate_points(area, rng, step=8)
    occupancy = InkOccupancy(area, cell_size)
    density_scale = min(1.0, math.sqrt(25 / max(1, len(words))))
    size_high = min(cfg.font_max_pt, cfg.font_min_pt + 55 * density_scale)
    ordered = sorted(words, key=len, reverse=True)
    placements: list[InkPlacement] = []
    placement_cells: list[set[tuple[int, int]]] = []
    centers: list[tuple[float, float]] = []
    shape_cache: dict[tuple[str, int], InkShape] = {}
    for index, word in enumerate(ordered, 1):
        # Fallback still keeps a deliberate hierarchy, but the actual target
        # for each word is randomized so the page does not look templated.
        rank = (index - 1) / max(1, len(ordered) - 1)
        hierarchy_ceiling = size_high - (size_high - cfg.font_min_pt) * 0.35 * rank
        desired = round(rng.uniform(cfg.font_min_pt, hierarchy_ceiling))
        selected = None
        for size in range(desired, cfg.font_min_pt - 1, -2):
            key = (word, size)
            shape = shape_cache.get(key)
            if shape is None:
                shape = _render_shape(font_path, word, size, 0, 1, cell_size)
                shape_cache[key] = shape
            for x, y in points:
                valid, cells = occupancy.can_place(shape, x, y)
                if valid:
                    selected = (InkPlacement(word, x, y, size, 0), cells)
                    break
            if selected:
                break
        if selected is None:
            raise ValueError(f"ไม่สามารถจัดวางคำลำดับที่ {index} ใน varied fit ได้")
        placement, cells = selected
        occupancy.reserve(cells)
        placements.append(placement)
        placement_cells.append(cells)
        centers.append((placement.x, placement.y))
        if progress:
            progress(index, len(words))
    _grow_placements(placements, placement_cells, occupancy, points, area, cfg, size_high, shape_cache, font_path, rng)
    return placements


def pack_words_with_ink(words: list[str], area, cfg: AppConfig, font_path: Path, rng: random.Random, progress=None) -> list[InkPlacement]:
    """Retry independent starts so an unlucky random layout does not fail."""
    last_error: Exception | None = None
    for _ in range(3):
        try:
            seed = rng.randrange(0, 2**63 - 1)
            return _pack_words_once(words, area, cfg, font_path, random.Random(seed), progress)
        except ValueError as exc:
            last_error = exc
    try:
        return _pack_varied_fit(words, area, cfg, font_path, random.Random(rng.randrange(0, 2**63 - 1)), progress)
    except ValueError as exc:
        last_error = exc
    try:
        return _pack_minimum_fit(words, area, cfg, font_path, random.Random(rng.randrange(0, 2**63 - 1)), progress)
    except ValueError as exc:
        last_error = exc
    raise ValueError(
        f"ไม่สามารถจัดวางคำทั้งหมดได้ภายในพื้นที่ A4 (จำนวน {len(words)} คำ) "
        "กรุณาลดจำนวนคำต่อหน้า ลดขนาดฟอนท์ขั้นต่ำ หรือเพิ่มจำนวนหน้า"
    ) from last_error
