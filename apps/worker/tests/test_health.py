import asyncio

from app.main import _health_handler


class FakeWriter:
    def __init__(self):
        self.data = b""
        self.closed = False

    def write(self, data):
        self.data += data

    async def drain(self):
        return None

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return None


def test_worker_health_endpoint_returns_ok():
    async def run():
        reader = asyncio.StreamReader()
        reader.feed_data(b"GET /ready HTTP/1.1\r\nHost: localhost\r\n\r\n")
        reader.feed_eof()
        writer = FakeWriter()
        await _health_handler(reader, writer)
        assert writer.data.startswith(b"HTTP/1.1 200 OK")
        assert b'"service": "moreai-worker"' in writer.data
        assert writer.closed

    asyncio.run(run())
