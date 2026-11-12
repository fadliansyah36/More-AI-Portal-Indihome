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

    class FakeStdin:
        def write(self, data): pass
        async def drain(self): pass
        def close(self): pass
        async def wait_closed(self): pass

    class FakeProcess:
        returncode = 0
        pid = 12345

        def __init__(self):
            self.stdin = FakeStdin()
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

    async def resolve(host, port, socktype):
        import socket
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)), resolver=resolve)
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
async def test_browser_request_guard_detects_dns_rebinding():
    import socket
    from app.browser_security import BrowserRequestGuard

    answer = ["93.184.216.34"]

    async def resolve(host, port, socktype):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (answer[0], port))]

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)), resolver=resolve)
    await guard.validate_request("https://trusted.example/one")
    answer[0] = "127.0.0.1"
    with pytest.raises(BrowserPolicyError, match="private_or_reserved"):
        await guard.validate_request("https://trusted.example/two")


def test_browser_proxy_entrypoints_use_container_local_imports():
    from app.browser_proxy import PinnedConnectProxy
    from app.proxy_main import serve
    from app.browser_proxy_server import main

    assert PinnedConnectProxy is not None
    assert callable(serve)
    assert callable(main)


@pytest.mark.asyncio
async def test_browser_request_guard_allows_global_cdn_rotation_but_pins_current_request():
    import socket
    from app.browser_security import BrowserRequestGuard

    answer = ["93.184.216.34"]
    async def resolve(host, port, socktype):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (answer[0], port))]

    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)), resolver=resolve)
    await guard.validate_request("https://trusted.example/one")
    answer[0] = "1.1.1.1"
    _, _, pinned = await guard.resolve_pinned("https://trusted.example/two")
    assert pinned == ("1.1.1.1",)


def test_browser_policy_host_allowlist_blocks_redirect_hosts_and_suffix_lookalikes():
    policy = BrowserPolicy(("example.com",))
    assert policy.allows_host("example.com")
    assert policy.allows_host("sub.example.com")
    assert not policy.allows_host("not-allowlisted.invalid")
    assert not policy.allows_host("example.com.attacker.invalid")


def test_connect_proxy_rejects_socket_peer_that_differs_from_dns_pin(monkeypatch):
    import asyncio
    import base64
    import socket
    from app.browser_proxy import PinnedConnectProxy
    from app.browser_security import BrowserPolicy, BrowserRequestGuard

    token = "p" * 40
    async def resolver(host, port, socktype):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    class FakeWriter:
        def __init__(self, peer):
            self.peer = peer
            self.output = bytearray()
            self.closed = False
        def get_extra_info(self, name):
            return self.peer if name == "peername" else None
        def write(self, data):
            self.output.extend(data)
        async def drain(self):
            return None
        def close(self):
            self.closed = True
        async def wait_closed(self):
            return None
        def is_closing(self):
            return self.closed

    async def run():
        upstream_reader = asyncio.StreamReader()
        candidate = FakeWriter(("127.0.0.1", 443))
        async def fake_open_connection(*args, **kwargs):
            return upstream_reader, candidate
        monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

        authorization = base64.b64encode(("moreai:" + token).encode()).decode()
        client_reader = asyncio.StreamReader()
        client_reader.feed_data(
            f"CONNECT example.com:443 HTTP/1.1\\r\\nProxy-Authorization: Basic {authorization}\\r\\n\\r\\n".encode()
        )
        client_reader.feed_eof()
        client_writer = FakeWriter(("172.18.0.2", 3128))
        proxy = PinnedConnectProxy(
            BrowserRequestGuard(BrowserPolicy(("example.com",)), resolver=resolver),
            token=token,
        )
        await proxy.handle(client_reader, client_writer)
        assert candidate.closed is True
        assert b"502 Bad Gateway" in client_writer.output

    asyncio.run(run())
