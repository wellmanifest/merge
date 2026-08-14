# Autonomous merge

A decision closes when someone merges. This document says who that someone is,
what has to be true first, and why a pull request that satisfies every visible
gate can still sit open.

## Roles

| Role | May do | May never do |
| --- | --- | --- |
| Interactive agent | gather evidence, record a decision, open the pull request, request an autonomous merge | merge, approve its own work, bypass a ruleset |
| Validator identity in CI | validate at exact head, approve, merge, delete the branch | invent authority the standing policy did not grant |
| Owner | everything, including an explicit administrative override | — |

The split is not a formality. An interactive agent runs under the identity that
pushed the branch, so its approval would be a self-approval, and its merge would
be an unreviewed write to a protected branch. Sessions that try it should be
stopped by their own permission boundary — that is the guardrail working, not a
defect to route around.

`merge` therefore is not an action an interactive agent authorizes for itself.
It authorizes `request-autonomous-merge`; the validator identity authorizes and
performs `merge`.

## What must be true for a pull request to merge itself

Six conditions, in the order they fail:

1. **The protected registry enables the repository.** Its one profile names
   the allowed base branches, exact required check contexts and
   `scheduled_scan=true`. A repository without a reviewed profile is never
   scanned — by design, so that adding one is an explicit act.
2. **The scheduled plan and runtime policy are the same projection.**
   `plan-direct-scan` generates the matrix from the registry; each repository
   leg exports its scan config from those same protected bytes and verifies the
   planned registry digest before minting a target token.
3. **The ticket is derivable** from a `Ticket:` body line, a `ticket/NNN-` or
   `ticket-NNN-` branch, or the title. An unattributable pull request is never
   handed to the validator.
4. **Every required check passes at the exact head**, and the head carries no
   earlier approval at that same commit.
5. **The pull request is younger than the age bound** the scanner enforces.
6. **The standing policy is on**: the scheduled run merges only when the merge
   policy variable is set, and stays fail-closed when it is absent.

Then the target repository must actually accept the validator's review: the
ruleset's approving-review requirement has to be satisfiable by that identity,
and `delete_branch_on_merge` should be on so the branch does not become an
orphan the branch-lifecycle gate then rejects.

## Historical failure and current invariant

Before validator-agent 0.6.41, repository membership lived in a static workflow
matrix while base/check policy lived in separately maintained scan config. A
repository could sit in the matrix and be absent from that config. Its green
job then skipped the repository without failing or notifying anyone. A stale
repository variable and an inline value made that drift harder to diagnose.

The deployed runtime removes that failure class. Protected
`config/direct-pr-registry.json` is the sole repository membership, base and
required-check policy source. `plan-direct-scan` derives the job matrix from
it, runtime config is generated from it, and every leg verifies the same byte
digest. The obsolete `DIRECT_PR_SCAN_CONFIG` repository variable is absent.
Tests require the scheduled matrix projection and runtime scan projection to
contain exactly the same repositories.

Three independent policy boundaries intentionally remain:

- the protected registry profile;
- the standing execution and merge variables;
- the target repository's hosted checks, ruleset and branch settings.

They express different authority and must not be collapsed. Repository
membership is code review; standing variables enable effects in an environment;
the target ruleset decides what its protected branch accepts.

## Enablement checklist

For each repository that should merge autonomously:

- [ ] one protected registry profile with `scheduled_scan=true`, the allowed
      base and the **exact** check names the target workflow publishes, verified
      against the repository's own required-checks contract rather than copied;
- [ ] Validator App installation on the target repository, plus dependency-read
      access to `subactor/subllm`;
- [ ] branch naming that yields a ticket (`ticket/NNN-…`);
- [ ] ruleset whose approving-review requirement the validator identity can
      satisfy, with `require_last_push_approval` compatible with a bot approver;
- [ ] `delete_branch_on_merge` enabled;
- [ ] the standing scan and merge policy variables set deliberately per
      environment.

Do not add a workflow matrix row or `DIRECT_PR_SCAN_CONFIG` variable. They are
not enablement mechanisms. Copy no check subset: a subset is the same class of
defect as a hardcoded required-checks list because the gate passes while
enforcing less than it claims.

The recurring `test` and `validate` dependency setup uses a short-lived
Validator App token scoped to `subactor/skills-agent` and `subactor/subllm`.
Each scan leg separately mints its target-repository token and a SubLLM read
token. The legacy `PROJECT_TOKEN` remains only inside cross-organization
Issue/Project queue operations; exhausting its quota may fail that queue job,
but must not suppress `plan-direct-scan` or its repository legs.

## Diagnosing a stuck pull request

Use this order because it follows the execution boundary:

1. `gh pr checks <n>` — are the required checks actually green at the head?
2. `gh api repos/<repo>/pulls/<n> --jq .mergeable_state` — `blocked` means a
   ruleset requirement is unmet, usually the approving review.
3. `gh api repos/<repo>/pulls/<n>/reviews` — did the validator identity approve,
   and at which commit? An approval at an older head does not count.
4. In the scheduled run, did `plan-direct-scan` succeed and did the generated
   `scan-direct (<owner>, <name>)` leg and its artifact exist? Absence from the
   plan means the protected registry profile is absent or not scheduled.
5. Compare the planner's protected registry digest with the digest verified by
   the repository leg. Drift is a hard failure, never a skip.
6. Separate queue health from fleet health. A `validate` failure caused by
   `PROJECT_TOKEN` concerns the legacy Issue/Project queue. The independently
   planned repository legs must still run. A failed `test` prerequisite instead
   points to the Validator App dependency token or the test suite and correctly
   prevents both paths from using an unverified runtime.

The last distinction prevents the most expensive false diagnosis: a queue PAT
failure and a target merge-policy failure are no longer allowed to have the
same fleet-wide symptom. Diagnose them from named jobs and per-repository
artifacts, not from the workflow's aggregate conclusion alone.
