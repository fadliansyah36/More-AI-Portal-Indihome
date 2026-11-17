# P1 Executable Payload Review — Batch 005 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Python files were fetched from the pinned source commit and inspected as source text. Targeted static scans covered process execution, network clients, dynamic code, filesystem writes, renderer calls, Maya imports and dynamic module loading. No code was imported or executed. No Blender/Maya runtime, dependency installation, build, test, render, worker, filesystem write, network call, provider, staging, deployment or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/blender/scenario-blender-sculpting/scripts/bx_sculpt.py` | 79,076 | NumPy mesh-data sculpting; headless-safe per module docs; writes rendered image outputs; imports through skill path | DEFER |
| `skills/dcc/blender/scenario-blender-texturing-shading/scripts/bx_materials.py` | 87,244 | Material/node construction, texture path inputs, render checks and output-directory creation; imports sibling expert scripts | DEFER |
| `skills/dcc/blender/scenario-blender-uv-baking/scripts/bx_uvbake.py` | 107,561 | UV unwrap/pack/bake and render/output paths; mutates import path to load sibling modules | DEFER |
| `skills/dcc/maya/scenario-maya-animation/scripts/mx_anim.py` | 111,834 | Maya 2027 animation/curve tools; filesystem plan/output operations; lazy Maya imports and GUI playblast references; prepends skill paths | DEFER |
| `skills/dcc/maya/scenario-maya-deformation/scripts/mx_skin.py` | 115,009 | Maya skinning/weight and deformation tools; filesystem spec/report operations; dynamic `importlib.import_module` plugin/module loading; sibling path injection | DEFER |

## Findings

- Blender sculpting, material, UV and baking modules are headless-oriented DCC operations, but headless compatibility does not equal permission to run them in FastAPI. They require the isolated DCC worker and durable Agent Run lifecycle.
- Blender modules generate render/bake/review outputs and accept or document filesystem paths. Production adapters must generate per-run paths server-side, reject path traversal/symlinks, enforce quotas and ensure all output remains within the ephemeral workspace.
- Maya modules target Maya 2027 and depend on Maya runtime/API availability. They must not be routed to a Blender worker or generic Python worker. Runtime image, license entitlement, plugins, API version and worker capacity must be separately pinned and governed.
- `mx_anim.py` documents both headless and GUI playblast paths. GUI-only actions must be separated from headless operations and must not be silently substituted.
- `mx_skin.py` uses `importlib.import_module` for optional modules/plugins. Production must use a fixed allowlisted module registry; user-controlled module names or paths must never be imported.
- The limited static scan found no `eval()` or `exec()` calls and no demonstrated outbound HTTP/socket client in these five files. This is not proof that all transitive dependencies or invoked DCC APIs are safe.
- NumPy and Maya/Blender binary/API dependencies require exact-version and license reconciliation. Maya runtime licensing and distribution constraints remain explicit blockers pending legal review.
- No skill is enabled or approved by this review. Hash matches establish source integrity only, not licensing, security or production suitability.

## Required adaptation boundary

- Keep all five payloads disabled pending complete content, dependency, license and transitive-call review.
- Use distinct digest-pinned worker images and execution policies for Blender and Maya; never run DCC code directly inside FastAPI.
- Separate headless capabilities from GUI-only workflows; GUI workflows require a separately authorized interactive desktop session.
- Enforce per-Agent-Run ephemeral workspace, server-generated paths, process-tree termination, resource/time/output quotas, default-deny egress and cleanup.
- Validate inputs and generated image/video outputs; quarantine and scan before artifact publication; bind artifacts to owner, workspace and Agent Run.
- For dynamic Maya plugins, resolve only from a pinned server-side allowlist with explicit license and provenance records.
- Enforce durable cancellation, timeout, lease fencing, audit receipts and usage metering through the existing worker lifecycle.

## Result

**Batch 005: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** No preliminary evidence ledger row was changed to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–005: **25**. P1 remains OPEN. Continue the remaining executable review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
