#!/usr/bin/env python3
"""Dependency-free semantic conformance for wellmanifest.merge-decision/v1.

The rules here are the reusable part of the standard: which evidence each
disposition owes before it may be recorded, and what a destructive decision
must carry so the work it destroys can come back.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

import cqrs_conformance

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "merge-decision.schema.json"
GRAMMAR_PATH = ROOT / "merge-decision.v1.gbnf"
BINDINGS_PATH = ROOT / "tool-bindings.json"
RULES_PATH = ROOT / "merge-rules.env"
EVENTS_PATH = ROOT / "merge-events.env"
EVENTS_DOC_PATH = ROOT.parent / "docs" / "MERGE_EVENTS.md"
OPERATIONS_PATH = ROOT.parent / "operations" / "index.json"
ENV_DSL_PATH = ROOT / "env_dsl.py"
ENV_DSL_SOURCE_REVISION = "1d5ed6c"
ENV_DSL_DIGEST = "5bf2e2b0983f9bbe421278a2eb76f485a5fee4c10cd820a19bfd5d1ac6e2dc24"
RULES_DIGEST = "214bbcea8cf7e9d3951864a3423f92eed149394622cbe85fcc575e597f2c470a"
SCHEMA_DIGEST = "0a122f0c003e4389fc954ae9f5a38dad7e93804b6056bcefe75f97203795a23a"
GRAMMAR_DIGEST = "8e3aa2cb41ed435a503ae656374e5acd1e202876f9a0dd430d2f64e5b478cd8f"
BINDINGS_DIGEST = "d20b43eafac91d7ace8d4b126ca8838b0b33e9d68f17d84f4a0a010ecac48abe"
SCHEMA_FAMILY = "wellmanifest.merge-decision/v1"
SCHEMA_URI = "https://wellmanifest.com/schemas/merge-decision/v1"

CANDIDATE_KEYS = {
    "schema", "kind", "candidateId", "repository", "shape", "ref", "headRevision", "baseRef",
    "baseRevision", "ahead", "behind", "authors", "lastActivity", "intent", "recoverable",
}
CANDIDATE_OPTIONAL = {"headRevision", "intent"}
EVIDENCE_KEYS = {
    "schema", "kind", "evidenceId", "candidateId", "evidenceKind", "producer", "command",
    "observation", "artifactDigest", "coverage", "deterministic", "observedAt",
}
EVIDENCE_OPTIONAL = {"artifactDigest", "coverage"}
DECISION_KEYS = {
    "schema", "kind", "decisionId", "candidateId", "disposition", "evidenceIds", "rationale",
    "supersededBy", "decidedBy", "actionsAuthorized", "executor", "destructive", "recoveryRefs",
    "decidedAt",
}
DECISION_OPTIONAL = {"supersededBy"}
RECEIPT_KEYS = {
    "schema", "kind", "decisionId", "candidateId", "executedActions", "outcome", "resultingRefs",
    "recoveryRefs", "secretsRedacted", "recordedAt",
}

SHAPES = {"remote-branch", "local-branch", "unpushed-commit", "staged-tree", "worktree", "pull-request"}
UNRECOVERABLE_SHAPES = {"staged-tree", "worktree"}
DISPOSITIONS = {"adopt", "rebuild", "already-implemented", "superseded", "regressive", "obsolete", "defer"}
EVIDENCE_KINDS = {
    "content-identity", "patch-equivalence", "reachability", "intent-delta", "gate-outcome",
    "code-liveness", "dependency-evidence", "history-shape", "recoverability",
}
PRODUCERS = {"git", "gate", "todo2code", "code2llm", "deconnected", "giton", "human"}
ACTIONS = {"open-pull-request", "request-autonomous-merge", "merge", "rebuild-history",
           "delete-branch", "discard-worktree", "record-backlog", "no-action"}
EXECUTORS = {"interactive-agent", "automated-validator", "owner"}
# Six conditions the independent Validator must verify before merging.
MERGE_PRECONDITIONS = ("in-scan-matrix", "in-scan-config", "ticket-derivable",
                       "required-checks-green", "approved-at-exact-head", "standing-merge-policy")
# A required check that was never executed (runner not started, billing,
# no matching runner) is neither green nor failed. See docs/MERGE_EVENTS.md.
CHECKS_NOT_RUN = "required-checks-not-run"
# The resolution matrix in merge-events.env: who acts, and which states exist.
EVENT_ACTORS = {"INTERACTIVE_AGENT", "ONEDEV_AGENT", "VALIDATOR_AGENT"}
EVENT_STATES = {"DRAFT", "AWAITING_CHECKS", "AWAITING_LOCAL_VERIFY", "AWAITING_VALIDATOR",
                "AWAITING_ENROLLMENT", "AWAITING_OWNER_DECISION", "CHANGES_REQUIRED", "REPLANNING",
                "SERIALIZED", "MERGED", "CLOSED"}
EVENT_FIELDS = ("ACTOR", "ACTION", "NEXT", "NOTIFY", "PRIORITY", "BLOCKS_MERGE", "AUTONOMOUS")
DESTRUCTIVE_ACTIONS = {"delete-branch", "discard-worktree", "rebuild-history"}
OUTCOMES = {"applied", "partially-applied", "blocked", "abandoned"}

# Each disposition owes evidence. These are minimums, not ceilings.
REQUIRED_EVIDENCE: dict[str, set[str]] = {
    "adopt": {"gate-outcome", "reachability"},
    "rebuild": {"gate-outcome", "history-shape"},
    "already-implemented": {"content-identity"},
    "superseded": {"patch-equivalence"},
    "regressive": {"content-identity"},
    "obsolete": {"dependency-evidence"},
    "defer": {"intent-delta"},
}
# Dispositions that may only authorize effect-free follow-up.
EFFECT_FREE = {"defer": {"record-backlog", "no-action"}}

PATTERNS = {
    "candidateId": r"^candidate:[a-z0-9][a-z0-9._-]{0,95}$",
    "evidenceId": r"^evidence:[a-z0-9][a-z0-9._-]{0,95}$",
    "decisionId": r"^decision:[a-z0-9][a-z0-9._-]{0,95}$",
    "repository": r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$",
    "revision": r"^[0-9a-f]{40}$",
    "actorRef": r"^actor://[a-z0-9][a-z0-9.-]*/[A-Za-z0-9._:-]+$",
    "recoveryRef": r"^(?:ref|patch|tag):[A-Za-z0-9._:/-]+$",
    "digest": r"^sha256:[0-9a-f]{64}$",
}
SENSITIVE = re.compile(
    r"(?:password|passwd|token|secret|credential|api[-_]?key|cookie|private[-_]?key)", re.I
)
SAFE_ASSERTIONS = {"secretsRedacted"}


class ContractError(ValueError):
    """A bounded rejection that never repeats untrusted content."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reject_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key not in SAFE_ASSERTIONS and SENSITIVE.search(key):
                raise ContractError("MRG-SECRET-001", "unsafe key")
            reject_sensitive(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_sensitive(nested)


def closed(doc: Any, keys: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise ContractError("MRG-DOC-001", "expected an object")
    optional = optional or set()
    if set(doc) - keys or (keys - optional) - set(doc):
        raise ContractError("MRG-DOC-001", "document fields are not closed")
    return doc


def match(name: str, value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(PATTERNS[name], value):
        raise ContractError("MRG-REF-001", f"invalid reference: {name}")
    return value


def validate_candidate(doc: dict[str, Any]) -> dict[str, Any]:
    doc = closed(doc, CANDIDATE_KEYS, CANDIDATE_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "candidate":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("candidateId", doc["candidateId"])
    match("repository", doc["repository"])
    match("revision", doc["baseRevision"])
    if doc["shape"] not in SHAPES:
        raise ContractError("MRG-DOC-001", "unknown candidate shape")
    if doc["headRevision"] is not None:
        match("revision", doc["headRevision"])
    elif doc["shape"] not in UNRECOVERABLE_SHAPES:
        raise ContractError("MRG-CANDIDATE-001", "a committed candidate must name its head revision")
    if not isinstance(doc["ahead"], int) or not isinstance(doc["behind"], int):
        raise ContractError("MRG-DOC-001", "ahead and behind must be integers")
    if doc["shape"] in UNRECOVERABLE_SHAPES and doc["recoverable"] is not False:
        raise ContractError(
            "MRG-CANDIDATE-001", "an uncommitted shape is not recoverable from git alone"
        )
    if not isinstance(doc["authors"], list) or not doc["authors"]:
        raise ContractError("MRG-CANDIDATE-001", "a candidate must name whose work it is")
    return doc


def validate_evidence(doc: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    doc = closed(doc, EVIDENCE_KEYS, EVIDENCE_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "evidence":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("evidenceId", doc["evidenceId"])
    if match("candidateId", doc["candidateId"]) != candidate["candidateId"]:
        raise ContractError("MRG-REF-001", "evidence is bound to another candidate")
    if doc["evidenceKind"] not in EVIDENCE_KINDS:
        raise ContractError("MRG-EVIDENCE-001", "unknown evidence kind")
    if doc["producer"] not in PRODUCERS:
        raise ContractError("MRG-EVIDENCE-001", "unknown producer")
    if not isinstance(doc["command"], str) or len(doc["command"].strip()) < 3:
        raise ContractError("MRG-EVIDENCE-001", "evidence must name the command that produced it")
    if doc.get("artifactDigest") is not None:
        match("digest", doc["artifactDigest"])
    if doc["producer"] == "human" and doc["deterministic"] is not False:
        raise ContractError("MRG-EVIDENCE-001", "a human observation is never deterministic")
    coverage = doc.get("coverage")
    if coverage is not None:
        closed(coverage, {"compared", "total", "matched"})
        if coverage["compared"] > coverage["total"] or coverage["matched"] > coverage["compared"]:
            raise ContractError("MRG-EVIDENCE-001", "coverage counts are inconsistent")
    return doc


def full_identity(evidence: dict[str, Any]) -> bool:
    """Content identity counts only when every file was compared and matched."""
    coverage = evidence.get("coverage")
    if not coverage or coverage["total"] == 0:
        return False
    return coverage["compared"] == coverage["total"] and coverage["matched"] == coverage["total"]


def validate_decision(
    doc: dict[str, Any], candidate: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    doc = closed(doc, DECISION_KEYS, DECISION_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "decision":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("decisionId", doc["decisionId"])
    if match("candidateId", doc["candidateId"]) != candidate["candidateId"]:
        raise ContractError("MRG-REF-001", "decision is bound to another candidate")
    match("actorRef", doc["decidedBy"])
    if doc["disposition"] not in DISPOSITIONS:
        raise ContractError("MRG-DECISION-001", "unknown disposition")
    if not isinstance(doc["rationale"], str) or len(doc["rationale"].strip()) < 10:
        raise ContractError("MRG-DECISION-001", "a decision must state why")

    ids = doc["evidenceIds"]
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
        raise ContractError("MRG-REF-001", "evidence references must be unique and nonempty")
    cited: list[dict[str, Any]] = []
    for item in ids:
        match("evidenceId", item)
        if item not in evidence:
            raise ContractError("MRG-REF-001", "decision cites unknown evidence")
        cited.append(evidence[item])
    kinds = {item["evidenceKind"] for item in cited}

    required = REQUIRED_EVIDENCE[doc["disposition"]]
    if not required <= kinds:
        raise ContractError("MRG-DECISION-001", "disposition lacks the evidence its rule requires")

    if doc["disposition"] in {"already-implemented", "regressive"}:
        identity = [i for i in cited if i["evidenceKind"] == "content-identity"]
        if doc["disposition"] == "already-implemented" and not any(full_identity(i) for i in identity):
            raise ContractError(
                "MRG-EVIDENCE-001", "already-implemented requires identity over every file"
            )
        if doc["disposition"] == "regressive" and all(full_identity(i) for i in identity):
            raise ContractError(
                "MRG-EVIDENCE-001", "regressive requires an observed divergence, not full identity"
            )
    if doc["disposition"] == "superseded" and doc.get("supersededBy") is None:
        raise ContractError("MRG-DECISION-001", "superseded must name the revision that replaced it")
    if doc["disposition"] != "superseded" and doc.get("supersededBy") is not None:
        raise ContractError("MRG-DECISION-001", "only a superseded decision names a replacement")
    if doc.get("supersededBy") is not None:
        match("revision", doc["supersededBy"])

    actions = doc["actionsAuthorized"]
    if not isinstance(actions, list) or not actions or len(actions) != len(set(actions)):
        raise ContractError("MRG-DECISION-001", "authorized actions must be unique and nonempty")
    if not set(actions) <= ACTIONS:
        raise ContractError("MRG-DECISION-001", "unknown authorized action")
    allowed = EFFECT_FREE.get(doc["disposition"])
    if allowed is not None and not set(actions) <= allowed:
        raise ContractError("MRG-DECISION-001", "this disposition may only authorize effect-free actions")

    if doc["executor"] not in EXECUTORS:
        raise ContractError("MRG-DECISION-001", "unknown executor")
    if "merge" in actions:
        if doc["executor"] != "automated-validator":
            raise ContractError(
                "MRG-MERGE-001", "only the independent Validator may authorize merge",
            )
        gate_outcomes = [i for i in cited if i["evidenceKind"] == "gate-outcome"]
        if any(CHECKS_NOT_RUN in i["observation"] for i in gate_outcomes):
            raise ContractError(
                "MRG-MERGE-001",
                "a required check that never ran is not green",
            )
        satisfied = merge_gate_markers(cited)
        if satisfied != set(MERGE_PRECONDITIONS):
            raise ContractError(
                "MRG-MERGE-001",
                "a Validator merge must evidence every precondition it depends on",
            )
    destructive = bool(set(actions) & DESTRUCTIVE_ACTIONS)
    if doc["destructive"] is not destructive:
        raise ContractError("MRG-DECISION-001", "the destructive flag disagrees with the authorized actions")
    recovery = doc["recoveryRefs"]
    if not isinstance(recovery, list) or len(recovery) != len(set(recovery)):
        raise ContractError("MRG-REF-001", "recovery references must be unique")
    for item in recovery:
        match("recoveryRef", item)
    if destructive:
        if "recoverability" not in kinds:
            raise ContractError("MRG-RECOVERY-001", "a destructive decision needs recoverability evidence")
        if not recovery:
            raise ContractError("MRG-RECOVERY-001", "a destructive decision must name how to restore the work")
        if candidate["recoverable"] is False and not any(r.startswith("patch:") for r in recovery):
            raise ContractError(
                "MRG-RECOVERY-001", "uncommitted work needs a written patch, not a git reference"
            )
        if all(item["deterministic"] is False for item in cited):
            raise ContractError(
                "MRG-EVIDENCE-001", "advisory evidence alone cannot authorize a destructive action"
            )
    if "delete-branch" in actions and candidate["shape"] in UNRECOVERABLE_SHAPES:
        raise ContractError("MRG-DECISION-001", "an uncommitted shape has no branch to delete")
    return doc


def validate_receipt(doc: dict[str, Any], decision: dict[str, Any]) -> None:
    doc = closed(doc, RECEIPT_KEYS)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "receipt":
        raise ContractError("MRG-DOC-001", "wrong document family")
    if doc["decisionId"] != decision["decisionId"] or doc["candidateId"] != decision["candidateId"]:
        raise ContractError("MRG-REF-001", "receipt is bound to another decision")
    if doc["outcome"] not in OUTCOMES:
        raise ContractError("MRG-DOC-001", "unknown outcome")
    executed = doc["executedActions"]
    if not isinstance(executed, list) or len(executed) != len(set(executed)):
        raise ContractError("MRG-DOC-001", "executed actions must be unique")
    if not set(executed) <= set(decision["actionsAuthorized"]):
        raise ContractError("MRG-RECEIPT-001", "receipt executed an action the decision never authorized")
    if doc["secretsRedacted"] is not True:
        raise ContractError("MRG-SECRET-001", "a receipt must be redacted")
    if decision["destructive"] and not doc["recoveryRefs"]:
        raise ContractError("MRG-RECOVERY-001", "a destructive receipt must carry its recovery references")


EFFECT_FREE_ACTIONS = {"record-backlog", "no-action"}


def load_env_dsl() -> Any:
    """Load the vendored Env DSL checker from the exact file whose digest was checked.

    Loading by explicit path keeps the pin and the executed code the same
    object, and keeps this suite importable from any working directory.
    """
    if digest(ENV_DSL_PATH.read_bytes()) != ENV_DSL_DIGEST:
        raise ContractError("MRG-CONTRACT-001", "pinned Env DSL checker digest mismatch")
    spec = importlib.util.spec_from_file_location("merge_pinned_env_dsl", ENV_DSL_PATH)
    if spec is None or spec.loader is None:
        raise ContractError("MRG-CONTRACT-001", "pinned Env DSL checker is not loadable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def dsl_name(value: str) -> str:
    return value.upper().replace("-", "_")


def identity_reading(cited: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Read the broadest content-identity observation the decision cites."""
    records = [i for i in cited if i["evidenceKind"] == "content-identity" and i.get("coverage")]
    if not records:
        return 0, 0, 0
    best = max(records, key=lambda i: (i["coverage"]["total"], i["coverage"]["matched"]))
    coverage = best["coverage"]
    return coverage["total"], coverage["compared"], coverage["matched"]


def merge_gate_markers(cited: list[dict[str, Any]]) -> set[str]:
    """Read exact affirmative markers from deterministic gate observations.

    Free text, negated assignments and human observations cannot assert a
    merge precondition. The protected Validator still verifies the actual
    status source and exact head/base outside this descriptive contract.
    """
    allowed = set(MERGE_PRECONDITIONS)
    markers: set[str] = set()
    for item in cited:
        if (item["evidenceKind"] != "gate-outcome" or item["producer"] != "gate"
                or item["deterministic"] is not True):
            continue
        tokens = item["observation"].split()
        if tokens and set(tokens) <= allowed:
            markers.update(tokens)
    return markers


def facts_for(
    candidate: dict[str, Any], decision: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> dict[str, str]:
    """Project one decision onto the Env DSL fact constants."""
    cited = [evidence[i] for i in decision["evidenceIds"] if i in evidence]
    kinds = {item["evidenceKind"] for item in cited}
    total, compared, matched = identity_reading(cited)
    effectful = [a for a in decision["actionsAuthorized"] if a not in EFFECT_FREE_ACTIONS]
    def boolean(value: bool) -> str:
        return "TRUE" if value else "FALSE"

    facts = {
        "FACT_DISPOSITION": dsl_name(decision["disposition"]),
        "FACT_IDENTITY_TOTAL": str(total),
        "FACT_IDENTITY_COMPARED": str(compared),
        "FACT_IDENTITY_MATCHED": str(matched),
        "FACT_RECOVERY_REF_COUNT": str(len(decision["recoveryRefs"])),
        "FACT_DETERMINISTIC_EVIDENCE_COUNT": str(sum(1 for i in cited if i["deterministic"])),
        "FACT_EFFECTFUL_ACTION_COUNT": str(len(effectful)),
        "FACT_DESTRUCTIVE": boolean(decision["destructive"]),
        "FACT_PATCH_RECOVERY": boolean(any(r.startswith("patch:") for r in decision["recoveryRefs"])),
        "FACT_CANDIDATE_RECOVERABLE": boolean(candidate["recoverable"]),
        "FACT_HAS_REPLACEMENT": boolean(decision.get("supersededBy") is not None),
        "FACT_EXECUTOR": dsl_name(decision["executor"]),
        "FACT_AUTHORIZES_MERGE": boolean("merge" in decision["actionsAuthorized"]),
    }
    observed = {i["observation"] for i in cited if i["evidenceKind"] == "gate-outcome"}
    positive = merge_gate_markers(cited)
    for name in MERGE_PRECONDITIONS:
        facts[f"FACT_{dsl_name(name)}"] = boolean(name in positive)
    facts["FACT_REQUIRED_CHECKS_NOT_RUN"] = boolean(any(CHECKS_NOT_RUN in text for text in observed))
    for kind in sorted(EVIDENCE_KINDS):
        facts[f"FACT_HAS_{dsl_name(kind)}"] = boolean(kind in kinds)
    return facts


def dsl_admissible(
    candidate: dict[str, Any], decision: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> bool:
    """Evaluate the same rules through the pinned Env DSL evaluator."""
    env_dsl = load_env_dsl()
    document, diagnostics = env_dsl.parse_file(RULES_PATH)
    if document is None or diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the rule document is not valid Env DSL")
    merged, diagnostics = env_dsl.merge_documents([document])
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the rule document does not merge")
    merged.update(facts_for(candidate, decision, evidence))
    values, diagnostics = env_dsl.evaluate_constants(
        merged, {"ENV_DSL_ENVIRONMENT": document.environment}
    )
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", "rule evaluation reported diagnostics")
    result = values.get("DECISION_ADMISSIBLE_CONDITION")
    if not isinstance(result, bool):
        raise ContractError("MRG-CONTRACT-001", "admissibility must evaluate to a boolean")
    return result


def load_event_matrix(env_dsl: Any) -> tuple[Any, dict[str, str]]:
    document, diagnostics = env_dsl.parse_file(EVENTS_PATH)
    if document is None or diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the event matrix is not valid Env DSL")
    merged, diagnostics = env_dsl.merge_documents([document])
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the event matrix does not merge")
    return document, merged


def evaluate_events(env_dsl: Any, document: Any, merged: dict[str, str], event: str,
                    facts: dict[str, str] | None = None) -> dict[str, Any]:
    constants = {**merged, "FACT_EVENT": event, **(facts or {})}
    values, diagnostics = env_dsl.evaluate_constants(constants, {"ENV_DSL_ENVIRONMENT": document.environment})
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", f"event matrix evaluation reported diagnostics for {event}")
    return values


def validate_event_matrix() -> dict[str, Any]:
    """Every merge event resolves to exactly one autonomous, non-owner resolution.

    Only the Validator identity may lead to MERGED. The equations prove it for
    the document; this function additionally proves every event routes once,
    that mutations breaking an invariant are rejected, and that the human
    documentation lists the same matrix.
    """
    env_dsl = load_env_dsl()
    document, merged = load_event_matrix(env_dsl)
    events = sorted(name[len("ROUTE_"):-len("_CONDITION")] for name in merged
                    if name.startswith("ROUTE_") and name.endswith("_CONDITION"))
    if not events:
        raise ContractError("MRG-CONTRACT-001", "the event matrix declares no events")
    priorities: dict[str, int] = {}
    for event in events:
        fields = {field: merged.get(f"EVENT_{event}_{field}") for field in EVENT_FIELDS}
        if any(value is None for value in fields.values()):
            raise ContractError("MRG-CONTRACT-001", f"event {event} lacks a resolution field")
        if fields["ACTOR"] not in EVENT_ACTORS or fields["NEXT"] not in EVENT_STATES:
            raise ContractError("MRG-CONTRACT-001", f"event {event} names an undeclared actor or state")
        if fields["NOTIFY"] not in {"NONE", "OWNER"}:
            raise ContractError("MRG-CONTRACT-001", f"event {event} names an undeclared notice")
        if fields["NEXT"] == "MERGED" and fields["ACTOR"] != "VALIDATOR_AGENT":
            raise ContractError("MRG-CONTRACT-001", f"event {event} lets a non-Validator actor merge")
        priorities[event] = int(fields["PRIORITY"])
        facts = ({"FACT_PROTECTED_MERGE_RECEIPT_MATCHES_BRANCH": "TRUE"}
                 if event == "ORPHAN_BRANCH" else None)
        values = evaluate_events(env_dsl, document, merged, event, facts)
        routes = [name for name, value in values.items()
                  if name.startswith("ROUTE_") and name.endswith("_CONDITION") and value is True]
        if routes != [f"ROUTE_{event}_CONDITION"] or values.get("EVENT_RESOLVED_CONDITION") is not True:
            raise ContractError("MRG-CONTRACT-001", f"event {event} does not resolve to exactly one route")
    if len(set(priorities.values())) != len(priorities):
        raise ContractError("MRG-CONTRACT-001", "event priorities must be unique so concurrent events order deterministically")
    unknown = evaluate_events(env_dsl, document, merged, "UNDECLARED_EVENT")
    if unknown.get("EVENT_KNOWN_CONDITION") is not False or unknown.get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "an undeclared event must fail closed")
    unproved_merge = evaluate_events(env_dsl, document, merged, "ORPHAN_BRANCH")
    if unproved_merge.get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "merged-branch cleanup requires a matching protected merge receipt")
    contradicted_close = evaluate_events(env_dsl, document, merged, "CLOSED_UNMERGED_PR",
                                         {"FACT_PROTECTED_MERGE_RECEIPT_MATCHES_BRANCH": "TRUE"})
    if contradicted_close.get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "closed-unmerged preservation conflicts with a merge receipt")

    sample_event = events[0]
    mutations = {
        "interactive-agent-reaches-merged": {f"EVENT_{sample_event}_ACTOR": "INTERACTIVE_AGENT",
                                             f"EVENT_{sample_event}_NEXT": "MERGED"},
        "owner-as-actor": {f"EVENT_{sample_event}_ACTOR": "OWNER"},
        "non-autonomous-resolution": {f"EVENT_{sample_event}_AUTONOMOUS": "FALSE"},
    }
    rejected_mutations = []
    for case, change in mutations.items():
        values = evaluate_events(env_dsl, document, {**merged, **change}, sample_event)
        if values.get("EVENT_RESOLVED_CONDITION") is not False:
            raise AssertionError(f"the event matrix accepted {case}")
        rejected_mutations.append(case)
    for case, change in {
        "prune-closed-unmerged-branch": {"EVENT_CLOSED_UNMERGED_PR_ACTION": "PRUNE_WITH_RECOVERY_RECEIPT"},
        "close-without-owner-decision": {"EVENT_CLOSED_UNMERGED_PR_NEXT": "CLOSED"},
        "prune-without-recovery-receipt": {"EVENT_ORPHAN_BRANCH_ACTION": "PRUNE_MERGED_BRANCH"},
    }.items():
        values = evaluate_events(env_dsl, document, {**merged, **change}, "CLOSED_UNMERGED_PR")
        if values.get("EVENT_RESOLVED_CONDITION") is not False:
            raise AssertionError(f"the event matrix accepted {case}")
        rejected_mutations.append(case)

    documentation = EVENTS_DOC_PATH.read_text()
    for event in events:
        row = f"| {priorities[event]} | `{event}` |"
        actor, action, next_state = (merged[f"EVENT_{event}_{f}"] for f in ("ACTOR", "ACTION", "NEXT"))
        line = next((line for line in documentation.splitlines() if line.startswith(row)), None)
        if line is None or not all(f"`{v}`" in line for v in (actor, action, next_state)):
            raise ContractError("MRG-CONTRACT-001", f"docs/MERGE_EVENTS.md does not match the matrix for {event}")
    return {
        "document": "merge-events.env",
        "eventsDigest": "sha256:" + digest(EVENTS_PATH.read_bytes()),
        "events": events,
        "rejectedMutations": rejected_mutations,
    }


# Which validator answers which command, and which diagnostics the shared
# helpers raise on its behalf.
_COMMAND_VALIDATORS = {
    "validate_candidate": "merge.candidate.record",
    "validate_evidence": "merge.evidence.observe",
    "validate_decision": "merge.decision.record",
    "validate_receipt": "merge.action.execute",
}
_HELPER_CODES = {
    "closed": ("MRG-DOC-001",),
    "match": ("MRG-REF-001",),
    "refs": ("MRG-REF-001",),
    "reject_sensitive": ("MRG-SECRET-001",),
}


def raisable_codes(function: ast.FunctionDef) -> set[str]:
    """Read the diagnostics a validator can actually raise, from its own body."""
    found: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id == "ContractError" and node.args and isinstance(node.args[0], ast.Constant):
            found.add(node.args[0].value)
        found.update(_HELPER_CODES.get(node.func.id, ()))
    return found


def validate_rejection_surface() -> dict[str, list[str]]:
    """A command must declare every diagnostic its own validation can raise.

    Derived from this file rather than from a hand-kept list, because a
    rejection surface maintained by hand drifts the moment a rule is added: the
    command keeps refusing, and the catalogue stops saying so.
    """
    operations = json.loads(OPERATIONS_PATH.read_text())
    declared = {command["id"]: set(command["rejects"]) for command in operations["commands"]}
    tree = ast.parse(Path(__file__).read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    surface: dict[str, list[str]] = {}
    for name, command in _COMMAND_VALIDATORS.items():
        if name not in functions:
            raise ContractError("MRG-CQRS-001", "a declared command has no validator")
        actual = raisable_codes(functions[name])
        if command not in declared:
            raise ContractError("MRG-CQRS-001", "a validated command is absent from the registry")
        if actual != declared[command]:
            raise ContractError(
                "MRG-CQRS-001", "a command's declared rejections differ from what it can raise"
            )
        surface[command] = sorted(actual)
    return surface


def expect_rejected(
    name: str, code: str, validator: Callable[[dict[str, Any]], Any],
    base: dict[str, Any], mutation: Callable[[dict[str, Any]], None],
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
    evidence = {}
    for item in (
        {
            "evidenceId": "evidence:gate", "evidenceKind": "gate-outcome", "producer": "gate",
            "command": "./project/governance-check.sh --actor agent --base b --head HEAD",
            "observation": "GOV-FAIL: 4 errors (delivery contract absent, intent not plan-first, path owned by no workstream)",
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:history", "evidenceKind": "history-shape", "producer": "git",
            "command": "git log --format='%an: %s' origin/main..HEAD",
            "observation": "intent.json and its implementation land in one commit; original authorship must be preserved on rebuild",
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:intent", "evidenceKind": "intent-delta", "producer": "todo2code",
            "command": "t2c compare-workspace . --base origin/main --markdown-mode deterministic",
            "observation": "trend mixed; alignment flat 11.5%; implemented 14.1 to 13.9 percent; gaps 430 to 439",
            "deterministic": False,
        },
        {
            "evidenceId": "evidence:identity", "evidenceKind": "content-identity", "producer": "git",
            "command": "git diff --quiet origin/main -- <each changed path>",
            "observation": "0 of 32 changed files are already identical on the target",
            "coverage": {"compared": 32, "total": 32, "matched": 0}, "deterministic": True,
        },
        {
            "evidenceId": "evidence:recovery", "evidenceKind": "recoverability", "producer": "git",
            "command": "git rev-parse origin/fix/ticket-037-managed-eol",
            "observation": "branch tip recorded before deletion; rebased copies carry identical content",
            "deterministic": True,
        },
        {
            "evidenceId": "evidence:hearsay-identity", "evidenceKind": "content-identity", "producer": "human",
            "command": "read the diff by eye",
            "observation": "looked mostly the same as the target",
            "coverage": {"compared": 4, "total": 32, "matched": 4}, "deterministic": False,
        },
        {
            "evidenceId": "evidence:hearsay-recovery", "evidenceKind": "recoverability", "producer": "human",
            "command": "asked the author whether a copy exists",
            "observation": "author believes a copy exists somewhere",
            "deterministic": False,
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
        "evidenceIds": ["evidence:gate", "evidence:history", "evidence:intent", "evidence:identity", "evidence:recovery"],
        "rationale": "Intent is still live on the target, but the delivery cannot pass the gate as authored, so the history is rebuilt plan-first with authorship preserved.",
        "decidedBy": "actor://wellmanifest.com/maintainer",
        "actionsAuthorized": ["rebuild-history", "open-pull-request", "request-autonomous-merge", "delete-branch"],
        "executor": "interactive-agent",
        "destructive": True,
        "recoveryRefs": ["ref:5555555555555555555555555555555555555555"],
        "decidedAt": "2026-08-14T12:30:00Z",
    }
    receipt = {
        "schema": SCHEMA_FAMILY, "kind": "receipt", "decisionId": decision["decisionId"],
        "candidateId": candidate["candidateId"],
        "executedActions": ["rebuild-history", "open-pull-request", "delete-branch"],
        "outcome": "applied",
        "resultingRefs": ["subactor/intent-contract-dsl-runtime#15"],
        "recoveryRefs": ["ref:5555555555555555555555555555555555555555"],
        "secretsRedacted": True, "recordedAt": "2026-08-14T13:00:00Z",
    }
    return candidate, evidence, decision, receipt


def run_all() -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text())
    grammar = GRAMMAR_PATH.read_bytes()
    bindings = json.loads(BINDINGS_PATH.read_text())
    if (
        digest(canonical(schema)) != SCHEMA_DIGEST
        or digest(grammar) != GRAMMAR_DIGEST
        or digest(canonical(bindings)) != BINDINGS_DIGEST
        or digest(RULES_PATH.read_bytes()) != RULES_DIGEST
    ):
        raise ContractError("MRG-CONTRACT-001", "contract digest mismatch")
    if schema.get("$id") != SCHEMA_URI:
        raise ContractError("MRG-CONTRACT-001", "schema identity mismatch")
    for forbidden in (b"password", b"credential", b"token", b"http://"):
        if forbidden in grammar.lower():
            raise ContractError("MRG-SECRET-001", "unsafe grammar surface")
    bound_kinds = {item["evidenceKind"] for item in bindings["bindings"]}
    if not bound_kinds <= EVIDENCE_KINDS:
        raise ContractError("MRG-EVIDENCE-001", "a binding names an undeclared evidence kind")
    unbound = EVIDENCE_KINDS - bound_kinds
    if unbound:
        raise ContractError("MRG-EVIDENCE-001", "every evidence kind needs a producer binding")

    rejection_surface = validate_rejection_surface()
    candidate, evidence, decision, receipt = sample()
    validate_candidate(candidate)
    validate_decision(decision, candidate, evidence)
    validate_receipt(receipt, decision)

    check_candidate = validate_candidate

    def check_evidence(document: dict[str, Any]) -> dict[str, Any]:
        return validate_evidence(document, candidate)

    def check_decision(document: dict[str, Any]) -> dict[str, Any]:
        return validate_decision(document, candidate, evidence)

    def check_receipt(document: dict[str, Any]) -> None:
        validate_receipt(document, decision)

    staged = {**candidate, "shape": "staged-tree", "headRevision": None, "recoverable": False}

    rejected = [
        expect_rejected("uncommitted-claims-recoverable", "MRG-CANDIDATE-001", check_candidate, candidate,
                        lambda d: d.update(shape="staged-tree", headRevision=None)),
        expect_rejected("committed-without-head", "MRG-CANDIDATE-001", check_candidate, candidate,
                        lambda d: d.update(headRevision=None)),
        expect_rejected("anonymous-work", "MRG-CANDIDATE-001", check_candidate, candidate,
                        lambda d: d.update(authors=[])),
        expect_rejected("human-evidence-claims-determinism", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:gate"], lambda d: d.update(producer="human")),
        expect_rejected("evidence-without-command", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:gate"], lambda d: d.update(command="  ")),
        expect_rejected("impossible-coverage", "MRG-EVIDENCE-001", check_evidence,
                        evidence["evidence:identity"], lambda d: d.update(coverage={"compared": 3, "total": 32, "matched": 9})),
        expect_rejected("disposition-without-required-evidence", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(disposition="obsolete")),
        expect_rejected("already-implemented-on-partial-identity", "MRG-EVIDENCE-001", check_decision, decision,
                        lambda d: d.update(disposition="already-implemented",
                                           evidenceIds=["evidence:identity", "evidence:recovery"],
                                           actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[])),
        expect_rejected("superseded-without-replacement", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(disposition="superseded",
                                           evidenceIds=["evidence:identity", "evidence:recovery"],
                                           actionsAuthorized=["no-action"], destructive=False, recoveryRefs=[])),
        expect_rejected("replacement-on-non-superseded", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(supersededBy="a" * 40)),
        expect_rejected("defer-authorizes-effects", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(disposition="defer", evidenceIds=["evidence:intent"],
                                           actionsAuthorized=["delete-branch"], destructive=True)),
        expect_rejected("destructive-flag-disagrees", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(destructive=False)),
        expect_rejected("destructive-without-recovery-ref", "MRG-RECOVERY-001", check_decision, decision,
                        lambda d: d.update(recoveryRefs=[])),
        expect_rejected("destructive-without-recoverability-evidence", "MRG-RECOVERY-001", check_decision, decision,
                        lambda d: d.update(evidenceIds=["evidence:gate", "evidence:history"])),
        expect_rejected("advisory-evidence-authorizes-destruction", "MRG-EVIDENCE-001", check_decision, decision,
                        lambda d: d.update(disposition="regressive",
                                           evidenceIds=["evidence:hearsay-identity", "evidence:hearsay-recovery"],
                                           actionsAuthorized=["delete-branch"], destructive=True)),
        expect_rejected("unknown-evidence-cited", "MRG-REF-001", check_decision, decision,
                        lambda d: d["evidenceIds"].append("evidence:imagined")),
        expect_rejected("rationale-too-thin", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(rationale="ok")),
        expect_rejected("receipt-exceeds-authorization", "MRG-RECEIPT-001", check_receipt, receipt,
                        lambda d: d.update(executedActions=["discard-worktree"])),
        expect_rejected("destructive-receipt-without-recovery", "MRG-RECOVERY-001", check_receipt, receipt,
                        lambda d: d.update(recoveryRefs=[])),
        expect_rejected("receipt-not-redacted", "MRG-SECRET-001", check_receipt, receipt,
                        lambda d: d.update(secretsRedacted=False)),
        expect_rejected("interactive-agent-authorizes-merge", "MRG-MERGE-001", check_decision, decision,
                        lambda d: d.update(actionsAuthorized=["merge"], destructive=False,
                                           recoveryRefs=[], executor="interactive-agent")),
        expect_rejected("autonomous-merge-without-preconditions", "MRG-MERGE-001", check_decision, decision,
                        lambda d: d.update(actionsAuthorized=["merge"], destructive=False,
                                           recoveryRefs=[], executor="automated-validator")),
        expect_rejected("unknown-executor", "MRG-DECISION-001", check_decision, decision,
                        lambda d: d.update(executor="cron")),
    ]
    # The uncommitted case has its own recovery rule: a git reference is not enough.
    rejected.append(
        expect_rejected(
            "uncommitted-discard-with-git-ref-only", "MRG-RECOVERY-001",
            lambda d: validate_decision(d, staged, evidence), decision,
            lambda d: d.update(disposition="regressive", evidenceIds=["evidence:identity", "evidence:recovery"],
                               actionsAuthorized=["discard-worktree"], destructive=True,
                               recoveryRefs=["ref:5555555555555555555555555555555555555555"]),
        )
    )
    # The Env DSL rule document is the portable projection of the same rules.
    # Parity is asserted, not assumed: the equations must agree with this file
    # on the reference decision and on every mutation the equations can express.
    if not dsl_admissible(candidate, decision, evidence):
        raise ContractError("MRG-CONTRACT-001", "the rule equations reject the reference decision")
    parity = []
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
    # Missing required checks block every executor, even with passing local
    # tests or an observation claiming all other preconditions.
    not_run_evidence = dict(evidence)
    for item in (
        {"evidenceId": "evidence:hosted-not-run", "evidenceKind": "gate-outcome", "producer": "gate",
         "command": "gh pr checks --required",
         "observation": "required-checks-not-run: jobs not started (runner unavailable)", "deterministic": True},
        {"evidenceId": "evidence:claimed-preconditions", "evidenceKind": "gate-outcome", "producer": "gate",
         "command": "validator preconditions --exact-head",
         "observation": " ".join(MERGE_PRECONDITIONS), "deterministic": True},
        {"evidenceId": "evidence:local-tests", "evidenceKind": "gate-outcome", "producer": "gate",
         "command": "python3 -m pytest -q", "observation": "45 passed at the exact head", "deterministic": True},
    ):
        record = {"schema": SCHEMA_FAMILY, "kind": "evidence", "candidateId": candidate["candidateId"],
                  "observedAt": "2026-09-24T12:00:00Z", **item}
        not_run_evidence[record["evidenceId"]] = validate_evidence(record, candidate)

    def merge_on(executor: str, ids: list[str]) -> Callable[[dict[str, Any]], None]:
        return lambda d: d.update(actionsAuthorized=["merge"], destructive=False, recoveryRefs=[],
                                  executor=executor, evidenceIds=ids)

    not_run_cases = (
        ("validator-merge-on-checks-not-run",
         merge_on("automated-validator", ["evidence:hosted-not-run", "evidence:claimed-preconditions", "evidence:history"])),
        ("validator-merge-on-checks-not-run-with-local-tests",
         merge_on("automated-validator", ["evidence:hosted-not-run", "evidence:claimed-preconditions", "evidence:local-tests", "evidence:history"])),
        ("owner-merge-on-checks-not-run-with-local-tests",
         merge_on("owner", ["evidence:hosted-not-run", "evidence:claimed-preconditions", "evidence:local-tests", "evidence:history"])),
        ("owner-merge-with-all-preconditions",
         merge_on("owner", ["evidence:claimed-preconditions", "evidence:history"])),
    )
    for case, mutation in not_run_cases:
        rejected.append(expect_rejected(case, "MRG-MERGE-001",
                                        lambda d: validate_decision(d, candidate, not_run_evidence), decision, mutation))
        mutated = copy.deepcopy(decision)
        mutation(mutated)
        if dsl_admissible(candidate, mutated, not_run_evidence):
            raise AssertionError(f"the rule equations accepted {case}")
        parity.append(case)
    validator_with_preconditions = copy.deepcopy(decision)
    merge_on("automated-validator", ["evidence:claimed-preconditions", "evidence:history"])(validator_with_preconditions)
    validate_decision(validator_with_preconditions, candidate, not_run_evidence)
    if not dsl_admissible(candidate, validator_with_preconditions, not_run_evidence):
        raise AssertionError("the rule equations rejected a Validator merge with all preconditions")
    parity.append("validator-merge-with-all-preconditions")
    # The status words must form the entire deterministic gate observation;
    # a substring, prose assertion or human report cannot make a check green.
    for case, changes in (
        ("negated-check-marker", {"observation": " ".join(MERGE_PRECONDITIONS).replace(
            "required-checks-green", "required-checks-green=false")}),
        ("prose-check-marker", {"observation": "claimed: " + " ".join(MERGE_PRECONDITIONS)}),
        ("nondeterministic-check-marker", {"deterministic": False}),
        ("human-check-marker", {"producer": "human", "deterministic": False}),
    ):
        variant = dict(not_run_evidence)
        record = {**variant["evidence:claimed-preconditions"], **changes}
        variant[record["evidenceId"]] = validate_evidence(record, candidate)
        rejected.append(expect_rejected(case, "MRG-MERGE-001",
                                        lambda d: validate_decision(d, candidate, variant),
                                        validator_with_preconditions, lambda d: None))
        if dsl_admissible(candidate, validator_with_preconditions, variant):
            raise AssertionError(f"the rule equations accepted {case}")
        parity.append(case)

    staged_decision = copy.deepcopy(decision)
    staged_decision.update(disposition="regressive",
                           evidenceIds=["evidence:identity", "evidence:recovery"],
                           actionsAuthorized=["discard-worktree"], destructive=True)
    if dsl_admissible(staged, staged_decision, evidence):
        raise AssertionError("the rule equations accepted uncommitted-discard-with-git-ref-only")
    parity.append("uncommitted-discard-with-git-ref-only")

    return {
        "schema": "wellmanifest.merge-decision-conformance/v1",
        "ok": True,
        "positiveDocuments": 4,
        "rejectionSurface": rejection_surface,
        "ruleProjection": {
            "document": "merge-rules.env",
            "language": "wellmanifest/env-dsl",
            "sourceRevision": ENV_DSL_SOURCE_REVISION,
            "validatorDigest": "sha256:" + ENV_DSL_DIGEST,
            "rulesDigest": "sha256:" + RULES_DIGEST,
            "parityCases": parity,
        },
        "dispositions": sorted(DISPOSITIONS),
        "adversarialRejected": rejected,
        "schemaDigest": "sha256:" + SCHEMA_DIGEST,
        "grammarDigest": "sha256:" + GRAMMAR_DIGEST,
        "bindingsDigest": "sha256:" + BINDINGS_DIGEST,
        "eventMatrix": validate_event_matrix(),
        "cqrs": cqrs_conformance.run_all(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="wellmanifest.merge-decision/v1 conformance")
    parser.add_argument("--all", action="store_true")
    parser.parse_args()
    print(json.dumps(run_all(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
