# Merge events and autonomous resolutions

Each declared situation a pull request can reach on its way to `main` is a
closed **event** with one governed resolution. The normative source is
[`standard/merge-events.env`](../standard/merge-events.env) (Env DSL); this
table is generated from the same list and `standard/conformance.py` fails when
they diverge.

## Actors

| Actor | Identity | May |
| --- | --- | --- |
| `INTERACTIVE_AGENT` | the coding agent that pushed the ticket branch | change the ticket branch, open the pull request, request an autonomous merge, open enrollment tickets |
| `ONEDEV_AGENT` | `subactor/onedev-agent` | verify the exact head merged with the current base (`onedev/local-verify`), consolidate duplicate or superseded tickets, retire merged work by lifecycle |
| `VALIDATOR_AGENT` | `subactor/validator-agent` App identity | validate at the exact head, approve, merge |

The owner is never an execution actor in this matrix. `NOTIFY=OWNER` is an
out-of-band notice, not authority to delete or merge. For a closed unmerged PR,
OneDev preserves the branch autonomously; discarding it later requires the
owner's explicit decision after intent reconciliation. The interactive agent
never merges and never asks a human whether to merge.

## How to resolve

1. Observe every event that currently holds for the pull request.
2. Resolve the one with the highest priority first; set `FACT_EVENT` to it.
3. Exactly one `ROUTE_<EVENT>_CONDITION` is true and `EVENT_RESOLVED_CONDITION`
   holds. An undeclared event fails closed: add it to the matrix first.
4. The actor performs the action; the pull request moves to the next state.
   Observe again.

`ORPHAN_BRANCH` means a branch left after a verified merge. Its route requires
`FACT_PROTECTED_MERGE_RECEIPT_MATCHES_BRANCH=TRUE`, supplied by a protected
controller after binding the merge receipt to the exact branch. Without that
receipt, cleanup fails closed. A PR closed without merge uses
`CLOSED_UNMERGED_PR` and keeps its branch while the owner decides whether to
discard the unmerged work.

## Matrix

| Priority | Event | Meaning | Actor | Action | Next state | Notify |
| ---: | --- | --- | --- | --- | --- | --- |
| 100 | `BYPASS_REQUESTED` | Someone asks an agent to self-merge, use `--admin`, rotate reviewer profiles or press "bypass rules". | `INTERACTIVE_AGENT` | `REFUSE_AND_REQUEST_AUTONOMOUS_MERGE` | `AWAITING_VALIDATOR` | `NONE` |
| 99 | `SECRET_DETECTED` | A secret is in the diff or history. Removal is autonomous; rotation is the owner's out-of-band task. | `INTERACTIVE_AGENT` | `REMOVE_SECRET_REBUILD_BRANCH_AND_PUSH` | `CHANGES_REQUIRED` | `OWNER` |
| 96 | `FOREIGN_DIRTY_CHECKOUT` | The primary checkout holds unknown or someone else's uncommitted work. | `INTERACTIVE_AGENT` | `PRESERVE_AND_USE_LINKED_WORKTREE` | `DRAFT` | `NONE` |
| 92 | `REPOSITORY_NOT_ENROLLED` | The repository has no protected registry profile or OneDev verification profile. | `INTERACTIVE_AGENT` | `OPEN_ENROLLMENT_TICKETS_IN_VALIDATOR_AND_ONEDEV` | `AWAITING_ENROLLMENT` | `NONE` |
| 88 | `INTENT_SCOPE_VIOLATION` | The diff leaves the ticket's `allowedPaths` or workstream ownership. | `INTERACTIVE_AGENT` | `RETURN_TO_PLAN_AND_AMEND_INTENT` | `REPLANNING` | `NONE` |
| 86 | `BUDGET_EXCEEDED` | The diff exceeds the delivery budget (`GOV-BUDGET-001`). | `INTERACTIVE_AGENT` | `SPLIT_INTO_DEPENDENT_TICKETS` | `REPLANNING` | `NONE` |
| 82 | `CHECKS_NOT_RUN` | Hosted required checks never executed (billing, spending limit, no runner). Not green and not failed. | `ONEDEV_AGENT` | `RUN_LOCAL_VERIFY_ON_EXACT_MERGE_RESULT` | `AWAITING_LOCAL_VERIFY` | `OWNER` |
| 80 | `GOVERNANCE_FAILED` | The governance gate reports `GOV-*` findings. | `INTERACTIVE_AGENT` | `APPLY_DIAGNOSTIC_RUNBOOK` | `CHANGES_REQUIRED` | `NONE` |
| 76 | `MERGE_CONFLICT` | The pull request no longer merges cleanly into the current base. | `INTERACTIVE_AGENT` | `REBUILD_REBASE_RETEST_AND_PUSH` | `AWAITING_CHECKS` | `NONE` |
| 74 | `CHANGES_REQUESTED` | The Validator review requests changes. | `INTERACTIVE_AGENT` | `ADDRESS_FINDINGS_ON_TICKET_BRANCH` | `CHANGES_REQUIRED` | `NONE` |
| 72 | `CHECKS_FAILED` | A required hosted check ran and failed. | `INTERACTIVE_AGENT` | `FIX_ON_TICKET_BRANCH_AND_PUSH` | `AWAITING_CHECKS` | `NONE` |
| 70 | `LOCAL_VERIFY_FAILED` | `onedev/local-verify` ran and failed. | `INTERACTIVE_AGENT` | `FIX_ON_TICKET_BRANCH_AND_PUSH` | `AWAITING_LOCAL_VERIFY` | `NONE` |
| 62 | `SCOPE_RESERVED` | Another active ticket reserves the requested scope. | `INTERACTIVE_AGENT` | `SERIALIZE_AFTER_OWNING_TICKET` | `SERIALIZED` | `NONE` |
| 58 | `DUPLICATE_WORK` | The same outcome is already delivered or tracked (`already-implemented`). | `ONEDEV_AGENT` | `CONSOLIDATE_SHARED_TICKETS_WITH_RECEIPT` | `CLOSED` | `NONE` |
| 56 | `SUPERSEDED` | A newer change replaces this pull request (`superseded`). | `ONEDEV_AGENT` | `CONSOLIDATE_SUPERSEDED_WITH_RECEIPT` | `CLOSED` | `NONE` |
| 50 | `PR_OPENED` | The ticket branch is pushed and the pull request exists. | `INTERACTIVE_AGENT` | `REQUEST_AUTONOMOUS_MERGE` | `AWAITING_CHECKS` | `NONE` |
| 46 | `STALE_PULL_REQUEST` | The pull request is older than the scanner's age bound. | `ONEDEV_AGENT` | `REBUILD_OR_DEFER_BY_INTENT_DELTA` | `AWAITING_CHECKS` | `NONE` |
| 40 | `CHECKS_PENDING` | Required checks are queued or running at the exact head. | `VALIDATOR_AGENT` | `WAIT_FOR_EXACT_HEAD_CHECKS` | `AWAITING_CHECKS` | `NONE` |
| 34 | `HEAD_CHANGED` | The head moved while validation was running. | `VALIDATOR_AGENT` | `START_NEW_EXACT_HEAD_EPOCH` | `AWAITING_CHECKS` | `NONE` |
| 32 | `BASE_ADVANCED` | The base branch advanced; the pull request still merges cleanly. | `VALIDATOR_AGENT` | `VERIFY_MERGE_RESULT_AGAINST_CURRENT_BASE` | `AWAITING_CHECKS` | `NONE` |
| 24 | `VALIDATOR_UNAVAILABLE` | The Validator workflow cannot be dispatched or does not start. | `ONEDEV_AGENT` | `QUEUE_REDISPATCH_WITH_BACKOFF_AND_OPEN_INCIDENT` | `AWAITING_VALIDATOR` | `OWNER` |
| 20 | `RATE_LIMITED` | GitHub API quota is exhausted for the scanning identity. | `VALIDATOR_AGENT` | `WAIT_RETRY_AFTER_THEN_RESCAN` | `AWAITING_VALIDATOR` | `NONE` |
| 16 | `CLOSED_UNMERGED_PR` | A PR closed without merge still has its ticket branch; its intent needs reconciliation. | `ONEDEV_AGENT` | `PRESERVE_BRANCH_AND_RECONCILE_INTENT` | `AWAITING_OWNER_DECISION` | `OWNER` |
| 15 | `ORPHAN_BRANCH` | A branch remains after a protected merge receipt identifies it. | `ONEDEV_AGENT` | `PRUNE_WITH_RECOVERY_RECEIPT` | `CLOSED` | `NONE` |
| 12 | `LOCAL_VERIFY_GREEN` | `onedev/local-verify` is green on the exact head merged with the current base. | `VALIDATOR_AGENT` | `VALIDATE_APPROVE_AND_MERGE_EXACT_HEAD` | `MERGED` | `NONE` |
| 10 | `CHECKS_GREEN` | Every required check passed at the exact head. | `VALIDATOR_AGENT` | `VALIDATE_APPROVE_AND_MERGE_EXACT_HEAD` | `MERGED` | `NONE` |
| 5 | `MERGED` | The merge is read back on the base branch. | `ONEDEV_AGENT` | `RELEASE_SCOPE_AND_RETIRE_WORKTREE_BY_LIFECYCLE` | `CLOSED` | `NONE` |

## Invariants

The equations in `merge-events.env` prove, and conformance re-checks:

- only `VALIDATOR_AGENT` leads to `MERGED`;
- no event has the owner as its actor;
- every resolution is autonomous;
- every event routes exactly once and priorities are unique, so concurrent
  events are ordered deterministically;
- an undeclared event is not resolved.
- an unmerged branch is preserved; merged-branch cleanup requires a matching
  protected merge receipt and a recovery receipt.

`merge-rules.env` keeps the decision-level rules: an interactive agent never
authorizes `merge`, and a check that never ran (`required-checks-not-run`)
is not green.
