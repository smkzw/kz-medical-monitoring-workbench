"""Data-contract tests for Slice 4 ``window.MM_R1_JOURNEY`` fixture.

Run with:
    .venv/bin/python -m pytest -q \\
      poc/medical_monitoring_ai_native_r1/slices/patient_journey/tests/test_data_contract.py
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

SLICE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = SLICE_ROOT / "data" / "journey_fixture.js"
SLICE3_DATA = (
    SLICE_ROOT.parent
    / "aemh_audience_workbench"
    / "data"
    / "mm_r1_data.js"
)

SCHEMA_VERSION = "patient_journey_r1_slice4_v1"
DEFAULT_SUBJECT = "SYNTHETIC-SUBJECT-001"
EXPECTED_SPINE = "spine:SYNTHETIC-RUN-N1:SYNTHETIC-SUBJECT-001"
VISIT_TYPES = {"planned", "actual", "unscheduled"}
GEOMETRIES = {"point", "interval", "interval_open", "pending"}
RECORD_CLASSES = {"formal_fact", "candidate", "established_risk"}

_ABS_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/var/folders/|[A-Za-z]:\\|/tmp/|/private/tmp/)"
)
_ASSIGN_PREFIX = "window.MM_R1_JOURNEY = "
_FORBIDDEN_AUDIENCE_TERMS = (
    "正式事实",
    "正式 AE/MH 事实",
    "候选信号",
    "漏报候选",
    "非正式候选",
    "只读",
    "时间脊事件",
    "正式记录",
)


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


@pytest.fixture(scope="module")
def payload() -> dict:
    assert FIXTURE_PATH.exists(), f"missing fixture: {FIXTURE_PATH}"
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    assert text.startswith(_ASSIGN_PREFIX)
    assert text.endswith(";\n")
    body = text[len(_ASSIGN_PREFIX) : -2]
    data = json.loads(body)
    assert isinstance(data, dict)
    return data


@pytest.fixture(scope="module")
def fixture_text() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def slice3_subject_spine() -> str:
    if not SLICE3_DATA.exists():
        pytest.skip("Slice 3 mm_r1_data.js not available for spine cross-check")
    text = SLICE3_DATA.read_text(encoding="utf-8")
    body = text[len("window.MM_R1_DATA = ") : -2]
    data = json.loads(body)
    profile = data["subject_profiles"][DEFAULT_SUBJECT]
    timeline = data["subject_timelines"][DEFAULT_SUBJECT]
    assert profile["temporal_spine_id"] == timeline["temporal_spine_id"]
    return profile["temporal_spine_id"]


def test_schema_version_and_synthetic_guards(payload, fixture_text):
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["fixture_marker"] == "SYNTHETIC"
    assert payload["synthetic_only"] is True
    assert "合成" in payload["disclaimer"]
    assert "医学经理终审" in payload["ai_boundary"]
    assert payload["default_subject_id"] == DEFAULT_SUBJECT
    assert payload["spine_id"] == EXPECTED_SPINE
    assert fixture_text.count("window.MM_R1_JOURNEY") == 1
    assert "fetch(" not in fixture_text
    assert _ABS_PATH_RE.search(fixture_text) is None


def test_unique_ids_across_collections(payload):
    journey = payload["subject_journey"]
    collections = {
        "visit_id": [v["visit_id"] for v in journey["visits"]],
        "event_id": [e["event_id"] for e in journey["events"]],
        "fact_id": [f["fact_id"] for f in journey["facts"]],
        "candidate_id": [c["candidate_id"] for c in journey["candidates"]],
        "risk_id": [r["risk_id"] for r in journey["risks"]],
        "query_id": [q["query_id"] for q in journey["queries"]],
        "phase_id": [p["phase_id"] for p in journey["phase_bands"]],
        "locator": [row["locator"] for row in journey["evidence_locators"]],
        "planned_visit_id": [
            v["visit_id"] for v in payload["study_schedule"]["planned_visits"]
        ],
        "schedule_phase_id": [
            p["phase_id"] for p in payload["study_schedule"]["phases"]
        ],
    }
    for label, values in collections.items():
        assert values, label
        assert len(values) == len(set(values)), f"duplicate {label}: {values}"


def test_date_ordering_for_phases_visits_events_and_spine(payload):
    journey = payload["subject_journey"]

    phase_starts = [p["start_date"] for p in journey["phase_bands"]]
    assert phase_starts == sorted(phase_starts)
    for phase in journey["phase_bands"]:
        assert _parse_iso_date(phase["end_date"]) >= _parse_iso_date(phase["start_date"])

    schedule_phases = payload["study_schedule"]["phases"]
    assert [p["start_date"] for p in schedule_phases] == sorted(
        p["start_date"] for p in schedule_phases
    )

    dated_visits = [
        v for v in journey["visits"] if v.get("actual_date") or v.get("nominal_date")
    ]

    def visit_sort_key(visit: dict) -> tuple[str, int, str]:
        # Planned anchors sort by nominal date; observed visits by actual date.
        if visit["visit_type"] == "planned":
            axis = visit["nominal_date"]
        else:
            axis = visit["actual_date"]
        return (axis, int(visit.get("order", 0)), visit["visit_id"])

    assert dated_visits == sorted(dated_visits, key=visit_sort_key)

    spine_dates = [e["actual_date"] for e in journey["temporal_spine"]["events"]]
    assert spine_dates == sorted(spine_dates)

    axis_events = [e for e in journey["events"] if e["placement"] == "axis"]

    def event_axis_date(event: dict) -> str:
        return event.get("actual_date") or event.get("start_date")

    axis_dates = [event_axis_date(e) for e in axis_events]
    assert axis_dates == sorted(axis_dates)
    for event in axis_events:
        assert event_axis_date(event)


def test_visit_types_include_planned_actual_unscheduled(payload):
    visits = payload["subject_journey"]["visits"]
    types_present = {v["visit_type"] for v in visits}
    assert types_present == VISIT_TYPES

    for visit in visits:
        assert visit["visit_type"] in VISIT_TYPES
        assert visit["fixture_marker"] == "SYNTHETIC"
        if visit["visit_type"] == "planned":
            assert visit["record_kind"] == "schedule_knowledge_anchor"
            assert visit["is_clinical_fact"] is False
            assert visit.get("nominal_date")
            assert visit.get("actual_date") is None
        elif visit["visit_type"] == "actual":
            assert visit.get("actual_date")
            assert visit["record_kind"] == "visit_occurrence"
            assert visit["is_clinical_fact"] is False
        elif visit["visit_type"] == "unscheduled":
            assert visit.get("actual_date")
            assert visit.get("nominal_date") is None
            assert visit["is_clinical_fact"] is False

    for planned in payload["study_schedule"]["planned_visits"]:
        assert planned["visit_type"] == "planned"
        assert planned["record_kind"] == "schedule_knowledge_anchor"
        assert planned["is_clinical_fact"] is False
        assert planned["nominal_date"]

    schedule = payload["study_schedule"]
    assert schedule["record_kind"] == "schedule_knowledge_anchor"
    assert schedule["is_clinical_fact"] is False


def test_interval_validity_and_pending_surface(payload):
    events = payload["subject_journey"]["events"]
    geometries = {e["geometry"] for e in events}
    assert "point" in geometries
    assert "interval" in geometries
    assert "interval_open" in geometries
    assert "pending" in geometries

    pending_count = 0
    open_count = 0
    closed_count = 0
    for event in events:
        assert event["geometry"] in GEOMETRIES
        if event["geometry"] == "point":
            assert event.get("actual_date")
            assert event["placement"] == "axis"
        elif event["geometry"] == "interval":
            closed_count += 1
            assert event.get("start_date") and event.get("end_date")
            assert event.get("open_ended") is False
            assert _parse_iso_date(event["end_date"]) >= _parse_iso_date(
                event["start_date"]
            )
            assert event["placement"] == "axis"
        elif event["geometry"] == "interval_open":
            open_count += 1
            assert event.get("start_date")
            assert event.get("end_date") is None
            assert event.get("open_ended") is True
            assert event["placement"] == "axis"
        elif event["geometry"] == "pending":
            pending_count += 1
            assert event["placement"] == "pending_date_surface"
            assert event["date_status"] in {"missing", "partial", "conflicted"}
            assert event.get("actual_date") is None
            assert event.get("start_date") is None
            assert event.get("end_date") is None

    assert closed_count >= 1
    assert open_count >= 1
    assert pending_count >= 1


def test_source_and_evidence_coverage(payload):
    journey = payload["subject_journey"]
    locator_index = {row["locator"]: row for row in journey["evidence_locators"]}
    assert locator_index

    for locator, row in locator_index.items():
        assert locator.startswith("SYNTHETIC|")
        assert "SYNTHETIC" in row["record_id"]
        assert row["subject_id"] == DEFAULT_SUBJECT

    def refs_of(item: dict, *keys: str) -> list[str]:
        for key in keys:
            if key in item and item[key] is not None:
                values = item[key]
                if isinstance(values, list):
                    return values
        return []

    for event in journey["events"]:
        refs = refs_of(event, "source_refs", "evidence_refs")
        assert refs, event["event_id"]
        for ref in refs:
            assert ref in locator_index, ref

    for fact in journey["facts"]:
        for ref in fact["evidence_refs"]:
            assert ref in locator_index

    for candidate in journey["candidates"]:
        for ref in candidate["evidence_refs"]:
            assert ref in locator_index

    for risk in journey["risks"]:
        assert risk["evidence_refs"]
        for ref in risk["evidence_refs"]:
            assert ref in locator_index

    for query in journey["queries"]:
        assert query["evidence_refs"]
        for ref in query["evidence_refs"]:
            assert ref in locator_index

    # Reuse Slice 3 locators where they truly exist.
    reused = set(payload["slice3_reference"]["reused_locators"])
    assert reused
    for locator in reused:
        assert locator in locator_index
        assert locator_index[locator]["origin"] == "slice3"
        assert locator.startswith("SYNTHETIC|snapshot=")


def test_risk_to_event_and_query_binding(payload):
    journey = payload["subject_journey"]
    events = {e["event_id"]: e for e in journey["events"]}
    queries = {q["query_id"]: q for q in journey["queries"]}
    risks = journey["risks"]
    assert risks

    medium_or_higher = {"medium", "high", "severe"}
    assert any(r["severity"] in medium_or_higher for r in risks)

    for risk in risks:
        assert risk["record_class"] == "established_risk"
        assert risk["shape"] == "established_risk"
        assert risk["is_formal_ae_mh_fact"] is False
        assert risk["candidate_not_counted_as_reported"] is True
        assert risk["lifecycle_state"] == "established"
        assert risk["anchor_event_id"] in events
        anchor = events[risk["anchor_event_id"]]
        assert anchor["placement"] == "axis"
        assert anchor.get("actual_date") or anchor.get("start_date")
        assert risk.get("anchor_actual_date") == (
            anchor.get("actual_date") or anchor.get("start_date")
        )

        risk_refs = set(risk["evidence_refs"])
        assert risk_refs
        assert risk_refs.intersection(set(anchor["source_refs"]))

        assert risk["query_ids"]
        for query_id in risk["query_ids"]:
            assert query_id in queries
            query = queries[query_id]
            assert risk["identity_key"] in query["risk_identity_keys"]
            assert risk["risk_id"] in query.get("risk_ids", [])
            query_refs = set(query["evidence_refs"])
            assert query_refs.intersection(risk_refs)
            assert query["anchor_event_id"] == risk["anchor_event_id"]


def test_same_spine_semantics(payload, slice3_subject_spine):
    journey = payload["subject_journey"]
    state = payload["shared_view_state"]

    assert payload["spine_id"] == EXPECTED_SPINE
    assert journey["spine_id"] == EXPECTED_SPINE
    assert journey["temporal_spine"]["spine_id"] == EXPECTED_SPINE
    assert state["spine_id"] == EXPECTED_SPINE
    assert state["subject_id"] == journey["subject_id"] == DEFAULT_SUBJECT
    assert state["project_id"] == payload["project_id"]
    assert state["run_id"] == payload["run_id"]
    assert state["snapshot_id"] == payload["snapshot_id"]
    assert state["axis_mode"] == "actual_date"
    assert state["tabs"] == ["旅程总览", "指标趋势", "事件明细", "风险证据"]

    spine_event_ids = {e["event_id"] for e in journey["temporal_spine"]["events"]}
    axis_event_ids = {
        e["event_id"] for e in journey["events"] if e["placement"] == "axis"
    }
    assert spine_event_ids == axis_event_ids

    assert slice3_subject_spine == EXPECTED_SPINE
    assert payload["slice3_reference"]["shared_spine_id"] == slice3_subject_spine
    assert payload["slice3_reference"]["read_only"] is True
    assert payload["slice3_reference"]["must_not_copy_or_edit"] is True


def test_candidate_not_formal_invariants(payload):
    journey = payload["subject_journey"]
    sep = journey["candidate_fact_separation"]

    fact_ids = {f["fact_id"] for f in journey["facts"]}
    candidate_ids = {c["candidate_id"] for c in journey["candidates"]}
    assert fact_ids
    assert candidate_ids
    assert fact_ids.isdisjoint(candidate_ids)
    assert set(sep["reported_fact_ids"]) == fact_ids
    assert set(sep["candidate_ids"]) == candidate_ids
    assert sep["candidates_counted_as_reported"] is False
    assert sep["reported_ae_mh_count"] == len(fact_ids)
    assert sep["candidate_count"] == len(candidate_ids)

    for fact in journey["facts"]:
        assert fact["record_class"] == "formal_fact"
        assert fact["is_formal_ae_mh_fact"] is True
        assert fact["shape"] == "fact"
        assert fact["line_style"] == "solid"
        assert fact["anchor_event_id"]

    for candidate in journey["candidates"]:
        assert candidate["record_class"] == "candidate"
        assert candidate["is_formal_ae_mh_fact"] is False
        assert candidate["candidate_not_counted_as_reported"] is True
        assert candidate["shape"] == "candidate"
        assert candidate["line_style"] == "dashed"

    for risk in journey["risks"]:
        assert risk["is_formal_ae_mh_fact"] is False
        assert risk["candidate_not_counted_as_reported"] is True
        assert risk["record_class"] == "established_risk"

    for event in journey["events"]:
        assert event["record_class"] in RECORD_CLASSES
        if event["record_class"] == "formal_fact" and event.get("is_formal_ae_mh_fact"):
            assert event["shape"] == "fact"
            assert event["line_style"] == "solid"
        if event["record_class"] == "candidate":
            assert event["is_formal_ae_mh_fact"] is False
            assert event.get("candidate_not_counted_as_reported") is True
            assert event["shape"] == "candidate"
            assert event["line_style"] == "dashed"

    # Schedule knowledge anchors must never be formal AE/MH facts.
    for planned in payload["study_schedule"]["planned_visits"]:
        assert planned["is_clinical_fact"] is False
    for visit in journey["visits"]:
        if visit["record_kind"] == "schedule_knowledge_anchor":
            assert visit["is_clinical_fact"] is False


def test_audience_assets_do_not_expose_internal_terms():
    audience_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            SLICE_ROOT / "index.html",
            SLICE_ROOT / "app.js",
            FIXTURE_PATH,
        )
    )
    for term in _FORBIDDEN_AUDIENCE_TERMS:
        assert term not in audience_text, term
