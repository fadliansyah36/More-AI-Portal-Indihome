# P1 Executable Payload Review — Batch 014 (50 files) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope and method

Reviewed the next 50 consecutive `executable-source` ledger entries, rows 171–220. These cover Godot multiplayer, performance/export, pipeline automation, rendering/lighting and shaders. Source files were fetched from the pinned commit and targeted static scans were performed for process execution, network/socket/server behavior, dynamic execution/import, filesystem/resource access, script dispatch, shader operations and project paths.

This is static source review only. No source was executed/imported; no Godot, browser, server, renderer, build, test, worker, provider, staging, deployment, migration or Supabase operation was run.

## Integrity and inventory

Fetched Git blob SHA matched the P1 ledger SHA for all 50 entries: **50/50**.

| Ledger rows | Scope | Interim disposition |
|---|---|---|
| 171–180 | Godot multiplayer helpers and Python harness `gd_net.py` | DEFER |
| 181–189 | Performance/export helpers, local web bridge and Python adapter `gd_perf.py` | DEFER |
| 190–209 | GLB/property pipeline, addon, CI shell, GDExtension example, importer examples, Python adapter and gdUnit test sources | DEFER |
| 210–218 | Rendering compositor, GI bake, graphics tiers, lighting audit/lookdev/sweep and Python adapter | DEFER |
| 219–220 | Dissolve shader and material swap helper | DEFER |

All 50 remain **DEFER**; no final disposition is assigned.

## Findings

### 1. Multiplayer toolkit (171–180)

- `net_audit.gd`, `net_build.gd`, `net_lab.gd`, `net_player.gd`, `net_prop.gd`, `net_session_job.gd` and `net_util.gd` configure/load networked scenes and use Godot multiplayer APIs, ENet and WebSocket transports. This is a networked game test harness, not an agent-to-agent transport or a production tenant messaging service.
- `net_lab.gd` accepts configuration such as role, transport, address, port, authentication mode, password and scene paths. Any adoption requires strict typed configuration, no customer-controlled arbitrary bind address, port or scene path, and a separate network policy.
- Multiplayer authority is a trust boundary. Client-owned state is explicitly described as responsive but trivially cheat-able; server-owned state must be authoritative for gameplay decisions. Validate every RPC sender, peer ownership, payload size/rate, state transition and object reference. Do not trust client-replicated position or other authoritative state.
- `net_boot.gd` writes a result file. Keep results in a run-scoped output directory.
- `gd_net.py` creates subprocesses, uses sockets, creates project clones with `rsync`, starts peer processes, waits with timeouts and manages local network ports. It is a multi-process/network test harness and must never be exposed as an API shell or run in a shared API worker. Bind ephemeral ports, isolate network namespaces, prevent access to internal/control-plane networks, cap peer count and bytes, and terminate all child processes on cancellation.
- These sources should not be imported as MoreAI runtime networking without a separate architecture and threat-model decision.

### 2. Performance and export toolkit (181–189)

- `perf_audit.gd`, `perf_bench.gd`, `perf_fixes.gd`, `perf_stress.gd`, `perf_logger.gd` and `ship_boot.gd` load scenes, generate stress workloads, modify resources/configuration, write performance logs and mount optional DLC packs. Bound entity counts, frame/time duration, GPU/VRAM, artifact size and output paths. DLC `.pck` files must be digest-verified and loaded only from an operator-approved source.
- `web_bridge.gd` uses `JavaScriptBridge.eval` with constructed JavaScript strings for browser-side status/acknowledgement. Current matches are fixed snippets plus serialized text, but any future variable interpolation must use safe JSON serialization and strict size limits; never concatenate untrusted code into eval. Review browser-origin and message-channel boundaries.
- `gd_perf.py` has broad build/export functionality: subprocess calls to native tools (including Java/keytool and export utilities), filesystem writes, a local `http.server.ThreadingHTTPServer` bound to loopback, and Python import-path mutation. Loopback binding alone is not authentication. Do not expose its server on shared hosts; use per-run isolated network namespaces, random ephemeral ports, strict request routing, no directory traversal, no cross-tenant file access, bounded request sizes and automatic shutdown. Signing/keystore operations are privileged: secrets must come from scoped secret injection, never user arguments/logs/artifacts. Fixed command allowlists, timeouts and output limits are mandatory.
- Performance/export tools are build-system capabilities and should remain separate from the FastAPI request lifecycle.

### 3. Asset/pipeline automation (190–209)

- `glb_probe.gd` parses GLB bytes. Treat uploaded GLB as hostile input: enforce file-size, chunk-count, JSON depth, buffer, mesh, accessor, image/texture and decompression limits; reject malformed or unsupported chunk types.
- `prop_audit.gd`, `prop_ingest.gd`, `prop_textures.gd` and `prop_thumbs.gd` read manifests, traverse import folders, load scenes/resources, write manifests and generate thumbnails. The ingest path must be owner-scoped; validate manifest schema and identifiers, reject path traversal/symlink escapes, prevent silent overwrite/deletion, and bound texture resolution, mipmaps, mesh complexity and thumbnail count.
- `prop_rules.gd` provides naming/acceptance policy. Keep policy deterministic and versioned; do not let uploaded metadata override validation rules.
- The editor addon `plugin.gd` and `prop_post_import.gd` run in Godot editor import lifecycle. They are not safe to enable in an arbitrary customer project without isolated editor/worker execution and a reviewed plugin allowlist.
- `godot_ci.sh` invokes Godot headless and gdUnit/GUT test runners and copies reports. It is CI automation, not production runtime. It was not executed in this review.
- `pipeline_ext.c` is a native GDExtension C example. Native code has process-level privileges; compile only from reviewed pinned source in an isolated build worker, scan binary outputs and never load arbitrary customer-provided native extensions into shared services.
- Level importer examples read project source files and install editor plugins. Keep them in sandboxed, disposable projects.
- `gd_pipeline.py` downloads artifacts through `urllib.request.urlopen`, makes subprocess calls, launches processes, writes project files and changes Python import paths. This is a high-risk build/asset ingestion boundary. Use host allowlists, pinned digests, redirect validation, TLS, size/time limits, safe temp files, fixed executable/argument allowlists, no shell, minimal environment, process-tree cleanup and strict workspace confinement. No user-controlled URL, executable, command or Python module path.
- The gdUnit sources (205–209) are test/example code. They remain unexecuted and must not be mistaken for evidence that test suites passed.

### 4. Rendering, lighting and shaders (210–220)

- `grayscale.glsl` uses storage image load/store; `post_effect.gd` loads a shader resource and binds RenderingDevice resources. Restrict shader files to pinned reviewed assets; cap texture dimensions, dispatch/workgroup counts and GPU memory; handle unsupported rendering backends safely.
- `compositor_tools.gd`, `gi_bake.gd`, `light_audit.gd`, `lookdev.gd` and `sweep.gd` load and instantiate scenes, bake GI, capture images and generate variants. Their scene/resource inputs must be resolved through a trusted manifest and outputs confined to the run workspace. GI baking and multi-variant sweeps can exhaust GPU/CPU/memory; impose strict quotas.
- `sweep.gd` accepts variant entries with a `call` pair containing a script path, method name and args, then loads and calls that method. This is a significant dynamic script-dispatch surface. Do not expose this interface to customer input. Replace with a fixed operation registry and typed variant schema; only operator-approved methods should be callable.
- `gd_lighting.py` installs GDScript modules, changes `sys.path` and reads/writes image files. Pin its dependency modules and keep all filesystem operations within the run workspace.
- `dissolve.gdshader` and `dissolve_swap.gd` implement a material effect. Shader source is executable GPU logic: review complexity, loops, texture access and resource limits, and only use pinned/approved shaders. Avoid allowing customers to upload arbitrary shader source for execution in a shared rendering process.

## Cross-cutting controls required before adoption

1. Keep all Godot, native GDExtension, browser bridge, media, rendering and export work out of FastAPI. Use dedicated ephemeral non-root workers pinned by image digest.
2. Do not expose arbitrary shell, executable, script path, method invocation, JavaScript eval, Python import path or native extension loading to customers. Use fixed operation registries and strict Pydantic schemas.
3. Multiplayer harnesses require isolated network namespaces, explicit egress allowlists, blocked metadata/control-plane/private network ranges, peer/rate/payload caps, authentication and server-authoritative state.
4. Local HTTP servers must not be treated as secure merely because they bind to loopback. Isolate network namespace and filesystem, add request authentication, route allowlists, size limits and guaranteed shutdown.
5. Downloads require operator-approved HTTPS hosts, redirect validation, pinned content hashes/signatures, byte/time limits, safe temporary paths and content inspection.
6. Canonicalize all paths and confine reads/writes to owner/run-scoped workspaces. Reject traversal, symlink escapes, absolute host paths and shared-template mutation.
7. Native binaries, shaders, imported scenes, GLB files and project resources are active/untrusted content. Apply parser/resource limits and separate build-time review from runtime approval.
8. Bind jobs/artifacts to authenticated owner, Agent Run, skill version, permission/approval and audit receipt. Preserve idempotency, lease fencing, cancellation, cleanup and owner-checked downloads.
9. Source hashes prove integrity only, not license compliance, security or runtime correctness.

## Status

- Reviewed ledger rows: **171–220 (50 files)**.
- Git blob SHA matched ledger: **50 / 50**.
- Interim dispositions: **50 DEFER; 0 final approvals**.
- Cumulative executable-source files manually reviewed across batches 001–014: **220 / 875 (25.14%)**.
- P1 remains **OPEN**. Next batch: rows **221–270** (50 files). After all 875 executable files, continue configuration/schema, references/dependencies, assets/fonts and SBOM review before final per-file decisions.

