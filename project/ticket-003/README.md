# Ticket 003: Correct autonomous merge runtime contract

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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

- [ ] AC-01: The document names `config/direct-pr-registry.json` as the only
  repository membership, base and required-check policy source.
- [ ] AC-02: The enablement and diagnosis procedures match the generated
  `plan-direct-scan` matrix, digest-bound runtime config and target ruleset.
- [ ] AC-03: The document no longer lists already-onboarded repositories as
  missing, and no longer presents the deleted repository variable as runtime
  configuration.
- [ ] AC-04: Dependency reads required by the fleet use short-lived Validator
  App tokens; a legacy queue PAT failure is documented as isolated from the
  repository scan fan-out.
- [ ] AC-05: A real `schedule` event finds this attributable PR, validates and
  merges its exact head with the Validator App, without `workflow_dispatch` or
  an interactive merge.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
