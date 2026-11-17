# P1 Executable Payload Review — Batch 010 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five executable files were fetched from the pinned Scenario Skills commit and inspected statically. Scans covered process execution, network/socket listeners, dynamic code execution, dynamic imports, filesystem and application lifecycle. No source was imported or executed. No ZBrush/Maya runtime, process, package installation, test, build, render, worker, provider, staging, deployment, migration or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_bridge.py` | 1,334 | Client opens TCP connection to loopback port 7788 and transmits caller-provided Python code in JSON | DEFER / HIGH-RISK REMOTE-CODE CLIENT |
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_launch.py` | 24,109 | Starts/stops ZBrush via subprocess/Popen; sends code through bridge; macOS process/osascript controls; runtime operations partly unverified | DEFER / HIGH-RISK PROCESS & CODE DISPATCH |
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_ops.py` | 51,257 | ZBrush command wrappers, file writes and potentially crash-prone operations; source says functions not yet run in ZBrush | DEFER |
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_plugins/zb_bridge_server.py` | 4,372 | TCP server binds loopback; accepts JSON code and runs `exec(compile(code,...), ns)`; no authentication visible in reviewed server source | DEFER / CRITICAL ARBITRARY CODE EXECUTION |
| `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_review.py` | 10,053 | ZBrush view capture and image/contact-sheet processing; filesystem output and image reads; most ZBrush layer not yet run | DEFER |

## Critical security finding — ZBrush bridge

The reviewed `zb_bridge_server.py` accepts a JSON request containing a `code` string and executes it using `exec(compile(code, "<agent>", "exec"), ns)`. The listener is configured for `127.0.0.1` and a configurable port, but loopback binding alone is not an authentication or authorization boundary. The paired `zb_bridge.py` client sends arbitrary code text; `zb_launch.py` exposes run/call behavior to the agent side.

This is an arbitrary-code-execution bridge inside the ZBrush process context. It must not be exposed to customer input, browser-originated requests, untrusted skills, other local tenants, or a shared worker. Treat it as **CRITICAL / DO NOT DEPLOY OR ENABLE** in the current form. A safe future design must remove arbitrary code transport rather than merely adding a port restriction. Replace it with a narrow, typed, fixed operation protocol, explicit server-side operation registry, strict schemas, per-run authorization, capability checks, request authentication bound to the isolated worker, replay protection, hard limits and audit records. Keep the bridge private to a single ephemeral worker and do not rely on loopback as the only control.

## Additional findings

- `zb_launch.py` launches a host ZBrush executable with subprocess/Popen and controls macOS processes via `osascript`; it also orchestrates arbitrary code sent to the bridge. Process paths, environment, arguments, lifecycle, timeout and process-tree cleanup need a strict server-owned allowlist.
- `zb_ops.py` includes ZBrush commands that can crash the application and file writes; its source explicitly says individual functions are not yet run in ZBrush. Any operation that may irreversibly alter a document needs explicit authorization and a per-run copy, not the user's original artifact.
- `zb_review.py` reads image artifacts and writes review output. Enforce image decoding limits, pixel/dimension bounds, path confinement, ownership checks and output quarantine.
- `zb_bridge.py` uses a socket client to localhost and accepts caller-supplied code. It is not a safe service API or tenant isolation mechanism.
- No direct outbound HTTP client was demonstrated in these five files. This is not a complete transitive egress/dependency audit.
- ZBrush 2026, CPython 3.11.9, Maxon plugin behavior and macOS-specific lifecycle require a separate pinned/licensed runtime matrix. Do not place these components inside FastAPI or a general-purpose worker.
- No file is approved or enabled. Hash/size integrity does not establish license, security or production suitability.

## Required disposition and remediation

- Keep all five files disabled. Mark the current arbitrary-code bridge implementation as **EXCLUDE from production use** unless it is replaced by a separately reviewed typed protocol; this is a security recommendation, not a final P1 ledger disposition.
- Do not forward raw Python, MEL, shell, or arbitrary code through OpenManus, OpenFuse, FastAPI, skills, or customer UI to the DCC runtime.
- Keep ZBrush in a separate digest-pinned, licensed, ephemeral worker with non-root execution, no host mounts/secrets, default-deny egress, strict CPU/RAM/PID/disk/time quotas and process-tree termination.
- Expose only narrowly typed operations from a fixed allowlist. Reject arbitrary module/function names, source strings, plugin paths, executable paths and caller-supplied filesystem paths.
- Bind every operation to authenticated owner, Agent Run, approved skill version and capability snapshot; persist durable audit events and cancellation/timeout state through the existing FastAPI/Supabase architecture.
- Operate on server-generated per-run copies; enforce path containment, output quotas, artifact quarantine and owner-checked signed downloads.
- Before any future use, perform complete source and dependency review, license review, runtime compatibility review and threat-model signoff. Those gates are not satisfied by this static batch.

## Result

**Batch 010: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** A critical arbitrary-code execution bridge was identified in `zb_bridge_server.py`; current bridge must not be deployed or enabled. No preliminary evidence ledger row was promoted to final disposition.

Cumulative manually reviewed executable payloads in batches 001–010: **50**. P1 remains OPEN. Continue remaining executable payload review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
