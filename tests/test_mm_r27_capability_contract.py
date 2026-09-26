"""R27-01能力合同回归：登记处收口、可达性预检、启动闭包、诚实分类。

钉住的行为与理由：
- mapping提示词版本→工具能力的映射唯一收口在
  packages/medical_monitoring/admission/evidence_tool_contract.py；
  能力以登记表为准，不按版本名tools-vN后缀声称。
- 首轮盲核（verifier-v8-tools-v6）与主侧默认（v19）的实际执行路径是
  单次provider调用，必须如实登记为无工具（空功能集），历史302作业
  不得被描述为已做自主取证。
- 带工具合同的提交要求本部署能兑现该合同；不可达时在提交点显式
  失败（旧行为是入队后运行期才崩溃，本文件一并钉住新边界）。
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission import evidence_tool_contract as contract
from packages.medical_monitoring.admission.evidence_tool_contract import (
    DEPENDENCY_MAPPING_PROMPT_VERSIONS,
    EVIDENCE_TOOL_PROMPT_VERSIONS,
    ROLE_EQUIVALENCE_PROMPT_VERSIONS,
    STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS,
    VISUAL_MAPPING_PROMPT_VERSIONS,
    assert_prompt_version_reachable,
    check_prompt_version_tool_closure,
    classify_tool_usage,
    prompt_version_features,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    MAPPING_ADJUDICATION_PROMPT_VERSION,
    MAPPING_ADJUDICATION_VERIFIER_PROMPT_VERSION,
)
from services.api.app.monitoring_evidence_tool_loop import (
    TOOL_REQUEST_SCHEMA,
    _validate_requests,
)
from services.api.app.monitoring_ai_service import (
    MonitoringAiTaskType,
    PROMPT_VERSION_BY_TASK,
)
from tests.test_monitoring_ai_service import (
    FakeProvider,
    _field_profile,
    _revision,
    _service,
)

PRIMARY_FIRST_ROUND = PROMPT_VERSION_BY_TASK[
    MonitoringAiTaskType.LISTING_FIELD_MAPPING
]
VERIFIER_FIRST_ROUND = MONITORING_C3_VERIFIER_PROMPT_VERSION


def test_first_round_defaults_are_registered_as_no_tools() -> None:
    """首轮默认版本必须显式登记且登记为无工具：后缀不构成能力声称。"""
    for version in (PRIMARY_FIRST_ROUND, VERIFIER_FIRST_ROUND):
        assert version in {
            "monitoring-listing-field-mapping-v19",
            "monitoring-listing-field-mapping-verifier-v8-tools-v6",
        }
        assert prompt_version_features(version) == frozenset()
        assert version not in EVIDENCE_TOOL_PROMPT_VERSIONS
        assert classify_tool_usage(version, 0) == "single_call"
    # 裁决lane关闭工具读开关时的遗留派发身份同样如实登记为无工具。
    for version in (
        MAPPING_ADJUDICATION_PROMPT_VERSION,
        MAPPING_ADJUDICATION_VERIFIER_PROMPT_VERSION,
    ):
        assert prompt_version_features(version) == frozenset()
        assert version not in EVIDENCE_TOOL_PROMPT_VERSIONS


def test_no_tool_registration_grants_nothing_in_any_derived_set() -> None:
    """无工具登记行不得泄漏进任何派生能力集合（v19/verifier-v8等）。"""
    derived = {
        "evidence_tool": EVIDENCE_TOOL_PROMPT_VERSIONS,
        "dependency": DEPENDENCY_MAPPING_PROMPT_VERSIONS,
        "visual": VISUAL_MAPPING_PROMPT_VERSIONS,
        "role_eq": ROLE_EQUIVALENCE_PROMPT_VERSIONS,
        "strict": STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS,
    }
    for version, features in contract._PROMPT_VERSION_FEATURES.items():
        if not features:
            for name, versions in derived.items():
                assert version not in versions, (version, name)


def test_registered_tool_versions_keep_their_tool_contract() -> None:
    """已登记的tool-enabled版本不受无工具登记影响（旧行为钉住）。"""
    for version in (
        "monitoring-listing-field-mapping-v20-tools-v1",
        "monitoring-listing-field-mapping-verifier-v2-tools-v1",
        *MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    ):
        assert "evidence_tool" in prompt_version_features(version)
        assert version in EVIDENCE_TOOL_PROMPT_VERSIONS
    assert len(EVIDENCE_TOOL_PROMPT_VERSIONS) == 34


def test_current_dispatch_set_passes_startup_closure() -> None:
    check_prompt_version_tool_closure({
        PRIMARY_FIRST_ROUND,
        VERIFIER_FIRST_ROUND,
        *MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    })


def test_startup_closure_rejects_unregistered_dispatch_version() -> None:
    with pytest.raises(ValueError, match="not registered"):
        check_prompt_version_tool_closure({
            PRIMARY_FIRST_ROUND,
            "monitoring-listing-field-mapping-v99-unregistered",
        })


def test_startup_closure_rejects_unknown_feature_and_layer_drift() -> None:
    saved = dict(contract._PROMPT_VERSION_FEATURES)
    try:
        contract._PROMPT_VERSION_FEATURES["monitoring-listing-field-mapping-v40"] = (
            frozenset({"evidance_tool"})  # 拼写漂移：功能键未知
        )
        with pytest.raises(ValueError, match="unknown feature keys"):
            check_prompt_version_tool_closure()
        contract._PROMPT_VERSION_FEATURES["monitoring-listing-field-mapping-v41"] = (
            frozenset({"visual"})  # 层叠违约：visual缺dependency/evidence_tool
        )
        with pytest.raises(ValueError, match="layered features missing"):
            check_prompt_version_tool_closure()
    finally:
        contract._PROMPT_VERSION_FEATURES.clear()
        contract._PROMPT_VERSION_FEATURES.update(saved)


def test_claimed_tools_resolve_through_real_toolset_and_loop(tmp_path) -> None:
    """每个登记为evidence_tool的版本，其声称的工具都能经真实工具集与
    工具循环的请求校验解析（R27-01启动闭包的运行期口径）。"""
    from packages.medical_monitoring.admission.pipeline import DataAdmissionPipeline
    from packages.medical_monitoring.admission.source_tools import FrozenListingEvidenceTools
    from packages.medical_monitoring.graph.store import Store
    from packages.medical_monitoring.runtime.runtime_progress import (
        RUNTIME_DIR_NAME, RUNTIME_DB_NAME, ARTIFACT_DIR_NAME,
    )
    from services.api.app.monitoring_evidence_toolset import MonitoringEvidenceToolset

    source = tmp_path / "synthetic-source"
    source.mkdir()
    (source / "listing.csv").write_text("synthetic fixture")
    rows = [{"A": index, "B": [None, 0, -1, "<5", "mg/L"][index % 5]} for index in range(45)]

    def parser(*_):
        return [{"table_name": "Observations", "headers": ["A", "B"],
                 "rows": rows, "row_numbers": list(range(4, 49))}]

    workspace = tmp_path / "workspace"
    record = DataAdmissionPipeline(parser).create_attempt(
        project_id="tool-study", source_dir=source, workspace_dir=workspace)
    technical = record["technical_details"]
    binding = {"table_binding_id": "table-one", "domain": "Observations",
               "snapshot_id": technical["snapshot_ids"][0],
               "source_revision_id": technical["revision_ids"][0], "sheet_index": 1}
    profile = {"project_id": "tool-study", "table_bindings": [binding],
               "source_bindings": [{"source_entry_id": binding["source_revision_id"],
                                    "source_content_sha256": technical["files"][0]["sha256"]}]}
    store = Store(workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
                  workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME)
    try:
        reader = FrozenListingEvidenceTools(
            store, project_id="tool-study", input_revision="f" * 64,
            field_profile=profile,
        )
        toolkit = MonitoringEvidenceToolset(reader)
        base_arguments = {
            "sample_rows": {"table_binding_id": "table-one", "filter_column_index": 0,
                            "raw_value": 0, "column_indexes": [0]},
            "read_source_region": {"table_binding_id": "table-one",
                                   "column_indexes": [0]},
            "get_column_profile": {"table_binding_id": "table-one",
                                   "column_index": 0},
        }
        for version in sorted(EVIDENCE_TOOL_PROMPT_VERSIONS):
            assert base_arguments.keys() <= toolkit.schemas.keys()
            for name, arguments in base_arguments.items():
                request = {"schema_version": TOOL_REQUEST_SCHEMA,
                           "task_id": "task-1",
                           "input_revision_sha256": "f" * 64,
                           "tool_requests": [{"request_id": "req-1",
                                              "name": name,
                                              "arguments": arguments}]}
                parsed = _validate_requests(request, "task-1", "f" * 64,
                                            toolkit.schemas, set())
                assert parsed[0]["name"] == name
        # 无document_evidence时，视觉声称版本的可用工具退为基础三件——
        # 这是可用性降级，不是合同授予（visual合同工具需绑定文档才出现）。
        assert set(toolkit.schemas) == set(base_arguments)
    finally:
        store.close()


def test_submit_precheck_rejects_unregistered_version(tmp_path) -> None:
    """未登记的mapping版本在提交点拒收（收口到唯一登记处）。"""
    service = _service(tmp_path, FakeProvider([]))
    with pytest.raises(ValueError, match="not registered in evidence_tool_contract"):
        service.submit_listing_field_mapping(
            project_id="project-alpha",
            input_revision=_revision(),
            field_profile=_field_profile(field_count=1),
            prompt_version="monitoring-listing-field-mapping-v99-unregistered",
        )


def test_submit_precheck_rejects_unreachable_tool_contract(tmp_path) -> None:
    """声称取证工具而工具集不可达：提交点显式失败，不再入队后崩溃。"""
    service = _service(tmp_path, FakeProvider([]))
    with pytest.raises(ValueError, match="evidence toolset is not configured"):
        service.submit_listing_field_mapping(
            project_id="project-alpha",
            input_revision=_revision(),
            field_profile=_field_profile(field_count=1),
            prompt_version="monitoring-listing-field-mapping-v20-tools-v1",
        )

    @contextmanager
    def factory(*_args):
        yield SimpleNamespace(schemas={}, execute=lambda *_: None)

    service.evidence_tool_factory = factory
    job = service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=_field_profile(field_count=1),
        prompt_version="monitoring-listing-field-mapping-v20-tools-v1",
    )
    assert job.prompt_version == "monitoring-listing-field-mapping-v20-tools-v1"


def test_no_tool_versions_still_submit_without_toolset(tmp_path) -> None:
    """无工具合同（首轮v19/盲核v8）提交不需要任何工具设施。"""
    service = _service(tmp_path, FakeProvider([]))
    for version in (PRIMARY_FIRST_ROUND, VERIFIER_FIRST_ROUND):
        job = service.submit_listing_field_mapping(
            project_id="project-alpha",
            input_revision=_revision(),
            field_profile=_field_profile(field_count=1),
            prompt_version=version,
        )
        assert job.prompt_version == version


def test_classify_tool_usage_honest_classes() -> None:
    tool_version = "monitoring-listing-field-mapping-adjudication-v19-tools-v7.2"
    assert classify_tool_usage(tool_version, 3) == "tool_loop_executed"
    assert classify_tool_usage(tool_version, 0) == "tool_loop_idle"
    assert classify_tool_usage(PRIMARY_FIRST_ROUND, 0) == "single_call"
    assert classify_tool_usage(PRIMARY_FIRST_ROUND, 2) == (
        "receipts_without_tool_contract"
    )
    assert classify_tool_usage("never-registered", 0) == "unregistered"


def test_tool_usage_audit_script_classifies_persisted_jobs(tmp_path) -> None:
    """审计脚本按「登记合同×实际回执」分类，不按版本名（端到端）。"""
    from scripts.monitoring_mapping_tool_usage_audit import classify_persisted_jobs

    db = tmp_path / "monitoring-ai.sqlite3"
    conn = sqlite3.connect(db)
    try:
        conn.executescript(
            """
            CREATE TABLE monitoring_ai_jobs (
                job_id TEXT PRIMARY KEY, task_type TEXT, prompt_version TEXT,
                status TEXT);
            CREATE TABLE monitoring_ai_evidence_reads (
                read_id INTEGER PRIMARY KEY, job_id TEXT);
            INSERT INTO monitoring_ai_jobs VALUES
                ('j1', 'listing_field_mapping',
                 'monitoring-listing-field-mapping-v19', 'completed'),
                ('j2', 'listing_field_mapping',
                 'monitoring-listing-field-mapping-verifier-v8-tools-v6', 'completed'),
                ('j3', 'listing_field_mapping',
                 'monitoring-listing-field-mapping-adjudication-v19-tools-v7.2',
                 'completed');
            INSERT INTO monitoring_ai_evidence_reads (job_id) VALUES
                ('j3'), ('j3');
            """
        )
        conn.commit()
    finally:
        conn.close()
    report = classify_persisted_jobs(db)
    assert report["total_jobs"] == 3
    assert report["by_class"] == {
        "single_call": 2,
        "tool_loop_executed": 1,
    }
    rows = {item["prompt_version"]: item for item in report["rows"]}
    assert rows["monitoring-listing-field-mapping-verifier-v8-tools-v6"][
        "class"] == "single_call"
    assert rows["monitoring-listing-field-mapping-verifier-v8-tools-v6"][
        "evidence_read_rows"] == 0
