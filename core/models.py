from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ConnectionInfo:
    protocol: str       # "TCP" or "UDP"
    local_address: str  # "ip:port"
    remote_address: str # "ip:port"
    state: str          # "ESTABLISHED", "LISTEN", etc.

@dataclass
class ProcessInfo:
    pid: int
    name: str
    path: str
    upload_speed: float = 0.0      # Bytes per second
    download_speed: float = 0.0    # Bytes per second
    total_uploaded: int = 0        # Total bytes
    total_downloaded: int = 0      # Total bytes
    upload_limit_kb: Optional[int] = None   # KB/s, None = Unlimited
    download_limit_kb: Optional[int] = None # KB/s, None = Unlimited
    is_blocked: bool = False
    connections: List[ConnectionInfo] = field(default_factory=list)
