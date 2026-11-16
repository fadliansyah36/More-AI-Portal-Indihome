# Phase 09D / AI Skills / 09C — Source Implementation Continuation

Date: 2026-11-16  
Branch: `main`

## Scope

This increment continues implementation without staging or real runtime verification. It does not claim that a persistent desktop host, worker deployment, provider secrets, or production runtime is provisioned.

## AI Skills Governance

### SPDX inventory

`apps/api/app/routers/skills.py` now expands the generated SPDX-2.3 document to include:
- Dependency package records with declared license evidence and registry-resolution status.
- Individual ingested source-file records with SHA-256 checksums.
- Document-to-package and document-to-file relationships.
- Explicit `NOASSERTION` conclusions for file-level license/copyright where rights have not been proven.
- A scope disclaimer distinguishing source inventory from build attestation and legal approval.

Validation now fails closed to `review_required` when exact dependency registry metadata is unresolved, dependency license declarations are unknown/unrecognized, dependency versions are not exact, or binary assets lack rights evidence. This prevents the existing admin approval workflow from publishing packages whose validation state is not `validated`.

### Reviewer UI

The existing Super Admin Skill Review screen now displays the SPDX version, package/file counts, per-file SHA-256 evidence and dependency license declarations. It reuses the existing UI surface and styles; no new admin shell or global styling was introduced.

## Customer dashboard — Computer receipts

The existing Code Assistant screen now loads the authenticated customer's durable Computer action receipts through the existing typed `customerApi.computerActionReceipts` method. It shows Python/Bash action type, run/workspace reference, request time, terminal status and safe error code. It does not expose execution source or raw output. Loading and error states are included, with a manual refresh action.

This closes a concrete frontend visibility gap for Computer action lifecycle receipts; it does not enable execution or claim that the sandbox is deployed.

## Changesets

- `18840c18b9f089728a23970c28e9641c4a8b96e3` — expanded SPDX SBOM and strict validation findings.
- `d57a1a0db8c5ac5efbc74397f2ee83338ea56567` — exposed SBOM evidence in the Super Admin reviewer.
- `acc783e05ab645d1e6cf0a5c1bf4542ea38c0e0f` — customer Computer execution receipt panel.
- `a5734fdae7a95be783e058c8e35ceb6c0f8ed6ee` — stabilized receipt loading callback.

## Remaining implementation gates

1. Persistent per-customer Computer/Desktop runtime with isolated durable volumes, explicit session lifecycle, recovery, quotas and audit correlation is still not implemented. The current disposable runner must not be represented as a persistent desktop.
2. Multi-replica capacity coordination remains external to the process-local supervisor.
3. Malware scanning and complete binary asset/license provenance remain unresolved; skill execution stays release-gated.
4. Full recursive dependency closure for every ecosystem, transitive package metadata, vulnerability scanning and legal compatibility decisions require additional implementation and reviewer evidence.
5. Phase 09C still needs a full route-to-screen closure pass for remaining dashboard actions.
6. Phase 09A–09B operational completion still depends on persistent worker infrastructure and actual server-side provider secrets.

## Verification policy

Per product-owner instruction, no tests, build, lint, typecheck, browser/API/worker/Docker runtime, staging or deployment were run. These changes are source edits only; runtime behavior and release acceptance remain unverified.
