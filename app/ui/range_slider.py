from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class RangeSlider(QWidget):
    """A lightweight horizontal two-handle integer range slider."""

    lowerValueChanged = Signal(int)
    upperValueChanged = Signal(int)

    def __init__(self, minimum: int, maximum: int, lower: int, upper: int, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.lower = max(minimum, min(lower, maximum))
        self.upper = max(self.lower, min(upper, maximum))
        self._active_handle: str | None = None
        self.setMinimumHeight(26)
        self.setMinimumWidth(180)
        self.setMouseTracking(True)

    def values(self) -> tuple[int, int]:
        return self.lower, self.upper

    def _x_for(self, value: int) -> float:
        left, right = 10, max(11, self.width() - 10)
        ratio = (value - self.minimum) / max(1, self.maximum - self.minimum)
        return left + ratio * (right - left)

    def _value_for(self, x: float) -> int:
        left, right = 10, max(11, self.width() - 10)
        ratio = max(0.0, min(1.0, (x - left) / max(1, right - left)))
        return round(self.minimum + ratio * (self.maximum - self.minimum))

    def _set_from_mouse(self, x: float) -> None:
        value = self._value_for(x)
        if self._active_handle == "lower":
            value = min(value, self.upper)
            if value != self.lower:
                self.lower = value
                self.lowerValueChanged.emit(value)
        elif self._active_handle == "upper":
            value = max(value, self.lower)
            if value != self.upper:
                self.upper = value
                self.upperValueChanged.emit(value)
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        lower_distance = abs(event.position().x() - self._x_for(self.lower))
        upper_distance = abs(event.position().x() - self._x_for(self.upper))
        self._active_handle = "lower" if lower_distance <= upper_distance else "upper"
        self._set_from_mouse(event.position().x())

    def mouseMoveEvent(self, event):
        if self._active_handle:
            self._set_from_mouse(event.position().x())

    def mouseReleaseEvent(self, event):
        self._active_handle = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.height() / 2
        left, right = 10, max(11, self.width() - 10)
        lower_x, upper_x = self._x_for(self.lower), self._x_for(self.upper)
        painter.setPen(QPen(Qt.gray, 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(left, center, right, center)
        painter.setPen(QPen(Qt.darkBlue, 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(lower_x, center, upper_x, center)
        painter.setPen(QPen(Qt.lightGray, 1))
        painter.setBrush(Qt.white)
        painter.drawEllipse(lower_x - 8, center - 8, 16, 16)
        painter.drawEllipse(upper_x - 8, center - 8, 16, 16)
