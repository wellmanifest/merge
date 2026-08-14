# `MRG-CANDIDATE-001`

**Meaning.** The candidate misdescribes its shape, head or recoverability.

## What raises it

A committed shape omitted its head revision, an uncommitted shape claimed to
be recoverable, or nobody was named as the author.

## Why the rule exists

`recoverable` drives the destruction gate. A staged tree that claims
recoverability disarms the rule that would require a patch before discard.

## How to resolve it

Describe the shape truthfully. A staged tree or dirty worktree is not
recoverable from Git, regardless of what the discovery sweep expected.

A rejected decision appends `merge.decision.rejected` with this code. The event
records the refusal; it does not retry or authorize a correction.
