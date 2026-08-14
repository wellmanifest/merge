# Ticket 004: Publish CQRS contract source of truth

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-14

## Goal and scope

Publish the reference CQRS skeleton for the merge-decision standard. One closed
`operations/index.json` becomes the canonical source of truth for Commands,
Queries, projections and their model bindings. `events/index.json` owns only
append-only facts and replay semantics; `error/index.json` owns only stable
public rejection metadata and links to `error/[code].md` runbooks.

This slice adopts the five preserved event drafts and three public rejection
runbooks. Seven additional untracked error drafts remain preserved outside this
worktree because the bounded delivery limit is 15 implementation files.

The user's instruction to continue implementing the mandatory CQRS skeleton is
`SESSION_EXECUTION_AUTHORIZATION` for this exact scope and its protected
publication process.

## Acceptance criteria

- [ ] AC-01: `operations/index.json` is the only Commands/Queries source of
  truth; event and error catalogues do not duplicate C/Q definitions.
- [ ] AC-02: Every registered event has a document beside it, is emitted by a
  declared command, is append-only, carries no authority and never replays an
  effect.
- [ ] AC-03: Every public command rejection resolves to a stable entry in
  `error/index.json` and an `error/[code].md` runbook.
- [ ] AC-04: Command input and query output model references resolve to the
  existing closed model schema; transport formats, including future protobuf
  mappings, do not become semantic or authority sources.
- [ ] AC-05: A dependency-free checker rejects duplicate IDs, broken model/doc
  references, orphan events/errors, query effects and unsafe replay semantics;
  the main conformance entrypoint runs it.
- [ ] AC-06: Governance, existing conformance and the CQRS adversarial cases
  pass within the 15-file delivery bound.
- [ ] AC-07: Exact-head Validator App review and protected merge publish the
  reference without interactive self-approval.

## Non-goals

- Do not make the skeleton mandatory across adopters in this target-owned
  reference ticket; `wellmanifest/new-project` owns that policy.
- Do not introduce a runtime event store, message broker or protobuf compiler.
- Do not import the seven additional untracked error drafts in this slice.
- Do not treat an event, projection, transport schema or Markdown runbook as an
  authorization grant.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
