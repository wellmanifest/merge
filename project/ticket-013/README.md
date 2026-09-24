# Ticket 013: Reject negated or untrusted merge gate markers

- **ID**: ticket-013
- **Owner**: user continuation in this session
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-24

## Goal and scope

Ticket-012 restricted merge authority to Validator, but `conformance.py` still
searches substrings inside free-text gate observations. A value such as
`required-checks-green=false` or a human claim can satisfy a merge precondition.
Count only exact positive markers from deterministic gate-produced evidence.
Any cited `required-checks-not-run` observation remains a merge blocker.
The same extraction must drive Python and Env DSL facts.

## Acceptance criteria

- [x] AC-01: Negated, prose-only and nondeterministic precondition claims fail
      in both checker and Env DSL; exact deterministic gate markers pass.
- [x] AC-02: Conformance and governance pass at the ticket head.

At base `6a1ea0fbe72159cb0c9e199f7196eb280ad96724`, conformance passes
with 32 rejected adversarial cases and 19 Env DSL parity cases. Governance
reports GOV-PASS, and `git diff --check` passes. Protected Validator review
and merge remain separate publication steps.

## Tracking boundary

The canonical policy remains `docs/AUTONOMOUS_MERGE.md`, indexed in
`docs/README.md`. Raw evidence remains in private recovery storage.
