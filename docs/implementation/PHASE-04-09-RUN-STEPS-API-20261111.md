# Phase 04/09 — Durable workflow step read contract

- Added the missing authenticated `GET /api/v1/agent-runs/{run_id}/steps` endpoint consumed by the existing typed frontend API client.
- Ownership is checked against `agent_runs` before reading step metadata.
- Response is deliberately metadata-only (`sequence`, `step_key`, `status`, timestamps); private step input/output/error JSON is not exposed through this endpoint.
- No frontend components or visual styles changed. API runtime and UI integration tests were not run.
- This closes the missing route contract only; complete page-by-page UI data binding and OpenManus server/session parity remain open.
