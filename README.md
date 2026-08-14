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

Dependency-free. Pins the schema, grammar and tool-binding digests, accepts
four canonical documents and proves that 21 adversarial mutations reject with
their declared `MRG-*` code.

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
| `standard/conformance.py` | the disposition and recovery rules, with adversarial proof |
| `docs/ARCHITECTURE.md` | shapes, dispositions, rules, diagnostics |
| `docs/LOGIC_FLOW.md` | evidence ordering and the two destruction gates |
| `docs/PLAYBOOK.md` | six real decisions and what each cost to make |

## Why it exists

Two failure modes cost the most: deleting work that was never delivered, and
re-applying work that already was. Both look identical from a distance —
a branch nobody owns, a diff that resembles the target. Telling them apart is
cheap if you ask `git` the right question first, and expensive if you start
with analysis. [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) records the cost ordering
that emerged from doing it wrong.
