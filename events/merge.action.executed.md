# `merge.action.executed`

**Meaning.** Authorized actions ran and their outcome was receipted.

**Emitted by.** `merge.action.execute`

**Payload fields.** `decisionId`, `candidateId`, `executedActions`, `outcome`,
`resultingRefs`, `recoveryRefs`

## What produced it

The declared executor performed a subset of the decision's authorized actions
and recorded the resulting references and recovery artifacts.

## What matters in it

`executedActions` may only be a subset of `actionsAuthorized`. The receipt
cannot silently widen the executor's mandate.

## What it does not mean

That the decision was correct. The event records what happened, not whether it
should have happened.

## Replay

Replay rebuilds a projection. It never invokes the executor, repeats an action
or grants authority.
