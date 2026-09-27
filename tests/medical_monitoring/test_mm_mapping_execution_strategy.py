"""C2·B路线执行策略保证面回归（钉住行为，改断言须先改行为并注明理由）。

钉住的契约与理由：
① off回归：无开关（或未知值）时 `_submit_harness` 必须与改动前的原路径
   `submit_listing_field_mapping_chunks` 直调逐字段一致（作业数/business_key/
   chunk_size/prompt_version）——C1接缝的唯一合法性来源就是off路径零变化。
② proposed只存proposed：B产物只经既有 monitoring_ai_candidates(status=proposed)
   落库（monitoring_ai_service.py 候选构造处 status=PROPOSED），候选层决定只有
   accepted/rejected；不存在任何B→confirmed提升路径，confirm_draft 的未决问题门
   （mapping_questions_unresolved）与双对账门（mapping_reconciliation_required）
   仍在 confirm 之前（mapping_confirmation.py confirm_draft）。
③ 诚实审计：B模型作业 classify_tool_usage 必为 tool_loop_executed/idle（按实际
   回执数，不按版本名）；确定性作业登记有工具合同但零读取=tool_loop_idle；
   scripts/monitoring_mapping_tool_usage_audit.py 通过登记处泛化分类，对v20
   零专门逻辑，且每行携带 evidence_read_rows 供核查。
④ 重启语义钉为特性：v20/v2不在启动现役集（main.py 派发集/恢复集）也不在
   legacy_terminal集（mapping_pipeline.MAPPING_ADJUDICATION_LEGACY_TERMINAL_
   PROMPT_VERSIONS）⇒启动 supersede_prompt_versions_except 的保留子句（仅保护
   legacy集内 completed/failed）不覆盖任一B版本⇒B全部作业（模型+确定性、含
   completed/queued）重启即翻STALE_INPUT、候选翻SUPERSEDED。D2对照以『即刻导出』
   对冲该语义——这是设计行为，不是缺陷。
⑤ 投影连贯（N2+N5）：on态下attempt前缀下每个作业（单元与确定性）payload
   field_profile 都含 full_profile_sha256，且全部作业 prompt_version==本cohort
   B版——_latest_job_cohort（selectable排除workbench-system取最新模型作业版本、
   第一道AND为版本等式、workbench-system例外在第三条件内）对全部B作业可见。
"""
from __future__ import annotations

import inspect
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
    _unresolved_question_count,
)
from packages.medical_monitoring.admission.mapping_execution_strategy import (
    SEMANTIC_EVIDENCE_PROMPT_VERSIONS,
    SEMANTIC_EVIDENCE_STRATEGY,
    STRATEGY_DOMAINS_ENV,
    STRATEGY_EXECUTION_ENV,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
    MONITORING_MAPPING_COHORT_PRIMARY,
    MONITORING_MAPPING_COHORT_VERIFIER,
    monitoring_mapping_cohort_contract,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS,
    AdmissionMappingPipeline,
    _latest_job_cohort,
)
from packages.medical_monitoring.admission.evidence_tool_contract import (
    classify_tool_usage,
)
from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiCandidateStatus,
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    PROMPT_VERSION_BY_TASK,
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from services.api.app.monitoring_evidence_tool_loop import TOOL_REQUEST_SCHEMA

PRIMARY_B_VERSION = SEMANTIC_EVIDENCE_PROMPT_VERSIONS[MONITORING_MAPPING_COHORT_PRIMARY]
VERIFIER_B_VERSION = SEMANTIC_EVIDENCE_PROMPT_VERSIONS[MONITORING_MAPPING_COHORT_VERIFIER]
SOURCE_HASH = "a" * 64


class MutableClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 9, 27, 4, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._value

    def advance(self, **kwargs: int) -> None:
        self._value += timedelta(**kwargs)


class FakeProvider:
    provider_name = "test-provider"
    model_name = "test-model"
    expected_response_model = "test-model"
    transport_name = "openai_compatible"

    def __init__(self, builders):
        self.builders = list(builders)
        self.envelopes: List[Any] = []

    def run(self, envelope):
        self.envelopes.append(envelope)
        index = min(len(self.envelopes) - 1, len(self.builders) - 1)
        return self.builders[index](envelope)


def _valid_mapping_output(envelope) -> Dict[str, Any]:
    """单次调用即合法的 listing_field_mapping_set 输出（覆盖作业全部字段）。"""
    original_payload = envelope.payload.get("input_payload")
    if original_payload is None:
        original_payload = envelope.payload["original_task"]["input_payload"]
    source = envelope.payload["authorized_source_pairs"][0]
    fields = original_payload["field_profile"]["fields"]
    evidence = []
    field_mappings = []
    for index, field in enumerate(fields, start=1):
        evidence_id = f"evidence-{index}"
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_entry_id": source["source_entry_id"],
                "source_content_sha256": source["source_content_sha256"],
                "locator": f"profile://{field['domain']}/{field['field']}",
                "quote": "",
                "raw_fields": {
                    "domain": field["domain"],
                    "field": field["field"],
                    "inferred_type": field["inferred_type"],
                },
            }
        )
        field_mappings.append(
            {
                "domain": field["domain"],
                "source_field": field["field"],
                "recommended_role": "lab_result_candidate",
                "field_kind": "source_collected",
                "confidence": 0.82,
                "uncertainty": "仍需核对单位和参考范围字段。",
                "user_action": "请医学经理确认字段角色。",
                "user_decision_required": False,
                "related_fields": [],
                "evidence_ids": [evidence_id],
            }
        )
    candidates = [
        {
            "candidate_type": "listing_field_mapping_set",
            "title": "完整字段语义映射候选",
            "text": "完整覆盖冻结批次字段画像，供医学经理确认。",
            "structured_payload": {"field_mappings": field_mappings},
            "claims": [
                {
                    "claim_id": "claim-mapping-set",
                    "kind": "recommendation",
                    "text": "字段角色仍需结合项目数据字典确认。",
                    "confidence": 0.82,
                    "uncertainty": "当前仅使用完整字段画像。",
                    "user_action": "请逐项确认或修订。",
                    "evidence_ids": [evidence[0]["evidence_id"]],
                }
            ],
            "evidence": evidence,
        }
    ]
    return {
        "schema_version": MONITORING_AI_SCHEMA_VERSION,
        "task_id": envelope.task_id,
        "task_type": "listing_field_mapping",
        "input_revision_sha256": (
            envelope.payload.get("input_revision_sha256")
            or envelope.payload["original_task"]["input_revision_sha256"]
        ),
        "candidates": candidates,
    }


def _tool_request_output(envelope) -> Dict[str, Any]:
    return {
        "schema_version": TOOL_REQUEST_SCHEMA,
        "task_id": envelope.task_id,
        "input_revision_sha256": envelope.payload["input_revision_sha256"],
        "tool_requests": [
            {
                "request_id": "read-1",
                "name": "read_source_region",
                "arguments": {"row_start": 0},
            }
        ],
    }


@contextmanager
def _fake_tool_factory(job, payload):
    def execute(name, arguments):
        return {
            "input_revision_sha256": job.input_revision_sha256,
            "coverage": "partial",
            "cells": [{"raw_value": 0}],
        }

    yield SimpleNamespace(schemas={"read_source_region": {}}, execute=execute)


def _runtime(env: Dict[str, str]) -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id="independent-ai-test",
        provider="test-provider",
        model="test-model",
        env={
            "WORKBENCH_AI_PROVIDER": "test-provider",
            "WORKBENCH_AI_TRANSPORT": "openai_compatible",
            "WORKBENCH_AI_BASE_URL": "https://example.invalid/v1",
            "WORKBENCH_AI_API_KEY": "test-key",
            "WORKBENCH_AI_MODEL": "test-model",
            "WORKBENCH_AI_EXPECTED_RESPONSE_MODEL": "test-model",
            "WORKBENCH_AI_DEPLOYMENT_PROFILE": "local_private_clinical",
            "WORKBENCH_AI_OUTPUT_TOKEN_BUDGET": "65536",
            **env,
        },
    )


def _sample_profile() -> Dict[str, Any]:
    """CM(6元数据+14业务)+MH(3元数据+12业务链)：与C1冒烟同构的小样本。"""
    def make_field(domain: str, name: str) -> Dict[str, Any]:
        # 字段画像键与真实bridge一致（解析层按 inferred_type 构建证据）。
        return {
            "domain": domain,
            "field": name,
            "source_label": name,
            "total_rows": 120,
            "non_empty_count": 110,
            "null_rate": 0.0833,
            "inferred_type": "string",
            "unique_value_count": 25,
            "top_values": [],
            "representative_values": [f"{domain}-{name}-value"],
            "anomaly_examples": [],
        }

    cm_meta = ["USUBJID", "VISIT", "VISITNUM", "FORMOID", "FORMNM", "__FORMREPEATKEY"]
    mh_meta = ["USUBJID", "VISIT", "FORMNM"]
    comp_a = ["CMTRT", "CMDOS", "CMDOSU", "CMDOSFRQ", "CMROUTE", "CMSTDTC", "CMENDTC"]
    comp_b = ["CMINDC", "CMDOSEADJ"]
    isolated = ["CMSTDY", "CMENDY", "CMDUR", "CMTIMES", "CMDECOD"]
    mh_chain = [f"MHFIELD{i:02d}" for i in range(1, 13)]
    cm_fields = [make_field("CM", n) for n in cm_meta + comp_a + comp_b + isolated]
    mh_fields = [make_field("MH", n) for n in mh_meta + mh_chain]
    relationships = []
    for pair, rtype in (
        (["CMTRT", "CMDOS"], "value_unit_pair"),
        (["CMDOS", "CMDOSU"], "value_unit_pair"),
        (["CMDOSU", "CMDOSFRQ"], "statistical_pair"),
        (["CMDOSFRQ", "CMROUTE"], "statistical_pair"),
        (["CMROUTE", "CMSTDTC"], "statistical_pair"),
        (["CMSTDTC", "CMENDTC"], "statistical_pair"),
        (["CMINDC", "CMDOSEADJ"], "performed_reason_pair"),
    ):
        left, right = pair
        relationships.append({
            "domain": "CM", "left_field": left, "right_field": right,
            "relationship_type": rtype,
            "total_rows": 10, "jointly_non_empty_count": 8,
            "left_only_count": 1, "right_only_count": 1, "unique_pair_count": 6,
            "left_values_with_multiple_right": 0,
            "right_values_with_multiple_left": 0,
        })
    for left, right in zip(mh_chain, mh_chain[1:]):
        relationships.append({
            "domain": "MH", "left_field": left, "right_field": right,
            "relationship_type": "statistical_pair",
            "total_rows": 10, "jointly_non_empty_count": 8,
            "left_only_count": 1, "right_only_count": 1, "unique_pair_count": 6,
            "left_values_with_multiple_right": 0,
            "right_values_with_multiple_left": 0,
        })
    return {
        "schema_version": "monitoring_ai_field_profile_v3",
        "batch_id": "stg-20260927-c2",
        "project_id": "project-alpha",
        "batch_revision": 1,
        "mapping_revision": None,
        "expected_domains": ["CM", "MH"],
        "source_bindings": [
            {"source_entry_id": "source-listing", "source_content_sha256": SOURCE_HASH}
        ],
        "source_sha256s": [SOURCE_HASH],
        "row_count": 120,
        "input_sha256": "b" * 64,
        "fields": cm_fields + mh_fields,
        "relationships": relationships,
        "table_bindings": [
            {
                "table_binding_id": "mmtable-" + domain,
                "domain": domain,
                "source_file": f"{domain}.xlsx",
                "source_revision_id": "source-listing",
                "snapshot_id": "snap-1",
                "sheet_index": 1,
            }
            for domain in ("CM", "MH")
        ],
        "table_field_order": [
            {"domain": "CM", "field_order": [f["field"] for f in cm_fields]},
            {"domain": "MH", "field_order": [f["field"] for f in mh_fields]},
        ],
        "input_completeness": {"manifest_sha256": "c" * 64},
        "document_evidence": {},
        "payload_policy": "bounded_full_column_statistics",
        "profile_sha256": "d" * 64,
    }


def _input_revision() -> MonitoringAiInputRevision:
    return MonitoringAiInputRevision.model_validate({
        "project_id": "project-alpha",
        "batch_revision": "stg-20260927-c2",
        "mapping_revision": "mapping-001",
        "sources": [
            {"source_entry_id": "source-listing", "source_content_sha256": SOURCE_HASH}
        ],
    })


class Harness:
    """一个临时库 + 可选策略env的主/盲核双服务 + 接缝驱动器。"""

    def __init__(self, tmp_path: Path, name: str, env: Dict[str, str]) -> None:
        self.clock = MutableClock()
        self.db_path = tmp_path / f"{name}.sqlite3"
        self.repository = MonitoringAiRepository(self.db_path, clock=self.clock)
        self.profile = _sample_profile()
        self.env = dict(env)
        self.primary = self._build_service()
        self.verifier = self._build_service()

    def _build_service(self) -> MonitoringAiService:
        provider = FakeProvider([_valid_mapping_output])
        return MonitoringAiService(
            self.repository,
            runtime_resolver=lambda: _runtime(self.env),
            provider_factory=lambda _env: provider,
            current_revision_resolver=None,
            evidence_tool_factory=_fake_tool_factory,
        )

    def _service_for(self, cohort: str) -> MonitoringAiService:
        return (
            self.primary
            if cohort == MONITORING_MAPPING_COHORT_PRIMARY
            else self.verifier
        )

    def submit(self, cohort: str) -> tuple:
        service = self._service_for(cohort)
        pipeline = AdmissionMappingPipeline(
            ai_service=service,
            ai_repository=self.repository,
            input_revision_factory=MonitoringAiInputRevision.model_validate,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        )
        harness = SimpleNamespace(
            field_profile=self.profile,
            input_revision=_input_revision(),
        )
        jobs = pipeline._submit_harness(
            service,
            monitoring_mapping_cohort_contract(cohort),
            harness,
            project_id="project-alpha",
        )
        return tuple(jobs)

    def drain(self, service: MonitoringAiService) -> None:
        while True:
            result = service.run_next("worker-c2")
            if not result.processed:
                return


def job_payload_profile(repository: Any, job: Any) -> Dict[str, Any]:
    return repository.input_payload(job.project_id, job.job_id)["field_profile"]


# ---------------------------------------------------------------------------
# ① off回归：无开关时接缝返回与现行为逐字段一致
# ---------------------------------------------------------------------------

def _assert_a_route_shape(jobs, repository: Any) -> None:
    """A路线（改动前行为）形状：CM 20字段2片+MH 15字段2片，主侧默认v19。

    pinned理由：这是C1接缝之前就已存在的提交形状，off必须原样保留。
    """
    assert len(jobs) == 4
    keys = sorted(job.business_key for job in jobs)
    assert keys == sorted([
        "listing-field-mapping:stg-20260927-c2:CM:0001-of-0002",
        "listing-field-mapping:stg-20260927-c2:CM:0002-of-0002",
        "listing-field-mapping:stg-20260927-c2:MH:0001-of-0002",
        "listing-field-mapping:stg-20260927-c2:MH:0002-of-0002",
    ])
    # 主侧cohort合同prompt为空 ⇒ 服务默认v19是现行权威（monitoring_ai_service）。
    assert {job.prompt_version for job in jobs} == {
        PROMPT_VERSION_BY_TASK[MonitoringAiTaskType.LISTING_FIELD_MAPPING]
    }
    for job in jobs:
        profile = job_payload_profile(repository, job)
        assert profile["chunk_size_limit"] == 12


def test_off_seam_matches_direct_chunks_call(tmp_path: Path) -> None:
    harness = Harness(tmp_path, "off-primary", env={})
    pipeline = AdmissionMappingPipeline(
        ai_service=harness.primary,
        ai_repository=harness.repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    harness_input = SimpleNamespace(
        field_profile=harness.profile, input_revision=_input_revision(),
    )
    contract = monitoring_mapping_cohort_contract(MONITORING_MAPPING_COHORT_PRIMARY)
    jobs = pipeline._submit_harness(
        harness.primary, contract, harness_input, project_id="project-alpha",
    )
    _assert_a_route_shape(tuple(jobs), harness.repository)
    # 参照：C1改动前的原语句直调（全新库，同输入）必须得到相同提交。
    reference = Harness(tmp_path, "off-primary-ref", env={})
    reference_jobs = reference.primary.submit_listing_field_mapping_chunks(
        project_id="project-alpha",
        input_revision=_input_revision(),
        field_profile=reference.profile,
        chunk_size=12,
        prompt_version=contract.prompt_version,
        business_key_prefix=contract.business_key_prefix,
    )
    assert sorted(j.business_key for j in jobs) == sorted(
        j.business_key for j in reference_jobs
    )
    assert sorted(j.job_id for j in jobs) == sorted(j.job_id for j in reference_jobs)


def test_off_unknown_strategy_value_unchanged(tmp_path: Path) -> None:
    harness = Harness(tmp_path, "off-bogus", env={STRATEGY_EXECUTION_ENV: "bogus-x"})
    pipeline = AdmissionMappingPipeline(
        ai_service=harness.primary,
        ai_repository=harness.repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    jobs = pipeline._submit_harness(
        harness.primary,
        monitoring_mapping_cohort_contract(MONITORING_MAPPING_COHORT_PRIMARY),
        SimpleNamespace(field_profile=harness.profile, input_revision=_input_revision()),
        project_id="project-alpha",
    )
    _assert_a_route_shape(tuple(jobs), harness.repository)


# ---------------------------------------------------------------------------
# ② proposed只存proposed：B产物无confirmed提升路径
# ---------------------------------------------------------------------------

def test_b_outputs_stay_proposed_and_confirm_gates_stand(tmp_path: Path) -> None:
    harness = Harness(
        tmp_path, "proposed",
        env={STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY},
    )
    jobs = harness.submit(MONITORING_MAPPING_COHORT_PRIMARY)
    harness.drain(harness.primary)
    for job in jobs:
        completed = harness.repository.get(job.project_id, job.job_id)
        assert completed.status == MonitoringAiJobStatus.COMPLETED
        rows = harness.repository.candidates(job.project_id, job.job_id)
        # B产物（模型+确定性）只以proposed落库；confirmed不是候选状态。
        assert rows
        assert all(c.status == MonitoringAiCandidateStatus.PROPOSED for c in rows)
    # 候选层不存在confirmed决定：decide_candidate只接受accepted/rejected。
    assert not hasattr(MonitoringAiCandidateStatus, "CONFIRMED")
    with pytest.raises(ValueError):
        harness.repository.decide_candidate(
            "project-alpha",
            "moncand_nonexistent",
            decision=MonitoringAiCandidateStatus.PROPOSED,
            actor="tester",
            reason="试图重复决定",
            current_input_revision_sha256="0" * 64,
        )
    # 双门仍在confirm之前（mapping_confirmation.confirm_draft）。
    source = inspect.getsource(AdmissionMappingConfirmationService.confirm_draft)
    questions_gate = source.index("mapping_questions_unresolved")
    reconciliation_gate = source.index("mapping_reconciliation_required")
    confirm_call = source.index("self.mapping_repository.confirm(")
    assert questions_gate < confirm_call
    assert reconciliation_gate < confirm_call
    # 未决问题门按 user_decision_required 计数，B候选的未决项照样拦截。
    assert _unresolved_question_count(
        [{"user_decision_required": True, "user_action": "需要裁决"}]
    ) == 1
    assert _unresolved_question_count([{"user_decision_required": False}]) == 0
    # B路径本身（策略模块与接缝）不含任何confirm入口。
    import packages.medical_monitoring.admission.mapping_execution_strategy as strategy_module

    assert "confirm" not in inspect.getsource(strategy_module).casefold()
    pipeline_methods = [
        name for name in dir(AdmissionMappingPipeline) if name.startswith("confirm")
    ]
    assert pipeline_methods == []


# ---------------------------------------------------------------------------
# ③ 诚实审计：按实际回执分类；审计脚本对v20零专门逻辑
# ---------------------------------------------------------------------------

def test_b_model_job_tool_usage_is_honest(tmp_path: Path) -> None:
    # 单回执变体：provider先请求一次工具读取 ⇒ tool_loop_executed。
    executed_harness = Harness(
        tmp_path, "executed",
        env={
            STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY,
            STRATEGY_DOMAINS_ENV: "MH",  # 1单元+1确定性，规模最小
        },
    )
    provider = FakeProvider([_tool_request_output, _valid_mapping_output])
    executed_harness.primary.provider_factory = lambda _env: provider
    jobs = executed_harness.submit(MONITORING_MAPPING_COHORT_PRIMARY)
    executed_harness.drain(executed_harness.primary)
    model_jobs = [j for j in jobs if j.provider != "workbench-system"]
    det_jobs = [j for j in jobs if j.provider == "workbench-system"]
    assert len(model_jobs) == 1 and len(det_jobs) == 1
    completed = executed_harness.repository.get(
        model_jobs[0].project_id, model_jobs[0].job_id,
    )
    assert completed.status == MonitoringAiJobStatus.COMPLETED
    reads = executed_harness.repository.evidence_reads(
        model_jobs[0].project_id, model_jobs[0].job_id,
    )
    assert len(reads) == 1
    assert classify_tool_usage(completed.prompt_version, len(reads)) == (
        "tool_loop_executed"
    )
    # 确定性作业：登记有工具合同（v20）但零读取 ⇒ tool_loop_idle（非executed）。
    det = executed_harness.repository.get(det_jobs[0].project_id, det_jobs[0].job_id)
    assert det.status == MonitoringAiJobStatus.COMPLETED
    assert det.prompt_version == PRIMARY_B_VERSION
    assert classify_tool_usage(det.prompt_version, 0) == "tool_loop_idle"

    # 零回执变体：provider单次合法输出 ⇒ tool_loop_idle。
    idle_harness = Harness(
        tmp_path, "idle",
        env={
            STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY,
            STRATEGY_DOMAINS_ENV: "MH",
        },
    )
    idle_jobs = idle_harness.submit(MONITORING_MAPPING_COHORT_PRIMARY)
    idle_harness.drain(idle_harness.primary)
    idle_model = [j for j in idle_jobs if j.provider != "workbench-system"][0]
    completed_idle = idle_harness.repository.get(
        idle_model.project_id, idle_model.job_id,
    )
    assert completed_idle.status == MonitoringAiJobStatus.COMPLETED
    assert idle_harness.repository.evidence_reads(
        idle_model.project_id, idle_model.job_id,
    ) == ()
    assert classify_tool_usage(completed_idle.prompt_version, 0) == "tool_loop_idle"


def test_audit_script_classifies_b_jobs_without_v20_logic(tmp_path: Path) -> None:
    from scripts.monitoring_mapping_tool_usage_audit import classify_persisted_jobs

    harness = Harness(
        tmp_path, "audit",
        env={STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY},
    )
    jobs = harness.submit(MONITORING_MAPPING_COHORT_PRIMARY)
    harness.drain(harness.primary)
    report = classify_persisted_jobs(harness.db_path)
    assert report["total_jobs"] == len(jobs)
    rows = {item["job_id"]: item for item in report["rows"]}
    for job in jobs:
        row = rows[job.job_id]
        reads = len(harness.repository.evidence_reads(job.project_id, job.job_id))
        # 每行携带实际回执数（分类证据本身），class与逐作业合同×回执一致。
        assert row["evidence_read_rows"] == reads
        assert row["class"] == classify_tool_usage(job.prompt_version, reads)
        assert row["class"] in {"tool_loop_executed", "tool_loop_idle"}
    # 审计脚本靠登记处泛化分类：源码不含任何v20专门分支。
    script_source = (
        Path(__file__).resolve().parents[2]
        / "scripts" / "monitoring_mapping_tool_usage_audit.py"
    ).read_text(encoding="utf-8")
    assert "monitoring-listing-field-mapping-v20" not in script_source
    assert "verifier-v2-tools-v1" not in script_source


# ---------------------------------------------------------------------------
# ④ 重启语义钉为特性：B全部作业重启即STALE_INPUT、候选SUPERSEDED
# ---------------------------------------------------------------------------

def test_restart_supersession_retires_all_b_jobs(tmp_path: Path) -> None:
    # 派发集/恢复现役集/legacy保留集都不含B版本（main.py:1390-1395、:1712-1748；
    # mapping_pipeline legacy集）——这是B作业重启翻stale的直接前提。
    from services.api.app.main import MONITORING_MAPPING_DISPATCH_PROMPT_VERSIONS

    assert PRIMARY_B_VERSION not in MONITORING_MAPPING_DISPATCH_PROMPT_VERSIONS
    assert VERIFIER_B_VERSION not in MONITORING_MAPPING_DISPATCH_PROMPT_VERSIONS
    recovery_current = (
        {PROMPT_VERSION_BY_TASK[MonitoringAiTaskType.LISTING_FIELD_MAPPING]}
        | {MONITORING_C3_VERIFIER_PROMPT_VERSION}
        | MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS
    )
    assert PRIMARY_B_VERSION not in recovery_current
    assert VERIFIER_B_VERSION not in recovery_current
    assert PRIMARY_B_VERSION not in MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS
    assert VERIFIER_B_VERSION not in MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS

    # 双cohort共用一个库（生产即如此），白名单MH：每cohort 1单元+1确定性。
    harness = Harness(
        tmp_path, "restart",
        env={
            STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY,
            STRATEGY_DOMAINS_ENV: "MH",
        },
    )
    primary_jobs = harness.submit(MONITORING_MAPPING_COHORT_PRIMARY)
    verifier_jobs = harness.submit(MONITORING_MAPPING_COHORT_VERIFIER)
    b_jobs = list(primary_jobs) + list(verifier_jobs)
    assert {j.prompt_version for j in b_jobs} == {
        PRIMARY_B_VERSION, VERIFIER_B_VERSION,
    }
    harness.drain(harness.primary)
    harness.drain(harness.verifier)
    # 全部完成（含确定性workbench-system），候选proposed——重启前状态。
    for job in b_jobs:
        assert harness.repository.get(job.project_id, job.job_id).status == (
            MonitoringAiJobStatus.COMPLETED
        )
        assert harness.repository.candidates(job.project_id, job.job_id)
    # 现行v19排队作业作为对照：现役集覆盖它，清扫不翻stale。
    v19_jobs = harness.primary.submit_listing_field_mapping_chunks(
        project_id="project-alpha",
        input_revision=_input_revision(),
        field_profile=harness.profile,
        chunk_size=12,
        prompt_version="",
        business_key_prefix=(
            f"listing-field-mapping:{harness.profile['batch_id']}:legacyprobe"
        ),
    )
    # 精确复刻 main.py `_recover_monitoring_ai_jobs` 对LISTING_FIELD_MAPPING的
    # 启动清扫调用（现役集与legacy保留集同源）。
    retired = harness.repository.supersede_prompt_versions_except(
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        current_prompt_version=PROMPT_VERSION_BY_TASK[
            MonitoringAiTaskType.LISTING_FIELD_MAPPING
        ],
        additional_current_prompt_versions=(
            recovery_current
            - {PROMPT_VERSION_BY_TASK[MonitoringAiTaskType.LISTING_FIELD_MAPPING]}
        ),
        legacy_terminal_prompt_versions=(
            MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS
        ),
    )
    assert retired == len(b_jobs)
    for job in b_jobs:
        row = harness.repository.get(job.project_id, job.job_id)
        # 保留子句只保护legacy集内completed/failed；B版本一个都不在集内，
        # completed的模型/确定性作业同样翻STALE_INPUT（设计语义，D2即刻导出对冲）。
        assert row.status == MonitoringAiJobStatus.STALE_INPUT
        assert row.contract_retirement_code == "superseded_prompt_contract"
        assert row.retryable is False
        for candidate in harness.repository.candidates(job.project_id, job.job_id):
            assert candidate.status == MonitoringAiCandidateStatus.SUPERSEDED
    # 对照：现役v19排队作业不受清扫影响。
    for v19_job in v19_jobs:
        kept = harness.repository.get(v19_job.project_id, v19_job.job_id)
        assert kept.status == MonitoringAiJobStatus.QUEUED
        assert kept.contract_retirement_code == ""


# ---------------------------------------------------------------------------
# ⑤ 投影连贯：全作业同代B版 + 全含full_profile_sha256 ⇒ _latest_job_cohort全可见
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cohort,b_version", [
    (MONITORING_MAPPING_COHORT_PRIMARY, PRIMARY_B_VERSION),
    (MONITORING_MAPPING_COHORT_VERIFIER, VERIFIER_B_VERSION),
])
def test_b_projection_cohort_coherent(tmp_path: Path, cohort: str, b_version: str) -> None:
    harness = Harness(
        tmp_path, f"projection-{cohort}",
        env={STRATEGY_EXECUTION_ENV: SEMANTIC_EVIDENCE_STRATEGY},
    )
    jobs = harness.submit(cohort)
    assert len(jobs) == 10  # CM 7单元+MH 1单元 + CM/MH各1确定性
    full_sha = harness.profile["profile_sha256"]
    model_jobs = [j for j in jobs if j.provider != "workbench-system"]
    det_jobs = [j for j in jobs if j.provider == "workbench-system"]
    assert len(model_jobs) == 8 and len(det_jobs) == 2
    for job in jobs:
        # N5：全部作业（模型+确定性）与cohort B版同代。
        assert job.prompt_version == b_version
        # N2：全部作业payload都含full_profile_sha256且同源（确定性单发显式补键）。
        profile = job_payload_profile(harness.repository, job)
        assert profile["full_profile_sha256"] == full_sha
    # _latest_job_cohort：cohort_prompt取最新模型作业版本（selectable排除
    # workbench-system），第一道AND为版本等式——B全作业同代+同源 ⇒ 全可见。
    projection = _latest_job_cohort(jobs, repository=harness.repository)
    assert len(projection) == len(jobs)
    assert {j.job_id for j in projection} == {j.job_id for j in jobs}
    assert any(j.provider == "workbench-system" for j in projection)
