#!/usr/bin/env python3
"""Dependency-free semantic conformance for wellmanifest.merge-decision/v1.

The rules here are the reusable part of the standard: which evidence each
disposition owes before it may be recorded, and what a destructive decision
must carry so the work it destroys can come back.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import cqrs_conformance
from merge_adversarial import (
    expect_rejected,
    run_adversarial_and_parity,
    sample,
    verify_loader_hardening,
)
from merge_contracts import (
    BINDINGS_DIGEST,
    BINDINGS_PATH,
    DISPOSITIONS,
    ENV_DSL_DIGEST,
    ENV_DSL_SOURCE_REVISION,
    EVIDENCE_KINDS,
    GRAMMAR_DIGEST,
    GRAMMAR_PATH,
    ROOT,
    RULES_DIGEST,
    RULES_PATH,
    SCHEMA_DIGEST,
    SCHEMA_PATH,
    SCHEMA_URI,
    ContractError,
    canonical,
    closed,
    digest,
    full_identity,
    match,
    merge_gate_markers,
    reject_no_symlink,
    reject_sensitive,
    strict_json_load,
    validate_candidate,
    validate_decision,
    validate_evidence,
    validate_receipt,
    validate_rejection_surface,
)
from merge_dsl_events import (
    dsl_admissible,
    facts_for,
    identity_reading,
    load_env_dsl,
    validate_event_matrix,
)

OWNED_MODULES = (
    "conformance.py",
    "merge_contracts.py",
    "merge_dsl_events.py",
    "merge_adversarial.py",
    "cqrs_conformance.py",
)


def run_all() -> dict[str, Any]:
    for owned_py in OWNED_MODULES:
        line_count = len((ROOT / owned_py).read_text(encoding="utf-8").splitlines())
        if line_count >= 500:
            raise ContractError("MRG-CONTRACT-001", f"{owned_py} exceeds 500-line budget")

    verify_loader_hardening()
    reject_no_symlink(GRAMMAR_PATH)
    reject_no_symlink(RULES_PATH)
    schema = strict_json_load(SCHEMA_PATH)
    grammar = GRAMMAR_PATH.read_bytes()
    bindings = strict_json_load(BINDINGS_PATH)
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
    if bound_kinds != EVIDENCE_KINDS:
        raise ContractError("MRG-EVIDENCE-001", "evidence kind bindings mismatch")

    rejection_surface = validate_rejection_surface()
    candidate, evidence, decision, receipt = sample()
    validate_candidate(candidate)
    uncommitted_omitted = {k: v for k, v in candidate.items() if k != "headRevision"}
    uncommitted_omitted.update(shape="staged-tree", recoverable=False)
    validate_candidate(uncommitted_omitted)
    validate_decision(decision, candidate, evidence)
    validate_receipt(receipt, decision)

    rejected, parity = run_adversarial_and_parity(candidate, evidence, decision, receipt)
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


__all__ = [
    "ContractError",
    "canonical",
    "closed",
    "digest",
    "dsl_admissible",
    "expect_rejected",
    "facts_for",
    "full_identity",
    "identity_reading",
    "load_env_dsl",
    "main",
    "match",
    "merge_gate_markers",
    "reject_sensitive",
    "run_all",
    "sample",
    "validate_candidate",
    "validate_decision",
    "validate_event_matrix",
    "validate_evidence",
    "validate_receipt",
    "validate_rejection_surface",
]


if __name__ == "__main__":
    raise SystemExit(main())
