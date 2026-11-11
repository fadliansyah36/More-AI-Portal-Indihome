from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class BrowserLimits:
    navigation_timeout_ms: int = 20_000
    max_page_text_chars: int = 30_000


class BrowserSupervisor:
    """Playwright adapter that requires an authenticated mandatory egress proxy.

    The browser container/network namespace MUST deny direct outbound traffic.
    This class alone is not a network firewall and intentionally refuses to start
    unless deployment asserts that the network-level egress gate is active.
    """

    def __init__(self, *, proxy_server: str, proxy_token: str, egress_enforced: bool, limits: BrowserLimits = BrowserLimits()):
        if not egress_enforced:
            raise RuntimeError("browser_network_egress_enforcement_required")
        parsed = urlsplit(proxy_server)
        if parsed.scheme != "http" or not parsed.hostname or parsed.port is None:
            raise ValueError("browser_proxy_server_invalid")
        if len(proxy_token) < 32:
            raise ValueError("browser_proxy_token_invalid")
        self.proxy_server, self.proxy_token, self.limits = proxy_server, proxy_token, limits

    async def browser_use(self, arguments: dict, *, run_id: str, user_id: str) -> str:
        import json
        from playwright.async_api import async_playwright

        url = arguments.get("url")
        action = arguments.get("action")
        parsed = urlsplit(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("browser_url_must_be_https_without_credentials")
        if action not in ("navigate", "extract"):
            raise ValueError("browser_action_not_supported_by_supervisor")
        proxy = {
            "server": self.proxy_server,
            "username": "moreai",
            "password": self.proxy_token,
        }
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    "--disable-quic", "--disable-background-networking",
                    "--disable-component-update", "--disable-sync",
                    "--no-first-run", "--proxy-bypass-list=<-loopback>",
                ],
            )
            try:
                context = await browser.new_context(
                    accept_downloads=False,
                    service_workers="block",
                    java_script_enabled=True,
                    ignore_https_errors=False,
                )
                page = await context.new_page()
                async def request_guard(route):
                    request_url = route.request.url
                    request_parsed = urlsplit(request_url)
                    if request_parsed.scheme != "https" or not request_parsed.hostname:
                        await route.abort("blockedbyclient")
                    else:
                        await route.continue_()
                await page.route("**/*", request_guard)
                await page.goto(url, wait_until="domcontentloaded", timeout=self.limits.navigation_timeout_ms)
                if action == "navigate":
                    return json.dumps({"status":"navigated","url":page.url,"title":await page.title()},separators=(",",":"))
                text = (await page.locator("body").inner_text(timeout=5000))[:self.limits.max_page_text_chars]
                return json.dumps({"status":"extracted","url":page.url,"title":await page.title(),"text":text},ensure_ascii=False,separators=(",",":"))
            finally:
                await browser.close()
