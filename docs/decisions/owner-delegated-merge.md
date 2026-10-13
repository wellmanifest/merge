---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "owner-delegated-merge",
  "kind": "decision",
  "version": 1,
  "title": "Owner-delegated merge for repositories outside the Validator registry",
  "status": "proposed",
  "owner": "wellmanifest/merge",
  "created": "2026-10-13",
  "updated": "2026-10-13",
  "review_after": "2026-10-27",
  "source_revision": "bf4a8df21a0ad4ef7c6b72446550728b4a4b433d",
  "affected_repositories": [
    "wellmanifest/merge"
  ],
  "evidence": [
    "repo://wellmanifest/merge/docs/AUTONOMOUS_MERGE.md",
    "repo://wellmanifest/merge/standard/merge-rules.env",
    "repo://wellmanifest/merge/standard/conformance.py",
    "https://github.com/wellmanifest/data-plane/pull/9",
    "https://github.com/wellmanifest/data-plane/pull/10"
  ]
}
---

# Owner-delegated merge for repositories outside the Validator registry

<!-- docs:section purpose -->
## Purpose

Record the owner's request to let delivery reach `main` without the owner
running `gh pr merge` by hand. Compare it with the current rule and pick the
option the standard should adopt. This record is `proposed`. It changes no rule,
conformance code or host instruction, and grants no merge authority to anyone.

<!-- docs:section context -->
## Context

**Facts.**

- Who may merge is fixed by `docs/AUTONOMOUS_MERGE.md` (Roles),
  `RULE_MERGE_EXECUTOR_CONDITION=!@FACT_AUTHORIZES_MERGE||@FACT_EXECUTOR==:AUTOMATED_VALIDATOR`
  in `standard/merge-rules.env`, and `MRG-MERGE-001` in
  `standard/conformance.py`. Only the automated Validator executes a merge.
  An owner instruction does not turn an interactive agent into a Validator.
  The model also rejects `executor: owner`.
- The Validator scans only repositories that have a reviewed profile in
  protected `config/direct-pr-registry.json` (subactor/validator-agent).
- wellmanifest/data-plane and wellmanifest/data-gateway are not in that
  registry. During 2026-10-12 and 2026-10-13 every data-plane PR (#1–#8) was
  merged by the owner from the terminal after the agent opened it. Governance
  adoption PR #9 and docs-pin PR #10 are waiting in the same way.
- On 2026-10-12 the owner asked the agent why it does not merge on its own,
  then asked for both enrollment (a) and a change to the rule (b).

**Hypothesis.** Most of the manual merges disappear after enrollment. The
remaining friction is in repositories that cannot run the Validator: no App
installation and no satisfiable ruleset.

<!-- docs:section options -->
## Options

**A. Keep Validator-only and enroll the repositories (recommended).**
Each repository adopts the governance package, receives a registry profile with
exact required checks, installs the Validator App, sets a ruleset its review can
satisfy, and turns on `delete_branch_on_merge`. Nothing in the standard changes.
Cost: one-time owner admin actions per repository plus a registry PR reviewed
in subactor/validator-agent.

**B. Owner-delegated profile.** A new executor value, for example
`owner-delegated`, would be admissible only when all of these hold:

- a per-repository standing delegation signed by the owner names the repository,
  base branch, ticket workstreams and expiry;
- every required check is green at the exact frozen head;
- the delegated executor merges through the server-side merge API, never with
  `--admin` or bypass;
- a protected audit receipt binds head, base, checks and delegation digest;
- the owner can revoke the delegation at any time, and the next run refuses
  when it is revoked or expired.

Cost: new grammar value, new rule equation, new `MRG-*` adversarial mutations,
and changes to `AUTONOMOUS_MERGE.md` and the workspace host instructions. Each
of those needs its own ticket and owner review. The scheme also weakens the
independence guarantee: the identity that wrote the change could publish it,
with only automated checks between.

**C. Status quo.** The owner keeps merging repositories that are not enrolled.
No cost to the standard. The friction stays.

<!-- docs:section decision -->
## Decision

Proposed: **A**. B stays as a documented alternative. It is reconsidered only if
some repository cannot satisfy enrollment, and then only through the separate
reviewed tickets listed above. Until this record is `accepted` by the owner,
the current rule applies unchanged.

<!-- docs:section consequences -->
## Consequences

- With A, the independence boundary stays intact. The work moves to enrollment:
  - data-plane: PR #9 governance, PR #10 docs pin, the variable
    `NEW_PROJECT_RUNTIME_SHA`;
  - data-gateway: the same adoption;
  - a registry profile in subactor/validator-agent;
  - App installation, ruleset and branch settings by the owner.
- Accepting B would make `merge` with an executor other than the Validator
  admissible. Every consumer of `MRG-MERGE-001` and every host `AGENTS.md`
  that repeats the actor boundary would need coordinated updates.
- With C, nothing changes and the owner keeps the merge step.

<!-- docs:section limitations -->
## Limitations

No controller lease was issued for ticket-015. The record is written in the
canonical worktree without one, and this is recorded as a gap. The record does
not measure how many repositories cannot be enrolled, so it does not test the
hypothesis above.
