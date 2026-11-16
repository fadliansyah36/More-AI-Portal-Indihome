# Source-to-Target Disposition Register — 2026-11-17

This is a **preliminary path-based classification** generated from all pinned recursive trees. It is not the final per-file legal/security approval: source content review, nested dependency/license checks and exact implementation mapping are still required. The register includes directories and files to preserve tree completeness.

- Main source trees: 3,278 entries.
- Motion Skills 19-pack trees: 641 entries.
- Total registered entries: 3919.
- Preliminary decisions: {"copy":135,"archive-only":1813,"adapt":953,"exclude":54,"defer":964}.
- Every row is explicitly marked `PRELIMINARY_NOT_FINAL`.

Rules:
- OpenManusWeb: preserve the complete pristine vendor snapshot as mandated by AGENTS.md; its existing source manifest reports 111/111 matching Git blob SHA.
- OpenFuse: adapt server/worker/computer/backend modules into FastAPI/worker/engine; exclude its competing mobile UI; archive docs/assets/configs. Do not run OpenFuse as a second runtime.
- Visual Skills: adapt SKILL.md and markdown references only after retaining CC BY 4.0 attribution; archive demonstration assets.
- Scenario Skills: adapt skill instructions/references; defer executable scripts/assets until security/license review; archive tests/evidence.
- Motion Skills: adapt skill instructions/references; defer scripts to isolated renderer workers; archive showcase/example assets; preserve each pack's own MIT notice.
- Missing root license on generative-illustration-skills remains a hard block; its paths are marked archive-only pending permission, not authorized for reuse.

The CSV is the row-level source of truth for path, source commit, Git blob SHA, byte size, provisional decision, target and reason. SHA-256 raw-content hashes remain pending and must not be inferred from Git blob SHA.
