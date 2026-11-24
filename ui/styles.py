"""
OpenLimiter Pro - 2026 Linear / Raycast Inspired Design System
"""

PREMIUM_2026_THEME_QSS = """
QMainWindow {
    background-color: #080B12;
}

QWidget {
    color: #F1F5F9;
    font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 12px;
}

/* Surface Panels */
QFrame.SurfaceCard {
    background-color: #101725;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 12px 14px;
}

QFrame.MetricSurface {
    background-color: #101725;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 12px 14px;
}

/* Typography */
QLabel {
    background: transparent;
}

QLabel.BrandName {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.3px;
    color: #F1F5F9;
}

QLabel.ProTag {
    font-size: 9px;
    font-weight: 800;
    background-color: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.35);
    color: #00E5FF;
    padding: 2px 5px;
    border-radius: 4px;
}

QLabel.BrandSubtitle {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #8492A6;
    text-transform: uppercase;
}

QLabel.MetricHeader {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #8492A6;
    text-transform: uppercase;
}

QLabel.MetricValue {
    font-size: 22px;
    font-weight: 800;
    color: #F1F5F9;
    font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
    letter-spacing: -0.5px;
}

QLabel.MetricSub {
    font-size: 10.5px;
    font-weight: 600;
    color: #8492A6;
    font-family: "JetBrains Mono", "Cascadia Code", monospace;
}

QLabel.PanelTitle {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: #F1F5F9;
    text-transform: uppercase;
}

QLabel.CalcHint {
    font-size: 10.5px;
    font-weight: 600;
    color: #8492A6;
}

/* Inputs & Form Controls */
QDoubleSpinBox {
    background-color: #090E17;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 14px;
    font-weight: 700;
    color: #F1F5F9;
    font-family: "JetBrains Mono", "Cascadia Code", monospace;
}

QDoubleSpinBox:focus {
    border: 1px solid #00E5FF;
}

QDoubleSpinBox:disabled {
    background-color: #070A10;
    color: #475569;
    border-color: #151D2A;
}

QComboBox {
    background-color: #090E17;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11.5px;
    font-weight: 600;
    color: #CBD5E1;
}

QComboBox:focus {
    border: 1px solid #00E5FF;
}

QComboBox:disabled {
    background-color: #070A10;
    color: #475569;
    border-color: #151D2A;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #101725;
    border: 1px solid #1E293B;
    selection-background-color: #151F30;
    selection-color: #00E5FF;
    color: #F1F5F9;
    border-radius: 6px;
    padding: 4px;
}

/* Segmented Preset Buttons */
QPushButton.PresetBtn {
    background-color: #151F30;
    border: 1px solid #1E293B;
    border-radius: 6px;
    color: #8492A6;
    font-size: 10.5px;
    font-weight: 600;
    padding: 6px 4px;
}

QPushButton.PresetBtn:hover {
    background-color: #1C2638;
    color: #F1F5F9;
    border-color: #2D3D54;
}

QPushButton.PresetBtnActiveDL {
    background-color: rgba(0, 229, 255, 0.08);
    border: 1px solid rgba(0, 229, 255, 0.45);
    border-radius: 6px;
    color: #00E5FF;
    font-size: 10.5px;
    font-weight: 700;
    padding: 6px 4px;
}

QPushButton.PresetBtnActiveUL {
    background-color: rgba(167, 139, 250, 0.08);
    border: 1px solid rgba(167, 139, 250, 0.45);
    border-radius: 6px;
    color: #A78BFA;
    font-size: 10.5px;
    font-weight: 700;
    padding: 6px 4px;
}

/* Primary Action Button (Electric Cyan to Vivid Blue Gradient) */
QPushButton.PrimaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #398BFF);
    border: none;
    border-radius: 10px;
    color: #080B12;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.5px;
    padding: 12px 16px;
}

QPushButton.PrimaryAction:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33ECFF, stop:1 #5B9FFF);
}

QPushButton.PrimaryAction:pressed {
    background: #00C6DC;
}

/* Secondary Action Button */
QPushButton.SecondaryAction {
    background-color: #101725;
    border: 1px solid #1E293B;
    border-radius: 10px;
    color: #8492A6;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 16px;
}

QPushButton.SecondaryAction:hover {
    background-color: #151F30;
    color: #F1F5F9;
    border-color: #334155;
}

/* Status Badges */
QLabel.ElevatedBadge {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #34D399;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 6px;
}

QPushButton.ElevateReqBtn {
    background-color: rgba(57, 139, 255, 0.12);
    border: 1px solid rgba(57, 139, 255, 0.35);
    color: #398BFF;
    font-size: 10.5px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
}

QPushButton.ElevateReqBtn:hover {
    background-color: rgba(57, 139, 255, 0.22);
    border-color: #398BFF;
    color: #FFFFFF;
}

/* Status Footer */
QStatusBar {
    background-color: #080B12;
    color: #64748B;
    font-family: "JetBrains Mono", "Cascadia Code", monospace;
    font-size: 10px;
    font-weight: 600;
    border-top: 1px solid #151F30;
    padding-top: 4px;
}

/* System Tray & Context Menus */
QMenu {
    background-color: #101725;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 6px;
    color: #F1F5F9;
}

QMenu::item {
    background-color: transparent;
    padding: 7px 18px;
    border-radius: 6px;
    color: #F1F5F9;
    font-size: 12px;
}

QMenu::item:selected {
    background-color: #1E293B;
    color: #00E5FF;
}

QMenu::separator {
    height: 1px;
    background: #1E293B;
    margin: 4px 6px;
}

/* Settings CheckBox */
QCheckBox {
    color: #8492A6;
    font-size: 11px;
    font-weight: 600;
    spacing: 8px;
}

QCheckBox:hover {
    color: #F1F5F9;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #1E293B;
    background-color: #101725;
}

QCheckBox::indicator:hover {
    border-color: #00E5FF;
}

QCheckBox::indicator:checked {
    background-color: #00E5FF;
    border-color: #00E5FF;
}
"""
