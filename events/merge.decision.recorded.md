# `merge.decision.recorded`

**Meaning.** A disposition was recorded after its evidence obligation passed.

**Emitted by.** `merge.decision.record`

**Payload fields.** `decisionId`, `candidateId`, `disposition`, `evidenceIds`,
`executor`, `actionsAuthorized`, `destructive`, `recoveryRefs`

## What produced it

The `merge.decision.record` command evaluated the disposition's deterministic
rules and accepted the proposed record. The decision describes authorized next
actions; the event performs none of them.

## What matters in it

`executor` and `actionsAuthorized` jointly bound what may happen next. An
interactive agent may request an autonomous merge; it may not authorize its own
merge.

## What it does not mean

That any authorized action occurred. Only an execution receipt and
`merge.action.executed` state what actually happened.

## Replay

Replay rebuilds a projection. It never re-evaluates authority, performs an
action or grants authority.
