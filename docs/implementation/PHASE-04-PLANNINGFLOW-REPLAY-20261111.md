# Phase 04 — PlanningFlow durable replay parity

- PlanningAgentRuntime now reads persisted `planning.manifest` and `agent_run_steps` before calling the LLM. A resumed run restores the persisted plan instead of generating a different one.
- It validates manifest/row count, schema, dependency ordering, risk and usage metadata; orphaned step rows without a manifest fail closed.
- Succeeded steps are skipped and structured outputs are restored. Dependencies must be completed before downstream steps execute. Each step records start/completion checkpoints; output JSON is persisted on the step row.
- A high/critical or non-basic planned tool step is durably marked `waiting_approval` and stops execution rather than being marked failed.
- Runtime/tests not run.
