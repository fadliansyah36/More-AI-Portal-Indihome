# Raw-content SHA-256 evidence manifest — 2026-11-17

This manifest records **34 exact source files** whose GitHub blob JSON was fetched by immutable Git blob SHA. Base64 content was decoded and SHA-256 was computed over the exact decoded bytes. The decoded byte count matched GitHub's blob `size` for every row.

This is a selected integrity set, not a claim that all 3,919 tree entries or all selected skill package files have been SHA-256 hashed. The 18 Motion child-pack root LICENSE files share the same Git blob SHA and identical 1,064-byte content; each repository is listed separately to preserve provenance.

The OpenManusWeb 111-file vendor snapshot has a separate existing source/destination Git blob parity report (111/111). Skill ingestion code independently requires per-file SHA-256 and Git blob SHA checks before a skill can validate/publish. The remaining 230 product skill entrypoints and their selected reference/script/assets files still require exact raw-content SHA-256 as packages are individually selected for ingestion.

See `MOREAI_P1_RAW_SHA256_MANIFEST_20261117.csv` for per-file evidence. Do not infer SHA-256 from Git blob SHA.
