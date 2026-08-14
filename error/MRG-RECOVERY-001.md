# `MRG-RECOVERY-001`

**Meaning.** A destructive decision lacks the artifact that would restore the work.

## What raises it

A decision authorized deletion or discard without recoverability evidence, without any recovery reference, or — for an uncommitted shape — with a git reference instead of a written patch.

## Why the rule exists

This is the rule that separates a reversible mistake from a permanent one. A branch tip restores a branch; nothing restores a staged tree that was never written down.

## How to resolve it

Write the artifact first: `git rev-parse` for a ref, `git diff --cached > patch` for an index. Then decide.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
