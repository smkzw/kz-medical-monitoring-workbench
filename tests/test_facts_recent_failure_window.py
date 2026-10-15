"""状态机专项T1（02_DESIGN §5-T1）：facts失败时效窗接线。

- 时效窗推导（纯函数）：failure_recorded在窗（晚于最近ready且24h内）
  →retry_generate_facts动作键真实可达；ready后→退回generate_facts；
  无事件→False（现行为回归）；超24h陈旧失败→False。
- _assemble_stage_state装配侧：stage_events的facts事件驱动
  facts_recent_failure实参（stage过滤读取）。
- _record_facts_stage_state：failure_class经failure_class_for分类
  （infra失败码→infra，其余→content），不再硬编码"content"。
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.admission_stage_view import (  # noqa: E402
    build_stage_view,
)
from packages.medical_monitoring.api.r7_product import (  # noqa: E402
    mapping_candidate_routes as mcr,
)

NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def _event(
    *,
    event_type: str,
    to_state: str = "",
    minutes_ago: int = 5,
) -> dict:
    created = NOW - timedelta(minutes=minutes_ago)
    return {
        "event_type": event_type,
        "to_state": to_state,
        "created_at": created.isoformat(),
    }


def test_failure_event_in_window_yields_retry_key() -> None:
    """失败事件在窗→facts_recent_failure=True→retry键available。"""

    events = [_event(event_type="failure_recorded", minutes_ago=10)]
    assert mcr.facts_recent_failure_from_events(events, now=NOW) is True

    view = build_stage_view(
        project_id="p1",
        attempt_id="attempt-1",
        documents_state="ready",
        recognition_state="candidates_ready",
        mapping_state="confirmed",
        facts_state="not_generated",
        facts_recent_failure=True,
    )
    facts_entry = next(
        entry for entry in view["blocking"] if entry["stage"] == "facts"
    )
    assert facts_entry["action_key"] == "retry_generate_facts"
    assert facts_entry["action_available"] is True
    assert view["primary_action_key"] == "retry_generate_facts"


def test_ready_event_after_failure_reverts_to_generate() -> None:
    """ready后（state_changed→ready晚于failure）→退回generate_facts。"""

    events = [
        _event(event_type="failure_recorded", minutes_ago=30),
        _event(event_type="state_changed", to_state="ready", minutes_ago=10),
    ]
    assert mcr.facts_recent_failure_from_events(events, now=NOW) is False

    view = build_stage_view(
        project_id="p1",
        attempt_id="attempt-1",
        documents_state="ready",
        recognition_state="candidates_ready",
        mapping_state="confirmed",
        facts_state="not_generated",
        facts_recent_failure=False,
    )
    facts_entry = next(
        entry for entry in view["blocking"] if entry["stage"] == "facts"
    )
    assert facts_entry["action_key"] == "generate_facts"


def test_no_events_is_false_regressor() -> None:
    """无事件→False（参数缺省=现状行为回归）。"""

    assert mcr.facts_recent_failure_from_events([], now=NOW) is False


def test_stale_failure_beyond_24h_is_false() -> None:
    """超24h时效窗的陈旧失败不再引导重试。"""

    events = [_event(event_type="failure_recorded", minutes_ago=25 * 60)]
    assert mcr.facts_recent_failure_from_events(events, now=NOW) is False


def test_assemble_stage_state_passes_window_flag(tmp_path: Path) -> None:
    """装配侧：stage_events的facts失败事件→build_stage_view收到True。

    ai_repository.stage_store.list_events以stage=facts过滤读取（T1）。
    """

    recent = (NOW - timedelta(minutes=10)).isoformat()
    stale = (NOW - timedelta(hours=30)).isoformat()

    class StubStore:
        def list_events(self, project_id, attempt_id, *, stage="", after="", limit=200):
            assert stage == "facts"
            # 模拟store端stage过滤：只回facts事件。
            return [
                {
                    "stage": "facts",
                    "event_type": "failure_recorded",
                    "to_state": "",
                    "created_at": stale,
                },
                {
                    "stage": "facts",
                    "event_type": "failure_recorded",
                    "to_state": "",
                    "created_at": recent,
                },
            ]

    confirmation = SimpleNamespace(
        ai_repository=SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: [],
            stage_store=StubStore(),
        ),
        _recognition_state_row=lambda *, project_id, attempt_id: None,
        mapping_repository=None,
        _facts_status=lambda *, project_id, attempt_id, workspace_dir: {
            "facts_generated": False,
        },
        task_type=SimpleNamespace(value="listing_field_mapping"),
    )
    pipeline = SimpleNamespace(
        document_readiness=lambda **_kwargs: {"ready": True, "roles": []},
    )
    view = mcr._assemble_stage_state(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir=tmp_path,
        pipeline=pipeline,
        confirmation=confirmation,
        build_stage_view=build_stage_view,
        unresolved_question_counter=lambda fields: 0,
        pace_estimator=lambda jobs, total=0, completed=0: None,
    )
    facts_entry = next(
        entry for entry in view["blocking"] if entry["stage"] == "facts"
    )
    assert facts_entry["action_key"] == "retry_generate_facts"


def test_assemble_stage_state_store_failure_falls_back_false(
    tmp_path: Path,
) -> None:
    """事件读取故障→best-effort回退False=现状（留痕完整性<权威正确性）。"""

    class BrokenStore:
        def list_events(self, *args, **kwargs):
            raise RuntimeError("store unavailable")

    confirmation = SimpleNamespace(
        ai_repository=SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: [],
            stage_store=BrokenStore(),
        ),
        _recognition_state_row=lambda *, project_id, attempt_id: None,
        mapping_repository=None,
        _facts_status=lambda *, project_id, attempt_id, workspace_dir: {
            "facts_generated": False,
        },
        task_type=SimpleNamespace(value="listing_field_mapping"),
    )
    pipeline = SimpleNamespace(
        document_readiness=lambda **_kwargs: {"ready": True, "roles": []},
    )
    view = mcr._assemble_stage_state(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir=tmp_path,
        pipeline=pipeline,
        confirmation=confirmation,
        build_stage_view=build_stage_view,
        unresolved_question_counter=lambda fields: 0,
        pace_estimator=lambda jobs, total=0, completed=0: None,
    )
    facts_entry = next(
        entry for entry in view["blocking"] if entry["stage"] == "facts"
    )
    assert facts_entry["action_key"] == "generate_facts"


def test_facts_failure_event_classifies_infra_and_content(tmp_path: Path) -> None:
    """_record_facts_stage_state：failure_class经failure_class_for分类。

    infra失败码（provider_timeout）→infra；其余（content_error）→content；
    成功路径（ready）不落failure事件。main.monitoring_ai_repository以
    tmp仓替换（main模块级全局，T1验证wiring）。
    """

    import services.api.app.main as main_module
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "facts_t1.sqlite3")
    original = main_module.monitoring_ai_repository
    main_module.monitoring_ai_repository = repo
    try:
        main_module._record_facts_stage_state(
            "proj-t1", "attempt-t1", "not_generated", "provider_timeout"
        )
        main_module._record_facts_stage_state(
            "proj-t1", "attempt-t1", "not_generated", "field_profile_invalid"
        )
        main_module._record_facts_stage_state(
            "proj-t1", "attempt-t1", "ready", ""
        )
    finally:
        main_module.monitoring_ai_repository = original

    events = repo.stage_store.list_events("proj-t1", "attempt-t1", stage="facts")
    failures = {
        str(event["reason_code"]): str(event["failure_class"])
        for event in events
        if event["event_type"] == "failure_recorded"
    }
    assert failures == {
        "provider_timeout": "infra",
        "field_profile_invalid": "content",
    }
    ready = [
        event
        for event in events
        if event["event_type"] == "state_changed"
        and event["to_state"] == "ready"
    ]
    assert len(ready) == 1
