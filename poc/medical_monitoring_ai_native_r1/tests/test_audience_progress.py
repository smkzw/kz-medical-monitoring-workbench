"""Audience progress projection tests; synthetic/offline only."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from mm_r1.audience_progress import AudienceProgressError, project_audience_progress
from mm_r1.domain import (
    ExecutionBasis,
    ExecutionManifest,
    ManifestNode,
    ManifestWorkUnit,
    MonitoringRun,
    NodeStatus,
    NodeType,
    RunMode,
    SourceRevision,
    WorkUnitRun,
    content_hash,
)


def _prepare_run(
    store,
    *,
    unsafe_label: str = "",
    unsafe_target: str = "",
    unsafe_scope: str = "",
) -> ExecutionManifest:
    store.create_project("project-audience", "合成医学监查项目")
    store.add_source_revision(
        SourceRevision(
            revision_id="source-audience",
            project_id="project-audience",
            source_type="listing",
            version="synthetic-v1",
            content_hash=content_hash({"synthetic": True}),
        )
    )
    store.create_run(
        MonitoringRun(
            run_id="run-audience",
            project_id="project-audience",
            mode=RunMode.DAILY,
            data_cutoff="2026-08-09",
            source_revision_id="source-audience",
            execution_basis=ExecutionBasis.FULL,
        )
    )
    labels = (
        unsafe_label or "整理受试者 S001 访视数据",
        "分析受试者 S001 AE 风险",
        "核查受试者 S001 既往病史",
        "核查受试者 S001 合并用药",
        "核查受试者 S001 研究药物给药",
        "核查受试者 S001 入排标准",
        "核查受试者 S001 禁用药使用",
        "汇总受试者 S001 医学监查结果",
    )
    stages = (
        "数据解构",
        "风险分析",
        "风险分析",
        "风险分析",
        "方案符合性",
        "方案符合性",
        "方案符合性",
        "结果汇总",
    )
    units = [
        ManifestWorkUnit(
            work_unit_id=f"audience-{index}",
            node_id="monitor",
            label=label,
            stage=stages[index - 1],
            scope=(
                unsafe_scope
                if index == 1 and unsafe_scope
                else ("risk_domain" if index > 1 else "subject")
            ),
            target_ref=(
                unsafe_target
                if index == 1 and unsafe_target
                else (f"S001/{index}" if index > 1 else "S001")
            ),
            ordinal=index,
        )
        for index, label in enumerate(labels, start=1)
    ]
    manifest = ExecutionManifest(
        run_id="run-audience",
        nodes=[ManifestNode("monitor", NodeType.DETERMINISTIC_SERVICE)],
        work_units=units,
        graph_version="synthetic-audience-v1",
        schema_version="synthetic-schema-v1",
    )
    store.set_manifest(manifest)
    return manifest


class _ReadOnlyStore:
    def __init__(self, manifest, rows, source):
        self.manifest = manifest
        self.rows = rows
        self.source = source

    def structured_progress(self, run_id, feed_limit=20):
        assert run_id == "run-audience"
        assert feed_limit == 20
        return self.source

    def get_manifest(self, run_id, revision):
        assert (run_id, revision) == ("run-audience", 1)
        return self.manifest

    def list_work_unit_runs(self, run_id, revision):
        assert (run_id, revision) == ("run-audience", 1)
        return self.rows


def test_projection_conserves_all_statuses_without_runtime_leak(r1_store) -> None:
    manifest = _prepare_run(r1_store)
    states = (
        NodeStatus.PENDING,
        NodeStatus.RUNNING,
        NodeStatus.PASSED,
        NodeStatus.REUSED,
        NodeStatus.SKIPPED,
        NodeStatus.NOT_APPLICABLE,
        NodeStatus.BLOCKED,
        NodeStatus.FAILED,
    )
    for unit, state in zip(manifest.work_units, states):
        if state == NodeStatus.PENDING:
            continue
        r1_store.begin_work_unit(
            "run-audience",
            unit.work_unit_id,
            f"begin-{unit.ordinal}",
            "provider=synthetic model=fixture attempt=internal 正在执行",
            {
                "provider": "synthetic-provider",
                "model": "fixture-model",
                "attempt_id": f"attempt-{unit.ordinal}",
            },
        )
        if state != NodeStatus.RUNNING:
            r1_store.complete_work_unit(
                "run-audience",
                unit.work_unit_id,
                f"begin-{unit.ordinal}",
                state,
                "backend raw_log node_id=monitor 内部完成详情",
            )

    view = project_audience_progress(r1_store, "run-audience")

    assert view["completed"] == 6
    assert view["total"] == 8
    assert view["percent"] == 75.0
    assert view["progress_text"] == "已处理 6/8 项（75%）"
    assert view["headline"] == "医学监查进行中"
    assert [item["state_label"] for item in view["status_overview"]] == [
        "等待开始",
        "进行中",
        "已完成",
        "已沿用已有结果",
        "本次无需处理",
        "本研究不适用",
        "暂时受阻",
        "未完成",
    ]
    assert view["stage_progress"] == [
        {
            "stage": "数据解构",
            "processed": 0,
            "total": 1,
            "progress_text": "已处理 0/1 项",
        },
        {
            "stage": "风险分析",
            "processed": 2,
            "total": 3,
            "progress_text": "已处理 2/3 项",
        },
        {
            "stage": "方案符合性",
            "processed": 3,
            "total": 3,
            "progress_text": "已处理 3/3 项",
        },
        {
            "stage": "结果汇总",
            "processed": 1,
            "total": 1,
            "progress_text": "已处理 1/1 项",
        },
    ]
    assert view["current_work"][0]["label"] == "分析受试者 S001 AE 风险"
    assert view["current_work"][0]["message"] == "正在进行：分析受试者 S001 AE 风险"
    assert (
        view["latest_updates"][-1]["message"] == "未完成：汇总受试者 S001 医学监查结果"
    )

    serialized = json.dumps(view, ensure_ascii=False).casefold()
    for forbidden in (
        "provider",
        "model",
        "attempt",
        "backend",
        "node_id",
        "run_id",
        "work_unit",
        "event_type",
        "raw_log",
        "execution_identity",
        "正式事实",
        "候选信号",
        "只读",
        "日志",
    ):
        assert forbidden not in serialized


def _retry_projection_contract():
    unit = ManifestWorkUnit(
        work_unit_id="risk-S001-AE",
        node_id="risk",
        label="分析受试者 S001 AE 风险",
        stage="风险分析",
        scope="risk_domain",
        target_ref="S001/AE",
        ordinal=1,
    )
    manifest = ExecutionManifest(
        run_id="run-audience",
        nodes=[ManifestNode("risk", NodeType.AI_CANDIDATE)],
        work_units=[unit],
        revision=1,
    )
    row = WorkUnitRun(
        run_id="run-audience",
        manifest_revision=1,
        work_unit_id=unit.work_unit_id,
        node_id=unit.node_id,
        status=NodeStatus.RUNNING,
    )
    source = {
        "manifest_revision": 1,
        "is_current_revision": True,
        "completed": 0,
        "total": 1,
        "percent": 0.0,
        "by_status": {"running": 1},
        "running": [
            {
                "work_unit_id": unit.work_unit_id,
                "elapsed_seconds": 90,
                "execution_identity": {
                    "provider": "synthetic-provider",
                    "attempt_id": "attempt-risk-2",
                },
                "detail": "second attempt using backend",
            }
        ],
        "feed": [
            {
                "work_unit_id": unit.work_unit_id,
                "status": "running",
                "event_type": "work_unit_attempt_bound",
                "created_at": "2026-08-09T12:30:00+00:00",
                "attempt_ordinal": 2,
                "continued_from": "attempt-risk-1",
            }
        ],
    }

    return manifest, row, source


def test_retry_is_rendered_as_continue_without_attempt_identity() -> None:
    manifest, row, source = _retry_projection_contract()

    view = project_audience_progress(
        _ReadOnlyStore(manifest, [row], source), "run-audience"
    )
    assert view["latest_updates"] == [
        {
            "time_text": "08月09日 20:30",
            "stage": "风险分析",
            "label": "分析受试者 S001 AE 风险",
            "state_label": "进行中",
            "message": "正在继续处理：分析受试者 S001 AE 风险",
        }
    ]
    assert view["current_work"][0]["elapsed_text"] == "已进行 1 分钟"
    serialized = json.dumps(view, ensure_ascii=False).casefold()
    assert "attempt" not in serialized
    assert "provider" not in serialized
    assert "backend" not in serialized


def test_retry_event_with_non_running_status_fails_closed() -> None:
    manifest, row, source = _retry_projection_contract()
    source["feed"][0]["status"] = "failed"
    with pytest.raises(AudienceProgressError, match="继续处理动态状态"):
        project_audience_progress(
            _ReadOnlyStore(manifest, [row], source), "run-audience"
        )


def test_duplicate_running_work_record_fails_closed() -> None:
    manifest, row, source = _retry_projection_contract()
    source["running"].append(dict(source["running"][0]))
    with pytest.raises(AudienceProgressError, match="当前工作记录重复"):
        project_audience_progress(
            _ReadOnlyStore(manifest, [row], source), "run-audience"
        )


@pytest.mark.parametrize(
    "unsafe_label",
    (
        "provider=synthetic 正在分析 AE",
        "查看正式事实",
        "打开只读风险投影",
        "处理 attempt-risk-1",
        "读取 /Users/example/private.csv",
        "医学 provider_id=synthetic",
        "医学 backend_url=127.0.0.1:8911",
        "医学 hash=abc123",
        "医学 tel:+8613800138000",
        "医学 urn:example:clinical",
        "医学 about:blank",
        "医学 custom-scheme:value",
        "医学 x:opaque",
        "医学 X:opaque",
        "医学 TEL:+8613800138000",
        "医学 ABOUT:blank",
        "医学localhost:8911",
        "医学127.0.0.1:8911",
        "医学example.com:8080",
        "医学 SRC/MM_R1",
        "医学/tmp/private",
        "医学 folder/subdir",
    ),
)
def test_unsafe_manifest_label_fails_closed(r1_store, unsafe_label: str) -> None:
    _prepare_run(r1_store, unsafe_label=unsafe_label)
    with pytest.raises(AudienceProgressError):
        project_audience_progress(r1_store, "run-audience")


@pytest.mark.parametrize(
    "unsafe_target",
    (
        "/tmp/private.csv",
        "ssh://127.0.0.1:8911/medical",
        "hash=abc123",
        "node",
        "data/private.csv",
        "127.0.0.1:8911",
        "mailto:user@example.com",
        "data:text/plain,hello",
        "src/mm_r1",
        "foo/bar",
        "foo.csv?x=1",
        "foo.csv#frag",
        "foo.exe",
        "foo.tmp",
        "[::1]:8080",
        "::1",
        "2001:db8::1",
        "example.com:8080",
        "SRC/MM_R1",
        "DATA/PRIVATE",
        "FOO/BAR",
        "A/B",
        "SRC/CONFIG",
        "README/SETUP",
        "R1/POC",
        "受试者 S001 urn:example:clinical",
        "受试者 S001 custom-scheme:value",
        "受试者 S001 x:opaque",
        "SRC/受试者 S001",
        "README/受试者 S001",
        "受试者 S001/CONFIG",
    ),
)
def test_unsafe_target_fails_closed(r1_store, unsafe_target: str) -> None:
    _prepare_run(r1_store, unsafe_target=unsafe_target)
    with pytest.raises(AudienceProgressError):
        project_audience_progress(r1_store, "run-audience")


@pytest.mark.parametrize(
    "clinical_target",
    (
        "S001/AE",
        "MG-K10",
        "SITE01",
        "001-001",
        "01/PD",
        "受试者 S001",
        "受试者 S001/AE",
    ),
)
def test_clinical_target_formats_remain_visible(r1_store, clinical_target: str) -> None:
    _prepare_run(r1_store, unsafe_target=clinical_target)
    view = project_audience_progress(r1_store, "run-audience")
    assert view["total"] == 8


def test_clinical_abbreviation_punctuation_remains_visible(r1_store) -> None:
    manifest = _prepare_run(r1_store)
    manifest.work_units[0] = replace(
        manifest.work_units[0],
        label="核查 AE/MH 记录与 ALT:轻度升高",
    )
    r1_store.set_manifest(manifest)
    view = project_audience_progress(r1_store, "run-audience")
    assert view["total"] == 8


def test_unknown_scope_cannot_skip_target_validation(r1_store) -> None:
    _prepare_run(
        r1_store,
        unsafe_scope="unclassified_scope",
        unsafe_target="/tmp/private.csv",
    )
    with pytest.raises(AudienceProgressError, match="工作范围类型"):
        project_audience_progress(r1_store, "run-audience")


def test_non_chinese_stage_fails_closed(r1_store) -> None:
    manifest = _prepare_run(r1_store)
    manifest.work_units[0] = replace(manifest.work_units[0], stage="risk analysis")
    r1_store.set_manifest(manifest)
    with pytest.raises(AudienceProgressError, match="中文医学监查表达"):
        project_audience_progress(r1_store, "run-audience")


def test_internal_stage_fails_closed(r1_store) -> None:
    manifest = _prepare_run(r1_store)
    manifest.work_units[0] = replace(
        manifest.work_units[0], stage="医学 provider_id=synthetic"
    )
    r1_store.set_manifest(manifest)
    with pytest.raises(AudienceProgressError, match="内部执行标识"):
        project_audience_progress(r1_store, "run-audience")
