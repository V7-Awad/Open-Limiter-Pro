import ctypes
import os
import sys
from typing import Tuple

def is_admin() -> bool:
    """Checks if the current process has administrative privileges on Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def restart_as_admin():
    """Relaunches the current script with elevated administrator privileges."""
    if is_admin():
        return True
    
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    
    # Execute ShellExecuteW with 'runas' verb to trigger UAC prompt
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            python_exe,
            f'"{script_path}" {params}',
            None,
            1 # SW_SHOWNORMAL
        )
        if ret > 32:
            sys.exit(0)
            return True
        return False
    except Exception as e:
        print(f"Failed to elevate: {e}")
        return False

def format_speed(bytes_per_sec: float) -> str:
    """Formats bytes per second into human-readable rate string (B/s, KB/s, MB/s, GB/s)."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.1f} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"

def format_speed_dual(bytes_per_sec: float) -> Tuple[str, str]:
    """
    Returns both Byte rate (Chrome / Downloads) and Bit rate (Fast.com / Speedtest).
    Example: ("512.0 KB/s", "4.1 Mbps")
    """
    # 1. Byte rate
    byte_str = format_speed(bytes_per_sec)

    # 2. Bit rate (bits per sec = bytes * 8)
    bits_per_sec = bytes_per_sec * 8.0
    if bits_per_sec < 1000:
        bit_str = f"{bits_per_sec:.0f} bps"
    elif bits_per_sec < 1000 * 1000:
        bit_str = f"{bits_per_sec / 1000:.1f} Kbps"
    elif bits_per_sec < 1000 * 1000 * 1000:
        bit_str = f"{bits_per_sec / (1000 * 1000):.1f} Mbps"
    else:
        bit_str = f"{bits_per_sec / (1000 * 1000 * 1000):.2f} Gbps"

    return byte_str, bit_str

def format_bytes(total_bytes: int) -> str:
    """Formats total byte count into human-readable string (KB, MB, GB)."""
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f} KB"
    elif total_bytes < 1024 * 1024 * 1024:
        return f"{total_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"
