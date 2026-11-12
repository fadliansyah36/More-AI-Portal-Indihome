from __future__ import annotations

import asyncio
import ipaddress
import re
import base64
import socket
import logging
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.browser_security import BrowserPolicyError, BrowserRequestGuard

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProxyLimits:
    header_bytes: int = 16_384
    connect_timeout_seconds: float = 8.0
    idle_timeout_seconds: float = 60.0
    max_tunnel_seconds: float = 900.0


class PinnedConnectProxy:
    """Fail-closed HTTP CONNECT proxy; browser traffic must be forced through this listener.

    CONNECT establishes TLS end-to-end, so HTTP redirects are new CONNECT requests and
    are revalidated. Browser container network policy must deny all direct egress.
    """

    def __init__(self, guard: BrowserRequestGuard, *, token: str, limits: ProxyLimits = ProxyLimits()):
        if len(token) < 32:
            raise ValueError("browser_proxy_token_must_be_at_least_32_chars")
        self.guard, self.token, self.limits = guard, token, limits

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        upstream_writer = None
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=3)
            if len(raw) > self.limits.header_bytes:
                raise BrowserPolicyError("browser_proxy_request_too_large")
            line = raw.decode("ascii", "strict").strip().split()
            if len(line) != 3 or line[0].upper() != "CONNECT" or line[2] not in ("HTTP/1.0", "HTTP/1.1"):
                raise BrowserPolicyError("browser_proxy_connect_only")
            authority = line[1]
            if not re.fullmatch(r"\[[0-9A-Fa-f:]+\]:443|[A-Za-z0-9.-]+:443", authority):
                raise BrowserPolicyError("browser_proxy_authority_invalid")
            headers: dict[str, str] = {}
            total = len(raw)
            while True:
                header = await asyncio.wait_for(reader.readline(), timeout=3)
                total += len(header)
                if total > self.limits.header_bytes:
                    raise BrowserPolicyError("browser_proxy_headers_too_large")
                if header in (b"\r\n", b"\n"):
                    break
                key, sep, value = header.decode("latin-1").partition(":")
                if not sep:
                    raise BrowserPolicyError("browser_proxy_header_invalid")
                headers[key.strip().lower()] = value.strip()
            expected_auth = "Basic " + base64.b64encode(("moreai:" + self.token).encode()).decode("ascii")
            if headers.get("proxy-authorization") != expected_auth:
                writer.write(b"HTTP/1.1 407 Proxy Authentication Required\r\nConnection: close\r\n\r\n")
                await writer.drain()
                return
            host, port_text = authority.rsplit(":", 1)
            host = host.strip("[]")
            port = int(port_text)
            # resolve_pinned performs the validation and DNS lookup exactly once.
            # A second validation here could trigger false rebinding alarms on rotating DNS.
            pinned_host, _, addresses = await self.guard.resolve_pinned(f"https://{host}:{port}/")
            last_error = None
            for address in addresses:
                try:
                    upstream_reader, candidate = await asyncio.wait_for(
                        asyncio.open_connection(
                            address, port, family=socket.AF_INET6 if ":" in address else socket.AF_INET,
                            ssl=None,
                        ), timeout=self.limits.connect_timeout_seconds,
                    )
                    peer = candidate.get_extra_info("peername")
                    if not peer or str(ipaddress.ip_address(peer[0])) != address:
                        candidate.close()
                        await candidate.wait_closed()
                        raise BrowserPolicyError("browser_proxy_peer_ip_mismatch")
                    upstream_writer = candidate
                    break
                except OSError as exc:
                    last_error = exc
            if upstream_writer is None:
                raise BrowserPolicyError("browser_proxy_upstream_unavailable") from last_error
            writer.write(b"HTTP/1.1 200 Connection Established\r\nProxy-Agent: MoreAI-Egress\r\n\r\n")
            await writer.drain()
            async def relay(source: asyncio.StreamReader, destination: asyncio.StreamWriter):
                while True:
                    chunk = await asyncio.wait_for(source.read(65536), timeout=self.limits.idle_timeout_seconds)
                    if not chunk:
                        return
                    destination.write(chunk)
                    await destination.drain()
            await asyncio.wait_for(
                asyncio.gather(relay(reader, upstream_writer), relay(upstream_reader, writer)),
                timeout=self.limits.max_tunnel_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("browser proxy request failed (%s)", str(exc) if isinstance(exc, BrowserPolicyError) else type(exc).__name__)
            if not writer.is_closing():
                try:
                    writer.write(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n")
                    await writer.drain()
                except Exception:
                    pass
        finally:
            if upstream_writer is not None:
                upstream_writer.close()
                try:
                    await upstream_writer.wait_closed()
                except OSError:
                    pass
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    async def serve(self, host: str = "0.0.0.0", port: int = 8888) -> asyncio.AbstractServer:
        return await asyncio.start_server(self.handle, host, port, limit=self.limits.header_bytes)
