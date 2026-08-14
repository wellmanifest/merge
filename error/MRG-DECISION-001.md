# `MRG-DECISION-001`

**Meaning.** The disposition, evidence obligation or authorized actions are invalid.

## What raises it

The disposition lacked required evidence, named a replacement while not being
`superseded`, authorized an effect while deferring, or disagreed with its own
destructive flag.

## Why the rule exists

The destructive flag is derived from authorized actions, so a decision cannot
present itself as safe while authorizing deletion.

## How to resolve it

Gather the evidence the disposition owes, or choose the disposition and action
boundary that the evidence actually supports.

A rejected decision appends `merge.decision.rejected` with this code. The event
records the refusal; it does not authorize the replacement decision.
