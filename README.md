# OpenLimiter Pro

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20(64--bit)-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-cyan.svg)
![UI](https://img.shields.io/badge/Design-Linear%20%2F%20Raycast%202026-black.svg)
![License](https://img.shields.io/badge/License-MIT-emerald.svg)

**OpenLimiter Pro** is a Windows bandwidth controller with shared download and upload limits. Downloads are shaped through the Windows system proxy, so apps that ignore that proxy may bypass the download limit. Uploads use Windows QoS. It does not currently provide NetLimiter-style per-application rules; that requires a Windows network filter driver.

---

## ⚡ Key Highlights

- **Portable Build Available**: The project can be packaged as a single executable after installing PyInstaller.
- **Shared Bandwidth Limits**:
  - **Download**: Local token-bucket proxy (`127.0.0.1:8899`) for applications that honor Windows system proxy settings.
  - **Upload**: Windows NetQoS policy. This controls outbound traffic; it is not a per-app limiter.
- **1:1 Unit Matching (Mbps / MB/s / KB/s)**:
  - Default unit is **Mbps** (Speedtest / Fast.com standard). Entering `1.0 Mbps` enforces an exact `1.0 Mbps` limit on Fast.com.
  - Also supports `MB/s` (Browser / Steam / IDM transfer rates) and `KB/s` for fine-grained tuning.
- **Real-Time Telemetry & Vector Sparklines**:
  - Live throughput monitoring updated every second.
  - Real-time animated vector waveforms for download and upload activity.
  - Dual telemetry readout: simultaneously displays Byte rate (e.g., `512 KB/s`) and Bit rate (e.g., `4.1 Mbps`).
- **Silent & Clean Lifecycle**:
  - Headless QoS and registry execution with no visible console or PowerShell popup windows.
  - Closing the window exits and restores system settings, unless notification-area mode is enabled. Use the tray menu's **Exit** command to stop a background instance and restore settings.

---

## 🖥️ User Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│  ⚡ OPENLIMITER PRO                 [ ● ELEVATED ]          │
│     SYSTEM BANDWIDTH CONTROLLER                             │
├─────────────────────────────────────────────────────────────┤
│  ● LIVE DOWNLOAD                    ● LIVE UPLOAD           │
│    535.7 KB/s                          75.6 KB/s            │
│    ≈ 4.4 Mbps (Fast.com)               ≈ 619.7 Kbps         │
│    [~~~ Sparkline Graph ~~~]          [~~~ Sparkline ~~~]   │
├─────────────────────────────────────────────────────────────┤
│  ⬇ DOWNLOAD THROTTLE                               [ON]     │
│    [ 1.0       ]  [ Mbps (Speedtest/Fast.com)  ▼ ]          │
│    💡 Fast.com will show: 1.0 Mbps (~128 KB/s in Chrome)   │
│    [ 1 Mbps ]  [ 2 Mbps ]  [ 4 Mbps ]  [ 8 Mbps ] [ 16 Mbps]│
├─────────────────────────────────────────────────────────────┤
│  ⬆ UPLOAD THROTTLE                                 [ON]     │
│    [ 1.0       ]  [ Mbps (Speedtest/Fast.com)  ▼ ]          │
│    💡 Speedtest will show: 1.0 Mbps (~128 KB/s outbound)    │
│    [ 1 Mbps ]  [ 2 Mbps ]  [ 4 Mbps ]  [ 8 Mbps ] [ 16 Mbps]│
├─────────────────────────────────────────────────────────────┤
│         ⚡ ENGAGE BANDWIDTH LIMIT                           │
│         ✕ UNRESTRICT SPEED                                  │
├─────────────────────────────────────────────────────────────┤
│ SYS // UNRESTRICTED (MAX THROUGHPUT)       [ENGINE: READY]  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Portable Binary)

1. Install Python and the dependencies using the source instructions below, or build the standalone executable.
2. Run `run.bat` (source) or double-click **`dist/OpenLimiterPro.exe`** (after building).
3. The app opens normally. Accept a Windows UAC prompt only when you apply or remove Windows QoS limits.
4. Set your desired shared **Download** and **Upload** limits:
   - Use the preset buttons (e.g., `1 Mbps`, `2 Mbps`, `4 Mbps`, `8 Mbps`, `16 Mbps`) or enter a custom value.
5. Click **⚡ ENGAGE BANDWIDTH LIMIT**.
6. To remove the limits, click **✕ UNRESTRICT SPEED**. Closing the window exits unless notification-area mode is enabled.

Open **⚙ Settings** in the status bar to create a desktop shortcut, choose whether OpenLimiter starts when you sign in to Windows, and choose whether closing the window keeps it running in the notification area. Right-click the notification-area icon and choose **Exit** to stop it completely. The open window appears on the taskbar; Windows lets you pin the desktop shortcut to the taskbar manually.

---

## ⚙️ Technical Architecture

### 1. The Windows Ingress Throttling Challenge
Windows client editions (Windows 10 / 11) provide native QoS policies (`New-NetQosPolicy`) that only regulate **outbound (egress)** network packets. Windows has no native kernel mechanism for throttling incoming (ingress / download) traffic without installing third-party NDIS filter drivers.

### 2. Dual-Engine Solution
OpenLimiter Pro solves this through a synchronized two-layer architecture:
- **Layer 1: User-Mode Token-Bucket Traffic Shaper**:
  - Runs a local high-performance streaming socket proxy on `127.0.0.1:8899`.
  - Implements an asynchronous token-bucket rate limiter that paces chunk reads to enforce exact download limits.
  - Temporarily updates Windows Internet Settings and restores the previous proxy values when limits are removed or the app closes. Proxy-aware HTTP/HTTPS traffic is shaped; apps that bypass the system proxy are not.
- **Layer 2: Kernel NetQoS Policy Enforcement**:
  - Dynamically creates a Windows PowerShell NetQoS policy for shared outbound bandwidth throttling. Download QoS is not used because Windows client QoS does not reliably limit inbound traffic.
  - Automatically configures `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\QoS\Do not use NLA = 1` via native Windows Registry APIs so policies apply consistently across all network adapters.
- **Fail-Safe Cleanup**:
  - Proxy and QoS configurations are automatically deactivated on full app exit or when `UNRESTRICT SPEED` is triggered. Closing to the notification area keeps the app and active limits running.
  - Python's `atexit` handler guarantees that internet settings revert to direct connection even in the event of an unexpected termination.

---

## 📊 Speed Units & Measurement Guide

Internet bandwidth is measured differently depending on the tool:

| Interface / Application | Unit Displayed | Description | Example Conversion |
| :--- | :--- | :--- | :--- |
| **Speedtest.net / Fast.com** | **Mbps** (Megabits/sec) | Network transmission bitrate | `1.0 Mbps` = `128 KB/s` |
| **Chrome / Firefox / Edge** | **KB/s** or **MB/s** | File transfer byte rate | `1.0 MB/s` = `8.0 Mbps` |
| **Steam / Epic Games / IDM** | **MB/s** (MegaBytes/sec) | Storage payload written per sec | `2.0 MB/s` = `16.0 Mbps` |

OpenLimiter Pro displays both metrics simultaneously in the live telemetry header and dynamic calculation hints, ensuring you always know exactly what speed test results and browser downloads will report.

---

## 🛠️ Building from Source

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, 3.12, 3.13, or 3.14

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/V7-Awad/Open-Limiter-Pro.git
   cd Open-Limiter-Pro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run directly**:
   ```bash
   python main.py
   ```

4. **Compile Single Standalone Executable**:
   ```bash
   python -m pip install pyinstaller
   python -m PyInstaller --noconfirm --clean --onefile --windowed --icon="assets/icon.ico" --add-data="assets/icon.ico;assets" --add-data="assets/icon.png;assets" --name="OpenLimiterPro" --distpath="dist" main.py
   ```
   The compiled standalone binary will be generated at `dist/OpenLimiterPro.exe`.

---

## 📁 Repository Structure

```
Open-Limiter-Pro/
├── assets/
│   ├── icon.ico            # High-resolution application icon
│   └── icon.png            # PNG branding logo
├── core/
│   ├── limiter.py          # Dual-engine QoS & proxy orchestration
│   ├── monitor.py          # Real-time network throughput sampler (psutil)
│   ├── shaper.py           # Async token-bucket streaming proxy server
│   └── utils.py            # Elevation, unit conversions, settings persistence
├── ui/
│   ├── main_window.py      # Linear/Raycast dark dashboard interface
│   ├── sparkline.py        # Vector waveform sparkline widget
│   ├── styles.py           # High-end 2026 QSS stylesheet
│   └── toggle_switch.py    # Custom animated pill toggle switches
├── dist/
│   └── OpenLimiterPro.exe  # Standalone portable Windows executable
├── main.py                 # Application bootstrap entry point
├── requirements.txt        # Python package dependencies
└── README.md               # Documentation
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
