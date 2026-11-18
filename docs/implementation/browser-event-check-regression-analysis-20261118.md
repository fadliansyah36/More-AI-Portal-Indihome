# Browser event CHECK regression analysis

## Applied lineage

- 20261115084424 creates the event table with: created, restored, state_saved, closed, expired.
- 20261116083451 adds close_requested for the customer close-request lifecycle.
- 20261116083458 adds profile_retention_eligible and profile_deleted for 30-day browser profile retention.
- 20261116083502 defines SECURITY DEFINER RPCs that insert profile_retention_eligible and profile_deleted.
- Current live CHECK definition is exactly: created, restored, state_saved, close_requested, closed, expired, profile_retention_eligible, profile_deleted.

This lineage is backed by stored SQL in migration history and current catalog introspection.

## Source regressions

- 16250000 and 16260000 replace the CHECK with created/restored/state_saved/closed/expired plus takeover event values, removing close_requested and both profile events.
- 16280000 and 16300000 preserve close_requested but remove profile_retention_eligible and profile_deleted.
- 16270000 does not replace the CHECK.

These are source-level regressions relative to the applied lifecycle contract. They are not current live drift because none of the five source files is recorded in history or present as live objects.

## Correction proposal (not approved or implemented)

For each CHECK replacement, preserve all values from the last applied definition and append only event values required by that migration:
- 16250000: retain all eight existing values and add takeover_grant_created, takeover_grant_consumed, takeover_grants_revoked, takeover_input_succeeded, takeover_input_failed.
- 16260000: retain all existing values and the takeover values already introduced by 16250000; no further event type is introduced by this source.
- 16280000: retain all existing values and all takeover values, then add takeover_command_queued.
- 16300000: retain all existing values and all prior takeover/command values, then add preview_requested.

No value should be removed unless a product owner approves lifecycle deprecation and all dependent writers/readers are mapped. The proposal is not an owner decision and must not be applied.
