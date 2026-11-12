from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException


def decode_created_at_id_cursor(value: str | None) -> tuple[str, str] | None:
    """Decode an opaque, deterministic keyset cursor (created_at, UUID)."""
    if value is None:
        return None
    if not value or len(value) > 512:
        raise HTTPException(400, "pagination_cursor_invalid")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8")
        timestamp, identifier = raw.rsplit("|", 1)
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("cursor_timestamp_must_be_timezone_aware")
        parsed = parsed.astimezone(timezone.utc)
        normalized = parsed.isoformat()
        stable_id = str(UUID(identifier))
    except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
        raise HTTPException(400, "pagination_cursor_invalid") from exc
    return normalized, stable_id


def encode_created_at_id_cursor(row: dict) -> str:
    timestamp = row.get("created_at")
    identifier = row.get("id")
    if not isinstance(timestamp, str) or not isinstance(identifier, str):
        raise ValueError("pagination_row_missing_cursor_fields")
    raw = f"{timestamp}|{identifier}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def created_at_id_filter(cursor: tuple[str, str] | None) -> str | None:
    if cursor is None:
        return None
    timestamp, identifier = cursor
    return f"(created_at.lt.{timestamp},and(created_at.eq.{timestamp},id.lt.{identifier}))"
