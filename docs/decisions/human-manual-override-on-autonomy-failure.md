---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "human-manual-override-on-autonomy-failure",
  "kind": "decision",
  "version": 1,
  "title": "Human manual control and merge override on autonomy failure",
  "status": "accepted",
  "owner": "wellmanifest/merge",
  "scope": "repository",
  "created": "2026-11-24",
  "updated": "2026-11-24",
  "review_after": "2026-12-24",
  "source_revision": "a0cefaf5b9a184cd993d23c8d0d9ad50ec419624",
  "affected_repositories": [
    "wellmanifest/merge"
  ],
  "evidence": [
    "repo://wellmanifest/merge/docs/AUTONOMOUS_MERGE.md",
    "repo://wellmanifest/merge/docs/MERGE_EVENTS.md",
    "repo://wellmanifest/merge/standard/merge-rules.env",
    "repo://wellmanifest/merge/standard/conformance.py",
    "https://github.com/subactor/autonom/pull/228",
    "https://github.com/heyasa/heyasa/pull/1080"
  ]
}
---

# Human manual control and merge override on autonomy failure

<!-- docs:section context -->
## Context

Earlier `wellmanifest/merge` rules (`merge-rules.env`, `merge-events.env`, `MRG-MERGE-001`) rejected `executor: owner` alongside `executor: interactive-agent` and treated personal owner merges during automation failures as non-authoritative or blocking runtime progression. In production incidents on 2026-11-24 (`subactor/autonom#228`, `heyasa/heyasa#1080`, `#1081`, `#1083`, `#1085`), stalled OneDev queues, controller timeouts, and Validator backlog forced the human repository owner to perform direct manual merges to restore delivery. Reverting those manual merges destroys owner recovery work, while letting AI agents self-merge under the owner account would collapse the independent-validator guardrail.

<!-- docs:section evidence -->
## Evidence

- `standard/merge-rules.env` previously encoded `RULE_MERGE_EXECUTOR_CONDITION` with `@FACT_EXECUTOR==:AUTOMATED_VALIDATOR` only and failed even explicit `owner` recovery decisions in `standard/merge_adversarial.py`.
- `standard/merge-events.env` had no event modeling owner manual intervention on degraded autonomy (`AUTONOMY_DEGRADED_MANUAL_OVERRIDE`) or clean lifecycle preservation when an authenticated human owner merges directly (`OWNER_MANUAL_MERGE_OBSERVED`).
- Live operations demonstrated `onedev/local-verify` queue latency and `subactor/autonom` repair deadlocks leaving human manual merges on `main` while strict rules flagged them as blocking continuation.

<!-- docs:section alternatives -->
## Alternatives

1. **Revert personal owner merges and force re-submission through Validator**: Rejected because it punishes human incident recovery, introduces unnecessary merge churn, and blocks urgent fixes whenever automation itself is degraded.
2. **Allow AI coding agents to merge directly on failure**: Rejected because interactive agents run under the authoring identity and must never self-approve, run personal `gh pr merge`, or impersonate the human owner.
3. **Preserve authenticated human owner control and manual merge override on degraded autonomy (adopted)**: Allow `executor: owner` with full preconditions or explicit `autonomy-degraded` + `owner-manual-override` markers, preserve existing manual owner merges without auto-reverting, and keep `interactive-agent` fail-closed.

<!-- docs:section decision -->
## Decision

Adopt Option 3 across `standard/merge-rules.env`, `standard/merge-events.env`, `standard/merge_contracts.py`, `standard/merge_dsl_events.py`, `standard/merge_adversarial.py`, `docs/AUTONOMOUS_MERGE.md`, `docs/MERGE_EVENTS.md`, and `error/MRG-MERGE-001.md`. Authenticated human owner merges are preserved permanently on `main`, recorded distinctly from automated Validator proof as `manual-owner-override`, and never reverted automatically; AI agents remain barred from merging.

<!-- docs:section consequences -->
## Consequences

- `owner` merges with full green preconditions or declared `autonomy-degraded` + `owner-manual-override` deterministic gate markers pass schema, Python contract, and Env DSL conformance.
- `interactive-agent` merge attempts remain rejected (`MRG-MERGE-001`), even if `autonomy-degraded` is present.
- `automated-validator` continues to require all six green preconditions and still rejects `checks-not-run`.
- `wellmanifest/autonomy` and downstream host/governance policies can align runtime deployment and lifecycle retirement with explicit owner manual override receipts.

<!-- docs:section validation -->
## Validation

Verified via `python3 standard/conformance.py --all`, `python3 standard/cqrs_conformance.py`, `./project/governance-check.sh --actor agent`, `wellman check`, and `wellmanifest/docs/docs/standard/check.py --deliverable docs/decisions/human-manual-override-on-autonomy-failure.md`.

<!-- docs:section supersedes -->
## Supersedes

Refines and supersedes the earlier `owner` executor prohibition in [decisions/owner-delegated-merge.md](owner-delegated-merge.md) while keeping Validator-only execution intact for AI agents.
