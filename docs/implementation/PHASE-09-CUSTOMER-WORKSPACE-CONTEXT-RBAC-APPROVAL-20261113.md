# Phase 09 — Customer Workspace Context, RBAC & Approval Lifecycle Continuation

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-only continuation of Customer dashboard integration. No runtime verification or database mutation was performed in this increment.

## PRD and UI/UX decision

Reviewed `AGENTS.md`, `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md` section 6.1 (Customer Web PWA), section 7.1 (Agent Runtime), section 9 (tool execution security), and section 16 (design authority).

- The Customer PWA explicitly requires a workspace context, task/run monitor, and workspace/file/artifact browser.
- The PRD does not specify a dedicated Customer workspace-member administration screen. The current member API exposes listing and owner-only removal, but no invite workflow. A partial member-management screen would therefore create a misleading, incomplete workflow and was not added.
- The PRD requires task/run history, not a second workspace-specific run-monitor screen. The existing Workflow & Agent Runs screen remains the task/run monitor; this increment binds new Chat conversations and their durable Agent Runs to the selected workspace.
- Existing visual structure was preserved. The Chat composer received only the minimal workspace selector needed to supply the missing workspace context.

## Implemented

### 1. Workspace context from Chat to durable Agent Run

- Added optional `workspace_id` to the shared FastAPI `ConversationCreate` request contract.
- Both `POST /api/v1/customer/conversations` and the compatibility `POST /api/v1/conversations` now validate selected workspace membership and `agent.run.create` permission before persisting the conversation.
- Customer and compatibility conversation response schemas now expose nullable `workspace_id`; conversation list projections select the same field.
- The typed Customer API client now accepts an optional workspace ID when creating a conversation and types the returned association.
- Chat loads the real, paginated workspace list from FastAPI, allows selection for a new conversation, restores the persisted workspace association for an existing conversation, and keeps existing conversations bound to their stored workspace.
- Both Customer and compatibility message-enqueue routes re-check active workspace membership and `agent.run.create` permission before calling the durable enqueue RPC.
- The existing Supabase enqueue RPC copies `conversations.workspace_id` into `agent_runs.workspace_id`; this was inspected as source/schema evidence only and was not executed or changed.

### 2. Workspace authorization and role permissions

- Replaced membership-only authorization in the workspace router with role-aware resolution against `workspace_members`, `roles`, `role_permissions`, and `permissions`.
- Workspace owners retain owner authority. Active members must have the required workspace-scoped permission.
- Read operations require `workspace.read`.
- Workspace file upload, soft-delete, and restore require `workspace.manage`.
- Workspace run history requires `agent.run.read`.
- Workspace-bound conversation creation and message enqueue require `agent.run.create`.
- Workspace identity rename/archive and member removal remain owner-only.
- This follows the currently configured Supabase role-permission matrix; no role grants or assignments were modified.

### 3. Approval lifecycle visibility

- Workflow now retains the persisted `decided_at` timestamp returned by the decision API.
- The existing Workflow approval panel exposes non-pending decision history with explicit approved, denied, expired, and consumed states. Pending approvals remain actionable through the existing approve/deny actions.
- Pagination remains cursor-based and owner-scoped. The API decision RPC remains the authority for expiry, idempotent decisions, and worker resume; UI labels do not simulate those transitions.

### 4. Collection pagination hardening

- Files artifact-page append now deduplicates by artifact ID.
- Workspace file-page retries clear stale page errors before retrying; per-workspace cursors remain independently advanced only after successful page retrieval.
- Existing incremental pagination in Results, Workflow, Code, Tasks, Research, Analyse, notifications, approvals, workspaces, conversations/messages, ledger and usage remains in place.

## Authorization and response-contract audit

Source review covered Customer-facing routes in:
- `customer.py`
- `conversations.py`
- `agent_runs.py`
- `workspaces.py`
- `artifacts.py`
- `knowledge.py`
- `learning.py`
- `notifications.py`
- `tool_approvals.py`
- `catalog.py`

Customer business routes use `customer_principal`; workspace resources additionally enforce owner/member/role checks. Partner and Admin routers remain separate principal boundaries. The only Customer endpoints without JSON response models in the reviewed set are intentionally streaming or binary transport endpoints (Agent Run SSE and speed-test download).

This is a source-level audit only. It is not proof of live RLS, cross-tenant isolation, OpenAPI generation, or worker/runtime behavior.

## Explicitly not implemented in this increment

- No workspace-member administration screen: PRD section 6.1 does not define member invitation/management as a Customer navigation module, and there is no invite API contract. Existing member listing/removal endpoints remain available under owner/member authorization.
- No separate workspace-only run screen: existing Workflow & Agent Runs is the PRD task/run monitor; new runs now inherit the selected workspace association.
- No gateway/OTP, EduTech catalog/video, payment settlement, media generation, or support integration without authoritative provider contracts and credentials.
- No fake provider, local business-data fallback, or synthetic success response was introduced.

## Verification boundary

Per the product owner's instruction, none of the following were run: tests, lint, typecheck, build, browser checks/screenshots, API probes, worker execution, real provider calls, staging, migrations, or deployment. No Supabase data or schema was mutated in this increment. GitHub source writes were committed directly to `main`.

## Commits in this increment

- `22fc14f557012bef322473cb9da6892f36c503eb` — conversation creation accepts authorized workspace context.
- `99dbef8426920426d6d24195d80d0166a13f98ee` — Customer conversation response/list exposes workspace association.
- `caffdb98d9b9cfb4546167edc45a0b601aa9513c` — typed Customer conversation workspace association.
- `cebd2c7d8d5cec51241c2b21517c57d7572657ff` — Chat workspace selector and persisted association restore.
- `1954452556b8b029d15e0b33ac49099a164be749` — workspace role-based authorization.
- `c5f5ff03a4919a7c43f3d695b6b54b2b8fa801cc`, `2cff2d53342d776270284ac879ba1b5103edf3f3`, `9d9843d144ac98f97080e79472b5abe8ad639388`, `b5f5e7313825fca86c0c9ac56e9e984fcdc79ec6` — enforce run-create permission at workspace binding and enqueue.
- `90acc207b2c25a37b7e7c42626b7412251cac9a9` — durable approval decision history in Workflow.
- `419e78be7f94133637cadb7cb8cc61a567fce281` — Files pagination dedupe/retry hardening.

## Phase status and next work

**Phase 09 remains IN PROGRESS.** No acceptance or phase completion is claimed.

Continue Phase 09 with:
1. Complete remaining Customer action-by-action source audit, including profile/security, network sessions, learning, knowledge retry/archive, and notification preference edge cases.
2. Reconcile role-aware UI affordances with workspace permission responses so read-only members do not see unavailable write actions.
3. Review conversation/session and Agent Run state projections across SSE, WebSocket, cancellation, approval expiry/consumption and worker recovery.
4. Finish provider-independent screen/action gaps only where the backend contract is authoritative.
5. Keep external provider-dependent workflows fail-closed.

Phase 10 must not start until Phase 09 Customer integration gaps are closed and explicitly accepted.
