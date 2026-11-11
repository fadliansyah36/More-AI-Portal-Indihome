# Phase 04 — PlanningFlow Durable Resume Increment
Date: 2026-11-11
Branch: `main`
Scope: OpenManus PlanningFlow execution lifecycle and restart recovery.

## Changes
- Planning runtime now reads the canonical persisted plan before requesting a new LLM plan. A worker restart therefore rehydrates the plan instead of regenerating it.
- Persisted manifest/step-count mismatch and orphaned manifests fail closed rather than silently executing an incomplete plan.
- Existing successful steps are skipped and their persisted outputs are restored into the resumed result.
- Step dependencies are checked against durable succeeded states before execution.
- Successful step outputs are written to the existing `agent_run_steps.output` JSON field; no new business table or migration was introduced.
- High-risk or sandbox-dependent plan steps are recorded as `waiting_approval` and checkpointed before execution is blocked. They are not silently marked as completed or run without policy approval.
- The plan store reads canonical `agent_run_steps` and writes state through the existing worker repository client.

## Security and boundaries
- No UI files changed.
- No browser, Python or Bash execution was enabled.
- No service-role secret or provider credential was added.
- No Supabase migration or production row mutation was executed during this source-only increment.
- This does not solve the separate orchestration issue that a worker-level paused run must be released/reclaimed and resumed after approval; the existing tool approval polling path is the current supported pause mechanism for individual tool calls.

## Verification and limitations
- Per product-owner instruction, no staging, real provider, runtime, integration or test suite was run.
- No build, lint, typecheck or deployment is claimed.
- Full Phase 04 remains open: upstream server/session/WebSocket parity, workspace lease/CAS/versioning, deployed browser network isolation, full Flow selection/lifecycle parity and durable approval-resume scheduling remain incomplete.

## Next
Continue Phase 04 with the run-level approval pause/resume contract and Flow/session compatibility; retain fail-closed browser/sandbox activation until deployment network controls and security verification are authorized.
