# Ticket 019: Allow human owner manual merge and override on autonomy failure

- **ID**: ticket-019
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-24
- **Authorization**: `SESSION_EXECUTION_AUTHORIZATION` (user explicitly instructed not to revert personal merges made when automation failed, to allow human merging, and to update Wellmanifest standards to account for autonomy failures and permit manual control).

## Goal and scope

Update `wellmanifest/merge` (`standard/merge-rules.env`, `standard/merge-events.env`, `standard/merge-decision.schema.json`, `standard/merge_contracts.py`, `standard/merge_dsl_events.py`, `standard/merge_adversarial.py`, `docs/AUTONOMOUS_MERGE.md`, `docs/MERGE_EVENTS.md`, `docs/decisions/human-manual-override-on-autonomy-failure.md`, `docs/README.md`, `error/MRG-MERGE-001.md`) so the standard preserves independent automated-validator boundaries for AI agents while permitting an authenticated human repository owner to steer work manually and perform direct manual merges when autonomy fails or degrades — without auto-reverting earlier manual owner merges.

## Acceptance criteria

- [x] AC-01: `standard/merge-rules.env`, `standard/merge-events.env`, `standard/merge_contracts.py`, `standard/merge_dsl_events.py`, and `standard/merge_adversarial.py` permit `executor=owner` direct merge with full preconditions or declared `autonomy-degraded` + `owner-manual-override` gate evidence while still rejecting `interactive-agent` self-merge and unverified `checks-not-run` Validator merges.
- [x] AC-02: `docs/AUTONOMOUS_MERGE.md`, `docs/MERGE_EVENTS.md`, `docs/decisions/human-manual-override-on-autonomy-failure.md`, `docs/README.md`, and `error/MRG-MERGE-001.md` document human manual control, autonomy-failure override, and preservation of manual owner merges.
- [x] AC-03: `python3 standard/conformance.py --all`, `python3 standard/cqrs_conformance.py`, `./project/governance-check.sh --actor agent`, and `wellman check` exit 0 with 0 errors.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
