# Ticket 012: Require Validator merge authority and verified OneDev fallback

- **ID**: ticket-012
- **Owner**: user request in this session
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-24

## Goal and scope

The user instructed agents to use OneDev and Validator instead of human review,
and asked to continue, test and merge. Ticket-010 left an `executor: owner`
exception that lets the interactive agent run a merge on the owner's instruction
and treats local tests as a bypass when a required hosted check never ran. That
contradicts the protected review boundary. Align the decision checker, Env DSL,
schema description and canonical merge documentation. A protected OneDev status
may satisfy a check only when the current Validator policy requires it.

## Acceptance criteria

- [x] AC-01: Only `automated-validator` can authorize `merge`; `owner` and
      `interactive-agent` merge decisions are rejected in Python and Env DSL.
- [x] AC-02: `required-checks-not-run` blocks merge for every executor;
      arbitrary local tests cannot turn the missing required check green.
- [x] AC-03: Documentation directs missing-check recovery to protected OneDev
      and Validator policy, with no agent-executed owner bypass.
- [x] AC-04: Exact-head conformance, Env DSL parity and governance checks pass.

At base `1e8549e599d05f20ffe8919fb5fd5a0de2cbce97`,
`python3 standard/conformance.py --all` passes with negative owner and
missing-check cases plus a positive Validator case; `./project/governance-check.sh`
reports GOV-PASS and `git diff --check` passes. This is local evidence; the
protected Validator still reviews the pushed exact head before merge.

## Tracking boundary

The canonical merge behavior is documented in `docs/AUTONOMOUS_MERGE.md` and
`docs/ARCHITECTURE.md`, both indexed in `docs/README.md`. Raw command logs
remain in private recovery storage.
