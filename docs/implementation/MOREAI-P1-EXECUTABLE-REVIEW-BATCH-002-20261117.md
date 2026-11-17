# P1 Executable Payload Review — Batch 002 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Python payloads were fetched from the exact pinned raw GitHub paths and inspected as text. This is manual static review only. No Python code was imported or executed; no Blender process, package installation, build, test, renderer, filesystem write, network call, provider, staging, deployment or Supabase mutation was performed.

## Reviewed files

| File | Bytes in evidence | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex1_watchmaker.py` | 8,683 | Imports `os`/ `sys`, adds script directory to import path, imports shared scene helpers; constructs a complete Blender scene | DEFER |
| `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex2_saltflat.py` | 8,899 | Same import-path pattern; scene construction with large environment geometry and animated vehicles | DEFER |
| `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex3_bridge.py` | 12,567 | Same import-path pattern; imports `random`; builds multi-character scene and animation | DEFER |
| `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex4_sky_islands.py` | 13,572 | Same import-path pattern; imports `random` and `mathutils`; builds large multi-character fantasy scene | DEFER |
| `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex_common.py` | 4,319 | Imports Blender and sibling modules; reads command-line arguments; derives output path; appends sibling script paths; writes scene deliverables/reports via helper workflow | DEFER — shared entrypoint/helper has output-path and process-boundary implications |

## Findings

- These are complete Blender scene-generation examples, not isolated pure functions. Their scene mutations and asset creation must occur only inside a dedicated isolated DCC worker.
- Each example changes Python's module search path based on its own file location and imports `ex_common`. The helper then appends paths for sibling skills and imports `bx_blockout` and `bx_kits`. Runtime composition therefore depends on a precisely assembled, pinned skill bundle; do not install or expose arbitrary sibling paths.
- `ex_common.py` consumes command-line arguments and assigns the first argument to an output directory. No path confinement is visible in the reviewed opening/argument setup. The caller must supply a server-generated job directory, never a customer-selected host path.
- The helper's docstring describes writing JSON stats, still images, playblast and a Blender project. Output quotas, allowed extensions, MIME inspection, quarantine and ownership binding are mandatory.
- `ex3_bridge.py` and `ex4_sky_islands.py` import Python's `random`; deterministic seed policy should be explicit if reproducible artifacts are required.
- Limited pattern inspection found no direct `subprocess`, network-client, `eval()` or `exec()` marker in these five files. This is not proof of safety: imported helpers and Blender operators can perform additional filesystem or process operations.
- The examples are useful as curated DCC workflow templates, but should not be exposed as customer-authored arbitrary Python or copied as a general-purpose backend capability.

## Required adaptation boundary

1. Keep all example scripts disabled as executable skills until dependency, license and full transitive-call review is accepted.
2. Run only through a server-selected, pinned Blender worker image; the API must enqueue typed jobs and never invoke arbitrary scripts or shell commands.
3. Mount only an ephemeral per-run workspace; confine every output path to that workspace and enforce size/time/process quotas.
4. Default-deny network egress and block private/metadata address ranges.
5. Validate all input assets, quarantine outputs, inspect MIME and dimensions, and store final artifacts through owner-scoped FastAPI flows.
6. Link every run to Agent Run ownership, cancellation, durable checkpoints, retry fencing, usage metering and audit events.

## Result

**Batch 002: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** The evidence ledger's preliminary disposition remains unchanged. No final P1 acceptance is implied.

Cumulative manually reviewed executable payloads in batches 001–002: 10. P1 remains OPEN. Continue with the next executable batch and then finish configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
