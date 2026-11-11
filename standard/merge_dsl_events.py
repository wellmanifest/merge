"""Env DSL rule projection and merge-events.env conformance evaluator."""

from __future__ import annotations

import importlib.util
import sys
from typing import Any

from merge_contracts import (
    CHECKS_NOT_RUN,
    EFFECT_FREE_ACTIONS,
    ENV_DSL_DIGEST,
    ENV_DSL_PATH,
    EVENTS_DOC_PATH,
    EVENTS_PATH,
    EVIDENCE_KINDS,
    MERGE_PRECONDITIONS,
    RULES_PATH,
    ContractError,
    digest,
    merge_gate_markers,
    reject_no_symlink,
)

EVENT_ACTORS = {"INTERACTIVE_AGENT", "ONEDEV_AGENT", "VALIDATOR_AGENT"}
EVENT_STATES = {
    "DRAFT",
    "AWAITING_CHECKS",
    "AWAITING_LOCAL_VERIFY",
    "AWAITING_VALIDATOR",
    "AWAITING_ENROLLMENT",
    "AWAITING_OWNER_DECISION",
    "CHANGES_REQUIRED",
    "REPLANNING",
    "SERIALIZED",
    "MERGED",
    "CLOSED",
}
EVENT_FIELDS = ("ACTOR", "ACTION", "NEXT", "NOTIFY", "PRIORITY", "BLOCKS_MERGE", "AUTONOMOUS")


def load_env_dsl() -> Any:
    reject_no_symlink(ENV_DSL_PATH)
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
    records = [i for i in cited if i["evidenceKind"] == "content-identity" and i.get("coverage")]
    if not records:
        return 0, 0, 0
    best = max(records, key=lambda i: (i["coverage"]["total"], i["coverage"]["matched"]))
    coverage = best["coverage"]
    return coverage["total"], coverage["compared"], coverage["matched"]


def facts_for(
    candidate: dict[str, Any], decision: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> dict[str, str]:
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
        "FACT_PATCH_RECOVERY": boolean(
            any(r.startswith("patch:") for r in decision["recoveryRefs"])
        ),
        "FACT_CANDIDATE_RECOVERABLE": boolean(candidate["recoverable"]),
        "FACT_HAS_REPLACEMENT": boolean(decision.get("supersededBy") is not None),
        "FACT_EXECUTOR": dsl_name(decision["executor"]),
        "FACT_AUTHORIZES_MERGE": boolean("merge" in decision["actionsAuthorized"]),
    }
    observed = {i["observation"] for i in cited if i["evidenceKind"] == "gate-outcome"}
    positive = merge_gate_markers(cited)
    for name in MERGE_PRECONDITIONS:
        facts[f"FACT_{dsl_name(name)}"] = boolean(name in positive)
    facts["FACT_REQUIRED_CHECKS_NOT_RUN"] = boolean(
        any(CHECKS_NOT_RUN in text for text in observed)
    )
    for kind in sorted(EVIDENCE_KINDS):
        facts[f"FACT_HAS_{dsl_name(kind)}"] = boolean(kind in kinds)
    return facts


def dsl_admissible(
    candidate: dict[str, Any], decision: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> bool:
    reject_no_symlink(RULES_PATH)
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
    reject_no_symlink(EVENTS_PATH)
    document, diagnostics = env_dsl.parse_file(EVENTS_PATH)
    if document is None or diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the event matrix is not valid Env DSL")
    merged, diagnostics = env_dsl.merge_documents([document])
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", "the event matrix does not merge")
    return document, merged


def evaluate_events(
    env_dsl: Any,
    document: Any,
    merged: dict[str, str],
    event: str,
    facts: dict[str, str] | None = None,
) -> dict[str, Any]:
    constants = {**merged, "FACT_EVENT": event, **(facts or {})}
    values, diagnostics = env_dsl.evaluate_constants(
        constants, {"ENV_DSL_ENVIRONMENT": document.environment}
    )
    if diagnostics:
        raise ContractError("MRG-CONTRACT-001", f"event matrix diagnostics for {event}")
    return values


def validate_event_matrix() -> dict[str, Any]:
    env_dsl = load_env_dsl()
    document, merged = load_event_matrix(env_dsl)
    events = sorted(
        name[len("ROUTE_") : -len("_CONDITION")]
        for name in merged
        if name.startswith("ROUTE_") and name.endswith("_CONDITION")
    )
    if not events:
        raise ContractError("MRG-CONTRACT-001", "the event matrix declares no events")
    priorities: dict[str, int] = {}
    for event in events:
        fields = {field: merged.get(f"EVENT_{event}_{field}") for field in EVENT_FIELDS}
        if any(value is None for value in fields.values()):
            raise ContractError("MRG-CONTRACT-001", f"event {event} lacks a resolution field")
        if fields["ACTOR"] not in EVENT_ACTORS or fields["NEXT"] not in EVENT_STATES:
            raise ContractError("MRG-CONTRACT-001", f"event {event} names an undeclared actor")
        if fields["NOTIFY"] not in {"NONE", "OWNER"}:
            raise ContractError("MRG-CONTRACT-001", f"event {event} names an undeclared notice")
        if fields["NEXT"] == "MERGED" and fields["ACTOR"] != "VALIDATOR_AGENT":
            raise ContractError("MRG-CONTRACT-001", f"event {event} lets non-Validator merge")
        priorities[event] = int(fields["PRIORITY"] or "0")
        facts = (
            {"FACT_PROTECTED_MERGE_RECEIPT_MATCHES_BRANCH": "TRUE"}
            if event == "ORPHAN_BRANCH"
            else None
        )
        values = evaluate_events(env_dsl, document, merged, event, facts)
        routes = [
            name
            for name, val in values.items()
            if name.startswith("ROUTE_") and name.endswith("_CONDITION") and val is True
        ]
        if routes != [f"ROUTE_{event}_CONDITION"] or values.get("EVENT_RESOLVED_CONDITION") is not True:
            raise ContractError("MRG-CONTRACT-001", f"event {event} does not resolve uniquely")
    if len(set(priorities.values())) != len(priorities):
        raise ContractError("MRG-CONTRACT-001", "event priorities must be unique")
    unknown = evaluate_events(env_dsl, document, merged, "UNDECLARED_EVENT")
    if unknown.get("EVENT_KNOWN_CONDITION") is not False or unknown.get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "an undeclared event must fail closed")
    if evaluate_events(env_dsl, document, merged, "ORPHAN_BRANCH").get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "merged-branch cleanup requires merge receipt")
    contradicted = evaluate_events(
        env_dsl,
        document,
        merged,
        "CLOSED_UNMERGED_PR",
        {"FACT_PROTECTED_MERGE_RECEIPT_MATCHES_BRANCH": "TRUE"},
    )
    if contradicted.get("EVENT_RESOLVED_CONDITION") is not False:
        raise ContractError("MRG-CONTRACT-001", "closed-unmerged conflicts with merge receipt")

    sample_event = events[0]
    mutations = {
        "interactive-agent-reaches-merged": {
            f"EVENT_{sample_event}_ACTOR": "INTERACTIVE_AGENT",
            f"EVENT_{sample_event}_NEXT": "MERGED",
        },
        "owner-as-actor": {f"EVENT_{sample_event}_ACTOR": "OWNER"},
        "non-autonomous-resolution": {f"EVENT_{sample_event}_AUTONOMOUS": "FALSE"},
    }
    rejected_mutations: list[str] = []
    for case, change in mutations.items():
        if evaluate_events(env_dsl, document, {**merged, **change}, sample_event).get("EVENT_RESOLVED_CONDITION") is not False:
            raise AssertionError(f"the event matrix accepted {case}")
        rejected_mutations.append(case)
    for case, change in {
        "prune-closed-unmerged-branch": {
            "EVENT_CLOSED_UNMERGED_PR_ACTION": "PRUNE_WITH_RECOVERY_RECEIPT"
        },
        "close-without-owner-decision": {"EVENT_CLOSED_UNMERGED_PR_NEXT": "CLOSED"},
        "prune-without-recovery-receipt": {"EVENT_ORPHAN_BRANCH_ACTION": "PRUNE_MERGED_BRANCH"},
    }.items():
        if evaluate_events(env_dsl, document, {**merged, **change}, "CLOSED_UNMERGED_PR").get("EVENT_RESOLVED_CONDITION") is not False:
            raise AssertionError(f"the event matrix accepted {case}")
        rejected_mutations.append(case)

    reject_no_symlink(EVENTS_DOC_PATH)
    documentation = EVENTS_DOC_PATH.read_text(encoding="utf-8")
    for event in events:
        row = f"| {priorities[event]} | `{event}` |"
        actor, action, next_state = (
            merged[f"EVENT_{event}_{f}"] for f in ("ACTOR", "ACTION", "NEXT")
        )
        line = next((ln for ln in documentation.splitlines() if ln.startswith(row)), None)
        if line is None or not all(f"`{v}`" in line for v in (actor, action, next_state)):
            raise ContractError(
                "MRG-CONTRACT-001", f"docs/MERGE_EVENTS.md does not match matrix for {event}"
            )
    return {
        "document": "merge-events.env",
        "eventsDigest": "sha256:" + digest(EVENTS_PATH.read_bytes()),
        "events": events,
        "rejectedMutations": rejected_mutations,
    }
