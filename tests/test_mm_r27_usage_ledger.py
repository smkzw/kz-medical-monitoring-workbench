"""R27-B5用量记录回归：发出前start/结束更新、提供方实际schema规范化、
0与unknown显式分离、reasoning/cached不重复计入total、中断留started。

全部使用stub transport/合成diagnostics，不消耗真实模型。

钉住的行为与理由：
- 修改前：账本行只在请求结束后写入（进程中断→整行缺失，无从知晓一次
  已发出的物理POST）；SSE流只透传total一个数、非流式完全不提取usage——
  真实HTTP调用的prompt/completion/reasoning/cached全部丢失成unknown。
- 修改后：请求发出前先落started行（中断时保持started/unknown，绝不推断
  为0）；结束后原行更新；提供方实际usage schema（OpenAI嵌套details、
  DeepSeek缓存命中、input/output别名、detail子字典）在账本统一规范化；
  total只取上游回报值，绝不从组件相加（reasoning⊆completion、
  cached⊆prompt，重复计入即双算）；显式None判断，0不丢失为unknown。
"""
from __future__ import annotations

from pathlib import Path

from services.api.app.monitoring_ai_contracts import MonitoringAiJobStatus
from services.api.app.monitoring_ai_repository import (
    MonitoringAiRepository,
    _normalize_call_usage,
)
from tests.test_monitoring_ai_service import (
    FakeProvider,
    _field_profile,
    _revision,
    _service,
    _valid_output,
)


def test_provider_actual_schemas_are_normalized(tmp_path: Path) -> None:
    """提供方实际schema（OpenAI嵌套details/DeepSeek/别名）规范化入列。"""
    repo = MonitoringAiRepository(tmp_path / "b5-schema.sqlite3")
    # OpenAI实际schema：缓存/推理在子字典里
    repo.record_call(
        project_id="p1", job_id="j-openai", attempt_id="att", call_seq=0,
        owner="w1", provider="prov", requested_model="m",
        observed_model="m",
        diagnostics={
            "wire": "sse",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "prompt_tokens_details": {"cached_tokens": 20},
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
        },
        outcome="success",
    )
    row = repo.call_ledger("p1", "j-openai")[0]
    assert row["prompt_tokens"] == 100
    assert row["completion_tokens"] == 50
    assert row["reasoning_tokens"] == 30
    assert row["cached_tokens"] == 20
    # total只取上游回报值——绝不做 prompt+completion+reasoning+cached
    # （那会双算：reasoning⊆completion、cached⊆prompt）
    assert row["total_tokens"] == 150
    assert row["usage_unknown"] == 0

    # DeepSeek实际schema：缓存命中独立字段；别名input/output
    repo.record_call(
        project_id="p1", job_id="j-deepseek", attempt_id="att", call_seq=0,
        owner="w1", provider="prov", requested_model="m",
        observed_model="m",
        diagnostics={
            "wire": "sse",
            "usage": {
                "input_tokens": 80,
                "output_tokens": 40,
                "prompt_cache_hit_tokens": 15,
            },
        },
        outcome="success",
    )
    row = repo.call_ledger("p1", "j-deepseek")[0]
    assert row["prompt_tokens"] == 80
    assert row["completion_tokens"] == 40
    assert row["cached_tokens"] == 15

    # 上游未回报total：保持None不伪造（既有钉点延续，也不从组件相加）
    repo.record_call(
        project_id="p1", job_id="j-nototal", attempt_id="att", call_seq=0,
        owner="w1", provider="prov", requested_model="m",
        observed_model="m",
        diagnostics={
            "wire": "sse",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
        outcome="success",
    )
    assert repo.call_ledger("p1", "j-nototal")[0]["total_tokens"] is None


def test_zero_usage_in_provider_subdict_is_not_unknown() -> None:
    """显式None判断：新schema子字典里的明确0是真实观测值，不丢失。"""
    prompt, completion, reasoning, cached, total, unknown = _normalize_call_usage({
        "usage": {
            "prompt_tokens": 7,
            "completion_tokens": 3,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
        }
    })
    assert (prompt, completion) == (7, 3)
    assert cached == 0 and reasoning == 0
    assert unknown == 0
    # 全部已知键缺失→unknown
    _, _, _, _, _, unknown_missing = _normalize_call_usage({"wire": "sse"})
    assert unknown_missing == 1


def test_start_call_leaves_started_unknown_row_on_interruption(tmp_path: Path) -> None:
    """请求发出前落started行；进程中断（无complete_call）时该行保持
    started/unknown——用量列为NULL，绝不推断为0。"""
    repo = MonitoringAiRepository(tmp_path / "started.sqlite3")
    call_id = repo.start_call(
        project_id="p1", job_id="j-int", attempt_id="att",
        owner="w1", provider="prov", requested_model="m",
    )
    assert call_id.startswith("moncall_")
    rows = repo.call_ledger("p1", "j-int")
    assert len(rows) == 1
    row = rows[0]
    assert row["outcome"] == "started"
    assert row["prompt_tokens"] is None  # 未观测≠0
    assert row["total_tokens"] is None
    assert row["usage_unknown"] == 1
    summary = repo.call_ledger_summary("p1")
    assert summary["started_calls"] == 1
    assert summary["usage_unknown_count"] == 1
    assert summary["total_prompt_tokens"] == 0  # 聚合为0可，单行推断不可

    # 正常结束：原行更新（不新增行）
    repo.complete_call(
        call_id,
        diagnostics={
            "wire": "sse",
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
            },
        },
        observed_model="m-observed",
        outcome="success",
    )
    rows = repo.call_ledger("p1", "j-int")
    assert len(rows) == 1
    row = rows[0]
    assert row["outcome"] == "success"
    assert row["prompt_tokens"] == 12
    assert row["total_tokens"] == 20
    assert row["usage_unknown"] == 0
    assert row["observed_model"] == "m-observed"


def test_transport_started_row_exists_before_response_and_updates_after(
    tmp_path: Path,
) -> None:
    """stub transport端到端：run()执行期间账本已存在started行（请求发出
    前落账）；结束后原行更新为success+真实用量；不残留started/重复行。"""

    class _LedgerInspectingProvider(FakeProvider):
        def __init__(self, builders):
            super().__init__(builders)
            self._repo = None
            self._project_id = ""
            self._job_id = ""
            self.started_during_call = False
            self.response_diagnostics: dict = {}

        def run(self, envelope):
            rows = self._repo.call_ledger(self._project_id, self._job_id)
            self.started_during_call = bool(
                rows and rows[-1]["outcome"] == "started"
            )
            return super().run(envelope)

    provider = _LedgerInspectingProvider(
        [lambda envelope: _valid_output(envelope)]
    )
    repository = MonitoringAiRepository(tmp_path / "transport.sqlite3")
    service = _service(tmp_path, provider)
    service.repository = repository
    job = service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=_field_profile(field_count=1),
    )
    provider._repo = repository
    provider._project_id = "project-alpha"
    provider._job_id = job.job_id
    provider.response_diagnostics = {
        "wire": "sse",
        "usage": {
            "prompt_tokens": 64,
            "completion_tokens": 32,
            "total_tokens": 96,
            "prompt_tokens_details": {"cached_tokens": 8},
            "completion_tokens_details": {"reasoning_tokens": 16},
        },
    }

    result = service.run_next("usage-worker")

    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.COMPLETED, (
        f"{result.job.failure_code}: {result.job.failure_message}"
    )
    assert provider.started_during_call is True  # 请求发出前行已存在
    rows = repository.call_ledger("project-alpha", job.job_id)
    assert len(rows) == 1  # started行原行更新，不重复
    row = rows[0]
    assert row["outcome"] == "success"
    assert row["prompt_tokens"] == 64
    assert row["completion_tokens"] == 32
    assert row["total_tokens"] == 96
    assert row["reasoning_tokens"] == 16
    assert row["cached_tokens"] == 8
    assert row["usage_unknown"] == 0


def test_provider_error_after_start_updates_the_started_row(
    tmp_path: Path,
) -> None:
    """调用中途抛错：started行原行更新为provider_error，不残留重复行。"""

    class _ExplodingProvider(FakeProvider):
        def run(self, envelope):
            raise RuntimeError("synthetic transport outage")

    provider = _ExplodingProvider([])
    repository = MonitoringAiRepository(tmp_path / "error.sqlite3")
    service = _service(tmp_path, provider)
    service.repository = repository
    service.provider_factory = lambda _env: provider
    service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=_field_profile(field_count=1),
    )
    result = service.run_next("usage-error")

    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.FAILED
    rows = repository.call_ledger("project-alpha")
    assert len(rows) == 1
    assert rows[0]["outcome"] == "provider_error"
    assert rows[0]["error_code"] == "RuntimeError"
    assert rows[0]["prompt_tokens"] is None  # 无usage：unknown不填0
    assert rows[0]["usage_unknown"] == 1
