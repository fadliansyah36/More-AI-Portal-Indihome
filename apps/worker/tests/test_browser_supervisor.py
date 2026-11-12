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
    )
    assert supervisor.service_url == "https://browser.internal.example"


def test_supervisor_accepts_compose_http_only_with_explicit_private_network_opt_in():
    supervisor = BrowserSupervisor(
        service_url="http://browser-supervisor:8080",
        service_token="s" * 40,
        egress_enforced=True,
        http=_client(),
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
            allow_private_http=allow_private_http,
        )


def test_supervisor_refuses_missing_egress_enforcement():
    with pytest.raises(RuntimeError, match="egress_enforcement"):
        BrowserSupervisor(
            service_url="https://browser.internal.example",
            service_token="s" * 40,
            egress_enforced=False,
            http=_client(),
        )
