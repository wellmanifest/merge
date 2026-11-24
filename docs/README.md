# Merge documentation

- [MERGE_EVENTS.md](MERGE_EVENTS.md) — normative event routes and branch retention guards.
- [AUTONOMOUS_MERGE.md](AUTONOMOUS_MERGE.md) — protected review and Validator merge flow.
- [ARCHITECTURE.md](ARCHITECTURE.md) — merge decision model and evidence boundaries.
- [LOGIC_FLOW.md](LOGIC_FLOW.md) — decision flow.
- [PLAYBOOK.md](PLAYBOOK.md) — worked recovery cases.

## Decisions

- [decisions/human-manual-override-on-autonomy-failure.md](decisions/human-manual-override-on-autonomy-failure.md) — accepted: preserve authenticated human owner manual steering and direct manual merges on autonomy failure without weakening AI agent non-self-merge boundaries.
- [decisions/account-scoped-registry-admission.md](decisions/account-scoped-registry-admission.md) — proposed: three-tier protected registry admission (`repositories` > `accounts` > `account_groups`) so enrolled owner accounts onboard new repositories without manual per-repo edits.
- [decisions/owner-delegated-merge.md](decisions/owner-delegated-merge.md) — proposed (superseded for `executor: owner` by `human-manual-override-on-autonomy-failure.md`): keep Validator-only merge for AI agents and enroll repositories; owner-delegated profile recorded as an alternative.
