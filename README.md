# OpenLimiter Pro

OpenLimiter Pro is an open-source, system-wide network bandwidth controller and telemetry utility for Windows 10 and 11. It provides real-time traffic monitoring and bandwidth shaping for both download and upload streams.

## Features

- **System-Wide Bandwidth Control**: Throttle both download and upload throughput across the entire operating system.
- **Dual-Engine Architecture**:
  - Asynchronous token-bucket traffic shaper with local HTTP/HTTPS tunneling.
  - Native Windows Quality of Service (QoS) egress throttling policies.
- **Real-Time Telemetry**: Live throughput gauges with integrated vector sparkline history graphs.
- **Unit Synchronization**: Supports input and display in Megabits per second (Mbps), Megabytes per second (MB/s), and Kilobytes per second (KB/s).
- **Standalone Portable Executable**: Compiled standalone Windows binary with embedded icon and administrator manifest (`dist/OpenLimiterPro.exe`).

## Architecture

The project consists of two core layers:
1. `core/`:
   - `shaper.py`: High-performance asynchronous rate-pacing proxy and Windows system proxy controller.
   - `limiter.py`: Bandwidth controller managing both the user-mode token bucket and Windows QoS policies.
   - `monitor.py`: Background telemetry thread querying physical adapter I/O counters.
   - `utils.py`: Privilege elevation and dual-unit string formatters.
2. `ui/`:
   - `main_window.py`: Primary application interface.
   - `sparkline.py`: Vector waveform graph rendered with anti-aliasing.
   - `toggle_switch.py`: Custom animated switch component.
   - `styles.py`: Application visual stylesheet.

## Running the Application

### Option A: Standalone Executable
Run the pre-compiled binary directly:
```
dist/OpenLimiterPro.exe
```

### Option B: From Source
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python main.py
   ```

## License
MIT License.
