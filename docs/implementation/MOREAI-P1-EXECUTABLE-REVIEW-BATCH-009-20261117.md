# P1 Executable Payload Review — Batch 009 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five executable files were fetched from the pinned Scenario Skills commit and inspected statically. Scans covered process execution, network clients, dynamic code/import, filesystem access, application launch and DCC runtime boundaries. No source was imported or executed. No ZBrush/Maya runtime, process, package install, test, build, render, worker, provider, staging, deployment, migration or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_batch_job.py` | 6,002 | ZBrush `-script` job entrypoint; reads job JSON, resolves recipe references, writes result; imports toolkit modules dynamically by path | DEFER / HIGH-RISK JOB & MODULE BOUNDARY |
| `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_goz.py` | 18,844 | GoZ binary read/write and folder protocol; subprocess launches macOS `open -a` | DEFER |
| `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_plugin_ops.py` | 30,311 | ZBrush plugin/SubTool operations; filesystem exports; explicitly says not yet run in ZBrush | DEFER |
| `skills/dcc/zbrush/scenario-zbrush-character-creature/scripts/zb_character.py` | 112,551 | Character/creature sculpt toolkit; dynamic importlib loading of expert modules; source marks ZBrush-side layer unverified | DEFER / DYNAMIC MODULE BOUNDARY |
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_audit.py` | 17,846 | Agent-side OBJ audit, filesystem reads/JSON output, CLI, NumPy dependency | DEFER |

## Findings

- `zb_batch_job.py` accepts a job JSON path and resolves recipe references; it dynamically imports a set of toolkit modules by temporarily modifying `sys.path`. The job schema, recipe step names, referenced functions, parameter values, result path and scene path must be validated against a server-owned allowlist. Never accept arbitrary module/function names or caller-selected output paths.
- `zb_goz.py` is comparatively portable for binary GoZ parsing/writing, but contains an application-launch helper using subprocess `open -a`. Keep binary parsing separate from desktop application control; the latter is macOS-specific and must not run in a generic service worker.
- `zb_plugin_ops.py` automates ZBrush plugin operations and filesystem exports. Its own source status says the ZBrush-side functions have not yet run in ZBrush; offline fake-handle tests do not prove runtime compatibility.
- `zb_character.py` uses `importlib.import_module` with expert modules and explicitly documents unverified ZBrush-side operations. Dynamic module names must be replaced by a fixed registry and all scene operations must remain in the isolated ZBrush worker.
- `zb_audit.py` parses OBJ files and writes JSON output; it requires NumPy and has CLI/file-path surfaces. Bound file size, vertex/face counts, memory/CPU and runtime; input must be an owner-authorized artifact and paths must be workspace-confined.
- The narrow scan did not demonstrate direct outbound HTTP clients. This is not a complete transitive dependency or egress audit.
- ZBrush 2026/CPython 3.11.9, plugin versions, OS support and Maxon licensing need a separately pinned and approved runtime matrix. Do not co-locate ZBrush GUI automation with FastAPI or the general worker.
- No file is approved or enabled. Integrity hashes are not license, security or production approval.

## Required adaptation boundary

- Keep all five files disabled pending full source, dependency, license and runtime review.
- Split pure GoZ/OBJ parsing from ZBrush application/plugin automation; only the pure data layer may be considered for a separately sandboxed, dependency-pinned parser after format and resource-limit review.
- Replace dynamic imports with fixed server-side module/function registries. Reject customer-controlled module names, recipe callables, executable paths and arbitrary commands.
- Accept only schema-validated recipes with bounded step count, argument types, file sizes and resource budgets.
- Use separate digest-pinned, licensed ZBrush worker; non-root, ephemeral, no host mounts/secrets, default-deny egress, fixed executable paths, process-tree termination and hard timeouts.
- Restrict all inputs/outputs to server-generated per-run workspaces; enforce canonical path containment, symlink-safe operations, quotas and cleanup.
- Keep Agent Run lifecycle, authorization, audit, quota and artifact ownership in FastAPI/Supabase; publish only validated/quarantined artifacts with owner-checked downloads.

## Result

**Batch 009: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** Dynamic import/job-recipe boundaries and host application launch are key controls. No preliminary ledger row was promoted to final disposition.

Cumulative manually reviewed executable payloads in batches 001–009: **45**. P1 remains OPEN. Continue remaining executable payload review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
