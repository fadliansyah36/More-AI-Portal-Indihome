# P1 Executable Payload Review — Batch 008 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five executable source files were fetched from the pinned Scenario Skills commit and reviewed as text. Targeted static scans covered process creation, network calls, dynamic execution/import, filesystem paths, Maya commands and rendering. No file was imported or executed. No Maya/ZBrush runtime, process, package installation, test, build, render, worker, provider, staging, deployment, migration, or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/maya/scenario-maya-modeling/scripts/mx_modeling.py` | 82,559 | Maya modeling and OpenMaya operations; MEL cleanup call; skill path manipulation; source says Maya layer unverified | DEFER |
| `skills/dcc/maya/scenario-maya-pipeline-scripting/scripts/mx_pipeline.py` | 118,323 | Maya pipeline; subprocess delegated to mx_run; MEL/FBX commands; filesystem output; dynamic importlib module loading | DEFER / HIGH-RISK PROCESS & MODULE BOUNDARY |
| `skills/dcc/maya/scenario-maya-retopology-uv/scripts/mx_retopology_uv.py` | 151,741 | Retopology/UV/bake-prep; reads spec and writes JSON/output dirs; Maya API; skill path mutation | DEFER |
| `skills/dcc/maya/scenario-maya-rigging/scripts/mx_rig.py` | 126,334 | Rigging, Maya solver MEL call, review sheet output; Maya layer not yet verified | DEFER |
| `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_batch.py` | 53,865 | ZBrush batch orchestration; subprocess/Popen, macOS `screencapture`/`osascript`/`open`; folder discovery/staging/output/logging | DEFER / HIGH-RISK HOST PROCESS & OS-SPECIFIC |

## Findings

- `mx_pipeline.py` invokes `mx_run.run_subprocess` for per-scene mayapy jobs, uses `importlib.import_module(name)`, constructs FBX/MEL operations, and writes job outputs. The called runner, module names, executable, arguments and file paths require end-to-end allowlisting and review; do not expose arbitrary module names or job paths to customer input.
- `zb_batch.py` launches host processes using subprocess/Popen and invokes macOS-specific GUI utilities (`screencapture`, `osascript`, `open`). It assumes desktop/host application control and cannot be treated as a portable headless Linux worker capability. Any future adapter needs a separate ZBrush worker/runtime and explicit executable allowlists, process-tree cleanup, timeouts, and isolated I/O.
- `mx_modeling.py` and `mx_rig.py` use Maya/MEL operations; their source documentation states Maya-layer calls remain unverified. Offline pure-Python coverage does not establish Maya runtime compatibility.
- `mx_retopology_uv.py` reads caller-supplied spec files and writes output artifacts. The adapter must resolve inputs only from owner-authorized artifacts, validate schema and size, and confine all paths to a per-run workspace.
- No direct outbound HTTP client was demonstrated by the narrow scan. This is not a transitive egress or dependency audit.
- Maya 2027 and ZBrush 2026 require separately pinned, licensed runtime images and plugin/OS matrices. Neither should execute inside FastAPI or a generic worker.
- No file is approved or enabled. Source hash/size integrity does not establish license, security or production suitability.

## Required adaptation boundary

- Keep all five files disabled pending complete source/dependency/license review.
- Split Maya and ZBrush into separate, digest-pinned worker images with explicit license entitlement and runtime acceptance.
- Replace dynamic module loading with a fixed server-side registry; reject customer-controlled module, executable, command, plugin, and path values.
- Permit only server-generated per-run input/output directories; enforce canonical path containment, symlink-safe operations, quotas, timeout, cancellation, process-tree termination and cleanup.
- Use non-root, ephemeral workers with no host mounts/secrets and default-deny egress.
- Audit MEL/FBX command construction and escape/validate every scene, node, filename and path value; do not pass arbitrary customer-authored MEL/Python.
- Keep UI/Agent Run orchestration in existing FastAPI lifecycle; persist run state/artifact provenance in Supabase through trusted backend APIs.
- Validate/quarantine output files before publication and bind artifacts to run owner with authorization-checked downloads.

## Result

**Batch 008: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** High-risk boundaries identified in Maya pipeline subprocess/module loading and ZBrush host process/GUI orchestration. No preliminary evidence ledger row was promoted to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–008: **40**. P1 remains OPEN. Continue remaining executable payload review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
