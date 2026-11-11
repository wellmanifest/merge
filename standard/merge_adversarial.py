"""Worked sample and adversarial/parity cases for wellmanifest.merge-decision/v1."""

from __future__ import annotations

import copy
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from merge_contracts import (
    MERGE_PRECONDITIONS,
    SCHEMA_FAMILY,
    ContractError,
    strict_json_load,
    validate_candidate,
    validate_decision,
    validate_evidence,
    validate_receipt,
)
from merge_dsl_events import dsl_admissible


def expect_rejected(
    name: str,
    code: str,
    validator: Callable[[dict[str, Any]], Any],
    base: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
) -> dict[str, str]:
    doc = copy.deepcopy(base)
    mutation(doc)
    try:
        validator(doc)
    except ContractError as error:
        if error.code != code:
            raise AssertionError(f"{name} rejected with {error.code}, expected {code}") from error
        return {"case": name, "code": code}
    raise AssertionError(f"adversarial case accepted: {name}")


def sample() -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """One worked case: an orphaned branch whose intent is still live."""
    candidate = {
        "schema": SCHEMA_FAMILY, "kind": "candidate", "candidateId": "candidate:orphan-eol",
        "repository": "subactor/intent-contract-dsl-runtime", "shape": "remote-branch",
        "ref": "fix/ticket-037-managed-eol", "headRevision": "5" * 40, "baseRef": "main",
        "baseRevision": "b" * 40, "ahead": 5, "behind": 9, "authors": ["Mateusz Lewandowski"],
        "lastActivity": "2026-08-13T09:00:00Z",
        "intent": "Normalize managed governance file line endings and record pending backlog",
        "recoverable": True,
    }
    evidence: dict[str, dict[str, Any]] = {}
    for item in (
        {
            "evidenceId": "evidence:gate", "evidenceKind": "gate-outcome", "producer": "gate",
            "command": "./project/governance-check.sh --actor agent --base b --head HEAD",
            "observation": (
                "GOV-FAIL: 4 errors (delivery contract absent, intent not plan-first, "
                "path owned by no workstream)"
            ),
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:history", "evidenceKind": "history-shape", "producer": "git",
            "command": "git log --format='%an: %s' origin/main..HEAD",
            "observation": (
                "intent.json and its implementation land in one commit; "
                "original authorship must be preserved on rebuild"
            ),
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:intent", "evidenceKind": "intent-delta",
            "producer": "todo2code",
            "command": "t2c compare-workspace . --base origin/main --markdown-mode deterministic",
            "observation": (
                "trend mixed; alignment flat 11.5%; implemented 14.1 to 13.9 percent; "
                "gaps 430 to 439"
            ),
            "deterministic": False,
        },
        {
            "evidenceId": "evidence:identity", "evidenceKind": "content-identity",
            "producer": "git", "command": "git diff --quiet origin/main -- <each changed path>",
            "observation": "0 of 32 changed files are already identical on the target",
            "coverage": {"compared": 32, "total": 32, "matched": 0}, "deterministic": True,
        },
        {
            "evidenceId": "evidence:recovery", "evidenceKind": "recoverability", "producer": "git",
            "command": "git rev-parse origin/fix/ticket-037-managed-eol",
            "observation": "branch tip recorded before deletion; rebased copies carry content",
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:hearsay-identity", "evidenceKind": "content-identity",
            "producer": "human", "command": "read the diff by eye",
            "observation": "looked mostly the same as the target",
            "coverage": {"compared": 4, "total": 32, "matched": 4}, "deterministic": False,
        },
        {
            "evidenceId": "evidence:hearsay-recovery", "evidenceKind": "recoverability",
            "producer": "human", "command": "asked the author whether a copy exists",
            "observation": "author believes a copy exists somewhere", "deterministic": False,
        },
    ):
        record = {
            "schema": SCHEMA_FAMILY, "kind": "evidence", "candidateId": candidate["candidateId"],
            "observedAt": "2026-08-14T12:00:00Z", **item,
        }
        evidence[record["evidenceId"]] = validate_evidence(record, candidate)
    decision = {
        "schema": SCHEMA_FAMILY, "kind": "decision", "decisionId": "decision:orphan-eol",
        "candidateId": candidate["candidateId"], "disposition": "rebuild",
        "evidenceIds": [
            "evidence:gate", "evidence:history", "evidence:intent",
            "evidence:identity", "evidence:recovery",
        ],
        "rationale": (
            "Intent is still live on the target, but the delivery cannot pass the gate as "
            "authored, so the history is rebuilt plan-first with authorship preserved."
        ),
        "decidedBy": "actor://wellmanifest.com/maintainer",
        "actionsAuthorized": [
            "rebuild-history", "open-pull-request", "request-autonomous-merge", "delete-branch",
        ],
        "executor": "interactive-agent", "destructive": True,
        "recoveryRefs": ["ref:5555555555555555555555555555555555555555"],
        "decidedAt": "2026-08-14T12:30:00Z",
    }
    receipt = {
        "schema": SCHEMA_FAMILY, "kind": "receipt", "decisionId": decision["decisionId"],
        "candidateId": candidate["candidateId"],
        "executedActions": ["rebuild-history", "open-pull-request", "delete-branch"],
        "outcome": "applied", "resultingRefs": ["subactor/intent-contract-dsl-runtime#15"],
        "recoveryRefs": ["ref:5555555555555555555555555555555555555555"],
        "secretsRedacted": True, "recordedAt": "2026-08-14T13:00:00Z",
    }
    return candidate, evidence, decision, receipt


def verify_loader_hardening() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        dup_path = tmp_dir / "dup.json"
        dup_path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
        try:
            strict_json_load(dup_path)
        except ContractError as err:
            if err.code != "MRG-CONTRACT-001":
                raise AssertionError(f"unexpected duplicate-key code: {err.code}") from err
        else:
            raise AssertionError("duplicate JSON key accepted")
        valid_path = tmp_dir / "ok.json"
        valid_path.write_text('{"ok": true}', encoding="utf-8")
        link_path = tmp_dir / "link.json"
        link_path.symlink_to(valid_path)
        try:
            strict_json_load(link_path)
        except ContractError as err:
            if err.code != "MRG-CONTRACT-001":
                raise AssertionError(f"unexpected symlink code: {err.code}") from err
        else:
            raise AssertionError("symlinked JSON accepted")


def run_adversarial_and_parity(
    candidate: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    decision: dict[str, Any],
    receipt: dict[str, Any],
) -> tuple[list[dict[str, str]], list[str]]:
    def check_evidence(document: dict[str, Any]) -> dict[str, Any]:
        return validate_evidence(document, candidate)

    def check_decision(document: dict[str, Any]) -> dict[str, Any]:
        return validate_decision(document, candidate, evidence)

    def check_receipt(document: dict[str, Any]) -> None:
        validate_receipt(document, decision)

    staged = {**candidate, "shape": "staged-tree", "headRevision": None, "recoverable": False}
    bearer_canary = "Bearer " + ("x" * 24)

    rejected = [
        expect_rejected("uncommitted-claims-recoverable", "MRG-CANDIDATE-001", validate_candidate,
                        candidate, lambda d: d.update(shape="staged-tree", headRevision=None)),
        expect_rejected("committed-without-head", "MRG-CANDIDATE-001", validate_candidate,
                        candidate, lambda d: d.update(headRevision=None)),
        expect_rejected("committed-omits-head-key", "MRG-CANDIDATE-001", validate_candidate,
                        candidate, lambda d: d.pop("headRevision", None)),
        expect_rejected("candidate-bool-ahead", "MRG-DOC-001", validate_candidate,
                        candidate, lambda d: d.update(ahead=True)),
        expect_rejected("candidate-negative-behind", "MRG-DOC-001", validate_candidate,
                        candidate, lambda d: d.update(behind=-1)),
        expect_rejected("anonymous-work", "MRG-CANDIDATE-001", validate_candidate,
                        candidate, lambda d: d.update(authors=[])),
        expect_rejected("human-evidence-claims-determinism", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:gate"], lambda d: d.update(producer="human")),
        expect_rejected("evidence-without-command", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:gate"], lambda d: d.update(command="  ")),
        expect_rejected("evidence-inline-bearer-secret", "MRG-SECRET-001", check_evidence,
                        evidence["evidence:gate"],
                        lambda d: d.update(observation=f"auth {bearer_canary}")),
        expect_rejected("impossible-coverage", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:identity"],
                        lambda d: d.update(coverage={"compared": 3, "total": 32, "matched": 9})),
        expect_rejected("bool-coverage-count", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:identity"],
                        lambda d: d.update(coverage={"compared": True, "total": 32, "matched": 0})),
        expect_rejected("unhashable-evidence-ids", "MRG-REF-001", check_decision,
                        decision, lambda d: d.update(evidenceIds=[{}])),
        expect_rejected("unhashable-actions-authorized", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(actionsAuthorized=[{}])),
        expect_rejected("disposition-without-required-evidence", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(disposition="obsolete")),
        expect_rejected("already-implemented-on-partial-identity", "MRG-EVIDENCE-001",
                        check_decision, decision,
                        lambda d: d.update(
                            disposition="already-implemented",
                            evidenceIds=["evidence:identity", "evidence:recovery"],
                            actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[],
                        )),
        expect_rejected("superseded-without-replacement", "MRG-DECISION-001", check_decision,
                        decision,
                        lambda d: d.update(
                            disposition="superseded",
                            evidenceIds=["evidence:identity", "evidence:recovery"],
                            actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[],
                        )),
        expect_rejected("replacement-on-non-superseded", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(supersededBy="a" * 40)),
        expect_rejected("defer-authorizes-effects", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(
                            disposition="defer", evidenceIds=["evidence:intent"],
                            actionsAuthorized=["delete-branch"], destructive=True,
                        )),
        expect_rejected("destructive-flag-disagrees", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(destructive=False)),
        expect_rejected("destructive-without-recovery-ref", "MRG-RECOVERY-001", check_decision,
                        decision, lambda d: d.update(recoveryRefs=[])),
        expect_rejected("destructive-without-recoverability-evidence", "MRG-RECOVERY-001",
                        check_decision, decision,
                        lambda d: d.update(evidenceIds=["evidence:gate", "evidence:history"])),
        expect_rejected("advisory-evidence-authorizes-destruction", "MRG-EVIDENCE-001",
                        check_decision, decision,
                        lambda d: d.update(
                            disposition="regressive",
                            evidenceIds=["evidence:hearsay-identity", "evidence:hearsay-recovery"],
                            actionsAuthorized=["delete-branch"], destructive=True,
                        )),
        expect_rejected("unknown-evidence-cited", "MRG-REF-001", check_decision,
                        decision, lambda d: d["evidenceIds"].append("evidence:imagined")),
        expect_rejected("rationale-too-thin", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(rationale="ok")),
        expect_rejected("receipt-exceeds-authorization", "MRG-RECEIPT-001", check_receipt,
                        receipt, lambda d: d.update(executedActions=["discard-worktree"])),
        expect_rejected("receipt-unhashable-executed-actions", "MRG-DOC-001", check_receipt,
                        receipt, lambda d: d.update(executedActions=[{}])),
        expect_rejected("destructive-receipt-without-recovery", "MRG-RECOVERY-001", check_receipt,
                        receipt, lambda d: d.update(recoveryRefs=[])),
        expect_rejected("receipt-not-redacted", "MRG-SECRET-001", check_receipt,
                        receipt, lambda d: d.update(secretsRedacted=False)),
        expect_rejected("interactive-agent-authorizes-merge", "MRG-MERGE-001", check_decision,
                        decision, lambda d: d.update(
                            actionsAuthorized=["merge"], destructive=False,
                            recoveryRefs=[], executor="interactive-agent",
                        )),
        expect_rejected("autonomous-merge-without-preconditions", "MRG-MERGE-001", check_decision,
                        decision, lambda d: d.update(
                            actionsAuthorized=["merge"], destructive=False,
                            recoveryRefs=[], executor="automated-validator",
                        )),
        expect_rejected("unknown-executor", "MRG-DECISION-001", check_decision,
                        decision, lambda d: d.update(executor="cron")),
        expect_rejected("uncommitted-discard-with-git-ref-only", "MRG-RECOVERY-001",
                        lambda d: validate_decision(d, staged, evidence), decision,
                        lambda d: d.update(
                            disposition="regressive",
                            evidenceIds=["evidence:identity", "evidence:recovery"],
                            actionsAuthorized=["discard-worktree"], destructive=True,
                            recoveryRefs=["ref:5555555555555555555555555555555555555555"],
                        )),
    ]

    if not dsl_admissible(candidate, decision, evidence):
        raise ContractError("MRG-CONTRACT-001", "the rule equations reject the reference decision")
    parity: list[str] = []
    for case, mutation in (
        ("disposition-without-required-evidence", lambda d: d.update(disposition="obsolete")),
        ("already-implemented-on-partial-identity",
         lambda d: d.update(disposition="already-implemented",
                            evidenceIds=["evidence:hearsay-identity", "evidence:recovery"],
                            actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[])),
        ("superseded-without-replacement",
         lambda d: d.update(disposition="superseded",
                            evidenceIds=["evidence:identity", "evidence:recovery"],
                            actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[])),
        ("defer-authorizes-effects",
         lambda d: d.update(disposition="defer", evidenceIds=["evidence:intent"],
                            actionsAuthorized=["delete-branch"], destructive=True)),
        ("destructive-without-recovery-ref", lambda d: d.update(recoveryRefs=[])),
        ("destructive-without-recoverability-evidence",
         lambda d: d.update(evidenceIds=["evidence:gate", "evidence:history"])),
        ("interactive-agent-authorizes-merge",
         lambda d: d.update(actionsAuthorized=["merge"], destructive=False, recoveryRefs=[],
                            executor="interactive-agent")),
        ("autonomous-merge-without-preconditions",
         lambda d: d.update(actionsAuthorized=["merge"], destructive=False, recoveryRefs=[],
                            executor="automated-validator")),
        ("advisory-evidence-authorizes-destruction",
         lambda d: d.update(disposition="regressive",
                            evidenceIds=["evidence:hearsay-identity", "evidence:hearsay-recovery"],
                            actionsAuthorized=["delete-branch"], destructive=True)),
    ):
        mutated = copy.deepcopy(decision)
        mutation(mutated)
        if dsl_admissible(candidate, mutated, evidence):
            raise AssertionError(f"the rule equations accepted {case}")
        parity.append(case)

    not_run_ev = dict(evidence)
    for item in (
        {"evidenceId": "evidence:hosted-not-run", "evidenceKind": "gate-outcome",
         "producer": "gate", "command": "gh pr checks --required",
         "observation": "required-checks-not-run: jobs not started (runner unavailable)",
         "deterministic": True},
        {"evidenceId": "evidence:claimed-preconditions", "evidenceKind": "gate-outcome",
         "producer": "gate", "command": "validator preconditions --exact-head",
         "observation": " ".join(MERGE_PRECONDITIONS), "deterministic": True},
        {"evidenceId": "evidence:local-tests", "evidenceKind": "gate-outcome",
         "producer": "gate", "command": "python3 -m pytest -q",
         "observation": "45 passed at the exact head", "deterministic": True},
    ):
        rec = {"schema": SCHEMA_FAMILY, "kind": "evidence",
               "candidateId": candidate["candidateId"], "observedAt": "2026-09-24T12:00:00Z",
               **item}
        not_run_ev[rec["evidenceId"]] = validate_evidence(rec, candidate)

    def merge_on(executor: str, ids: list[str]) -> Callable[[dict[str, Any]], None]:
        return lambda d: d.update(
            actionsAuthorized=["merge"], destructive=False,
            recoveryRefs=[], executor=executor, evidenceIds=ids,
        )

    for case, mutation in (
        ("validator-merge-on-checks-not-run",
         merge_on("automated-validator",
                  ["evidence:hosted-not-run", "evidence:claimed-preconditions",
                   "evidence:history"])),
        ("validator-merge-on-checks-not-run-with-local-tests",
         merge_on("automated-validator",
                  ["evidence:hosted-not-run", "evidence:claimed-preconditions",
                   "evidence:local-tests", "evidence:history"])),
        ("owner-merge-on-checks-not-run-with-local-tests",
         merge_on("owner",
                  ["evidence:hosted-not-run", "evidence:claimed-preconditions",
                   "evidence:local-tests", "evidence:history"])),
        ("owner-merge-with-all-preconditions",
         merge_on("owner", ["evidence:claimed-preconditions", "evidence:history"])),
    ):
        rejected.append(
            expect_rejected(case, "MRG-MERGE-001",
                            lambda d: validate_decision(d, candidate, not_run_ev),
                            decision, mutation)
        )
        mutated = copy.deepcopy(decision)
        mutation(mutated)
        if dsl_admissible(candidate, mutated, not_run_ev):
            raise AssertionError(f"the rule equations accepted {case}")
        parity.append(case)

    validator_ok = copy.deepcopy(decision)
    merge_on("automated-validator", ["evidence:claimed-preconditions", "evidence:history"])(
        validator_ok
    )
    validate_decision(validator_ok, candidate, not_run_ev)
    if not dsl_admissible(candidate, validator_ok, not_run_ev):
        raise AssertionError("the rule equations rejected Validator merge with all preconditions")
    parity.append("validator-merge-with-all-preconditions")

    for case, changes in (
        ("negated-check-marker",
         {"observation": " ".join(MERGE_PRECONDITIONS).replace(
             "required-checks-green", "required-checks-green=false")}),
        ("prose-check-marker", {"observation": "claimed: " + " ".join(MERGE_PRECONDITIONS)}),
        ("nondeterministic-check-marker", {"deterministic": False}),
        ("human-check-marker", {"producer": "human", "deterministic": False}),
    ):
        variant = dict(not_run_ev)
        rec = {**variant["evidence:claimed-preconditions"], **changes}
        variant[rec["evidenceId"]] = validate_evidence(rec, candidate)
        rejected.append(
            expect_rejected(case, "MRG-MERGE-001",
                            lambda d, v=variant: validate_decision(d, candidate, v),
                            validator_ok, lambda _d: None)
        )
        if dsl_admissible(candidate, validator_ok, variant):
            raise AssertionError(f"the rule equations accepted {case}")
        parity.append(case)

    staged_decision = copy.deepcopy(decision)
    staged_decision.update(disposition="regressive",
                           evidenceIds=["evidence:identity", "evidence:recovery"],
                           actionsAuthorized=["discard-worktree"], destructive=True)
    if dsl_admissible(staged, staged_decision, evidence):
        raise AssertionError("the rule equations accepted uncommitted-discard-with-git-ref-only")
    parity.append("uncommitted-discard-with-git-ref-only")
    return rejected, parity
