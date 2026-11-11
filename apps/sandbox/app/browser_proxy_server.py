from __future__ import annotations

import asyncio
import os

from apps.sandbox.app.browser_proxy import PinnedConnectProxy
from apps.sandbox.app.browser_security import BrowserPolicy, BrowserRequestGuard


async def main() -> None:
    token = os.getenv("MOREAI_BROWSER_PROXY_TOKEN", "")
    domains = tuple(
        item.strip().lower()
        for item in os.getenv("MOREAI_BROWSER_ALLOWED_DOMAINS", "").split(",")
        if item.strip()
    )
    if len(token) < 32 or not domains:
        raise RuntimeError("browser_proxy_requires_token_and_domain_allowlist")
    policy = BrowserPolicy(allowed_domains=domains)
    proxy = PinnedConnectProxy(BrowserRequestGuard(policy), token=token)
    server = await proxy.serve(
        host=os.getenv("MOREAI_BROWSER_PROXY_HOST", "0.0.0.0"),
        port=int(os.getenv("MOREAI_BROWSER_PROXY_PORT", "8888")),
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
