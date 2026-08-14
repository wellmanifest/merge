# `MRG-DOC-001`

**Meaning.** Document family or closed field set is invalid.

## What raises it

A document carried a field the contract does not declare, missed a required one, or named the wrong schema family.

## Why the rule exists

An undeclared field is how a contract silently grows. The closed set is what lets a reader trust that the document says everything it says — an authority reference smuggled into a decision is caught here, not later.

## How to resolve it

Add the field to the contract deliberately, or remove it from the document. Do not widen the checker.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
