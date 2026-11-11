# Ticket 016: Modularize and harden merge decision and CQRS conformance

- **ID**: ticket-016
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

Modularize `standard/conformance.py` (960 lines) and compact `standard/cqrs_conformance.py` (536 lines) so all owned Python modules stay strictly below 500 lines (preserving digest-pinned `standard/env_dsl.py`), and harden validation against omitted optional `headRevision` `KeyError` crashes, `bool`-as-`int` acceptance, unhashable list item `TypeError` crashes, missing JSON Schema field/length/timestamp parity checks, inline bearer/private-key secret values, duplicate JSON keys, and symlink traversal.

## Acceptance criteria

- [x] AC-01: `python3 standard/conformance.py --all`, `python3 standard/cqrs_conformance.py --all`, `./project/governance-check.sh --base origin/main`, and `wellman check` pass with all owned modules `< 500` lines.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
