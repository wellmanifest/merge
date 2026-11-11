"""Core data contracts and validators for wellmanifest.merge-decision/v1."""

from __future__ import annotations

import ast
import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any

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

SHAPES = {
    "remote-branch", "local-branch", "unpushed-commit", "staged-tree", "worktree", "pull-request",
}
UNRECOVERABLE_SHAPES = {"staged-tree", "worktree"}
DISPOSITIONS = {
    "adopt", "rebuild", "already-implemented", "superseded", "regressive", "obsolete", "defer",
}
EVIDENCE_KINDS = {
    "content-identity", "patch-equivalence", "reachability", "intent-delta", "gate-outcome",
    "code-liveness", "dependency-evidence", "history-shape", "recoverability",
}
PRODUCERS = {"git", "gate", "todo2code", "code2llm", "deconnected", "giton", "human"}
ACTIONS = {
    "open-pull-request", "request-autonomous-merge", "merge", "rebuild-history",
    "delete-branch", "discard-worktree", "record-backlog", "no-action",
}
EXECUTORS = {"interactive-agent", "automated-validator", "owner"}
MERGE_PRECONDITIONS = (
    "in-scan-matrix", "in-scan-config", "ticket-derivable",
    "required-checks-green", "approved-at-exact-head", "standing-merge-policy",
)
CHECKS_NOT_RUN = "required-checks-not-run"
DESTRUCTIVE_ACTIONS = {"delete-branch", "discard-worktree", "rebuild-history"}
EFFECT_FREE_ACTIONS = {"record-backlog", "no-action"}
OUTCOMES = {"applied", "partially-applied", "blocked", "abandoned"}

REQUIRED_EVIDENCE: dict[str, set[str]] = {
    "adopt": {"gate-outcome", "reachability"},
    "rebuild": {"gate-outcome", "history-shape"},
    "already-implemented": {"content-identity"},
    "superseded": {"patch-equivalence"},
    "regressive": {"content-identity"},
    "obsolete": {"dependency-evidence"},
    "defer": {"intent-delta"},
}
EFFECT_FREE = {"defer": {"record-backlog", "no-action"}}

PATTERNS = {
    "candidateId": r"^candidate:[a-z0-9][a-z0-9._-]{0,95}$",
    "evidenceId": r"^evidence:[a-z0-9][a-z0-9._-]{0,95}$",
    "decisionId": r"^decision:[a-z0-9][a-z0-9._-]{0,95}$",
    "repository": r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$",
    "gitRef": r"^[A-Za-z0-9][A-Za-z0-9._/-]*$",
    "revision": r"^[0-9a-f]{40}$",
    "actorRef": r"^actor://[a-z0-9][a-z0-9.-]*/[A-Za-z0-9._:-]+$",
    "recoveryRef": r"^(?:ref|patch|tag):[A-Za-z0-9._:/-]+$",
    "digest": r"^sha256:[0-9a-f]{64}$",
    "timestamp": (
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]{1,9})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
    ),
}
MAX_LENGTHS = {
    "repository": 160,
    "gitRef": 160,
    "actorRef": 240,
    "recoveryRef": 320,
    "timestamp": 40,
}
SENSITIVE = re.compile(
    r"(?:password|passwd|token|secret|credential|api[-_]?key|cookie|private[-_]?key)",
    re.IGNORECASE,
)
SENSITIVE_VALUE = re.compile(
    r"(?:\bBearer\s+[A-Za-z0-9._~+/-]{16,}|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----)",
    re.IGNORECASE,
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


def reject_no_symlink(path: Path) -> None:
    cur = Path(path.anchor) if path.is_absolute() else Path()
    parts = path.parts[1:] if path.is_absolute() else path.parts
    for part in parts:
        cur = cur / part
        if cur.is_symlink():
            raise ContractError("MRG-CONTRACT-001", "symlinked contract artifact is forbidden")


def strict_json_load(path: Path) -> Any:
    reject_no_symlink(path)

    def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, val in pairs:
            if key in out:
                raise ContractError("MRG-CONTRACT-001", "duplicate JSON key in contract")
            out[key] = val
        return out

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("MRG-CONTRACT-001", "contract JSON is unreadable") from error


def _is_nonneg_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _is_unique_str_list(
    value: Any, *, min_items: int = 0, max_items: int = 32, max_len: int | None = None
) -> bool:
    if not isinstance(value, list) or not (min_items <= len(value) <= max_items):
        return False
    if not all(isinstance(item, str) and bool(item.strip()) for item in value):
        return False
    if max_len is not None and any(len(item) > max_len for item in value):
        return False
    return len(value) == len(set(value))


def reject_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str) or (key not in SAFE_ASSERTIONS and SENSITIVE.search(key)):
                raise ContractError("MRG-SECRET-001", "unsafe key")
            reject_sensitive(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_sensitive(nested)
    elif isinstance(value, str) and SENSITIVE_VALUE.search(value):
        raise ContractError("MRG-SECRET-001", "unsafe secret material in value")


def closed(doc: Any, keys: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise ContractError("MRG-DOC-001", "expected an object")
    optional = optional or set()
    if set(doc) - keys or (keys - optional) - set(doc):
        raise ContractError("MRG-DOC-001", "document fields are not closed")
    return doc


def match(name: str, value: Any) -> str:
    max_len = MAX_LENGTHS.get(name)
    if (
        not isinstance(value, str)
        or (max_len is not None and len(value) > max_len)
        or not re.fullmatch(PATTERNS[name], value)
    ):
        raise ContractError("MRG-REF-001", f"invalid reference: {name}")
    if name == "timestamp":
        try:
            datetime.datetime.fromisoformat(value)
        except ValueError as error:
            raise ContractError("MRG-REF-001", "invalid timestamp calendar value") from error
    return value


def merge_gate_markers(cited: list[dict[str, Any]]) -> set[str]:
    allowed = set(MERGE_PRECONDITIONS)
    markers: set[str] = set()
    for item in cited:
        if (
            item["evidenceKind"] != "gate-outcome"
            or item["producer"] != "gate"
            or item["deterministic"] is not True
        ):
            continue
        tokens = item["observation"].split()
        if tokens and set(tokens) <= allowed:
            markers.update(tokens)
    return markers


def full_identity(evidence: dict[str, Any]) -> bool:
    coverage = evidence.get("coverage")
    if not coverage or coverage["total"] == 0:
        return False
    return coverage["compared"] == coverage["total"] and coverage["matched"] == coverage["total"]


def validate_candidate(doc: dict[str, Any]) -> dict[str, Any]:
    doc = closed(doc, CANDIDATE_KEYS, CANDIDATE_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "candidate":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("candidateId", doc["candidateId"])
    match("repository", doc["repository"])
    match("gitRef", doc["ref"])
    match("gitRef", doc["baseRef"])
    match("revision", doc["baseRevision"])
    match("timestamp", doc["lastActivity"])
    if doc["shape"] not in SHAPES:
        raise ContractError("MRG-DOC-001", "unknown candidate shape")
    head_rev = doc.get("headRevision")
    if head_rev is not None:
        match("revision", head_rev)
    elif doc["shape"] not in UNRECOVERABLE_SHAPES:
        raise ContractError("MRG-CANDIDATE-001", "a committed candidate must name its head revision")
    if not _is_nonneg_int(doc["ahead"]) or not _is_nonneg_int(doc["behind"]):
        raise ContractError("MRG-DOC-001", "ahead and behind must be non-negative integers")
    if not isinstance(doc["recoverable"], bool):
        raise ContractError("MRG-DOC-001", "recoverable must be a boolean")
    if doc["shape"] in UNRECOVERABLE_SHAPES and doc["recoverable"] is not False:
        raise ContractError(
            "MRG-CANDIDATE-001", "an uncommitted shape is not recoverable from git alone"
        )
    if "intent" in doc and (not isinstance(doc["intent"], str) or len(doc["intent"]) > 320):
        raise ContractError("MRG-DOC-001", "intent must be a bounded string")
    authors = doc["authors"]
    if (
        not isinstance(authors, list)
        or not (1 <= len(authors) <= 16)
        or not all(isinstance(a, str) and bool(a.strip()) and len(a) <= 120 for a in authors)
    ):
        raise ContractError("MRG-CANDIDATE-001", "a candidate must name whose work it is")
    return doc


def validate_evidence(doc: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    doc = closed(doc, EVIDENCE_KEYS, EVIDENCE_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "evidence":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("evidenceId", doc["evidenceId"])
    match("timestamp", doc["observedAt"])
    if match("candidateId", doc["candidateId"]) != candidate["candidateId"]:
        raise ContractError("MRG-REF-001", "evidence is bound to another candidate")
    if doc["evidenceKind"] not in EVIDENCE_KINDS:
        raise ContractError("MRG-EVIDENCE-001", "unknown evidence kind")
    if doc["producer"] not in PRODUCERS:
        raise ContractError("MRG-EVIDENCE-001", "unknown producer")
    cmd = doc["command"]
    if not isinstance(cmd, str) or len(cmd.strip()) < 3 or len(cmd) > 400:
        raise ContractError("MRG-EVIDENCE-001", "evidence must name a bounded command")
    obs = doc["observation"]
    if not isinstance(obs, str) or len(obs.strip()) < 3 or len(obs) > 800:
        raise ContractError("MRG-EVIDENCE-001", "evidence must carry a bounded observation")
    if not isinstance(doc["deterministic"], bool):
        raise ContractError("MRG-DOC-001", "deterministic must be a boolean")
    if doc.get("artifactDigest") is not None:
        match("digest", doc["artifactDigest"])
    if doc["producer"] == "human" and doc["deterministic"] is not False:
        raise ContractError("MRG-EVIDENCE-001", "a human observation is never deterministic")
    coverage = doc.get("coverage")
    if coverage is not None:
        closed(coverage, {"compared", "total", "matched"})
        if not all(_is_nonneg_int(coverage[k]) for k in ("compared", "total", "matched")):
            raise ContractError("MRG-EVIDENCE-001", "coverage counts must be non-negative integers")
        if coverage["compared"] > coverage["total"] or coverage["matched"] > coverage["compared"]:
            raise ContractError("MRG-EVIDENCE-001", "coverage counts are inconsistent")
    return doc


def validate_decision(
    doc: dict[str, Any], candidate: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    doc = closed(doc, DECISION_KEYS, DECISION_OPTIONAL)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "decision":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("decisionId", doc["decisionId"])
    match("timestamp", doc["decidedAt"])
    if match("candidateId", doc["candidateId"]) != candidate["candidateId"]:
        raise ContractError("MRG-REF-001", "decision is bound to another candidate")
    match("actorRef", doc["decidedBy"])
    if doc["disposition"] not in DISPOSITIONS:
        raise ContractError("MRG-DECISION-001", "unknown disposition")
    rat = doc["rationale"]
    if not isinstance(rat, str) or len(rat.strip()) < 10 or len(rat) > 800:
        raise ContractError("MRG-DECISION-001", "a decision must state a bounded rationale")
    if not isinstance(doc["destructive"], bool):
        raise ContractError("MRG-DOC-001", "destructive must be a boolean")

    ids = doc["evidenceIds"]
    if not _is_unique_str_list(ids, min_items=1, max_items=32):
        raise ContractError("MRG-REF-001", "evidence references must be unique and nonempty")
    cited: list[dict[str, Any]] = []
    for item in ids:
        match("evidenceId", item)
        if item not in evidence:
            raise ContractError("MRG-REF-001", "decision cites unknown evidence")
        cited.append(evidence[item])
    kinds = {item["evidenceKind"] for item in cited}

    if not REQUIRED_EVIDENCE[doc["disposition"]] <= kinds:
        raise ContractError("MRG-DECISION-001", "disposition lacks the evidence its rule requires")

    if doc["disposition"] in {"already-implemented", "regressive"}:
        identity = [i for i in cited if i["evidenceKind"] == "content-identity"]
        if doc["disposition"] == "already-implemented" and not any(
            full_identity(i) for i in identity
        ):
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
    if not _is_unique_str_list(actions, min_items=1, max_items=8):
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
                "MRG-MERGE-001", "only the independent Validator may authorize merge"
            )
        gate_outcomes = [i for i in cited if i["evidenceKind"] == "gate-outcome"]
        if any(CHECKS_NOT_RUN in i["observation"] for i in gate_outcomes):
            raise ContractError("MRG-MERGE-001", "a required check that never ran is not green")
        if merge_gate_markers(cited) != set(MERGE_PRECONDITIONS):
            raise ContractError(
                "MRG-MERGE-001",
                "a Validator merge must evidence every precondition it depends on",
            )
    destructive = bool(set(actions) & DESTRUCTIVE_ACTIONS)
    if doc["destructive"] is not destructive:
        raise ContractError("MRG-DECISION-001", "the destructive flag disagrees with actions")
    recovery = doc["recoveryRefs"]
    if not _is_unique_str_list(recovery, min_items=0, max_items=8):
        raise ContractError("MRG-REF-001", "recovery references must be unique")
    for item in recovery:
        match("recoveryRef", item)
    if destructive:
        if "recoverability" not in kinds:
            raise ContractError("MRG-RECOVERY-001", "destructive decision needs recoverability")
        if not recovery:
            raise ContractError("MRG-RECOVERY-001", "destructive decision must name recovery")
        if candidate["recoverable"] is False and not any(r.startswith("patch:") for r in recovery):
            raise ContractError("MRG-RECOVERY-001", "uncommitted work needs a written patch")
        if all(item["deterministic"] is False for item in cited):
            raise ContractError(
                "MRG-EVIDENCE-001", "advisory evidence alone cannot authorize destruction"
            )
    if "delete-branch" in actions and candidate["shape"] in UNRECOVERABLE_SHAPES:
        raise ContractError("MRG-DECISION-001", "an uncommitted shape has no branch to delete")
    return doc


def validate_receipt(doc: dict[str, Any], decision: dict[str, Any]) -> None:
    doc = closed(doc, RECEIPT_KEYS)
    reject_sensitive(doc)
    if doc["schema"] != SCHEMA_FAMILY or doc["kind"] != "receipt":
        raise ContractError("MRG-DOC-001", "wrong document family")
    match("decisionId", doc["decisionId"])
    match("candidateId", doc["candidateId"])
    match("timestamp", doc["recordedAt"])
    if doc["decisionId"] != decision["decisionId"] or doc["candidateId"] != decision["candidateId"]:
        raise ContractError("MRG-REF-001", "receipt is bound to another decision")
    if doc["outcome"] not in OUTCOMES:
        raise ContractError("MRG-DOC-001", "unknown outcome")
    executed = doc["executedActions"]
    if not _is_unique_str_list(executed, min_items=0, max_items=8):
        raise ContractError("MRG-DOC-001", "executed actions must be unique strings")
    if not set(executed) <= set(decision["actionsAuthorized"]):
        raise ContractError("MRG-RECEIPT-001", "receipt executed an unauthorized action")
    if not _is_unique_str_list(doc["resultingRefs"], min_items=0, max_items=16, max_len=200):
        raise ContractError("MRG-DOC-001", "resultingRefs must be bounded unique strings")
    recovery = doc["recoveryRefs"]
    if not _is_unique_str_list(recovery, min_items=0, max_items=8):
        raise ContractError("MRG-REF-001", "recovery references must be unique")
    for item in recovery:
        match("recoveryRef", item)
    if doc["secretsRedacted"] is not True:
        raise ContractError("MRG-SECRET-001", "a receipt must be redacted")
    if decision["destructive"] and not recovery:
        raise ContractError("MRG-RECOVERY-001", "a destructive receipt must carry recoveryRefs")


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
    found: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if (
            node.func.id == "ContractError"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            found.add(node.args[0].value)
        found.update(_HELPER_CODES.get(node.func.id, ()))
    return found


def validate_rejection_surface() -> dict[str, list[str]]:
    operations = strict_json_load(OPERATIONS_PATH)
    declared = {command["id"]: set(command["rejects"]) for command in operations["commands"]}
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    surface: dict[str, list[str]] = {}
    for name, command in _COMMAND_VALIDATORS.items():
        if name not in functions:
            raise ContractError("MRG-CQRS-001", "a declared command has no validator")
        actual = raisable_codes(functions[name])
        if command not in declared:
            raise ContractError("MRG-CQRS-001", "a validated command is absent from registry")
        if actual != declared[command]:
            raise ContractError(
                "MRG-CQRS-001", "a command's declared rejections differ from what it can raise"
            )
        surface[command] = sorted(actual)
    return surface
