# Expected schema baseline candidate comparison

Decision: INSUFFICIENT_EVIDENCE / BASELINE_SELECTION_BLOCKED.

| Rank | Candidate | Strength | Contradictions/gaps | Decision |
|---|---|---|---|---|
| 1 | Applied migration history plus recoverable historical SQL | Best evidence of recorded version sequence and stored statements; several browser lineage objects can be reconstructed | 32 history names have no same-name current source; no native checksum; 23 current-main pair differences; execution receipts absent | Best lineage source, not a complete baseline |
| 2 | Live Supabase catalog snapshot | Authoritative for observed object definitions at inspection time | Does not establish intended/expected definitions; environment role not independently attested | Observed baseline only |
| 3 | Current main migration directory | Authoritative for current branch source and blob identity | 85 files vs 116 history rows; five unapplied browser files have invalid timestamp hour components; duplicate/misnamed 15090000 | Repository intent only |
| 4 | Master PRD v1.2 Draft | Product/architecture constraints | Not DDL complete; draft | Context only |
| 5 | Schema dump / offline replay | Could establish a complete expected state with provenance | No trusted immutable dump identified; offline replay not authorized | Required evidence unavailable |

A narrow lineage-backed expected definition is supported for the browser session event CHECK: initial values from 15084424, close_requested added by 16083451, profile_retention_eligible/profile_deleted added by 16083458, with 16083502 RPCs writing the retention values. This is a scoped object contract, not a whole-database baseline.

No candidate is selected as the full expected schema baseline. A complete object inventory with authoritative expected definitions cannot be manufactured from aggregate counts or partial SQL history.
