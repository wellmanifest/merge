# Plan (agent:claude)

1. Read `docs/AUTONOMOUS_MERGE.md`, `standard/merge-rules.env` (`RULE_MERGE_EXECUTOR_CONDITION`) and `MRG-MERGE-001` in `standard/conformance.py`; cite them as the current rule.
2. Write `docs/decisions/owner-delegated-merge.md` (status `proposed`):
   - context: owner request of 2026-10-12, data-plane/data-gateway not enrolled;
   - options: A keep Validator-only and enroll repositories (recommended path already supported); B owner-delegated profile: per-repository, owner-signed standing delegation, exact-head required checks green, audit receipt, revocable, never `--admin`; C status quo;
   - consequences, including that B weakens the independence guarantee and needs rule, conformance and host-instruction changes in separate tickets.
3. Index it in `docs/README.md`.
4. Run `python3 standard/conformance.py --all` and `./project/governance-check.sh`; open PR on `ticket/015-…` for independent review.
5. No lease is fabricated: the controller lease is absent and recorded as a gap.

## Result

- Record: `docs/decisions/owner-delegated-merge.md` (v1, `proposed`, recommends A), indexed in `docs/README.md`.
- `python3 standard/conformance.py --all`: ok. `./project/governance-check.sh`: GOV-PASS.
- No controller lease was issued; none fabricated.
