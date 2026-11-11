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
