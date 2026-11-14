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
    # Do not persist caller-invented lesson identifiers while the official EduTech
    # catalogue/enrollment contract is unavailable. Read-only saved progress remains enabled.
    raise HTTPException(
        status_code=503,
        detail={
            "code": "learning_catalog_unavailable",
            "message": "Learning progress can only be updated after a first-party MoreAI learning path supplies an owner-scoped canonical module and lesson record.",
        },
    )



@router.get("/paths")
async def list_learning_paths(
    request: Request,
    response: Response,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List the authenticated learner's first-party paths and enrollment state."""
    decoded = decode_timestamp_id_cursor(cursor)
    filters = {
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,title,description,education_level,learning_goal,status,created_by_run_id,created_at,updated_at",
        "order": "updated_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "updated_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    repo = repository(request)
    paths = await repo.select("learning_paths", filters)
    has_more = len(paths) > limit
    paths = paths[:limit]
    if has_more and paths:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(paths[-1], "updated_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    total_count = await repo.count("learning_paths", {"owner_user_id": f"eq.{user['id']}"})
    if not paths:
        return {"items": [], "count": total_count}
    path_ids = ",".join(str(item["id"]) for item in paths)
    enrollments = await repo.select("learning_enrollments", {
        "user_id": f"eq.{user['id']}", "path_id": f"in.({path_ids})",
        "select": "id,path_id,status,enrolled_at,completed_at,updated_at",
    })
    summaries = await repo.select("learning_path_progress_summary", {
        "owner_user_id": f"eq.{user['id']}", "path_id": f"in.({path_ids})",
        "select": "path_id,lessons_started,lessons_completed,lessons_total,average_percent",
        "limit": str(limit),
    })
    enrollment_by_path = {str(row["path_id"]): row for row in enrollments}
    summary_by_path = {str(row["path_id"]): row for row in summaries}
    items = []
    for path in paths:
        key = str(path["id"])
        summary = summary_by_path.get(key, {})
        items.append({
            **path,
            "enrollment": enrollment_by_path.get(key),
            "progress": {
                "lessons_started": int(summary.get("lessons_started") or 0),
                "lessons_completed": int(summary.get("lessons_completed") or 0),
                "lessons_total": int(summary.get("lessons_total") or 0),
                "average_percent": float(summary.get("average_percent") or 0),
            },
        })
    return {"items": items, "count": total_count}


@router.get("/paths/{path_id}")
async def get_learning_path(
    path_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return only a path and nested curriculum owned by the authenticated learner."""
    repo = repository(request)
    rows = await repo.select("learning_paths", {
        "id": f"eq.{path_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "*", "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Learning path not found")
    path = rows[0]
    modules = await repo.select("learning_modules", {
        "path_id": f"eq.{path_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,path_id,module_index,title,summary,estimated_minutes,created_at",
        "order": "module_index.asc",
    })
    lessons = await repo.select("learning_lessons", {
        "path_id": f"eq.{path_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,path_id,module_id,lesson_index,title,content_md,objectives,content_version,status,source_run_id,created_at,updated_at",
        "order": "module_id.asc,lesson_index.asc",
        "limit": "1000",
    })
    progress = await repo.select("learning_progress", {
        "path_id": f"eq.{path_id}", "user_id": f"eq.{user['id']}",
        "select": "id,lesson_id,status,progress_percent,started_at,completed_at,updated_at",
        "limit": "1000",
    })
    quizzes = await repo.select("learning_quizzes", {
        "path_id": f"eq.{path_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,lesson_id,title,questions,pass_score,created_at",
        "order": "created_at.desc",
        "limit": "200",
    })
    quiz_ids = ",".join(str(row["id"]) for row in quizzes)
    attempts = await repo.select("learning_quiz_attempts", {
        "user_id": f"eq.{user['id']}", "quiz_id": f"in.({quiz_ids})" if quiz_ids else "eq.00000000-0000-0000-0000-000000000000",
        "select": "id,quiz_id,score,passed,feedback,submitted_at",
        "order": "submitted_at.desc",
        "limit": "500",
    }) if quizzes else []
    assessments = await repo.select("learning_assessments", {
        "user_id": f"eq.{user['id']}", "path_id": f"eq.{path_id}",
        "select": "id,module_id,lesson_id,quiz_id,run_id,assessment_type,score,rubric,feedback,created_at",
        "order": "created_at.desc",
        "limit": "500",
    })
    attempts_by_quiz: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        attempts_by_quiz.setdefault(str(attempt["quiz_id"]), []).append(attempt)
    progress_by_lesson = {str(row["lesson_id"]): row for row in progress}
    enrollment_rows = await repo.select("learning_enrollments", {
        "path_id": f"eq.{path_id}", "user_id": f"eq.{user['id']}",
        "select": "id,status,enrolled_at,completed_at,updated_at", "limit": "1",
    })
    lessons_by_module: dict[str, list[dict[str, Any]]] = {}
    for lesson in lessons:
        lesson["progress"] = progress_by_lesson.get(str(lesson["id"]))
        safe_quizzes = []
        for quiz in quizzes:
            if str(quiz["lesson_id"]) != str(lesson["id"]):
                continue
            safe_questions = []
            for question in quiz.get("questions") or []:
                if isinstance(question, dict):
                    safe_questions.append({
                        key: value for key, value in question.items()
                        if key.lower() not in {"answer", "answer_key", "correct_answer", "explanation", "rationale", "grading_notes", "rubric"}
                    })
            safe_quizzes.append({
                "id": quiz["id"], "title": quiz["title"], "questions": safe_questions,
                "question_count": len(safe_questions), "pass_score": quiz["pass_score"],
                "attempts": attempts_by_quiz.get(str(quiz["id"]), []),
                "created_at": quiz["created_at"],
            })
        lesson["quizzes"] = safe_quizzes
        lessons_by_module.setdefault(str(lesson["module_id"]), []).append(lesson)
    for module in modules:
        module["lessons"] = lessons_by_module.get(str(module["id"]), [])
    path["enrollment"] = enrollment_rows[0] if enrollment_rows else None
    completed_lessons = sum(1 for row in progress if row["status"] == "completed")
    path["progress"] = {
        "lessons_started": len(progress),
        "lessons_completed": completed_lessons,
        "lessons_total": len(lessons),
        "average_percent": round(sum(float(row["progress_percent"]) for row in progress) / len(lessons), 1) if lessons else 0,
    }
    return {"path": path, "modules": modules, "assessments": assessments, "enrollment": enrollment_rows[0] if enrollment_rows else None}


@router.get("/progress/detail")
async def list_canonical_learning_progress(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    filters = {
        "user_id": f"eq.{user['id']}",
        "select": "id,path_id,module_id,lesson_id,status,progress_percent,last_run_id,started_at,completed_at,updated_at",
        "order": "updated_at.desc,id.desc",
        "limit": str(limit),
    }
    rows = await repo.select("learning_progress", filters)
    total_count = await repo.count("learning_progress", {"user_id": f"eq.{user['id']}"})
    return {"items": rows, "count": total_count}


@router.get("/runs/{run_id}/artifacts")
async def list_learning_run_artifacts(
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    owned_run = await repo.select("agent_runs", {
        "id": f"eq.{run_id}", "user_id": f"eq.{user['id']}",
        "select": "id", "limit": "1",
    })
    if not owned_run:
        raise HTTPException(404, "Agent Run not found")
    items = await repo.select("learning_run_artifacts", {
        "run_id": f"eq.{run_id}", "user_id": f"eq.{user['id']}",
        "select": "id,artifact_type,resource_id,payload,created_at",
        "order": "created_at.asc,id.asc",
        "limit": "200",
    })
    return {"items": items, "count": len(items)}


@router.get("/paths/{path_id}/lessons/{lesson_id}/versions")
async def list_learning_lesson_versions(
    path_id: UUID,
    lesson_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    owned_lesson = await repo.select("learning_lessons", {
        "id": f"eq.{lesson_id}", "path_id": f"eq.{path_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id", "limit": "1",
    })
    if not owned_lesson:
        raise HTTPException(404, "Learning lesson not found")
    items = await repo.select("learning_lesson_versions", {
        "lesson_id": f"eq.{lesson_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,version,content_md,objectives,source_run_id,created_at",
        "order": "version.desc",
        "limit": "100",
    })
    return {"items": items, "count": len(items)}
