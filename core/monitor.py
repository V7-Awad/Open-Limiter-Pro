import time
import logging
from PySide6.QtCore import QThread, Signal
import psutil

logger = logging.getLogger("OpenLimiter.Monitor")

def get_physical_network_io():
    """
    Calculates total network I/O across physical adapters only,
    explicitly excluding Loopback and virtual adapters to prevent double-counting.
    """
    try:
        pernic = psutil.net_io_counters(pernic=True)
        total_recv = 0
        total_sent = 0
        for name, stats in pernic.items():
            name_lower = name.lower()
            if "loopback" in name_lower or "vmnet" in name_lower or "veth" in name_lower or "virtual" in name_lower:
                continue
            total_recv += stats.bytes_recv
            total_sent += stats.bytes_sent
        return total_recv, total_sent
    except Exception:
        io = psutil.net_io_counters()
        return io.bytes_recv, io.bytes_sent


class GlobalNetworkMonitor(QThread):
    """
    Measures the real physical throughput of the PC in Bytes/second.
    """
    # Emits (download_speed_bps, upload_speed_bps)
    speed_updated = Signal(float, float)

    def __init__(self, interval: float = 1.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.is_running = True
        self.prev_recv = 0
        self.prev_sent = 0
        self.prev_time = None

    def stop(self):
        self.is_running = False
        self.wait(1000)

    def run(self):
        logger.info("Physical network monitor started.")
        self.prev_recv, self.prev_sent = get_physical_network_io()
        self.prev_time = time.time()

        while self.is_running:
            time.sleep(self.interval)
            if not self.is_running:
                break

            now = time.time()
            curr_recv, curr_sent = get_physical_network_io()
            dt = now - self.prev_time

            if dt > 0.1:
                dl_speed = max(0.0, (curr_recv - self.prev_recv) / dt)
                up_speed = max(0.0, (curr_sent - self.prev_sent) / dt)
                self.speed_updated.emit(dl_speed, up_speed)

            self.prev_recv = curr_recv
            self.prev_sent = curr_sent
            self.prev_time = now

        logger.info("Physical network monitor stopped.")
