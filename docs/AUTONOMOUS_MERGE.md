# Autonomous merge

A decision closes when someone merges. This document says who that someone is,
what has to be true first, and why a pull request that satisfies every visible
gate can still sit open.

## Roles

| Role | May do | May never do |
| --- | --- | --- |
| Interactive agent | gather evidence, record a decision, open the pull request, request an autonomous merge | execute a merge, approve its own work, approve through another account or reviewer profile, bypass a ruleset (`--admin`, UI "bypass rules"), impersonate Owner |
| Validator identity | validate at exact head, approve, merge, retire a branch with a protected receipt | invent authority the standing policy did not grant, waive `checks-not-run` |
| Owner | set policy, resolve intent, steer work manually, and execute direct manual merge when autonomy fails/stalls or on green PRs | turn an interactive agent into a Validator or authorize AI agent self-merge |

The split prevents AI agent self-approval while keeping the human repository
owner in control. An interactive agent runs under the identity that pushed the
branch, so its approval would be a self-approval, and its merge would be an
unreviewed write to a protected branch. Approving through a second account or
browser profile does not change that: it is the same agent presenting itself as
an independent reviewer. Sessions that try it should be stopped by their own
permission boundary — that is the guardrail working, not a defect to route
around.

`merge` therefore is not an action an interactive agent authorizes for itself:
it authorizes `request-autonomous-merge`, and the Validator identity performs
autonomous `merge` after all six preconditions hold. When automation fails or
degrades (`autonomy-degraded`), an authenticated human `owner` acting directly
MAY exercise manual steering or manual `merge` (see below), whereas the model
still rejects `merge` with `executor: interactive-agent`.

This matches `RULE_MERGE_EXECUTOR_CONDITION`,
`RULE_MERGE_PRECONDITIONS_CONDITION`, and `RULE_CHECKS_NOT_RUN_CONDITION` in
`standard/merge-rules.env`, plus `MRG-MERGE-001` in `standard/conformance.py`.
Free-text prose, negated assignments such as `required-checks-green=false`, and
unstructured claims do not satisfy deterministic preconditions; the Validator
must verify real check status and exact head/base bindings before autonomous
merge, and owner overrides must carry deterministic `autonomy-degraded` and
`owner-manual-override` gate markers when checks/automation stalled.

## Human manual control and autonomy failure override

Autonomy is an assistive default, never a lock against the repository owner.

- **Fallback on degraded autonomy**: When CI, local OneDev verification,
  Validator reconciliation, rate-limit budgets, or controller pipelines fail,
  stall, time out, or reject stale pull requests (`autonomy-degraded`), the
  authenticated human owner retains full authority to steer work manually and
  execute a direct manual merge on GitHub.
- **Never revert human manual merges**: Automation, validators, and AI agents
  MUST preserve commits merged directly by an authenticated human owner (`git`
  ancestry is authoritative once merged by the owner). Do not automatically
  revert, overwrite, or reject an already-merged PR merely because automated
  Validator certification is missing; record the outcome distinctly as a
  manual-owner override (`manual-owner-override`, event
  `OWNER_MANUAL_MERGE_OBSERVED`) and retire owned clean worktrees/lifecycle
  normally on verified ancestry.
- **Strict boundary for AI agents**: This permission belongs strictly to the
  authenticated human owner. Interactive and coding AI agents still may NEVER
  run personal `gh pr merge`, self-approve, click UI merge buttons via CDP, use
  `--admin` bypass, or claim owner identity.
- **Owner-directed runtime continuation**: Separating Validator certification
  from owner authority means a manual owner merge does not forge an automated
  `Validator` proof receipt, yet explicit owner direction authorizes runtime
  reconciliation, lifecycle cleanup, and follow-up work on top of the merged
  `main`.

## Checks that never ran

A required check that was never executed — the runner was not started
because of billing or spending limits, no runner matched the label, or the
workflow was not triggered — is **not green**. It is also not a test failure.
Record it as the gate observation `required-checks-not-run` and follow event
`CHECKS_NOT_RUN` in [`MERGE_EVENTS.md`](MERGE_EVENTS.md):

- `subactor/onedev-agent` verifies the exact head merged with the current
  base and publishes `onedev/local-verify`
  (see `wellmanifest/new-project` `docs/information/local-ci-publication.md`);
- the Validator identity then validates, approves and merges
  (`LOCAL_VERIFY_GREEN`); it never counts a check that did not run;
- a repository without a OneDev profile or registry entry raises
  `REPOSITORY_NOT_ENROLLED`: the agent opens enrollment tickets and the pull
  request waits;
- the owner receives a billing notice. A local test result is diagnostic
  evidence; it never turns an unrun required context green. If a protected
  policy has migrated that context to `onedev/local-verify`, the Validator
  checks the current profile and exact-head/base receipt before merging.
  Otherwise the PR waits for the required context or a separately reviewed
  policy change.

The full catalogue of merge events and their autonomous resolutions is in
[`MERGE_EVENTS.md`](MERGE_EVENTS.md).

## What must be true for a pull request to merge itself

Six conditions, in the order they fail:

1. **The protected registry enables the repository.** A repository resolves its
   allowed base branches, exact required check contexts, and scheduled-scan flag
   from the digest-bound protected registry using three deterministic tiers (in
   precedence order):
   - an **explicit repository override** (`repositories.<owner>/<repo>`), which
     retains exact custom checks, merge method, and (when the owner policy sets
     `respect_repository_scan=true`) explicit scan opt-outs;
   - an **enrolled account policy** (`accounts.<owner>`), which covers every
     non-fork, non-archived repository under that owner without per-repository
     registry edits;
   - a **named account group** (`account_groups.<group>`), which binds one
     bounded default policy to a sorted list of enrolled owner accounts so new
     repositories under any listed owner inherit admission automatically without
     duplicating per-account boilerplate or contending on `repositories`.

   An owner may belong to at most one account policy (`accounts` and
   `account_groups` are strictly disjoint; ambiguous overlap fails closed).
   Unlisted owners, forks (unless `include_forks=true`), and archived/disabled
   repositories remain rejected fail-closed (`REPOSITORY_NOT_ENROLLED`), and
   target pull requests still grant zero merge or check authority.
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

- [ ] protected registry admission via an explicit repository profile, an
      enrolled `accounts.<owner>` policy, or a named `account_groups.<group>`
      membership naming the allowed base and the **exact** required check
      contexts verified against the repository's CI/OneDev contract (never a
      weakened subset);
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

## Rate-Limit Resilience and Browser CDP Fallback

When remote API tokens encounter GitHub rate limits (`HTTP 403: API rate limit exceeded`
or secondary rate limits) on GraphQL and REST interfaces:
1. **No Delivery Stall**: Delivery must not freeze due to token quota exhaustion.
2. **Wait, do not route around**: honour `Retry-After` / the reset time and let
   the next validator scan merge. Driving the GitHub web UI through a browser
   session to merge is an interactive-agent merge and is not permitted, and
   "bypass rules" is never an agent action.
3. **Diagnose per job**: a rate-limited queue job must not suppress the
   repository scan legs (see above).

## Automated Rebuild Pipeline for Conflicted Downstream PRs

When PRs merge into `main`, adjacent open PRs frequently transition into `mergeable: CONFLICTING`:
1. **No Premature Abandonment**: Conflicted PRs must not be summarily closed without
   verifying ticket intent.
2. **Disposition: `rebuild`**: Such PRs transition to the standard Wellmanifest `rebuild` disposition.
3. **Rebase & Semantic Reconciliation**: The agent re-synchronizes the ticket branch
   with `origin/main` (`git rebase origin/main`), resolves textual and semantic overlaps
   (e.g., reconciling centralized scan/load functions), verifies the test suite (`exit code 0`),
   and pushes to complete the merge.

## Post-Merge Lifecycle Hygiene and Worktree Pruning

Lingering worktrees and branches from merged or superseded tickets cause cascading governance
lockouts (`GOV-CONFLICT-001`, `GOV-BRANCH-LIFECYCLE-002`):
1. **Owned terminal cleanup**: A terminal ticket triggers a read-only inventory,
   not permission to delete every checkout. Bind the independently observed merge
   or authorized supersession receipt to the exact ticket, HEAD, canonical
   worktree path and branch. Confirm that the controller has released the lease,
   no process or IDE is still using that checkout, and its tracked and untracked
   contents are clean. Preserve unique history and ignored operational evidence
   in a verified recovery artifact before cleanup.
2. **Ordinary Git removal**: Remove only that owned, verified worktree with
   `git worktree remove <exact-path>`. Then remove its released local branch only
   after verifying reachability from the published target. Observe remote branch
   retirement separately through the protected delivery receipt. Forced removal,
   broad pruning and deleting unknown registrations are not automatic remedies.
3. **Unknown or active state**: Preserve dirty, leased, actively used and legacy
   checkouts as read-only recovery inventory. Record the exact blocker and next
   observable action; do not waive concurrency or ownership controls. Run the
   adopted workspace lifecycle checker through Goal for the terminal audit.
