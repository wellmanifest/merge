# Ticket 001: Enable autonomous Validator publication

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-14

## Goal and scope

Adopt the published `wellmanifest/new-project` governance package and add one
hosted `conformance` check for the existing dependency-free standard suite.
Publish through exact-head review by `ifuri-validator-agent[bot]`; the
interactive agent must never approve or merge this work.

## Acceptance criteria

- [x] AC-01: The user's autonomous execution request records
  `SESSION_EXECUTION_AUTHORIZATION` without treating it as merge approval.
- [x] AC-02: Governance is pinned to published `new-project` v0.18.0 at exact
  revision `769183ca27593af1d166acee11bc9e37decf9870`.
- [ ] AC-03: The existing deterministic conformance suite is a required hosted
  check named exactly `conformance`.
- [ ] AC-04: The managed governance gate passes for this bounded ticket and
  accepted base.
- [ ] AC-05: The target ruleset requires `conformance` plus a fresh approving
  review, the Validator App approves and merges the exact head, and the ticket
  branch is deleted.
- [ ] AC-06: After the bootstrap proof, the protected validator registry turns
  on scheduled membership without adding another matrix/config list.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Non-goals

- No change to standard semantics, rule equations or runtime dependencies.
- No PAT-based target review and no interactive self-approval or merge.
