# Ticket 011: Preserve branches of closed unmerged pull requests

- **ID**: ticket-011
- **Owner**: user request in this session
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-24

## Goal and scope

The user authorized fixing the unsafe `ORPHAN_BRANCH` route after PR #18 merged.
The current matrix sends a merged **or closed** ticket branch to automatic prune,
while the adopted agent rule preserves a PR closed without merge until the owner
explicitly discards that work. This ticket changes the Env DSL matrix,
conformance regression and canonical event documentation only.

## Acceptance criteria

- [x] AC-01: A branch left after a verified merge may be retired only with
      protected merge evidence and a recovery receipt.
- [x] AC-02: A closed unmerged PR preserves its branch and requires an explicit
      owner discard decision before any later deletion; mutation tests enforce it.
- [x] AC-03: Conformance and repository governance gates pass.

Validation at `7fcd6b6b82f2a41ef21a409e6bd90696fefc66d0` base:
`python3 standard/conformance.py --all` reports 27 routed events and six
rejected invariant mutations; `./project/governance-check.sh` reports GOV-PASS.

## Tracking boundary

The source and tests live outside this ticket. The canonical event result is
`docs/MERGE_EVENTS.md` and is indexed in `docs/README.md`.
