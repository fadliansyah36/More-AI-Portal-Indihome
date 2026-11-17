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

## Selected skill entrypoint inventory update — 2026-11-17

A 229-entry eligible product-skill register is now committed. It contains 2 Visual Skills entrypoints, 172 Scenario Skills entrypoints and 55 eligible Motion Skills entrypoints. The remaining Motion pack, `generative-illustration-skills`, is excluded from this eligible register because its root license is missing.

The register is preliminary source scope only. It does not supersede the preliminary 3,919-row disposition register and does not constitute final per-file legal, security or content approval. P1 remains OPEN until each selected skill folder and its recursively referenced files are reviewed, hashed and assigned a final disposition.


## Selected skill folder-level row register — 2026-11-17

A dedicated row-level register has been added for the 229 eligible skill entrypoints and all files under their selected folders: MOREAI_P1_SELECTED_SKILL_PAYLOAD_MANIFEST_20261117.csv. It contains 1,923 unique payload paths / 26,586,168 bytes, each with exact source repository, commit, path, Git blob SHA, expected byte size, content class, preliminary disposition and review reason.

Proposed disposition split: 952 adapt (SKILL.md and reference documents) and 971 defer (898 executable files, 67 config/schema files, 6 font/media assets). These are conservative proposals, not final decisions. The existing 3,919-row all-source-tree register remains the broader provenance inventory and still has PRELIMINARY_NOT_FINAL decisions.

25 root/nested license/notice paths have separately verified raw SHA-256; the payload manifest SHA-256 fields remain pending. A binary-safe recursive auditor is committed but not run.


## Manual reference triage status — 2026-11-17

The committed 1,941-file recursive payload audit's 148 parser reference candidates are now triaged in `MOREAI_P1_MANUAL_REFERENCE_TRIAGE_20261117.md`: 49 heading fragments match existing headings, 78 targets resolve to existing directories, and 21 are contextual/generated/runtime/example references. This corrects the earlier coarse residual estimate of 25 for this exact CSV. No parser candidate in this set is approved for code execution or production import solely by this triage.

The 229-entrypoint content review remains partial (16 reviewed); executable/configuration, font/binary provenance, package tarball notices, vulnerability evidence and final per-file decisions remain open. The 3,919-entry source register and 1,941-file selected payload register remain `PRELIMINARY_NOT_FINAL`; P1 has not been accepted.


## Selected payload disposition supersession — 2026-11-17

The selected 1,941-file payload scope now has a separate row-level operational register: `MOREAI_P1_SELECTED_PAYLOAD_FINAL_OPERATIONAL_DISPOSITION_20261117.csv`. This register supersedes the earlier 1,941-row selected-payload proposals described above. It records **15 ARCHIVE_ONLY** (10 media/binary + 5 test/example fixtures) and **1,926 DEFER**. The 23 manually reviewed executable files include review evidence and remain DEFER for isolated-runtime/provider/action-boundary reasons. All other files remain DEFER pending individual content, provenance, license, security and target-module review. No COPY/ADAPT promotion is approved yet.

The broader 3,919-entry all-source-tree register remains preliminary; the selected-payload register does not silently replace it. The historical CSV path `MOREAI_P1_SOURCE_TO_TARGET_DISPOSITION_20261117.csv` is empty in the current repository tree and must not be cited as an available row-level register. The next task is to regenerate a complete 3,919-entry source-tree ledger from the pinned recursive manifests and apply reviewed decisions without inferring legal approval from file type.

P1 remains OPEN. No source was executed, installed, tested, staged, deployed or imported into Supabase.
