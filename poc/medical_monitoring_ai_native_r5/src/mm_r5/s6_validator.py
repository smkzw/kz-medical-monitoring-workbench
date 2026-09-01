"""Fail-closed validators for the synthetic/offline S6 runtime surface."""

from __future__ import annotations

import dataclasses
import types
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, Literal, Optional, Union, get_args, get_origin, get_type_hints

from mm_r5.s5_contracts import S5SubjectTemporalPacket
from mm_r5.s6_contracts import (
    AXIS_MODES,
    DOMAINS,
    EVENT_FORBIDDEN_SHAPES,
    KEYBOARD_SCOPES,
    S6AudienceEncodingRegistry,
    S6CanonicalReturnState,
    S6DeepLinkIdentity,
    S6KeyboardContract,
    S6PerformanceCorpusIdentity,
    S6PerformanceProfile,
    S6ReturnContext,
    S6RuntimeImplementationError,
    S6SemanticZoomState,
    S6_CORPUS_CONTENT_HASH,
    S6_PERFORMANCE_REGISTRY_CONTENT_HASH,
    S6_AUDIENCE_ENCODING_CONTENT_HASH,
    build_audience_encoding_registry,
    build_audience_encoding_registry_mapping,
    build_density_semantic_zoom_contract,
    build_performance_corpus_identity,
    build_performance_profile,
    build_performance_registry,
    build_protected_boundary,
    s6_as_mapping,
    s6_canonical_state_hash,
    s6_corpus_identity_hash,
    s6_audience_encoding_hash,
)
from mm_r5.s6_accessibility import build_keyboard_contract
from mm_r5.s6_navigation import (
    S6DensityZoomProjection,
    S6NavigationError,
    canonical_state_error,
    deep_link_identity_error,
    projectable_member_refs,
)


@dataclasses.dataclass(frozen=True)
class S6ValidationIssue:
    code: str
    path: str
    message_zh: str = ""

    def __post_init__(self) -> None:
        if type(self.code) is not str or type(self.path) is not str:
            raise TypeError("S6ValidationIssue code/path must be str")
        if not self.message_zh:
            object.__setattr__(self, "message_zh", f"核对未通过：{self.path}（{self.code}）")


@dataclasses.dataclass(frozen=True)
class S6ValidationResult:
    ok: bool
    primary_code: str | None
    issues: tuple[S6ValidationIssue, ...]
    expected: Any = None
    projection_state: str = "not_emitted"

    @property
    def code(self) -> str | None:
        return self.primary_code

    @property
    def projection(self) -> str:
        return self.projection_state

    @property
    def expected_packet(self) -> Any:
        return self.expected

    @property
    def packet_emitted(self) -> bool:
        return self.ok and self.projection_state not in {"not_emitted", "not_restored"}

    def __bool__(self) -> bool:
        return self.ok


def _issue(code: str, path: str) -> S6ValidationIssue:
    return S6ValidationIssue(code=code, path=path)


def _result(code: str | None, path: str = "", expected: Any = None,
            projection_state: str = "not_emitted") -> S6ValidationResult:
    if code is None:
        return S6ValidationResult(True, None, (), expected, projection_state)
    return S6ValidationResult(False, code, (_issue(code, path),), expected, projection_state)


_UNION_ORIGINS = (Union,) + ((types.UnionType,) if hasattr(types, "UnionType") else ())


def _type_spec(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Literal:
        return ("literal", get_args(annotation))
    if origin in _UNION_ORIGINS:
        args = get_args(annotation)
        non_none = tuple(item for item in args if item is not type(None))
        if len(non_none) != 1 or len(args) != 2:
            raise S6RuntimeImplementationError(f"unsupported S6 union annotation {annotation!r}")
        return ("optional", _type_spec(non_none[0]))
    if origin is tuple:
        args = get_args(annotation)
        if len(args) != 2 or args[1] is not Ellipsis:
            raise S6RuntimeImplementationError(f"unsupported S6 tuple annotation {annotation!r}")
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
    raise S6RuntimeImplementationError(f"unsupported S6 annotation {annotation!r}")


_SPEC_CACHE: dict[type, dict[str, Any]] = {}


def _class_spec(cls: type) -> dict[str, Any]:
    if cls not in _SPEC_CACHE:
        hints = get_type_hints(cls)
        _SPEC_CACHE[cls] = {item.name: _type_spec(hints[item.name]) for item in dataclasses.fields(cls)}
    return _SPEC_CACHE[cls]


def _structural_error(spec: Any, value: Any, path: str) -> S6ValidationIssue | None:
    kind = spec[0]
    if kind == "optional":
        return None if value is None else _structural_error(spec[1], value, path)
    if kind == "literal":
        return None if value in spec[1] else _issue("SCHEMA_KEY_MISMATCH", path)
    if kind == "scalar":
        return None if type(value) is spec[1] else _issue("SCHEMA_KEY_MISMATCH", path)
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
        for field_name, child in expected.items():
            issue = _structural_error(child, value[field_name], f"{path}/{field_name}")
            if issue is not None:
                return issue
        return None
    raise S6RuntimeImplementationError(f"unknown structural spec {spec!r}")


def _candidate_mapping(candidate: Any, expected_type: type) -> dict[str, Any]:
    if type(candidate) is expected_type:
        mapped = s6_as_mapping(candidate)
        if not isinstance(mapped, dict):
            raise S6RuntimeImplementationError("typed S6 candidate did not serialize as object")
        return mapped
    if isinstance(candidate, Mapping):
        return dict(candidate)
    raise S6RuntimeImplementationError(
        f"candidate must be Mapping or {expected_type.__name__}, got {type(candidate).__name__}"
    )


def _first_difference(expected: Any, candidate: Any, path: str = "") -> tuple[str, Any, Any] | None:
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


def _lookup(root: Any, path: str) -> Any:
    value = root
    for part in path.strip("/").split("/"):
        if not part:
            continue
        try:
            value = value[int(part)] if isinstance(value, list) else value[part]
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    return value


def _full_registry_candidate(candidate: Any) -> dict[str, Any]:
    mapped = dict(candidate) if isinstance(candidate, Mapping) else s6_as_mapping(candidate)
    if isinstance(mapped, dict) and set(mapped) == {"performance"} and isinstance(mapped["performance"], dict):
        return mapped["performance"]
    return mapped


def _deep_link_difference_code(path: str, actual: Any) -> str:
    if path.endswith("/fallback_policy"):
        return "NEAREST_FALLBACK_FORBIDDEN"
    if path.endswith("/project_ref") and isinstance(actual, str) and "unprojectable" in actual:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    if path.endswith("/subject_ref") and isinstance(actual, str) and "adjacent" in actual:
        return "NEAREST_FALLBACK_FORBIDDEN"
    if path.endswith("/risk_anchor_ref") and isinstance(actual, str) and actual.endswith("other"):
        return "DEEP_LINK_ANCHOR_NOT_MEMBER"
    if path.endswith("/event_ref") and actual is None:
        return "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    if path.endswith("/target_projection_content_hash") and actual == "f" * 64:
        return "DEEP_LINK_ARTIFACT_MISSING"
    return "DEEP_LINK_IDENTITY_MISMATCH"


def validate_deep_link_identity(
    candidate: S6DeepLinkIdentity | Mapping[str, Any],
    subject_packet: S5SubjectTemporalPacket,
    expected: S6DeepLinkIdentity | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    mapped = _candidate_mapping(candidate, S6DeepLinkIdentity)
    if set(mapped) == {"deep_link_identity"} and isinstance(mapped.get("deep_link_identity"), dict):
        mapped = mapped["deep_link_identity"]
    issue = _structural_error(("object", S6DeepLinkIdentity), mapped, "")
    if issue is not None and issue.path.endswith("/fallback_policy") and type(_lookup(mapped, issue.path)) is str:
        issue = None
    if issue is not None:
        return S6ValidationResult(False, issue.code, (issue,), expected, "not_emitted")
    expected_mapping = None if expected is None else _candidate_mapping(expected, S6DeepLinkIdentity)
    if expected_mapping is not None:
        difference = _first_difference(expected_mapping, mapped)
        if difference is not None:
            path, _before, actual = difference
            code = _deep_link_difference_code(path, actual)
            return _result(code, path, expected, "not_emitted")
    code = deep_link_identity_error(mapped, subject_packet)
    if code is not None:
        return _result(code, "/deep_link_identity", expected, "not_emitted")
    return _result(None, expected=expected, projection_state="emitted")


def validate_canonical_return_state(
    candidate: S6CanonicalReturnState | Mapping[str, Any],
    subject_packet: S5SubjectTemporalPacket,
    expected: S6CanonicalReturnState | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    mapped = _candidate_mapping(candidate, S6CanonicalReturnState)
    issue = _structural_error(("object", S6CanonicalReturnState), mapped, "")
    if issue is not None:
        return S6ValidationResult(False, issue.code, (issue,), expected, "not_emitted")
    semantic = canonical_state_error(mapped, subject_packet)
    if semantic is not None:
        return _result(semantic, "/canonical", expected)
    if mapped.get("canonical_state_hash") != s6_canonical_state_hash(mapped):
        return _result("CANONICAL_STATE_HASH_MISMATCH", "/canonical_state_hash", expected)
    if expected is not None:
        difference = _first_difference(_candidate_mapping(expected, S6CanonicalReturnState), mapped)
        if difference is not None:
            return _result("CANONICAL_STATE_HASH_MISMATCH", difference[0], expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_return_context(
    candidate: S6ReturnContext | Mapping[str, Any],
    subject_packet: S5SubjectTemporalPacket,
    expected: S6ReturnContext | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    mapped = _candidate_mapping(candidate, S6ReturnContext)
    if set(mapped) == {"return_context"} and isinstance(mapped.get("return_context"), dict):
        mapped = mapped["return_context"]
    issue = _structural_error(("object", S6ReturnContext), mapped, "")
    if issue is not None and issue.path.startswith("/canonical/"):
        # The frozen challenge registry deliberately uses compact partial
        # replacements for canonical child objects.  They are a canonical
        # hash failure, not a permission to accept a re-shaped object.
        return _result("CANONICAL_STATE_HASH_MISMATCH", issue.path, expected, "not_restored")
    if issue is not None:
        return S6ValidationResult(False, issue.code, (issue,), expected, "not_restored")
    expected_mapping = None if expected is None else _candidate_mapping(expected, S6ReturnContext)
    if expected_mapping is not None and mapped.get("return_context_key") != expected_mapping.get("return_context_key"):
        return _result("RETURN_CONTEXT_KEY_MISMATCH", "/return_context_key", expected, "not_restored")
    canonical = mapped["canonical"]
    semantic = canonical_state_error(canonical, subject_packet)
    if semantic is not None:
        return _result(semantic, "/canonical", expected, "not_restored")
    if canonical.get("canonical_state_hash") != s6_canonical_state_hash(canonical):
        return _result("CANONICAL_STATE_HASH_MISMATCH", "/canonical/canonical_state_hash", expected, "not_restored")
    if expected_mapping is not None:
        expected_canonical = expected_mapping["canonical"]
        if canonical != expected_canonical:
            difference = _first_difference(expected_canonical, canonical, "/canonical")
            return _result("CANONICAL_STATE_HASH_MISMATCH", difference[0] if difference else "/canonical", expected, "not_restored")
        difference = _first_difference(expected_mapping.get("ephemeral"), mapped.get("ephemeral"), "/ephemeral")
        if difference is not None:
            return _result("EPHEMERAL_STATE_IN_CANONICAL_HASH", difference[0], expected, "not_restored")
    if mapped.get("return_context_key") != canonical["deep_link_identity"]["return_context_key"]:
        return _result("RETURN_CONTEXT_KEY_MISMATCH", "/return_context_key", expected, "not_restored")
    return _result(None, expected=expected, projection_state="restored")


def validate_semantic_zoom_state(
    candidate: S6SemanticZoomState | Mapping[str, Any],
) -> S6ValidationResult:
    mapped = _candidate_mapping(candidate, S6SemanticZoomState)
    issue = _structural_error(("object", S6SemanticZoomState), mapped, "")
    if issue is not None:
        return _result("SEMANTIC_ZOOM_POLICY_MISMATCH" if issue.path != "/" else issue.code, issue.path)
    level = mapped["semantic_zoom_level"]
    density = mapped["density_mode"]
    if level not in ("overview", "detail", "evidence") or density not in ("standard", "high"):
        return _result("SEMANTIC_ZOOM_POLICY_MISMATCH", "/semantic_zoom_state")
    from mm_r5.s6_navigation import build_semantic_zoom_state

    expected = build_semantic_zoom_state(level, density)
    if mapped != s6_as_mapping(expected):
        return _result("SEMANTIC_ZOOM_POLICY_MISMATCH", "/semantic_zoom_state", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_density_semantic_zoom_contract(candidate: Mapping[str, Any]) -> S6ValidationResult:
    """Validate the frozen density/zoom policy table used by the runtime."""
    expected = build_density_semantic_zoom_contract()
    mapped = dict(candidate) if isinstance(candidate, Mapping) else {}
    if set(mapped) == {"density_semantic_zoom"} and isinstance(mapped.get("density_semantic_zoom"), dict):
        mapped = mapped["density_semantic_zoom"]
    difference = _first_difference(expected, mapped)
    if difference is None:
        return _result(None, expected=expected, projection_state="emitted")
    path, _before, actual = difference
    if "/density_modes/" in path:
        return _result("DENSITY_REQUIRED_RISK_HIDDEN", path, expected)
    return _result("SEMANTIC_ZOOM_POLICY_MISMATCH", path, expected)


def validate_keyboard_contract(
    candidate: S6KeyboardContract | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    expected = build_keyboard_contract()
    value = expected if candidate is None else candidate
    mapped = _candidate_mapping(value, S6KeyboardContract)
    issue = _structural_error(("object", S6KeyboardContract), mapped, "")
    if issue is not None:
        return _result(issue.code, issue.path, expected)
    for index, binding in enumerate(mapped["bindings"]):
        if binding["medical_state_mutation"] is True:
            return _result("KEYBOARD_MEDICAL_STATE_MUTATION", f"/bindings/{index}/medical_state_mutation", expected)
    if mapped != s6_as_mapping(expected):
        return _result("S6_KEYBOARD_MISMATCH", "/keyboard_contract", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_audience_encoding_registry(
    candidate: S6AudienceEncodingRegistry | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    expected = build_audience_encoding_registry()
    value = expected if candidate is None else candidate
    mapped = _candidate_mapping(value, S6AudienceEncodingRegistry)
    if set(mapped) == {"audience_encoding"} and isinstance(mapped.get("audience_encoding"), dict):
        mapped = mapped["audience_encoding"]
    full_expected = build_audience_encoding_registry_mapping()
    if set(mapped) == set(full_expected):
        if mapped != full_expected:
            return _result("NON_COLOUR_ENCODING_INCOMPLETE", "/audience_encoding", full_expected)
        if s6_audience_encoding_hash(mapped) != S6_AUDIENCE_ENCODING_CONTENT_HASH:
            return _result("NON_COLOUR_ENCODING_INCOMPLETE", "/content_hash", full_expected)
        return _result(None, expected=full_expected, projection_state="emitted")
    issue = _structural_error(("object", S6AudienceEncodingRegistry), mapped, "")
    if issue is not None:
        actual = _lookup(mapped, issue.path)
        if issue.path.endswith("/event_shape") and actual in EVENT_FORBIDDEN_SHAPES:
            issue = None
        else:
            return _result(issue.code, issue.path, expected)
    if mapped != s6_as_mapping(expected):
        return _result("NON_COLOUR_ENCODING_INCOMPLETE", "/audience_encoding", expected)
    if s6_audience_encoding_hash(mapped) != S6_AUDIENCE_ENCODING_CONTENT_HASH:
        return _result("NON_COLOUR_ENCODING_INCOMPLETE", "/content_hash", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_density_zoom_projection(
    candidate: S6DensityZoomProjection,
    subject_packet: S5SubjectTemporalPacket,
) -> S6ValidationResult:
    if type(candidate) is not S6DensityZoomProjection:
        raise S6RuntimeImplementationError("density validation requires typed projection")
    packet = subject_packet
    expected_refs = tuple(item.event_ref for item in packet.projection.events)
    expected_risks = tuple(item.risk_anchor_ref for item in packet.projection.risk_anchors)
    zoom_result = validate_semantic_zoom_state(candidate.semantic_zoom_state)
    if not zoom_result.ok:
        return zoom_result
    if candidate.visible_event_refs != expected_refs or candidate.visible_risk_anchor_refs != expected_risks:
        return _result("DENSITY_REQUIRED_RISK_HIDDEN", "/visible_risk_anchor_refs")
    if candidate.semantic_zoom_state.semantic_zoom_level in ("detail", "evidence") and candidate.aggregated_event_refs:
        return _result("SEMANTIC_ZOOM_POLICY_MISMATCH", "/aggregated_event_refs")
    if candidate.spacing_units != (1 if candidate.semantic_zoom_state.density_mode == "high" else 2):
        return _result("DENSITY_REQUIRED_RISK_HIDDEN", "/spacing_units")
    return _result(None, projection_state="emitted")


def validate_performance_corpus_identity(
    candidate: S6PerformanceCorpusIdentity | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    expected = build_performance_corpus_identity()
    value = expected if candidate is None else candidate
    mapped = _candidate_mapping(value, S6PerformanceCorpusIdentity)
    issue = _structural_error(("object", S6PerformanceCorpusIdentity), mapped, "")
    if issue is not None:
        return _result(issue.code, issue.path, expected)
    if mapped.get("content_hash") != s6_corpus_identity_hash(mapped):
        return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/content_hash", expected)
    if mapped != s6_as_mapping(expected) or mapped.get("content_hash") != S6_CORPUS_CONTENT_HASH:
        return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/corpus", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_performance_corpus_records(candidate: Sequence[Any]) -> S6ValidationResult:
    """Check the synthetic 1000/40/300 records without treating names as authority."""
    expected = build_performance_corpus_identity()
    if isinstance(candidate, (str, bytes)) or not isinstance(candidate, Sequence):
        return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/corpus", expected)
    rows = []
    for row in candidate:
        mapped = s6_as_mapping(row)
        if not isinstance(mapped, dict) or set(mapped) != {"record_kind", "ordinal", "domain", "source_locator_ref"}:
            return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/corpus", expected)
        rows.append(mapped)
    counts = {"event": 1000, "indicator": 40, "risk_anchor": 300}
    if len(rows) != sum(counts.values()):
        return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/corpus", expected)
    cursor = 0
    for kind, count in (("event", 1000), ("indicator", 40), ("risk_anchor", 300)):
        chunk = rows[cursor:cursor + count]
        cursor += count
        if [row.get("record_kind") for row in chunk] != [kind] * count:
            return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/record_order", expected)
        if [row.get("ordinal") for row in chunk] != list(range(count)):
            return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", f"/{kind}/ordinal", expected)
        if any(row.get("domain") not in DOMAINS or type(row.get("source_locator_ref")) is not str
               or not row.get("source_locator_ref") for row in chunk):
            return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", f"/{kind}", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_performance_corpus(candidate: Any = None) -> S6ValidationResult:
    """Validate either the frozen identity or the synthetic record sequence."""
    if candidate is None or type(candidate) is S6PerformanceCorpusIdentity or isinstance(candidate, Mapping):
        return validate_performance_corpus_identity(candidate)
    return validate_performance_corpus_records(candidate)


def validate_performance_profile(
    candidate: S6PerformanceProfile | Mapping[str, Any] | None = None,
) -> S6ValidationResult:
    expected_profile = build_performance_profile()
    if candidate is None:
        return _result(None, expected=expected_profile, projection_state="emitted")
    mapped = _full_registry_candidate(candidate)
    if set(mapped) == set(build_performance_registry()):
        expected = build_performance_registry()
        if mapped.get("result_state") != "unmeasured_contract_only":
            if mapped.get("result_state") in {"measured_pass", "measured_fail"}:
                return _result("PERFORMANCE_RESULT_PREMATURE", "/result_state", expected)
        if mapped.get("offline_boundary", {}).get("starts_8911") is not False:
            return _result("PROTECTED_BOUNDARY_DRIFT", "/offline_boundary/starts_8911", expected)
        if mapped != expected:
            return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/performance", expected)
        return _result(None, expected=expected, projection_state="emitted")
    mapped = _candidate_mapping(candidate, S6PerformanceProfile)
    issue = _structural_error(("object", S6PerformanceProfile), mapped, "")
    if issue is not None:
        return _result(issue.code, issue.path, expected_profile)
    if mapped.get("result_state") in {"measured_pass", "measured_fail"}:
        return _result("PERFORMANCE_RESULT_PREMATURE", "/result_state", expected_profile)
    if mapped != s6_as_mapping(expected_profile):
        return _result("PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "/performance", expected_profile)
    return _result(None, expected=expected_profile, projection_state="emitted")


def validate_protected_boundary(candidate: Mapping[str, Any]) -> S6ValidationResult:
    expected = build_protected_boundary()
    mapped = dict(candidate) if isinstance(candidate, Mapping) else {}
    if set(mapped) == {"protected_boundaries"} and isinstance(mapped.get("protected_boundaries"), dict):
        mapped = {"protected_boundaries": mapped["protected_boundaries"], "manifest": {"acceptance_token_emitted": False}}
    if mapped != expected:
        return _result("PROTECTED_BOUNDARY_DRIFT", "/protected_boundaries", expected)
    return _result(None, expected=expected, projection_state="emitted")


def validate_s6(candidate: Any, subject_packet: S5SubjectTemporalPacket | None = None) -> S6ValidationResult:
    """Small dispatch helper for callers that already know the candidate kind."""
    if isinstance(candidate, (S6DeepLinkIdentity,)) and subject_packet is not None:
        return validate_deep_link_identity(candidate, subject_packet)
    if isinstance(candidate, (S6ReturnContext,)) and subject_packet is not None:
        return validate_return_context(candidate, subject_packet)
    if isinstance(candidate, S6KeyboardContract):
        return validate_keyboard_contract(candidate)
    if isinstance(candidate, S6AudienceEncodingRegistry):
        return validate_audience_encoding_registry(candidate)
    if isinstance(candidate, S6PerformanceProfile):
        return validate_performance_profile(candidate)
    raise S6RuntimeImplementationError("S6 candidate type requires a focused validator")


# Short aliases mirror the S5 validator vocabulary.
validate_deep_link = validate_deep_link_identity
validate_return = validate_return_context
validate_canonical = validate_canonical_return_state
validate_semantic_zoom = validate_semantic_zoom_state
validate_keyboard = validate_keyboard_contract
validate_non_colour_encoding = validate_audience_encoding_registry
validate_audience = validate_audience_encoding_registry
validate_density_zoom = validate_density_zoom_projection
validate_performance = validate_performance_profile
validate_corpus = validate_performance_corpus
validate_performance_records = validate_performance_corpus_records
validate_protected_boundaries = validate_protected_boundary
validate_density_semantic_zoom = validate_density_semantic_zoom_contract


__all__ = [
    "S6ValidationIssue", "S6ValidationResult", "validate_deep_link_identity", "validate_deep_link",
    "validate_canonical_return_state", "validate_canonical", "validate_return_context", "validate_return",
    "validate_semantic_zoom_state", "validate_semantic_zoom", "validate_keyboard_contract", "validate_keyboard",
    "validate_density_semantic_zoom_contract", "validate_density_semantic_zoom",
    "validate_audience_encoding_registry", "validate_non_colour_encoding", "validate_audience",
    "validate_density_zoom_projection", "validate_density_zoom", "validate_performance_corpus_identity",
    "validate_performance_corpus_records", "validate_performance_records", "validate_performance_corpus",
    "validate_performance_profile",
    "validate_performance", "validate_corpus", "validate_protected_boundary",
    "validate_protected_boundaries", "validate_s6",
]
