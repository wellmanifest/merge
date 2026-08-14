---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-003
---
# Participant: codex (AI agent)

## Understanding

The existing autonomous-merge guide records the historical failure accurately
but has become false after the fix: it still requires both a workflow matrix
and scan-config entry, names a repository variable plus inline literal, and
lists repositories that the protected registry already scans. Leaving that
text in the maintained standard would instruct operators to recreate the same
dual-source defect.

The authoritative runtime now derives both the scheduled matrix and exact
base/check config from one reviewed registry and verifies its digest in each
leg. Version 0.6.43 additionally removes the shared queue PAT from the `test`
prerequisite and `validate` dependency setup. A real cron-owned merge is still
required to distinguish configuration correctness from another successful
manual dispatch.

## Execution plan

1. Record the one-file bounded integration intent from current `main`.
2. Rewrite the historical failure and enablement sections around the protected
   single registry and repository-scoped App tokens.
3. Run the standard conformance suite and managed governance gate.
4. Open one attributable PR with both hosted checks green.
5. Do not dispatch it. Observe a `schedule` run that generates the
   `wellmanifest/merge` leg and lets the Validator App review and merge it.
6. Record exact run, job, PR head, review and merge evidence from integrated
   `main` before terminal ticket closure.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- No implementation file has been changed before recording this plan.
- Replaced the historical four-list contract with the deployed protected
  registry, generated plan/runtime projection and digest check.
- Updated enablement and diagnosis around repository-scoped App tokens,
  standing policy variables and target rulesets.
- Recorded that the legacy queue PAT is isolated from the scheduled fan-out.
- The conformance suite and managed gate pass; the ticket remains
  `IN_PROGRESS / PUBLICATION` until a real schedule event merges the canary PR.
- The first hosted remote-lifecycle attempt exposed ticket-004's retained
  branch after its implementation PR was closed. Without editing that ticket,
  the branch was attached to draft PR #7; draft PRs preserve ownership while
  validator-agent deterministically skips them.
- Scheduled run `31839610022` generated and completed the
  `scan-direct (wellmanifest, merge)` leg without a manual dispatch. The report
  bound registry digest `4910fa6c…`, exact head `ec877d8…`, ticket-003 and the
  stable correlation ID, then recorded App approval and explicit merge.
- The protected process merged PR #5 as `9060008…` and deleted its branch. All
  acceptance criteria now have deterministic repository or GitHub API evidence.

## Blockers

- None. The ticket is complete on integrated `main`.
