import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QDoubleSpinBox, 
    QComboBox, QMessageBox, QStatusBar, QCheckBox, QSystemTrayIcon, QMenu,
    QApplication, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QAction

try:
    from core.monitor import GlobalNetworkMonitor
    from core.limiter import GlobalBandwidthLimiter
    from core.utils import (
        is_admin, restart_as_admin, format_speed_dual,
        load_config, save_config, set_autostart, is_autostart_enabled,
        create_desktop_shortcut
    )
    from ui.sparkline import SparklineWidget
    from ui.toggle_switch import ToggleSwitch
except ImportError:
    from ..core.monitor import GlobalNetworkMonitor
    from ..core.limiter import GlobalBandwidthLimiter
    from ..core.utils import (
        is_admin, restart_as_admin, format_speed_dual,
        load_config, save_config, set_autostart, is_autostart_enabled,
        create_desktop_shortcut
    )
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
        self.setToolTip(
            "Shared system limits: downloads use the Windows system proxy; uploads use Windows QoS. "
            "Apps that bypass the system proxy may not follow the download limit."
        )

        # Application state
        self.config = load_config()
        self.config["autostart"] = is_autostart_enabled()
        self._force_exit = False
        self.tray_icon = None

        # Core engines
        self.is_elevated = is_admin()
        self.limiter = GlobalBandwidthLimiter()
        self.monitor = GlobalNetworkMonitor(interval=1.0)

        # Store preset buttons for dynamic active styling
        self.dl_preset_btns = []
        self.ul_preset_btns = []

        self._setup_ui()
        self._setup_tray()
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

        # UAC State Pill
        if self.is_elevated:
            elev_badge = QLabel("● ELEVATED")
            elev_badge.setProperty("class", "ElevatedBadge")
            header_layout.addWidget(elev_badge)
        else:
            self.elev_btn = QPushButton("🛡 RUN ELEVATED")
            self.elev_btn.setProperty("class", "ElevateReqBtn")
            self.elev_btn.setCursor(Qt.PointingHandCursor)
            self.elev_btn.clicked.connect(self._on_restart_admin)
            header_layout.addWidget(self.elev_btn)

        main_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. Live Network Telemetry
        # -------------------------------------------------------------
        telemetry_frame = QFrame()
        telemetry_frame.setProperty("class", "MetricSurface")
        telemetry_layout = QHBoxLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(14, 12, 14, 12)
        telemetry_layout.setSpacing(16)

        # Download Metric Block
        dl_metric_vbox = QVBoxLayout()
        dl_metric_vbox.setSpacing(2)

        dl_header_row = QHBoxLayout()
        dl_dot = QLabel("●")
        dl_dot.setStyleSheet("color: #00E5FF; font-size: 10px;")
        dl_lbl = QLabel("LIVE DOWNLOAD")
        dl_lbl.setProperty("class", "MetricHeader")
        dl_header_row.addWidget(dl_dot)
        dl_header_row.addWidget(dl_lbl)
        dl_header_row.addStretch()
        dl_metric_vbox.addLayout(dl_header_row)

        self.lbl_dl_val = QLabel("0.0 KB/s")
        self.lbl_dl_val.setProperty("class", "MetricValue")
        dl_metric_vbox.addWidget(self.lbl_dl_val)

        self.lbl_dl_sub = QLabel("≈ 0.0 Mbps (Fast.com)")
        self.lbl_dl_sub.setProperty("class", "MetricSub")
        dl_metric_vbox.addWidget(self.lbl_dl_sub)

        self.dl_sparkline = SparklineWidget(stroke_color="#00E5FF", height=36)
        dl_metric_vbox.addWidget(self.dl_sparkline)

        telemetry_layout.addLayout(dl_metric_vbox, 1)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #1E293B;")
        telemetry_layout.addWidget(div)

        # Upload Metric Block
        ul_metric_vbox = QVBoxLayout()
        ul_metric_vbox.setSpacing(2)

        ul_header_row = QHBoxLayout()
        ul_dot = QLabel("●")
        ul_dot.setStyleSheet("color: #A78BFA; font-size: 10px;")
        ul_lbl = QLabel("LIVE UPLOAD")
        ul_lbl.setProperty("class", "MetricHeader")
        ul_header_row.addWidget(ul_dot)
        ul_header_row.addWidget(ul_lbl)
        ul_header_row.addStretch()
        ul_metric_vbox.addLayout(ul_header_row)

        self.lbl_ul_val = QLabel("0.0 KB/s")
        self.lbl_ul_val.setProperty("class", "MetricValue")
        ul_metric_vbox.addWidget(self.lbl_ul_val)

        self.lbl_ul_sub = QLabel("≈ 0.0 Mbps")
        self.lbl_ul_sub.setProperty("class", "MetricSub")
        ul_metric_vbox.addWidget(self.lbl_ul_sub)

        self.ul_sparkline = SparklineWidget(stroke_color="#A78BFA", height=36)
        ul_metric_vbox.addWidget(self.ul_sparkline)

        telemetry_layout.addLayout(ul_metric_vbox, 1)

        main_layout.addWidget(telemetry_frame)

        # -------------------------------------------------------------
        # 3. Download Throttle Control Card
        # -------------------------------------------------------------
        dl_panel = QFrame()
        dl_panel.setProperty("class", "SurfaceCard")
        dl_vbox = QVBoxLayout(dl_panel)
        dl_vbox.setContentsMargins(14, 12, 14, 12)
        dl_vbox.setSpacing(10)

        # Top Control Row
        dl_top_row = QHBoxLayout()
        dl_title_icon = QLabel("⬇")
        dl_title_icon.setStyleSheet("color: #398BFF; font-size: 13px; font-weight: bold;")
        dl_title_lbl = QLabel("DOWNLOAD THROTTLE")
        dl_title_lbl.setProperty("class", "ControlHeader")

        dl_top_row.addWidget(dl_title_icon)
        dl_top_row.addWidget(dl_title_lbl)
        dl_top_row.addStretch()

        self.dl_toggle = ToggleSwitch(active_color="#00E5FF")
        self.dl_toggle.setToolTip(
            "Shared download limit through the Windows system proxy. Apps that bypass that proxy are not shaped."
        )
        self.dl_toggle.setChecked(True)
        dl_toggle_lbl = QLabel("ENABLE")
        dl_toggle_lbl.setStyleSheet("color: #8492A6; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
        dl_top_row.addWidget(self.dl_toggle)
        dl_top_row.addWidget(dl_toggle_lbl)
        dl_vbox.addLayout(dl_top_row)

        # Input Row: SpinBox + Unit Combo
        dl_input_row = QHBoxLayout()
        dl_input_row.setSpacing(8)

        self.dl_spin = QDoubleSpinBox()
        self.dl_spin.setRange(0.1, 100000.0)
        self.dl_spin.setDecimals(1)
        self.dl_spin.setValue(2.0)
        self.dl_spin.setSingleStep(0.5)
        dl_input_row.addWidget(self.dl_spin, 1)

        self.dl_combo = QComboBox()
        self.dl_combo.addItems(["Mbps (Speedtest/Fast)", "MB/s (Browser)", "KB/s"])
        self.dl_combo.setCurrentIndex(self.UNIT_MBPS)
        dl_input_row.addWidget(self.dl_combo)

        dl_vbox.addLayout(dl_input_row)

        # Live calculation hint
        self.lbl_dl_hint = QLabel("")
        self.lbl_dl_hint.setProperty("class", "CalcHint")
        dl_vbox.addWidget(self.lbl_dl_hint)

        # Quick Preset Buttons
        dl_presets_layout = QHBoxLayout()
        dl_presets_layout.setSpacing(6)
        dl_presets = [
            ("1 Mbps", 1.0, self.UNIT_MBPS),
            ("2 Mbps", 2.0, self.UNIT_MBPS),
            ("4 Mbps", 4.0, self.UNIT_MBPS),
            ("8 Mbps", 8.0, self.UNIT_MBPS),
            ("16 Mbps", 16.0, self.UNIT_MBPS),
        ]
        for label, val, u_idx in dl_presets:
            btn = QPushButton(label)
            btn.setProperty("class", "PresetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda ch, v=val, u=u_idx, b=btn: self._apply_preset_dl(v, u, b))
            dl_presets_layout.addWidget(btn)
            self.dl_preset_btns.append(btn)
        dl_vbox.addLayout(dl_presets_layout)

        main_layout.addWidget(dl_panel)

        # -------------------------------------------------------------
        # 4. Upload Throttle Control Card
        # -------------------------------------------------------------
        ul_panel = QFrame()
        ul_panel.setProperty("class", "SurfaceCard")
        ul_vbox = QVBoxLayout(ul_panel)
        ul_vbox.setContentsMargins(14, 12, 14, 12)
        ul_vbox.setSpacing(10)

        # Top Control Row
        ul_top_row = QHBoxLayout()
        ul_title_icon = QLabel("⬆")
        ul_title_icon.setStyleSheet("color: #A78BFA; font-size: 13px; font-weight: bold;")
        ul_title_lbl = QLabel("UPLOAD THROTTLE")
        ul_title_lbl.setProperty("class", "ControlHeader")

        ul_top_row.addWidget(ul_title_icon)
        ul_top_row.addWidget(ul_title_lbl)
        ul_top_row.addStretch()

        self.ul_toggle = ToggleSwitch(active_color="#00E5FF")
        self.ul_toggle.setToolTip("Shared upload limit enforced with Windows QoS.")
        self.ul_toggle.setChecked(True)
        ul_toggle_lbl = QLabel("ENABLE")
        ul_toggle_lbl.setStyleSheet("color: #8492A6; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
        ul_top_row.addWidget(self.ul_toggle)
        ul_top_row.addWidget(ul_toggle_lbl)
        ul_vbox.addLayout(ul_top_row)

        # Input Row: SpinBox + Unit Combo
        ul_input_row = QHBoxLayout()
        ul_input_row.setSpacing(8)

        self.ul_spin = QDoubleSpinBox()
        self.ul_spin.setRange(0.1, 100000.0)
        self.ul_spin.setDecimals(1)
        self.ul_spin.setValue(1.0)
        self.ul_spin.setSingleStep(0.5)
        ul_input_row.addWidget(self.ul_spin, 1)

        self.ul_combo = QComboBox()
        self.ul_combo.addItems(["Mbps (Speedtest/Fast)", "MB/s (Browser)", "KB/s"])
        self.ul_combo.setCurrentIndex(self.UNIT_MBPS)
        ul_input_row.addWidget(self.ul_combo)

        ul_vbox.addLayout(ul_input_row)

        # Live calculation hint
        self.lbl_ul_hint = QLabel("")
        self.lbl_ul_hint.setProperty("class", "CalcHint")
        ul_vbox.addWidget(self.lbl_ul_hint)

        # Quick Preset Buttons
        ul_presets_layout = QHBoxLayout()
        ul_presets_layout.setSpacing(6)
        ul_presets = [
            ("512 Kbps", 0.5, self.UNIT_MBPS),
            ("1 Mbps", 1.0, self.UNIT_MBPS),
            ("2 Mbps", 2.0, self.UNIT_MBPS),
            ("4 Mbps", 4.0, self.UNIT_MBPS),
            ("8 Mbps", 8.0, self.UNIT_MBPS),
        ]
        for label, val, u_idx in ul_presets:
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
        self.btn_engage.clicked.connect(lambda: self._on_engage_clicked(silent=False))
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
        self._setup_settings_dialog()

        self._load_saved_values()
        self._update_dl_hint()
        self._update_ul_hint()
        self._update_status_display()

    def _connect_signals(self):
        self.monitor.speed_updated.connect(self._on_speed_updated)

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = QApplication.windowIcon()
        if icon.isNull():
            icon = self.windowIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("OpenLimiter Pro")

        tray_menu = QMenu(self)
        show_action = QAction("Open OpenLimiter", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_from_tray)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        self.start_minimized = (
            "--minimized" in sys.argv
            and self.config.get("close_to_tray", False)
            and self.tray_icon is not None
        )

    def _setup_settings_dialog(self):
        self.settings_dialog = QDialog(self)
        self.settings_dialog.setWindowTitle("OpenLimiter Settings")
        self.settings_dialog.setMinimumWidth(390)
        dialog_layout = QVBoxLayout(self.settings_dialog)
        dialog_layout.setSpacing(12)

        self.autostart_check = QCheckBox("Start OpenLimiter when I sign in to Windows")
        self.autostart_check.setChecked(bool(self.config.get("autostart", False)))
        self.autostart_check.setToolTip(
            "OpenLimiter starts with Windows. It starts hidden when notification-area mode is enabled."
        )
        self.autostart_check.toggled.connect(self._on_autostart_toggled)
        dialog_layout.addWidget(self.autostart_check)

        self.close_to_tray_check = QCheckBox("Keep running in the notification area when closed")
        self.close_to_tray_check.setChecked(bool(self.config.get("close_to_tray", False)))
        self.close_to_tray_check.setToolTip(
            "The X button hides the window; use the OpenLimiter tray icon and choose Exit to stop the app."
        )
        self.close_to_tray_check.setEnabled(QSystemTrayIcon.isSystemTrayAvailable())
        self.close_to_tray_check.toggled.connect(self._on_close_to_tray_toggled)
        dialog_layout.addWidget(self.close_to_tray_check)

        shortcut_button = QPushButton("Create desktop shortcut")
        shortcut_button.clicked.connect(self._on_create_desktop_shortcut)
        dialog_layout.addWidget(shortcut_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.settings_dialog.accept)
        dialog_layout.addWidget(close_button)

        settings_button = QPushButton("⚙ Settings")
        settings_button.setToolTip("Startup, background, and desktop shortcut settings")
        settings_button.clicked.connect(self.settings_dialog.exec)
        self.status_bar.addPermanentWidget(settings_button)

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_from_tray()

    def _exit_from_tray(self):
        self._force_exit = True
        self.close()

    def _on_autostart_toggled(self, enabled: bool):
        if not set_autostart(enabled):
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(not enabled)
            self.autostart_check.blockSignals(False)
            QMessageBox.warning(self, "Startup setting failed", "Windows could not update the startup setting.")
            return
        self.config["autostart"] = enabled
        save_config(self.config)

    def _on_close_to_tray_toggled(self, enabled: bool):
        self.config["close_to_tray"] = enabled
        save_config(self.config)

    def _on_create_desktop_shortcut(self):
        if create_desktop_shortcut():
            QMessageBox.information(self, "Shortcut created", "OpenLimiter Pro was added to your desktop.")
        else:
            QMessageBox.warning(self, "Shortcut failed", "Windows could not create the desktop shortcut.")

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
            self.lbl_dl_hint.setText(f"💡 Fast.com will show: {val:.1f} Mbps  (~{kb} KB/s in Chrome)")
        elif mode == self.UNIT_MBS:
            mbps = val * 8
            self.lbl_dl_hint.setText(f"💡 {val:.1f} MB/s = {mbps:.1f} Mbps on Fast.com (1 Byte = 8 bits. Choose Mbps for {val:.0f} Mbps)")
        else: # KB/s
            mbps = (val * 8) / 1024
            self.lbl_dl_hint.setText(f"💡 {val:.0f} KB/s = {mbps:.2f} Mbps on Fast.com (1 Byte = 8 bits)")

    def _update_ul_hint(self):
        val = self.ul_spin.value()
        mode = self.ul_combo.currentIndex()
        if mode == self.UNIT_MBPS:
            kb = int(val * 1024 / 8)
            self.lbl_ul_hint.setText(f"💡 Speedtest will show: {val:.1f} Mbps  (~{kb} KB/s outbound)")
        elif mode == self.UNIT_MBS:
            mbps = val * 8
            self.lbl_ul_hint.setText(f"💡 {val:.1f} MB/s = {mbps:.1f} Mbps on Speedtest (1 Byte = 8 bits)")
        else:
            mbps = (val * 8) / 1024
            self.lbl_ul_hint.setText(f"💡 {val:.0f} KB/s = {mbps:.2f} Mbps on Speedtest (1 Byte = 8 bits)")

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
        # Restore UI selections from config
        dl_val = self.config.get("dl_value", 1.0)
        dl_unit = self.config.get("dl_unit", self.UNIT_MBPS)
        dl_on = self.config.get("dl_enabled", True)
        self.dl_spin.setValue(dl_val)
        self.dl_combo.setCurrentIndex(dl_unit)
        self.dl_toggle.setChecked(dl_on)

        ul_val = self.config.get("ul_value", 512.0)
        ul_unit = self.config.get("ul_unit", self.UNIT_KBS)
        ul_on = self.config.get("ul_enabled", True)
        self.ul_spin.setValue(ul_val)
        self.ul_combo.setCurrentIndex(ul_unit)
        self.ul_toggle.setChecked(ul_on)

    def _on_engage_clicked(self, silent: bool = False):
        if not self.is_elevated:
            if not silent:
                res = QMessageBox.warning(
                    self,
                    "Elevation Required",
                    "Applying bandwidth limits requires Administrator privileges.\n\n"
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
            # Persist state
            self.config["dl_value"] = self.dl_spin.value()
            self.config["dl_unit"] = self.dl_combo.currentIndex()
            self.config["dl_enabled"] = self.dl_toggle.isChecked()
            self.config["ul_value"] = self.ul_spin.value()
            self.config["ul_unit"] = self.ul_combo.currentIndex()
            self.config["ul_enabled"] = self.ul_toggle.isChecked()
            self.config["engaged"] = True
            save_config(self.config)

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
            if not silent:
                QMessageBox.critical(self, "Error", "Failed to apply bandwidth limit policies.")

    def _on_unrestrict_clicked(self):
        if not self.is_elevated:
            self._on_restart_admin()
            return

        self.dl_toggle.setChecked(False)
        self.ul_toggle.setChecked(False)
        if not self.limiter.remove_all_limits():
            QMessageBox.critical(
                self,
                "Could not fully remove limits",
                "The proxy settings were restored where possible, but Windows QoS did not confirm removal. "
                "Run the app as Administrator and try again."
            )
            self._update_status_display()
            return

        self.config["engaged"] = False
        save_config(self.config)

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
            self.status_bar.showMessage(f"SYS // ENGAGED: DL {txt_dl} | UL {txt_ul}   [ENGINE: PROXY + QoS]")
        else:
            self.status_bar.showMessage("SYS // UNRESTRICTED (MAX THROUGHPUT)   [ENGINE: READY]")

    def _on_restart_admin(self):
        self.monitor.stop()
        if not restart_as_admin() and not self.monitor.isRunning():
            self.monitor.start()

    def closeEvent(self, event):
        """Hide to the notification area when requested, otherwise exit cleanly."""
        if (not self._force_exit and self.close_to_tray_check.isChecked()
                and self.tray_icon and self.tray_icon.isVisible()):
            self.hide()
            event.ignore()
            return

        self.monitor.stop()
        self.limiter.stop()
        event.accept()
        QApplication.quit()
