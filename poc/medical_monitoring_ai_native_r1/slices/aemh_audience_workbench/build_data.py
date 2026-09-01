#!/usr/bin/env python3
"""Generate read-only ``window.MM_R1_DATA`` for the Slice 3 audience workbench.

This script imports accepted Slice 1 ``mm_r1`` code read-only, runs the synthetic
N → N+1 AE/MH vertical slice against a temporary Store, and writes a classic
``file://`` script that assigns ``window.MM_R1_DATA`` once.  It never mutates
accepted source, never promotes candidates to facts, and never embeds absolute
filesystem paths.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

SLICE_ROOT = Path(__file__).resolve().parent
POC_ROOT = SLICE_ROOT.parents[1]
SRC_ROOT = POC_ROOT / "src"
DEFAULT_JS_PATH = SLICE_ROOT / "data" / "mm_r1_data.js"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mm_r1 import ae_mh as ae_mh_mod  # noqa: E402
from mm_r1 import domain as domain_mod  # noqa: E402
from mm_r1.ae_mh import (  # noqa: E402
    AEMHResult,
    evidence_ref,
    run_ae_mh_vertical_slice,
)
from mm_r1.domain import (  # noqa: E402
    RiskLifecycleState,
    canonical_json,
    content_hash,
    to_jsonable,
)
from mm_r1.fixtures import (  # noqa: E402
    SYNTHETIC_MARKER,
    SYNTHETIC_PROJECT_ID,
    SYNTHETIC_RUN_N,
    SYNTHETIC_RUN_N1,
    SYNTHETIC_SNAPSHOT_N,
    SYNTHETIC_SNAPSHOT_N1,
    seed_synthetic_snapshots,
)
from mm_r1.projections import ProjectionBundle, build_projections  # noqa: E402
from mm_r1.store import Store  # noqa: E402

# Frozen clock for deterministic candidate/query/transition timestamps.
FIXED_NOW_ISO = "2026-01-31T12:00:00.000000+00:00"

DISCLAIMER_ZH = (
    "本页面仅展示隔离的合成演示数据，用于验证 AE/MH 漏报风险定位与证据下钻。"
    "AI 辅助定位证据与风险，医学经理终审。待核实风险线索不等于已记录 AE/MH；"
    "缺失不等于结案。"
)

_AUDIENCE_TERMS = {
    "unplanned admission": "非计划住院",
    "skin rash": "皮疹",
    "alt elevation": "ALT 升高",
    "hypertension": "高血压",
    "headache": "头痛",
    "fatigue": "疲乏",
    "nausea": "恶心",
    "dizziness": "头晕",
}

DELTA_GROUP_KEYS = (
    "current",
    "new",
    "escalated",
    "carry_forward",
    "resolved",
    "not_evaluable",
)

_ABS_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/var/folders/|[A-Za-z]:\\|/tmp/|/private/tmp/)"
)


def _freeze_clock() -> None:
    """Patch now_iso bindings used by discovery/lifecycle for determinism."""

    def _fixed() -> str:
        return FIXED_NOW_ISO

    domain_mod.now_iso = _fixed  # type: ignore[assignment]
    ae_mh_mod.now_iso = _fixed  # type: ignore[assignment]


def _polarity_for_row(table: str, row: Mapping[str, Any]) -> str:
    if table in ("ae", "mh"):
        return "formal_fact"
    if row.get("counterevidence_for"):
        return "counterevidence"
    if row.get("candidate_signal") or row.get("potential_unreported") or row.get(
        "possible_ae"
    ) or row.get("possible_mh"):
        return "supporting"
    return "context"


def _build_source_rows(
    listing: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    snapshot_id: str,
    snapshot_version: str,
    snapshot_label: str,
) -> Dict[str, Dict[str, Any]]:
    """Index every synthetic listing row by its stable locator."""
    index: Dict[str, Dict[str, Any]] = {}
    for table in sorted(listing):
        for row_index, row in enumerate(listing.get(table, ())):
            locator = evidence_ref(snapshot_version, table, row, row_index)
            record_id = str(row.get("record_id") or row.get("id") or f"{table}-{row_index + 1}")
            index[locator] = {
                "fixture_marker": SYNTHETIC_MARKER,
                "locator": locator,
                "snapshot_id": snapshot_id,
                "snapshot_version": snapshot_version,
                "snapshot_label": snapshot_label,
                "table": table,
                "row_index": row_index,
                "record_id": record_id,
                "subject_id": row.get("subject_id"),
                "site_id": row.get("site_id"),
                "actual_date": (
                    row.get("actual_date")
                    or row.get("onset")
                    or row.get("start_date")
                    or row.get("date")
                    or row.get("event_date")
                ),
                "polarity": _polarity_for_row(table, row),
                "is_formal_ae_mh_fact": table in ("ae", "mh"),
                "is_candidate_signal": bool(
                    row.get("candidate_signal")
                    or row.get("potential_unreported")
                    or row.get("possible_ae")
                    or row.get("possible_mh")
                ),
                "raw_values": dict(row),
            }
    return index


def _primary_transition_kind(
    instance_id: str,
    transitions: Sequence[Any],
) -> str:
    kinds = [t.kind for t in transitions if t.instance_id == instance_id]
    if not kinds:
        return "current"
    # Prefer the most specific terminal semantic when several exist.
    priority = (
        "not_evaluable",
        "identity_ambiguous",
        "resolve",
        "carry_forward_high_risk",
        "carry_forward",
        "escalate",
        "de_escalate",
        "reopen",
        "establish",
        "merge",
        "split",
        "supersede",
    )
    for kind in priority:
        if kind in kinds:
            return kind
    return kinds[-1]


def _delta_bucket(kind: str, lifecycle_state: RiskLifecycleState) -> str:
    if kind in ("not_evaluable", "identity_ambiguous") or (
        lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
    ):
        return "not_evaluable"
    if kind == "resolve" or lifecycle_state == RiskLifecycleState.RESOLVED_BY_DATA:
        return "resolved"
    if kind in ("carry_forward", "carry_forward_high_risk"):
        return "carry_forward"
    if kind == "escalate" or lifecycle_state == RiskLifecycleState.ESCALATED:
        return "escalated"
    if kind == "establish" or lifecycle_state == RiskLifecycleState.ESTABLISHED:
        # "new" is establish-only; other established-looking states stay current.
        return "new" if kind == "establish" else "current"
    return "current"


def _is_active_current(lifecycle_state: RiskLifecycleState) -> bool:
    return lifecycle_state not in (
        RiskLifecycleState.RESOLVED_BY_DATA,
        RiskLifecycleState.CLOSED,
        RiskLifecycleState.SUPERSEDED,
    )


def _build_delta_groups(
    result: AEMHResult,
    risk_cards: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    cards_by_identity = {card.get("identity_key"): card for card in risk_cards}
    groups: Dict[str, List[Dict[str, Any]]] = {key: [] for key in DELTA_GROUP_KEYS}
    for instance in result.lifecycle.instances:
        kind = _primary_transition_kind(instance.instance_id, result.lifecycle.transitions)
        bucket = _delta_bucket(kind, instance.lifecycle_state)
        card = cards_by_identity.get(instance.identity_key, {})
        entry = {
            "fixture_marker": SYNTHETIC_MARKER,
            "instance_id": instance.instance_id,
            "identity_key": instance.identity_key,
            "lifecycle_state": instance.lifecycle_state.value,
            "transition_kind": kind,
            "severity": instance.current_severity,
            "subject_id": card.get("subject_id") or result.identity_metadata.get(
                instance.identity_key, {}
            ).get("subject_id"),
            "site_id": card.get("site_id") or result.identity_metadata.get(
                instance.identity_key, {}
            ).get("site_id"),
            "concept": card.get("concept") or result.identity_metadata.get(
                instance.identity_key, {}
            ).get("concept"),
            "risk_type": card.get("risk_type") or result.identity_metadata.get(
                instance.identity_key, {}
            ).get("risk_type"),
            "is_candidate": True,
            "is_formal_ae_mh_fact": False,
            "absence_is_not_resolution": kind in (
                "carry_forward_high_risk",
                "not_evaluable",
                "identity_ambiguous",
                "supersede",
            ),
        }
        groups[bucket].append(entry)
        if _is_active_current(instance.lifecycle_state):
            groups["current"].append(entry)

    for key in DELTA_GROUP_KEYS:
        groups[key].sort(key=lambda item: (
            str(item.get("severity") or ""),
            str(item.get("identity_key") or ""),
        ))

    return {
        "fixture_marker": SYNTHETIC_MARKER,
        "semantics": {
            "current": "本次仍然可见、需要关注的活跃风险",
            "new": "本次数据中新建立的风险",
            "escalated": "与上次相比严重程度上调",
            "carry_forward": "从上次延续至本次；高危风险缺失时不得自动结案",
            "resolved": "在完整且已接受的数据清单中确认风险已消失或已纠正",
            "not_evaluable": "覆盖不全、未接受或身份歧义；缺失≠结案",
            "absence_is_not_resolution": True,
        },
        "groups": groups,
        "counts": {key: len(groups[key]) for key in DELTA_GROUP_KEYS},
    }


def _source_refs(items: Any) -> set[str]:
    """Return normalized source locators from string or object links."""
    refs: set[str] = set()
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return refs
    for item in items:
        if isinstance(item, str):
            ref = item
        elif isinstance(item, Mapping):
            ref = str(item.get("source_ref") or item.get("locator") or "")
        else:
            ref = ""
        if ref:
            refs.add(ref)
    return refs


def _audience_query_text(value: str) -> str:
    """Translate the synthetic Query projection into audience-facing Chinese."""
    text = value.replace("SYNTHETIC 全量 listing", "全量数据清单")
    text = text.replace("AE/MH listing", "AE/MH 数据清单")
    text = re.sub(
        r"；证据定位：SYNTHETIC\|[^\n；]+",
        "；相关原始记录见证据下钻",
        text,
    )
    for source, target in _AUDIENCE_TERMS.items():
        text = re.sub(rf"\b{re.escape(source)}\b", target, text, flags=re.IGNORECASE)
    return text


def _bind_queries_to_risk_identities(
    queries: Sequence[Mapping[str, Any]],
    risk_cards: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Derive auditable Query-to-risk bindings from shared evidence locators.

    Subject-only matching is deliberately insufficient: one subject can have
    several concurrent risks and Query drafts.  A Query may bind to more than
    one risk identity when its evidence genuinely overlaps more than one card;
    consumers must use the explicit list instead of guessing by subject.
    """
    card_refs = [
        (
            str(card.get("identity_key") or ""),
            _source_refs(card.get("evidence_links")),
        )
        for card in risk_cards
    ]
    bound: List[Dict[str, Any]] = []
    for query in queries:
        item = dict(query)
        query_refs = _source_refs(
            query.get("evidence_links") or query.get("evidence_refs")
        )
        item["risk_identity_keys"] = sorted(
            identity
            for identity, refs in card_refs
            if identity and query_refs.intersection(refs)
        )
        for field_name in ("basis", "finding", "action"):
            item[field_name] = _audience_query_text(str(item.get(field_name) or ""))
        item["three_part_text"] = (
            f"依据：{item['basis']}\n"
            f"发现：{item['finding']}\n"
            f"行动项：{item['action']}"
        )
        bound.append(item)
    return bound


def _stabilize_coverage(coverage: Any) -> Any:
    """Sort coverage units without mutating accepted Slice 1 objects.

    Slice 1 builds subject/site coverage from set insertion order.  Sorting here
    keeps the audience JS byte-stable across process hash seeds while leaving
    the authoritative Store/analysis objects untouched.
    """
    if coverage is None:
        return None
    data = to_jsonable(coverage)
    if not isinstance(data, dict):
        return data

    def _unit_key(unit: Mapping[str, Any]) -> Tuple[str, str]:
        return (str(unit.get("scope") or ""), str(unit.get("key") or ""))

    for field_name in ("expected", "produced"):
        units = data.get(field_name)
        if isinstance(units, list):
            data[field_name] = sorted(
                (dict(unit) for unit in units if isinstance(unit, Mapping)),
                key=_unit_key,
            )
    return data


def _rehash_projection_versions(data: MutableMapping[str, Any]) -> None:
    """Refresh version source_hash values from already-stabilized payloads."""
    versions = data.get("versions")
    if not isinstance(versions, list):
        return
    project = data.get("project_dashboard") or {}
    sites = data.get("site_dashboards") or {}
    profiles = data.get("subject_profiles") or {}
    timelines = data.get("subject_timelines") or {}
    refreshed: List[Dict[str, Any]] = []
    for version in versions:
        if not isinstance(version, Mapping):
            continue
        item = dict(version)
        kind = item.get("kind")
        subject_id = item.get("subject_id")
        site_id = item.get("site_id")
        if kind == "project_dashboard":
            payload = project
        elif kind == "site_dashboard":
            payload = sites.get(site_id, {})
        elif kind == "subject_profile":
            payload = profiles.get(subject_id, {})
        elif kind == "subject_timeline":
            payload = timelines.get(subject_id, {})
        else:
            payload = {}
        item["source_hash"] = content_hash(payload)
        refreshed.append(item)
    data["versions"] = refreshed


def _stabilize_projections(projections: ProjectionBundle) -> Dict[str, Any]:
    data = projections.as_dict()
    project = data.get("project_dashboard")
    if isinstance(project, dict) and project.get("coverage") is not None:
        project = dict(project)
        project["coverage"] = _stabilize_coverage(project.get("coverage"))
        data["project_dashboard"] = project
    _rehash_projection_versions(data)
    return data


def _analysis_payload(result: AEMHResult, projections: ProjectionBundle) -> Dict[str, Any]:
    projection_data = _stabilize_projections(projections)
    return {
        "fixture_marker": SYNTHETIC_MARKER,
        "project_id": result.project_id,
        "run_id": result.run_id,
        "snapshot_version": result.snapshot_version,
        "coverage_complete": result.coverage_complete,
        "snapshot_baseline_eligible": result.snapshot_baseline_eligible,
        "candidate_fact_separation": result.candidate_fact_separation(),
        "counts": {
            "candidate_count": result.candidate_count,
            "reported_ae_count": result.reported_ae_count,
            "reported_mh_count": result.reported_mh_count,
            "reported_ae_mh_count": result.reported_ae_mh_count,
            "counterevidence_count": len(result.counterevidence),
            "query_count": len(result.queries),
            "candidates_counted_as_reported": 0,
        },
        "reported_facts": to_jsonable(result.reported_facts),
        "candidates": to_jsonable(result.candidates),
        "counterevidence": [item.as_dict() for item in result.counterevidence],
        "queries": to_jsonable(result.queries),
        "lifecycle": to_jsonable(result.lifecycle),
        "identity_metadata": to_jsonable(result.identity_metadata),
        "historical_evidence_refs": to_jsonable(result.historical_evidence_refs),
        "temporal_spines": to_jsonable(result.temporal_spines),
        "coverage": _stabilize_coverage(result.coverage),
        "projections": projection_data,
    }


def _progress_payload(result_n1: AEMHResult) -> Dict[str, Any]:
    detail_nodes = [
        {"id": "seed_snapshots", "label": "准备上次与本次全量数据", "status": "complete"},
        {"id": "analyze_n", "label": "分析上次全量 AE/MH 数据", "status": "complete"},
        {
            "id": "analyze_n1",
            "label": "分析本次全量 AE/MH 数据并核对变化",
            "status": "complete",
        },
        {"id": "project_dashboard", "label": "生成项目、中心与受试者视图", "status": "complete"},
        {"id": "source_index", "label": "建立原始数据定位索引", "status": "complete"},
        {"id": "delta_groups", "label": "整理变化优先风险分组", "status": "complete"},
    ]
    return {
        "fixture_marker": SYNTHETIC_MARKER,
        "status": "complete",
        "completed": len(detail_nodes),
        "total": len(detail_nodes),
        "detail_nodes": detail_nodes,
        "current_work": "本次 AE/MH 风险分析与看板更新已完成",
        "run_id": result_n1.run_id,
        "snapshot_version": result_n1.snapshot_version,
    }


def build_mm_r1_data(*, store: Store) -> Dict[str, Any]:
    """Build the audience payload from accepted Slice 1 APIs."""
    _freeze_clock()
    bundle = seed_synthetic_snapshots(store, project_id=SYNTHETIC_PROJECT_ID)
    snapshot_version_n = f"{SYNTHETIC_MARKER}-N"
    snapshot_version_n1 = f"{SYNTHETIC_MARKER}-N1"

    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id=SYNTHETIC_RUN_N,
        snapshot_version=snapshot_version_n,
        store=store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id=SYNTHETIC_RUN_N1,
        snapshot_version=snapshot_version_n1,
        previous_result=result_n,
        store=store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    projections_n = build_projections(result_n)
    projections_n1 = build_projections(result_n1)
    projections_n1_data = _stabilize_projections(projections_n1)

    source_rows: Dict[str, Dict[str, Any]] = {}
    source_rows.update(
        _build_source_rows(
            bundle.listing_n,
            snapshot_id=bundle.snapshot_n.snapshot_id,
            snapshot_version=snapshot_version_n,
            snapshot_label="N",
        )
    )
    source_rows.update(
        _build_source_rows(
            bundle.listing_n1,
            snapshot_id=bundle.snapshot_n1.snapshot_id,
            snapshot_version=snapshot_version_n1,
            snapshot_label="N+1",
        )
    )

    delta_groups = _build_delta_groups(
        result_n1,
        projections_n1_data["project_dashboard"].get("risk_cards", ()),
    )
    queries = _bind_queries_to_risk_identities(
        projections_n1_data["project_dashboard"].get("queries", ()),
        projections_n1_data["project_dashboard"].get("risk_cards", ()),
    )

    payload: Dict[str, Any] = {
        "fixture_marker": SYNTHETIC_MARKER,
        "synthetic_only": True,
        "disclaimer": DISCLAIMER_ZH,
        "ai_boundary": "AI辅助定位证据与风险，医学经理终审",
        "schema_version": "aemh_audience_workbench_r1_slice3_v1",
        "generated_at": FIXED_NOW_ISO,
        "content_hash": "",  # filled after body is stable
        "snapshot_lineage": {
            "project_id": bundle.project_id,
            "snapshot_n": {
                "snapshot_id": SYNTHETIC_SNAPSHOT_N,
                "snapshot_version": snapshot_version_n,
                "acceptance_state": store.get_acceptance(
                    bundle.snapshot_n.snapshot_id
                ).state.value,
                "row_count": bundle.snapshot_n.row_count,
                "content_hash": bundle.snapshot_n.content_hash,
            },
            "snapshot_n1": {
                "snapshot_id": SYNTHETIC_SNAPSHOT_N1,
                "snapshot_version": snapshot_version_n1,
                "acceptance_state": store.get_acceptance(
                    bundle.snapshot_n1.snapshot_id
                ).state.value,
                "row_count": bundle.snapshot_n1.row_count,
                "content_hash": bundle.snapshot_n1.content_hash,
            },
            "prior_for_n1": "N",
        },
        "run_lineage": {
            "run_n": {
                "run_id": result_n.run_id,
                "snapshot_version": result_n.snapshot_version,
                "candidate_count": result_n.candidate_count,
                "reported_ae_mh_count": result_n.reported_ae_mh_count,
            },
            "run_n1": {
                "run_id": result_n1.run_id,
                "snapshot_version": result_n1.snapshot_version,
                "candidate_count": result_n1.candidate_count,
                "reported_ae_mh_count": result_n1.reported_ae_mh_count,
                "prior_run_id": result_n.run_id,
            },
        },
        "analyses": {
            "n": _analysis_payload(result_n, projections_n),
            "n1": _analysis_payload(result_n1, projections_n1),
        },
        # Default audience surface is N+1 with N as prior for lifecycle.
        "project_dashboard": projections_n1_data["project_dashboard"],
        "site_dashboards": projections_n1_data["site_dashboards"],
        "subject_profiles": projections_n1_data["subject_profiles"],
        "subject_timelines": projections_n1_data["subject_timelines"],
        "projection_versions": projections_n1_data["versions"],
        "source_rows": source_rows,
        "queries": queries,
        "counterevidence": projections_n1_data["project_dashboard"].get(
            "counterevidence", []
        ),
        "coverage": projections_n1_data["project_dashboard"].get("coverage"),
        "coverage_complete": projections_n1_data["project_dashboard"].get(
            "coverage_complete"
        ),
        "candidate_fact_separation": projections_n1_data["project_dashboard"].get(
            "candidate_fact_separation"
        ),
        "delta_groups": delta_groups,
        "progress": _progress_payload(result_n1),
    }
    # Hash excludes the self-referential content_hash field.
    payload["content_hash"] = content_hash({k: v for k, v in payload.items() if k != "content_hash"})
    return payload


def render_mm_r1_js(payload: Mapping[str, Any]) -> str:
    """Render a classic-script assignment ending with a newline."""
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"window.MM_R1_DATA = {body};\n"


def assert_payload_contract(payload: Mapping[str, Any], js_text: str) -> None:
    """Fail closed on non-synthetic or non-script-safe output."""
    if payload.get("fixture_marker") != SYNTHETIC_MARKER:
        raise ValueError("payload fixture_marker must be SYNTHETIC")
    if not payload.get("synthetic_only"):
        raise ValueError("payload must declare synthetic_only=true")
    if "fetch(" in js_text:
        raise ValueError("generated JS must not call fetch")
    if js_text.count("window.MM_R1_DATA") != 1:
        raise ValueError("generated JS must contain exactly one window.MM_R1_DATA assignment")
    if not js_text.endswith("\n"):
        raise ValueError("generated JS must end with a newline")
    if _ABS_PATH_RE.search(js_text):
        raise ValueError("generated JS must not contain absolute filesystem paths")
    # Spot-check shared spine identity for every subject present in both maps.
    profiles = payload.get("subject_profiles") or {}
    timelines = payload.get("subject_timelines") or {}
    for subject_id in sorted(set(profiles) & set(timelines)):
        profile = profiles[subject_id]
        timeline = timelines[subject_id]
        if profile.get("temporal_spine_id") != timeline.get("temporal_spine_id"):
            raise ValueError(f"shared spine id mismatch for {subject_id}")
        if canonical_json(profile.get("temporal_spine")) != canonical_json(
            timeline.get("temporal_spine")
        ):
            raise ValueError(f"shared spine payload mismatch for {subject_id}")


def generate_mm_r1_data_js(output_path: Path) -> Tuple[Dict[str, Any], str]:
    """Generate the JS file under a temporary Store and return payload + text."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mm_r1_slice3_build_") as tmp:
        tmp_path = Path(tmp)
        with Store(tmp_path / "r1.sqlite3", tmp_path / "artifacts") as store:
            payload = build_mm_r1_data(store=store)
    js_text = render_mm_r1_js(payload)
    assert_payload_contract(payload, js_text)
    output_path.write_text(js_text, encoding="utf-8")
    return payload, js_text


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_JS_PATH),
        help="path to write data/mm_r1_data.js (default: slice-local data file)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    output_path = Path(args.output)
    # Keep writes inside the authorized slice root.
    authorized_root = SLICE_ROOT.resolve()
    try:
        output_path.resolve().relative_to(authorized_root)
    except ValueError as exc:
        raise SystemExit(
            f"refusing to write outside authorized slice root: {authorized_root}"
        ) from exc
    payload, js_text = generate_mm_r1_data_js(output_path)
    print("MM_R1_DATA_OK")
    print(f"OUTPUT={output_path}")
    print(f"BYTES={len(js_text.encode('utf-8'))}")
    print(f"CONTENT_HASH={payload['content_hash']}")
    print(f"SOURCE_ROWS={len(payload['source_rows'])}")
    print(
        "DELTA_COUNTS="
        + json.dumps(payload["delta_groups"]["counts"], ensure_ascii=False, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
