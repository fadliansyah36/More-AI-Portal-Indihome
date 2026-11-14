from __future__ import annotations

import json
import re
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


    @staticmethod
    def _normalize_answer(value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"\\s+", " ", value).strip().casefold()
        if isinstance(value, list):
            return sorted(SupabaseLearningTools._normalize_answer(item) for item in value)
        if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
            return value
        raise ValueError("learning_answer_value_invalid")

    @classmethod
    def _grade_quiz(cls, questions: list[dict[str, Any]], answers: list[dict[str, Any]]) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
        if not questions or len(questions) > 100 or not isinstance(answers, list):
            raise ValueError("learning_assessment_payload_invalid")
        answer_by_id: dict[str, Any] = {}
        for answer in answers:
            if not isinstance(answer, dict) or not isinstance(answer.get("question_id"), str):
                raise ValueError("learning_answer_question_id_required")
            key = answer["question_id"]
            if key in answer_by_id:
                raise ValueError("learning_duplicate_question_answer")
            answer_by_id[key] = answer.get("answer")
        question_ids: set[str] = set()
        total_points = 0.0
        earned_points = 0.0
        details: list[dict[str, Any]] = []
        rubric: list[dict[str, Any]] = []
        for question in questions:
            if not isinstance(question, dict):
                raise ValueError("learning_question_contract_invalid")
            question_id = question.get("id")
            kind = question.get("type")
            if not isinstance(question_id, str) or not question_id or question_id in question_ids:
                raise ValueError("learning_question_id_invalid")
            question_ids.add(question_id)
            if kind not in {"single_choice", "multiple_choice", "true_false", "short_answer"} or "correct_answer" not in question:
                raise ValueError("learning_question_not_machine_gradable")
            expected = question["correct_answer"]
            submitted = answer_by_id.get(question_id)
            if kind == "multiple_choice" and (not isinstance(expected, list) or not isinstance(submitted, list)):
                raise ValueError("learning_multiple_choice_answer_must_be_array")
            if kind != "multiple_choice" and isinstance(expected, list):
                raise ValueError("learning_question_answer_type_mismatch")
            points = question.get("points", 1)
            if isinstance(points, bool) or not isinstance(points, (int, float)) or points <= 0:
                raise ValueError("learning_question_points_invalid")
            correct = submitted is not None and cls._normalize_answer(submitted) == cls._normalize_answer(expected)
            total_points += float(points)
            if correct:
                earned_points += float(points)
            detail = {"question_id": question_id, "correct": correct, "earned_points": float(points) if correct else 0.0, "total_points": float(points)}
            details.append(detail)
            rubric.append({"criterion": question_id, "score": float(points) if correct else 0.0, "max_score": float(points), "status": "met" if correct else "not_met"})
        if set(answer_by_id) - question_ids:
            raise ValueError("learning_answer_contains_unknown_question")
        score = round(earned_points / total_points * 100, 2)
        return score, {"grading": "deterministic_exact_match_v1", "earned_points": earned_points, "total_points": total_points, "items": details}, rubric

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
        questions = arguments.get("questions")
        if not isinstance(questions, list) or not 1 <= len(questions) <= 100:
            raise ValueError("learning_quiz_questions_required")
        # Validate the same explicit machine-grading contract used at submission.
        cls = type(self)
        cls._grade_quiz(questions, [])
        return await self._rpc("moreai_learning_quiz_generate", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_lesson_id": arguments["lesson_id"],
            "p_title": arguments["title"],
            "p_questions": questions,
            "p_pass_score": arguments.get("pass_score", 70),
        })

    async def answer_assess(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        quiz_id = arguments.get("quiz_id")
        rows = await self.client.select("learning_quizzes", {
            "id": f"eq.{quiz_id}", "owner_user_id": f"eq.{user_id}",
            "select": "id,questions,pass_score", "limit": "1",
        })
        if not rows:
            raise ValueError("learning_quiz_not_found")
        questions = rows[0].get("questions")
        if not isinstance(questions, list):
            raise RuntimeError("learning_quiz_contract_invalid")
        score, feedback, rubric = self._grade_quiz(questions, arguments.get("answers"))
        # Client/model supplied score, feedback and rubric are intentionally ignored.
        return await self._rpc("moreai_learning_answer_assess", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_quiz_id": quiz_id,
            "p_answers": arguments["answers"],
            "p_score": score,
            "p_feedback": feedback,
            "p_rubric": rubric,
        })

    async def learning_progress_update(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
    ) -> str:
        return await self._rpc("moreai_learning_progress_update", {
            "p_user_id": user_id, "p_run_id": run_id,
            "p_lesson_id": arguments["lesson_id"],
            "p_status": arguments["status"],
        })
