"""Fail-closed validation for S5 public packets and shared workspaces."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import date
from typing import Any, Literal, Optional, Union, get_args, get_origin, get_type_hints

from mm_r5 import public_authority_common as common
from mm_r5.s5_authority_adapter import (
    S5AuthorityAdapterError,
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
)
from mm_r5.s5_contracts import (
    DOMAIN_SUBTYPE_MATRIX,
    DOMAINS,
    JOURNEY_SUBTYPES,
    S5AEMHPacket,
    S5AudienceEncodingRegistry,
    S5AudienceLexicon,
    S5SubjectTemporalPacket,
    S5SubjectWorkspaceContract,
    LEGACY_SEVERITY_MAPPING,
    FORBIDDEN_AUDIENCE_TERMS,
    RISK_OVERLAY_SHAPE,
    SEVERITIES,
    build_audience_encoding_registry,
    build_audience_lexicon,
    S5RuntimeImplementationError,
    s5_as_mapping,
)
from mm_r5.s5_projection import project_subject_workspace


@dataclasses.dataclass(frozen=True)
class S5ValidationIssue:
    code: str
    path: str
    message_zh: str = ""

    def __post_init__(self) -> None:
        if type(self.code) is not str or type(self.path) is not str:
            raise TypeError("S5ValidationIssue code/path must be str")
        if not self.message_zh:
            object.__setattr__(self, "message_zh", f"核对未通过：{self.path}（{self.code}）")


@dataclasses.dataclass(frozen=True)
class S5ValidationResult:
    ok: bool
    primary_code: Optional[str]
    issues: tuple[S5ValidationIssue, ...]
    expected_packet: Any = None
    packet_emitted: bool = False

    @property
    def projection(self) -> str:
        return "emitted" if self.ok and self.packet_emitted else "not_emitted"

    @property
    def code(self) -> Optional[str]:
        return self.primary_code

    def __bool__(self) -> bool:
        return self.ok


def _issue(code: str, path: str) -> S5ValidationIssue:
    return S5ValidationIssue(code=code, path=path)


def _result(code: Optional[str], path: str, expected: Any = None) -> S5ValidationResult:
    if code is None:
        return S5ValidationResult(True, None, (), expected, True)
    issue = _issue(code, path)
    return S5ValidationResult(False, code, (issue,), expected, False)


def _type_spec(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Literal:
        return ("literal", get_args(annotation))
    if origin is Union:
        args = get_args(annotation)
        non_none = tuple(item for item in args if item is not type(None))
        if len(non_none) != 1 or len(args) != 2:
            raise S5RuntimeImplementationError(f"unsupported S5 union annotation {annotation!r}")
        return ("optional", _type_spec(non_none[0]))
    if origin in (tuple, list):
        args = get_args(annotation)
        if len(args) != 2 or args[1] is not Ellipsis:
            raise S5RuntimeImplementationError(f"unsupported S5 tuple annotation {annotation!r}")
        return ("list", _type_spec(args[0]))
    if annotation is str:
        return ("scalar", str)
    if annotation is int:
        return ("scalar", int)
    if annotation is bool:
        return ("scalar", bool)
    if annotation is date:
        return ("date", date)
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return ("object", annotation)
    raise S5RuntimeImplementationError(f"unsupported S5 annotation {annotation!r}")


_SPEC_CACHE: dict[type, dict[str, Any]] = {}


def _class_spec(cls: type) -> dict[str, Any]:
    if cls not in _SPEC_CACHE:
        hints = get_type_hints(cls)
        _SPEC_CACHE[cls] = {field.name: _type_spec(hints[field.name]) for field in dataclasses.fields(cls)}
    return _SPEC_CACHE[cls]


def _structural_error(spec: Any, value: Any, path: str) -> Optional[S5ValidationIssue]:
    kind = spec[0]
    if kind == "optional":
        return None if value is None else _structural_error(spec[1], value, path)
    if kind == "literal":
        return None if type(value) is str and value in spec[1] else _issue("SCHEMA_KEY_MISMATCH", path)
    if kind == "scalar":
        expected_type = spec[1]
        return None if type(value) is expected_type else _issue("SCHEMA_KEY_MISMATCH", path)
    if kind == "date":
        if type(value) is not str:
            return _issue("SCHEMA_KEY_MISMATCH", path)
        try:
            date.fromisoformat(value)
        except ValueError:
            return _issue("SCHEMA_KEY_MISMATCH", path)
        return None
    if kind == "list":
        if type(value) is not list:
            return _issue("SCHEMA_KEY_MISMATCH", path)
        for index, item in enumerate(value):
            issue = _structural_error(spec[1], item, f"{path}/{index}")
            if issue is not None:
                return issue
        return None
    if kind == "object":
        if type(value) is not dict:
            return _issue("SCHEMA_KEY_MISMATCH", path)
        expected = _class_spec(spec[1])
        if set(value) != set(expected):
            return _issue("SCHEMA_KEY_MISMATCH", path)
        for field, child_spec in expected.items():
            issue = _structural_error(child_spec, value[field], f"{path}/{field}")
            if issue is not None:
                return issue
        return None
    raise S5RuntimeImplementationError(f"unknown structural spec {spec!r}")


def _candidate_mapping(candidate: Any, expected_type: type) -> dict[str, Any]:
    if type(candidate) is expected_type:
        mapped = s5_as_mapping(candidate)
        if not isinstance(mapped, dict):
            raise S5RuntimeImplementationError("typed S5 candidate did not serialize as object")
        return mapped
    if isinstance(candidate, Mapping):
        return dict(candidate)
    raise S5RuntimeImplementationError(
        f"candidate must be Mapping or {expected_type.__name__}, got {type(candidate).__name__}"
    )


def _first_difference(expected: Any, candidate: Any, path: str = "") -> Optional[tuple[str, Any, Any]]:
    if type(expected) is not type(candidate):
        return path or "/", expected, candidate
    if isinstance(expected, dict):
        if set(expected) != set(candidate):
            return path or "/", expected, candidate
        for key in expected:
            difference = _first_difference(expected[key], candidate[key], f"{path}/{key}")
            if difference is not None:
                return difference
        return None
    if isinstance(expected, list):
        if len(expected) != len(candidate):
            return path or "/", expected, candidate
        for index, (left, right) in enumerate(zip(expected, candidate)):
            difference = _first_difference(left, right, f"{path}/{index}")
            if difference is not None:
                return difference
        return None
    return None if expected == candidate else (path or "/", expected, candidate)


def _path_contains(path: str, token: str) -> bool:
    return f"/{token}/" in path or path.endswith(f"/{token}")


def _semantic_code(path: str, expected: Any, actual: Any, root: dict[str, Any]) -> str:
    # Receipt and projection identity are deliberately checked before generic
    # content hashes so a re-signed candidate cannot hide a binding drift.
    if path == "/receipt/receipt_id":
        return "RECEIPT_BINDING_MISMATCH"
    if path == "/receipt/public_projection_content_hash":
        return "PROJECTION_HASH_MISMATCH"
    if path.startswith("/receipt/scope_identity/"):
        return "SCOPE_IDENTITY_MISMATCH"
    if path == "/projection/receipt_ref":
        return "RECEIPT_BINDING_MISMATCH"
    if path == "/projection/projection_id" or path == "/projection/projection_content_hash":
        return "PROJECTION_HASH_MISMATCH"
    if path == "/projection/scope_identity/subject_ref":
        return "SCOPE_IDENTITY_MISMATCH"
    if path == "/projection/scope_identity/spine_ref":
        return "SECOND_TEMPORAL_SPINE"
    if path.startswith("/projection/events/") and path.endswith("/event_ref"):
        visits = root.get("projection", {}).get("visits", [])
        if actual in {item.get("visit_ref") for item in visits if isinstance(item, dict)} or (
            isinstance(actual, str) and actual.startswith("visit")
        ):
            return "VISIT_EVENT_AXIS_MISMATCH"
    if "/domain_tracks/" in path and path.endswith("/applicability_state"):
        return "APPLICABILITY_STATE_DRIFT"
    if path.startswith("/projection/events/") and path.endswith("/domain"):
        if actual not in DOMAINS:
            return "UNKNOWN_DOMAIN_FAIL_CLOSED"
        return "DOMAIN_SUBTYPE_MISMATCH"
    if path.startswith("/projection/events/") and path.endswith("/subtype"):
        if actual not in JOURNEY_SUBTYPES:
            return "UNKNOWN_SUBTYPE_FAIL_CLOSED"
        return "DOMAIN_SUBTYPE_MISMATCH"
    if "/projection/" in path and (
        "/start_endpoint" in path or "/end_endpoint" in path or path.endswith("/cutoff_endpoint")
    ):
        if path.endswith("/state") and actual == "exact":
            # An exact state without an exact date is geometry-invalid,
            # regardless of whether the source state was missing or partial.
            endpoint_path = path.rsplit("/", 1)[0]
            endpoint = _lookup(root, endpoint_path)
            if isinstance(endpoint, dict) and endpoint.get("exact_date") is None:
                return "DATE_GEOMETRY_MISMATCH"
        if path.endswith("/exact_date") and actual is not None:
            endpoint_path = path.rsplit("/", 1)[0]
            endpoint = _lookup(root, endpoint_path)
            if isinstance(endpoint, dict) and endpoint.get("state") == "missing":
                return "DATE_STATE_LOSS"
        if path.endswith("/exact_date") and actual is None:
            endpoint_path = path.rsplit("/", 1)[0]
            endpoint = _lookup(root, endpoint_path)
            if isinstance(endpoint, dict) and endpoint.get("state") == "exact":
                return "DATE_GEOMETRY_MISMATCH"
        return "DATE_STATE_LOSS"
    if "/projection/accepted_thread_prefixes" in path:
        return "AEMH_PREFIX_NOT_RETAINED"
    if "/projection/threads/" in path and (
        "/history_entries/" in path or path.endswith("/history_entries")
    ):
        if path.endswith("/later_fact_content_identities") or "/later_fact_content_identities/" in path:
            return "AEMH_IDENTITY_REWRITE"
        if path.endswith("/risk_lifecycle_effect") and actual != "none":
            return "AEMH_AUTOMATIC_CLOSURE"
        return "AEMH_HISTORY_NOT_APPEND_ONLY"
    return "S5_PACKET_MISMATCH"


def _lookup(root: Any, path: str) -> Any:
    value = root
    for part in path.strip("/").split("/"):
        if part == "":
            continue
        try:
            value = value[int(part)] if isinstance(value, list) else value[part]
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    return value


def _validate_packet(candidate: Any, expected: Any, expected_type: type) -> S5ValidationResult:
    expected_mapping = s5_as_mapping(expected)
    candidate_mapping = _candidate_mapping(candidate, expected_type)
    issue = _structural_error(("object", expected_type), candidate_mapping, "")
    # The closed enum remains fail-closed, but the S5 registry assigns a more
    # useful stable oracle to an unknown event domain/subtype than a generic
    # schema label.  Let those two scalar leaves reach the semantic gate.
    if issue is not None and issue.code == "SCHEMA_KEY_MISMATCH":
        structural_value = _lookup(candidate_mapping, issue.path)
        if issue.path.endswith("/domain") and type(structural_value) is str:
            issue = None
        elif issue.path.endswith("/subtype") and type(structural_value) is str:
            issue = None
        elif issue.path.endswith("/risk_lifecycle_effect") and type(structural_value) is str:
            issue = None
        elif "/projection/" in issue.path and (
            "/start_endpoint" in issue.path or "/end_endpoint" in issue.path
            or issue.path.endswith("/cutoff_endpoint")
        ):
            # A dropped range leaf is a date-state loss even when a malformed
            # candidate omitted the nested key entirely.
            issue = None
    if issue is not None:
        return S5ValidationResult(False, issue.code, (issue,), expected, False)
    difference = _first_difference(expected_mapping, candidate_mapping)
    if difference is None:
        return _result(None, "", expected)
    path, expected_value, actual_value = difference
    code = _semantic_code(path, expected_value, actual_value, candidate_mapping)
    return _result(code, path, expected)


def _expected_subject(source: common.AuthorityBundleV02) -> S5SubjectTemporalPacket:
    try:
        return adapt_subject_temporal_authority(source)
    except S5AuthorityAdapterError as exc:
        raise S5RuntimeImplementationError(f"trusted subject authority rejected: {exc.code}") from exc


def _expected_aemh(source: common.AuthorityBundleV02) -> S5AEMHPacket:
    try:
        return adapt_aemh_match_history_authority(source)
    except S5AuthorityAdapterError as exc:
        raise S5RuntimeImplementationError(f"trusted AEMH authority rejected: {exc.code}") from exc


def validate_subject_temporal_packet(
    candidate: Mapping[str, Any] | S5SubjectTemporalPacket,
    source: common.AuthorityBundleV02,
) -> S5ValidationResult:
    if type(source) is not common.AuthorityBundleV02 or source.target_contract != common.SUBJECT_CONTRACT_ID:
        raise S5RuntimeImplementationError("subject validation requires typed subject AuthorityBundleV02")
    expected = _expected_subject(source)
    return _validate_packet(candidate, expected, S5SubjectTemporalPacket)


def validate_aemh_match_history_packet(
    candidate: Mapping[str, Any] | S5AEMHPacket,
    source: common.AuthorityBundleV02,
) -> S5ValidationResult:
    if type(source) is not common.AuthorityBundleV02 or source.target_contract != common.AEMH_CONTRACT_ID:
        raise S5RuntimeImplementationError("AEMH validation requires typed AEMH AuthorityBundleV02")
    expected = _expected_aemh(source)
    return _validate_packet(candidate, expected, S5AEMHPacket)


def validate_s5_authority_packet(
    candidate: Mapping[str, Any] | S5SubjectTemporalPacket | S5AEMHPacket,
    source: common.AuthorityBundleV02,
) -> S5ValidationResult:
    if type(source) is not common.AuthorityBundleV02:
        raise S5RuntimeImplementationError("S5 validation requires typed AuthorityBundleV02")
    if source.target_contract == common.SUBJECT_CONTRACT_ID:
        return validate_subject_temporal_packet(candidate, source)  # type: ignore[arg-type]
    if source.target_contract == common.AEMH_CONTRACT_ID:
        return validate_aemh_match_history_packet(candidate, source)  # type: ignore[arg-type]
    raise S5RuntimeImplementationError("unknown S5 authority target")


def validate_s5_packet(candidate: Any, source: common.AuthorityBundleV02) -> S5ValidationResult:
    return validate_s5_authority_packet(candidate, source)


def validate_domain_subtype_pair(domain: str, subtype: str) -> S5ValidationResult:
    """Validate the closed domain/subtype matrix before any projection."""
    if domain not in DOMAINS:
        return _result("UNKNOWN_DOMAIN_FAIL_CLOSED", "/projection/events/0/domain")
    if subtype not in JOURNEY_SUBTYPES:
        return _result("UNKNOWN_SUBTYPE_FAIL_CLOSED", "/projection/events/0/subtype")
    if subtype not in DOMAIN_SUBTYPE_MATRIX[domain]:
        return _result("DOMAIN_SUBTYPE_MISMATCH", "/projection/events/0/subtype")
    return _result(None, "")


def validate_legacy_severity(value: str) -> S5ValidationResult:
    if value not in LEGACY_SEVERITY_MAPPING:
        return _result("LEGACY_SEVERITY_FAIL_CLOSED", "/audience_constants/legacy_severity_mapping")
    return _result(None, "")


def validate_audience_term(value: str) -> S5ValidationResult:
    if value in FORBIDDEN_AUDIENCE_TERMS:
        return _result("FORBIDDEN_AUDIENCE_TERM", "/audience_constants/forbidden_terms")
    return _result(None, "")


def validate_legacy_treatment_mapping(
    legacy_kind: str,
    mapping_state: str,
    mapping_authority_ref: Optional[str] = None,
    target_domain: Optional[str] = None,
    target_subtype: Optional[str] = None,
) -> S5ValidationResult:
    if legacy_kind not in ("background_treatment", "non_drug_treatment"):
        return _result("LEGACY_TREATMENT_FAIL_CLOSED", "/audience_constants/legacy_treatment_mapping")
    if mapping_state == "mapped" and (
        mapping_authority_ref is None or target_domain is None or target_subtype is None
    ):
        return _result("LEGACY_TREATMENT_FAIL_CLOSED", "/audience_constants/legacy_treatment_mapping")
    if mapping_state not in ("mapped", "unmapped_fail_closed"):
        return _result("LEGACY_TREATMENT_FAIL_CLOSED", "/audience_constants/legacy_treatment_mapping")
    return _result(None, "")


def _validate_audience(candidate: Any, expected: Any, expected_type: type) -> S5ValidationResult:
    expected_mapping = s5_as_mapping(expected)
    candidate_mapping = _candidate_mapping(candidate, expected_type)
    issue = _structural_error(("object", expected_type), candidate_mapping, "")
    if issue is not None:
        # Unknown domain values have an explicit semantic oracle; retain the
        # fail-closed result while still rejecting the malformed registry.
        if issue.path.endswith("/domain") and type(_lookup(candidate_mapping, issue.path)) is str:
            return _result("UNKNOWN_DOMAIN_FAIL_CLOSED", issue.path, expected)
        if issue.path.startswith("/domain_items/") and issue.path.endswith("/event_shape"):
            # Collision with the separate risk overlay vocabulary is a
            # semantic encoding failure, not merely an unknown enum value.
            if type(_lookup(candidate_mapping, issue.path)) is str:
                issue = None
        if issue is not None:
            return S5ValidationResult(False, issue.code, (issue,), expected, False)
    difference = _first_difference(expected_mapping, candidate_mapping)
    if difference is None:
        return _result(None, "", expected)
    path, expected_value, actual_value = difference
    if path.startswith("/domain_items/") and path.endswith("/domain"):
        values = [item.get("domain") for item in candidate_mapping["domain_items"]]
        code = "DOMAIN_REGISTRY_NOT_BIJECTIVE" if actual_value in values[:int(path.split('/')[2])] else "UNKNOWN_DOMAIN_FAIL_CLOSED"
    elif path.startswith("/domain_items/") and path.endswith("/event_shape"):
        index = int(path.split("/")[2])
        domain = candidate_mapping["domain_items"][index].get("domain")
        code = "RISK_EVENT_SHAPE_COLLISION" if actual_value == RISK_OVERLAY_SHAPE else (
            "SYMPTOM_EFFICACY_SHAPE_COLLISION" if domain == "symptom_efficacy" else "S5_AUDIENCE_MISMATCH"
        )
    elif path.startswith("/severity_items/") and path.endswith("/severity"):
        code = "SEVERITY_PROMOTION" if expected_value == "high" and actual_value == "critical" else "S5_AUDIENCE_MISMATCH"
    elif path.startswith("/legacy_treatment_mapping/"):
        row = candidate_mapping["legacy_treatment_mapping"][int(path.split("/")[2])]
        code = "LEGACY_TREATMENT_FAIL_CLOSED" if row.get("mapping_state") == "mapped" else "S5_AUDIENCE_MISMATCH"
    else:
        code = "S5_AUDIENCE_MISMATCH"
    return _result(code, path, expected)


def validate_audience_encoding_registry(
    candidate: Mapping[str, Any] | S5AudienceEncodingRegistry,
) -> S5ValidationResult:
    return _validate_audience(candidate, build_audience_encoding_registry(), S5AudienceEncodingRegistry)


def validate_audience_lexicon(
    candidate: Mapping[str, Any] | S5AudienceLexicon,
) -> S5ValidationResult:
    expected = build_audience_lexicon()
    result = _validate_audience(candidate, expected, S5AudienceLexicon)
    if result.ok:
        return result
    if result.primary_code == "S5_AUDIENCE_MISMATCH":
        mapping = _candidate_mapping(candidate, S5AudienceLexicon)
        difference = _first_difference(s5_as_mapping(expected), mapping)
        if difference is not None and "/forbidden_terms" in difference[0]:
            if difference[2] in FORBIDDEN_AUDIENCE_TERMS:
                return _result("FORBIDDEN_AUDIENCE_TERM", difference[0], expected)
    return result


def validate_s5_subject_workspace(
    candidate: Mapping[str, Any] | S5SubjectWorkspaceContract,
    expected_or_subject: S5SubjectWorkspaceContract | S5SubjectTemporalPacket,
    aemh_packet: Optional[S5AEMHPacket] = None,
    **kwargs: Any,
) -> S5ValidationResult:
    if type(expected_or_subject) is S5SubjectWorkspaceContract:
        expected = expected_or_subject
    elif type(expected_or_subject) is S5SubjectTemporalPacket:
        try:
            expected = project_subject_workspace(expected_or_subject, aemh_packet, **kwargs)
        except Exception as exc:
            raise S5RuntimeImplementationError("unable to rebuild expected workspace") from exc
    else:
        raise S5RuntimeImplementationError("workspace validation requires typed expected workspace or subject packet")
    expected_mapping = s5_as_mapping(expected)
    candidate_mapping = _candidate_mapping(candidate, S5SubjectWorkspaceContract)
    wrapper = isinstance(candidate_mapping, dict) and set(candidate_mapping) == {"workspace"}
    if wrapper and isinstance(candidate_mapping.get("workspace"), dict):
        candidate_mapping = candidate_mapping["workspace"]
    issue = _structural_error(("object", S5SubjectWorkspaceContract), candidate_mapping, "")
    if issue is not None:
        return S5ValidationResult(False, issue.code, (issue,), expected, False)
    difference = _first_difference(expected_mapping, candidate_mapping)
    if difference is None:
        return _result(None, "", expected)
    path, expected_value, actual_value = difference
    if "/view_bindings/" in path and path.endswith("/spine_ref"):
        code = "SHARED_SPINE_MISMATCH"
    elif path in ("/shared_context/window_start", "/shared_context/window_end"):
        code = "SHARED_WINDOW_MISMATCH"
    elif path == "/shared_context/selection_anchor/anchor_ref":
        code = "SELECTION_ANCHOR_NOT_MEMBER"
    elif "/view_bindings/" in path and path.endswith("/authority_projection_id"):
        code = "UI_STATE_AS_AUTHORITY"
    elif path in ("/spine_ref", "/shared_context/spine_ref"):
        code = "SHARED_SPINE_MISMATCH"
    elif path.startswith("/shared_context/") or path.startswith("/view_bindings/"):
        code = "SHARED_CONTEXT_MISMATCH"
    else:
        code = "S5_WORKSPACE_MISMATCH"
    if wrapper:
        path = "/workspace" + path
    return _result(code, path, expected)


validate_workspace = validate_s5_subject_workspace
validate_subject_workspace = validate_s5_subject_workspace
validate_aemh_packet = validate_aemh_match_history_packet
validate_subject_packet = validate_subject_temporal_packet
validate_subject_temporal_authority = validate_subject_temporal_packet
validate_aemh_match_history_authority = validate_aemh_match_history_packet


__all__ = [
    "S5ValidationIssue", "S5ValidationResult",
    "validate_domain_subtype_pair", "validate_s5_authority_packet",
    "validate_s5_packet", "validate_subject_temporal_packet",
    "validate_aemh_match_history_packet", "validate_subject_packet",
    "validate_aemh_packet", "validate_s5_subject_workspace",
    "validate_subject_workspace", "validate_workspace",
    "validate_subject_temporal_authority", "validate_aemh_match_history_authority",
    "validate_legacy_severity", "validate_audience_term",
    "validate_legacy_treatment_mapping", "validate_audience_encoding_registry",
    "validate_audience_lexicon",
]
