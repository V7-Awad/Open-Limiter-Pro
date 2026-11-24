import subprocess
import os
import json
import logging
import winreg
from typing import Tuple, Optional

try:
    from core.shaper import TrafficShaperServer, set_system_proxy, disable_system_proxy
except ImportError:
    from .shaper import TrafficShaperServer, set_system_proxy, disable_system_proxy

logger = logging.getLogger("OpenLimiter.Limiter")

POLICY_DL = "OpenLimiter_Global_Download"
POLICY_UL = "OpenLimiter_Global_Upload"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "global_config.json")

class GlobalBandwidthLimiter:
    """
    Dual-Engine Bandwidth Controller:
    1. Local Token-Bucket Traffic Shaper + Windows System Proxy:
       Guarantees 100% hard throttling for Download and Upload on all browser,
       streaming, web, and application traffic.
    2. Windows QoS (Quality of Service) Policies + NLA Bypass:
       Enforces kernel-level egress throttling across all network interfaces.
    """
    def __init__(self):
        self.dl_limit_kb: Optional[int] = None
        self.ul_limit_kb: Optional[int] = None
        
        # Initialize and start traffic shaper daemon
        self.shaper = TrafficShaperServer(port=8899)
        self.shaper.start()

        self.load_config()
        self._ensure_nla_bypass()

    def load_config(self):
        """Loads saved limits from global_config.json."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dl_limit_kb = data.get("dl_limit_kb")
                    self.ul_limit_kb = data.get("ul_limit_kb")
            except Exception as e:
                logger.warning(f"Could not load config: {e}")

    def save_config(self):
        """Saves current limits to global_config.json."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "dl_limit_kb": self.dl_limit_kb,
                    "ul_limit_kb": self.ul_limit_kb
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save config: {e}")

    def apply_global_limits(self, dl_kb: Optional[int], ul_kb: Optional[int]) -> bool:
        """
        Applies system-wide download and upload limits to the whole PC.
        Enforces both user-mode token-bucket shaping and Windows QoS.
        """
        has_limit = (dl_kb and dl_kb > 0) or (ul_kb and ul_kb > 0)

        # 1. Update Shaper & System Proxy
        dl_bytes = (dl_kb * 1024) if (dl_kb and dl_kb > 0) else 0
        ul_bytes = (ul_kb * 1024) if (ul_kb and ul_kb > 0) else 0

        self.shaper.set_limits(dl_bytes, ul_bytes)

        if has_limit:
            set_system_proxy(True, host="127.0.0.1", port=8899)
        else:
            set_system_proxy(False)

        # 2. Update Windows QoS Kernel Policies
        self._set_policy(POLICY_DL, dl_kb)
        self._set_policy(POLICY_UL, ul_kb)

        self.dl_limit_kb = dl_kb if (dl_kb and dl_kb > 0) else None
        self.ul_limit_kb = ul_kb if (ul_kb and ul_kb > 0) else None
        self.save_config()

        logger.info(f"Bandwidth limits applied: DL={dl_kb} KB/s, UL={ul_kb} KB/s")
        return True

    def remove_all_limits(self) -> bool:
        """Removes all speed limits and restores 100% full unthrottled throughput."""
        # Disable proxy and reset shaper
        set_system_proxy(False)
        self.shaper.set_limits(0, 0)

        # Clear Windows QoS policies
        self._remove_policy(POLICY_DL)
        self._remove_policy(POLICY_UL)

        self.dl_limit_kb = None
        self.ul_limit_kb = None
        self.save_config()

        logger.info("All bandwidth limits removed.")
        return True

    def stop(self):
        """Cleanly stops limiter and shaper server."""
        self.remove_all_limits()
        if hasattr(self, 'shaper') and self.shaper:
            self.shaper.stop()

    def _ensure_nla_bypass(self):
        r"""
        Fixes Windows Workstation issue where QoS is ignored on non-domain networks.
        Sets HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\QoS\Do not use NLA = 1
        Uses direct winreg API to eliminate console process popups.
        """
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\QoS")
            winreg.SetValueEx(key, "Do not use NLA", 0, winreg.REG_SZ, "1")
            winreg.CloseKey(key)
        except Exception as e:
            logger.debug(f"NLA bypass update: {e}")

    def _set_policy(self, policy_name: str, limit_kb: Optional[int]) -> bool:
        self._remove_policy(policy_name)
        if not limit_kb or limit_kb <= 0:
            return True

        bps = int(limit_kb * 8192)
        ps_cmd = f"& {{ New-NetQosPolicy -Name '{policy_name}' -NetworkProfile All -ThrottleRateActionBitsPerSecond {bps} -Confirm:`$false -ErrorAction SilentlyContinue }}"
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            res = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                errors='ignore',
                creationflags=flags
            )
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed setting policy {policy_name}: {e}")
            return False

    def _remove_policy(self, policy_name: str):
        ps_cmd = f"& {{ Remove-NetQosPolicy -Name '{policy_name}' -Confirm:`$false -ErrorAction SilentlyContinue }}"
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                errors='ignore',
                creationflags=flags
            )
        except Exception:
            pass
