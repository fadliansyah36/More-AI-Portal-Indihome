# P1 Executable Payload Review — Batch 004 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Python files were fetched from the pinned source commit and inspected as source text, including targeted static scans for process execution, network clients, dynamic code, filesystem writes, Blender rendering and import-path mutation. No code was imported or executed. No Blender, dependency installation, build, test, renderer, worker, filesystem write, network call, provider, staging, deployment or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/blender/scenario-blender-hard-surface/scripts/bx_hardsurface.py` | 69,529 | Blender mesh/BMesh operations, NumPy and mathutils; appends sibling expert scripts to `sys.path`; invokes Blender still render | DEFER |
| `skills/dcc/blender/scenario-blender-lighting-rendering/scripts/bx_light.py` | 102,909 | Blender lighting/compositor/render and OpenImageIO image reads; creates output directories and writes a legend file; invokes render | DEFER |
| `skills/dcc/blender/scenario-blender-previs-storyboard/scripts/bx_previs.py` | 69,531 | Scene/camera/animation/Video Sequence Editor workflows; creates output directories, still renders and animatic outputs; mutates import path | DEFER |
| `skills/dcc/blender/scenario-blender-retopology/scripts/bx_retopo.py` | 128,581 | BMesh/NumPy/BVH mesh processing; creates output directories and renders; appends sibling expert scripts to `sys.path` | DEFER |
| `skills/dcc/blender/scenario-blender-rigging/scripts/bx_rig.py` | 139,639 | Rigify/armature/weights/pose/render workflows; imports `subprocess`, invokes a Blender subprocess via argument list, creates temporary/output directories and files, mutates import path | DEFER |

## Findings

- These are Blender DCC capabilities, not FastAPI request-handler code. All execution must be dispatched to a separately isolated, digest-pinned DCC worker with non-root identity, resource/time/process/output quotas, no host mounts/secrets and default-deny egress.
- `bx_hardsurface.py`, `bx_light.py`, `bx_previs.py`, `bx_retopo.py` contain rendering and/or filesystem output behavior. Output paths must be server-generated and confined to an ephemeral per-Agent-Run workspace; caller-controlled absolute paths must not reach these functions.
- `bx_rig.py` explicitly imports `subprocess` and calls `subprocess.run` to launch Blender for cycle checking. The call uses an argument list rather than a shell string, but still requires process allowlisting, fixed executable selection, bounded execution, process-tree termination, and path confinement. It must not run inside FastAPI.
- Several modules append sibling skill directories to `sys.path`. Production packaging must resolve these dependencies from a pinned, immutable worker image rather than accepting customer-controlled import paths.
- NumPy is imported by hard-surface and retopology; lighting also imports NumPy and optionally OpenImageIO. Rigging imports NumPy. Exact versions, binary provenance, platform compatibility and transitive license obligations remain SBOM gates.
- The limited scan found no `eval()` or `exec()` calls and no demonstrated outbound HTTP/socket client in these five files. This narrow pattern scan is not proof of absence of all dynamic execution or egress paths.
- No skill is enabled or approved by this review. Hash matches establish source integrity only, not licensing, security or production suitability.

## Required adaptation boundary

- Keep all five payloads disabled pending full content, dependency, license and transitive-call review.
- Preserve the hard rule: Blender GUI-only skills are not routed to headless workers. These five modules document headless workflows, but that does not authorize execution until worker acceptance gates are met.
- Run DCC tasks only in a disposable isolated worker; FastAPI only validates/authorizes/enqueues and tracks durable Agent Run state.
- Generate workspace paths server-side; enforce path traversal/symlink protections, per-run isolation, cleanup and output quotas.
- Validate source inputs and generated image/video MIME, file signatures, dimensions, duration, frame rate and size; quarantine and scan before artifact publication.
- Bind every accepted artifact to its Agent Run, owner and workspace; use signed, ownership-checked downloads.
- Enforce durable cancellation, timeout, lease fencing, audit receipts and usage metering through the existing worker lifecycle.

## Result

**Batch 004: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** No preliminary evidence ledger row was changed to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–004: **20**. P1 remains OPEN. Continue the remaining executable review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
