from __future__ import annotations

import asyncio
import os

from app.browser_proxy import PinnedConnectProxy
from app.browser_security import BrowserPolicy, BrowserRequestGuard


async def serve() -> None:
    token = os.getenv("MOREAI_BROWSER_PROXY_TOKEN", "")
    domains = tuple(
        item.strip().lower().rstrip(".")
        for item in os.getenv("MOREAI_BROWSER_ALLOWED_DOMAINS", "").split(",")
        if item.strip()
    )
    if not domains:
        raise RuntimeError("browser_proxy_domain_allowlist_required")
    if len(token) < 32:
        raise RuntimeError("browser_proxy_token_required")
    policy = BrowserPolicy(allowed_domains=domains)
    guard = BrowserRequestGuard(policy)
    proxy = PinnedConnectProxy(guard, token=token)
    server = await proxy.serve(
        host=os.getenv("MOREAI_BROWSER_PROXY_HOST", "0.0.0.0"),
        port=int(os.getenv("MOREAI_BROWSER_PROXY_PORT", "8888")),
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(serve())
