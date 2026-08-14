# Ticket 002: Declare CQRS standard path ownership

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-14

## Goal and scope

Declare deterministic ownership for the domain-contract skeleton requested for
every Wellmanifest standard. The integration workstream will own the canonical
command/query operation registry, append-only event catalogue, typed error
catalogue and transport-model namespaces. This prerequisite changes no merge
semantics and creates none of those contracts yet.

The user's request to continue and make the CQRS skeleton mandatory is
`SESSION_EXECUTION_AUTHORIZATION` for this bounded prerequisite and its
protected publication process.

## Acceptance criteria

- [x] AC-01: `operations/**`, `events/**`, `error/**`, `models/**` and
  `proto/**` have exactly one declared owner: the integration workstream.
- [x] AC-02: Existing application, interface, infrastructure and governance
  ownership remains unchanged.
- [x] AC-03: The manifest remains schema-valid, and the managed governance gate
  plus the merge conformance suite pass.
- [x] AC-04: The prerequisite is published through exact-head protected review;
  no interactive agent approves or merges its own change.

## Publication evidence

- Pull request #3 passed `conformance` and `governance / remote lifecycle` on
  exact head `0be726e6899266c138a360d185acd5f0bcb5cca9`.
- `ifuri-validator-agent[bot]` approved that exact head; the protected process
  merged it as `dfca0c31a4171062f603400265888ca62ee27a12` on 2026-08-14.
- The implementation branch was deleted by the server. The integrated manifest
  on `main` now owns all five new namespaces through `integration`.

## Non-goals

- Do not copy the currently untracked reference drafts from the primary
  checkout into this governance ticket.
- Do not make a path mandatory before the integration workstream has published
  a conforming reference implementation.
- Do not edit the pinned adoption base or lock; `.governance/manifest.json` is
  the package-declared extendable project contract.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
