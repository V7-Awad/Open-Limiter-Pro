import ctypes
import json
import os
import sys
import winreg
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

def get_config_dir() -> str:
    """Returns directory path for storing user configuration."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = os.path.expanduser("~")
    config_dir = os.path.join(appdata, "OpenLimiterPro")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path() -> str:
    """Returns absolute path to the config.json file."""
    return os.path.join(get_config_dir(), "config.json")

def load_config() -> dict:
    """Loads saved settings from config.json with fallback defaults."""
    default_config = {
        "dl_value": 2.0,
        "dl_unit": 0,  # 0: Mbps (Speedtest/Fast.com)
        "dl_enabled": True,
        "ul_value": 1.0,
        "ul_unit": 0,  # 0: Mbps (Speedtest/Fast.com)
        "ul_enabled": True,
        "engaged": False,
        "autostart": True,
    }
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception as e:
            print(f"Failed to load config: {e}")
    return default_config

def save_config(config: dict):
    """Persists settings dictionary to config.json."""
    try:
        path = get_config_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")

def set_autostart(enable: bool) -> bool:
    """
    Configures Windows registry to launch OpenLimiter Pro at user logon.
    Key: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "OpenLimiterPro"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}" --minimized'
            else:
                main_py = os.path.abspath(sys.argv[0])
                cmd = f'"{sys.executable}" "{main_py}" --minimized'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to configure autostart: {e}")
        return False

def is_autostart_enabled() -> bool:
    """Checks whether the application is registered in Windows startup registry."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "OpenLimiterPro"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_QUERY_VALUE)
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except Exception:
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
    byte_str = format_speed(bytes_per_sec)

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
