# Autonomous merge

A decision closes when someone merges. This document says who that someone is,
what has to be true first, and why a pull request that satisfies every visible
gate can still sit open forever.

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

1. **The repository is in the validator's scan matrix.** A job exists for it.
2. **The repository has a scan-config entry** naming its required check names and
   allowed base branches. A repository without an entry is never scanned — by
   design, so that adding one is an explicit act.
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

## The failure this document exists for

Those conditions live in **four separate places** that must agree, and nothing
reconciles them:

- the workflow's repository matrix;
- the scan configuration (both a repository variable and an inline literal
  exist; different jobs read different ones);
- the standing policy variables;
- the target repository's ruleset and branch settings.

A repository can sit in the matrix and be absent from the scan config. Then a
job runs, finds no entry, and skips it — with green checks, an approving
reviewer configured, and no error anywhere. The pull request simply never
merges, and nobody is told why.

That is not hypothetical. At the time of writing, `wellmanifest/twin-lifecycle`,
`subactor/doctor-agent` and `subactor/intent-contract-dsl-runtime` are in the
matrix with no scan-config entry, and `wellmanifest/merge` — this repository —
is in neither.

## Enablement checklist

For each repository that should merge autonomously:

- [ ] matrix entry in the validator workflow;
- [ ] scan-config entry with the **exact** check names the workflow publishes,
      verified against the repository's own required-checks contract rather than
      copied;
- [ ] branch naming that yields a ticket (`ticket/NNN-…`);
- [ ] ruleset whose approving-review requirement the validator identity can
      satisfy, with `require_last_push_approval` compatible with a bot approver;
- [ ] `delete_branch_on_merge` enabled;
- [ ] the standing merge policy variable set, deliberately, per environment.

Copy nothing. A subset of check names is the same class of defect as a hardcoded
required-checks list: the gate passes while enforcing less than it claims.

## Diagnosing a stuck pull request

In this order, because that is the cost order:

1. `gh pr checks <n>` — are the required checks actually green at the head?
2. `gh api repos/<repo>/pulls/<n> --jq .mergeable_state` — `blocked` means a
   ruleset requirement is unmet, usually the approving review.
3. `gh api repos/<repo>/pulls/<n>/reviews` — did the validator identity approve,
   and at which commit? An approval at an older head does not count.
4. Is the repository in both the matrix and the scan config?
5. Did the validator run at all, or is the fleet failing for an unrelated
   reason — an exhausted shared API quota fails every agent at once and looks
   exactly like a merge policy problem.

Step 5 is the one that wastes the most time. A shared personal token is a single
point of failure for every scheduled agent; when its quota is gone, merges,
approvals and health checks stop together.
