# `MRG-MERGE-001`

**Meaning.** An interactive agent authorized its own merge, an automated merge lacks a required precondition, or an owner merge lacks full preconditions and `autonomy-degraded` override markers.

## What raises it

A decision put `merge` in its authorized actions while `executor` was `interactive-agent`, while `automated-validator` lacked any of the six merge preconditions (or saw `required-checks-not-run`), or while `owner` lacked both the six preconditions and deterministic `autonomy-degraded` + `owner-manual-override` gate markers.

## Why the rule exists

An interactive AI agent runs under the identity that pushed the branch: its approval is a self-approval and its merge an unreviewed write. Human repository owners retain manual control when automation fails, provided the degraded-autonomy override is explicitly recorded.

## How to resolve it

- For AI agents: authorize `request-autonomous-merge` instead and let `automated-validator` merge once all six preconditions pass.
- For an authenticated human owner recovering stalled automation: either complete the six preconditions or record deterministic gate evidence containing `autonomy-degraded` and `owner-manual-override`.

Refusals are facts. A rejected decision appends `merge.decision.rejected`
carrying this code, so a refusal is visible in the stream rather than only in
whatever log someone happened to read.
