# OpenLimiter Pro

OpenLimiter Pro is an open-source, system-wide network bandwidth controller and telemetry utility for Windows 10 and 11. It provides real-time traffic monitoring and precise bandwidth shaping for both download and upload streams.

---

## Key Features

- **System-Wide Bandwidth Limiting**: Throttle both download and upload throughput across the entire operating system without per-application configuration.
- **Dual-Engine Shaping Architecture**:
  - Asynchronous token-bucket traffic shaper with local HTTP/HTTPS tunneling for precise ingress rate pacing.
  - Native Windows Quality of Service (QoS) egress throttling policies via Windows PowerShell management API.
- **Real-Time Telemetry**: Live throughput gauges with integrated anti-aliased vector sparkline graphs for instant visual feedback.
- **Unified Unit Selectors**: Set targets and read throughput in **Mbps**, **MB/s**, or **KB/s** with automatic dual-unit display and live calculation hints.
- **Professional Dark Interface**: Polished UI with smooth animations, elevated status indicator, and segmented preset pills.
- **Standalone Executable & Windows Installer**:
  - **Standalone Executable**: Portable single-file binary with embedded icons and automatic UAC elevation manifest.
  - **Windows Installer**: Complete setup wizard that installs to Program Files, creates Start Menu and Desktop shortcuts, and provides clean uninstallation.

---

## Installation & Usage

### 1. Using the Windows Installer (Recommended)
Download and run the installer:
```text
dist/OpenLimiterPro_Setup_v1.0.0.exe
```
This installs OpenLimiter Pro into your system, creates Desktop and Start Menu shortcuts, and integrates with Windows Programs & Features.

### 2. Using the Standalone Portable Executable
Run the portable executable directly without installation:
```text
dist/OpenLimiterPro.exe
```

### 3. Running from Source
1. **Prerequisites**: Python 3.10+ on Windows.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch**:
   ```bash
   python main.py
   ```

---

## Building from Source

### Compiling the Standalone Executable
To rebuild `OpenLimiterPro.exe`:
```bash
pyinstaller --noconfirm --onedir=False --windowed --uac-admin --icon="assets/icon.ico" --add-data="assets/icon.ico;assets" --add-data="assets/icon.png;assets" --name="OpenLimiterPro" main.py
```

### Compiling the Windows Setup Installer
OpenLimiter Pro uses Inno Setup 6:
```bash
ISCC installer.iss
```
The output installer will be generated in `dist/OpenLimiterPro_Setup_v1.0.0.exe`.

---

## Project Structure

```text
OpenLimiter/
├── assets/
│   ├── icon.ico            # Windows application icon
│   └── icon.png            # High-resolution application logo
├── core/
│   ├── limiter.py          # Bandwidth controller (QoS + Token-Bucket coordination)
│   ├── models.py           # Data structures and settings dataclasses
│   ├── monitor.py          # Adapter I/O telemetry background worker
│   ├── shaper.py           # Asynchronous token-bucket proxy & WinINet controller
│   └── utils.py            # UAC elevation, formatting utilities
├── ui/
│   ├── main_window.py      # Primary Qt application window
│   ├── sparkline.py        # Vector waveform graph
│   ├── styles.py           # Application visual stylesheet
│   └── toggle_switch.py    # Custom animated switch component
├── dist/
│   ├── OpenLimiterPro.exe                 # Portable executable
│   └── OpenLimiterPro_Setup_v1.0.0.exe    # Windows Setup Installer
├── installer.iss           # Inno Setup 6 installer script
├── main.py                 # Application entry point
├── requirements.txt        # Python package dependencies
└── README.md               # Documentation
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
