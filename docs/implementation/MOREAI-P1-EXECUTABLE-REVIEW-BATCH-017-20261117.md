# P1 Executable Payload Review — Batch 017 (Ledger rows 523–572) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Ledger: `docs/implementation/p1-skill-payload-evidence/skill-payload-file-audit.csv`
Ledger blob SHA at review: `6661261f2cc6f87c326ae911c9551b5d5013c8a7`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope and integrity

This batch covers the 50 contiguous executable-source entries, rows 523–572 inclusive, from the current ledger (875 executable-source entries total). Each source was fetched from the pinned commit and its Git blob SHA and byte size were compared with the ledger. **50/50 blob SHAs match; 50/50 byte sizes match; no fetch failures observed.** This is source identity/integrity evidence only, not proof of license compatibility, dependency closure, security, or runtime correctness.

The review was static. No source was executed/imported; no Unity Editor, Unity CLI, project runner, Python adapter, browser, media renderer, provider, customer runtime, or Supabase operation was launched. No tests, builds, staging, deployment, migrations, or worker jobs were run.

## Inventory and interim disposition

| Rows | Source area | Interim disposition |
|---|---|---|
| 523–527 | Unity architecture PlayMode test templates: lifecycle, cancellation/lifetime, local multiplayer, prefab isolation, runtime sets | DEFER |
| 528 | Unity architecture runner/scaffolding, project file generation, Git merge-driver configuration, static audits | DEFER |
| 529–535 | Unity expert AgentKit bridge/job protocol, JSON serialization/reflection, build/capture/audit job support | DEFER |
| 536–540 | Unity expert environment/project discovery, live editor bridge, review/stat/run helpers | DEFER |
| 541–544 | Unity gameplay editor jobs: audio mixer authoring, scene audit, NavMesh scenes, physics/project settings | DEFER |
| 545–569 | Unity gameplay runtime components and performance/AI/network prediction helpers | DEFER |
| 570 | Unity gameplay runner-side adapter | DEFER |
| 571–572 | Unity mobile audio import and Android/iOS build/player settings jobs | DEFER |

**All 50 entries remain DEFER.** No final `copy`, `adapt`, `archive-only`, or `exclude` decision is made. This report does not authorize skill registration, import, execution, or activation.

## Findings

### 1. Unity test templates and architecture runner (523–528)

- Rows 523–527 are Unity/NUnit PlayMode fixtures that create GameObjects, invoke lifecycle callbacks, inspect Input System/player isolation, enumerate prefabs and ScriptableObjects, and verify event/listener cleanup. They are engine-specific tests/fixtures, not MoreAI tests and not evidence of test execution.
- `ut_arch.py` (528) scaffolds Unity project directories and C# templates, edits project files, configures Git and invokes UnityYAMLMerge. It imports shared runner modules and uses filesystem/process operations. Never run in the FastAPI request process or expose arbitrary project paths, Git configuration or merge operations to customer prompts.
- Unity lifecycle patterns such as explicit cancellation/disposal may be useful as conceptual references, but must be independently mapped to the existing MoreAI durable-run/event lifecycle; do not copy Unity object lifecycle semantics into the API/worker.

### 2. Unity expert AgentKit and editor bridge (529–540)

- AgentKit source defines a job protocol that reads `args.json`, dispatches editor methods, writes result envelopes, persists bridge context via Unity SessionState, and can exit or remain resident. It is a Unity Editor control plane, not a general MoreAI agent runtime.
- `AgentJob.cs` accepts method names/arguments, reads/writes files, exposes project-root path resolution, and can invoke editor-side operations. Arbitrary method dispatch and caller-controlled paths would be unsafe as customer-facing capabilities.
- `AgentJson.cs` uses reflection/public-field serialization and generic object conversion. Any reuse would need strict typed schemas and bounded payload sizes; arbitrary reflection/object serialization is not an acceptable API contract.
- Runner-side helpers use subprocesses to launch/inspect Unity, mutate project files, manage editor processes and bridge requests, and may invoke CLI/editor code. They require a dedicated isolated worker, immutable toolchain, fixed operation allowlist, argument validation, process-tree timeout/cleanup, workspace confinement and explicit approval.
- The live bridge supports executing C# snippets and editor methods. Treat this as privileged arbitrary-code execution; it must not be exposed to customer prompts or the ordinary Skill Registry.
- Image review/stat helpers process generated captures or reports; they are not directly relevant to MoreAI customer dashboard capability absent a separately approved Unity product workflow.

### 3. Unity gameplay editor and runtime code (541–570)

- Editor jobs manipulate Unity AudioMixer internals through reflection, audit scenes, bake NavMesh, create project assets, and alter physics/project settings. Internal Unity APIs are version-sensitive and project-mutating; keep deferred.
- Runtime components implement audio emitters, AI budgets, enemy state machines, perception, projectiles, pooling, navigation and update registries. They depend on Unity GameObjects, MonoBehaviours, Physics, NavMesh, Burst/Jobs and Unity lifecycle. They are not reusable as-is in a web/API runtime.
- Some performance and gameplay scripts write profiling/budget output to project-local files. Do not create a parallel local persistence store for MoreAI; canonical business/application state remains in Supabase behind FastAPI.
- `NetSim.cs` is described as a pure C# client prediction/reconciliation helper without Unity networking types. Even where logic is portable, its game-networking purpose does not map to MoreAI customer orchestration without a separate product requirement and review.
- `ut_gameplay.py` is a runner-side helper importing shared Unity expert tooling and manipulating project files; isolate and constrain if ever adopted.

### 4. Unity mobile build and media jobs (571–572)

- Mobile audio jobs inspect/fix import settings and project assets; build jobs configure Android/iOS player settings and invoke platform build operations. These are privileged project mutation/build tasks.
- Any future adoption requires a dedicated ephemeral worker with pinned Unity/editor and platform toolchains, fixed target allowlist, immutable inputs, project-copy isolation, signed/provenanced artifacts, strict output limits, cancellation and auditable approval. No build or editor process was launched for this audit.

## MoreAI adoption constraints

1. OpenManus remains the single Agent Runtime. OpenFuse remains an internal capability adapter in FastAPI, not a second application/runtime.
2. The single Memory Coordinator owns Working, Conversation, Long-term, Episodic, Semantic and Procedural memory over existing Supabase structures. Do not introduce Unity/local-file persistence or another database.
3. Customer frontend actions continue through typed FastAPI contracts; browser Supabase access remains limited to approved Auth flows.
4. Do not expose Unity CLI/editor control, arbitrary C# snippets, dynamic method dispatch, process commands, project paths, build/publish operations or raw file writes to customer prompts.
5. Any engine-specific skill needs explicit product mapping, legal/provenance review, isolated worker design and final P1 approval before registration.
6. Preserve the existing Next.js customer UI. Add only genuinely missing PRD components using existing CSS, fonts, buttons, colors and design tokens.
7. Hash agreement proves the reviewed bytes match the pinned source; it does not prove license, security, dependency completeness, data rights or production readiness.

## Status and next work

- Rows reviewed in this batch: **523–572 (50 files)**.
- Integrity: **50/50 Git blob SHA matches; 50/50 byte-size matches**.
- Interim disposition: **50 DEFER; 0 final approvals**.
- Cumulative contiguous rows covered by batches 014–017: **171–572**, subject to verifying all earlier batch reports/ledger references before stating overall completion.
- Next executable-source range: **573–622 (50 files)**.
- After all 875 executable-source entries are reviewed, audit non-executable configuration/schema, references/dependencies, assets/fonts and SBOM; reconcile exact-version dependency graph and licenses; then make final per-file dispositions.
- P1 remains **OPEN**. Do not claim Phase 04–09 integration completion or Phase 10/11 release acceptance based on this audit. User has prohibited real tests and staging, so Phase 10/11 acceptance remains blocked.
