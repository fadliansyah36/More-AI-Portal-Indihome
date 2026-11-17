# P1 Executable Payload Review — Batch 007 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Maya Python files were fetched from the pinned source commit and inspected as text. Targeted scans covered process execution, network clients, dynamic code, filesystem operations, renderer calls and dynamic imports. No source was imported or executed. No Maya/mayapy runtime, DCC process, package installation, build, test, render, worker, filesystem write, network call, provider, staging, deployment or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_validate.py` | 42,079 | Scene validation and optional safe-fix operations; uses Maya commands/MEL; module explicitly says not yet run in Maya; adds skill path | DEFER |
| `skills/dcc/maya/scenario-maya-fx/scripts/mx_fx.py` | 103,486 | Nucleus/nCloth/Bifrost/MASH/cache and Arnold workflows; MEL commands; temp/output directories; several Maya-layer calls marked unverified | DEFER |
| `skills/dcc/maya/scenario-maya-groom/scripts/mx_groom.py` | 168,954 | XGen Interactive Groom, plugin loading, filesystem/cache/render workflows; contains `exec(pmc, ...)` and MEL evaluation paths | DEFER / HIGH-RISK DYNAMIC EXECUTION |
| `skills/dcc/maya/scenario-maya-lighting-rendering/scripts/mx_light.py` | 196,902 | Maya/Arnold render pipeline; subprocess render invocation; dynamic module import via `__import__(m)`; Maya layer documented as not yet run in Maya | DEFER |
| `skills/dcc/maya/scenario-maya-lookdev/scripts/mx_shade.py` | 128,158 | Look-dev/material/texture/Arnold rendering; reads image/texture files and invokes MEL batch render; Maya layer documented as not yet run in Maya | DEFER |

## Findings

- `mx_groom.py` contains a direct `exec(pmc, {"cmds": cmds, "mel": mel})` path and several MEL evaluation operations. The execution context and origin of `pmc` must be traced end-to-end before any use. Treat it as a high-risk dynamic execution surface; never pass customer-authored strings or untrusted scene content into it.
- `mx_light.py` uses `subprocess.run` for a render command and `__import__(m)` for module loading. Both executable and imported module must be selected from a server-side allowlist, with fixed paths, pinned versions, bounded arguments, timeouts and process-tree cleanup.
- `mx_fx.py` invokes Maya MEL procedures for simulation/cache/render operations. Several Maya API/procedure names are explicitly marked unverified in source; offline helper tests do not validate the installed Maya/MtoA/Bifrost/MASH runtime.
- `mx_validate.py` offers both read-only validation and optional mutation via safe-fix operations. The adapter must expose read-only validation separately and require an explicit policy/approval gate for any scene mutation or save-as operation.
- `mx_shade.py` handles texture/image paths and render outputs. Inputs and outputs must be confined to the per-Agent-Run workspace; external texture paths must not permit arbitrary host filesystem reads.
- Maya 2027, Arnold/MtoA, XGen, Bifrost, MASH and associated plugins require a separately pinned runtime/plugin matrix and legal review. They cannot be assumed available or compatible in a generic Python/Blender worker.
- The narrow scan did not demonstrate an outbound HTTP client in these five files. It is not a complete transitive egress review. The scan found dynamic code execution in `mx_groom.py` and dynamic module loading in `mx_light.py`.
- No skill is enabled or approved by this review. Hash matches establish source integrity only, not license, security or production suitability.

## Required adaptation boundary

- Keep all five payloads disabled pending full content, dependency, license and transitive-call review.
- For Maya headless tasks, use a distinct digest-pinned Maya worker image; never execute DCC code inside FastAPI or a Blender worker.
- Prohibit customer-provided Python/MEL and arbitrary `exec`/dynamic import. Replace dynamic module lookup with a fixed allowlisted registry; remove or strictly isolate dynamic execution after a documented source trace and security review.
- Separate read-only validation from scene mutation, save, cache generation and rendering; mutations require explicit authorization and durable audit records.
- Restrict plugin set, external binaries, texture paths, scene paths and output paths to server-managed allowlists and per-run workspaces.
- Enforce non-root execution, no host mounts/secrets, default-deny egress, CPU/RAM/PID/disk/time/output quotas, process-tree termination and ephemeral workspace cleanup.
- Validate and quarantine image/video/cache outputs, scan before publication, and bind accepted artifacts to owner and Agent Run with ownership-checked signed downloads.
- Enforce durable cancellation, timeout, lease fencing, audit receipts and usage metering through the existing worker lifecycle.

## Result

**Batch 007: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** `mx_groom.py` is flagged for dynamic code execution; `mx_light.py` for subprocess and dynamic module loading. No preliminary evidence ledger row was changed to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–007: **35**. P1 remains OPEN. Continue remaining executable review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
