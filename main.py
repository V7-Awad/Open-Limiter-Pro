import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.styles import PREMIUM_2026_THEME_QSS
from ui.main_window import MainWindow

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("OpenLimiter Pro")
    app.setApplicationDisplayName("OpenLimiter Pro")
    app.setQuitOnLastWindowClosed(False)

    # Set Window and Taskbar Icon
    icon_path = os.path.join(BASE_DIR, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply 2026 High-End Linear/Raycast Dark Theme
    app.setStyleSheet(PREMIUM_2026_THEME_QSS)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    if getattr(window, "start_minimized", False):
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
