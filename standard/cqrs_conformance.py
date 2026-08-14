#!/usr/bin/env python3
"""Dependency-free CQRS registry conformance for the merge standard."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS_PATH = ROOT / "operations/index.json"
OPERATIONS_SCHEMA_PATH = ROOT / "operations/registry.schema.json"
EVENTS_PATH = ROOT / "events/index.json"
ERRORS_PATH = ROOT / "error/index.json"

OPERATIONS_KEYS = {
    "$schema",
    "schema",
    "domain",
    "sourceOfTruth",
    "invariants",
    "models",
    "commands",
    "queries",
    "projections",
}
SOURCE_KEYS = {"commandsAndQueries", "events", "errors", "models", "transportRule"}
INVARIANT_KEYS = {
    "commandEffectsBecomeFactsOnlyThroughEvents",
    "queriesAreEffectFree",
    "replayExecutesEffects",
    "eventsCarryAuthority",
    "modelsCarryAuthority",
}
MODEL_KEYS = {"id", "schemaRef", "transport", "authority"}
COMMAND_KEYS = {
    "id",
    "uri",
    "intent",
    "inputModel",
    "authority",
    "inputCarriesAuthority",
    "idempotency",
    "effect",
    "emits",
    "rejects",
}
QUERY_KEYS = {
    "id",
    "uri",
    "intent",
    "inputModel",
    "outputModel",
    "cardinality",
    "projection",
    "consistency",
    "effect",
    "emits",
}
PROJECTION_KEYS = {
    "id",
    "intent",
    "outputModel",
    "cardinality",
    "rebuiltFrom",
    "reducer",
}
REDUCER_KEYS = {"version", "deterministic", "effects"}
EVENTS_KEYS = {"schema", "domain", "sourceOfTruth", "immutability", "events"}
IMMUTABILITY_KEYS = {"appendOnly", "eventsCarryAuthority", "replayExecutesEffects"}
EVENT_KEYS = {
    "id",
    "emittedBy",
    "payloadFields",
    "documentation",
    "authority",
    "replay",
}
REPLAY_KEYS = {"deterministic", "effects"}
ERRORS_KEYS = {"schema", "domain", "sourceOfTruth", "errors"}
ERROR_KEYS = {"code", "documentation", "retryability", "status", "rejectionEvent"}
STATUS_KEYS = {"http", "grpc"}

ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
COMMAND_URI_PATTERN = re.compile(r"^urn:wellmanifest:[a-z0-9-]+:command:[a-z0-9-]+$")
QUERY_URI_PATTERN = re.compile(r"^urn:wellmanifest:[a-z0-9-]+:query:[a-z0-9-]+$")
ERROR_PATTERN = re.compile(r"^MRG-[A-Z]+-[0-9]{3}$")


class CQRSContractError(ValueError):
    """Fail-closed diagnostic that never repeats untrusted document values."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise CQRSContractError("CQRS-DOC-001", "contract JSON is unreadable") from error
    if not isinstance(value, dict):
        raise CQRSContractError("CQRS-DOC-001", "contract root must be an object")
    return value


def exact(value: Any, keys: set[str], code: str, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CQRSContractError(code, f"{label} fields are not closed")
    return value


def records(value: Any, code: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        raise CQRSContractError(code, f"{label} must be a nonempty object list")
    return value


def unique(records_value: list[dict[str, Any]], field: str, code: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records_value:
        value = record.get(field)
        if not isinstance(value, str) or not value or value in result:
            raise CQRSContractError(code, f"{field} values must be nonempty and unique")
        result[value] = record
    return result


def unique_strings(value: Any, code: str, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise CQRSContractError(code, f"{label} must be a unique string list")
    if not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        raise CQRSContractError(code, f"{label} must be a unique string list")
    return value


def inside_root(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise CQRSContractError("CQRS-REF-001", "reference escapes the standard root") from error
    return resolved


def resolve_schema_ref(reference: str) -> None:
    if not isinstance(reference, str) or "#" not in reference:
        raise CQRSContractError("CQRS-MODEL-001", "model reference needs a file and JSON Pointer")
    file_name, fragment = reference.split("#", 1)
    if not file_name or not fragment.startswith("/"):
        raise CQRSContractError("CQRS-MODEL-001", "model reference is not a JSON Pointer")
    target = inside_root(OPERATIONS_PATH.parent / file_name)
    document = load_json(target)
    current: Any = document
    for raw_part in fragment[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise CQRSContractError("CQRS-MODEL-001", "model JSON Pointer does not resolve")
        current = current[part]
    if not isinstance(current, dict):
        raise CQRSContractError("CQRS-MODEL-001", "model JSON Pointer must resolve to an object schema")


def require_document(path_value: str, expected: str, snippets: tuple[str, ...], code: str) -> None:
    if path_value != expected:
        raise CQRSContractError(code, "documentation path does not match the stable identifier")
    path = inside_root(ROOT / path_value)
    try:
        text = path.read_text()
    except OSError as error:
        raise CQRSContractError(code, "documentation file is missing") from error
    if any(snippet not in text for snippet in snippets):
        raise CQRSContractError(code, "documentation skeleton is incomplete")


def validate_schema_contract() -> None:
    schema = load_json(OPERATIONS_SCHEMA_PATH)
    if schema.get("$id") != "https://wellmanifest.com/schemas/operations/v1":
        raise CQRSContractError("CQRS-DOC-001", "operation schema identity is wrong")
    if schema.get("additionalProperties") is not False:
        raise CQRSContractError("CQRS-DOC-001", "operation schema must be closed")
    if set(schema.get("required", [])) != OPERATIONS_KEYS:
        raise CQRSContractError("CQRS-DOC-001", "operation schema and registry top level differ")
    if set(schema.get("properties", {})) != OPERATIONS_KEYS:
        raise CQRSContractError("CQRS-DOC-001", "operation schema properties are incomplete")


def validate_documents(
    operations: dict[str, Any], events: dict[str, Any], errors: dict[str, Any]
) -> dict[str, int]:
    exact(operations, OPERATIONS_KEYS, "CQRS-DOC-001", "operation registry")
    if operations["$schema"] != "./registry.schema.json":
        raise CQRSContractError("CQRS-DOC-001", "operation registry schema reference is wrong")
    if operations["schema"] != "wellmanifest.operations/v1":
        raise CQRSContractError("CQRS-DOC-001", "operation registry family is wrong")

    source = exact(operations["sourceOfTruth"], SOURCE_KEYS, "CQRS-DOC-001", "sourceOfTruth")
    if source["commandsAndQueries"] != "operations/index.json":
        raise CQRSContractError("CQRS-DOC-001", "C/Q source of truth is not canonical")
    if source["events"] != "events/index.json" or source["errors"] != "error/index.json":
        raise CQRSContractError("CQRS-REF-001", "catalogue source reference is wrong")
    if not isinstance(source["transportRule"], str) or "do not" not in source["transportRule"]:
        raise CQRSContractError("CQRS-MODEL-001", "transport authority boundary is missing")

    invariants = exact(operations["invariants"], INVARIANT_KEYS, "CQRS-DOC-001", "invariants")
    expected_invariants = {
        "commandEffectsBecomeFactsOnlyThroughEvents": True,
        "queriesAreEffectFree": True,
        "replayExecutesEffects": False,
        "eventsCarryAuthority": False,
        "modelsCarryAuthority": False,
    }
    if invariants != expected_invariants:
        raise CQRSContractError("CQRS-DOC-001", "CQRS invariants are unsafe")

    model_records = records(operations["models"], "CQRS-MODEL-001", "models")
    models = unique(model_records, "id", "CQRS-MODEL-001")
    for model in model_records:
        exact(model, MODEL_KEYS, "CQRS-MODEL-001", "model")
        if not ID_PATTERN.fullmatch(model["id"]):
            raise CQRSContractError("CQRS-MODEL-001", "model id is invalid")
        if model["transport"] not in {"json-schema", "protobuf"} or model["authority"] is not False:
            raise CQRSContractError("CQRS-MODEL-001", "transport model carries unsafe semantics")
        resolve_schema_ref(model["schemaRef"])

    command_records = records(operations["commands"], "CQRS-COMMAND-001", "commands")
    commands = unique(command_records, "id", "CQRS-COMMAND-001")
    command_uris: set[str] = set()
    for command in command_records:
        exact(command, COMMAND_KEYS, "CQRS-COMMAND-001", "command")
        if not ID_PATTERN.fullmatch(command["id"]) or not COMMAND_URI_PATTERN.fullmatch(command["uri"]):
            raise CQRSContractError("CQRS-COMMAND-001", "command id or URI is invalid")
        if command["uri"] in command_uris:
            raise CQRSContractError("CQRS-COMMAND-001", "command URI is duplicated")
        command_uris.add(command["uri"])
        if command["inputModel"] not in models:
            raise CQRSContractError("CQRS-MODEL-001", "command input model is unknown")
        if (
            command["authority"] != "external-policy"
            or command["inputCarriesAuthority"] is not False
            or command["idempotency"] != "required"
        ):
            raise CQRSContractError("CQRS-COMMAND-001", "command authority boundary is unsafe")
        if command["effect"] not in {"append-events", "authorized-action-and-append-receipt"}:
            raise CQRSContractError("CQRS-COMMAND-001", "command effect class is unknown")
        unique_strings(command["emits"], "CQRS-COMMAND-001", "command emits")
        unique_strings(command["rejects"], "CQRS-COMMAND-001", "command rejects")

    projection_records = records(
        operations["projections"], "CQRS-PROJECTION-001", "projections"
    )
    projections = unique(projection_records, "id", "CQRS-PROJECTION-001")
    for projection in projection_records:
        exact(projection, PROJECTION_KEYS, "CQRS-PROJECTION-001", "projection")
        if not ID_PATTERN.fullmatch(projection["id"]):
            raise CQRSContractError("CQRS-PROJECTION-001", "projection id is invalid")
        if projection["outputModel"] not in models:
            raise CQRSContractError("CQRS-MODEL-001", "projection output model is unknown")
        if projection["cardinality"] not in {"one", "one-or-none", "many"}:
            raise CQRSContractError("CQRS-PROJECTION-001", "projection cardinality is invalid")
        unique_strings(
            projection["rebuiltFrom"], "CQRS-PROJECTION-001", "projection events"
        )
        reducer = exact(
            projection["reducer"], REDUCER_KEYS, "CQRS-PROJECTION-001", "reducer"
        )
        if (
            not isinstance(reducer["version"], int)
            or reducer["version"] < 1
            or reducer["deterministic"] is not True
            or reducer["effects"] is not False
        ):
            raise CQRSContractError("CQRS-PROJECTION-001", "projection reducer is unsafe")

    query_records = records(operations["queries"], "CQRS-QUERY-001", "queries")
    queries = unique(query_records, "id", "CQRS-QUERY-001")
    query_uris: set[str] = set()
    for query in query_records:
        exact(query, QUERY_KEYS, "CQRS-QUERY-001", "query")
        if not ID_PATTERN.fullmatch(query["id"]) or not QUERY_URI_PATTERN.fullmatch(query["uri"]):
            raise CQRSContractError("CQRS-QUERY-001", "query id or URI is invalid")
        if query["uri"] in query_uris:
            raise CQRSContractError("CQRS-QUERY-001", "query URI is duplicated")
        query_uris.add(query["uri"])
        if query["inputModel"] not in models or query["outputModel"] not in models:
            raise CQRSContractError("CQRS-MODEL-001", "query model is unknown")
        if query["projection"] not in projections:
            raise CQRSContractError("CQRS-PROJECTION-001", "query projection is unknown")
        if query["consistency"] not in {"strong", "eventual"}:
            raise CQRSContractError("CQRS-QUERY-001", "query consistency is invalid")
        if query["effect"] != "none" or query["emits"] != []:
            raise CQRSContractError("CQRS-QUERY-001", "query must be effect-free")
    if {query["projection"] for query in query_records} != set(projections):
        raise CQRSContractError("CQRS-PROJECTION-001", "projection is orphaned")

    exact(events, EVENTS_KEYS, "CQRS-EVENT-001", "event catalogue")
    if (
        events["schema"] != "wellmanifest.events/v1"
        or events["domain"] != operations["domain"]
        or events["sourceOfTruth"] != "operations/index.json"
    ):
        raise CQRSContractError("CQRS-EVENT-001", "event catalogue binding is wrong")
    immutability = exact(
        events["immutability"], IMMUTABILITY_KEYS, "CQRS-EVENT-001", "immutability"
    )
    if immutability != {
        "appendOnly": True,
        "eventsCarryAuthority": False,
        "replayExecutesEffects": False,
    }:
        raise CQRSContractError("CQRS-EVENT-001", "event catalogue is not append-only and safe")
    event_records = records(events["events"], "CQRS-EVENT-001", "events")
    event_map = unique(event_records, "id", "CQRS-EVENT-001")
    for event in event_records:
        exact(event, EVENT_KEYS, "CQRS-EVENT-001", "event")
        if not ID_PATTERN.fullmatch(event["id"]) or event["emittedBy"] not in commands:
            raise CQRSContractError("CQRS-EVENT-001", "event id or emitter is invalid")
        unique_strings(event["payloadFields"], "CQRS-EVENT-001", "event payload fields")
        if event["authority"] is not False:
            raise CQRSContractError("CQRS-EVENT-001", "event carries authority")
        replay = exact(event["replay"], REPLAY_KEYS, "CQRS-EVENT-001", "event replay")
        if replay != {"deterministic": True, "effects": False}:
            raise CQRSContractError("CQRS-EVENT-001", "event replay is unsafe")
        require_document(
            event["documentation"],
            f"events/{event['id']}.md",
            ("**Meaning.**", "**Emitted by.**", "**Payload fields.**", "## Replay"),
            "CQRS-EVENT-001",
        )
        if event["id"] not in commands[event["emittedBy"]]["emits"]:
            raise CQRSContractError("CQRS-EVENT-001", "event emitter relation is inconsistent")
    emitted = {item for command in command_records for item in command["emits"]}
    if emitted != set(event_map):
        raise CQRSContractError("CQRS-EVENT-001", "emitted event is missing or orphaned")
    rebuilt = {item for projection in projection_records for item in projection["rebuiltFrom"]}
    if rebuilt != set(event_map):
        raise CQRSContractError("CQRS-PROJECTION-001", "event is absent from projection rebuilds")

    exact(errors, ERRORS_KEYS, "CQRS-ERROR-001", "error catalogue")
    if (
        errors["schema"] != "wellmanifest.errors/v1"
        or errors["domain"] != operations["domain"]
        or errors["sourceOfTruth"] != "operations/index.json#/commands/*/rejects"
    ):
        raise CQRSContractError("CQRS-ERROR-001", "error catalogue binding is wrong")
    error_records = records(errors["errors"], "CQRS-ERROR-001", "errors")
    error_map = unique(error_records, "code", "CQRS-ERROR-001")
    for error in error_records:
        exact(error, ERROR_KEYS, "CQRS-ERROR-001", "error")
        if not ERROR_PATTERN.fullmatch(error["code"]):
            raise CQRSContractError("CQRS-ERROR-001", "error code is invalid")
        if error["retryability"] not in {"never", "after-correction", "after-new-evidence"}:
            raise CQRSContractError("CQRS-ERROR-001", "error retryability is invalid")
        status = exact(error["status"], STATUS_KEYS, "CQRS-ERROR-001", "error status")
        if not isinstance(status["http"], int) or status["grpc"] not in {
            "INVALID_ARGUMENT",
            "FAILED_PRECONDITION",
        }:
            raise CQRSContractError("CQRS-ERROR-001", "error status mapping is invalid")
        if error["rejectionEvent"] not in event_map:
            raise CQRSContractError("CQRS-ERROR-001", "error rejection event is unknown")
        require_document(
            error["documentation"],
            f"error/{error['code']}.md",
            ("**Meaning.**", "## What raises it", "## Why the rule exists", "## How to resolve it"),
            "CQRS-ERROR-001",
        )
    rejected = {item for command in command_records for item in command["rejects"]}
    if rejected != set(error_map):
        raise CQRSContractError("CQRS-ERROR-001", "public command rejection is missing or orphaned")

    used_models = {
        *(command["inputModel"] for command in command_records),
        *(query["inputModel"] for query in query_records),
        *(query["outputModel"] for query in query_records),
        *(projection["outputModel"] for projection in projection_records),
    }
    if used_models != set(models):
        raise CQRSContractError("CQRS-MODEL-001", "transport model is unused or missing")
    return {
        "models": len(models),
        "commands": len(commands),
        "queries": len(queries),
        "projections": len(projections),
        "events": len(event_map),
        "errors": len(error_map),
    }


def canonical_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def expect_rejected(
    name: str,
    code: str,
    operations: dict[str, Any],
    events: dict[str, Any],
    errors: dict[str, Any],
    mutation: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None],
) -> dict[str, str]:
    operation_copy = copy.deepcopy(operations)
    event_copy = copy.deepcopy(events)
    error_copy = copy.deepcopy(errors)
    mutation(operation_copy, event_copy, error_copy)
    try:
        validate_documents(operation_copy, event_copy, error_copy)
    except CQRSContractError as error:
        if error.code != code:
            raise AssertionError(f"{name} rejected with {error.code}, expected {code}") from error
        return {"case": name, "code": code}
    raise AssertionError(f"adversarial case accepted: {name}")


def run_all() -> dict[str, Any]:
    validate_schema_contract()
    operations = load_json(OPERATIONS_PATH)
    events = load_json(EVENTS_PATH)
    errors = load_json(ERRORS_PATH)
    counts = validate_documents(operations, events, errors)
    rejected = [
        expect_rejected(
            "duplicate-command-id",
            "CQRS-COMMAND-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["commands"].append(
                copy.deepcopy(operation["commands"][0])
            ),
        ),
        expect_rejected(
            "query-declares-effect",
            "CQRS-QUERY-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["queries"][0].update(
                effect="append-events"
            ),
        ),
        expect_rejected(
            "query-emits-event",
            "CQRS-QUERY-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["queries"][0].update(
                emits=["merge.candidate.recorded"]
            ),
        ),
        expect_rejected(
            "broken-model-pointer",
            "CQRS-MODEL-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["models"][0].update(
                schemaRef="../standard/merge-decision.schema.json#/$defs/missing"
            ),
        ),
        expect_rejected(
            "replay-executes-effects",
            "CQRS-EVENT-001",
            operations,
            events,
            errors,
            lambda _operation, event, _error: event["events"][0]["replay"].update(effects=True),
        ),
        expect_rejected(
            "event-emitter-disagrees",
            "CQRS-EVENT-001",
            operations,
            events,
            errors,
            lambda _operation, event, _error: event["events"][0].update(
                emittedBy="merge.evidence.observe"
            ),
        ),
        expect_rejected(
            "projection-omits-event",
            "CQRS-PROJECTION-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["projections"][1]["rebuiltFrom"].pop(),
        ),
        expect_rejected(
            "duplicate-error-code",
            "CQRS-ERROR-001",
            operations,
            events,
            errors,
            lambda _operation, _event, error: error["errors"].append(
                copy.deepcopy(error["errors"][0])
            ),
        ),
        expect_rejected(
            "unregistered-command-rejection",
            "CQRS-ERROR-001",
            operations,
            events,
            errors,
            lambda operation, _event, _error: operation["commands"][0]["rejects"].append(
                "MRG-UNKNOWN-001"
            ),
        ),
    ]
    return {
        "schema": "wellmanifest.cqrs-conformance/v1",
        "ok": True,
        **counts,
        "adversarialRejected": rejected,
        "digests": {
            "operations": canonical_digest(operations),
            "events": canonical_digest(events),
            "errors": canonical_digest(errors),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Wellmanifest CQRS registry conformance")
    parser.add_argument("--all", action="store_true")
    parser.parse_args()
    print(json.dumps(run_all(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
