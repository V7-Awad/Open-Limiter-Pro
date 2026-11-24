import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QDoubleSpinBox, 
    QComboBox, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

try:
    from core.monitor import GlobalNetworkMonitor
    from core.limiter import GlobalBandwidthLimiter
    from core.utils import is_admin, restart_as_admin, format_speed_dual
    from ui.sparkline import SparklineWidget
    from ui.toggle_switch import ToggleSwitch
except ImportError:
    from ..core.monitor import GlobalNetworkMonitor
    from ..core.limiter import GlobalBandwidthLimiter
    from ..core.utils import is_admin, restart_as_admin, format_speed_dual
    from .sparkline import SparklineWidget
    from .toggle_switch import ToggleSwitch

class MainWindow(QMainWindow):
    """
    OpenLimiter Pro - 2026 High-End System Bandwidth Controller.
    Designed with Linear / Raycast / Vercel aesthetics:
    Less noise. More precision. Maximum control.
    """
    UNIT_MBPS = 0  # Megabits/sec (Fast.com, Speedtest)
    UNIT_MBS = 1   # MegaBytes/sec (Chrome, IDM, Steam)
    UNIT_KBS = 2   # KiloBytes/sec

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OPENLIMITER PRO // BANDWIDTH CONTROLLER")
        self.setFixedSize(500, 730)

        # Core engines
        self.is_elevated = is_admin()
        self.limiter = GlobalBandwidthLimiter()
        self.monitor = GlobalNetworkMonitor(interval=1.0)

        # Store preset buttons for dynamic active styling
        self.dl_preset_btns = []
        self.ul_preset_btns = []

        self._setup_ui()
        self._connect_signals()

        # Start live throughput telemetry
        self.monitor.start()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 18, 22, 16)
        main_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Header: Branding & System State
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Logo Glyphic Mark
        logo_box = QLabel("⚡")
        logo_box.setFixedSize(32, 32)
        logo_box.setAlignment(Qt.AlignCenter)
        logo_box.setStyleSheet("""
            background-color: #101725;
            border: 1px solid #1E293B;
            border-radius: 8px;
            color: #00E5FF;
            font-size: 14px;
            font-weight: 900;
        """)
        header_layout.addWidget(logo_box)

        # Brand Titles
        brand_vbox = QVBoxLayout()
        brand_vbox.setSpacing(1)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        name_lbl = QLabel("OPENLIMITER")
        name_lbl.setProperty("class", "BrandName")
        pro_tag = QLabel("PRO")
        pro_tag.setProperty("class", "ProTag")
        title_row.addWidget(name_lbl)
        title_row.addWidget(pro_tag)
        title_row.addStretch()

        sub_lbl = QLabel("SYSTEM BANDWIDTH CONTROLLER")
        sub_lbl.setProperty("class", "BrandSubtitle")

        brand_vbox.addLayout(title_row)
        brand_vbox.addWidget(sub_lbl)
        header_layout.addLayout(brand_vbox)

        header_layout.addStretch()

        # Elevation State Badge
        if self.is_elevated:
            elevated_badge = QLabel("● ELEVATED")
            elevated_badge.setProperty("class", "ElevatedBadge")
            header_layout.addWidget(elevated_badge)
        else:
            btn_elevate = QPushButton("⚡ RUN AS ADMIN")
            btn_elevate.setProperty("class", "ElevateReqBtn")
            btn_elevate.setCursor(Qt.PointingHandCursor)
            btn_elevate.clicked.connect(self._on_restart_admin)
            header_layout.addWidget(btn_elevate)

        main_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. Live Network Monitoring Grid with Embedded Sparklines
        # -------------------------------------------------------------
        monitor_grid = QHBoxLayout()
        monitor_grid.setSpacing(12)

        # 2A. Download Card
        self.dl_metric_card = QFrame()
        self.dl_metric_card.setProperty("class", "MetricSurface")
        dl_card_layout = QVBoxLayout(self.dl_metric_card)
        dl_card_layout.setContentsMargins(12, 10, 12, 8)
        dl_card_layout.setSpacing(2)

        dl_hdr_row = QHBoxLayout()
        dl_dot = QLabel("●")
        dl_dot.setStyleSheet("color: #00E5FF; font-size: 8px;")
        dl_hdr_lbl = QLabel("LIVE DOWNLOAD")
        dl_hdr_lbl.setProperty("class", "MetricHeader")
        dl_hdr_row.addWidget(dl_dot)
        dl_hdr_row.addWidget(dl_hdr_lbl)
        dl_hdr_row.addStretch()
        dl_card_layout.addLayout(dl_hdr_row)

        self.lbl_dl_val = QLabel("0.0 KB/s")
        self.lbl_dl_val.setProperty("class", "MetricValue")
        dl_card_layout.addWidget(self.lbl_dl_val)

        self.lbl_dl_sub = QLabel("≈ 0.0 Mbps (Fast.com)")
        self.lbl_dl_sub.setProperty("class", "MetricSub")
        dl_card_layout.addWidget(self.lbl_dl_sub)

        # Embedded Live Sparkline
        self.dl_sparkline = SparklineWidget(stroke_color="#00E5FF", fill_alpha=40, max_points=35)
        dl_card_layout.addWidget(self.dl_sparkline)

        monitor_grid.addWidget(self.dl_metric_card)

        # 2B. Upload Card
        self.ul_metric_card = QFrame()
        self.ul_metric_card.setProperty("class", "MetricSurface")
        ul_card_layout = QVBoxLayout(self.ul_metric_card)
        ul_card_layout.setContentsMargins(12, 10, 12, 8)
        ul_card_layout.setSpacing(2)

        ul_hdr_row = QHBoxLayout()
        ul_dot = QLabel("●")
        ul_dot.setStyleSheet("color: #A78BFA; font-size: 8px;")
        ul_hdr_lbl = QLabel("LIVE UPLOAD")
        ul_hdr_lbl.setProperty("class", "MetricHeader")
        ul_hdr_row.addWidget(ul_dot)
        ul_hdr_row.addWidget(ul_hdr_lbl)
        ul_hdr_row.addStretch()
        ul_card_layout.addLayout(ul_hdr_row)

        self.lbl_ul_val = QLabel("0.0 KB/s")
        self.lbl_ul_val.setProperty("class", "MetricValue")
        ul_card_layout.addWidget(self.lbl_ul_val)

        self.lbl_ul_sub = QLabel("≈ 0.0 Mbps")
        self.lbl_ul_sub.setProperty("class", "MetricSub")
        ul_card_layout.addWidget(self.lbl_ul_sub)

        # Embedded Live Sparkline
        self.ul_sparkline = SparklineWidget(stroke_color="#A78BFA", fill_alpha=40, max_points=35)
        ul_card_layout.addWidget(self.ul_sparkline)

        monitor_grid.addWidget(self.ul_metric_card)
        main_layout.addLayout(monitor_grid)

        # -------------------------------------------------------------
        # 3. Download Throttle Control Panel
        # -------------------------------------------------------------
        dl_panel = QFrame()
        dl_panel.setProperty("class", "SurfaceCard")
        dl_vbox = QVBoxLayout(dl_panel)
        dl_vbox.setContentsMargins(14, 12, 14, 12)
        dl_vbox.setSpacing(8)

        # Top row: Icon + Title + Modern Toggle
        dl_top_row = QHBoxLayout()
        dl_icon = QLabel("↓")
        dl_icon.setStyleSheet("color: #00E5FF; font-weight: 900; font-size: 13px;")
        dl_title = QLabel("DOWNLOAD THROTTLE")
        dl_title.setProperty("class", "PanelTitle")
        dl_top_row.addWidget(dl_icon)
        dl_top_row.addWidget(dl_title)
        dl_top_row.addStretch()

        self.dl_toggle = ToggleSwitch(checked=False, active_color="#00E5FF")
        dl_top_row.addWidget(self.dl_toggle)
        dl_vbox.addLayout(dl_top_row)

        # Input Row (Unified Heights)
        dl_inp_row = QHBoxLayout()
        dl_inp_row.setSpacing(8)

        self.dl_spin = QDoubleSpinBox()
        self.dl_spin.setFixedHeight(34)
        self.dl_spin.setRange(0.1, 10000.0)
        self.dl_spin.setDecimals(1)
        self.dl_spin.setValue(4.0)
        self.dl_spin.setEnabled(False)
        self.dl_spin.valueChanged.connect(self._update_dl_hint)

        self.dl_combo = QComboBox()
        self.dl_combo.setFixedHeight(34)
        self.dl_combo.addItems([
            "Mbps (Fast.com / Speedtest)",
            "MB/s (Chrome / IDM)",
            "KB/s (Kilobytes)"
        ])
        self.dl_combo.setEnabled(False)
        self.dl_combo.currentIndexChanged.connect(self._update_dl_hint)

        dl_inp_row.addWidget(self.dl_spin, stretch=3)
        dl_inp_row.addWidget(self.dl_combo, stretch=4)
        dl_vbox.addLayout(dl_inp_row)

        # Live Calculation Hint
        self.lbl_dl_hint = QLabel("💡 4.0 Mbps = ~500 KB/s in Chrome / Downloads")
        self.lbl_dl_hint.setProperty("class", "CalcHint")
        dl_vbox.addWidget(self.lbl_dl_hint)

        # Segmented Preset Buttons
        dl_presets_layout = QHBoxLayout()
        dl_presets_layout.setSpacing(6)
        dl_options = [
            ("1 Mbps", 1.0, self.UNIT_MBPS),
            ("2 Mbps", 2.0, self.UNIT_MBPS),
            ("4 Mbps", 4.0, self.UNIT_MBPS),
            ("10 Mbps", 10.0, self.UNIT_MBPS),
            ("20 Mbps", 20.0, self.UNIT_MBPS)
        ]
        for label, val, u_idx in dl_options:
            btn = QPushButton(label)
            btn.setProperty("class", "PresetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda ch, v=val, u=u_idx, b=btn: self._apply_preset_dl(v, u, b))
            dl_presets_layout.addWidget(btn)
            self.dl_preset_btns.append(btn)
        dl_vbox.addLayout(dl_presets_layout)

        main_layout.addWidget(dl_panel)

        # -------------------------------------------------------------
        # 4. Upload Throttle Control Panel
        # -------------------------------------------------------------
        ul_panel = QFrame()
        ul_panel.setProperty("class", "SurfaceCard")
        ul_vbox = QVBoxLayout(ul_panel)
        ul_vbox.setContentsMargins(14, 12, 14, 12)
        ul_vbox.setSpacing(8)

        # Top row: Icon + Title + Modern Toggle
        ul_top_row = QHBoxLayout()
        ul_icon = QLabel("↑")
        ul_icon.setStyleSheet("color: #A78BFA; font-weight: 900; font-size: 13px;")
        ul_title = QLabel("UPLOAD THROTTLE")
        ul_title.setProperty("class", "PanelTitle")
        ul_top_row.addWidget(ul_icon)
        ul_top_row.addWidget(ul_title)
        ul_top_row.addStretch()

        self.ul_toggle = ToggleSwitch(checked=False, active_color="#A78BFA")
        ul_top_row.addWidget(self.ul_toggle)
        ul_vbox.addLayout(ul_top_row)

        # Input Row (Unified Heights)
        ul_inp_row = QHBoxLayout()
        ul_inp_row.setSpacing(8)

        self.ul_spin = QDoubleSpinBox()
        self.ul_spin.setFixedHeight(34)
        self.ul_spin.setRange(0.1, 10000.0)
        self.ul_spin.setDecimals(1)
        self.ul_spin.setValue(2.0)
        self.ul_spin.setEnabled(False)
        self.ul_spin.valueChanged.connect(self._update_ul_hint)

        self.ul_combo = QComboBox()
        self.ul_combo.setFixedHeight(34)
        self.ul_combo.addItems([
            "Mbps (Fast.com / Speedtest)",
            "MB/s (MegaBytes)",
            "KB/s (Kilobytes)"
        ])
        self.ul_combo.setEnabled(False)
        self.ul_combo.currentIndexChanged.connect(self._update_ul_hint)

        ul_inp_row.addWidget(self.ul_spin, stretch=3)
        ul_inp_row.addWidget(self.ul_combo, stretch=4)
        ul_vbox.addLayout(ul_inp_row)

        # Live Calculation Hint
        self.lbl_ul_hint = QLabel("💡 2.0 Mbps = ~250 KB/s in upload")
        self.lbl_ul_hint.setProperty("class", "CalcHint")
        ul_vbox.addWidget(self.lbl_ul_hint)

        # Segmented Preset Buttons
        ul_presets_layout = QHBoxLayout()
        ul_presets_layout.setSpacing(6)
        ul_options = [
            ("512 Kbps", 512, self.UNIT_KBS),
            ("1 Mbps", 1.0, self.UNIT_MBPS),
            ("2 Mbps", 2.0, self.UNIT_MBPS),
            ("5 Mbps", 5.0, self.UNIT_MBPS),
            ("10 Mbps", 10.0, self.UNIT_MBPS)
        ]
        for label, val, u_idx in ul_options:
            btn = QPushButton(label)
            btn.setProperty("class", "PresetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda ch, v=val, u=u_idx, b=btn: self._apply_preset_ul(v, u, b))
            ul_presets_layout.addWidget(btn)
            self.ul_preset_btns.append(btn)
        ul_vbox.addLayout(ul_presets_layout)

        main_layout.addWidget(ul_panel)

        # Toggle bindings
        self.dl_toggle.toggled.connect(self._on_dl_toggled)
        self.ul_toggle.toggled.connect(self._on_ul_toggled)

        # -------------------------------------------------------------
        # 5. Primary & Secondary Action Buttons
        # -------------------------------------------------------------
        actions_vbox = QVBoxLayout()
        actions_vbox.setSpacing(8)

        self.btn_engage = QPushButton("⚡ ENGAGE BANDWIDTH LIMIT")
        self.btn_engage.setProperty("class", "PrimaryAction")
        self.btn_engage.setCursor(Qt.PointingHandCursor)
        self.btn_engage.clicked.connect(self._on_engage_clicked)
        actions_vbox.addWidget(self.btn_engage)

        self.btn_unrestrict = QPushButton("✕ UNRESTRICT SPEED")
        self.btn_unrestrict.setProperty("class", "SecondaryAction")
        self.btn_unrestrict.setCursor(Qt.PointingHandCursor)
        self.btn_unrestrict.clicked.connect(self._on_unrestrict_clicked)
        actions_vbox.addWidget(self.btn_unrestrict)

        main_layout.addLayout(actions_vbox)

        # -------------------------------------------------------------
        # 6. Technical Status Footer
        # -------------------------------------------------------------
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._load_saved_values()
        self._update_dl_hint()
        self._update_ul_hint()
        self._update_status_display()

    def _connect_signals(self):
        self.monitor.speed_updated.connect(self._on_speed_updated)

    def _on_speed_updated(self, dl_bytes: float, ul_bytes: float):
        dl_byte_str, dl_bit_str = format_speed_dual(dl_bytes)
        ul_byte_str, ul_bit_str = format_speed_dual(ul_bytes)

        # Update numbers
        self.lbl_dl_val.setText(dl_byte_str)
        self.lbl_dl_sub.setText(f"≈ {dl_bit_str} (Fast.com)")

        self.lbl_ul_val.setText(ul_byte_str)
        self.lbl_ul_sub.setText(f"≈ {ul_bit_str}")

        # Update sparkline graphs
        self.dl_sparkline.add_point(dl_bytes)
        self.ul_sparkline.add_point(ul_bytes)

    def _on_dl_toggled(self, checked: bool):
        self.dl_spin.setEnabled(checked)
        self.dl_combo.setEnabled(checked)
        self.lbl_dl_hint.setVisible(checked)

    def _on_ul_toggled(self, checked: bool):
        self.ul_spin.setEnabled(checked)
        self.ul_combo.setEnabled(checked)
        self.lbl_ul_hint.setVisible(checked)

    def _update_dl_hint(self):
        val = self.dl_spin.value()
        mode = self.dl_combo.currentIndex()
        if mode == self.UNIT_MBPS:
            kb = int(val * 1024 / 8)
            mb = kb / 1024
            self.lbl_dl_hint.setText(f"💡 {val:.1f} Mbps = ~{kb} KB/s ({mb:.2f} MB/s) in Chrome / Downloads")
        elif mode == self.UNIT_MBS:
            mbps = val * 8
            self.lbl_dl_hint.setText(f"💡 {val:.1f} MB/s = ~{mbps:.1f} Mbps on Fast.com / Speedtest")
        else: # KB/s
            mbps = (val * 8) / 1024
            self.lbl_dl_hint.setText(f"💡 {val:.0f} KB/s = ~{mbps:.2f} Mbps on Fast.com / Speedtest")

    def _update_ul_hint(self):
        val = self.ul_spin.value()
        mode = self.ul_combo.currentIndex()
        if mode == self.UNIT_MBPS:
            kb = int(val * 1024 / 8)
            self.lbl_ul_hint.setText(f"💡 {val:.1f} Mbps = ~{kb} KB/s in upload")
        elif mode == self.UNIT_MBS:
            mbps = val * 8
            self.lbl_ul_hint.setText(f"💡 {val:.1f} MB/s = ~{mbps:.1f} Mbps on Speedtest")
        else:
            mbps = (val * 8) / 1024
            self.lbl_ul_hint.setText(f"💡 {val:.0f} KB/s = ~{mbps:.2f} Mbps on Speedtest")

    def _apply_preset_dl(self, val: float, unit_idx: int, clicked_btn: QPushButton):
        self.dl_toggle.setChecked(True)
        self.dl_combo.setCurrentIndex(unit_idx)
        self.dl_spin.setValue(val)
        self._update_dl_hint()

        # Update button visual state
        for btn in self.dl_preset_btns:
            btn.setProperty("class", "PresetBtnActiveDL" if btn == clicked_btn else "PresetBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _apply_preset_ul(self, val: float, unit_idx: int, clicked_btn: QPushButton):
        self.ul_toggle.setChecked(True)
        self.ul_combo.setCurrentIndex(unit_idx)
        self.ul_spin.setValue(val)
        self._update_ul_hint()

        # Update button visual state
        for btn in self.ul_preset_btns:
            btn.setProperty("class", "PresetBtnActiveUL" if btn == clicked_btn else "PresetBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _get_dl_in_kb(self) -> int:
        val = self.dl_spin.value()
        mode = self.dl_combo.currentIndex()
        if mode == self.UNIT_MBPS:
            return max(10, int(val * 1024 / 8))
        elif mode == self.UNIT_MBS:
            return max(10, int(val * 1024))
        else:
            return max(10, int(val))

    def _get_ul_in_kb(self) -> int:
        val = self.ul_spin.value()
        mode = self.ul_combo.currentIndex()
        if mode == self.UNIT_MBPS:
            return max(10, int(val * 1024 / 8))
        elif mode == self.UNIT_MBS:
            return max(10, int(val * 1024))
        else:
            return max(10, int(val))

    def _load_saved_values(self):
        dl_kb = self.limiter.dl_limit_kb
        ul_kb = self.limiter.ul_limit_kb

        if dl_kb and dl_kb > 0:
            self.dl_toggle.setChecked(True)
            mbps = (dl_kb * 8) / 1024
            self.dl_spin.setValue(round(mbps, 1))
            self.dl_combo.setCurrentIndex(self.UNIT_MBPS)

        if ul_kb and ul_kb > 0:
            self.ul_toggle.setChecked(True)
            mbps = (ul_kb * 8) / 1024
            self.ul_spin.setValue(round(mbps, 1))
            self.ul_combo.setCurrentIndex(self.UNIT_MBPS)

    def _on_engage_clicked(self):
        if not self.is_elevated:
            res = QMessageBox.warning(
                self,
                "Elevation Required",
                "Applying Windows system-wide bandwidth limits requires Administrator privileges.\n\n"
                "Relaunch OpenLimiter as Administrator now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self._on_restart_admin()
            return

        dl_kb = self._get_dl_in_kb() if self.dl_toggle.isChecked() else None
        ul_kb = self._get_ul_in_kb() if self.ul_toggle.isChecked() else None

        success = self.limiter.apply_global_limits(dl_kb, ul_kb)
        if success:
            parts = []
            if dl_kb:
                dl_mbps = (dl_kb * 8) / 1024
                parts.append(f"DL: {dl_mbps:.1f} Mbps ({dl_kb} KB/s)")
            else:
                parts.append("DL: MAX")

            if ul_kb:
                ul_mbps = (ul_kb * 8) / 1024
                parts.append(f"UL: {ul_mbps:.1f} Mbps ({ul_kb} KB/s)")
            else:
                parts.append("UL: MAX")

            self.status_bar.showMessage(f"SYS // ENGAGED: {' | '.join(parts)}", 8000)
            self._update_status_display()
        else:
            QMessageBox.critical(self, "Error", "Failed to apply bandwidth limit policies.")

    def _on_unrestrict_clicked(self):
        if not self.is_elevated:
            self._on_restart_admin()
            return

        self.dl_toggle.setChecked(False)
        self.ul_toggle.setChecked(False)
        self.limiter.remove_all_limits()
        self.status_bar.showMessage("SYS // RESTORED: UNRESTRICTED THROUGHPUT", 8000)
        self._update_status_display()

        # Reset preset button states
        for btn in self.dl_preset_btns:
            btn.setProperty("class", "PresetBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        for btn in self.ul_preset_btns:
            btn.setProperty("class", "PresetBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _update_status_display(self):
        dl_kb = self.limiter.dl_limit_kb
        ul_kb = self.limiter.ul_limit_kb
        if dl_kb or ul_kb:
            txt_dl = f"{(dl_kb*8)/1024:.1f} Mbps" if dl_kb else "MAX"
            txt_ul = f"{(ul_kb*8)/1024:.1f} Mbps" if ul_kb else "MAX"
            self.status_bar.showMessage(f"SYS // ENGAGED: DL {txt_dl} | UL {txt_ul}   [ENGINE: KERNEL + SHAPER]")
        else:
            self.status_bar.showMessage("SYS // UNRESTRICTED (MAX THROUGHPUT)   [ENGINE: READY]")

    def _on_restart_admin(self):
        self.monitor.stop()
        restart_as_admin()

    def closeEvent(self, event):
        self.monitor.stop()
        self.limiter.remove_all_limits()
        event.accept()
