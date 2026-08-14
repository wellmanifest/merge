# `merge.evidence.observed`

**Meaning.** One typed observation was attached to a candidate.

**Emitted by.** `merge.evidence.observe`

**Payload fields.** `evidenceId`, `candidateId`, `evidenceKind`, `producer`,
`command`, `deterministic`, `coverage`

## What produced it

A producer—Git, the target gate, todo2code, code2llm, deconnected, giton or a
human—answered one question about the candidate. The command records the
producer and invocation; the event records the resulting fact.

## What matters in it

`deterministic` separates evidence that may support a destructive decision from
evidence that can only inform one. `coverage` makes a content-identity claim
mean every file rather than only the files someone inspected.

## What it does not mean

That the observation is current forever. A later push creates a new fact and
invalidates conclusions bound to the old head.

## Replay

Replay rebuilds a projection. It never invokes the producer, executes an effect
or grants authority.
