# `merge.decision.rejected`

**Meaning.** A proposed disposition was refused because its rule was not met.

**Emitted by.** `merge.decision.record`

**Payload fields.** `candidateId`, `disposition`, `diagnostic`

## What produced it

The command found a missing or invalid evidence obligation, recovery artifact,
executor or action boundary. `diagnostic` names the stable public rejection
code from `error/index.json`.

## What matters in it

A refusal is an append-only fact rather than an exception that existed only in
one process log. The reverse command-to-error mapping remains canonical in
`operations/index.json`.

## What it does not mean

That the candidate is undecidable. It means this attempt was not admissible and
may be retried only according to the registered error metadata.

## Replay

Replay rebuilds a projection. It never retries the command, performs an effect
or grants authority.
