# Supabase historical migration source archive

Recovery baseline: repository main ad9a159221bbd36ecea494ea539622e3eb072e63
Supabase project: `uunfgimtokhucegqbpce`
Method: read-only SELECT from `supabase_migrations.schema_migrations`.
No migration, DDL, history mutation, replay, reset, or production write was performed.

Each JSON record preserves the original `statements` array, rollback value, history metadata, and per-statement SHA-256.
All 32 records have one stored SQL statement and NULL rollback. A basic credential-pattern scan returned no matches; this is not a substitute for human security review.
These files are immutable historical evidence and MUST NOT be placed in `supabase/migrations/` or replayed.

| Version | Name | Statement SHA-256 | Archive |
|---|---|---|---|
| 20261102073329 | revoke_public_rls_event_function_execution | 32028dea732e28db9c2f7223747cab95114c1ff7a14aba77a8937667f2aa4e34 | `docs/implementation/migration-history-archive/20261102073329_revoke_public_rls_event_function_execution.json` |
| 20261102073850 | moreai_phase02_identity_partner_network_foundation | 603da32b39fd98a3da1197edfd02d8be6b5c32928431e7661c9fff6685946949 | `docs/implementation/migration-history-archive/20261102073850_moreai_phase02_identity_partner_network_foundation.json` |
| 20261102073934 | moreai_phase02_permission_matrix_seed | f6f506a19e9e6beecb7eb4af9755a896069d583d295f7bb64bb91207d7b73493 | `docs/implementation/migration-history-archive/20261102073934_moreai_phase02_permission_matrix_seed.json` |
| 20261102074028 | fix_workspace_membership_rls_qualification | 100247b9aa6709fcbd73a9b741aa3d9edecd5aaaa905eb8143b5d18c58a48a1a | `docs/implementation/migration-history-archive/20261102074028_fix_workspace_membership_rls_qualification.json` |
| 20261102074504 | moreai_phase02_tenant_read_rls_policies | 1c197fe3f437d605c1eb52024a4e902f76077233e84da479f24c2e9a5ea5174c | `docs/implementation/migration-history-archive/20261102074504_moreai_phase02_tenant_read_rls_policies.json` |
| 20261102075051 | explicit_server_only_deny_policies | fd46b3da0e4ef179d9a2f5e6ed4998d03a61a08897bf6fa81013eae0809f142a | `docs/implementation/migration-history-archive/20261102075051_explicit_server_only_deny_policies.json` |
| 20261102075825 | moreai_phase02_agent_billing_campaign_domains | 2993e387aeb23b61b36d2d612be392aa73982597bdb5c1806650d600ad62d0e3 | `docs/implementation/migration-history-archive/20261102075825_moreai_phase02_agent_billing_campaign_domains.json` |
| 20261102080148 | moreai_atomic_credit_reservation_settlement | c0a302119ad8fc3ab5a1efe2df3c9e45895ab0ac12a438984fd4dd4738a0e5a0 | `docs/implementation/migration-history-archive/20261102080148_moreai_atomic_credit_reservation_settlement.json` |
| 20261102081613 | moreai_durable_worker_run_lifecycle | 9b93ba8fb273f2ff9789f323c51dad416a2bdce45ab343492f483429af904db2 | `docs/implementation/migration-history-archive/20261102081613_moreai_durable_worker_run_lifecycle.json` |
| 20261102082317 | moreai_worker_leases_recovery_cancellation_deadletter | 73dfba3235894b656a713f291b5fec540c22c685784136d8a9057a4de13a5b08 | `docs/implementation/migration-history-archive/20261102082317_moreai_worker_leases_recovery_cancellation_deadletter.json` |
| 20261102082504 | moreai_worker_lease_lifecycle_hardening | a86a88654cc59acd151441476f1039b71e5ca59bc303d89b4d68d98b4a7a68ae | `docs/implementation/migration-history-archive/20261102082504_moreai_worker_lease_lifecycle_hardening.json` |
| 20261102083716 | moreai_worker_cancel_and_legacy_rpc_hardening | bd1daec6920ba1ad1bde340b378de95db3c1dea17ffdf8b2d18c6ca20aba7ab8 | `docs/implementation/migration-history-archive/20261102083716_moreai_worker_cancel_and_legacy_rpc_hardening.json` |
| 20261102084310 | moreai_llm_durable_idempotent_settlement | f27a0158e08bd07033918713c196cec478eca283142a7c3bc2e169980ddb2e3c | `docs/implementation/migration-history-archive/20261102084310_moreai_llm_durable_idempotent_settlement.json` |
| 20261102084950 | moreai_llm_request_record_server_only_policy | 02bf1be58999cdf9b7d1e2c674253fb37eadde86a877be6d6ccac99d4eb9e748 | `docs/implementation/migration-history-archive/20261102084950_moreai_llm_request_record_server_only_policy.json` |
| 20261103100442 | single_active_network_verification_method | 102625caacb42a891cb951a7604eee9053f546623e215d7c88270770dea5d41d | `docs/implementation/migration-history-archive/20261103100442_single_active_network_verification_method.json` |
| 20261103101050 | grant_super_admin_partner_org_permissions | 12918e37a2b589560b09560379fdc958026ec1144d04ef2b6d19f0ba6ee70a05 | `docs/implementation/migration-history-archive/20261103101050_grant_super_admin_partner_org_permissions.json` |
| 20261103101208 | partner_onboarding_and_review_atomic_rpcs | adf6cf6b36220eb2fb35c35f4db6994d3d35e2587e549de099d30ecf5bbd2953 | `docs/implementation/migration-history-archive/20261103101208_partner_onboarding_and_review_atomic_rpcs.json` |
| 20261103101333 | serialize_partner_application_submission | 3f4366ef1c0a6ae202836edcc0f83525272efede08824d5f6d01432e2c5df075 | `docs/implementation/migration-history-archive/20261103101333_serialize_partner_application_submission.json` |
| 20261103101453 | atomic_admin_llm_provider_model_routing_management | df943385f579fa3ef42fafbe075e6c1f87696e4d790fdd6cf61910db2e01e15b | `docs/implementation/migration-history-archive/20261103101453_atomic_admin_llm_provider_model_routing_management.json` |
| 20261103102141 | atomic_platform_role_assignment_and_revocation | cb5a9af790c9475d587335bbedff5cd438be4f209f61a9a8740d4163441589d2 | `docs/implementation/migration-history-archive/20261103102141_atomic_platform_role_assignment_and_revocation.json` |
| 20261103102304 | serialize_super_admin_role_revocation | d93d766f7077eb5ca4820516e6cd1b2aff6d5885cffaa8520ed0fa3ca9c6b749 | `docs/implementation/migration-history-archive/20261103102304_serialize_super_admin_role_revocation.json` |
| 20261103102756 | preserve_partner_invites_on_approval | 7eb5059d0ee511a607242c0707ca60787d7ecb4e189b9a7ba0a6d448f0fb7413 | `docs/implementation/migration-history-archive/20261103102756_preserve_partner_invites_on_approval.json` |
| 20261103122523 | workspace_chat_idempotency | 9e0794c3dda1c7759fbf3ec1c9ddce09b8f4dddb043dee35a5b3f70d557c8b3c | `docs/implementation/migration-history-archive/20261103122523_workspace_chat_idempotency.json` |
| 20261103122556 | extend_completed_chat_idempotency_retention | cf03713d18b4bf2df75430c55f95108d4e8de4e85ae5569524903909014ebcfe | `docs/implementation/migration-history-archive/20261103122556_extend_completed_chat_idempotency_retention.json` |
| 20261103122824 | atomic_admin_role_permission_matrix | 258e11221502f39cc1804f69bed8fb8ff6a9b0236c75bf1c394b69dc69ee1cc1 | `docs/implementation/migration-history-archive/20261103122824_atomic_admin_role_permission_matrix.json` |
| 20261103123820 | use_invoker_security_for_admin_rpcs | 3480781bb800340763eff929c776af1efd9fde622f7d750ca1ded49adbb0c185 | `docs/implementation/migration-history-archive/20261103123820_use_invoker_security_for_admin_rpcs.json` |
| 20261105095527 | partner_access_codes_atomic_redemption | fd57115dab0c985b5a45c9ebe5897e91ed12b3e8a9bdf9b922bc8568f0468200 | `docs/implementation/migration-history-archive/20261105095527_partner_access_codes_atomic_redemption.json` |
| 20261111083146 | moreai_notifications_private_artifacts_immutable_audit | f540adb90f37cb096c82a5197f99efb70eba6e4e36600b694b908e5ce1063d2a | `docs/implementation/migration-history-archive/20261111083146_moreai_notifications_private_artifacts_immutable_audit.json` |
| 20261111091531 | moreai_durable_run_event_outbox_phase_07a | 5a4da40e3a2c1c8a484e80a6dccb23c8a4000baad38422545deffdf82949a48e | `docs/implementation/migration-history-archive/20261111091531_moreai_durable_run_event_outbox_phase_07a.json` |
| 20261111091638 | moreai_outbox_retry_lease_fencing | a975cc21b12a9d1b0b6949683b8e4fe60ac2cb5512aa5f41a9abdab8c32a64a7 | `docs/implementation/migration-history-archive/20261111091638_moreai_outbox_retry_lease_fencing.json` |
| 20261114070551 | moreai_edutech_path_summary_view | 4ed779d68235619ca409c2a1d972fed9a6bc3bf2356fffc24e31b5a0e59fefeb | `docs/implementation/migration-history-archive/20261114070551_moreai_edutech_path_summary_view.json` |
| 20261115090226 | moreai_edutech_assessment_derived_progress | 96de056306359f57c3eaddbfc9ad06d59981ff295538eb5a655498ef3b9c6725 | `docs/implementation/migration-history-archive/20261115090226_moreai_edutech_assessment_derived_progress.json` |

Status: source bytes recovered from migration history; original repository commit/blob provenance and SQL equivalence to historical deployed schema remain under review.
