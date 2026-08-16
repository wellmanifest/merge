# Playbook: five decisions, and what each one cost to make

Every case below is real, from a single day of cleanup across `subactor/*` and
`wellmanifest/*`. The point of recording them is that the cheap evidence and the
expensive evidence are not the ones you expect.

## 1. Orphaned branch, live intent → `rebuild`

`subactor/intent-contract-dsl-runtime`, branch `fix/ticket-037-managed-eol`:
5 commits, 9 behind, no pull request, one day idle.

| Evidence | Producer | Observation |
| --- | --- | --- |
| `intent-delta` | todo2code | trend mixed; alignment flat 11.5%; implemented 14.1% → 13.9%; gaps 430 → **439** |
| `content-identity` | git | 0 of 32 changed files already present on the target |
| `gate-outcome` | gate | `GOV-FAIL`: 4 errors |
| `history-shape` | git | intent and implementation in one commit; `.gitattributes` owned by no workstream |

The intent-delta looked bad at first glance — implemented percentage *down*,
gaps *up*. It was not a regression: the branch recorded four backlog tickets, so
declared intent rose without implementation. That is the signature of a backlog
change and it is why the number moves the wrong way for the right reason.

What decided it was the target's own text: `TODO.md` on `main` still described
all four items as open, and `main`'s `.gitattributes` still lacked the LF rules
whose absence caused `GOV-SYNC-001` on Windows. Nothing was already done.

Rebuild, not adopt, because the gate rejected the delivery: no bounded delivery
contract, intent not committed before its implementation, and a file owned by no
workstream. The fix was structural — plan-first ordering, ownership added to the
governance workstream, original authorship preserved on content commits.

Result: PR opened, all four required checks green. It also repaired a default
branch that had been red for an unrelated formatting failure.

## 2. Staged tree that duplicated the target → `already-implemented`

`subactor/platform`, 40 staged files from a governance adoption re-run.

The decisive evidence was boring and complete: a per-file comparison found
**39 of 40 byte-identical** to `main`, which had already adopted the same
package revision. No intent analysis was needed for those 39.

## 3. The fortieth file → `regressive`

The one file that differed was `.governance/manifest.json`, and it differed
downward: the freshly generated version dropped a `deployment` workstream and
two ownership entries the repository had added by hand.

This is the case that justifies a separate disposition. "Not identical" is not
"newer". A generator that re-emits a customized file at its base form produces a
diff that looks like work and behaves like a rollback.

Discarding it was destructive against an unrecoverable shape, so the decision
carried `patch:` recovery — `git diff --cached` written to a file first. A
branch tip would not have been enough; a staged tree does not exist in git once
it is restored away.

## 4. A commit already delivered under another name → `superseded`

`subactor/platform`, `feat/subactor-saas-deployment-binding`, one commit ahead.

`git cherry -v origin/main <branch>` marked it `+` — patch not upstream. That
was misleading: `main` had received the same intent through ticket-014 under a
different revision, with the file since evolved further. The `+` reflects patch
text, not delivered intent.

`superseded` therefore requires naming the replacing revision. Here that was the
ticket-014 commit, and the evidence that closed it was the target's own file
already containing the binding the branch wanted to add.

## 5. Someone else's unpushed commit → `adopt`, by cherry-pick

`wellmanifest/twin-lifecycle` had a local, unpushed commit adding a CI workflow
that ran the conformance suite — authored by the repository owner, not by the
agent doing the cleanup.

The tempting move is to write an equivalent workflow. That produces two
competing files and quietly erases someone's authorship. The correct move was to
cherry-pick it, preserving the author, and add one commit on top repinning its
actions to the revisions the adopted governance workflow already used.

Two lessons worth keeping:

- **Check who wrote it before deciding what it is.** Two separate sessions in
  this day misattributed a commit to each other; `git log -1 --format='%an %ae'`
  settles it in one call and prevents both "I'll clean up my mess" and "not
  mine, leave it".
- **Publishing another party's uncommitted work is their call, not yours.** The
  session that found it correctly refused to push it and said so.

## 6. Backlog that should not become work → `defer`

The four tickets the orphaned branch created (`039`-`042`) were left as
`BACKLOG / PLAN`. They reserve no workstream, so they block nothing, and the
disposition may authorize only effect-free actions.

## Cost ordering, in practice

1. `git` per-file identity and `merge-base` — seconds, and they resolve most
   cases outright.
2. The target repository's own gate — seconds, and it converts "should we take
   this?" into "in what shape?".
3. `t2c compare-workspace` — a minute or two, and it is the right tool for
   *is this addition, restatement or staleness*, not for go/no-go.
4. `code2llm` / `deconnected` — reach for these only when the question is
   whether the code or the referenced surface is still alive; they are the only
   honest way to support `obsolete`.

Reaching for the expensive tools first is the common failure. The intent graph
tells you the shape of a change; it does not tell you whether the change is
already in the file you are looking at.

## 6. Divergent commercial offer in a parallel worktree → `superseded` or `regressive`

When one worktree carries a live commercial model (example: Basic 97 PLN /
Operations Plus 59 PLN / Twin Plus) and another ticket rewrites the same
`plans.json` (or a local offer/brand facade) to a different public sheet, do
not treat green ticket tests as authority. Ticket AC often moves with the
rewrite.

Canonical product HOMEs: `subactor/offer` (list prices + site bindings) and
`subactor/brand` (tokens + vocabulary). `wellmanifest/policy-dsl` owns promo
qualification only. Portal files are facades.

Evidence to gather:

| Evidence | Producer | What it answers |
| --- | --- | --- |
| `intent-delta` | ticket intents + todo2code | Did both claim commercial/brand paths? Was `conflictsWith` empty? |
| `content-identity` | `subactor/offer` binding + lock + pin-check | Which tuple matches the pinned `offer://subactor/offer/…` digest? |
| `gate-outcome` | commercial-ssot + brand/vocab gates + governance | Would current main fail the SSOT gate? |

Disposition:

- `superseded` when `subactor/offer` already names the winning offer and the
  other branch only re-implements an older or alternate price sheet;
- `regressive` when applying the branch would undo the offer binding or brand
  profile lock;
- `rebuild` when the intent is still live but delivery must re-base on the
  product catalog/profile before touching the portal facade.

Never invent an eighth disposition for "commercial conflict". Never invent a
second price or brand SSOT inside the portal ticket to "win" the merge.

