# Ticket 018: Standardize account-scoped and account-group Validator registry admission

- **ID**: ticket-018
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-21
- **Authorization**: `SESSION_EXECUTION_AUTHORIZATION` (user requested changing the standards and implementation of the Validator registry mechanism so new repositories under enrolled owner accounts do not require manual per-repository registry edits).

## Goal and scope

Formalize protected account-scoped and account-group default admission in `wellmanifest/merge` (`docs/AUTONOMOUS_MERGE.md`, `docs/decisions/account-scoped-registry-admission.md`, `docs/README.md`) while preserving every existing independence and fail-closed invariant (`MRG-MERGE-001`, Validator-only merge, App installation scope, exact required checks, fork exclusion, no target-authored authority).

## Acceptance criteria

- [x] AC-01: `docs/AUTONOMOUS_MERGE.md` documents the three-tier protected registry resolution order (`repositories` explicit override > `accounts` owner default > `account_groups` shared owner-group default) and its safety invariants.
- [x] AC-02: `docs/decisions/account-scoped-registry-admission.md` records the decision, alternatives, invariants, and indexing in `docs/README.md`.
- [x] AC-03: `python3 standard/conformance.py`, `python3 standard/cqrs_conformance.py`, and `./project/governance-check.sh --actor agent` pass with 0 errors.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose and raw command logs are not required delivery output.
