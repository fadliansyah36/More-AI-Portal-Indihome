# Phase 04 — Planning step approval resume wiring

- High/critical and non-basic tool planning steps now call the same durable run-level approval gate as isolated tools.
- The first pass writes `waiting_approval` step state and a checkpoint; pending approval raises the dedicated pause control signal through the WorkerRpcClient, which atomically pauses the run and releases its lease.
- On resume, the persisted plan is restored, the approved decision is consumed once, and the step proceeds. Denied/expired decisions fail closed.
- This does not bypass the actual tool registry policy: tool execution remains independently allowlisted and approval-gated.
