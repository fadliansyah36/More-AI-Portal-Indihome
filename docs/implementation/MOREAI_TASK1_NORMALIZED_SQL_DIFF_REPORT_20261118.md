# Task 1 — Normalized SQL Diff & Semantic Classification
Date: 2026-11-18

## Normalization contract
The analytical normalizer is a lexical SQL tokenizer, not an AST parser:
- Drops whitespace and SQL comments outside quoted tokens.
- Preserves single-quoted literals and double-quoted identifiers verbatim.
- Preserves operators, punctuation, numeric tokens and statement ordering.
- Treats dollar-quoted PL/pgSQL bodies as SQL text and tokenizes their content recursively, so formatting inside function bodies does not cause false mismatches.
- Does not rewrite, reformat or replace either original source.

## 23-pair result
- Raw SQL equality: 0/23.
- Ordered lexical-token equality on the original same-name pair: 21/23.
- Additional semantic equivalence despite token difference: 1/23 (grant consolidation in `20261114040000`).
- Source identity unresolved: 1/23 (`20261115090000` is an exact content duplicate of the later attachment-compat source and not the source for applied history `20261115084819`).

## Classification breakdown
| Classification | Count | Rationale |
|---|---:|---|
| FORMAT_ONLY | 18 | Ordered SQL token streams are identical; only formatting/line wrapping differs |
| COMMENT_ONLY | 3 | SQL tokens identical; repository adds explanatory comments/blank lines |
| FORMAT_ONLY — equivalent GRANT consolidation | 1 | Same privilege set and grantee; statement grouping differs |
| FUNCTION_OR_TRIGGER_CHANGE + SOURCE_IDENTITY_UNVERIFIED | 1 | The same-name history row is a different historical step; repository file matches another applied migration instead |

## Corrected notable findings
1. `20261114040000_moreai_customer_agent_configuration_capability_registry.sql`: the history grants SELECT separately from INSERT/UPDATE; repository combines these privileges into one GRANT. Same relation, same grantee, same effective privilege set. No permission widening/narrowing.
2. `20261115090000_moreai_agent_model_preferences.sql`: repository Git blob SHA `86c53087c128b6a867bc462f4b3671ad716ea048` is byte-identical to `20261115100000_moreai_agent_model_preferences_attachment_compat.sql`. Its raw MD5 `561ec2dfb21f2e7d74ad4a8ebf0ea4d5` exactly matches applied history `20261115085314`. It does not match applied history `20261115084819` (MD5 `9f5254d8a2749d42f512de381d22b68c`), which contains the preferred_model_id column and index creation. The original 15084819 SQL is still a source-identity gap.
3. `20261115111000_moreai_provider_endpoint_allowlist.sql`: earlier claims of a behavior delta are withdrawn. SQL token streams match; allowlist checks are already present in the historical statement.

## Risk and impact
- 22 normalized/equivalent pairs: no demonstrated schema, data, constraint, index, function, trigger, RLS, grant, execution or compatibility change.
- 15090000 source-identity gap: HIGH provenance risk because a same-name file is a duplicate of a later migration and the original applied 15084819 source is not represented by a distinct repository file. The live database confirms the preferred_model_id column and partial index exist, but source replay parity cannot be inferred from that fact.
- No migration or database changes are authorized by this report.
