from __future__ import annotations

import os
from urllib.parse import urlsplit
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

app = FastAPI(title="MoreAI Isolated Browser Supervisor", version="0.1.0")


class BrowserAction(BaseModel):
    url: str = Field(min_length=9, max_length=2048)
    action: Literal["navigate", "extract"]
    run_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)


def _authorize(value: str | None) -> None:
    token = os.getenv("MOREAI_BROWSER_SERVICE_TOKEN", "")
    if len(token) < 32 or value != f"Bearer {token}":
        raise HTTPException(401, "browser_supervisor_unauthorized")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "moreai-browser-supervisor"}


@app.get("/ready")
async def ready(authorization: str | None = Header(default=None)):
    _authorize(authorization)
    from .browser_readiness import browser_readiness

    result = await browser_readiness()
    if result["status"] != "ready":
        raise HTTPException(503, "browser_egress_proxy_not_ready")
    return result


@app.post("/v1/browser/actions")
async def browser_action(body: BrowserAction, authorization: str | None = Header(default=None)):
    import asyncio
    import json

    _authorize(authorization)
    parsed = urlsplit(body.url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(400, "browser_url_invalid")
    proxy_url = os.getenv("MOREAI_BROWSER_PROXY_URL", "")
    proxy_token = os.getenv("MOREAI_BROWSER_PROXY_TOKEN", "")
    if not proxy_url.startswith("http://") or len(proxy_token) < 32:
        raise HTTPException(503, "browser_egress_proxy_not_configured")
    if os.getenv("MOREAI_BROWSER_EGRESS_ENFORCED", "false").lower() != "true":
        raise HTTPException(503, "browser_network_egress_not_enforced")

    proxy = {"server": proxy_url, "username": "moreai", "password": proxy_token}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            proxy=proxy,
            args=[
                "--disable-quic", "--disable-background-networking",
                "--disable-component-update", "--disable-sync", "--no-first-run",
                "--proxy-bypass-list=<-loopback>",
            ],
        )
        try:
            context = await browser.new_context(
                accept_downloads=False, service_workers="block",
                ignore_https_errors=False,
            )
            page = await context.new_page()
            request_count = 0
            max_requests = 200

            async def request_guard(route):
                nonlocal request_count
                request_count += 1
                request = urlsplit(route.request.url)
                if request_count > max_requests or request.scheme != "https" or not request.hostname or request.username or request.password:
                    await route.abort("blockedbyclient")
                    return
                await route.continue_()

            await page.route("**/*", request_guard)
            # WebSockets are not part of the approved browser action contract; deny them
            # rather than allowing a secondary channel outside normal request inspection.
            async def deny_websocket(websocket):
                await websocket.close(code=1008)

            await page.route_web_socket("**/*", deny_websocket)
            try:
                await page.goto(body.url, wait_until="domcontentloaded", timeout=20_000)
            except Exception as exc:
                # Do not expose Playwright internals, request URLs, or proxy details.
                raise HTTPException(502, "browser_navigation_blocked_or_failed") from exc
            if body.action == "navigate":
                return {"status": "navigated", "url": page.url, "title": await page.title(), "requests": request_count}
            content = (await page.locator("body").inner_text(timeout=5_000))[:30_000]
            return {"status": "extracted", "url": page.url, "title": await page.title(), "text": content, "requests": request_count}
        finally:
            await browser.close()
