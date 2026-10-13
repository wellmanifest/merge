# Ticket 015: Propose owner-delegated merge decision record

- **ID**: ticket-015
- **Owner**: human:owner (requested 2026-10-12); agent:claude drafts
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-12

SESSION_EXECUTION_AUTHORIZATION: owner asked to change the rule so that the interactive agent may merge, "in line with wellmanifest". Under `docs/AUTONOMOUS_MERGE.md` and `MRG-MERGE-001` that change is the owner's policy decision; this ticket only drafts it for review.

## Goal and scope

Add a **proposed** decision record `docs/decisions/owner-delegated-merge.md` that states the owner's request, the current rule, alternatives and consequences, and index it in `docs/README.md`. No change to `standard/**`, `MRG-*` rules, conformance code or `AUTONOMOUS_MERGE.md`; the record grants no authority until the owner accepts it through the protected process.

## Acceptance criteria

- [x] AC-01: Scope is approved by a human owner. (owner replied "TAK" to the plan on 2026-10-13)
- [x] AC-02: The record separates current rule (facts, cited), proposal and alternatives (keep Validator-only; owner-delegated profile; per-repository Validator enrollment).
- [x] AC-03: Status is `proposed`; it states explicitly that rules, conformance and host AGENTS stay unchanged until acceptance.
- [x] AC-04: `docs/README.md` links it; `standard/conformance.py --all` and the governance gate still pass.

No unrelated scope or required gate may be removed.
