from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/learning", tags=["customer-learning"])


class LearningProgressRecordResponse(BaseModel):
    module_key: str
    lesson_key: str
    completed_at: datetime
    updated_at: datetime


class LearningProgressListResponse(BaseModel):
    items: list[LearningProgressRecordResponse]
    count: int


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
    request: Request, module_key: str | None = Query(default=None, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$"),
    user: dict[str, Any] = Depends(customer_principal),
):
    filters = {
        "user_id": f"eq.{user['id']}",
        "select": "module_key,lesson_key,completed_at,updated_at",
        "order": "completed_at.desc",
        "limit": "1000",
    }
    if module_key:
        filters["module_key"] = f"eq.{module_key}"
    rows = await repository(request).select("customer_learning_progress", filters)
    return {"items": rows, "count": len(rows)}


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
