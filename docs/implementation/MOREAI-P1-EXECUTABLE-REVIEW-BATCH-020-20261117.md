# P1 Executable Payload Review — Batch 020 (Ledger rows 673–722) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Ledger: `docs/implementation/p1-skill-payload-evidence/skill-payload-file-audit.csv`
Ledger blob SHA at review: `6661261f2cc6f87c326ae911c9551b5d5013c8a7`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope and integrity

This batch covers the next 50 contiguous selected payload entries, rows 673–722 inclusive. All 50 immutable source paths were fetched from the pinned commit and inspected as text/configuration. The current ledger records Git blob SHA and raw byte-size matches and SHA-256 evidence for these rows. The audit establishes source identity, not license approval, vulnerability clearance, or production suitability.

No Luau, Python, Lune, Roblox Studio, Blender, external CLI, networked skill runtime, provider, worker or customer runtime was executed. No package was installed; no tests, builds, staging, deployment, Supabase writes or migrations were run.

## Inventory and findings

| Rows | Source area | Static review finding | Interim disposition |
|---|---|---|---|
| 673–682 | Roblox data/backend references and DataAudit/DataCheck/KeyQueue/Migrate/MockDataStore modules | Roblox DataStore/ProfileStore simulation and persistence helpers; includes mock store and engine-specific test harness material | DEFER |
| 683–692 | Roblox data modules, Python data adapter, Roblox environment entrypoint and references | Session-locked player data, purchases/receipts, trade/teleport flows, local process and file handling | DEFER |
| 693–702 | Roblox environment references and Luau world/terrain/lighting helpers | Studio scene/terrain/material/lighting mutation and editor-side validation | DEFER |
| 703–712 | Roblox environment scripts, Roblox expert entrypoint and references | Studio bridge, environment audit and capture workflows; engine-specific project operations | DEFER |
| 713–722 | Roblox expert references and Luau/Python tooling | Offline/Studio audits, Luau checks, Studio MCP client, playtest, screenshots and process orchestration | DEFER |

### 1. Roblox persistence and data helpers

- `scenario-roblox-data` is specific to Roblox DataStoreService, ProfileStore, player profiles, session locks, receipts, trades, teleports, MemoryStore and MessagingService.
- `DataCheck`, `DataAudit`, `KeyQueue`, `Migrate`, `PlayerData`, `Receipts`, `SafeTeleport`, `ServerSim`, `Trade` and `MockDataStore` are Luau modules that operate on Roblox service contracts and simulated game-server state.
- `rbx_data.py` is a Python adapter over the sibling Roblox expert toolkit. It coordinates local files and Roblox Studio operations and must not run in the FastAPI process.
- Generic ideas such as per-key ordering, idempotent operation IDs, versioned migrations and unknown-outcome handling may inform separate MoreAI domain design. Do not copy Roblox DataStore/ProfileStore code into MoreAI or replace Supabase, wallet/ledger, quota, entitlement, or the Memory Coordinator.

### 2. Roblox environment and world-building helpers

- `scenario-roblox-environment` references and scripts manipulate Roblox Studio terrain, map geometry, foliage, materials, lighting and capture/verification state.
- Luau modules such as `EnvAudit`, `Graybox`, `Looks`, `MaterialKit`, `Scatter`, `TerrainKit` and `WorldCheck` depend on Roblox's in-memory DataModel and Studio APIs. They are not web UI components or generic MoreAI workflow steps.
- `rbx_environment.py` is a local Studio automation adapter. Filesystem/process signals in the source require an isolated runner and allowlisted project paths if any future product use is justified.
- References and procedure documents include code intended to run in Studio. They are instructional source content, not authorization to execute the embedded commands in MoreAI.

### 3. Roblox expert toolkit

- The `scenario-roblox-expert` entrypoint and references describe the shared Roblox Studio MCP/toolkit contract used by sibling Roblox skills.
- `rbx_mcp.py` is a local stdio client that connects to a running signed-in Roblox Studio instance. `rbx_env.py`, `rbx_play.py`, `rbx_review.py` and `rbx_check.py` coordinate local processes, project files, Studio/playtest sessions, screenshots and Luau analysis.
- These tools have a privileged local desktop/project boundary and are not safe as customer-callable FastAPI tools. A future integration would require a dedicated, isolated desktop/worker adapter, fixed operation schemas, workspace confinement, approvals, audit receipts and no ambient host credentials.
- Static content in the expert references includes operational instructions and external source links. External references and credentials mentioned in documentation are not verified MoreAI provider integrations.

## License, dependency and security status

1. Scenario Skills root MIT notice remains the repository-level baseline; any nested notice, third-party reference, font/media or source-header rights still require per-file reconciliation. This batch does not extend license coverage by assumption.
2. All rows remain interim `DEFER`. No file is promoted to `copy`, `adapt`, `archive-only` or `exclude` final disposition.
3. Local process execution, filesystem mutation, Studio bridge access, project editing, simulated game-server execution and network operations are not permitted in the API process or ordinary Agent Run tool path.
4. No Roblox persistence implementation may introduce a second database or conflict with Supabase as MoreAI's canonical store.
5. Existing MoreAI customer UI, typed FastAPI client, OpenManus runtime, OpenFuse adapter and six-domain Memory Coordinator remain the only product integration boundaries.

## Status and next work

- Rows reviewed: **673–722 (50 files)**.
- Source fetch/static inspection: **50/50 fetched**.
- Ledger integrity evidence: **Git blob SHA, raw byte-size and SHA-256 evidence recorded for the batch**.
- Interim disposition: **50 DEFER; 0 final approvals**.
- Contiguous executable review frontier: **rows 171–722 across batches 014–020**, subject to validating earlier reports and ledger references.
- Next executable-source range: **723–772**. This completes the wider range 623–772 requested for this continuation once batch 021 is reviewed.
- After executable-source review, continue the remaining selected references, configurations, scripts, fonts/media/assets, package tarball/NOTICE inspection, exact-version vulnerability review, and final file-level dispositions.
- P1 remains **OPEN**. P2 ADR remains **DRAFT / NOT ACCEPTED**. This batch does not certify Phase 04–09 completion or Phase 10/11 acceptance.
