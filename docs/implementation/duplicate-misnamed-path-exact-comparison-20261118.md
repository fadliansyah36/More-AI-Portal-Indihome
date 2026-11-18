# Duplicate/misnamed path exact comparison

## Model preference current paths

- Current main 20261115090000_moreai_agent_model_preferences.sql: blob 86c53087c128b6a867bc462f4b3671ad716ea048, 5,956 bytes.
- Current main 20261115100000_moreai_agent_model_preferences_attachment_compat.sql: same blob SHA, same size, byte-identical.
- Their raw SQL MD5 is 561ec2dfb21f2e7d74ad4a8ebf0ea4d5, matching applied history 15085314.
- They do not match history 15084819 (MD5 9f5254d8a2749d42f512de381d22b68c).
- Historical source for 15084819 was recovered at Git commit cc5563e... path 15090000; Git blob b7278df...; 619/619 ordered tokens match history SQL.

Decision: current 15090000 is a confirmed duplicate/misnamed alias of 15100000 / history 15085314. The original historical 15084819 source exists in Git history but is not the current main file. Keep both current files unchanged until owner decides canonical path and archival disposition.

## Durable run event outbox alias

Repository 20261111110000 has exact SQL content matching applied history 20261111091531. It is an alias, not an additional unapplied migration to apply. Preserve pending owner-approved archive/duplicate disposition.

## Browser IDs

The five current source IDs encode invalid hours 25/26/27/28/30. This is a naming/provenance issue separate from their SQL source defects. No new identifier is assigned.
