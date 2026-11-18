# Task 1 — Exact SQL Diff Report
Date: 2026-11-18
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main
Supabase: uunfgimtokhucegqbpce
Read-only audit only. No DDL, migration apply, DB write, staging, tests or deployment.

## Method and provenance
- Historical side: exact `statements[1]` value read from `supabase_migrations.schema_migrations` using the applied version in the mismatch register.
- Repository side: exact SQL file from branch `main`.
- Raw identity: repository Git blob SHA plus raw SQL MD5 for both sides. Raw content differs for every row in this same-name mismatch set.
- Exact line-level comparison: original line endings/content retained; differences were compared without modifying either source.
- Normalized analysis: separate SQL lexical-token comparison; it removes comments and whitespace outside quoted strings/identifiers and tokenizes dollar-quoted PL/pgSQL bodies as SQL text. It preserves literals, identifiers, operators, punctuation and statement order. This is not a SQL AST/parser or a proof of runtime behavior.
- Historical migration history has no native checksum column; MD5s are reconstructed audit checksums, not Supabase execution checksums.

## Pair inventory and exact source references

| Repo migration | Applied history version | Repo Git blob SHA | Repo raw MD5 | Applied raw MD5 | Semantic disposition | Decision |
|---|---|---|---|---|---|---|
| `20261111050000` moreai_tool_approval_lifecycle | `20261111061443` | `54a27f0a32404ef73e2e463c1b16d820bd771228` | `df27086c86dbcdbcd7e9878e0c69385e` | `981cf360e0350d54ddf10d4fd11f8806` | FORMAT_ONLY | RESOLVED |
| `20261111103000` moreai_admin_partner_status_atomic_audit | `20261111083342` | `c366008f7f8bef7bf0b26232a163db08a8ccefb2` | `63c897cf6c048f3f0380f423640b57b9` | `34efd4fc40eee99c860714f4e64c1f1a` | FORMAT_ONLY | RESOLVED |
| `20261111120000` moreai_explicit_server_only_rls_denials | `20261111112556` | `bb5bf6bcc11bc29910b90b25b4c1cd38d95d1b71` | `790f9a1c52ef12b55f88cf051e568802` | `3f7b7efec24c5cd390b55fc486bc510a` | FORMAT_ONLY | RESOLVED |
| `20261111180000` moreai_openmanus_approval_tool_keys | `20261111160343` | `c1e1435f7f2f76bc18b3e1ae8306bdd8a6943840` | `35ffd4ac45f107a681b96b9b8239f452` | `5c29f9f5c26b623ce31812a3d44c7eb8` | FORMAT_ONLY | RESOLVED |
| `20261112084047` moreai_auth_profile_provisioning_and_owner_update | `20261112084047` | `b916fd7dd49ce4bda67a23fa9cc0d7f7dfae97c6` | `ea05b2e6c2b8fe8b73c1e0d2b6970536` | `8ca5de3c3f4ca16f46888b5685f3646b` | FORMAT_ONLY | RESOLVED |
| `20261113160000` moreai_customer_workspace_union_pagination | `20261113132826` | `5a4f337687dfbc24832c1d395aa410f03c59615e` | `1104220c5fe4b4db4daa8351502d563a` | `bbaba61263405295e1ecea4a6491e300` | FORMAT_ONLY | RESOLVED |
| `20261113170000` moreai_customer_workspace_file_lifecycle | `20261113133149` | `0278942b405b9f6ad3b9a230ca08521d3be4ee37` | `b486384b6208df8fb925d150320a4349` | `c597a121c4436ff227795b1284e69507` | FORMAT_ONLY | RESOLVED |
| `20261113180000` moreai_customer_workspace_pagination_indexes | `20261113133346` | `15c5bd0bc6d475f2cf1991ebcc61ea771e3dd257` | `4ad369edfedfed3ff0175ffba1c9c245` | `de0391931d2c7943eb7baae2cc076075` | COMMENT_ONLY | RESOLVED |
| `20261113190000` moreai_customer_workspace_restore_immutable_version | `20261113133453` | `9740a410506331916b5527c727765b661b78f625` | `0f81b845978803a1aa0ace41a148bb6a` | `6b0b0fb2024fcb7f3c3d8365c2d5a38b` | FORMAT_ONLY | RESOLVED |
| `20261113200000` moreai_customer_workspace_delete_version_archive | `20261113133519` | `498794d75e0f6de1a0d75ca0d40524035c7cbffb` | `b8b59afbbc7efa8781c4c97bc669deae` | `1494683083c9c4cbeb6fb2945ec21cb4` | FORMAT_ONLY | RESOLVED |
| `20261113220000` moreai_worker_workspace_restore_immutable_version | `20261113133656` | `cbcaef705f423e985f39e2a66d58cd9b5cfdefe6` | `3f6385029172ccf4b456f1a31c914f92` | `dd6cc7f1635d26616b14992a18b862e4` | FORMAT_ONLY | RESOLVED |
| `20261113230000` moreai_customer_workspace_restore_empty_file | `20261113133736` | `707926e48c9cf59d3f088c8f10970da085ffac37` | `20300c5c7a199ae03b06509b626ac7d9` | `e01014f6ce013124b28dadc28b012eee` | FORMAT_ONLY | RESOLVED |
| `20261113240000` moreai_customer_learning_progress_pagination | `20261113134251` | `57c6b312497b3f1e1916635f6c8126f980305e6c` | `109970209df70e863cdad9a4807b6652` | `7eecab746acce209b74b009c5677c7e3` | FORMAT_ONLY | RESOLVED |
| `20261113250000` moreai_customer_knowledge_chunk_count | `20261113134544` | `d77d3ed51ca9f23b4008cb221bd3550a8a453277` | `8563490773317a05e801c3baa4ff03f4` | `f13fcd37e0aec3d98f510052d0e8cd47` | FORMAT_ONLY | RESOLVED |
| `20261114040000` moreai_customer_agent_configuration_capability_registry | `20261114034343` | `8b6d52457083b7bbbd888a67d5be2cb520644d03` | `8096df936267e71ab5a18388bcf10011` | `0edead7a27bfec40d556c6e74ab00ecc` | FORMAT_ONLY (GRANT CONSOLIDATION; EFFECTIVE PRIVILEGES EQUIVALENT) | RESOLVED |
| `20261115090000` moreai_agent_model_preferences | `20261115084819` | `86c53087c128b6a867bc462f4b3671ad716ea048` | `561ec2dfb21f2e7d74ad4a8ebf0ea4d5` | `9f5254d8a2749d42f512de381d22b68c` | FUNCTION_OR_TRIGGER_CHANGE (WRONG SAME-NAME PAIR) | SOURCE_IDENTITY_UNVERIFIED |
| `20261115110000` moreai_provider_configuration_and_route_types | `20261115092653` | `e88042d70e06f3b55dbb2f11fdb160fd8998eb7b` | `521b62cacd94702260778beb8bd405d3` | `d494325c65161c95c49701e17d7256fa` | FORMAT_ONLY | RESOLVED |
| `20261115111000` moreai_provider_endpoint_allowlist | `20261115092950` | `0475ff6dd22bf59e63976fb079996004271d6fa5` | `4349733bdb56d13f4b96efcc305fecc0` | `e068e4c5d738153a5472128b788fdd48` | FORMAT_ONLY | RESOLVED |
| `20261115130000` moreai_browser_action_receipts | `20261115095114` | `ed5795d85ecbf6741009be31d927b0dccf653d00` | `2873e62c61087c73860b8cd5283ac85e` | `f52d0432250f25a6293e7042fdc1ccdb` | FORMAT_ONLY | RESOLVED |
| `20261115131000` moreai_browser_action_receipt_action_types | `20261115095611` | `ce18eecf0110157f154b3c2d9701659763f9a336` | `5c1d149d80170217be73ffead4bf1077` | `5ea2b13a5bdcff1942965682d2202e26` | COMMENT_ONLY | RESOLVED |
| `20261115132000` moreai_browser_session_close_requests | `20261115095839` | `e7b345e5802bd0b3cad652b49aaf3cdc7c24e945` | `2a85f67a95f96f0521fa2079e0f4b394` | `2363ca343430740729c993d6666a996d` | COMMENT_ONLY | RESOLVED |
| `20261115134000` moreai_browser_action_receipt_result_retention | `20261115100615` | `ed88a05110c61e299b2a1d8f51041812b20ae65d` | `5195c0b159d4c10b116d41148ac52b7a` | `4af6ec5f69126924ab16910aaef2537f` | FORMAT_ONLY | RESOLVED |
| `20261115140000` moreai_computer_action_receipts | `20261115101318` | `4364d8bbb77a486dd9702cd743778f682684e5b9` | `dd86108c58b283cd74ae22af663efaa4` | `d765b85db8a61b88815198921d5f2180` | FORMAT_ONLY | RESOLVED |

## Raw diff conclusions
- 23/23 pairs were fetched from their actual source locations and compared.
- 23/23 raw MD5 pairs differ; raw equality is false for all.
- 21 pairs have identical ordered SQL lexical-token streams after comment/whitespace removal. Their raw differences are comments, blank lines, line wrapping or whitespace.
- One additional pair (`20261114040000`) has a token difference only because two GRANT statements were consolidated into one. The history grants SELECT, then INSERT and UPDATE; the repo grants SELECT, INSERT and UPDATE in one statement to the same grantee on the same relation. The effective privilege set is identical.
- One pair (`20261115090000`) is not a valid same-name source pairing. The repo file's MD5 is `561ec2dfb21f2e7d74ad4a8ebf0ea4d5`, identical to applied history `20261115085314` (`moreai_agent_model_preferences_attachment_compat`) and to repo file `20261115100000_moreai_agent_model_preferences_attachment_compat.sql` (same Git blob SHA `86c53087c128b6a867bc462f4b3671ad716ea048`). The paired history row `20261115084819` has a different MD5 `9f5254d8a2749d42f512de381d22b68c` and includes the preferred_model_id column/index DDL. The exact source identity for the historical 15084819 record is not present as a distinct repository file; do not treat the duplicate 15090000 file as its source.
- Prior classification that `20261115111000_moreai_provider_endpoint_allowlist` changed provider behavior was incorrect: its SQL lexical tokens match the applied history statement; only comments/formatting differ.
- The prior simple regex-based `whitespace_comment_stripped_match` field produced false negatives for SQL containing PL/pgSQL bodies. This report supersedes that field for semantic triage.

## Required resolution
- Preserve all 23 original source pairs and historical rows.
- Keep the 22 equivalent/format-only pairs as documented raw diffs; do not rewrite migration SQL solely for formatting.
- Keep `20261115090000` marked `SOURCE_IDENTITY_UNVERIFIED`; its source is a duplicate alias of `20261115100000`/applied `20261115085314`, while the original `20261115084819` source must be recovered or explicitly approved as historical-only.
- No migrations were applied and no schema was changed.

## Evidence files
- Source mismatch inventory: `docs/implementation/MOREAI_SUPABASE_MIGRATION_SQL_MISMATCH_REVIEW_20261118.csv`
- Final classification matrix: `docs/implementation/MOREAI_TASK1_SQL_MISMATCH_RECONCILIATION_FINAL_20261118.csv`
- Prior batch notes: `docs/implementation/MOREAI_TASK1_EXACT_SQL_DIFF_BATCH_NOTES_20261118.md`


## Addendum — migration 20261115084819 source recovered (2026-11-18)

The earlier status `SOURCE_IDENTITY_UNVERIFIED` for the current-main same-name pair is superseded by historical Git evidence. The source was recovered at commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`, historical path `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql`, Git blob `b7278df23425678a3009cb5c15f20e7c6cf53327`. A recursive SQL lexical tokenizer compared that historical Git source with history version `20261115084819`: 619/619 ordered tokens match. The current main file remains blob `86c53087c128b6a867bc462f4b3671ad716ea048`, identical to `20261115100000` and applied history `20261115085314`; it is not the 15084819 source. Thus the current-main pair remains a raw/source mismatch, but the historical source identity is now recovered. Overall provenance remains PARTIAL because there is no native history checksum/execution receipt and the filename version differs from the history version. See `migration-20261115084819-provenance-report.md`.
