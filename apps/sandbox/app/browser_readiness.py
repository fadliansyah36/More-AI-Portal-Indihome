from __future__ import annotations

import asyncio
import os
from urllib.parse import urlsplit


async def browser_readiness(
    *,
    proxy_url: str | None = None,
    proxy_token: str | None = None,
    egress_enforced: bool | None = None,
) -> dict[str, object]:
    """Report ready only when the configured private egress proxy is reachable."""
    proxy = proxy_url if proxy_url is not None else os.getenv("MOREAI_BROWSER_PROXY_URL", "")
    token = proxy_token if proxy_token is not None else os.getenv("MOREAI_BROWSER_PROXY_TOKEN", "")
    enforced = (
        egress_enforced if egress_enforced is not None
        else os.getenv("MOREAI_BROWSER_EGRESS_ENFORCED", "false").lower() == "true"
    )
    parsed = urlsplit(proxy)
    configured = (
        parsed.scheme == "http"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and parsed.port is not None
        and len(token) >= 32
        and enforced
    )
    reachable = False
    if configured:
        writer = None
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(parsed.hostname, parsed.port),
                timeout=1.5,
            )
            reachable = True
        except (OSError, TimeoutError):
            reachable = False
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
    return {
        "status": "ready" if configured and reachable else "degraded",
        "egress_enforced": enforced,
        "proxy_configured": configured,
        "proxy_reachable": reachable,
    }
