# Browser migration exact correction diffs (proposal only)

No repository SQL file was changed. The following are proposed minimal diffs, not approved SQL.

## Event CHECK preservation

### 16250000 and 16260000 — before (source)
```sql
check (event_type in ('created','restored','state_saved','closed','expired',
  'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
  'takeover_input_succeeded','takeover_input_failed'));
```

### Proposed after (preserve existing applied lifecycle + new takeover events)
```sql
check (event_type in (
  'created','restored','state_saved','close_requested','closed','expired',
  'profile_retention_eligible','profile_deleted',
  'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
  'takeover_input_succeeded','takeover_input_failed'
));
```

### 16280000 — before (source)
```sql
check (event_type in (
  'created','restored','state_saved','close_requested','closed','expired',
  'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
  'takeover_input_succeeded','takeover_input_failed','takeover_command_queued'
));
```

### Proposed after
Same prior values plus profile_retention_eligible and profile_deleted; do not remove close_requested or any takeover value.

### 16300000 — before (source)
Same as 16280000, plus preview_requested.

### Proposed after
Same prior values plus profile_retention_eligible and profile_deleted; retain preview_requested.

## 16280000 malformed claim function

Before (malformed fragment):
```sql
if p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}    select c.id
```

Proposed guard shape (not a complete replacement function):
```sql
if p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}$'
   or p_limit < 1 or p_limit > 25 then
  raise exception 'takeover_command_claim_payload_invalid' using errcode='22023';
end if;
```

The remaining claim body must be reconstructed as one complete function with one candidate CTE, one lease-recovery policy, one UPDATE/RETURNING path, and one closing end;. Duplicate finish/revoke function and trigger blocks must be reduced to one canonical definition after owner approval. No full SQL replacement is supplied because source lineage and intended lease-retry semantics need owner confirmation.

## Identifier correction

Do not invent a replacement timestamp. Owner must approve the intended chronological position and valid YYYYMMDDHHMMSS IDs for all five sources as a coordinated set. Keep originals unchanged until that decision.


## Full proposed CHECK after-blocks (exact event set, not approved)

### 16280000 proposed after
```sql
check (event_type in (
  'created','restored','state_saved','close_requested','closed','expired',
  'profile_retention_eligible','profile_deleted',
  'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
  'takeover_input_succeeded','takeover_input_failed','takeover_command_queued'
));
```

### 16300000 proposed after
```sql
check (event_type in (
  'created','restored','state_saved','close_requested','closed','expired',
  'profile_retention_eligible','profile_deleted',
  'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
  'takeover_input_succeeded','takeover_input_failed','takeover_command_queued',
  'preview_requested'
));
```

These are event-vocabulary proposals only. They do not correct the malformed 16280000 function body or resolve the invalid migration IDs. They are not owner-approved and are not implemented.
