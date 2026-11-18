# Migration provenance — 20261115084819

Date: 2026-11-18. Scope: read-only Git/history comparison. No migration, DDL, DB write, staging, testing or deployment.

## Finding

Status: **SOURCE_CONFIRMED / PROVENANCE_PARTIAL**.

Supabase history contains version `20261115084819`, name `moreai_agent_model_preferences`, one SQL statement, 3,480 bytes, MD5 `9f5254d8a2749d42f512de381d22b68c`, SHA-256 `40c4a5081052cca21b287fc7e0797676eabda86ef72e584e2bf9a45dc2855320`. The history row is confirmed by a read-only query to `supabase_migrations.schema_migrations`. This confirms a history record, not independent execution attestation.

The historical SQL source is present in Git history at commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`, path `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql`, blob `b7278df23425678a3009cb5c15f20e7c6cf53327` (4,108 characters; source commit timestamp 2026-11-15 15:48:10 +07:00 from GitHub commit search). A recursive SQL lexical tokenizer that enters dollar-quoted PL/pgSQL bodies found 619/619 ordered tokens identical between this Git source and the SQL stored in migration history. Comments/whitespace differ; no token, literal, identifier, operator, punctuation or statement-order difference was detected. This is stronger than a filename-only match but is not an AST or runtime proof.

## Provenance chain

1. **Original Git source representation:** commit `cc5563e...`, path named `20261115090000`; Git blob `b7278df...`. Commit diff introduces the preferred_model_id column, partial index and 6-argument enqueue function.
2. **Applied-history representation:** version `20261115084819`, logical name `moreai_agent_model_preferences`; stored SQL hash above. 619 ordered lexical tokens match the Git source.
3. **Current repository representation:** `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql` on main now has blob `86c53087c128b6a867bc462f4b3671ad716ea048`, 5,956 bytes. It is byte-identical to `20261115100000_moreai_agent_model_preferences_attachment_compat.sql`, and matches applied history `20261115085314`, not 15084819.
4. **Reconciliation evidence:** the existing 23-pair exact diff report previously classified the wrong same-name pairing as `SOURCE_IDENTITY_UNVERIFIED`. That classification is now superseded for source recovery: Git history recovers the original SQL representation. The current main file remains a duplicate/misnamed alias and must not be relabelled as the 15084819 source.

## SQL summary and identity

The recovered source adds `preferred_model_id uuid references public.llm_models(id) on delete set null`, a partial index for non-null model IDs, and replaces `moreai_enqueue_chat_run_with_config(uuid,uuid,text,text,text,uuid)` to snapshot the preferred model and enforce that the selected model/provider are enabled. It revokes client execution and grants execution to service_role. Historical and Git source are lexically equivalent after formatting/comment normalization.

Raw hashes intentionally differ because the stored history representation is more compact. No native checksum column exists in Supabase migration history; the MD5/SHA-256 are reconstructed audit hashes, not platform execution checksums.

## Decision

- Source of record for the applied-history SQL: the SQL text stored in history version 15084819, cross-identified to Git commit `cc5563e...` by exact ordered lexical-token equivalence.
- Canonical audit reference: this report + source inventory/hash comparison + commit URL `https://github.com/fadliansyah36/More-AI-Portal-Indihome/commit/cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`.
- Status: `HISTORY_RECORD_CONFIRMED`, `SOURCE_CONFIRMED`, `PROVENANCE_PARTIAL`; not `PROVENANCE_CONFIRMED` because migration history has no native source checksum/execution receipt, the Git filename version (15090000) differs from history version (15084819), and the commit's relation to the actual deployment pipeline is not independently attested.
- Preserve the original commit object and history row. Do not overwrite/delete the current duplicate files or create a replacement migration. Owner-approved disposition is still required for the duplicate/misnamed current path.
- No evidence supports applying, replaying, renaming or editing any migration as part of this audit.
