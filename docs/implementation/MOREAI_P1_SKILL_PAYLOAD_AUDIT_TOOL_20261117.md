# Read-only P1 Skill Payload Audit Utility

## Inputs
Use the pinned source manifests and selected entrypoint register committed under docs/implementation/:
- MOREAI_P1_SELECTED_SKILL_ENTRYPOINTS_20261117.csv
- MOREAI_P1_RECURSIVE_SOURCE_TREE_MANIFEST_20261117.csv
- MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_20261117.csv
- MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_PART2_20261117.csv

## Invocation
From the repository root, with Python 3.11+ and outbound HTTPS to GitHub permitted:

    python scripts/p1/audit_skill_payloads.py \
      --selected-entrypoints docs/implementation/MOREAI_P1_SELECTED_SKILL_ENTRYPOINTS_20261117.csv \
      --primary-manifest docs/implementation/MOREAI_P1_RECURSIVE_SOURCE_TREE_MANIFEST_20261117.csv \
      --motion-manifest docs/implementation/MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_20261117.csv \
      --motion-manifest-part2 docs/implementation/MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_PART2_20261117.csv \
      --out-dir .audit/p1-skill-payloads

The command is a read-only source audit, not a test or staging action. It fetches exact pinned raw bytes and writes three local evidence files:
- skill-payload-file-audit.csv
- skill-reference-audit.csv
- skill-payload-audit-summary.json

It does not run source code, install packages, activate providers, access Supabase, or change production data. Review fetch failures and unresolved references; a successful hash is not legal approval or safe-to-execute status. Commit generated outputs only after reviewing contents and confirming no secrets or unrelated user data are included.

## Current execution status
The utility is committed but has **not** been run. No test, build, staging, provider activation, migration, Supabase write or deployment was performed.