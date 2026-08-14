# `MRG-RECEIPT-001`

**Meaning.** A receipt executed something the decision never authorized.

## What raises it

The executed actions were not a subset of the authorized ones.

## Why the rule exists

A receipt is the only record of what actually happened. Allowing it to exceed its decision would make the decision decorative.

## How to resolve it

Record what was done truthfully, then record a second decision for the rest if it was warranted.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
