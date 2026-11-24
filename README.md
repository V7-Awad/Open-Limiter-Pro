# OpenLimiter Pro

OpenLimiter Pro is a specialized network bandwidth management utility for Windows 10 and Windows 11 (64-bit). It enables users to establish precise, system-wide download and upload speed limits without needing per-application configuration or third-party kernel drivers.

---

## Technical Overview

### The Ingress Regulation Challenge on Windows
Windows provides built-in Quality of Service (QoS) cmdlets (`New-NetQosPolicy`), but these policies only regulate outbound (egress / upload) traffic. Windows client editions provide no native mechanism for throttling incoming (ingress / download) traffic without external network drivers.

### The Dual-Engine Solution
OpenLimiter Pro solves this limitation using a synchronized dual-engine architecture:

1. **Ingress Engine (Download Shaper)**:
   - Implements an asynchronous token-bucket rate-limiting stream proxy running on `127.0.0.1:8899`.
   - Regulates incoming socket buffers using dynamic sleep intervals calculated from the target byte bucket.
   - Configures WinINet system routing dynamically while running and automatically restores default networking states upon exit.

2. **Egress Engine (Upload Controller)**:
   - Interfaces directly with Windows PowerShell NetQoS infrastructure.
   - Generates and modifies system-level QoS policies to enforce kernel-level egress throttling.
   - Configures registry parameters (`Do not use NLA = 1`) to ensure QoS policies function reliably on non-domain client environments.

3. **Loopback Filtered Telemetry**:
   - Queries system network adapter I/O counters directly via `psutil`.
   - Isolates physical network interfaces (Wi-Fi, Ethernet) from internal loopback sockets to prevent double-counting traffic forwarded through the local shaping proxy.

---

## Core Capabilities

- **Single Global Rate Control**: Throttle all system network activity through a single control interface.
- **Background Execution via System Tray**:
  - Closing the application window minimizes it to the Windows Notification Area (System Tray).
  - Bandwidth throttling policies remain active in the background.
  - Context menu provides instant status inspection, speed unrestriction, and clean application exit.
- **Logon Startup & State Persistence**:
  - Optional registration in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
  - Saves user settings to `%APPDATA%\OpenLimiterPro\config.json`.
  - Automatically loads and re-engages saved limits upon Windows logon without opening an intrusive window.
- **Multi-Unit Input & Telemetry**:
  - Input targets in Megabits per second (**Mbps**), Megabytes per second (**MB/s**), or Kilobytes per second (**KB/s**).
  - Displays dual telemetry showing both byte-based transfer rates and bit-based connection speeds.
- **Live Vector Waveform**:
  - Real-time sparkline visualization rendered with anti-aliasing to display short-term bandwidth variations.
- **Segmented Quick Presets**:
  - Quick-selection pills for frequently used rates (512 KB, 1 MB, 2 MB, 5 MB, 10 MB).

---

## Telemetry Calculation Reference

Different applications report network speeds in different units:
- **Web Speed Tests (Fast.com, Speedtest.net)**: Measured in Megabits per second (**Mbps**).
- **Web Browsers & Download Clients (Chrome, Steam, IDM)**: Measured in Kilobytes/Megabytes per second (**KB/s**, **MB/s**).

### Conversion Formulas
$$\text{Bitrate (Mbps)} = \frac{\text{Bytes per second} \times 8}{1{,}000{,}000}$$

$$\text{Transfer Rate (MB/s)} = \frac{\text{Bytes per second}}{1{,}048{,}576}$$

**Example:**
- Setting a download limit of `512 KB/s` corresponds to:
  $$512 \times 8 = 4{,}096\text{ Kbps} \approx 4.1\text{ Mbps}$$
- OpenLimiter Pro displays both values simultaneously to eliminate confusion.

---

## Installation & Distribution

OpenLimiter Pro is distributed as a single unified Windows setup installer:

### Official Installer Executable
- **File**: `dist/OpenLimiterPro_Setup.exe`
- **Installation Directory**: `C:\Program Files\OpenLimiter Pro`
- **Features Included**:
  - Standard setup wizard with administrative execution manifest.
  - Start Menu program group and desktop shortcut.
  - Automatic registry startup configuration.
  - Clean uninstaller registered in Windows Settings (Apps & Features).

---

## User Guide

### 1. Initial Launch
Run `OpenLimiterPro_Setup.exe` to complete the installation. Launch OpenLimiter Pro from the desktop or Start Menu. When prompted by Windows User Account Control (UAC), accept administrative elevation.

### 2. Setting Download Speed Limit
1. Locate the **Download Throttle** panel.
2. Toggle the switch to **ENABLE**.
3. Select your preferred unit from the dropdown:
   - `Mbps`: Match speed test targets (e.g., enter `4.0` for 4 Mbps).
   - `MB/s`: Match browser download speeds (e.g., enter `1.0` for 1 MB/s).
   - `KB/s`: Precise kilobyte-level control.
4. Or click one of the preset pills (`512 KB`, `1 MB`, `2 MB`, `5 MB`, `10 MB`).
5. Click **ENGAGE BANDWIDTH LIMIT**.

### 3. Setting Upload Speed Limit
1. Locate the **Upload Throttle** panel.
2. Toggle the switch to **ENABLE**.
3. Select your preferred unit and specify the desired maximum outbound rate.
4. Click **ENGAGE BANDWIDTH LIMIT**.

### 4. Running in the Background
- Click the window close button `[X]`.
- The window will hide and minimize to the system tray. Traffic shaping continues running without interruption.
- To reopen the window, double-click the system tray icon or right-click and choose **Open OpenLimiter Pro**.

### 5. Restoring Unrestricted Speed
- In the main window, click **UNRESTRICT SPEED**.
- Alternatively, right-click the system tray icon and select **Unrestrict Speed**.
- All QoS rules are deleted and default network routing is restored.

### 6. Completely Exiting
- Right-click the system tray icon and choose **Exit Application**.
- OpenLimiter Pro will disable all policies, restore network adapter settings, and terminate.

---

## Building from Source

### Prerequisites
- Windows 10 / 11 (64-bit)
- Python 3.10+
- Inno Setup 6 (for packaging the setup installer)

### Step 1: Clone Repository & Install Dependencies
```powershell
git clone https://github.com/V7-Awad/Open-Limiter-Pro.git
cd Open-Limiter-Pro
pip install -r requirements.txt
```

### Step 2: Run Application from Source
```powershell
python main.py
```

### Step 3: Compile Standalone Executable
```powershell
python -m PyInstaller --noconfirm --onefile --windowed --uac-admin --icon="assets/icon.ico" --add-data="assets/icon.ico;assets" --add-data="assets/icon.png;assets" --name="OpenLimiterPro" main.py
```

### Step 4: Compile Windows Setup Installer
```powershell
ISCC installer.iss
```
The output file `OpenLimiterPro_Setup.exe` will be generated in the `dist/` directory.

---

## Project Structure

```text
OpenLimiter/
├── assets/
│   ├── icon.ico                     # Embedded application icon
│   └── icon.png                     # Visual logo asset
├── core/
│   ├── limiter.py                   # High-level bandwidth orchestrator (QoS + Token Bucket)
│   ├── models.py                    # Structured dataclasses and settings models
│   ├── monitor.py                   # Physical adapter telemetry reader
│   ├── shaper.py                    # Asynchronous token-bucket proxy & WinINet manager
│   └── utils.py                     # Autostart registry helper, config persistence, UAC
├── ui/
│   ├── main_window.py               # Main Qt interface & System Tray integration
│   ├── sparkline.py                 # Real-time vector waveform widget
│   ├── styles.py                    # Dark theme stylesheet definition
│   └── toggle_switch.py             # Animated toggle switch widget
├── dist/
│   └── OpenLimiterPro_Setup.exe     # Unified Windows Setup Installer
├── installer.iss                    # Inno Setup 6 installer script
├── main.py                          # Program entry point
├── requirements.txt                 # Python runtime dependencies
└── README.md                        # Documentation
```

---

## Technical Considerations

- **Administrative Privileges**: Managing Windows NetQoS policies and system-level socket proxies requires elevated administrator rights. OpenLimiter Pro includes a UAC execution manifest to request elevation at launch.
- **Port Binding**: The local ingress shaper listens on loopback port `127.0.0.1:8899`. If another process occupies this port, OpenLimiter Pro gracefully handles the socket binding.
- **Safe Exit Guarantees**: A clean exit hook (`atexit`) ensures that even if the process is terminated unexpectedly, system proxy flags are reset to direct connection to avoid leaving the system in a disconnected state.

---

## License Information

Open source software. OpenLimiter Pro is freely distributable and customizable.
