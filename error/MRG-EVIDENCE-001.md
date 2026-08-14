# `MRG-EVIDENCE-001`

**Meaning.** Evidence is unattributed, inconsistent or too weak for its claim.

## What raises it

Evidence arrived without the producing command, with impossible coverage,
with a human observation marked deterministic, or a disposition relied on
evidence that did not support it.

## Why the rule exists

Partial identity cannot prove `already-implemented`, and advisory evidence
alone cannot carry a destructive decision.

## How to resolve it

Produce the missing observation with an attributable command and honest
coverage. If the rule needs new evidence, do not retry with the same payload.

A rejected decision appends `merge.decision.rejected` with this code. The event
records the refusal; it does not strengthen the evidence.
