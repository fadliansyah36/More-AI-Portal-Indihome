import pytest

from app.browser_security import BrowserPolicy, BrowserPolicyError, validate_download, validate_navigation_url
from app.runner import DockerSandbox


@pytest.mark.asyncio
async def test_browser_rejects_non_allowlisted_domain():
    with pytest.raises(BrowserPolicyError, match="not_allowlisted"):
        await validate_navigation_url("https://example.com", BrowserPolicy(("trusted.example",)))


@pytest.mark.asyncio
async def test_browser_rejects_private_ip_even_if_allowlisted():
    with pytest.raises(BrowserPolicyError, match="private_or_reserved"):
        await validate_navigation_url("https://127.0.0.1", BrowserPolicy(("127.0.0.1",)))


def test_download_requires_scanner_and_clean_verdict():
    policy = BrowserPolicy(("trusted.example",))
    with pytest.raises(BrowserPolicyError, match="scanner_unavailable"):
        validate_download(size_bytes=100, content_type="text/plain", policy=policy, scanner_available=False, scan_clean=False)
    with pytest.raises(BrowserPolicyError, match="scan_failed"):
        validate_download(size_bytes=100, content_type="text/plain", policy=policy, scanner_available=True, scan_clean=False)


def test_download_enforces_size():
    with pytest.raises(BrowserPolicyError, match="size_denied"):
        validate_download(size_bytes=11, content_type="text/plain", policy=BrowserPolicy(("x.example",), 10), scanner_available=True, scan_clean=True)


@pytest.mark.asyncio
async def test_sandbox_refuses_unpinned_or_missing_image():
    with pytest.raises(RuntimeError, match="digest_pinned"):
        await DockerSandbox(image="python:3.12").execute("print(1)", language="python")


@pytest.mark.asyncio
async def test_docker_runner_uses_disposable_networkless_restricted_container(monkeypatch):
    import asyncio

    captured = []

    class FakeProcess:
        returncode = 0
        pid = 12345

        def __init__(self):
            self.stdout = asyncio.StreamReader()
            self.stderr = asyncio.StreamReader()
            self.stdout.feed_data(b"ok")
            self.stdout.feed_eof()
            self.stderr.feed_eof()

        async def wait(self):
            return 0

    async def fake_exec(*command, **kwargs):
        captured.extend(command)
        assert kwargs["start_new_session"] is True
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    result = await DockerSandbox(
        image="registry.example/moreai-sandbox@sha256:" + ("a" * 64),
    ).execute("print('ok')", language="python")

    assert result.exit_code == 0
    assert "--network=none" in captured
    assert "--read-only" in captured
    assert "--cap-drop=ALL" in captured
    assert "--security-opt=no-new-privileges:true" in captured
    assert "--user" in captured and "65534:65534" in captured
    assert "--pids-limit" in captured
    assert "--memory" in captured
    assert "--cpus" in captured
    assert not any(item.startswith("--mount") or item.startswith("-v") for item in captured)


def test_sandbox_rejects_malformed_digest_even_when_digest_marker_exists():
    with pytest.raises(RuntimeError, match="digest_invalid"):
        DockerSandbox(image="registry.example/sandbox@sha256:latest")._validate()


@pytest.mark.asyncio
async def test_browser_request_guard_revalidates_each_redirect_and_rejects_unapproved_host():
    from app.browser_security import BrowserRequestGuard

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)))
    with pytest.raises(BrowserPolicyError, match="not_allowlisted"):
        await guard.validate_redirect_chain([
            "https://trusted.example/start",
            "https://attacker.example/redirect",
        ])


@pytest.mark.asyncio
async def test_browser_request_guard_rejects_nonstandard_ports():
    from app.browser_security import BrowserRequestGuard

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)))
    with pytest.raises(BrowserPolicyError, match="port_denied"):
        await guard.validate_request("https://trusted.example:8443/")


@pytest.mark.asyncio
async def test_browser_request_guard_detects_dns_rebinding(monkeypatch):
    import socket
    from app.browser_security import BrowserRequestGuard

    answer = ["93.184.216.34"]

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)))
    # Exercise the guard with a deterministic resolver override.
    async def resolve(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (answer[0], port))]
    monkeypatch.setattr("app.browser_security.asyncio.get_running_loop", lambda: type("Loop", (), {"getaddrinfo": resolve})())
    await guard.validate_request("https://trusted.example/one")
    answer[0] = "1.1.1.1"
    with pytest.raises(BrowserPolicyError, match="rebinding"):
        await guard.validate_request("https://trusted.example/two")
