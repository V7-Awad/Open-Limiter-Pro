# OpenLimiter Pro

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20(64--bit)-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-cyan.svg)
![UI](https://img.shields.io/badge/Design-Linear%20%2F%20Raycast%202026-black.svg)
![License](https://img.shields.io/badge/License-MIT-emerald.svg)

**OpenLimiter Pro** is a high-performance system-wide network bandwidth controller and monitoring application for Windows. Engineered with a futuristic, precision-driven dark aesthetic inspired by Linear, Raycast, and Vercel, it enables system-wide throttling for both download and upload speeds without requiring external hardware or kernel drivers.

---

## ⚡ Key Highlights

- **Single Standalone Executable**: Completely portable (`OpenLimiterPro.exe`). Zero installation required, zero setup conflicts, and zero file locks.
- **Dual-Engine Precision Architecture**:
  - **Ingress (Download)**: High-throughput local token-bucket streaming proxy (`127.0.0.1:8899`) with WinINet system routing.
  - **Egress (Upload)**: Windows NetQoS kernel policy enforcement with automated NLA bypass.
- **1:1 Unit Matching (Mbps / MB/s / KB/s)**:
  - Default unit is **Mbps** (Speedtest / Fast.com standard). Entering `1.0 Mbps` enforces an exact `1.0 Mbps` limit on Fast.com.
  - Also supports `MB/s` (Browser / Steam / IDM transfer rates) and `KB/s` for fine-grained tuning.
- **Real-Time Telemetry & Vector Sparklines**:
  - Live throughput monitoring updated every second.
  - Real-time animated vector waveforms for download and upload activity.
  - Dual telemetry readout: simultaneously displays Byte rate (e.g., `512 KB/s`) and Bit rate (e.g., `4.1 Mbps`).
- **Silent & Clean Lifecycle**:
  - Headless QoS and registry execution with no visible console or PowerShell popup windows.
  - Clean process exit: closing the window immediately restores full unthrottled network speed and terminates all threads cleanly.

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

1. Download the standalone executable from `dist/OpenLimiterPro.exe` or the GitHub Releases page.
2. Double-click **`OpenLimiterPro.exe`**.
3. Accept the Windows UAC (User Account Control) prompt to grant administrative privileges (required for Windows network QoS and system proxy configuration).
4. Set your desired **Download** and **Upload** limits:
   - Use the preset buttons (e.g., `1 Mbps`, `2 Mbps`, `4 Mbps`, `8 Mbps`, `16 Mbps`) or enter a custom value.
5. Click **⚡ ENGAGE BANDWIDTH LIMIT**.
6. To restore maximum bandwidth at any time, click **✕ UNRESTRICT SPEED** or simply close the application.

---

## ⚙️ Technical Architecture

### 1. The Windows Ingress Throttling Challenge
Windows client editions (Windows 10 / 11) provide native QoS policies (`New-NetQosPolicy`) that only regulate **outbound (egress)** network packets. Windows has no native kernel mechanism for throttling incoming (ingress / download) traffic without installing third-party NDIS filter drivers.

### 2. Dual-Engine Solution
OpenLimiter Pro solves this through a synchronized two-layer architecture:
- **Layer 1: User-Mode Token-Bucket Traffic Shaper**:
  - Runs a local high-performance streaming socket proxy on `127.0.0.1:8899`.
  - Implements an asynchronous token-bucket rate limiter that paces chunk reads to enforce exact download limits.
  - Automatically updates the Windows Internet Settings registry (`ProxyEnable = 1`) and notifies WinINet to redirect HTTP/HTTPS/WebSocket traffic seamlessly.
- **Layer 2: Kernel NetQoS Policy Enforcement**:
  - Dynamically creates Windows PowerShell NetQoS policies for system-wide outbound bandwidth throttling.
  - Automatically configures `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\QoS\Do not use NLA = 1` via native Windows Registry APIs so policies apply consistently across all network adapters.
- **Fail-Safe Cleanup**:
  - Proxy and QoS configurations are automatically deactivated when the app is closed or when `UNRESTRICT SPEED` is triggered.
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
   python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin --icon="assets/icon.ico" --add-data="assets/icon.ico;assets" --add-data="assets/icon.png;assets" --name="OpenLimiterPro" --distpath="dist" main.py
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
