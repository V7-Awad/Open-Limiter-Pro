# OpenLimiter Pro — Comprehensive Development & Engineering Audit Log
**Document Version:** 1.0.0  
**Target Environment:** Windows 10 / 11 (64-bit)  
**Repository:** [https://github.com/V7-Awad/Open-Limiter-Pro.git](https://github.com/V7-Awad/Open-Limiter-Pro.git)  
**Branch:** `main`  
**Author:** Engineering Team  

---

## 1. Executive Summary

This document provides a comprehensive technical audit of the complete development lifecycle of **OpenLimiter Pro**, beginning from the reverse engineering and analysis of the original codebase, through the high-end UI/UX redesign, down to the network traffic shaping implementation, edge-case debugging, installer complications, and final restoration of a rock-solid standalone portable binary.

This document is prepared specifically for external architectural review (e.g., Claude) to provide full visibility into all code modifications, design decisions, failure modes encountered, root causes, and recommended future optimizations.

---

## 2. Phase 1: Reverse Engineering & Core Network Architecture

### 2.1 The Windows Bandwidth Throttling Challenge
Windows client editions (Windows 10 / 11 Workstation) do not provide a native kernel-level packet throttling mechanism for **ingress (download)** network traffic without installing third-party NDIS filter drivers or WinDivert kernels.
- **Outbound (Egress / Upload)**: Windows natively supports egress throttling through the PowerShell Network Quality of Service cmdlet: `New-NetQosPolicy -ThrottleRateActionBitsPerSecond <bps>`.
- **Inbound (Ingress / Download)**: Windows QoS policies explicitly ignore incoming packets on client editions.

### 2.2 The Dual-Engine Mechanism
To achieve global bandwidth control without third-party driver installation, OpenLimiter was engineered with a dual-engine architecture:

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    OPENLIMITER PRO                     │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                        ┌──────────────────────────────────┴──────────────────────────────────┐
                        ▼                                                                     ▼
         ┌──────────────────────────────┐                                      ┌──────────────────────────────┐
         │       DOWNLOAD ENGINE        │                                      │        UPLOAD ENGINE         │
         │  (User-Mode Token Shaper)    │                                      │     (Kernel NetQoS Layer)    │
         └──────────────┬───────────────┘                                      └──────────────┬───────────────┘
                        │                                                                     │
     1. Local Socket Proxy (127.0.0.1:8899)                                 1. New-NetQosPolicy Cmdlet
     2. Windows System Proxy Configuration                                   2. NLA Registry Bypass
     3. Async Token-Bucket Rate Limiter                                     3. Egress Throttle (Bits/sec)
                        │                                                                     │
                        ▼                                                                     ▼
         ┌──────────────────────────────┐                                      ┌──────────────────────────────┐
         │ All Browser & Web Traffic    │                                      │ All Outbound System Sockets  │
         │ Dynamically Paced & Delayed  │                                      │ Throttled at TCP/IP Stack    │
         └──────────────────────────────┘                                      └──────────────────────────────┘
```

#### Engine A: Local Token-Bucket Traffic Shaper (`core/shaper.py`)
- **Proxy Server**: An asynchronous streaming proxy server (`TrafficShaperServer`) listening on `127.0.0.1:8899`.
- **System Proxy Injection**: Automatically modifies `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings`:
  - `ProxyEnable = 1`
  - `ProxyServer = 127.0.0.1:8899`
  - `ProxyOverride = localhost;127.*;10.*;192.168.*;<local>`
  - Dispatches `INTERNET_OPTION_SETTINGS_CHANGED` (39) and `INTERNET_OPTION_REFRESH` (37) via `ctypes.windll.wininet.InternetSetOptionW` so browsers and system apps immediately route traffic through the shaper.
- **Token Bucket Algorithm (`TokenBucket`)**:
  - Implemented using Python's `asyncio`.
  - Calculates chunk delay: $\text{delay} = \frac{\text{needed tokens}}{\text{rate bytes/sec}}$.
  - Sleeps up to $40\text{ ms}$ increments to pace packet consumption smoothly without starving socket buffers.
- **Fail-safe Cleanup**: Registers an `atexit` hook (`atexit.register(disable_system_proxy)`) to ensure proxy redirection is disabled even if the process is terminated abruptly.

#### Engine B: Windows NetQoS Egress Enforcement (`core/limiter.py`)
- Configures system-wide QoS policies:
  ```powershell
  New-NetQosPolicy -Name 'OpenLimiter_Global_Upload' -NetworkProfile All -ThrottleRateActionBitsPerSecond <bps> -Confirm:$false
  ```
- **NLA Bypass**: Windows Network Location Awareness (NLA) often ignores QoS policies on non-domain joined networks. The app modifies:
  `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\QoS\Do not use NLA = 1`

#### Engine C: Loopback-Filtered Telemetry (`core/monitor.py`)
- Queries real-time network throughput via `psutil.net_io_counters(pernic=True)`.
- Isolates physical network interfaces (Wi-Fi, Ethernet) and strips `Loopback Pseudo-Interface 1` to prevent double-counting traffic redirected through `127.0.0.1:8899`.

---

## 3. Phase 2: Complete UI/UX Redesign (2026 Linear / Raycast Aesthetic)

### 3.1 Design Principles & Visual Hierarchy
The legacy UI was completely redesigned into a high-end, dark, precision-engineered desktop application inspired by Linear, Raycast, and Vercel.

- **Color System (`ui/styles.py`)**:
  - Main Canvas: `#080B12` (Deep near-black)
  - Card Surfaces: `#101725` (Dark navy surface)
  - Elevated Containers: `#151F30`
  - Primary Accent: `#00E5FF` (Electric Cyan for Download & System state)
  - Upload Accent: `#A78BFA` (Soft Violet for Outbound controls)
  - Secondary Accent: `#398BFF` (Vivid Blue)
  - Borders: `#1E293B` (Subtle 1px border lines)
  - Typography: `#F1F5F9` (Primary text), `#8492A6` (Secondary text / labels)

### 3.2 Custom Components Developed
1. **`ToggleSwitch` (`ui/toggle_switch.py`)**:
   - Built on `QAbstractButton` with custom `paintEvent`.
   - Smooth animated pill track with rounded thumb indicator.
   - Distinct color themes: Electric cyan for Download, soft violet for Upload.
2. **`SparklineWidget` (`ui/sparkline.py`)**:
   - Real-time vector waveform widget using `QPainter` with anti-aliasing.
   - Smooth Bézier curve interpolation (`QPainterPath.cubicTo`).
   - Vertical gradient area fill beneath the stroke with dynamic auto-scaling.
3. **`MainWindow` (`ui/main_window.py`)**:
   - Fixed geometry: `500 x 730 px`.
   - Elevated status pill badge (`● ELEVATED`).
   - Large digital throughput telemetry (`535.7 KB/s` + `≈ 4.4 Mbps`).
   - Segmented preset pills (`1 Mbps`, `2 Mbps`, `4 Mbps`, `8 Mbps`, `16 Mbps`).
   - Dynamic conversion hint showing predicted Speedtest and browser transfer rates.
   - Action buttons: `⚡ ENGAGE BANDWIDTH LIMIT` and `✕ UNRESTRICT SPEED`.
   - Monospaced technical status bar: `SYS // UNRESTRICTED (MAX THROUGHPUT) [ENGINE: READY]`.

---

## 4. Phase 3: Critical Bugs, Cascading Failures & Root Causes

During testing and deployment, several critical failure modes occurred. Below is an exhaustive breakdown of each issue and its engineering resolution.

---

### Bug 1: `SparklineWidget.__init__()` Signature Mismatch
- **Symptom**:
  The application crashed on startup with an unhandled exception dialog:
  ```
  TypeError: SparklineWidget.__init__() got an unexpected keyword argument 'color'
  File "ui\main_window.py", line 166, in _setup_ui
  ```
- **Root Cause**:
  `MainWindow` instantiated `SparklineWidget` with `color=QColor(...)`, but `SparklineWidget.__init__` defined the parameter as `stroke_color`.
- **Fix**:
  Updated `ui/sparkline.py` to accept `color=None`, `stroke_color=None`, and `height=36`, normalizing both parameter names.

---

### Bug 2: Blue PowerShell Console Popups & Parameter Binding Hang
- **Symptom**:
  A blue PowerShell console window flashed on startup and hung intermittently when engaging or removing bandwidth limits.
- **Root Cause**:
  1. `core/limiter.py` executed `reg.exe` and `powershell.exe` subprocesses without `subprocess.CREATE_NO_WINDOW`.
  2. In `Remove-NetQosPolicy -Name '...' -Confirm:$false`, the parameter `-Confirm:$false` was parsed incorrectly when passed inside `powershell -Command "..."`, causing PowerShell to prompt interactively for confirmation in a headless process.
- **Fix**:
  1. Converted `_ensure_nla_bypass()` to use Python's native `winreg` API, eliminating process spawning entirely.
  2. Wrapped PowerShell commands in `& { ... }` with escaped backtick `-Confirm:`$false`, `-NoProfile`, and `-NonInteractive`.
  3. Added `creationflags=subprocess.CREATE_NO_WINDOW`.

---

### Bug 3: Speed Test Discrepancy (Fast.com Showing 8.3 Mbps for 1 MB/s)
- **Symptom**:
  The user selected `1.0` in the application, but Fast.com measured `8.3 Mbps` instead of `1.0 Mbps`.
- **Root Cause**:
  - The default unit dropdown was set to `MB/s` (Megabytes per second).
  - $1.0\text{ MB/s} = 1{,}048{,}576\text{ bytes/sec} \times 8 = 8{,}388{,}608\text{ bits/sec} \approx 8.3\text{ Mbps}$.
  - Network speed test sites (Fast.com, Speedtest.net) measure strictly in **Megabits per second (Mbps)**, whereas browser download managers (Chrome, IDM) report in **Megabytes per second (MB/s)**.
- **Fix**:
  1. Set **`Mbps`** as the default unit (index 0).
  2. Changed preset pills to **`1 Mbps`**, **`2 Mbps`**, **`4 Mbps`**, **`8 Mbps`**, **`16 Mbps`**.
  3. Added real-time dynamic conversion hints:
     `💡 Fast.com will show: 1.0 Mbps (~128 KB/s in Chrome)`.

---

### Bug 4: Background Tray Persistence & Installer Lockup Cascade
- **Symptom**:
  When installing updates, Inno Setup threw:
  ```
  DeleteFile failed; code 5. Access is denied.
  C:\Users\...\Programs\OpenLimiter Pro\OpenLimiterPro.exe
  ```
  Followed by elevation launch failure:
  ```
  CreateProcess failed; code 740. The requested operation requires elevation.
  ```
  And multiple zombie processes locked port 8899 in Task Manager.
- **Root Cause Analysis**:
  1. In an earlier iteration, the user requested that the app run in the background when closed and start with Windows.
  2. `ui/main_window.py` was modified so `closeEvent` called `event.ignore()` and `self.hide()`, while `main.py` set `app.setQuitOnLastWindowClosed(False)`.
  3. When the user clicked the `[X]` button, the application remained active in the background as an elevated Administrator process holding open port 8899 and locking `OpenLimiterPro.exe`.
  4. When the user ran `OpenLimiterPro_Setup.exe`:
     - The setup installer was configured with `PrivilegesRequired=lowest` (per-user).
     - Windows restricts standard user processes from terminating or overwriting files owned by elevated administrator processes.
     - As a result, `taskkill` failed silently, and Inno Setup failed with `DeleteFile failed; code 5` because the file was locked by running instances.
  5. Distributing two separate executables (`OpenLimiterPro.exe` and `OpenLimiterPro_Setup.exe`) caused extreme confusion.
- **Fix & Architectural Restoration**:
  1. Terminated all lingering background instances using CIM:
     ```powershell
     Get-CimInstance Win32_Process -Filter "name = 'OpenLimiterPro.exe'" | Invoke-CimMethod -MethodName Terminate
     ```
  2. Completely removed background tray persistence and autostart checkboxes from `ui/main_window.py` and `main.py`.
  3. Reverted `closeEvent` to ensure 100% clean termination:
     ```python
     def closeEvent(self, event):
         self.monitor.stop()
         self.limiter.stop()
         event.accept()
     ```
  4. Removed the Inno Setup installer script (`installer.iss`) and cleaned `dist/` to provide **only ONE single standalone executable (`dist/OpenLimiterPro.exe`)**.

---

## 5. Phase 4: Current Codebase State & File Inventory

### 5.1 Repository File Map

```
OpenLimiter/
├── assets/
│   ├── icon.ico                     # Embedded 256x256 Windows icon
│   └── icon.png                     # Visual logo asset
├── core/
│   ├── __init__.py                  # Package descriptor
│   ├── limiter.py                   # QoS policy & proxy controller
│   ├── monitor.py                   # psutil real-time bandwidth monitor thread
│   ├── shaper.py                    # Async token-bucket streaming proxy server
│   └── utils.py                     # Elevation checks, math, config persistence
├── ui/
│   ├── __init__.py                  # Package descriptor
│   ├── main_window.py               # Complete Linear/Raycast UI window
│   ├── sparkline.py                 # Vector waveform widget
│   ├── styles.py                    # High-end 2026 QSS stylesheet
│   └── toggle_switch.py             # Custom animated pill switch widget
├── dist/
│   └── OpenLimiterPro.exe           # Standalone portable Windows binary (39 MB)
├── main.py                          # Application entry point
├── requirements.txt                 # PySide6, psutil
├── README.md                        # Production documentation
└── DEVELOPMENT_AUDIT_LOG.md         # This technical audit report
```

### 5.2 Core Implementation Details

#### `main.py`
```python
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

    icon_path = os.path.join(BASE_DIR, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(PREMIUM_2026_THEME_QSS)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

#### `core/limiter.py` (Selected Methods)
```python
    def apply_global_limits(self, dl_kb: Optional[int], ul_kb: Optional[int]) -> bool:
        has_limit = (dl_kb and dl_kb > 0) or (ul_kb and ul_kb > 0)

        dl_bytes = (dl_kb * 1024) if (dl_kb and dl_kb > 0) else 0
        ul_bytes = (ul_kb * 1024) if (ul_kb and ul_kb > 0) else 0

        self.shaper.set_limits(dl_bytes, ul_bytes)

        if has_limit:
            set_system_proxy(True, host="127.0.0.1", port=8899)
        else:
            set_system_proxy(False)

        self._set_policy(POLICY_DL, dl_kb)
        self._set_policy(POLICY_UL, ul_kb)

        self.dl_limit_kb = dl_kb if (dl_kb and dl_kb > 0) else None
        self.ul_limit_kb = ul_kb if (ul_kb and ul_kb > 0) else None
        self.save_config()
        return True

    def remove_all_limits(self) -> bool:
        set_system_proxy(False)
        self.shaper.set_limits(0, 0)
        self._remove_policy(POLICY_DL)
        self._remove_policy(POLICY_UL)
        self.dl_limit_kb = None
        self.ul_limit_kb = None
        self.save_config()
        return True

    def stop(self):
        """Cleanly stops limiter and shaper server."""
        self.remove_all_limits()
        if hasattr(self, 'shaper') and self.shaper:
            self.shaper.stop()
```

#### `ui/main_window.py` (Clean Shutdown)
```python
    def closeEvent(self, event):
        """Clean termination on window close."""
        self.monitor.stop()
        self.limiter.stop()
        event.accept()
```

---

## 6. Git Commit History Summary

| Commit Hash | Message Summary |
| :--- | :--- |
| `b31a66a` | Initial release of OpenLimiter Pro (Clean UI redesign complete) |
| `b448d41` | Add installer configuration and update documentation |
| `27e93e0` | Add system tray background mode, Windows autostart, and settings persistence |
| `f8cb108` | Expand documentation with comprehensive technical overview and architecture |
| `5acc0cb` | Fix elevation error 740 on postinstall launch by adding shellexec flag |
| `f54128a` | Fix SparklineWidget parameter signature mismatch (`color` vs `stroke_color`) |
| `d7bf9d3` | Eliminate PowerShell popups, switch default unit to Mbps, add Mbps preset pills |
| `6f82fa9` | Configure per-user installation and automated process termination on update |
| `5478428` | Fix PrivilegesRequired directive for per-user installation |
| `3d26ed6` | Restore standalone portable single executable with clean exit and detailed documentation |
| `c1f59c6` | Remove legacy installer script (`installer.iss`) |

---

## 7. Architectural Review Items for Claude

When reviewing this codebase, the following technical vectors are recommended for deeper analysis and potential enhancement:

### 1. Ingress Shaping Alternatives
- Currently, download shaping relies on a user-mode loopback proxy (`127.0.0.1:8899`) registered through WinINet system proxy settings.
- **Trade-off**: Applications that bypass WinINet (e.g., custom raw UDP connections or certain CLI tools) are not throttled on download.
- **Potential Upgrade**: Evaluate Windows Filtering Platform (WFP) callout drivers or `WinDivert` packet-divert libraries if full system-wide transport-layer packet interception without proxy routing is required.

### 2. HTTPS Tunneling & Socket Concurrency
- In `core/shaper.py`, HTTP `CONNECT` tunneling is passed through asynchronously via `asyncio.open_connection`.
- **Review Vector**: Inspect whether socket buffer sizes or TCP window scale parameters need tuning when processing multi-gigabit connections to minimize CPU overhead.

### 3. Graceful Socket Teardown on Windows
- Ensure all pending async tasks in `TrafficShaperServer._handle_client` are cancelled immediately when `stop()` is called to prevent `RuntimeError: Event loop is closed` during fast process exits.

### 4. Single-Instance Inter-Process Communication (IPC)
- If the user ever decides to bring back background execution in the future:
  - Do NOT rely on silent file locks.
  - Implement a named pipe (`\\.\pipe\OpenLimiterPro_IPC`) or local socket to allow subsequent instances to communicate with the primary instance, bring the window to the foreground, or instruct it to terminate cleanly before updates.

---

## 8. Conclusion

The implementation has a polished interface, but the earlier claims of complete system-wide shaping and a verified standalone binary were too strong. The download shaper only handles applications that use the Windows system proxy; NetQoS is used for outbound traffic. Per-application controls and transparent shaping require a Windows filtering driver. Confirm the packaged executable exists in `dist/` before distributing it.

### Review correction (2026-11-24)
- Fixed PowerShell QoS commands to pass `-Confirm:$false` as a PowerShell boolean and report command failures instead of silently treating them as success.
- Removed stale saved limit values from the active state at startup; old `global_config.json` values no longer make the UI claim limits are active when they were not applied.
- Added a readiness check for the local proxy before enabling download shaping.
- Preserved and restored the user's previous proxy registry values. Cleanup no longer disables an unrelated proxy.
- Removed the ineffective download NetQoS policy; Windows client QoS is used for upload only.
- Updated the UI help text and README to describe shared proxy/QoS limits and their per-application limitations accurately.
- Added source launcher checks with actionable Python/dependency setup instructions.
- Reintroduced optional notification-area mode and Windows sign-in startup at the user's request. Both settings are disabled by default and can be changed in the Settings dialog.
- Added a desktop shortcut action and removed the executable's always-administrator manifest so background startup does not trigger UAC. QoS operations still request elevation when needed.
