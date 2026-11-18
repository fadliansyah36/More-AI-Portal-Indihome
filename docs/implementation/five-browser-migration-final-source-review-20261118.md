# Five browser migration final source review — 2026-11-18

All five files were fetched from current main. They are repository-only, absent from Supabase migration history. Static source inspection only; no execution, testing or database writes.

| File ID | Timestamp validity | Blob SHA | SQL review | Dependency | Owner status |
|---|---|---|---|---|---|
| 20261116250000 | Invalid hour 25 | 8cd9be2c829feedec2137a64255118fc97017d3f | CHECK removes close_requested and both profile events; creates grants/RPCs/trigger | Base session tables exist | OWNER_DECISION_REQUIRED |
| 20261116260000 | Invalid hour 26 | e577c761e5c02075a9c308d05f66c9e907b193ea | CHECK removes close_requested and both profile events; run terminal revocation trigger | Requires grants from 16250000 | OWNER_DECISION_REQUIRED / BLOCKED |
| 20261116270000 | Invalid hour 27 | fad309b95d7c67e1f0585d4b3d923456e6443449 | Logout revocation RPC; no CHECK replacement; service-only function accepts p_user_id | Requires grants from 16250000 | OWNER_DECISION_REQUIRED / BLOCKED |
| 20261116280000 | Invalid hour 28 | dac0d2796ebef75570a7ca79ed10a13025579615 | Malformed PL/pgSQL, duplicate function/trigger definitions, orphan condition fragment; CHECK omits two profile events | Requires grants from 16250000 | OWNER_DECISION_REQUIRED / BLOCKED |
| 20261116300000 | Invalid hour 30 | 1ae88c4f56cb1c69ae225a258273e8e1f3f6bfe2 | Preview queue; CHECK omits two profile events; run/session and artifact associations insufficiently constrained in SQL | Base tables exist; no grants dependency | OWNER_DECISION_REQUIRED |

## Identifier finding

The filenames use 14-digit migration-like identifiers but encode hours 25, 26, 27, 28 and 30 for 2026-11-16. Those are invalid wall-clock values under YYYYMMDDHHMMSS. No evidence found that establishes a deliberate alternative numbering convention, and no owner-approved replacement IDs were found. Do not silently normalize them.

## Decision

Source review is complete; source approval is not. Keep originals immutable. All five owner decisions remain OWNER_DECISION_REQUIRED. 16260000, 16270000 and 16280000 are dependency-blocked; 16250000 and 16300000 remain unresolved pending owner decision/correction. No migration is approved for application.
