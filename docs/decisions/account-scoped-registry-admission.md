---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "account-scoped-registry-admission",
  "kind": "decision",
  "version": 1,
  "title": "Account-scoped and account-group default admission in the Validator registry",
  "status": "proposed",
  "owner": "wellmanifest/merge",
  "created": "2026-11-21",
  "updated": "2026-11-21",
  "review_after": "2026-12-05",
  "source_revision": "04d5c4839277063c86bec2a40f71a4d8791c91f4",
  "affected_repositories": [
    "wellmanifest/merge",
    "subactor/validator-agent"
  ],
  "evidence": [
    "repo://wellmanifest/merge/docs/AUTONOMOUS_MERGE.md",
    "repo://wellmanifest/merge/docs/decisions/owner-delegated-merge.md",
    "repo://wellmanifest/merge/standard/merge-rules.env"
  ]
}
---

# Account-scoped and account-group default admission in the Validator registry

<!-- docs:section purpose -->
## Purpose

Eliminate repetitive manual per-repository edits to the protected Validator
registry whenever the owner creates a new repository inside an already governed
organization, without weakening independent Validator review, exact-head merge
authority, or fail-closed check enforcement.

<!-- docs:section context -->
## Context

**Facts.**

- `owner-delegated-merge.md` kept Validator-only merge (`MRG-MERGE-001`) so the
  interactive coding agent never merges or approves its own branch under the
  owner's personal GitHub token.
- In `subactor/validator-agent`, `config/direct-pr-registry.json` already
  supports account-level defaults under `accounts` (deployed for `clonerd-com`,
  `maskservice`, and `wellmanifest`), yet most owner organizations (`semcod`,
  `subactor`, `heyasa`, `autogrammar`, `dockuri`, `uritime`, `emllm`, etc.)
  still rely on hundreds of explicit per-repository entries under
  `repositories`.
- Every newly created repository in those organizations blocks on
  `REPOSITORY_NOT_ENROLLED` / `PUBLICATION_PROFILE_MISSING` and forces a manual
  PR editing the single shared `config/direct-pr-registry.json`, causing
  serialized lease contention across unrelated workstreams.

<!-- docs:section options -->
## Options

**A. Per-repository explicit entries only (status quo).**
Every new repository needs its own registry PR before Validator can review or
merge it. High operational friction and constant scope contention on the shared
registry file.

**B. Self-merge by author / interactive agent.**
Removes registration friction by letting the author's interactive agent merge.
Rejected because it violates `MRG-MERGE-001` and collapses the actor boundary
between code writer and independent validator.

**C. Three-tier protected registry admission (`repositories` > `accounts` > `account_groups`) (recommended).**
Keep the protected, digest-bound registry as the sole authorization source and
standardize three deterministic tiers:

1. `repositories.<owner>/<repo>`: explicit per-repository override (custom
   checks, merge method, or explicit `scheduled_scan: false` pause when
   `respect_repository_scan=true`).
2. `accounts.<owner>`: explicit single-owner default policy.
3. `account_groups.<group>`: optional named policy template shared across a
   sorted list of enrolled owner accounts (`owners: [...]`) sharing the same
   verification contract (for example, `onedev/local-verify` vs hosted
   governance checks).

Invariants enforced fail-closed by the registry loader:

- An owner may appear in at most one account policy (overlap between two
  `account_groups`, or between `accounts` and `account_groups`, is rejected).
- Unlisted owners remain rejected (`direct_pr_registry_target_unknown` /
  `REPOSITORY_NOT_ENROLLED`).
- Forks (`include_forks=false` default), archived, and disabled repositories
  are excluded from discovery.
- Group-level entries cannot set `merge_method` or recovery
  `published_merge_status_producer` overrides; those stay explicit per
  repository.
- Required checks (`onedev/local-verify` or exact hosted contexts) and exact
  Validator App installation scope remain mandatory before approval or merge.

<!-- docs:section decision -->
## Decision

Adopt **Option C** in `docs/AUTONOMOUS_MERGE.md` and implement optional
`account_groups` in `subactor/validator-agent` (`DirectPrRegistry`).

<!-- docs:section consequences -->
## Consequences

- Once an owner organization is enrolled in `accounts` or an `account_groups`
  group, newly created repositories under that owner immediately inherit the
  bounded verification and base-branch policy without per-repository registry
  PRs or lock contention on `repositories`.
- All existing per-repository profiles remain exact overrides; backward
  compatibility with registries omitting `account_groups` is preserved.
- Independent Validator review (`MRG-MERGE-001`), exact-head check verification,
  and OneDev local verification remain completely intact.

<!-- docs:section limitations -->
## Limitations

- Adding an owner account to `accounts` or `account_groups` still requires one
  independently reviewed change in `subactor/validator-agent` and deployment of
  the updated registry pin.
- Repositories whose inherited policy requires `onedev/local-verify` still need
  OneDev verification coverage (either an explicit OneDev profile or an
  account-level OneDev runner default) before `onedev/local-verify` turns green.
