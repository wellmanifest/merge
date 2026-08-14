# merge

Versioned Wellmanifest standard for deciding what happens to work that
diverged: an orphaned branch, an unpushed commit, a staged tree nobody
remembers, or a change that may already be upstream under another name.

The standard is a closed set of seven dispositions, the evidence each one owes
before it may be recorded, and the bindings that say which tool can actually
produce that evidence. It decides; it never merges, deletes or publishes.

```text
python3 standard/conformance.py --all
```

Dependency-free. Pins the schema, grammar, tool-binding and rule digests,
accepts four canonical documents, proves that 21 adversarial mutations reject
with their declared `MRG-*` code, and checks that the portable rule equations
agree with this implementation on 10 of them.

## The seven dispositions

| Disposition | When | Owes |
| --- | --- | --- |
| `adopt` | the target's gate accepts it as authored | gate outcome, reachability |
| `rebuild` | intent is live, delivery is not acceptable | gate outcome, history shape |
| `already-implemented` | the target already has it, byte for byte | identity over **every** file |
| `superseded` | the same intent shipped as another revision | patch equivalence + that revision |
| `regressive` | applying it would undo something | identity showing divergence |
| `obsolete` | what it changes no longer exists | dependency evidence |
| `defer` | live, but not now | intent delta; effect-free actions only |

## The rules are equations, not prose

The decision rules exist twice on purpose. `standard/conformance.py` is the
reference implementation; `standard/merge-rules.env` is the same logic written
as [Env DSL](https://github.com/wellmanifest/env-dsl) operator equations, so a
consumer in any language can evaluate admissibility without running this
repository's Python:

```env
RULE_ALREADY_IMPLEMENTED_CONDITION=@FACT_DISPOSITION!=:ALREADY_IMPLEMENTED||(@FACT_HAS_CONTENT_IDENTITY&&@FACT_IDENTITY_TOTAL>0&&@FACT_IDENTITY_COMPARED==@FACT_IDENTITY_TOTAL&&@FACT_IDENTITY_MATCHED==@FACT_IDENTITY_TOTAL)
RULE_UNCOMMITTED_PATCH_CONDITION=!@FACT_DESTRUCTIVE||@FACT_CANDIDATE_RECOVERABLE||@FACT_PATCH_RECOVERY
DECISION_ADMISSIBLE_CONDITION=@RULE_ADOPT_CONDITION&&@RULE_REBUILD_CONDITION&&...
```

Each rule is an implication: a disposition that does not apply satisfies its
own rule vacuously, so one conjunction decides admissibility. The evaluation is
effect-free and descriptive — it reads no clock, network or secret, and it
authorizes nothing.

Parity is asserted rather than assumed. The suite evaluates both paths over the
reference decision and over every mutation the equations can express, and fails
if they ever disagree.

## Reused tools

Evidence kinds are bound to producers in
[`standard/tool-bindings.json`](standard/tool-bindings.json), with the command
that was actually run:

- **[todo2code](https://github.com/semcod/todo2code)** — `t2c compare-workspace
  <root> --base <ref>` for intent deltas: does the candidate add declared
  intent, restate it, or is it a stale subset of the target.
- **[code2llm](https://github.com/semcod/code2llm)** — static analysis for code
  liveness: does the code the candidate touches still exist and stay reachable.
- **[deconnected](https://github.com/semcod/deconnected)** — one evidence graph
  across code, routes, services and tables, before anything shared is called
  dead. Its own rule is adopted verbatim: a missing reference is evidence for
  investigation, not permission to delete.
- **[giton](https://github.com/semcod/giton)** — history shape: plan-first
  ordering and additive `fixup!` correction instead of rewriting authored
  commits.

`git` and the target repository's own governance gate remain the trust root.
Analytical producers inform every disposition and decide none: a decision whose
whole evidence set is non-deterministic must not authorize destruction.

## Layout

| Path | Contents |
| --- | --- |
| `standard/merge-decision.schema.json` | closed candidate, evidence, decision and receipt contracts |
| `standard/merge-decision.v1.gbnf` | grammar emitting only canonical decisions |
| `standard/tool-bindings.json` | evidence kind → producer, with real commands |
| `standard/merge-rules.env` | the same rules as portable Env DSL operator equations |
| `standard/env_dsl.py` | Env DSL evaluator pinned byte-for-byte to `wellmanifest/env-dsl@1d5ed6c` |
| `standard/conformance.py` | the disposition and recovery rules, with adversarial proof and DSL parity |
| `docs/ARCHITECTURE.md` | shapes, dispositions, rules, diagnostics |
| `docs/LOGIC_FLOW.md` | evidence ordering and the two destruction gates |
| `docs/AUTONOMOUS_MERGE.md` | who merges, the six preconditions, and why a green pull request still sits |
| `docs/PLAYBOOK.md` | six real decisions and what each cost to make |

## Who closes a decision

A decision ends in a merge, and the merge is not the deciding agent's to make.
An interactive agent runs under the identity that pushed the branch: its
approval would be a self-approval and its merge an unreviewed write. It
authorizes `request-autonomous-merge`; the validator identity in CI validates at
the exact head, approves, merges and deletes the branch.

Six conditions gate that. Repository membership, base branches and exact check
names now have one source in the Validator's protected registry; the scheduled
matrix and runtime scan configuration are generated from those same bytes.
The remaining independent boundaries are the standing policy variables and
the target repository's ruleset. A registry entry is therefore reviewed once,
while a digest mismatch fails before a target token is minted.
[`docs/AUTONOMOUS_MERGE.md`](docs/AUTONOMOUS_MERGE.md) carries the checklist and
the diagnosis order.

## Why it exists

Two failure modes cost the most: deleting work that was never delivered, and
re-applying work that already was. Both look identical from a distance —
a branch nobody owns, a diff that resembles the target. Telling them apart is
cheap if you ask `git` the right question first, and expensive if you start
with analysis. [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) records the cost ordering
that emerged from doing it wrong.
