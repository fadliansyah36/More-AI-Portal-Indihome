from __future__ import annotations

import os
import logging
import base64
import asyncio
import hashlib
import struct
from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

app = FastAPI(title="MoreAI Isolated Browser Supervisor", version="0.1.0")
logger = logging.getLogger(__name__)

MAX_DOWNLOAD_BYTES = 10_000_000

def _detect_download_mime(data: bytes) -> str:
    if data.startswith(b"%PDF-"): return "application/pdf"
    if data.startswith(b"\x89PNG\\r\\n\x1a\\n"): return "image/png"
    if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP": return "image/webp"
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06")): return "application/zip"
    try: value = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError: return "application/octet-stream"
    if "\x00" in value: return "application/octet-stream"
    if value.lstrip().startswith(("{", "[")):
        try:
            import json
            json.loads(value)
            return "application/json"
        except Exception: pass
    return "text/csv" if value.splitlines() and "," in value.splitlines()[0] else "text/plain"

async def _clamav_scan(data: bytes) -> None:
    host = os.getenv("MOREAI_CLAMAV_HOST", "")
    port = int(os.getenv("MOREAI_CLAMAV_PORT", "3310"))
    if not host: raise RuntimeError("download_malware_scanner_not_configured")
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
    try:
        writer.write(b"zINSTREAM\0")
        await writer.drain()
        for offset in range(0, len(data), 65536):
            chunk = data[offset:offset + 65536]
            writer.write(struct.pack("!I", len(chunk)) + chunk)
            await writer.drain()
        writer.write(struct.pack("!I", 0))
        await writer.drain()
        verdict = await asyncio.wait_for(reader.read(4096), timeout=20)
        if not verdict.endswith(b"OK"): raise RuntimeError("download_malware_scan_rejected")
    finally:
        writer.close()
        await writer.wait_closed()


class BrowserAction(BaseModel):
    url: str = Field(min_length=9, max_length=2048)
    action: Literal["navigate", "extract"]
    run_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    storage_state: dict = Field(default_factory=dict, max_length=1000)


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
    if (
        parsed.scheme != "https" or not parsed.hostname
        or parsed.username or parsed.password or parsed.port not in (None, 443)
    ):
        raise HTTPException(400, "browser_url_invalid")
    from .browser_security import BrowserPolicy
    allowed_domains = tuple(
        item.strip().lower().rstrip(".")
        for item in os.getenv("MOREAI_BROWSER_ALLOWED_DOMAINS", "").split(",")
        if item.strip()
    )
    if not allowed_domains:
        raise HTTPException(503, "browser_domain_allowlist_not_configured")
    policy = BrowserPolicy(allowed_domains=allowed_domains)
    initial_host = parsed.hostname.encode("idna").decode("ascii").lower()
    if not policy.allows_host(initial_host):
        raise HTTPException(403, "browser_navigation_target_not_allowlisted")
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
                "--no-default-browser-check", "--disable-default-apps",
                "--disable-extensions", "--disable-translate",
                "--disable-features=MediaRouter,OptimizationHints",
                "--proxy-bypass-list=<-loopback>",
            ],
        )
        try:
            context = await browser.new_context(
                accept_downloads=True, service_workers="block",
                ignore_https_errors=False, storage_state=body.storage_state or None,
            )
            page = await context.new_page()
            request_count = 0
            blocked_downloads = 0
            downloads: list[dict] = []
            download_tasks: set[asyncio.Task] = set()
            max_requests = 200

            # Browser actions currently expose navigation and text extraction only.
            # Never persist untrusted downloads into the supervisor filesystem.
            async def capture_download(download):
                nonlocal blocked_downloads
                try:
                    filename = Path(download.suggested_filename).name[:160]
                    if not filename or len(downloads) >= 3: raise RuntimeError("download_count_limit")
                    path = await download.path()
                    if not path: raise RuntimeError("download_tempfile_missing")
                    data = await asyncio.to_thread(Path(path).read_bytes)
                    if not data or len(data) > MAX_DOWNLOAD_BYTES: raise RuntimeError("download_size_limit")
                    mime = _detect_download_mime(data)
                    allowed = {"application/pdf", "image/png", "image/jpeg", "image/webp", "application/zip", "text/plain", "text/csv", "application/json"}
                    if mime not in allowed: raise RuntimeError("download_mime_not_allowed")
                    if mime in {"text/plain", "text/csv", "application/json"}: data.decode("utf-8", errors="strict")
                    if mime == "image/webp" and data[8:12] != b"WEBP": raise RuntimeError("download_signature_invalid")
                    await _clamav_scan(data)
                    downloads.append({"filename": filename, "mime_type": mime, "size_bytes": len(data),
                        "checksum_sha256": hashlib.sha256(data).hexdigest(),
                        "content_base64": base64.b64encode(data).decode("ascii"), "scan_status": "clean"})
                except Exception as exc:
                    blocked_downloads += 1
                    logger.warning("browser download quarantined (%s)", type(exc).__name__)
                    try: await download.cancel()
                    except Exception: pass

            def on_download(download):
                task = asyncio.create_task(capture_download(download))
                download_tasks.add(task)
                task.add_done_callback(download_tasks.discard)

            page.on("download", on_download)

            async def request_guard(route):
                nonlocal request_count
                request_count += 1
                request = urlsplit(route.request.url)
                request_host = (
                    request.hostname.encode("idna").decode("ascii").lower()
                    if request.hostname else ""
                )
                if (
                    request_count > max_requests
                    or request.scheme != "https"
                    or not request_host
                    or request.username or request.password
                    or request.port not in (None, 443)
                    or not policy.allows_host(request_host)
                ):
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
                final_url = urlsplit(page.url)
                final_host = (
                    final_url.hostname.encode("idna").decode("ascii").lower()
                    if final_url.hostname else ""
                )
                if (
                    final_url.scheme != "https"
                    or final_url.port not in (None, 443)
                    or not policy.allows_host(final_host)
                ):
                    raise HTTPException(403, "browser_navigation_target_not_allowlisted")
            except HTTPException:
                raise
            except Exception as exc:
                # Log only exception class; never include URL, page content or proxy credentials.
                logger.warning("browser navigation failed (%s)", type(exc).__name__)
                raise HTTPException(502, "browser_navigation_blocked_or_failed") from exc
            await asyncio.sleep(0.5)
            if download_tasks: await asyncio.gather(*list(download_tasks), return_exceptions=True)
            if body.action == "navigate":
                return {"status": "navigated", "url": page.url, "title": await page.title(), "requests": request_count, "blocked_downloads": blocked_downloads, "downloads": downloads, "storage_state": await context.storage_state()}
            content = (await page.locator("body").inner_text(timeout=5_000))[:30_000]
            return {"status": "extracted", "url": page.url, "title": await page.title(), "text": content, "requests": request_count, "blocked_downloads": blocked_downloads, "downloads": downloads, "storage_state": await context.storage_state()}
        finally:
            await browser.close()
