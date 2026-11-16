# P1 File-Content, Dependency-Graph and Integrity Continuation

**Date:** 2026-11-17  
**Branch:** `main`  
**Status:** EVIDENCE UPDATE — P1 NOT CLOSED  
**Scope:** Pinned upstream source tree metadata, representative content review, lockfile reconciliation and selected entrypoint SHA-256. Read-only. No dependency installation, script execution, tests, staging, provider activation, database writes or deployment.

## 1. Repository tree evidence

The recursive Git tree API returned `truncated=false` for all four root repositories.

| Pinned source | Blob files | Directories | Total bytes (tree metadata) | Skill entrypoints |
|---|---:|---:|---:|---:|
| OpenFuse `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | 219 | 32 | 4,345,760 | N/A |
| Scenario Skills `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | 2,114 | 702 | 62,154,351 | 172 product skills |
| Visual Skills `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | 60 | 8 | 676,353 | 2 |
| Motion Skills root `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` | 10 | 2 | 5,174,361 | Child packs |
| Motion Skills 19 pinned child packs | 446 | 195 | Existing pack manifest records all 19 pins | 56 product skills; 55 eligible pending per-file review |

Scenario tree classification by path found 521 files under `references/`, 907 files under `scripts/` or `tools/`, and 318 files under `tests/`. These are path-pattern counts from the recursive tree, not a claim that every file has been content-reviewed. The repository also contains 7 internal maintainer skills under `.agents/skills/`, distinct from the 172 product skill entrypoints.

The Motion child-pack manifests record 641 tree rows: 446 blobs and 195 directories. The 56 skill entrypoints are not all eligible for reuse: `generative-illustration-skills` has no root license and remains excluded/blocked pending rights evidence. The other 18 child pack roots carry identical MIT license blobs.

## 2. Content-level findings from representative files

### 2.1 OpenFuse: substantial engine, server, worker and security material

Pinned root source is MIT. The tree includes Hono server handlers, agent runtime, domain model, engine, durable task worker, Google OAuth, Gmail/calendar actions, search, finance, workspace/files, browser sessions, computer routes, worker proxy/network/download handling, Docker files, tests, docs and a complete pnpm lockfile.

The source README calls the project an alpha and says it runs its own server, task worker and browser worker. Its security policy says:

- one owner per deployment, shared access-key authentication, and no multi-tenant account auth;
- its API stores provider credentials and browser profiles contain private state;
- browser egress checks are application-enforced, not a kernel firewall or hostile-tenant guarantee;
- Playwright disables Chromium's internal sandbox by default;
- the optional E2B desktop mode has internet egress, passwordless sudo, publicly reachable VM ports and an 8-character effective VNC bearer secret; prompt injection can exfiltrate data or submit forms;
- Docker computer mode is single-owner, uses an embedded or optional PostgreSQL store, and is not a hostile-tenant VM guarantee.

The DB implementation supports embedded PGlite when no database URL is supplied, or PostgreSQL when configured. MoreAI must not import that as a second canonical database. The runtime/auth/tenant model, store interface, browser and computer execution boundaries need adaptation to the existing Supabase/Postgres, FastAPI, worker and sandbox contracts. E2B desktop is not acceptable for activation without a separate reviewed security architecture and explicit product approval.

**Required treatment:** preserve the pristine OpenFuse snapshot as governed source evidence; port relevant server/domain/engine/worker/MCP/browser/computer capabilities to MoreAI production modules. Do not deploy its Hono server, mobile frontend, PGlite database or single-owner authentication as parallel product infrastructure.

### 2.2 Scenario Skills: procedures can carry extensive executable payloads

The pinned Scenario root `SKILL.md` declares Streamable HTTP MCP at `https://mcp.scenario.com/mcp`, recommends OAuth, requires explicit `team_id` and `project_id` scope on calls, and distinguishes direct MCP tools from catalog-executor tools. It includes model discovery/schema, generation, uploads, job waits, asset handling, memory, team/project scope, quota/usage, and error recovery. It requires cost estimates for billable work unless the user says cost does not matter, and warns against retrying uncertain paid actions.

The inspected product skills show that a `SKILL.md` is only the entrypoint:

- `scenario-image` routes to sibling model skills and multiple reference files.
- `scenario-video` uses the Scenario generation/job/asset lifecycle.
- `scenario-workflows` exposes workflow list/get/run/approval/reject paths.
- `scenario-workflow-authoring` references local editor docs and a Python workflow-example script.
- `scenario-kinetic-film` has 36 local references, scripts, npm package/lock files, Python requirements, a local JS engine and examples.
- `scenario-kinetic-music-video` has 48 local references, Python/Node scripts, platform-specific Python requirement files, a Swift matte helper and a local engine.
- Blender, Godot and Roblox expert skills rely on local application installations, application-specific bridges/MCP and scripts; they are not generic server-only SaaS skills.

**Required treatment:** the full selected folder must include its references, scripts, engine, fixtures, tests, manifests, and required runtime files. The Skill Registry must capture sibling-skill dependencies and capability requirements. Scenario's remote service internals are not contained in this repository; implement a MoreAI provider adapter for the documented MCP contract instead of claiming those private services were copied. Scope, OAuth, budget, approval, metering, timeout, cancellation and job reconciliation must be enforced by MoreAI.

### 2.3 Visual Skills: CC BY 4.0 attribution and model-provider distinction

The root license is CC BY 4.0. `NOTICE` requires attribution to Serge Shima and identifies methods adapted after studying `agentara/skills` (MIT). The NOTICE must accompany copied/derivative content. The README credits logo assets from lobe-icons (MIT), but that upstream license does not establish trademark rights in each model/provider mark. Existing logo/asset deferrals remain valid.

The two skill entrypoints are prompt-writing workflows, not image/video inference engines. Their model-specific references, task references and visual prompt checks are required supporting content. The underlying image/video model engines are external providers and must route through MoreAI's approved gateway and provider adapters.

**Required treatment:** preserve the complete `image/` and `video/` trees with CC BY attribution. Continue excluding/defering provider logos and any asset without provenance/redistribution clearance.

### 2.4 Motion Skills: scripts and engines are first-class payload

The 19 child-pack manifests contain scripts, render helpers, examples, references, tests, lockfiles and assets in addition to 56 entrypoints. The 18 eligible child pack roots use the same MIT license blob; `generative-illustration-skills` remains blocked because no root license was found.

A content inspection of `talking-head-skills` found a real provider module: it calls ElevenLabs voice cloning and speech-to-text APIs, calls Fal.ai queue submission/status/result endpoints, uploads files through the Fal SDK, and downloads generated outputs. It requires `FAL_KEY`/ `FAL_API_KEY` and `ELEVENLABS_API_KEY` from the environment. Its error handling explicitly avoids automatic repeat of paid requests. Its lockfile pins `@fal-ai/client@1.10.1`, `@napi-rs/canvas@1.0.13` and transitive dependencies.

**Required treatment:** import the full eligible pack payload, including render scripts and local engines where legally reusable. Adapt provider code behind MoreAI's shared connection registry, secret vault, gateway, credit metering and durable media-job lifecycle. Never expose API keys to customer browser code or activate paid generation during governance.

## 3. Dependency graph reconciliation

The exact pinned lockfiles were fetched and parsed without installing packages.

| Lockfile | Importers | Package entries | Snapshot entries | Direct specifiers | Integrity records | License fields in lockfile |
|---|---:|---:|---:|---:|---:|---:|
| OpenFuse pnpm lock v9 | 3 | 1,890 | 2,532 | 55 | 1,452 | 0 |
| Scenario pnpm lock v9 | 1 | 533 | 659 | 11 | 466 | 0 |
| Motion talking-head pnpm lock v9 | 1 | 16 | 18 | 2 | 16 | 0 |

The lockfiles establish package versions, importer contexts, peer/snapshot relationships and integrity values, but do not provide package license metadata. A lockfile integrity hash is not a license attestation.

The previous CycloneDX SBOM reported 1,524 OpenFuse pnpm PURLs and 479 Scenario pnpm PURLs, while this exact lockfile parse found 1,890 and 533 package entries respectively. The differences are 366 OpenFuse entries and 54 Scenario entries and must be reconciled at package-coordinate/importer level before the SBOM can be accepted as complete. Motion talking-head's 16 PURLs match its 16 package entries.

The prior SBOM contained 2,032 unique components and 2,026 `NOASSERTION` license values. The historical OpenFuse audit's 1,793 `package@version` unresolved coordinates are a narrower prior scope, not an alternative total. All counts remain open until deduplicated against exact package coordinates and source/importer provenance.

MoreAI root `package.json` uses version ranges and has no root lockfile in the prior repository audit. API and worker `pyproject.toml` files declare pinned direct dependencies but no checked-in Python lock was found. OpenManusWeb's pinned `requirements.txt` has unpinned/ranged dependencies. Do not resolve these by installing packages in this no-test/no-staging task. Registry license reconciliation must use exact package versions and authoritative metadata; unknown values remain `NOASSERTION`.

## 4. Raw SHA-256 evidence

A new manifest has been committed:

`docs/implementation/MOREAI_P1_SKILL_ENTRYPOINT_SHA256_20261117.csv`

It contains 67 selected skill entrypoints:
- 10 representative Scenario entrypoints covering core MCP, image/video, workflows, local motion engines, Blender, Godot and Roblox;
- 55 eligible Motion Skills entrypoints; the unlicensed generative-illustration entrypoint is not included;
- 2 Visual Skills entrypoints.

For every row, raw UTF-8 byte length and SHA-256 were computed from the fetched blob content. Git blob SHA remains a separate field. This is not yet the complete selected-payload hash set: supporting references, scripts, engine files, manifests, fixtures, tests and assets still need final disposition and SHA-256 before import.

The prior 34-row raw manifest remains the additional integrity evidence for upstream licenses, notices and selected dependency files.

## 5. Current disposition decisions and holds

The existing 3,919-row source-to-target register is still marked preliminary. This continuation does not silently convert it to final decisions.

Confirmed direction:
- OpenManusWeb: pristine complete source snapshot plus backend capability parity port.
- OpenFuse: preserve source snapshot; adapt relevant backend/runtime code to FastAPI/worker/sandbox; archive competing mobile UI; exclude second runtime/database and single-owner auth from product runtime.
- Scenario: preserve candidate complete skill folders and all supporting files; adapt provider access through a secure MCP adapter; classify local-application-only capabilities separately from hosted worker capabilities.
- Visual: copy/adapt the two complete skill trees with required CC BY attribution; defer logos/assets lacking independent rights evidence.
- Motion: copy/adapt the 55 eligible skill payloads and supporting engines/scripts after file-level review; exclude the unlicensed generative-illustration pack until licensing is established; build shared provider adapters for iArt/Fal.ai/ElevenLabs rather than a new per-skill secret/billing system.
- No credentials, provider endpoints or remote generation were activated.

Still required before P1 closure:
1. Content-review every selected file and resolve every local reference/import/script/asset edge.
2. Inspect every nested license/notice and third-party asset provenance in all selected trees.
3. Reconcile every SBOM package coordinate to lockfile importer/snapshot and exact-version registry license metadata.
4. Complete raw SHA-256 for every final copy/adapt file, including references, scripts, engines, manifests, fixtures, tests and assets.
5. Finalize every file's disposition and rationale in the 3,919-row register; retain explicit blocked/excluded reasons.
6. Update the P1 tracker and submit P2 ADR for acceptance only after these artifacts are complete.

## 6. Execution boundary and phase position

No packages were installed. No scripts, builds, lint, type checks or tests were run. No external provider, OAuth, MCP service or paid API was activated. No Supabase write, migration, RLS change, staging or deployment was performed. No customer UI files were changed.

P1 Source Governance remains **IN PROGRESS**. P2 ADR remains **DRAFT / NOT ACCEPTED**. Mandatory Phase 04, 06, 07, 08 and 09 remain in progress. Phase 09 remains a prerequisite to Phase 10. With real tests and staging prohibited, Phase 10 and Phase 11 cannot be marked accepted or passed.

**Next action:** finish the file-level content/reference/license and exact package-license reconciliation, then hash every final copy/adapt file and close P1. Only then finalize/accept P2 and proceed through Phase 04–09.


## Corrective lockfile section recount — 2026-11-17

This addendum supersedes the earlier paragraph in section 3 that described 1,890 OpenFuse package entries / 2,532 snapshots and 533 Scenario package entries / 659 snapshots. Those figures were produced by an over-inclusive key parser and must not be used as lockfile section totals.

Both pinned pnpm v9 lockfiles were fetched again from their exact immutable commits and recounted using only first-level mapping keys within the `packages:` and `snapshots:` sections. Integrity values were counted independently. No package installation or script execution was performed.

| Pinned lockfile | Package-section keys | SHA integrity records | Snapshot-section keys | Snapshot dependency declaration lines* |
|---|---:|---:|---:|---:|
| OpenFuse `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | 1,455 | 1,452 | 2,341 | 3,978 |
| Scenario Skills `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | 467 | 466 | 693 | 730 |

The package-key vs integrity-record delta is 3 for OpenFuse and 1 for Scenario. The integrity-record counts agree with the previously corrected SBOM exact package-coordinate counts (1,452 and 466 respectively). This is a useful reconciliation signal, but not a complete dependency graph acceptance: the remaining package keys must be classified explicitly, and snapshot dependency declarations still need normalized package-coordinate resolution including peer-context suffixes, optional dependencies, platform conditions, and workspace/importer scope.

*The dependency declaration line totals are raw structural counts of child mapping lines in the snapshot section, not deduplicated graph-edge counts. They must not be represented as a resolved edge total or used to infer installability.

### Corrected interpretation

1. The earlier 1,890 / 533 package-entry figures and 2,532 / 659 snapshot figures are withdrawn as incorrect parser output.
2. The currently supported exact package-coordinate counts for the two pnpm lockfiles remain OpenFuse 1,452 and Scenario 466, matching the corrected SBOM records previously documented.
3. This recount does not resolve the historical 1,793 OpenFuse `NOASSERTION` baseline against the expanded full-source SBOM, nor does it establish exact-version registry license expressions.
4. The 1,989 `NOASSERTION` figure in the expanded SBOM remains a license-evidence status, not a count of missing lockfile entries. Registry metadata and package artifact/NOTICE review remain open for every exact package version.
5. Do not use the stale counts elsewhere in P1 reports as accepted evidence. Update dependent summaries when their next controlled revision is made.

**P1 remains OPEN.** The next dependency-graph deliverable must be a normalized importer → snapshot → package-coordinate edge export with peer contexts retained, followed by authoritative exact-version license/NOTICE evidence. Unknown or inaccessible metadata remains `NOASSERTION`; it must never be inferred from package names.
