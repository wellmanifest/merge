# Ticket 003: Correct autonomous merge runtime contract

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-14

## Goal and scope

Correct the standard after validator-agent removed the independent workflow
matrix and runtime variable. The document must describe the deployed protected
registry, its generated plan/runtime projection, repository-scoped Validator
App identity and isolation from the legacy Project queue PAT.

The user explicitly requested autonomous execution. That records
`SESSION_EXECUTION_AUTHORIZATION` for the bounded edit and its protected
publication, but it is not a trusted merge approval. This ticket's
implementation PR is also the canary: no interactive agent or manual workflow
dispatch may review or merge it.

## Acceptance criteria

- [x] AC-01: The document names `config/direct-pr-registry.json` as the only
  repository membership, base and required-check policy source.
- [x] AC-02: The enablement and diagnosis procedures match the generated
  `plan-direct-scan` matrix, digest-bound runtime config and target ruleset.
- [x] AC-03: The document no longer lists already-onboarded repositories as
  missing, and no longer presents the deleted repository variable as runtime
  configuration.
- [x] AC-04: Dependency reads required by the fleet use short-lived Validator
  App tokens; a legacy queue PAT failure is documented as isolated from the
  repository scan fan-out.
- [x] AC-05: A real `schedule` event finds this attributable PR, validates and
  merges its exact head with the Validator App, without `workflow_dispatch` or
  an interactive merge.

## Publication evidence

- GitHub Actions run `31839610022` was created with `event=schedule` at
  2026-08-14T20:48:39Z on protected validator-agent `main` revision
  `a78719afdcec384e07346cbe8d114032469631cf` (v0.6.43).
- `test` passed using the dependency-scoped Validator App token, then
  `plan-direct-scan` passed and generated 33 repository legs from registry
  digest `4910fa6c3ba1f6af961d9aec3941a4785ccff76aaed58386a3019e9e5d0dda10`.
- Job `94893608605`, `scan-direct (wellmanifest, merge)`, passed every token,
  registry, validation, summary and artifact step. Its report marked PR #5
  `approved` and `merged=true` while skipping draft PR #7 as a draft.
- The aggregate run concluded `failure` because legacy job `validate` hit
  `API rate limit already exceeded for user ID 5669657` in its Project queue.
  That failure did not cancel the protected plan or repository legs; the merge
  leg completed successfully afterward, proving queue-PAT isolation in vivo.
- `ifuri-validator-agent[bot]` approved exact head
  `ec877d8af719c169be03634160000b5047094b5f` at 20:50:19Z and merged it at
  20:50:23Z as `906000833031bf3afa589eb91e6907fd3ac19d63`.
- The implementation branch no longer exists on the remote. Neither the PR nor
  the scheduled run has a `workflow_dispatch` event.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
