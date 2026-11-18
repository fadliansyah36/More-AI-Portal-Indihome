# Object-level schema drift report — 2026-11-18

## Prerequisites
A full expected schema baseline is not available, so the full object-level comparison is blocked. This report contains only narrow lineage-backed comparisons and must not be read as a global no-drift result.

## Scoped comparisons
- The applied browser event CHECK lineage from 16083451 and 16083458 expects eight values. The live constraint definition contains exactly those eight values: MATCH.
- Three browser session retention columns from 16083458 are present as nullable timestamptz: MATCH for type/nullability only.
- preferred_model_id and a matching-named index are present. Column type/FK/index definition and current enqueue function evolution are not fully compared: PARTIAL_MATCH.
- Grants, commands and preview request tables from the five repository-only sources are absent from both history and observed catalog. This is EXPECTED_DIFFERENCE, not schema drift, while those sources remain unapplied.

## Counts
- Scoped object rows: 12.
- MATCH: 6 (including preferred_model_id column, FK and partial index).
- EXPECTED_DIFFERENCE: 3.
- NOT_VERIFIABLE: 2 (full public object set and superseded six-argument enqueue function).
No global object counts can be calculated because the expected schema object set is incomplete.

## Conclusion
No global NO_DRIFT conclusion. Full drift assessment remains NOT_VERIFIABLE. No schema correction or migration apply was performed.
