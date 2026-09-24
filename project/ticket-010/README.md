# Ticket 010: Align merge authority with the rules and add checks-not-run state

- **ID**: ticket-010
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-24

## Goal and scope

Session 2026-09-24, owner requests: "używamy zamiast człowieka walidacji
onedev-agent i validator-agent i każdy LLM powinien respektować decyzje tego
walidatora i konsolidatora"; "zapisz wszystkie możliwe zdarzenia i macierze
rozwiązań autonomicznych w ramach sformalizowanego DSL [...] odnośnie
mergowania"; "wykonaj". SESSION_EXECUTION_AUTHORIZATION recorded here.

This reverses the ticket-008 prose that let an interactive agent merge via
`--admin`, reviewer-profile rotation or a browser "bypass rules" click. That
prose contradicted the normative `RULE_MERGE_EXECUTOR_CONDITION` and
`MRG-MERGE-001`; the owner now names validator-agent and onedev-agent as the
review and merge authority.

Scope:

- `standard/merge-events.env`: closed catalogue of 26 merge events with one
  autonomous resolution each (actor, action, next state, notice, priority)
  and equations proving only the Validator reaches MERGED, the owner is never
  an actor and every resolution is autonomous;
- `standard/merge-rules.env` + `conformance.py`: `required-checks-not-run`
  is never green; parity cases in both the checker and the equations;
- docs: `MERGE_EVENTS.md` (generated table), `AUTONOMOUS_MERGE.md` and
  `ARCHITECTURE.md` aligned with the rules.

## Acceptance criteria

- [x] AC-01: Scope recorded from the session requests above.
- [x] AC-02: Every event routes exactly once and resolves; undeclared events
      fail closed; invariant-breaking mutations are rejected
      (`python3 standard/conformance.py --all`, `eventMatrix`).
- [x] AC-03: A check that never ran is rejected for Validator merges and for
      owner merges without local evidence, in the checker and the equations.
- [x] AC-04: No document grants an interactive agent merge, admin bypass or
      reviewer-profile rotation.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
