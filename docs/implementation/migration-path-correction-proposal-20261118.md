# Migration path correction proposal — not implemented

1. For current 20261115090000_moreai_agent_model_preferences.sql, owner chooses archive-only or deletion from current tree after confirming historical commit cc5563e is preserved and that the current file content is represented by canonical 20261115100000 / history 15085314. No path change in this Task 1 batch.
2. Retain 20261115100000_moreai_agent_model_preferences_attachment_compat.sql as canonical candidate for history 15085314 unless owner identifies a different authoritative source.
3. For 20261111110000_moreai_durable_run_event_outbox.sql, owner decides whether it remains as a documented alias or is archived; do not apply.
4. For the five browser migration files, owner supplies valid IDs and intended order as a coordinated set. Keep original filenames and blob identities until approved.
5. Any future rename/move must preserve source blob SHA, commit lineage and a path mapping record. Never rewrite historical migration history.
