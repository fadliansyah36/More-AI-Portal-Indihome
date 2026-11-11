from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.client import WorkerRpcClient

logger = logging.getLogger(__name__)


class DurableEventOutboxPublisher:
    """Leased at-least-once publisher; consumers deduplicate on event_id/sequence."""

    def __init__(self, rpc: WorkerRpcClient, *, poll_seconds: float = 1.0):
        self.rpc = rpc
        self.poll_seconds = max(0.25, min(30.0, poll_seconds))

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                rows = await self.rpc.claim_event_outbox(limit=25)
                if not rows:
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=self.poll_seconds)
                    except TimeoutError:
                        pass
                    continue
                for row in rows:
                    if stop.is_set():
                        return
                    event_id = row.get("event_id")
                    outbox_id = row.get("id")
                    if not isinstance(event_id, str) or not isinstance(outbox_id, str):
                        logger.error("outbox_row_missing_identity")
                        continue
                    try:
                        await self.rpc.publish_run_event(row)
                        if not await self.rpc.ack_event_outbox(outbox_id):
                            # Lease may have expired after a slow publish. A later worker
                            # may publish the same event again; consumers dedupe by event_id.
                            logger.warning("outbox_ack_lease_lost event_id=%s", event_id)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        code = type(exc).__name__.lower()[:80]
                        try:
                            state = await self.rpc.retry_event_outbox(outbox_id, code)
                            logger.warning("outbox_publish_failed event_id=%s state=%s", event_id, state)
                        except Exception:
                            logger.exception("outbox_retry_failed event_id=%s", event_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Database/schema unavailability must not crash the worker loop.
                # It is observable in logs; events remain durable and leased rows expire.
                logger.exception("outbox_poll_failed")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=min(10.0, self.poll_seconds * 5))
                except TimeoutError:
                    pass
