# Phase 08 Streaming Latency Accounting — 2026-11-12

## Scope

Corrected one concrete accounting gap in the metered streaming provider path.

## Source and commit

- File: `engine/llm/router.py`
- Commit: `157b110a14d456dad6751a22f34983a26c2df19e`
- Branch: `main`

## Change

The non-streaming completion path already measured elapsed provider time. The streaming path passed `latency_ms=0` into `UsageAccounting.record_provider_result`, which made streamed LLM requests report an inaccurate zero latency despite real provider activity.

The streaming path now captures a monotonic start timestamp before provider attempts and computes elapsed milliseconds when a candidate stream completes. The measured value is passed to the existing accounting repository alongside provider/model, token usage, actual cost and provider response ID.

This does not alter reservation, entitlement, quota, wallet, settlement, retry or fallback policy.

## Verification boundary

No provider call, DB write, credit reservation/settlement, test, lint, typecheck, build or worker runtime was executed. The fix is committed source only and is not runtime acceptance.

## Remaining Phase 08 work

Complete upstream provider/client parity, structured tool handlers and adapters, ReAct state/round parity, memory/RAG retrieval and persistence, prompt/schema contracts, retry/circuit-breaker policy, per-tool accounting, and full durable workflow/server parity. High-risk browser, Bash, Python and workspace tools remain disabled until isolation and release gates pass.

## Deployment

No deployment was requested or performed for this commit. Production release remains gated by Phase 10/11 authorization and acceptance evidence.
