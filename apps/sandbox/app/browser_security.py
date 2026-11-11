from __future__ import annotations

import asyncio
import ipaddress
import socket
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
