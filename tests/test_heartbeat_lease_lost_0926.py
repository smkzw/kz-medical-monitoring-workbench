"""W02-E0b（20260926）：失租约传播——heartbeat_error消费点。

验收锚点 R26-A30（review_pack_0926V1/kz_review_0926V1/04_ACCEPTANCE_0926V1.json）：
后台心跳失败后停止后续工具/候选提交；仍保留已经发生调用的真实账。

- 失租反例：stub repository的heartbeat在首次续租后抛失租冲突→
  _run_with_heartbeat以MonitoringAiHeartbeatLeaseLostError终止（携带
  job_id/owner），provider输出不返回、不会被上层消费；record_call仍写入
  本次物理调用的真实账（outcome=success：调用本身成功了，被丢弃是失租
  传播的结果）；
- 正常路径回归：无失租时输出照常返回、记账outcome=success；
- provider异常路径回归：run抛错照常传播、记账outcome=provider_error。

该失败反例已在修改前HEAD 872a451复现：当时heartbeat_error仅写入从不
读取，失租后函数照常返回provider输出（probe输出RETURNED OUTPUT）。
repository侧owner+到期CAS是第二道防线，本切片不动其行为。
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from services.api.app.monitoring_ai_repository import (
    MonitoringAiStateConflictError,
)
from services.api.app.monitoring_ai_service import (
    MonitoringAiService,
)

LEASE_SECONDS = 0.75  # interval = max(0.25, min(30, 0.75/3)) = 0.25s


class StubRepository:
    """heartbeat首次成功、其后失租冲突的存根；record_call照收真实账。"""

    lease_seconds = LEASE_SECONDS

    def __init__(self, *, fail_heartbeat: bool = True):
        self.heartbeats = 0
        self.calls: list[dict] = []
        self.fail_heartbeat = fail_heartbeat

    def heartbeat(self, project_id, job_id, owner):
        self.heartbeats += 1
        if self.fail_heartbeat and self.heartbeats > 1:
            raise MonitoringAiStateConflictError(
                "monitoring AI heartbeat lost lease"
            )

    def record_call(self, **kwargs):
        self.calls.append(kwargs)


class StubProvider:
    response_model = "model-x"
    response_diagnostics = {"wire": "stub"}

    def __init__(self, *, run_seconds: float = 0.0, error: Exception | None = None):
        self._run_seconds = run_seconds
        self._error = error

    def run(self, envelope):
        time.sleep(self._run_seconds)
        if self._error is not None:
            raise self._error
        return {"ok": True}


def _run_with_heartbeat(repository, provider, *, prompt_version="probe-v1"):
    return MonitoringAiService._run_with_heartbeat(
        SimpleNamespace(repository=repository),
        SimpleNamespace(
            job_id="job-1",
            project_id="p1",
            provider="stub",
            requested_model="model-x",
            prompt_version=prompt_version,
        ),
        "owner-1",
        provider,
        SimpleNamespace(),
    )


def test_heartbeat_lease_lost_stops_output_and_preserves_ledger() -> None:
    repository = StubRepository()
    provider = StubProvider(run_seconds=1.2)
    with pytest.raises(MonitoringAiStateConflictError) as excinfo:
        _run_with_heartbeat(repository, provider)
    # 失租异常复用repository失租冲突类型，携带job_id/owner，且链回
    # repository原始失租冲突（探针AST环境同族类型，保证可提取执行）。
    assert excinfo.value.job_id == "job-1"
    assert excinfo.value.owner == "owner-1"
    assert "heartbeat lost lease for job job-1 (owner owner-1)" in str(
        excinfo.value
    )
    assert isinstance(excinfo.value.__cause__, MonitoringAiStateConflictError)
    # 失租确实发生（首次续租成功、其后任一次续租抛失租冲突即停）。
    assert repository.heartbeats >= 2
    # A30后半句：已发生调用的真实账照记（outcome=success：物理调用成功）。
    assert len(repository.calls) == 1
    assert repository.calls[0]["outcome"] == "success"
    assert repository.calls[0]["owner"] == "owner-1"


def test_normal_path_returns_output_and_records_success() -> None:
    repository = StubRepository(fail_heartbeat=False)
    output = _run_with_heartbeat(repository, StubProvider())
    assert output == {"ok": True}
    assert repository.calls[-1]["outcome"] == "success"


def test_provider_error_path_still_records_and_propagates() -> None:
    repository = StubRepository(fail_heartbeat=False)
    boom = RuntimeError("provider exploded")
    with pytest.raises(RuntimeError, match="provider exploded"):
        _run_with_heartbeat(repository, StubProvider(error=boom))
    assert repository.calls[-1]["outcome"] == "provider_error"
    assert repository.calls[-1]["error_code"] == "RuntimeError"
