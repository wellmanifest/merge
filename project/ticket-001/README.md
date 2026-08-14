# Ticket 001: Enable autonomous Validator publication

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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
- [x] AC-03: The existing deterministic conformance suite is a required hosted
  check named exactly `conformance`.
- [x] AC-04: The managed governance gate passes for this bounded ticket and
  accepted base.
- [x] AC-05: The target ruleset requires `conformance` plus a fresh approving
  review, the Validator App approves and merges the exact head, and the ticket
  branch is deleted.
- [x] AC-06: After the bootstrap proof, the protected validator registry turns
  on scheduled membership without adding another matrix/config list.

## Publication evidence

- Pull request #1 passed `conformance` and the managed remote lifecycle check
  on exact head `b7f313f678cda4077415f9c50455b3e48548fb61`.
- `ifuri-validator-agent[bot]` approved that exact head; the protected process
  merged it as `14712eae437f8dee8d7295f87a692ee6a4585368` on 2026-08-14.
- Repository ruleset `20870194` is active, has no bypass actors, requires
  `conformance`, one fresh approval and resolved threads, and permits only a
  merge commit. `delete_branch_on_merge=true`, and the implementation branch
  no longer exists on the remote.
- Validator-agent pull request #56 merged as
  `12de44928d2bfd6a3ce34fde3871e1d9bc0178b0`; the protected registry now derives
  an hourly scheduled scan leg for `wellmanifest/merge` with required check
  `conformance`.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Non-goals

- No change to standard semantics, rule equations or runtime dependencies.
- No PAT-based target review and no interactive self-approval or merge.
