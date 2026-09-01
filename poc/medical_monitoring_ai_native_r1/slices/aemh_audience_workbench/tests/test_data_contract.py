"""Data-contract tests for Slice 3 ``window.MM_R1_DATA`` generation.

Run with:
    .venv/bin/python -m pytest -q \\
      poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/tests/test_data_contract.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

SLICE_ROOT = Path(__file__).resolve().parents[1]
POC_ROOT = SLICE_ROOT.parents[1]
SRC_ROOT = POC_ROOT / "src"

import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(SLICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SLICE_ROOT))

from build_data import (  # noqa: E402
    DEFAULT_JS_PATH,
    DELTA_GROUP_KEYS,
    FIXED_NOW_ISO,
    generate_mm_r1_data_js,
    render_mm_r1_js,
)
from mm_r1.domain import canonical_json, content_hash  # noqa: E402
from mm_r1.fixtures import SYNTHETIC_MARKER  # noqa: E402

_ABS_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/var/folders/|[A-Za-z]:\\|/tmp/|/private/tmp/)"
)
_FORBIDDEN_PHRASES = (
    "AI自动判断",
    "AI替代医学判断",
)
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


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    out = tmp_path_factory.mktemp("mm_r1_data") / "mm_r1_data.js"
    payload, js_text = generate_mm_r1_data_js(out)
    return {"path": out, "payload": payload, "js": js_text}


def test_js_is_classic_script_with_single_assignment(generated):
    js = generated["js"]
    assert js.startswith("window.MM_R1_DATA = ")
    assert js.endswith("\n")
    assert js.count("window.MM_R1_DATA") == 1
    assert "fetch(" not in js
    # Must parse as JSON object after the assignment prefix/suffix.
    body = js[len("window.MM_R1_DATA = ") : -2]  # drop trailing `;\n`
    assert body.endswith("}")
    parsed = json.loads(body)
    assert parsed["fixture_marker"] == SYNTHETIC_MARKER


def test_generation_is_byte_deterministic(tmp_path):
    first = tmp_path / "a.js"
    second = tmp_path / "b.js"
    payload_a, js_a = generate_mm_r1_data_js(first)
    payload_b, js_b = generate_mm_r1_data_js(second)
    assert js_a == js_b
    assert payload_a["content_hash"] == payload_b["content_hash"]
    assert content_hash(payload_a) == content_hash(payload_b)
    assert FIXED_NOW_ISO in js_a


def test_generation_is_deterministic_across_hash_seeds():
    """Audience JS must not depend on PYTHONHASHSEED / set iteration order."""
    import os
    import subprocess

    script = SLICE_ROOT / "build_data.py"
    outputs = []
    temp_paths = []
    try:
        for seed in ("0", "1", "42"):
            out = SLICE_ROOT / "data" / f"_determinism_seed_{seed}.js"
            temp_paths.append(out)
            env = dict(os.environ)
            env["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                [sys.executable, str(script), "--output", str(out)],
                cwd=str(SLICE_ROOT.parents[2]),  # workbench root
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr or completed.stdout
            outputs.append(out.read_text(encoding="utf-8"))
        assert outputs[0] == outputs[1] == outputs[2]
    finally:
        for path in temp_paths:
            if path.exists():
                path.unlink()


def test_output_is_synthetic_only_without_absolute_paths(generated):
    js = generated["js"]
    payload = generated["payload"]
    assert payload["synthetic_only"] is True
    assert payload["fixture_marker"] == SYNTHETIC_MARKER
    assert "合成演示数据" in payload["disclaimer"]
    assert "AI辅助定位证据与风险，医学经理终审" in payload["ai_boundary"]
    assert _ABS_PATH_RE.search(js) is None
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase not in js
    # Every source locator and identifier remains visibly synthetic.
    for locator, row in payload["source_rows"].items():
        assert locator.startswith("SYNTHETIC|")
        assert row["fixture_marker"] == SYNTHETIC_MARKER
        assert "SYNTHETIC" in str(row.get("subject_id") or "")
        assert "SYNTHETIC" in str(row.get("record_id") or "")


def test_source_locator_resolves_to_raw_row(generated):
    payload = generated["payload"]
    source_rows = payload["source_rows"]
    assert source_rows
    # Evidence links on the project dashboard must resolve.
    for link in payload["project_dashboard"]["evidence_links"]:
        ref = link["source_ref"] if isinstance(link, dict) else link
        # Historical refs may point at N rows; both snapshots are indexed.
        assert ref in source_rows, ref
        row = source_rows[ref]
        assert row["locator"] == ref
        assert row["table"]
        assert row["record_id"]
        assert isinstance(row["raw_values"], dict)
        assert row["raw_values"].get("fixture_marker") == SYNTHETIC_MARKER


def test_candidate_counts_remain_separate_from_reported_facts(generated):
    payload = generated["payload"]
    dash = payload["project_dashboard"]
    sep = dash["candidate_fact_separation"]
    assert sep["candidates_counted_as_reported"] is False
    assert dash["counts"]["candidates_counted_as_reported"] == 0
    assert dash["counts"]["candidate_count"] == sep["candidate_count"]
    assert dash["counts"]["reported_ae_mh_count"] == len(sep["reported_fact_ids"])
    assert set(sep["candidate_ids"]).isdisjoint(set(sep["reported_fact_ids"]))
    for card in dash["risk_cards"]:
        assert card["is_formal_ae_mh_fact"] is False
        assert card["candidate_not_counted_as_reported"] is True


def test_delta_groups_cover_required_semantics(generated):
    payload = generated["payload"]
    delta = payload["delta_groups"]
    assert delta["semantics"]["absence_is_not_resolution"] is True
    groups = delta["groups"]
    for key in DELTA_GROUP_KEYS:
        assert key in groups
        assert delta["counts"][key] == len(groups[key])
    # Synthetic N→N+1 fixture expectations.
    assert any(item.get("transition_kind") == "carry_forward_high_risk"
               for item in groups["carry_forward"])
    assert any(item.get("transition_kind") == "resolve"
               for item in groups["resolved"])
    # Absence must not be mislabeled as resolved for high-risk carry-forward.
    for item in groups["carry_forward"]:
        if item.get("transition_kind") == "carry_forward_high_risk":
            assert item["absence_is_not_resolution"] is True
            assert item["lifecycle_state"] != "resolved_by_data"
    # Resolved entries are explicit resolved_by_data, not mere absence.
    for item in groups["resolved"]:
        assert item["lifecycle_state"] == "resolved_by_data"
        assert item["transition_kind"] == "resolve"


def test_profile_and_timeline_share_spine_identity_and_payload(generated):
    payload = generated["payload"]
    profiles = payload["subject_profiles"]
    timelines = payload["subject_timelines"]
    assert profiles and timelines
    assert set(profiles) == set(timelines)
    for subject_id in profiles:
        profile = profiles[subject_id]
        timeline = timelines[subject_id]
        assert profile["temporal_spine_id"] == timeline["temporal_spine_id"]
        assert profile["temporal_spine_id"].startswith("spine:")
        assert canonical_json(profile["temporal_spine"]) == canonical_json(
            timeline["temporal_spine"]
        )
        assert profile["temporal_spine"] == timeline["temporal_spine"]
        # Candidate overlays remain visually distinct from formal facts.
        for overlay in timeline.get("candidate_overlays", []):
            assert overlay.get("shape") == "candidate"
            assert overlay.get("line_style") == "dashed"
        for overlay in timeline.get("reported_event_overlays", []):
            assert overlay.get("shape") == "fact"
            assert overlay.get("line_style") == "solid"


def test_both_full_analyses_are_present_with_n_as_prior(generated):
    payload = generated["payload"]
    assert "n" in payload["analyses"] and "n1" in payload["analyses"]
    assert payload["run_lineage"]["run_n1"]["prior_run_id"] == payload["run_lineage"]["run_n"]["run_id"]
    assert payload["snapshot_lineage"]["prior_for_n1"] == "N"
    assert payload["analyses"]["n"]["snapshot_version"] == "SYNTHETIC-N"
    assert payload["analyses"]["n1"]["snapshot_version"] == "SYNTHETIC-N1"
    assert payload["progress"]["status"] == "complete"
    assert payload["progress"]["completed"] == payload["progress"]["total"]


def test_queries_bind_to_risk_identities_by_shared_evidence(generated):
    payload = generated["payload"]
    cards = {
        card["identity_key"]: {
            link["source_ref"] if isinstance(link, dict) else link
            for link in card.get("evidence_links", [])
        }
        for card in payload["project_dashboard"]["risk_cards"]
    }
    assert payload["queries"]
    for query in payload["queries"]:
        query_refs = {
            link["source_ref"] if isinstance(link, dict) else link
            for link in query.get("evidence_links", query.get("evidence_refs", []))
        }
        assert query["risk_identity_keys"], query["query_id"]
        assert "listing" not in query["three_part_text"]
        assert "证据定位：SYNTHETIC|" not in query["three_part_text"]
        assert "依据：" in query["three_part_text"]
        assert "发现：" in query["three_part_text"]
        assert "行动项：" in query["three_part_text"]
        for identity in query["risk_identity_keys"]:
            assert identity in cards
            assert query_refs.intersection(cards[identity])


def test_default_checked_in_js_matches_generator(generated, tmp_path):
    """Regenerate and compare against the committed data file when present."""
    if not DEFAULT_JS_PATH.exists():
        pytest.skip("committed mm_r1_data.js not yet written")
    committed = DEFAULT_JS_PATH.read_text(encoding="utf-8")
    regen_path = tmp_path / "regen.js"
    _, regen = generate_mm_r1_data_js(regen_path)
    assert committed == regen
    assert render_mm_r1_js(generated["payload"]) == regen


def test_audience_assets_do_not_expose_internal_terms():
    audience_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            SLICE_ROOT / "index.html",
            SLICE_ROOT / "app.js",
            DEFAULT_JS_PATH,
        )
    )
    for term in _FORBIDDEN_AUDIENCE_TERMS:
        assert term not in audience_text, term
