# P1 Executable Payload Review — Batch 003 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Python files were fetched from the pinned raw GitHub commit and inspected as source text. No code was imported or executed. No Blender, package installation, build, test, renderer, filesystem write, network call, provider, staging, deployment or Supabase operation was run.

## Reviewed files

| File | Bytes in evidence | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/blender/scenario-blender-expert/scripts/bx_gui.py` | 8,951 | Blender GUI context and view3d brush operators; explicitly not headless-compatible per module documentation | DEFER / GUI-ONLY capability; do not expose through server worker |
| `skills/dcc/blender/scenario-blender-expert/scripts/bx_review.py` | 15,644 | Blender Workbench render/review helpers; filesystem/path usage; creates temporary scene and image outputs | DEFER |
| `skills/dcc/blender/scenario-blender-geometry-nodes/scripts/bx_gn.py` | 57,043 | Blender Geometry Nodes construction/evaluation/render; filesystem and time use; network-pattern scan requires contextual review | DEFER |
| `skills/dcc/blender/scenario-blender-grease-pencil/scripts/bx_gp.py` | 47,192 | Blender Grease Pencil data/animation/render; imports NumPy and tempfile; filesystem and network-pattern scan requires contextual review | DEFER |
| `skills/dcc/blender/scenario-blender-hair/scripts/bx_hair.py` | 55,125 | Blender hair-curves grooming and geometry-node workflows; imports NumPy; filesystem and network-pattern scan requires contextual review | DEFER |

## Findings

- `bx_gui.py` explicitly requires a running Blender GUI/window and view region. It must not be routed into a headless worker or ordinary customer request lifecycle. If ever supported, it needs a separately authorized interactive desktop session with explicit user control.
- `bx_review.py` renders into image outputs and temporarily creates a scene. Output location and temporary scene cleanup must remain inside an isolated per-run workspace.
- `bx_gn.py`, `bx_gp.py` and `bx_hair.py` construct/evaluate complex Blender data graphs and render artifacts. Their imported dependencies and transitive Blender API calls need pinned versions and worker resource quotas.
- Static network-pattern matches in `bx_gn.py`, `bx_gp.py` and `bx_hair.py` were contextualized against nearby source: the observed matches were ordinary identifiers, comments or Blender node/socket names rather than demonstrated outbound HTTP/socket calls. This is a narrow source observation, not a complete egress guarantee.
- Grease Pencil and Hair scripts import NumPy; exact runtime compatibility and license provenance for the transitive dependency set remains part of the SBOM gate.
- No direct `subprocess`, `eval()` or `exec()` marker was found in the five files by the limited scan. Absence of those text patterns does not establish safety.
- These are domain-specific DCC tools and cannot be treated as browser-side code, generic FastAPI handlers, or automatically enabled customer skills.

## Required adaptation boundary

- Keep all five payloads disabled pending license/dependency and complete transitive-call review.
- GUI-only actions remain unavailable in headless execution; never emulate or silently substitute them.
- Server-selected pinned Blender/NumPy runtime only; no arbitrary Python or shell from customer input.
- Ephemeral isolated workspace, strict output path confinement, CPU/RAM/time/process/output quotas, default-deny egress.
- Validate source assets and generated MIME/dimensions; quarantine outputs and bind signed downloads to owner and Agent Run.
- Enforce durable cancellation, timeout, lease fencing, audit receipts and usage metering through existing worker lifecycle.

## Result

**Batch 003: 5 additional executable payloads statically reviewed; all 5 remain DEFER (with bx_gui explicitly GUI-only).** No preliminary evidence ledger row was changed to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–003: 15. P1 remains OPEN. Continue the remaining executable review and then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
