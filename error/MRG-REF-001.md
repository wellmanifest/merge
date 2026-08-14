# `MRG-REF-001`

**Meaning.** A reference is malformed, duplicated, or points at another candidate.

## What raises it

An identifier did not match its shape, a list repeated an entry, or a decision cited evidence belonging to a different candidate.

## Why the rule exists

Evidence bound to the wrong candidate is worse than missing evidence: it looks like diligence.

## How to resolve it

Fix the reference. If evidence really applies to two candidates, observe it twice — once per candidate — so each decision cites its own.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
