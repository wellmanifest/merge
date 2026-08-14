# `MRG-MERGE-001`

**Meaning.** An interactive agent authorized its own merge, or an autonomous merge lacks evidence of a precondition.

## What raises it

A decision put `merge` in its authorized actions while its executor was the interactive agent, or an automated executor could not evidence all six merge preconditions.

## Why the rule exists

An interactive agent runs under the identity that pushed the branch: its approval is a self-approval and its merge an unreviewed write.

## How to resolve it

Authorize `request-autonomous-merge` instead, and make the preconditions true — including the ones that live in another repository's configuration.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
