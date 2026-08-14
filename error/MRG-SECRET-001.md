# `MRG-SECRET-001`

**Meaning.** The secret-free rule is violated.

## What raises it

A document carried a key that looks like a credential, or the request grammar exposed a surface that could transport one.

## Why the rule exists

Decisions are archived, quoted and replayed. Anything that enters one is durable.

## How to resolve it

Carry an opaque handle instead. The standard never needs the value.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
