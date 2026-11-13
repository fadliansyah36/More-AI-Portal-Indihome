from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository
from app.pagination import decode_timestamp_id_cursor, encode_timestamp_id_cursor, timestamp_id_filter

router = APIRouter(prefix="/api/v1/customer/learning", tags=["customer-learning"])


class LearningProgressRecordResponse(BaseModel):
    id: UUID
    module_key: str
    lesson_key: str
    completed_at: datetime
    updated_at: datetime


class LearningProgressListResponse(BaseModel):
    items: list[LearningProgressRecordResponse]
    count: int
    total_count: int


class LearningProgressMutationResponse(BaseModel):
    module_key: str
    lesson_key: str
    completed: bool
    completed_at: datetime | None


class LearningProgressUpdate(BaseModel):
    module_key: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")
    lesson_key: str = Field(min_length=1, max_length=512)
    completed: bool


@router.get("/progress", response_model=LearningProgressListResponse)
async def list_learning_progress(
    request: Request,
    response: Response,
    module_key: str | None = Query(default=None, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$"),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    filters = {
        "user_id": f"eq.{user['id']}",
        "select": "id,module_key,lesson_key,completed_at,updated_at",
        "order": "completed_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    if module_key:
        filters["module_key"] = f"eq.{module_key}"
    cursor_filter = timestamp_id_filter(decoded, "completed_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    repo = repository(request)
    rows = await repo.select("customer_learning_progress", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "completed_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    total_count = await repo.rpc("moreai_customer_learning_progress_count", {
        "p_user_id": user["id"],
        "p_module_key": module_key,
    })
    if isinstance(total_count, bool) or not isinstance(total_count, int):
        raise HTTPException(502, "Learning progress count returned an invalid database response")
    return {"items": rows, "count": len(rows), "total_count": total_count}


@router.put("/progress", response_model=LearningProgressMutationResponse)
async def set_learning_progress(
    body: LearningProgressUpdate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    result = await repository(request).rpc("moreai_set_customer_learning_progress", {
        "p_user_id": user["id"],
        "p_module_key": body.module_key,
        "p_lesson_key": body.lesson_key,
        "p_completed": body.completed,
    })
    return result
