# Ticket 004: Publish CQRS contract source of truth

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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

- [x] AC-01: `operations/index.json` is the only Commands/Queries source of
  truth; event and error catalogues do not duplicate C/Q definitions.
- [x] AC-02: Every registered event has a document beside it, is emitted by a
  declared command, is append-only, carries no authority and never replays an
  effect.
- [x] AC-03: Every public command rejection resolves to a stable entry in
  `error/index.json` and an `error/[code].md` runbook.
- [x] AC-04: Command input and query output model references resolve to the
  existing closed model schema; transport formats, including future protobuf
  mappings, do not become semantic or authority sources.
- [x] AC-05: A dependency-free checker rejects duplicate IDs, broken model/doc
  references, orphan events/errors, query effects and unsafe replay semantics;
  the main conformance entrypoint runs it.
- [x] AC-06: Governance, existing conformance and the CQRS adversarial cases
  pass within the 15-file delivery bound.
- [x] AC-07: Exact-head Validator App review and protected merge publish the
  reference without interactive self-approval.

## Publication evidence

- Hosted `governance / remote lifecycle` and `conformance` checks passed on
  exact PR #7 head `5b19cd9ad1e8ef125840cac911255f0f63ddf001`.
- Protected validator-agent run `31842721768` completed successfully;
  `ifuri-validator-agent[bot]` approved that exact head at 21:32:17Z.
- The protected process merged PR #7 at 21:32:21Z as
  `28de24d66d94b1773419f679a9d098a8372a8945` and deleted the remote
  implementation branch. This closure starts from that integrated merge.

## Non-goals

- Do not make the skeleton mandatory across adopters in this target-owned
  reference ticket; `wellmanifest/new-project` owns that policy.
- Do not introduce a runtime event store, message broker or protobuf compiler.
- Do not import the seven additional untracked error drafts in this slice.
- Do not treat an event, projection, transport schema or Markdown runbook as an
  authorization grant.

## Coordination state

The implementation was preserved at
`ca9e403ede3a430e4741f7f5889b1eba7babf08a` while the previously reserved
ticket-003 owned the integration workstream. Its schedule-only canary PR #5
was merged by Validator App as `906000833031bf3afa589eb91e6907fd3ac19d63`,
and its governance-only PR #8 was then merged as
`123467486af0d2a24fe359be58f154b6c7c75234`. The integrated ticket record is
now `DONE / DONE`, so ticket-004 owns the released integration workstream and
has updated from that exact base. Closed, unmerged PR #6 remains historical
evidence; its branch was correctly retained and is now reused for a fresh PR.
That replacement PR #7 is integrated and the reused implementation branch has
now been deleted by the protected process.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
