from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen

class ToggleSwitch(QWidget):
    """
    Sleek, tactile toggle switch inspired by Raycast and Linear.
    Emits toggled(bool).
    """
    toggled = Signal(bool)

    def __init__(self, checked=False, active_color="#00E5FF", parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._active_color = QColor(active_color)
        self._inactive_color = QColor("#1C2638")
        self._thumb_pos = 18.0 if checked else 2.0

    @Property(float)
    def thumb_pos(self):
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate(checked)
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)

    def _animate(self, target_state: bool):
        target_pos = 20.0 if target_state else 2.0
        self.anim = QPropertyAnimation(self, b"thumb_pos")
        self.anim.setDuration(160)
        self.anim.setStartValue(self._thumb_pos)
        self.anim.setEndValue(target_pos)
        self.anim.start()

    def set_active_color(self, hex_color: str):
        self._active_color = QColor(hex_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Track background
        track_color = self._active_color if self._checked else self._inactive_color
        track_rect = QRectF(0, 1, 40, 20)
        
        # Border
        border_pen = QPen(QColor(self._active_color if self._checked else "#28354D"), 1.0)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_rect, 10, 10)

        # Thumb
        thumb_color = QColor("#080B12") if self._checked else QColor("#94A3B8")
        thumb_rect = QRectF(self._thumb_pos, 3, 16, 16)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(thumb_color))
        painter.drawEllipse(thumb_rect)
