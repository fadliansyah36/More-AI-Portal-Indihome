# P1 Executable Payload Review — Batch 001 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review method and boundary

Five executable Python payloads were fetched from the exact pinned raw GitHub commit and read as source text. This was a manual static review only. No code was imported or executed; no package was installed; no Blender, subprocess, renderer, filesystem write, network call, provider, build, test, staging, deployment or Supabase operation was run.

This batch is an incremental source review. It is not a malware scan, sandbox certification, dependency/license clearance, or approval to copy or execute any file. The main audit CSV's preliminary dispositions are intentionally not changed to final.

## Files reviewed

| Payload | Bytes in existing evidence | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/blender/scenario-blender-animation/scripts/bx_anim.py` | 103,252 | Imports Blender APIs and math utilities; filesystem/path use; animation and image-generation helpers | DEFER pending sandbox/API, filesystem and dependency review |
| `skills/dcc/blender/scenario-blender-blockout/scripts/bx_blockout.py` | 35,735 | Imports Blender, bmesh, tempfile; creates/manipulates scenes and collections; writes backup copies | DEFER pending isolated project workspace and filesystem policy |
| `skills/dcc/blender/scenario-blender-blockout/scripts/bx_kits.py` | 66,846 | Imports Blender APIs; scene/object/material construction and modification; no network or subprocess pattern in static scan | DEFER pending isolated Blender worker and asset/resource limits |
| `skills/dcc/blender/scenario-blender-expert/scripts/bx_audit.py` | 31,886 | Imports Blender APIs; optional JSON report file write; CLI process exit behavior | DEFER pending sandbox and output-path controls |
| `skills/dcc/blender/scenario-blender-export/scripts/bx_export.py` | 36,318 | Imports subprocess, filesystem and temporary-file modules; CLI batch/export/import paths; static network-related pattern requires contextual follow-up | DEFER; highest-priority review for subprocess allowlist, path confinement and egress |

## Security and architecture findings

- All five scripts are Blender/DCC execution payloads, not safe customer-browser code and not ordinary FastAPI request-handler code.
- The first four use Blender APIs to inspect or mutate project data; scene/file ownership, project isolation, resource limits and output path confinement are required before any worker adaptation.
- `bx_blockout.py` includes backup creation with filesystem writes. The worker must never expose arbitrary host paths.
- `bx_audit.py` writes JSON to a caller-provided path and has CLI exit behavior; output destinations must be mapped to an isolated job workspace.
- `bx_export.py` explicitly imports `subprocess` and documents headless Blender command execution. Its process launch, argument construction, batch traversal, import/export paths and all network-related matches require a complete function-level review. It must not be invoked by API processes or customer-controlled arbitrary commands.
- The static pattern scan found no `eval()` or `exec()` call in these five files. This does not establish absence of dynamic execution through other APIs or imported dependencies.
- No external network request pattern was found in the first four files by the limited scan. The fifth file's network-related match remains unresolved and is not classified as a confirmed vulnerability without contextual source review.

## Required MoreAI adaptation boundary

Any future use must be mediated by a dedicated isolated renderer/DCC worker with:
- server-selected, pinned tool versions and immutable runtime image;
- no customer-supplied shell command or arbitrary Python execution;
- per-run ephemeral workspace, strict path normalization and no host filesystem mounts;
- CPU, memory, process-count, wall-clock and output-size quotas;
- default-deny egress, explicit destination allowlists and no cloud metadata/private-network access;
- credentials injected only as scoped server-side secret references when needed;
- malware/content scanning and MIME validation for inputs/outputs;
- artifact quarantine, signed owner-scoped downloads, retention/deletion and audit receipts;
- durable Agent Run linkage, cancellation, timeout, retry fencing and metering.

## Result

**Batch 001: 5 executable payloads statically reviewed. All five remain DEFER.** This is not a final per-file P1 disposition and does not reduce the remaining executable-review count unless the governance ledger is updated with an independently auditable row-level decision.

P1 remains OPEN. Continue with the next executable batch, then configuration/schema and reference payloads, asset/font provenance, and exact-version dependency/SBOM reconciliation.
