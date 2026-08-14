# `merge.candidate.recorded`

**Meaning.** One divergent shape entered evaluation.

**Emitted by.** `merge.candidate.record`

**Payload fields.** `candidateId`, `repository`, `shape`, `ref`,
`headRevision`, `ahead`, `behind`, `recoverable`

## What produced it

A sweep found a branch, an unpushed commit, a staged tree or a stale pull
request and the `merge.candidate.record` command registered it. Recording a
candidate asserts nothing about its fate.

## What matters in it

`recoverable` drives the later destruction gate. `false` means the shape cannot
be restored from Git alone, which forces a written patch before anything
destroys it.

## What it does not mean

That the work is stale, wanted, authorized or safe to delete. Only current
evidence and an independently authorized command may establish those facts.

## Replay

Replay rebuilds a projection. It never invokes the command, executes an effect
or grants authority.
