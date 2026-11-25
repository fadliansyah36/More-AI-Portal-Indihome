import asyncio
import pytest
import httpx

from apps.sandbox.app.browser_supervisor import BrowserSupervisor


def _client():
    return httpx.AsyncClient()


def test_supervisor_accepts_https_transport_without_private_http_flag():
    supervisor = BrowserSupervisor(
        service_url="https://browser.internal.example",
        service_token="s" * 40,
        egress_enforced=True,
        http=_client(),
        api_url="https://api.example.com",
        internal_token="i" * 40,
    )
    assert supervisor.service_url == "https://browser.internal.example"


def test_supervisor_accepts_compose_http_only_with_explicit_private_network_opt_in():
    supervisor = BrowserSupervisor(
        service_url="http://browser-supervisor:8080",
        service_token="s" * 40,
        egress_enforced=True,
        http=_client(),
        api_url="https://api.example.com",
        internal_token="i" * 40,
        allow_private_http=True,
    )
    assert supervisor.service_url == "http://browser-supervisor:8080"


@pytest.mark.parametrize(
    "service_url,allow_private_http",
    [
        ("http://browser-supervisor:8080", False),
        ("http://attacker.example:8080", True),
        ("http://browser-supervisor:8081", True),
        ("http://browser-supervisor:8080/path?token=leak", True),
        ("http://browser-supervisor:8080/other", True),
        ("https://browser.internal.example:8443", False),
        ("https://user:pass@browser.internal.example", False),
    ],
)
def test_supervisor_rejects_untrusted_http_or_malformed_urls(service_url, allow_private_http):
    with pytest.raises(ValueError):
        BrowserSupervisor(
            service_url=service_url,
            service_token="s" * 40,
            egress_enforced=True,
            http=_client(),
        api_url="https://api.example.com",
        internal_token="i" * 40,
            allow_private_http=allow_private_http,
        )


def test_supervisor_refuses_missing_egress_enforcement():
    with pytest.raises(RuntimeError, match="egress_enforcement"):
        BrowserSupervisor(
            service_url="https://browser.internal.example",
            service_token="s" * 40,
            egress_enforced=False,
            http=_client(),
        api_url="https://api.example.com",
        internal_token="i" * 40,
        )


def test_supervisor_readiness_requires_live_proxy_and_enforcement():
    async def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        assert request.url.path == "/sessions"
        assert request.headers["authorization"] == "Bearer " + "s" * 40
        return httpx.Response(200, json=[])
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    supervisor = BrowserSupervisor(
        service_url="https://browser.internal.example",
        service_token="s" * 40,
        egress_enforced=True,
        http=client,
        api_url="https://api.example.com",
        internal_token="i" * 40,
    )
    assert asyncio.run(supervisor.check_ready())["status"] == "ready"


def test_supervisor_readiness_fails_closed_when_proxy_is_degraded():
    async def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(503, json={"detail": "openfuse_sessions_unavailable"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    supervisor = BrowserSupervisor(
        service_url="https://browser.internal.example",
        service_token="s" * 40,
        egress_enforced=True,
        http=client,
        api_url="https://api.example.com",
        internal_token="i" * 40,
    )
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(supervisor.check_ready())
