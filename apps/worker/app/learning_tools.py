from __future__ import annotations

import json
from typing import Any


class SupabaseLearningTools:
    """First-party EduTech mutations through owner-checked Postgres RPCs."""

    def __init__(self, client: Any):
        self.client = client

    async def _rpc(self, name: str, payload: dict[str, Any]) -> str:
        result = await self.client.rpc(name, payload)
        if not isinstance(result, dict):
            raise RuntimeError("learning_tool_invalid_database_response")
        return json.dumps(result, separators=(",", ":"), ensure_ascii=False)

    async def learning_path_create(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        modules = arguments.get("modules")
        if not isinstance(modules, list) or not 1 <= len(modules) <= 30:
            raise ValueError("learning_path_modules_required")
        return await self._rpc("moreai_learning_path_create", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_title": arguments["title"],
            "p_description": arguments.get("description", ""),
            "p_education_level": arguments.get("education_level", "self_directed"),
            "p_learning_goal": arguments.get("learning_goal", ""),
            "p_modules": modules,
        })

    async def lesson_generate(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        return await self._rpc("moreai_learning_lesson_generate", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_lesson_id": arguments["lesson_id"],
            "p_title": arguments["title"],
            "p_content_md": arguments["content_md"],
            "p_objectives": arguments.get("objectives", []),
        })

    async def quiz_generate(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        return await self._rpc("moreai_learning_quiz_generate", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_lesson_id": arguments["lesson_id"],
            "p_title": arguments["title"],
            "p_questions": arguments["questions"],
            "p_pass_score": arguments.get("pass_score", 70),
        })

    async def answer_assess(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        return await self._rpc("moreai_learning_answer_assess", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_quiz_id": arguments["quiz_id"],
            "p_answers": arguments["answers"],
            "p_score": arguments["score"],
            "p_feedback": arguments.get("feedback", {}),
            "p_rubric": arguments.get("rubric", []),
        })

    async def learning_progress_update(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        return await self._rpc("moreai_learning_progress_update", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_lesson_id": arguments["lesson_id"],
            "p_status": arguments["status"],
        })
