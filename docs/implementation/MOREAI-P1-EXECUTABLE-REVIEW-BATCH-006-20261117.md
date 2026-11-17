# P1 Executable Payload Review — Batch 006 — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Review boundary

Five additional Maya Python files were fetched from the pinned source commit and inspected as text, with targeted scans for process execution, sockets/listeners, dynamic code, filesystem operations and dynamic imports. No source was imported or executed. No Maya/mayapy runtime, DCC process, package installation, build, test, render, worker, filesystem write, network call, provider, staging, deployment or Supabase operation was run.

## Reviewed files

| File | Bytes | Static observations | Interim disposition |
|---|---:|---|---|
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_audit.py` | 43,612 | Maya/OpenMaya mesh extraction plus offline analysis; writes JSON report; module states Maya extraction is not yet run/unverified | DEFER |
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_bridge.py` | 15,378 | External client uses Unix-domain socket or TCP connection to a Maya command bridge; stages job/options/output files; can request module/function invocation | DEFER |
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_bridge_server.py` | 14,909 | Starts loopback commandPort inside live GUI Maya; reads job code and executes `exec(compile(code,...))` in Maya namespace; writes job/log files | DEFER / HIGH-RISK EXECUTION BRIDGE |
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_review.py` | 63,769 | Maya/Arnold review renders, filesystem output, subprocess calls to image/video utilities, MEL batch render, GUI-only playblast | DEFER |
| `skills/dcc/maya/scenario-maya-expert/scripts/mx_run.py` | 21,770 | Headless mayapy launcher; uses subprocess.Popen with timeout/logging; opens/saves Maya scenes; optional plugin list; script nodes are disabled by default unless explicitly requested | DEFER |

## Findings

- `mx_bridge_server.py` is a critical trust boundary: it receives code from a bridge job file and executes it with Python `exec(compile(...))` inside a live Maya process. Loopback binding does not by itself establish safe tenant isolation, authentication, authorization, request provenance or resistance to local process access. It must not be exposed to customer input or used as a generic remote execution endpoint.
- `mx_bridge.py` supports TCP and Unix-domain sockets and transmits job code/options through files. The client/server pair must remain disabled unless a separately designed interactive-session security model, strong per-session authentication, filesystem isolation and explicit user approval exist. No current acceptance evidence establishes those controls.
- `mx_run.py` launches mayapy using subprocess and can open/save scene files. Its default of not executing scene script nodes is a useful fail-closed behavior; the `--script-nodes` option is an explicit arbitrary-code risk and must remain prohibited for untrusted/customer scenes. Plugin names, scene paths, save paths, process count and timeout must be server-pinned and bounded.
- `mx_review.py` invokes external image/video utilities through subprocess argument arrays and invokes MEL batch rendering. The external executable paths, binary versions, input/output arguments, process timeouts and file access must be fixed by the worker image and policy. Its viewport playblast path is explicitly GUI-only.
- `mx_audit.py` documentation explicitly states the Maya extraction layer has not yet been run in Maya and remains unverified. Offline pure-Python analysis does not validate Maya API behavior.
- No outbound HTTP client was demonstrated in the narrow scan. Socket use in the bridge is an active local IPC/network surface, not proof of external egress. No `eval()` was found; `exec(compile())` is explicitly present in the bridge server.
- These Maya 2027 modules require a separate, pinned Maya runtime, API/plugin inventory and legal review of Autodesk runtime licensing. They cannot be run in Blender worker images or in FastAPI.
- No skill is enabled or approved by this review. Hash matches establish source integrity only, not license, security or production suitability.

## Required adaptation boundary

- Keep the entire Maya bridge pair disabled for customer and automated worker use until its threat model and interactive-session architecture are explicitly approved. Do not expose arbitrary Python execution through commandPort, socket or file-queue adapters.
- For headless Maya work, prefer a narrowly scoped job adapter around a pinned mayapy runtime, fixed allowlisted module/function registry, server-generated job specs and no user-supplied Python source.
- Keep scene script-node execution disabled; reject any request to enable it for untrusted input.
- Use separate digest-pinned Maya worker images, non-root identity, isolated per-Agent-Run workspace, no host mounts/secrets, default-deny egress, resource/process/time/output limits and process-tree termination.
- Fix and verify external executable allowlists (e.g. image/video utilities) and pin their versions; never accept executable paths or shell fragments from customer payloads.
- GUI playblast/interactive bridge workflows require a separate authorized desktop session, not a headless worker.
- Validate and quarantine all image/video outputs, scan before publication, and bind artifacts to owner and Agent Run with ownership-checked signed downloads.
- Enforce durable cancellation, timeout, lease fencing, audit receipts and usage metering through the existing worker lifecycle.

## Result

**Batch 006: 5 additional executable payloads statically reviewed; all 5 remain DEFER.** The Maya command bridge is explicitly flagged as a high-risk arbitrary-code execution surface. No preliminary evidence ledger row was changed to a final disposition.

Cumulative manually reviewed executable payloads in batches 001–006: **30**. P1 remains OPEN. Continue remaining executable review, then configuration/schema, reference, asset/font provenance and exact-version SBOM reconciliation.
