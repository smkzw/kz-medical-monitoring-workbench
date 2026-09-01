"""R7 Slice-07C-1 synthetic run-setup contract tests.

These tests cover only the stdlib-only data contract: complete synthetic
listings, same-project published baselines, canonical keyed diffs, versioned
special-risk rules, and deterministic template-to-work-unit manifests.  They
do not start a service, invoke a model, or touch a real project.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from conftest import POC_ROOT, SRC_DIR
from fixtures_run_setup import (
    CURRENT_ROWS,
    CURRENT_SNAPSHOT_REF,
    MODE_DAILY,
    MODE_POST_LOCK_PRE_CFDI,
    MODE_PRE_LOCK,
    OTHER_PROJECT_ID,
    PRE_LOCK_ALT_SNAPSHOT_REF,
    PRIOR_ROWS,
    PRIOR_SNAPSHOT_REF,
    PROJECT_ID,
    make_catalog,
    make_fixture,
    make_no_key_catalog,
)
from mm_r7.run_setup import (
    BASIS_FULL,
    BASIS_INCREMENTAL,
    DIFF_ADDED,
    DIFF_DELETED,
    DIFF_REVISED,
    DIFF_UNCHANGED,
    RunSetupError,
    RiskRuleRegistry,
    canonical_keyed_diff,
    generate_work_units,
    get_mode_template,
    public_revision_token,
)


EXPECTED_MODES = (MODE_DAILY, MODE_PRE_LOCK, MODE_POST_LOCK_PRE_CFDI)


def _row_label(row: Any) -> str:
    """Get the explicit stable key from either side of a diff row."""

    source = row.current or row.prior
    assert source is not None
    return str(source["canonical_key"])


def _close_catalog(catalog: Any) -> None:
    catalog.close()


def test_options_expose_three_modes_and_filter_baselines_by_contract() -> None:
    catalog = make_catalog()
    try:
        options = catalog.get_options(
            PROJECT_ID, current_snapshot_ref=CURRENT_SNAPSHOT_REF
        )
        assert options.project_id == PROJECT_ID
        assert options.recommended_mode == MODE_DAILY
        assert tuple(mode.mode for mode in options.modes) == EXPECTED_MODES
        assert options.current_data is not None
        assert options.current_data.snapshot_ref == CURRENT_SNAPSHOT_REF
        assert len(options.current_data.rows) == len(CURRENT_ROWS)

        daily = options.modes[0]
        assert daily.default_execution_basis == BASIS_INCREMENTAL
        assert daily.recommended is True
        assert daily.published_baselines
        assert [item.run_id for item in daily.published_baselines] == [
            "synthetic-daily-published-001"
        ]
        assert daily.published_baselines[0].published is True

        pre_lock = options.modes[1]
        assert pre_lock.default_execution_basis == BASIS_FULL
        assert [item.run_id for item in pre_lock.published_baselines] == [
            "synthetic-pre-lock-published-002",
            "synthetic-pre-lock-published-001",
        ]
        assert pre_lock.published_baselines[0].snapshot_ref == PRE_LOCK_ALT_SNAPSHOT_REF
        assert pre_lock.published_baselines[0].published is True
        assert pre_lock.published_baselines[0].public_projection(recommended=True)["recommended"] is True
        assert pre_lock.published_baselines[1].public_projection()["recommended"] is False

        # Unpublished, fixed-total, mixed-mode, and cross-project candidates
        # are all present in the fixture but absent from selectable options.
        assert all(item.published and not item.fixed_total for item in pre_lock.published_baselines)
        assert all(item.project_id == PROJECT_ID for item in pre_lock.published_baselines)
        assert options.modes[2].published_baselines == ()
        assert all(
            baseline.mode == mode.mode
            for mode in options.modes[:2]
            for baseline in mode.published_baselines
        )

        public = options.as_dict()
        assert public["schema_version"] == "mm-r7-slice07c1-run-setup-v1"
        assert public["project_id"] == PROJECT_ID
        assert public["rule_revisions"] == []
    finally:
        _close_catalog(catalog)

def test_pre_lock_baseline_candidates_require_explicit_selection() -> None:
    catalog = make_catalog()
    try:
        candidates = catalog.baseline_candidates(PROJECT_ID, MODE_PRE_LOCK)
        assert [item.run_id for item in candidates] == [
            "synthetic-pre-lock-published-002",
            "synthetic-pre-lock-published-001",
        ]

        selected = catalog.baseline_for_token(
            PROJECT_ID, MODE_PRE_LOCK, candidates[1].baseline_token
        )
        assert selected.run_id == "synthetic-pre-lock-published-001"
        manifest = generate_work_units(
            MODE_PRE_LOCK,
            BASIS_FULL,
            current_snapshot_token="snapshot:synthetic-current-v1",
            prior_baseline_token=selected.baseline_token,
        )
        assert manifest.prior_baseline_token == selected.baseline_token
        assert manifest.denominator == len(get_mode_template(MODE_PRE_LOCK).nodes)

        ref_selected = catalog.baseline_for_token(
            PROJECT_ID, MODE_PRE_LOCK, candidates[0].snapshot_ref
        )
        assert ref_selected == candidates[0]

        with pytest.raises(RunSetupError) as error:
            catalog.baseline_for_token(
                OTHER_PROJECT_ID, MODE_PRE_LOCK, candidates[0].baseline_token
            )
        assert error.value.code == "baseline_not_published"

        with pytest.raises(RunSetupError) as error:
            catalog.baseline_for_token(
                PROJECT_ID, MODE_PRE_LOCK, "baseline:expired-synthetic-token"
            )
        assert error.value.code == "baseline_not_published"
    finally:
        _close_catalog(catalog)


def test_snapshot_option_token_expiry_fails_closed_after_options_refresh() -> None:
    source = make_catalog()
    try:
        current = source.get_options(PROJECT_ID).current_data
        assert current is not None
        expired_token = current.snapshot_token
    finally:
        _close_catalog(source)

    refreshed = make_catalog()
    try:
        refreshed.snapshots = tuple(
            item for item in refreshed.snapshots if item.snapshot_token != expired_token
        )
        with pytest.raises(RunSetupError) as error:
            refreshed.snapshot_for_token(PROJECT_ID, expired_token)
        assert error.value.code == "invalid_snapshot"
    finally:
        _close_catalog(refreshed)


def test_recommendation_reason_tracks_last_mode_without_changing_modes() -> None:
    for mode in EXPECTED_MODES:
        catalog = make_catalog(last_mode=mode)
        try:
            options = catalog.get_options(PROJECT_ID)
            assert options.recommended_mode == mode
            assert [item.mode for item in options.modes if item.recommended] == [mode]
            selected = next(item for item in options.modes if item.mode == mode)
            assert options.recommendation_reason == selected.recommendation_reason
        finally:
            _close_catalog(catalog)


def test_complete_listing_incremental_diff_carries_all_change_statuses() -> None:
    diff = canonical_keyed_diff(CURRENT_ROWS, PRIOR_ROWS)

    assert diff.comparable is True
    assert diff.key_fields == ("canonical_key",)
    assert diff.counts == {
        "added": 1,
        "revised": 2,
        "unchanged": 1,
        "deleted": 1,
        "cannot_compare": 0,
    }
    statuses = {_row_label(row): row.status for row in diff.rows}
    assert statuses == {
        "PT-001|V1": DIFF_UNCHANGED,
        "PT-002|V1": DIFF_REVISED,
        "PT-003|V1": DIFF_ADDED,
        "PT-004|V1": DIFF_DELETED,
        "PT-005|V1": DIFF_REVISED,
    }
    by_key = {_row_label(row): row for row in diff.rows}
    assert by_key["PT-002|V1"].changed_fields == (
        "alt",
        "query_ref",
        "revision_attribution",
        "risk_level",
    )
    assert by_key["PT-002|V1"].attribution_text == "Query 后修订影响"
    assert by_key["PT-005|V1"].attribution_text == "本轮数据修订变化"
    assert by_key["PT-004|V1"].current is None

    # Reordering either complete listing cannot change the canonical result.
    reordered = canonical_keyed_diff(tuple(reversed(CURRENT_ROWS)), tuple(reversed(PRIOR_ROWS)))
    assert reordered.as_dict() == diff.as_dict()


def test_end_to_end_options_baseline_diff_and_incremental_manifest() -> None:
    catalog = make_catalog()
    try:
        options = catalog.get_options(
            PROJECT_ID, current_snapshot_ref=CURRENT_SNAPSHOT_REF
        )
        current = options.current_data
        assert current is not None
        daily = next(item for item in options.modes if item.mode == MODE_DAILY)
        baseline = daily.published_baselines[0]
        assert baseline.snapshot_ref == PRIOR_SNAPSHOT_REF

        diff = canonical_keyed_diff(current.rows, baseline.rows, current.key_fields)
        manifest = generate_work_units(
            MODE_DAILY,
            daily.default_execution_basis,
            current_snapshot_token=current.snapshot_token,
            prior_baseline_token=baseline.baseline_token,
            diff=diff,
        )

        # The source remains a complete listing (4 rows); incremental only
        # adds carriers for the four changed rows, retaining deleted records.
        assert len(current.rows) == 4
        assert manifest.execution_basis == BASIS_INCREMENTAL
        assert manifest.current_snapshot_token == current.snapshot_token
        assert manifest.prior_baseline_token == baseline.baseline_token
        assert manifest.source_diff_digest == diff.digest
        assert manifest.denominator == len(get_mode_template(MODE_DAILY).nodes) + 4
        assert manifest.denominator == 14
        assert [unit.ordinal for unit in manifest.units] == list(
            range(1, manifest.denominator + 1)
        )
        diff_units = manifest.units[len(get_mode_template(MODE_DAILY).nodes) :]
        assert {_row_label(next(row for row in diff.rows if row.key == unit.target_ref)) for unit in diff_units} == {
            "PT-002|V1",
            "PT-003|V1",
            "PT-004|V1",
            "PT-005|V1",
        }
        assert all(unit.mandatory for unit in manifest.units)
    finally:
        _close_catalog(catalog)


def test_options_without_any_project_snapshot_remain_valid() -> None:
    catalog = make_catalog()
    try:
        options = catalog.get_options("project-without-snapshots")
        projection = options.public_projection()

        assert options.current_data is None
        assert projection["current_data"] is None
        assert tuple(item.mode for item in options.modes) == EXPECTED_MODES
        assert all(item.available for item in options.modes)
    finally:
        _close_catalog(catalog)


def test_missing_stable_key_fails_closed_and_disables_daily_incremental() -> None:
    catalog = make_no_key_catalog()
    try:
        options = catalog.get_options(PROJECT_ID)
        daily = options.modes[0]
        assert daily.default_execution_basis == BASIS_FULL
        assert daily.basis_disabled_reasons[BASIS_INCREMENTAL] == (
            "当前数据尚不能与上次结果逐项比较。"
        )
        assert daily.public_projection()["execution_basis_options"][0] == {
            "value": BASIS_INCREMENTAL,
            "label": "增量",
            "available": False,
            "disabled_reason": "当前数据尚不能与上次结果逐项比较。",
        }
    finally:
        _close_catalog(catalog)

    diff = canonical_keyed_diff(
        ({"subject_id": "PT-001", "value": 2},),
        ({"subject_id": "PT-001", "value": 1},),
    )
    assert diff.comparable is False
    assert diff.status == "cannot_compare"
    assert diff.rows == ()
    assert diff.reason == "当前数据尚不能与上次结果逐项比较。"


def test_mode_templates_are_the_only_full_manifest_source_and_denominator() -> None:
    expected_denominators = {
        MODE_DAILY: 10,
        MODE_PRE_LOCK: 11,
        MODE_POST_LOCK_PRE_CFDI: 11,
    }
    for mode, expected in expected_denominators.items():
        template = get_mode_template(mode)
        manifest = generate_work_units(
            mode,
            BASIS_FULL,
            current_snapshot_token="snapshot:synthetic-current",
        )
        assert manifest.template_version == template.version
        assert manifest.denominator == expected
        assert manifest.denominator == len(template.nodes)
        assert [unit.ordinal for unit in manifest.units] == list(range(1, expected + 1))
        assert [unit.stage for unit in manifest.units] == [node.stage for node in template.nodes]
        assert [unit.label for unit in manifest.units] == [node.label for node in template.nodes]
        assert [unit.target_ref for unit in manifest.units] == [
            node.target_ref for node in template.nodes
        ]
        assert all(
            unit.work_unit_id == "r7:%s:%s:%s" % (mode, template.version, node.node_key)
            for unit, node in zip(manifest.units, template.nodes)
        )

    with pytest.raises(RunSetupError) as error:
        generate_work_units(MODE_PRE_LOCK, BASIS_INCREMENTAL)
    assert error.value.code == "incremental_not_supported_for_mode"


def test_risk_rule_ambiguity_confirmation_versions_and_history_are_immutable() -> None:
    registry = RiskRuleRegistry()
    try:
        ambiguous = registry.preview(PROJECT_ID, "请重点关注异常")
        assert ambiguous.state == "ambiguous"
        assert ambiguous.confirmable is False
        assert len(ambiguous.candidates) == 2
        assert ambiguous.as_dict()["status"] == "待确认的关注规则"
        assert all(candidate.applicable_scope == "项目内全部适用范围" for candidate in ambiguous.candidates)
        with pytest.raises(RunSetupError) as error:
            registry.append_revision(PROJECT_ID, ambiguous)
        assert error.value.code == "ambiguous_risk_rule"

        first_preview = registry.preview(PROJECT_ID, "ALT > 3x ULN")
        first = registry.append_revision(
            PROJECT_ID,
            first_preview,
            created_at="2026-08-29T01:00:00+08:00",
            idempotency_key="same-confirmation",
        )
        assert first.revision == 1
        assert first.selectable is True
        assert first.starting_run == "本次确认后明确选择的运行"
        assert first.summary == "肝功能相关数据：ALT > 3x ULN"
        assert registry.resolve_public_token(
            PROJECT_ID, public_revision_token(first.revision_token)
        ) == first
        with pytest.raises(RunSetupError) as error:
            registry.resolve_public_token(
                OTHER_PROJECT_ID, public_revision_token(first.revision_token)
            )
        assert error.value.code == "risk_rule_not_found"

        replayed_again = registry.append_revision(
            PROJECT_ID,
            first_preview,
            created_at="2026-08-29T01:06:00+08:00",
            idempotency_key="same-confirmation",
        )
        assert replayed_again == first

        historical_manifest = generate_work_units(
            MODE_DAILY,
            BASIS_FULL,
            current_snapshot_token="snapshot:synthetic-current",
            rule_revisions=(first,),
        )
        assert historical_manifest.denominator == 11
        assert historical_manifest.units[-1].target_ref == first.revision_token

        second_preview = registry.preview(PROJECT_ID, "关注发热或感染事件")
        second = registry.append_revision(
            PROJECT_ID, second_preview, created_at="2026-08-29T02:00:00+08:00"
        )
        assert second.revision == 2
        assert second.revision_token != first.revision_token
        assert second.rule_digest != first.rule_digest
        assert [(item.revision, item.summary) for item in registry.list_revisions(PROJECT_ID)] == [
            (1, "肝功能相关数据：ALT > 3x ULN"),
            (2, "感染/发热相关事件：关注发热或感染事件"),
        ]

        # Later project revisions are opt-in and cannot rewrite a historical
        # manifest that selected only revision 1.
        replay = generate_work_units(
            MODE_DAILY,
            BASIS_FULL,
            current_snapshot_token="snapshot:synthetic-current",
            rule_revisions=(first,),
        )
        assert replay.as_dict() == historical_manifest.as_dict()
        current = generate_work_units(
            MODE_DAILY,
            BASIS_FULL,
            current_snapshot_token="snapshot:synthetic-current",
            rule_revisions=(first, second),
        )
        assert current.denominator == historical_manifest.denominator + 1
        assert [unit.target_ref for unit in current.units[-2:]] == [
            first.revision_token,
            second.revision_token,
        ]

        from mm_r7.run_setup import RunSetupCatalog

        options_catalog = RunSetupCatalog(
            project_id=PROJECT_ID,
            snapshots=make_fixture()["snapshots"],
            published_baselines=make_fixture()["baselines"],
            risk_rule_registry=registry,
        )
        assert [
            item.revision
            for item in options_catalog.get_options(PROJECT_ID).rule_revisions
        ] == [1, 2]
        assert options_catalog.get_options(OTHER_PROJECT_ID).rule_revisions == ()
    finally:
        registry.close()


def test_slice07c1_digest_and_manifest_are_stable_across_hash_seeds() -> None:
    script = r'''
import json
from fixtures_run_setup import CURRENT_ROWS, PRIOR_ROWS, PROJECT_ID, make_catalog
from mm_r7.run_setup import BASIS_INCREMENTAL, MODE_DAILY, canonical_keyed_diff, generate_work_units

catalog = make_catalog()
try:
    options = catalog.get_options(PROJECT_ID)
    current = options.current_data
    daily = options.modes[0]
    baseline = daily.published_baselines[0]
    diff = canonical_keyed_diff(CURRENT_ROWS, PRIOR_ROWS)
    manifest = generate_work_units(
        MODE_DAILY,
        BASIS_INCREMENTAL,
        current_snapshot_token=current.snapshot_token,
        prior_baseline_token=baseline.baseline_token,
        diff=diff,
    )
    print(json.dumps({
        "options": options.as_dict(),
        "diff": diff.as_dict(),
        "manifest": manifest.as_dict(),
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
finally:
    catalog.close()
'''
    outputs = []
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(SRC_DIR), str(Path(__file__).parent), existing) if item
    )
    for seed in ("0", "1", "42"):
        env["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(POC_ROOT),
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        outputs.append(completed.stdout)

    assert outputs[0] == outputs[1] == outputs[2]
    payload = json.loads(outputs[0])
    assert payload["diff"]["diff_digest"]
    assert payload["manifest"]["denominator"] == 14
    assert payload["manifest"]["manifest_digest"]
    assert [mode["mode"] for mode in payload["options"]["modes"]] == list(EXPECTED_MODES)
