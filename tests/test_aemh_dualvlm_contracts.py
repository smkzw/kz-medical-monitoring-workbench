"""WP0B回归：双VLM裁决/定向核实的身份与状态合同（审阅D-01/D-02/D-03）。

- 稳定finding_id：同一线索跨重跑身份不变；不同受试者/侧别不同。
- adjudicate(artifacts_dir=None)：纯内存评估，零落盘副作用。
- merge_focused_verifications四态：confirmed/refuted/insufficient_evidence
  与执行状态（missing/failed/timed_out/no_candidates）严格区分；技术缺口
  不写成"请医学监察员裁决"式医学反证措辞。
- submit_focused_verifications：finding_id关联（无zip/位置索引）、版本化
  focused合同标记、跳项原因持久化。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (  # noqa: E402
    FOCUSED_CONTRACT_VERSION,
    adjudicate,
    merge_focused_verifications,
    submit_focused_verifications,
)


def _candidate(
    candidate_id: str,
    title: str,
    text: str,
    *,
    evidence_ids: tuple[str, ...] = ("ev-ae-1", "ev-mh-1"),
    domains: tuple[str, ...] = ("AE", "MH"),
    claims: list[dict[str, Any]] | None = None,
) -> SimpleNamespace:
    payload_claims = claims if claims is not None else [
        {"claim_id": "c1", "kind": "inference", "text": text, "evidence_ids": list(evidence_ids)}
    ]
    return SimpleNamespace(
        candidate_id=candidate_id,
        title=title,
        text=text,
        evidence=tuple(
            SimpleNamespace(evidence_id=eid) for eid in evidence_ids
        ),
        structured_payload={
            "domains": list(domains),
            "claims": payload_claims,
        },
    )


@dataclass
class FakeRepository:
    jobs: dict[str, Any] = field(default_factory=dict)
    candidates_by_job: dict[str, list] = field(default_factory=dict)

    def get(self, project_id: str, job_id: str):
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    def candidates(self, project_id: str, job_id: str):
        return tuple(self.candidates_by_job.get(job_id, ()))


def _completed_job(job_id: str) -> SimpleNamespace:
    return SimpleNamespace(status="completed")


def test_adjudicate_dry_run_writes_no_artifacts(tmp_path: Path) -> None:
    repo = FakeRepository(
        jobs={"p1": _completed_job("p1"), "v1": _completed_job("v1")},
        candidates_by_job={
            "p1": [_candidate("c-p1", "血压记录矛盾", "主分析发现血压记录矛盾")],
            "v1": [_candidate("c-v1", "血压记录矛盾", "盲核同样发现血压记录矛盾")],
        },
    )
    art = adjudicate(
        ai_repository=repo,
        project_id="proj-test",
        subject_labels=["01001"],
        facts_snapshot_ref="facts-test",
        primary_job_by_subject={"01001": "p1"},
        verifier_job_by_subject={"01001": "v1"},
        artifacts_dir=None,
    )
    assert art["counts"]["accepted"] == 1
    assert list(tmp_path.iterdir()) == []  # 零落盘


def test_finding_ids_stable_and_distinct() -> None:
    # 盲核侧完成但只给出无关线索（不共享证据、无共同实体词）→
    # 主侧线索为单侧escalated。
    repo = FakeRepository(
        jobs={"p1": _completed_job("p1"), "v1": _completed_job("v1")},
        candidates_by_job={
            "p1": [_candidate("c-p1", "线索A", "主侧单方线索A")],
            "v1": [
                _candidate(
                    "c-v9",
                    "其他观察",
                    "盲核发现了完全另一件事",
                    evidence_ids=(),
                    domains=("CM",),
                )
            ],
        },
    )
    art = adjudicate(
        ai_repository=repo,
        project_id="proj-test",
        subject_labels=["01001"],
        facts_snapshot_ref="facts-test",
        primary_job_by_subject={"01001": "p1"},
        verifier_job_by_subject={"01001": "v1"},
        artifacts_dir=None,
    )
    escalated = [f for f in art["findings"] if f["state"] == "escalated"]
    assert len(escalated) == 2  # 主侧与盲核侧各产生一条单侧线索
    finding_id = next(
        f["finding_id"] for f in escalated if "-primary-" in f["finding_id"]
    )

    # 同样的线索在第二次裁决中身份不变
    art2 = adjudicate(
        ai_repository=repo,
        project_id="proj-test",
        subject_labels=["01001"],
        facts_snapshot_ref="facts-test",
        primary_job_by_subject={"01001": "p1"},
        verifier_job_by_subject={"01001": "v1"},
        artifacts_dir=None,
    )
    assert art2["findings"][0]["finding_id"] == finding_id

    # 不同受试者/侧别的线索身份不同
    repo2 = FakeRepository(
        jobs={"p2": _completed_job("p2")},
        candidates_by_job={"p2": [_candidate("c-p2", "线索A", "主侧单方线索A")]},
    )
    art3 = adjudicate(
        ai_repository=repo2,
        project_id="proj-test",
        subject_labels=["01002"],
        facts_snapshot_ref="facts-test",
        primary_job_by_subject={"01002": "p2"},
        verifier_job_by_subject={},
        artifacts_dir=None,
    )
    assert art3["findings"][0]["finding_id"] != finding_id


def test_merge_four_states_with_technical_wording() -> None:
    clue_view = {
        "subject_label": "01001",
        "finding_id": "fid-1",
        "state": "escalated",
        "primary": {
            "title": "线索A",
            "text": "主侧单方线索A：存在异常需关注",
            "domains": ["AE"],
            "payload": {
                "claims": [
                    {"text": "主侧单方线索A：存在异常需关注", "evidence_ids": ["ev-ae-1"]}
                ]
            },
        },
        "verifier": None,
    }

    def _repo_with(job_status: str, candidates: list) -> FakeRepository:
        return FakeRepository(
            jobs={"fv-1": SimpleNamespace(status=job_status)},
            candidates_by_job={"fv-1": candidates},
        )

    def _run(repo: FakeRepository, jobs: dict, timed_out: set[str] | None = None):
        findings = [dict(clue_view)]
        return merge_focused_verifications(
            ai_repository=repo,
            project_id="proj-test",
            findings=findings,
            focused_job_by_finding_id=jobs,
            wait_timed_out_ids=timed_out or set(),
        )[0]

    # confirmed：对侧一致候选 → accepted
    # V5-06：确认要求双侧立场都明确正向——fixture补方向词
    # （旧fixture"对侧确认线索A"无方向词，收紧后为escalated属预期）。
    confirmed_repo = _repo_with(
        "completed",
        [_candidate("fv-c1", "线索A", "对侧确认：存在线索A所述异常，需关注")],
    )
    item = _run(confirmed_repo, {"fid-1": "fv-1"})
    assert item["state"] == "accepted"
    assert item["verification_execution"] == "confirmed"

    # refuted：data_gap反证 → escalated+refuted（真分歧，请用户裁决）
    refuted_repo = _repo_with(
        "completed",
        [
            _candidate(
                "fv-g1",
                "证据缺口",
                "该观察与原始记录不一致",
                claims=[{"claim_id": "g1", "kind": "data_gap", "text": "缺口"}],
            )
        ],
    )
    item = _run(refuted_repo, {"fid-1": "fv-1"})
    assert item["state"] == "escalated"
    assert item["verification_execution"] == "refuted"
    assert "裁决" in item["reason_zh"]

    # insufficient：有候选但既未确认也未反证（不共享证据、无共同实体词）
    insufficient_repo = _repo_with(
        "completed",
        [
            _candidate(
                "fv-x1",
                "无关发现",
                "对侧描述了另一件事",
                evidence_ids=(),
            )
        ],
    )
    item = _run(insufficient_repo, {"fid-1": "fv-1"})
    assert item["state"] == "escalated"
    assert item["verification_execution"] == "insufficient_evidence"

    # 作业failed → 技术状态措辞，不得出现"裁决"
    item = _run(_repo_with("failed", []), {"fid-1": "fv-1"})
    assert item["state"] == "escalated"
    assert item["verification_execution"] == "verification_failed"
    assert "裁决" not in item["reason_zh"]

    # 等待超时 → 技术状态
    item = _run(_repo_with("running", []), {"fid-1": "fv-1"}, timed_out={"fid-1"})
    assert item["verification_execution"] == "verification_timed_out"
    assert "裁决" not in item["reason_zh"]

    # 作业缺失 → 技术状态
    item = _run(_repo_with("completed", []), {})
    assert item["verification_execution"] == "verification_missing"
    assert "裁决" not in item["reason_zh"]

    # 完成但零候选 → 技术状态
    item = _run(_repo_with("completed", []), {"fid-1": "fv-1"})
    assert item["verification_execution"] == "verification_no_candidates"
    assert "裁决" not in item["reason_zh"]


def test_submit_focused_keys_by_finding_id_and_records_skips(
    monkeypatch,
) -> None:
    from packages.medical_monitoring.analysis import ae_mh_cross_analysis as aemh

    def _fake_evidence(domains, subject_label):
        evidence = [
            {
                "evidence_id": "ev-ae-1",
                "evidence_kind": "original_data",
                "locator": f"{subject_label}:AE:r1",
                "raw_fields": {"domain": "AE", "term": "样本"},
            }
        ]
        digest = (
            "a" * 56 + f"{abs(hash(subject_label)) % 10 ** 8:08d}"
        )
        return evidence, {"AE": digest}

    monkeypatch.setattr(aemh, "build_subject_evidence", _fake_evidence)

    captured: list[dict[str, Any]] = []

    @dataclass
    class FakeJob:
        job_id: str

    class FakeService:
        def submit_task(self, **kwargs):
            captured.append(kwargs)
            return FakeJob(f"job-{len(captured)}")

    escalated = [
        {
            "subject_label": "01001",
            "finding_id": "fid-ok",
            "primary": {"title": "线索A", "text": "内容A"},
            "verifier": None,
        },
        {
            "subject_label": "01002",
            "finding_id": "",
            "primary": {"title": "缺id", "text": "内容"},
            "verifier": None,
        },
        {
            "subject_label": "",
            "finding_id": "fid-bad-subject",
            "primary": {"title": "空受试者", "text": "内容"},
            "verifier": None,
        },
    ]
    submission = submit_focused_verifications(
        verifier_service=FakeService(),
        project_id="proj-test",
        domains={},
        escalated=escalated,
        facts_snapshot_ref="facts-fv-test",
    )
    # 只有可提交的条目产生作业，且以finding_id为键
    assert set(submission.job_by_finding_id) == {"fid-ok"}
    assert captured[0]["business_key"].endswith("fid-ok")
    # 跳项原因持久化
    reasons = {s["finding_id"]: s["reason"] for s in submission.skipped}
    assert reasons[""] == "missing_finding_id"
    assert reasons["fid-bad-subject"] == "empty_subject_or_clue"
    # 版本化focused合同注入payload
    contract = captured[0]["input_payload"]["subject_context"]["focused_contract"]
    assert contract["version"] == FOCUSED_CONTRACT_VERSION
    assert contract["expected_candidates"] == 1
    assert json.dumps(contract)  # JSON可序列化


def test_clues_agree_rejects_opposite_direction_on_same_evidence():
    """N5命题核验：同一证据+相反方向≠一致（审阅V4关键缺陷）。"""
    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        _clues_agree,
    )

    class E:
        def __init__(self, eid):
            self.evidence_id = eid

    class Clue:
        def __init__(self, title, text, eids, domains=("AE", "CM")):
            self.title = title
            self.text = text
            self.evidence = tuple(E(eid) for eid in eids)
            self.structured_payload = {
                "domains": list(domains),
                "claims": [{"text": text, "evidence_ids": list(eids)}],
            }

    shared = ["ev-001", "ev-002"]
    # 正方向：主分析认为存在不一致
    positive = Clue("CM指征与AE记录不一致", "合并用药指征为本研究疾病，但AE记录为否，提示可能存在AE漏报", shared)
    # 负方向：盲核认为记录一致，无问题
    negative = Clue("CM与AE记录一致", "合并用药与AE记录未见明显不一致，数据相符", shared)

    assert not _clues_agree(positive, negative), "相反命题不应判一致"

    # 同方向+同证据 = 一致
    affirmative = Clue("CM指征与AE可能不匹配", "CM指征提示本研究疾病但AE未记录，存在漏报可能", shared)
    assert _clues_agree(positive, affirmative), "同方向同证据应判一致"

    # V5-06修订（行为依据：词频方向不能当确认依据）：neutral=无法判定
    # 方向，不得作为确认基础——保守升级为可见分歧交人工/定向核实。
    neutral = Clue("两记录涉及同一受试者", "两条记录引用同一受试者编号", shared)
    assert not _clues_agree(positive, neutral), (
        "neutral方向不得确认（V5-06）"
    )
