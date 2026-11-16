# P1 pnpm graph audit utility

This utility is an auditable, non-installing parser for pinned pnpm v9 lockfiles. It emits exact package coordinate rows, importer/snapshot dependency declarations, conservative resolution statuses, and optional exact-version npm registry license metadata. It does not run package scripts or install source dependencies.

Install the isolated audit-only dependency with `python -m pip install -r scripts/p1/requirements.txt`, then run:

```sh
python scripts/p1/normalize_pnpm_lock_graph.py \
  --source openfuse=PATH_TO_PINNED_OPENFUSE/pnpm-lock.yaml \
  --source scenario=PATH_TO_PINNED_SCENARIO/pnpm-lock.yaml \
  --out-dir artifacts/p1-lock-graph
```

Add `--registry-metadata` to query `registry.npmjs.org` for each exact package name/version. Keep the resulting raw metadata and outputs as evidence; an absent or non-SPDX registry field remains `NOASSERTION` and requires artifact/NOTICE inspection. This registry pass is not a vulnerability scan or legal approval.

Resolution deliberately reports ambiguous peer contexts, aliases and non-registry protocols instead of guessing. Review those rows before treating the graph as closed. Lockfiles must be the exact immutable source revisions documented in the P1 source pin manifest.
