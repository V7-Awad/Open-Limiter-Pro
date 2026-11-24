from collections import deque
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath

class SparklineWidget(QWidget):
    """
    Ultra-clean, high-performance real-time sparkline graph for network telemetry.
    Inspired by Linear, Raycast, and Datadog monitoring widgets.
    """
    def __init__(self, stroke_color="#00E5FF", color=None, fill_alpha=40, max_points=35, height=34, parent=None):
        super().__init__(parent)
        if color is not None:
            stroke_color = color
        self.stroke_color = QColor(stroke_color) if not isinstance(stroke_color, QColor) else stroke_color
        self.fill_alpha = fill_alpha
        self.max_points = max_points
        self.history = deque([0.0] * max_points, maxlen=max_points)
        self.setFixedHeight(height)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def add_point(self, value: float):
        self.history.append(value)
        self.update()

    def set_color(self, hex_color: str):
        self.stroke_color = QColor(hex_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        count = len(self.history)
        if count < 2:
            return

        max_val = max(self.history)
        if max_val <= 0:
            max_val = 1.0  # baseline

        # Build points
        points = []
        step = w / (self.max_points - 1)
        for i, val in enumerate(self.history):
            x = i * step
            # Scale y: keep a 3px padding top/bottom
            norm = min(1.0, max(0.0, val / max_val))
            y = (h - 4.0) - (norm * (h - 8.0))
            points.append(QPointF(x, y))

        # Path for stroke
        path = QPainterPath()
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)

        # Path for fill gradient
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        # Gradient fill
        grad = QLinearGradient(0, 0, 0, h)
        c_top = QColor(self.stroke_color)
        c_top.setAlpha(self.fill_alpha)
        c_bottom = QColor(self.stroke_color)
        c_bottom.setAlpha(0)
        grad.setColorAt(0.0, c_top)
        grad.setColorAt(1.0, c_bottom)

        painter.fillPath(fill_path, QBrush(grad))

        # Stroke line
        pen = QPen(self.stroke_color, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

        # Subtle current-point glow at the end
        if points:
            last = points[-1]
            painter.setPen(Qt.NoPen)
            glow_c = QColor(self.stroke_color)
            glow_c.setAlpha(80)
            painter.setBrush(QBrush(glow_c))
            painter.drawEllipse(last, 4.0, 4.0)
            painter.setBrush(QBrush(self.stroke_color))
            painter.drawEllipse(last, 2.0, 2.0)
