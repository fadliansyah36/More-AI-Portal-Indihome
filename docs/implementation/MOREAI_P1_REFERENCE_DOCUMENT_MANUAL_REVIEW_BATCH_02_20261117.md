# P1 Reference Document Manual Review — Batch 02

Date: 2026-11-17  
Branch: `main`  
Scope: 10 additional reference/maintainer documents from pinned Visual Skills and Scenario Skills.  
Method: read-only full-text review at immutable source commits. No Maya/Godot/Roblox application, MCP server, provider, package, model or media workflow was executed.

## Reviewed references

| # | Document | Findings | Decision |
|---:|---|---|---|
| 1 | Scenario Maya `references/maya-2027-traps.md` | Documents version-specific Maya 2027 behavior, multiple items marked `[verify]`, and local installation of packages via `mayapy -m pip install --target ~/Library/Preferences/Autodesk/...`. It also describes ML Deformer downloading PyTorch into the local Maya application directory. | **DEFER** — version-specific workstation guidance; do not install packages into MoreAI API/worker images or trust unverified items without isolated Maya version verification. |
| 2 | Scenario Godot `references/sources.md` | Explicitly marks multiple contributor credentials unverified and cites third-party videos, Godot MCP implementations, Godot docs and GUT. It records a source research window and author-run test claims. | **DEFER** — preserve unverified labels; external source review and current official docs required. No MCP package or tool is approved by this document. |
| 3 | Scenario Roblox `references/sources.md` | Contains official Roblox documentation and third-party YouTube/community sources, with several contributor credentials marked unverified. Includes Open Cloud, Studio MCP, CLI, publishing and CI references. | **DEFER** — keep unverified attributions explicit; any live publishing or Open Cloud action needs separately reviewed customer credentials and approval. |
| 4 | Scenario Kinetic Film `README.md` | Maintainer notes disclose open algorithmic issues in beat-grid/downbeat detection, synthetic-only verification for several paths, opt-in network font downloads and a Scenario MCP-generated author example. The author notes the real MCP-generated assets do not ship. | **DEFER** — not a validated end-to-end production workflow. Preserve known open issues and synthetic-only evidence; do not use the sample as quality/SLA proof. |
| 5 | Scenario Kinetic Music Video `README.md` | Supply-chain notes describe platform-specific wheel locks and hashes, but also disclose Demucs checkpoint download checked only by a short hash prefix followed by unpickling; Whisper model content verification was not checked; Demucs source build failed on Linux ARM64; and external tools (uv, Node, ffmpeg, Chrome, swiftc) are assumed. | **DEFER** — model artifact integrity is insufficient for untrusted checkpoints. Require full SHA-256/signature provenance, safe model formats (no untrusted pickle), pinned container toolchain and explicit platform support before execution. |
| 6 | Scenario Playable Ads `README.md` | Maintainer notes describe a synthetic asset inventory and state that a playable was not built end-to-end from a studio's files with the current version. | **DEFER** — retain as maintainer context only; do not claim customer-ready or end-to-end validation. |
| 7 | Visual Skills `image/references/gpt-image.md` | Contains model IDs and capability/latency claims for named GPT Image 2.5 variants and detailed prompt rules. The footer identifies Serge Shima, CC BY 4.0 and source repo. This is a third-party skill reference, not authoritative OpenAI API model availability evidence. | **DEFER** — attribution required; validate every model ID, provider capability and pricing against current official API docs before mapping to MoreAI model router. |
| 8 | Visual Skills `image/references/nano-banana.md` | Provider-specific model-tier and prompt recommendations; footer identifies Serge Shima, CC BY 4.0 and source repo. | **DEFER** — attribution required; validate model IDs, terms, data handling and availability against the actual provider before enabling. |
| 9 | Visual Skills `video/references/seedance.md` | ByteDance/Seedance prompt syntax and production advice; author/source footer identifies CC BY 4.0. It is descriptive prompting guidance, not a verified API contract. | **DEFER** — preserve attribution and separately verify provider contract, input/output limits and upload handling. |
| 10 | Visual Skills `video/references/veo.md` | Google Veo prompting/reference-image guidance with CC BY 4.0 attribution. | **DEFER** — preserve attribution; validate model/version and official API terms before implementation. |

## Newly identified Motion dependency-lock scope

The Kinetic Music Video maintainer notes revealed two large platform-specific Python lock files that were classified as reference documents by the payload scanner:
- `assets/python/linux-x86_64.txt`: 100 exact package coordinates.
- `assets/python/macos-arm64.txt`: 83 exact package coordinates.
- 104 unique package@version coordinates across both platform locks (79 shared exact coordinates).
- 3,660 SHA-256 wheel hash entries.
- 306 dependency edges reconstructed from lockfile reverse-dependency comments and direct requirements.
- `assets/python/requirements.in`: 13 direct requirements, several intentionally unpinned; the two platform locks resolve them separately.

Machine-readable package and edge evidence:
- `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_PACKAGES_20261117.csv`
- `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_EDGES_20261117.csv`

Important compatibility/security findings:
- Linux x86_64 includes CUDA/NVIDIA runtime packages and Triton; do not install this entire lock into a CPU-only/shared worker image by default.
- `av` and `onnxruntime` versions differ between Linux and macOS locks; platform selection must be explicit.
- No Linux ARM64 lock exists; the maintainer notes a Demucs source build failed because the `sphn` wheel was unavailable and a Rust source build was fetched/failed.
- Demucs checkpoint is downloaded from an external host, checked only against a short hash prefix, then unpickled. This is not acceptable for untrusted model artifacts.
- Whisper model is pinned to a Hugging Face commit, but content verification was not confirmed by the upstream maintainer.
- The lock files contain SHA-256 hashes for wheels and use binary-only installs; this is a positive supply-chain control but does not replace registry license/vulnerability review, model provenance or immutable container toolchain.

The nested Python locks were absent from the previous BOM input list. They are now represented in the package/edge CSVs but still require registry license and vulnerability evidence, source+PURL de-duplication against CycloneDX, and model artifact provenance review.

## Coverage and disposition

- Manual reference/maintainer documents reviewed in this batch: **10/726** (10 unique paths; Veo was already covered in Batch 01 and is not counted again).
- Cumulative reference document manual review: **17/726**.
- Remaining reference documents: **709/726**.
- All ten reviewed documents remain **DEFER**.
- This review does not convert author-reported tests or synthetic demonstrations into MoreAI test evidence.

No source, model, package, workflow, application, provider, Supabase object or migration was executed or modified. No tests, builds, staging or deployment were run.

**P1 remains OPEN.**
