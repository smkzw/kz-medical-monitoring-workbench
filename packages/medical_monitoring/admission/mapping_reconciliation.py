"""Deterministic dual-cohort reconciliation contract for C3 listing mapping.

The primary cohort (independent main analysis) and the verifier cohort
(independent blind re-check) are compared field by field. The contract is
pure and deterministic: identical inputs always produce an identical report,
no model is trusted, and nothing is dropped silently.

Contract rules:

1. Full field coverage — every ``(domain, source_field)`` of the admitted
   profile must appear exactly once in each cohort. Missing, unexpected or
   duplicated fields block the reconciliation.
2. Evidence reference closure — every ``evidence_ids`` entry referenced by a
   mapping verdict must resolve to evidence that actually exists in the same
   cohort. A non-``unmapped`` verdict must also carry at least one closing
   evidence reference on both sides before it may auto-pass.
3. Agreement auto-passes — when both cohorts state the same
   ``recommended_role`` and ``field_kind`` with closed evidence, the field is
   adoptable without human work.
4. Divergences are preserved — any disagreement is kept verbatim (both
   verdicts with their evidence references) and returns to the harness for
   focused evidence review. The reconciliation never picks a winner or sends
   bulk technical work to the user.
5. Mapping-stage output stays inside the mapping boundary — CTCAE grade
   conclusions, risk conclusions and Query conclusions are violations. Field
   mapping describes columns; it never grades an event, rates a risk or
   opens a Query.

Nothing here materializes canonical facts or mutates a draft.
"""

from __future__ import annotations

import re
from typing import Any, Collection, Iterable, Mapping, Sequence

from .mapping_gate import MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY


RECONCILIATION_SCHEMA_VERSION = "mm-c3-mapping-reconciliation-v2"

COHORT_PRIMARY = "primary"
COHORT_VERIFIER = "verifier"

RESULT_AGREED = "agreed"
RESULT_DIVERGED = "diverged"
RESULT_BLOCKED = "blocked"

STATE_AGREED = "agreed"
STATE_DIVERGED = "diverged"
STATE_BLOCKED = "blocked"

UNMAPPED_FIELD_KIND = "unmapped"


class MappingReconciliationError(RuntimeError):
    """Stable product error code for reconciliation misuse."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


# Structured keys that would carry a mapping-stage clinical conclusion. A
# field-mapping verdict describes a column; it has no business carrying a
# grade, a risk rating or a Query handle.
FORBIDDEN_CONCLUSION_ITEM_KEYS = frozenset({
    "ctcae",
    "ctcae_grade",
    "grade",
    "grade_conclusion",
    "toxicity_grade",
    "risk_level",
    "risk_grade",
    "risk_score",
    "risk_conclusion",
    "query_id",
    "query_status",
    "query_conclusion",
    "proposed_query",
    "requires_query",
    "need_query",
})

_CONCLUSION_TEXT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    # "CTCAE 3级", "CTCAE分级为4级", "CTCAE grade 3" — an asserted grade value.
    (
        "ctcae_grade_conclusion",
        re.compile(
            r"CTCAE[^。；;.\n]{0,16}?(?:[1-5]\s*级|grade\s*[1-5])",
            re.IGNORECASE,
        ),
    ),
    # "评定为3级", "判定为Grade 4", "分级为 5 级" without naming CTCAE.
    (
        "ctcae_grade_conclusion",
        re.compile(
            r"(?:评定|判定|评估|结论为|分级为|定为)\s*(?:为)?\s*"
            r"(?:CTCAE|毒性)?\s*[1-5]\s*级|"
            r"(?:评定|判定|评估|结论为|分级为|定为)\s*(?:为)?\s*grade\s*[1-5]",
            re.IGNORECASE,
        ),
    ),
    (
        "risk_conclusion",
        re.compile(
            r"风险(?:等级|级别|判定|评级)\s*[:：为]?\s*"
            r"(?:极高|高|中|低|无|high|medium|low|none)",
            re.IGNORECASE,
        ),
    ),
    (
        "risk_conclusion",
        re.compile(
            r"(?:属|为|判定为|评为)(?:极高|高|中|低)风险|"
            r"risk\s*(?:level|grade)\s*[:：=]?\s*(?:high|medium|low)",
            re.IGNORECASE,
        ),
    ),
    (
        "query_conclusion",
        re.compile(
            r"(?:发起|开立|创建|提出|开具)\s*(?:医学)?\s*(?:Query|疑问)",
            re.IGNORECASE,
        ),
    ),
    (
        "query_conclusion",
        re.compile(
            r"Query\s*(?:状态|status)\s*[:：=]?\s*\S+",
            re.IGNORECASE,
        ),
    ),
)

_VERDICT_TEXT_FIELDS = ("recommended_role", "uncertainty", "user_action")


def normalize_field_kind(value: Any) -> str:
    return str(value or "").strip().casefold()


def field_identity(item: Mapping[str, Any]) -> tuple[str, str]:
    """Return the stripped ``(domain, source_field)`` identity of a verdict."""

    return (
        str(item.get("domain") or "").strip(),
        str(item.get("source_field") or "").strip(),
    )


def mapping_conclusion_violations(
    item: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Return deterministic mapping-boundary violations for one verdict.

    The scan covers structured conclusion keys and assertive conclusion
    phrasing in the three free-text verdict fields. Describing a column
    ("该字段为CTCAE分级字段") stays legal; asserting a grade, a risk rating
    or a Query action for data is not.
    """

    violations: list[dict[str, str]] = []
    for key in sorted(FORBIDDEN_CONCLUSION_ITEM_KEYS):
        if key in item:
            violations.append({
                "code": "forbidden_conclusion_field",
                "detail": f"{key}",
            })
    for field_name in _VERDICT_TEXT_FIELDS:
        text = str(item.get(field_name) or "")
        if not text:
            continue
        for code, pattern in _CONCLUSION_TEXT_RULES:
            if pattern.search(text):
                violations.append({
                    "code": code,
                    "detail": field_name,
                })
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in violations:
        marker = (row["code"], row["detail"])
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(row)
    return deduped


def cohort_payload_from_candidates(
    candidates: Iterable[Any],
) -> dict[str, Any]:
    """Extract one cohort's verdicts and evidence ids from its candidates."""

    mappings: list[dict[str, Any]] = []
    evidence_ids: set[str] = set()
    for candidate in candidates:
        candidate_id = str(getattr(candidate, "candidate_id", "") or "")
        for evidence in getattr(candidate, "evidence", ()) or ():
            evidence_id = str(getattr(evidence, "evidence_id", "") or "")
            if evidence_id:
                evidence_ids.add(evidence_id)
        payload = getattr(candidate, "structured_payload", None) or {}
        raw_mappings = (
            payload.get("field_mappings")
            if isinstance(payload, Mapping)
            else None
        )
        for item in raw_mappings or ():
            if isinstance(item, Mapping):
                mappings.append({**dict(item), "candidate_id": candidate_id})
    return {"mappings": mappings, "evidence_ids": frozenset(evidence_ids)}


def _profile_identities(
    profile_fields: Sequence[Mapping[str, Any]],
) -> list[tuple[str, str]]:
    if not profile_fields:
        raise MappingReconciliationError("reconciliation_profile_invalid")
    identities: list[tuple[str, str]] = []
    for row in profile_fields:
        domain = str(row.get("domain") or "").strip()
        field = str(row.get("field") or row.get("source_field") or "").strip()
        if not domain or not field:
            raise MappingReconciliationError("reconciliation_profile_invalid")
        identities.append((domain, field))
    if len(identities) != len(set(identities)):
        raise MappingReconciliationError("reconciliation_profile_invalid")
    return identities


def _verdict_projection(item: Mapping[str, Any]) -> dict[str, Any]:
    projection: dict[str, Any] = {
        "domain": str(item.get("domain") or "").strip(),
        "source_field": str(item.get("source_field") or "").strip(),
        "recommended_role": str(item.get("recommended_role") or ""),
        "field_kind": str(item.get("field_kind") or ""),
        "confidence": item.get("confidence"),
        "evidence_ids": [
            str(evidence_id)
            for evidence_id in (item.get("evidence_ids") or ())
        ],
    }
    for optional in ("candidate_id", "job_id"):
        value = str(item.get(optional) or "").strip()
        if value:
            projection[optional] = value
    semantic_verdict = {
        key: item.get(key)
        for key in (
            "recommended_role",
            "field_kind",
            "related_fields",
            "dependency_fields",
            "standards_reference",
            "derivation_lineage",
            "value_constraints",
            "object_identity",
            "object_identity_evidence_fields",
            "object_identity_binding_id",
            "validated_treatment_identity_binding",
            "dose_semantics",
            "quality_gate_actions",
        )
        if key in item
    }
    if "recommended_role" in semantic_verdict:
        semantic_verdict["recommended_role"] = str(
            semantic_verdict["recommended_role"] or ""
        ).strip().casefold()
    if "field_kind" in semantic_verdict:
        semantic_verdict["field_kind"] = normalize_field_kind(
            semantic_verdict["field_kind"]
        )
    for unordered in (
        "related_fields",
        "object_identity_evidence_fields",
        "quality_gate_actions",
    ):
        if unordered in semantic_verdict:
            semantic_verdict[unordered] = sorted(
                str(value) for value in (semantic_verdict[unordered] or ())
            )
    projection["semantic_verdict"] = semantic_verdict
    return projection


def semantic_difference_paths(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[str]:
    """Locate disagreements without interpreting, accepting or dropping either side."""
    paths: list[str] = []
    def visit(a: Any, b: Any, path: str) -> None:
        if isinstance(a, Mapping) and isinstance(b, Mapping):
            for key in sorted(set(a) | set(b)):
                child = f"{path}.{key}" if path else str(key)
                if key not in a or key not in b:
                    paths.append(child)
                else:
                    visit(a[key], b[key], child)
        elif type(a) is not type(b) or a != b:
            paths.append(path)
    visit(left, right, "")
    return paths


def _index_cohort(
    *,
    cohort: str,
    mappings: Sequence[Mapping[str, Any]],
    profile_set: set[tuple[str, str]],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[str, str], list[dict[str, str]]],
    list[dict[str, Any]],
]:
    by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    conclusion_violations: dict[tuple[str, str], list[dict[str, str]]] = {}
    violations: list[dict[str, Any]] = []
    for index, raw in enumerate(mappings):
        if not isinstance(raw, Mapping):
            violations.append({
                "cohort": cohort,
                "index": index,
                "code": "malformed_mapping_item",
                "domain": "",
                "source_field": "",
            })
            continue
        item = dict(raw)
        identity = field_identity(item)
        if not identity[0] or not identity[1]:
            violations.append({
                "cohort": cohort,
                "index": index,
                "code": "malformed_mapping_item",
                "domain": identity[0],
                "source_field": identity[1],
            })
            continue
        if identity in by_identity:
            violations.append({
                "cohort": cohort,
                "index": index,
                "code": f"duplicate_in_{cohort}",
                "domain": identity[0],
                "source_field": identity[1],
            })
        elif identity not in profile_set:
            violations.append({
                "cohort": cohort,
                "index": index,
                "code": f"unexpected_in_{cohort}",
                "domain": identity[0],
                "source_field": identity[1],
            })
            continue
        else:
            by_identity[identity] = _verdict_projection(item)
        # The mapping-stage conclusion boundary is evaluated on the raw
        # verdict, including text and keys a projection would drop.
        item_conclusions = mapping_conclusion_violations(item)
        if item_conclusions:
            conclusion_violations.setdefault(identity, []).extend(
                item_conclusions
            )
    return by_identity, conclusion_violations, violations


def _evidence_closure(
    *,
    cohort: str,
    projection: Mapping[str, Any],
    available: Collection[str],
) -> tuple[bool, list[str], list[dict[str, str]]]:
    referenced = [
        str(evidence_id)
        for evidence_id in (projection.get("evidence_ids") or ())
    ]
    unknown = sorted({item for item in referenced if item not in available})
    violations: list[dict[str, str]] = [
        {"code": "evidence_reference_unclosed", "detail": evidence_id}
        for evidence_id in unknown
    ]
    required = normalize_field_kind(projection.get("field_kind")) != (
        UNMAPPED_FIELD_KIND
    )
    if required and not referenced:
        violations.append({
            "code": "evidence_reference_missing",
            "detail": cohort,
        })
    closed = not violations
    return closed, unknown, violations


def reconcile_mapping_cohorts(
    *,
    profile_fields: Sequence[Mapping[str, Any]],
    primary_mappings: Sequence[Mapping[str, Any]] = (),
    verifier_mappings: Sequence[Mapping[str, Any]] = (),
    primary_evidence_ids: Collection[str] = (),
    verifier_evidence_ids: Collection[str] = (),
    primary_execution_route: str = MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
    comparison_policy_version: str = RECONCILIATION_SCHEMA_VERSION,
) -> Mapping[str, Any]:
    """Reconcile the primary and verifier cohorts field by field.

    The report is deterministic and total: every profile field appears in
    ``fields`` exactly once with its preserved verdicts, and nothing is
    dropped or auto-resolved. ``auto_pass`` is true only when every field
    agreed with closed evidence on both cohorts, no contract violation
    exists, and the primary cohort actually executed on a remote primary
    route. A local-fallback first pass never yields ``dual_model_pass`` —
    agreement with a fallback run is a degraded signal, not an independent
    dual-model confirmation.
    """

    from .mapping_comparison import DEPENDENCY_COMPARISON_VERSION, compare_mapping_dependencies
    if comparison_policy_version not in {RECONCILIATION_SCHEMA_VERSION, DEPENDENCY_COMPARISON_VERSION}:
        raise MappingReconciliationError("unsupported_mapping_comparison_policy")
    executed_route = str(
        primary_execution_route or MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
    ).strip()

    identities = _profile_identities(profile_fields)
    profile_set = set(identities)
    primary_index, primary_conclusions, primary_violations = _index_cohort(
        cohort=COHORT_PRIMARY,
        mappings=primary_mappings,
        profile_set=profile_set,
    )
    verifier_index, verifier_conclusions, verifier_violations = _index_cohort(
        cohort=COHORT_VERIFIER,
        mappings=verifier_mappings,
        profile_set=profile_set,
    )
    primary_available = frozenset(primary_evidence_ids)
    verifier_available = frozenset(verifier_evidence_ids)

    fields: list[dict[str, Any]] = []
    divergences: list[dict[str, Any]] = []
    field_rows: list[dict[str, Any]] = []
    cohort_violations = primary_violations + verifier_violations
    coverage_violations: list[dict[str, Any]] = [
        {
            "cohort": COHORT_PRIMARY,
            "code": "missing_in_primary",
            "domain": domain,
            "source_field": field,
        }
        for domain, field in identities
        if (domain, field) not in primary_index
    ] + [
        {
            "cohort": COHORT_VERIFIER,
            "code": "missing_in_verifier",
            "domain": domain,
            "source_field": field,
        }
        for domain, field in identities
        if (domain, field) not in verifier_index
    ] + [
        {
            "cohort": item["cohort"],
            "code": item["code"],
            "domain": item["domain"],
            "source_field": item["source_field"],
        }
        for item in cohort_violations
    ]

    for domain, field in identities:
        primary = primary_index.get((domain, field))
        verifier = verifier_index.get((domain, field))
        row: dict[str, Any] = {
            "domain": domain,
            "source_field": field,
            "result": RESULT_BLOCKED,
            "human_decision_required": False,
            "system_review_required": False,
            "primary": primary,
            "verifier": verifier,
            "primary_evidence_closure": None,
            "verifier_evidence_closure": None,
            "violations": [],
        }
        field_violations: list[dict[str, Any]] = [
            dict(item)
            for item in cohort_violations
            if (item["domain"], item["source_field"]) == (domain, field)
        ]
        if primary is not None:
            closed, unknown, closure_violations = _evidence_closure(
                cohort=COHORT_PRIMARY,
                projection=primary,
                available=primary_available,
            )
            row["primary_evidence_closure"] = {
                "closed": closed,
                "unknown_evidence_ids": unknown,
            }
            field_violations.extend(
                {
                    "cohort": COHORT_PRIMARY,
                    "domain": domain,
                    "source_field": field,
                    **violation,
                }
                for violation in closure_violations
            )
            field_violations.extend(
                {
                    "cohort": COHORT_PRIMARY,
                    "domain": domain,
                    "source_field": field,
                    **violation,
                }
                for violation in primary_conclusions.get((domain, field), ())
            )
        if verifier is not None:
            closed, unknown, closure_violations = _evidence_closure(
                cohort=COHORT_VERIFIER,
                projection=verifier,
                available=verifier_available,
            )
            row["verifier_evidence_closure"] = {
                "closed": closed,
                "unknown_evidence_ids": unknown,
            }
            field_violations.extend(
                {
                    "cohort": COHORT_VERIFIER,
                    "domain": domain,
                    "source_field": field,
                    **violation,
                }
                for violation in closure_violations
            )
            field_violations.extend(
                {
                    "cohort": COHORT_VERIFIER,
                    "domain": domain,
                    "source_field": field,
                    **violation,
                }
                for violation in verifier_conclusions.get((domain, field), ())
            )
        if field_violations:
            row["result"] = RESULT_BLOCKED
            row["violations"] = field_violations
            # Missing coverage, malformed output and unclosed evidence are
            # system failures. They must be retried or repaired internally,
            # never converted into work for the medical monitor.
            row["human_decision_required"] = False
            row["system_review_required"] = True
        elif primary is not None and verifier is not None:
            agreed = primary["semantic_verdict"] == verifier["semantic_verdict"]
            if comparison_policy_version == DEPENDENCY_COMPARISON_VERSION:
                try:
                    comparison = compare_mapping_dependencies(primary["semantic_verdict"], verifier["semantic_verdict"])
                except ValueError as exc:
                    agreed = False
                    row["violations"].append({"cohort": "both", "domain": domain, "source_field": field,
                                              "code": "mapping_dependency_contract_invalid", "detail": str(exc)})
                else:
                    row["dependency_comparison"] = comparison
                    agreed = comparison["dependencies_agreed"]
            row["result"] = (RESULT_BLOCKED if row["violations"] else
                             RESULT_AGREED if agreed else RESULT_DIVERGED)
            # A model disagreement first returns to the harness for focused
            # evidence adjudication. Only the later medically substantive
            # residue may become a user question.
            row["system_review_required"] = not agreed
            row["human_decision_required"] = False
        if row["result"] != RESULT_AGREED:
            divergences.append({
                "domain": domain,
                "source_field": field,
                "result": row["result"],
                "primary": primary,
                "verifier": verifier,
                "violations": row["violations"],
            })
        fields.append(row)
        field_rows.append(row)

    hard_violations = len(coverage_violations) + sum(
        len(row["violations"]) for row in field_rows
    )
    if hard_violations:
        state = STATE_BLOCKED
    elif any(row["result"] == RESULT_DIVERGED for row in field_rows):
        state = STATE_DIVERGED
    else:
        state = STATE_AGREED
    return {
        "schema_version": comparison_policy_version,
        "state": state,
        # The dual-model pass is only honest when the primary cohort ran on
        # its remote route; a local fallback can never masquerade as one.
        "primary_execution_route": executed_route,
        "dual_model_pass": (
            state == STATE_AGREED
            and executed_route == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
        ),
        "auto_pass": (
            state == STATE_AGREED
            and executed_route == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
        ),
        "facts_generated": False,
        "candidate_fact_boundary": "reconciliation_only",
        "summary": {
            "field_count": len(field_rows),
            "agreed_count": sum(
                row["result"] == RESULT_AGREED for row in field_rows
            ),
            "diverged_count": sum(
                row["result"] == RESULT_DIVERGED for row in field_rows
            ),
            "blocked_count": sum(
                row["result"] == RESULT_BLOCKED for row in field_rows
            ),
            "coverage_violation_count": len(coverage_violations),
            "contract_violation_count": sum(
                len(row["violations"]) for row in field_rows
            ),
            "human_decision_count": sum(
                row["human_decision_required"] for row in field_rows
            ),
            "system_review_count": sum(
                row["system_review_required"] for row in field_rows
            ),
        },
        "coverage_violations": coverage_violations,
        "contract_violations": [
            {
                "cohort": violation["cohort"],
                "domain": violation["domain"],
                "source_field": violation["source_field"],
                "code": violation["code"],
                "detail": violation.get("detail", ""),
            }
            for row in field_rows
            for violation in row["violations"]
        ],
        "divergences": divergences,
        "fields": fields,
    }


__all__ = [
    "COHORT_PRIMARY",
    "COHORT_VERIFIER",
    "FORBIDDEN_CONCLUSION_ITEM_KEYS",
    "RECONCILIATION_SCHEMA_VERSION",
    "RESULT_AGREED",
    "RESULT_BLOCKED",
    "RESULT_DIVERGED",
    "STATE_AGREED",
    "STATE_BLOCKED",
    "STATE_DIVERGED",
    "MappingReconciliationError",
    "cohort_payload_from_candidates",
    "field_identity",
    "mapping_conclusion_violations",
    "normalize_field_kind",
    "reconcile_mapping_cohorts",
]
