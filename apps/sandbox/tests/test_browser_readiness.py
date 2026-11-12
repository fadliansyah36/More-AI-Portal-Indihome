import asyncio

import pytest

from app import browser_readiness


class FakeWriter:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return None


@pytest.mark.asyncio
async def test_browser_readiness_requires_reachable_authenticated_proxy(monkeypatch):
    writer = FakeWriter()

    async def open_connection(host, port):
        assert host == "browser-egress-proxy"
        assert port == 3128
        return asyncio.StreamReader(), writer

    monkeypatch.setenv("MOREAI_BROWSER_PROXY_URL", "http://browser-egress-proxy:3128")
    monkeypatch.setenv("MOREAI_BROWSER_PROXY_TOKEN", "x" * 40)
    monkeypatch.setenv("MOREAI_BROWSER_EGRESS_ENFORCED", "true")
    monkeypatch.setattr(browser_readiness.asyncio, "open_connection", open_connection)

    result = await browser_readiness.browser_readiness()
    assert result["status"] == "ready"
    assert result["proxy_reachable"] is True
    assert writer.closed is True


@pytest.mark.asyncio
async def test_browser_readiness_fails_closed_when_proxy_is_unreachable(monkeypatch):
    async def open_connection(host, port):
        raise OSError("connection_refused")

    monkeypatch.setenv("MOREAI_BROWSER_PROXY_URL", "http://browser-egress-proxy:3128")
    monkeypatch.setenv("MOREAI_BROWSER_PROXY_TOKEN", "x" * 40)
    monkeypatch.setenv("MOREAI_BROWSER_EGRESS_ENFORCED", "true")
    monkeypatch.setattr(browser_service.asyncio, "open_connection", open_connection)

    result = await browser_readiness.browser_readiness()
    assert result["status"] == "degraded"
    assert result["proxy_reachable"] is False
