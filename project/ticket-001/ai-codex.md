---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-001
---
# Participant: codex (AI agent)

## Understanding

The merge standard already has a dependency-free conformance suite but no
hosted check, governance package, ruleset or Validator fleet profile. A list
entry alone would therefore create an ineffective scan. The requested outcome
is the complete publication boundary: deterministic CI, protected review,
Validator-owned merge and branch cleanup.

The request explicitly requires autonomous execution and publication, so it
creates `SESSION_EXECUTION_AUTHORIZATION` and permits invoking the declared
protected delivery process. It does not make this interactive agent a trusted
reviewer and does not authorize a direct merge.

## Execution plan

1. Adopt exact published `wellmanifest/new-project` v0.18.0.
2. Record one bounded governance ticket and accepted base.
3. Add a hosted `conformance` job that runs the existing suite and governance
   gate without a new dependency.
4. Create the server ruleset and enable branch deletion.
5. Publish one ticket PR, dispatch the one-off protected Validator profile and
   verify exact-head approval, merge and branch deletion.
6. Enable scheduled registry membership in `validator-agent` and observe a
   non-manual scheduled scan.

## Actual changes

- Initialized the bounded ticket and recorded `SESSION_EXECUTION_AUTHORIZATION`.
- Adopted published governance v0.18.0 at exact revision
  `769183ca27593af1d166acee11bc9e37decf9870`.
- Added one hosted `conformance` job that runs the existing standard suite and
  the managed governance gate with full base history.

## Blockers

- None inside the recorded scope. External target settings are part of the
  requested protected publication boundary, not a hand-back to the user.
