from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urlsplit


class BrowserPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class BrowserPolicy:
    allowed_domains: tuple[str, ...]
    max_download_bytes: int = 10_000_000
    allowed_schemes: tuple[str, ...] = ("https",)


def _domain_allowed(host: str, allowlist: tuple[str, ...]) -> bool:
    host = host.rstrip(".").lower()
    for entry in allowlist:
        domain = entry.lstrip(".").rstrip(".").lower()
        if host == domain or host.endswith("." + domain):
            return True
    return False


async def validate_navigation_url(url: str, policy: BrowserPolicy) -> str:
    """Rejects non-web schemes, credentials, unapproved hosts and private/reserved DNS answers."""
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in policy.allowed_schemes:
        raise BrowserPolicyError("browser_scheme_denied")
    if not parsed.hostname or parsed.username or parsed.password:
        raise BrowserPolicyError("browser_url_invalid")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    if not _domain_allowed(host, policy.allowed_domains):
        raise BrowserPolicyError("browser_domain_not_allowlisted")
    try:
        literal = ipaddress.ip_address(host)
        addresses = [literal]
    except ValueError:
        try:
            records = await asyncio.get_running_loop().getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise BrowserPolicyError("browser_dns_resolution_failed") from exc
        addresses = [ipaddress.ip_address(record[4][0]) for record in records]
    if not addresses or any(not (ip.is_global and not ip.is_multicast and not ip.is_unspecified) for ip in addresses):
        raise BrowserPolicyError("browser_private_or_reserved_address_denied")
    return url


def validate_download(*, size_bytes: int, content_type: str, policy: BrowserPolicy, scanner_available: bool, scan_clean: bool) -> None:
    if size_bytes < 0 or size_bytes > policy.max_download_bytes:
        raise BrowserPolicyError("browser_download_size_denied")
    if not scanner_available:
        raise BrowserPolicyError("browser_download_scanner_unavailable")
    if not scan_clean:
        raise BrowserPolicyError("browser_download_scan_failed")
    if not content_type or content_type in {"application/x-msdownload", "application/x-executable"}:
        raise BrowserPolicyError("browser_download_content_type_denied")


class BrowserRequestGuard:
    """Per-browser-session SSRF guard with conservative DNS pinning.

    Call validate_request for the initial URL and for EVERY redirected or
    intercepted subresource request. Browser automation must route all network
    requests through this guard; a navigation-only call is insufficient.
    """

    def __init__(self, policy: BrowserPolicy, resolver=None):
        self.policy = policy
        self.resolver = resolver
        self._pinned: dict[str, frozenset[str]] = {}

    async def validate_request(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in self.policy.allowed_schemes:
            raise BrowserPolicyError("browser_scheme_denied")
        if parsed.port not in (None, 443):
            raise BrowserPolicyError("browser_port_denied")
        if not parsed.hostname or parsed.username or parsed.password:
            raise BrowserPolicyError("browser_url_invalid")
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if not _domain_allowed(host, self.policy.allowed_domains):
            raise BrowserPolicyError("browser_domain_not_allowlisted")
        try:
            literal = ipaddress.ip_address(host)
            addresses = frozenset({str(literal)})
        except ValueError:
            try:
                if self.resolver is None:
                    records = await asyncio.get_running_loop().getaddrinfo(
                        host, 443, type=socket.SOCK_STREAM
                    )
                else:
                    records = await self.resolver(host, 443, socket.SOCK_STREAM)
            except OSError as exc:
                raise BrowserPolicyError("browser_dns_resolution_failed") from exc
            addresses = frozenset(str(ipaddress.ip_address(record[4][0])) for record in records)
        if not addresses:
            raise BrowserPolicyError("browser_dns_resolution_empty")
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if not ip.is_global or ip.is_multicast or ip.is_unspecified:
                raise BrowserPolicyError("browser_private_or_reserved_address_denied")
        pinned = self._pinned.get(host)
        if pinned is not None and pinned != addresses:
            raise BrowserPolicyError("browser_dns_rebinding_detected")
        self._pinned.setdefault(host, addresses)
        return url

    async def resolve_pinned(self, url: str) -> tuple[str, int, tuple[str, ...]]:
        await self.validate_request(url)
        parsed = urlsplit(url)
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        port = parsed.port or 443
        pinned = self._pinned.get(host)
        if not pinned:
            raise BrowserPolicyError("browser_dns_pin_missing")
        return host, port, tuple(sorted(pinned))

    async def open_pinned_tls_connection(self, url: str):
        """Open TLS directly to a pinned IP; never let the socket layer resolve the hostname again.

        This is the transport primitive for a browser egress proxy/route handler.
        Browser engines must be configured to use this transport exclusively;
        calling validate_request from page code alone is not an egress boundary.
        """
        host, port, addresses = await self.resolve_pinned(url)
        last_error: OSError | None = None
        for address in addresses:
            context = ssl.create_default_context()
            try:
                reader, writer = await asyncio.open_connection(
                    host=address, port=port, ssl=context, server_hostname=host,
                    family=socket.AF_INET6 if ":" in address else socket.AF_INET,
                )
                peer = writer.get_extra_info("peername")
                if not peer or str(ipaddress.ip_address(peer[0])) != address:
                    writer.close()
                    await writer.wait_closed()
                    raise BrowserPolicyError("browser_socket_peer_did_not_match_dns_pin")
                return reader, writer
            except OSError as exc:
                last_error = exc
        raise BrowserPolicyError("browser_pinned_connection_failed") from last_error

    async def validate_redirect_chain(self, urls: list[str]) -> str:
        if not urls or len(urls) > 20:
            raise BrowserPolicyError("browser_redirect_chain_invalid")
        for url in urls:
            await self.validate_request(url)
        return urls[-1]
