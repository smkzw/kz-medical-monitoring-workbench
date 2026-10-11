"""R32-03/R32-04回归：识别失败分片的逐表暴露与显式重跑。

R32实测（ISO sqlite只读诊断，proj_user_9610ef8760c3/MY008 59表）：
265个识别分片 ``queue_dwell_timeout`` 终态失败且 attempt_count=0
（容量型滞留收割，从未被认领），LB域全部沦陷——LB表只剩确定性规则
命中的 VISTREP 1个字段（R32-03），而界面只笼统说「部分识别任务已终
态失败」，无失败表清单、无原因、无重跑入口（R32-04，report_B.md
发现2/3）。本回归覆盖：
1. 业务键→(表,分片)解析；
2. 公开投影按表聚合失败清单（无作业身份泄漏）；
3. pipeline.retry_failed_candidates：显式重排终态失败分片（重置滞留
   基线的 retry_terminal 语义）、按表过滤、三类跳过（合同退役/输入
   漂移/状态冲突）与worker唤醒。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from packages.medical_monitoring.admission.mapping_pipeline import (
    _chunk_business_identity,
    AdmissionMappingPipeline,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    _public_mapping_projection,
    _public_table_failures,
)


def test_chunk_business_identity_parses_table_and_chunk() -> None:
    assert _chunk_business_identity(
        "listing-field-mapping-verifier:stg-abc:LB9:0002-of-0003"
    ) == ("LB9", "0002", "0003")
    assert _chunk_business_identity(
        "listing-field-mapping:adm-1:DS--退出研究:0001-of-0004"
    ) == ("DS--退出研究", "0001", "0004")
    assert _chunk_business_identity("garbage") == ("", "", "")


def test_public_table_failures_groups_by_table_without_job_identity() -> None:
    jobs = [
        {
            "job_id": "job-1",
            "business_key": "listing-field-mapping:a1:LB9:0001-of-0003",
            "table_name": "LB9",
            "chunk_index": "0001",
            "status": "failed",
            "failure_code": "queue_dwell_timeout",
            "failure_message": "滞留收割",
            "attempt_count": 0,
            "max_attempts": 2,
            "provider": "deepseek",
        },
        {
            "job_id": "job-2",
            "table_name": "LB9",
            "chunk_index": "0002",
            "status": "failed",
            "failure_code": "queue_dwell_timeout",
            "failure_message": "滞留收割",
            "attempt_count": 0,
            "max_attempts": 2,
        },
        {
            "job_id": "job-3",
            "table_name": "DS1",
            "chunk_index": "0001",
            "status": "completed",
            "failure_code": "",
            "failure_message": "",
            "attempt_count": 1,
            "max_attempts": 2,
        },
    ]
    failures = _public_table_failures(jobs)
    assert [item["table_name"] for item in failures] == ["LB9"]
    assert failures[0]["failed_chunks"] == 2
    assert failures[0]["failure_codes"] == ["queue_dwell_timeout"]
    assert [chunk["chunk_index"] for chunk in failures[0]["chunks"]] == [
        "0001",
        "0002",
    ]
    blob = repr(failures)
    assert "job_id" not in blob and "job-1" not in blob
    assert "deepseek" not in blob


def test_public_mapping_projection_carries_table_failures() -> None:
    payload = {
        "state": "needs_attention",
        "summary": {"job_count": 3, "completed_job_count": 1},
        "candidates": [],
        "jobs": [
            {
                "job_id": "job-1",
                "table_name": "LB9",
                "chunk_index": "0001",
                "status": "failed",
                "failure_code": "queue_dwell_timeout",
                "failure_message": "",
                "attempt_count": 0,
                "max_attempts": 2,
            },
        ],
    }
    public = _public_mapping_projection(payload)
    assert public["state"] == "needs_attention"
    assert public["table_failures"][0]["table_name"] == "LB9"


@dataclass
class _Job:
    job_id: str
    business_key: str
    status: str
    input_revision_sha256: str
    attempt_count: int = 0
    max_attempts: int = 2
    contract_retirement_code: str = ""
    provider: str = "deepseek"
    requested_model: str = "m"
    response_model: str = "m"
    failure_code: str = ""
    failure_message: str = ""
    project_id: str = "proj-r32"


@dataclass
class _Repo:
    jobs: list = field(default_factory=list)
    retried: list = field(default_factory=list)
    conflict_ids: set = field(default_factory=set)

    def list_jobs(self, project_id, *, task_type, business_key_prefix):
        return [
            job for job in self.jobs
            if job.business_key.startswith(business_key_prefix)
        ]

    def retry_terminal(self, project_id, job_id, *, current_input_revision_sha256):
        if job_id in self.conflict_ids:
            from services.api.app.monitoring_ai_repository import (
                MonitoringAiStateConflictError,
            )
            raise MonitoringAiStateConflictError("conflict")
        self.retried.append(job_id)
        for job in self.jobs:
            if job.job_id == job_id:
                job.status = "queued"
        return job


@dataclass
class _Service:
    revision: str = "rev-1"

    def current_revision_resolver(self, job):
        return self.revision


class _Pipeline(AdmissionMappingPipeline):
    def __init__(self, repository, service, woken):  # noqa: D107 - test stub
        self._repository = repository
        self._service = service
        self._woken = woken
        self._task_type = "listing_field_mapping"
        self._worker_wake = self._wake

    def _wake(self):
        self._woken.append(True)

    def _cohort_contract(self, cohort):
        from packages.medical_monitoring.admission.mapping_gate import (
            monitoring_mapping_cohort_contract,
        )
        return monitoring_mapping_cohort_contract(cohort)

    def _cohort_service(self, cohort):
        return self._service

    def _configured(self, service):
        return True

    def _load_record(self, *, project_id, attempt_id, workspace_dir):
        return None


def test_retry_failed_candidates_requeues_and_wakes() -> None:
    repo = _Repo(jobs=[
        _Job("job-lb9-1", "listing-field-mapping:a1:LB9:0001-of-0003", "failed", "rev-1"),
        _Job("job-lb9-2", "listing-field-mapping:a1:LB9:0002-of-0003", "failed", "rev-1"),
        _Job("job-ds1-1", "listing-field-mapping:a1:DS1:0001-of-0002", "failed", "rev-1"),
        _Job("job-ok-1", "listing-field-mapping:a1:DS1:0002-of-0002", "completed", "rev-1"),
    ])
    woken: list = []
    pipeline = _Pipeline(repo, _Service(), woken)

    result = pipeline.retry_failed_candidates(
        project_id="proj-r32",
        attempt_id="a1",
        workspace_dir=None,
    )
    assert result["requeued_count"] == 3
    assert result["skipped_count"] == 0
    assert sorted(repo.retried) == ["job-ds1-1", "job-lb9-1", "job-lb9-2"]
    assert woken == [True]


def test_retry_failed_candidates_table_filter_and_skips() -> None:
    repo = _Repo(jobs=[
        _Job("job-lb9-1", "listing-field-mapping:a1:LB9:0001-of-0003", "failed", "rev-1"),
        _Job("job-lb9-2", "listing-field-mapping:a1:LB9:0002-of-0003", "failed", "rev-old"),
        _Job(
            "job-lb9-3",
            "listing-field-mapping:a1:LB9:0003-of-0003",
            "failed",
            "rev-1",
            contract_retirement_code="legacy_prompt",
        ),
        _Job("job-ds1-1", "listing-field-mapping:a1:DS1:0001-of-0002", "failed", "rev-1"),
    ])
    repo.conflict_ids.add("job-ds1-1")
    woken: list = []
    pipeline = _Pipeline(repo, _Service(), woken)

    result = pipeline.retry_failed_candidates(
        project_id="proj-r32",
        attempt_id="a1",
        workspace_dir=None,
        table_name="LB9",
    )
    assert [item["job_id"] for item in result["requeued"]] == ["job-lb9-1"]
    assert result["requeued_count"] == 1
    reasons = {item["job_id"]: item["reason"] for item in result["skipped"]}
    assert reasons == {
        "job-lb9-2": "input_revision_changed",
        "job-lb9-3": "contract_retired",
    }
    # 按表过滤+全部跳过冲突：DS1不在请求范围，无重排则不唤醒。
    assert repo.retried == ["job-lb9-1"]
    assert woken == [True]
