import asyncio
import time
import threading
import winreg
import ctypes
import logging
import atexit

logger = logging.getLogger("OpenLimiter.Shaper")

INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37
_PROXY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
_proxy_backup = None

def set_system_proxy(enable: bool, host: str = "127.0.0.1", port: int = 8899) -> bool:
    """
    Configures Windows system-wide Internet Settings proxy.
    Notifies wininet to reload configuration immediately.
    """
    global _proxy_backup
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _PROXY_KEY,
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE
        )
        if enable:
            if _proxy_backup is None:
                _proxy_backup = {}
                for name in ("ProxyEnable", "ProxyServer", "ProxyOverride"):
                    try:
                        _proxy_backup[name] = winreg.QueryValueEx(key, name)
                    except FileNotFoundError:
                        _proxy_backup[name] = None
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "localhost;127.*;10.*;192.168.*;<local>")
            logger.info(f"System proxy enabled: {host}:{port}")
        else:
            if _proxy_backup is None:
                try:
                    current_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    current_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                except FileNotFoundError:
                    current_server, current_enabled = None, 0
                # Do not disable a proxy configured by another application.
                if current_enabled and current_server == f"{host}:{port}":
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            else:
                for name, saved in _proxy_backup.items():
                    if saved is None:
                        try:
                            winreg.DeleteValue(key, name)
                        except FileNotFoundError:
                            pass
                    else:
                        value, value_type = saved
                        winreg.SetValueEx(key, name, 0, value_type, value)
                _proxy_backup = None
            logger.info("System proxy settings restored.")
        winreg.CloseKey(key)

        # Notify WinINet
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        return True
    except Exception as e:
        logger.error(f"Failed to set system proxy: {e}")
        return False

def disable_system_proxy():
    set_system_proxy(False)

# Ensure proxy is always disabled when Python exits to prevent network disruption
atexit.register(disable_system_proxy)


class TokenBucket:
    """
    Thread-safe token-bucket rate limiter for smooth bandwidth pacing.
    """
    def __init__(self, rate_bytes_sec: int):
        self.rate = rate_bytes_sec
        self.capacity = max(rate_bytes_sec * 0.2, 32768)
        self.tokens = self.capacity
        self.last_time = time.time()
        self.lock = asyncio.Lock()

    def update_rate(self, rate_bytes_sec: int):
        self.rate = max(0, rate_bytes_sec)
        self.capacity = max(self.rate * 0.2, 32768)

    async def consume(self, amount: int):
        if self.rate <= 0:
            return # Unlimited
        async with self.lock:
            while amount > 0:
                now = time.time()
                elapsed = now - self.last_time
                self.last_time = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                if self.tokens >= amount:
                    self.tokens -= amount
                    return
                needed = amount - self.tokens
                wait_time = needed / self.rate
                await asyncio.sleep(min(wait_time, 0.04))


class TrafficShaperServer:
    """
    High-performance async streaming proxy server running on 127.0.0.1:8899.
    Implements byte-level token-bucket rate limiting for both Download and Upload streams.
    """
    def __init__(self, port: int = 8899):
        self.port = port
        self.dl_bucket = TokenBucket(0)
        self.ul_bucket = TokenBucket(0)
        self.server = None
        self.loop = None
        self.thread = None
        self.is_running = False
        self._ready = threading.Event()
        self._startup_error = None

    def set_limits(self, dl_bytes_sec: int, ul_bytes_sec: int):
        self.dl_bucket.update_rate(dl_bytes_sec)
        self.ul_bucket.update_rate(ul_bytes_sec)

    def start(self):
        if self.is_running:
            return self._ready.wait(0)
        self.is_running = True
        self._ready.clear()
        self._startup_error = None
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        if not self._ready.wait(3.0):
            self.is_running = False
            logger.error("Timed out waiting for traffic shaper to bind port %s", self.port)
            return False
        return self._startup_error is None

    def stop(self):
        self.is_running = False
        disable_system_proxy()
        if self.loop and self.server:
            self.loop.call_soon_threadsafe(self.server.close)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._serve())
        except Exception as e:
            self._startup_error = e
            self._ready.set()
            logger.error(f"Shaper loop exception: {e}")
        finally:
            if not self.loop.is_closed():
                self.loop.close()

    async def _serve(self):
        self.server = await asyncio.start_server(self._handle_client, '127.0.0.1', self.port)
        logger.info(f"Traffic shaper active on 127.0.0.1:{self.port}")
        self._ready.set()
        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(self, client_reader, client_writer):
        try:
            req_line = await client_reader.readline()
            if not req_line:
                client_writer.close()
                return

            line_str = req_line.decode('latin1', 'ignore').strip()
            parts = line_str.split()
            if len(parts) < 2:
                client_writer.close()
                return

            method, target = parts[0], parts[1]

            # Read headers
            headers = []
            while True:
                h_line = await client_reader.readline()
                if not h_line or h_line == b'\r\n':
                    break
                headers.append(h_line)

            if method.upper() == 'CONNECT':
                # HTTPS Tunneling
                if ':' in target:
                    host, port_str = target.split(':', 1)
                    port = int(port_str)
                else:
                    host, port = target, 443

                try:
                    remote_reader, remote_writer = await asyncio.open_connection(host, port)
                except Exception:
                    client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await client_writer.drain()
                    client_writer.close()
                    return

                client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await client_writer.drain()

                # Bidirectional throttled streaming
                async def pipe_up():
                    try:
                        while True:
                            data = await client_reader.read(32768)
                            if not data:
                                break
                            await self.ul_bucket.consume(len(data))
                            remote_writer.write(data)
                            await remote_writer.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            remote_writer.close()
                        except Exception:
                            pass

                async def pipe_down():
                    try:
                        while True:
                            data = await remote_reader.read(32768)
                            if not data:
                                break
                            await self.dl_bucket.consume(len(data))
                            client_writer.write(data)
                            await client_writer.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            client_writer.close()
                        except Exception:
                            pass

                await asyncio.gather(pipe_up(), pipe_down())

            else:
                # Direct HTTP Forwarding
                host = None
                port = 80
                for h in headers:
                    if h.lower().startswith(b'host:'):
                        host_val = h.decode('latin1', 'ignore').split(':', 1)[1].strip()
                        if ':' in host_val:
                            host, p = host_val.split(':', 1)
                            port = int(p)
                        else:
                            host = host_val
                        break

                if not host:
                    client_writer.close()
                    return

                try:
                    remote_reader, remote_writer = await asyncio.open_connection(host, port)
                except Exception:
                    client_writer.close()
                    return

                remote_writer.write(req_line)
                for h in headers:
                    remote_writer.write(h)
                remote_writer.write(b'\r\n')
                await remote_writer.drain()

                async def pipe_up():
                    try:
                        while True:
                            data = await client_reader.read(32768)
                            if not data:
                                break
                            await self.ul_bucket.consume(len(data))
                            remote_writer.write(data)
                            await remote_writer.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            remote_writer.close()
                        except Exception:
                            pass

                async def pipe_down():
                    try:
                        while True:
                            data = await remote_reader.read(32768)
                            if not data:
                                break
                            await self.dl_bucket.consume(len(data))
                            client_writer.write(data)
                            await client_writer.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            client_writer.close()
                        except Exception:
                            pass

                await asyncio.gather(pipe_up(), pipe_down())

        except Exception:
            pass
        finally:
            try:
                client_writer.close()
            except Exception:
                pass
