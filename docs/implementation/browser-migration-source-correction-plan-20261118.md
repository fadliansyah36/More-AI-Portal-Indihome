# Browser migration source correction plan

1. Owner confirms whether the five 14-digit IDs with hour values 25/26/27/28/30 are invalid timestamp names or an intentional alternate convention. If invalid, owner supplies coordinated replacement IDs; implementer must not invent them.
2. Owner confirms canonical browser event vocabulary. Proposed default is additive preservation of all currently applied values, plus each migration's newly introduced values.
3. Correct 16250000 and 16260000 CHECK definitions only after owner decision.
4. Correct 16280000 by reconstructing one syntactically complete claim RPC, retaining one finish RPC, one revoke trigger function and one trigger. Owner must decide whether expired worker leases are reclaimable or outcome-unknown terminal, because the source contains conflicting fragments.
5. Correct 16300000 with explicit session↔run association (for example matching session.run_id/last_run_id under approved lifecycle semantics) and artifact ownership/session/run-purpose validation; owner must confirm expected model.
6. Recheck all five dependencies and security posture statically; preserve originals and attach exact before/after diffs.
7. Record approvals in reviewed PR or owner decision artifact before updating migration source files.
8. Only a separate authorized task may apply migrations; this Task 1 batch must not.

No correction has been approved or implemented.
