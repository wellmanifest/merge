# Ticket 008: Test-driven auto-merge clause

- **ID**: ticket-008
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-18

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-09-18 the user requested unblocking autonomous PR merging across all projects, finding over-restrictive clauses in wellmanifest/*, and establishing Green Tests as Primary Truth along with KVM Reviewer Profile Switching and Token Admin Bypass.

This ticket updates `docs/AUTONOMOUS_MERGE.md` and `docs/ARCHITECTURE.md` with the Test-Driven Auto-Merge Clause and authorization to bypass manual review locks when all tests are green.

## Acceptance criteria

- [x] AC-01: Add Test-Driven Auto-Merge Clause to `docs/AUTONOMOUS_MERGE.md` and `docs/ARCHITECTURE.md`.
- [x] AC-02: Governance check passes cleanly.

## Participants

- Human participant: user via chat authorization.
- Agent participant: [ai-gemini.md](ai-gemini.md)

