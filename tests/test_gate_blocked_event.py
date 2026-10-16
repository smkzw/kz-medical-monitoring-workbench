"""状态机专项M2（02_DESIGN §四-M2/N4）：B5运行门gate_blocked事件留痕。

- 未确认draft调门→gate_blocked事件存在且六字段正确（attempt_id=''、
  stage=mapping_confirmation、event_type=gate_blocked、
  reason_code=mapping_confirmation_required、detail.draft_status）；
- 无draft→同样留痕（draft_status=no_draft）；
- 事件写故障→门仍返回409详情（吞异常不外泄，留痕完整性<权威正确性）；
- 门是求值不是变迁：同项目重复触发允许多条（如实记录每次阻断）；
- confirmed放行→零事件（只在阻断时留痕）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import services.api.app.main as main_module  # noqa: E402
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)

PROJECT = "proj-gateblocked"


def _draft(status: str = "draft"):
    return SimpleNamespace(status=status, draft_id="draft-m2")


def _install(tmp_path: Path, *, draft, stage_store=None):
    """临时替换main模块级全局（draft仓桩+AI仓tmp实例），返回还原函数。"""

    repo = MonitoringAiRepository(tmp_path / "gate_m2.sqlite3")
    real_store = repo.stage_store
    if stage_store is not None:
        repo.stage_store = stage_store
    draft_repo = SimpleNamespace(latest_draft_for_project=lambda _pid: draft)
    original_ai = main_module.monitoring_ai_repository
    original_drafts = main_module.monitoring_mapping_draft_repository
    main_module.monitoring_ai_repository = repo
    main_module.monitoring_mapping_draft_repository = draft_repo
    return repo, real_store, lambda: (
        setattr(main_module, "monitoring_ai_repository", original_ai),
        setattr(
            main_module,
            "monitoring_mapping_draft_repository",
            original_drafts,
        ),
    )


def test_gate_blocked_event_six_fields_on_unconfirmed_draft(tmp_path: Path) -> None:
    """未确认draft调门→409详情+gate_blocked事件六字段正确。"""

    repo, _real_store, restore = _install(tmp_path, draft=_draft("draft"))
    try:
        blocked = main_module._r7_mapping_confirmation_gate(PROJECT)
        assert blocked is not None
        assert blocked["code"] == "mapping_confirmation_required"

        events = repo.stage_store.list_events(
            PROJECT, "", stage="mapping_confirmation"
        )
        assert len(events) == 1
        event = events[0]
        assert event["project_id"] == PROJECT
        assert event["attempt_id"] == ""
        assert event["stage"] == "mapping_confirmation"
        assert event["event_type"] == "gate_blocked"
        assert event["reason_code"] == "mapping_confirmation_required"
        assert json.loads(event["detail_json"]) == {"draft_status": "draft"}
    finally:
        restore()


def test_gate_blocked_event_no_draft_records_no_draft_status(
    tmp_path: Path,
) -> None:
    """项目无任何draft→409详情+事件draft_status=no_draft。"""

    repo, _real_store, restore = _install(tmp_path, draft=None)
    try:
        blocked = main_module._r7_mapping_confirmation_gate(PROJECT)
        assert blocked is not None
        events = repo.stage_store.list_events(
            PROJECT, "", stage="mapping_confirmation"
        )
        assert len(events) == 1
        assert json.loads(events[0]["detail_json"]) == {
            "draft_status": "no_draft"
        }
    finally:
        restore()


def test_gate_event_write_failure_does_not_change_gate(tmp_path: Path) -> None:
    """事件写故障→门仍返回409详情（吞异常不外泄）。"""

    class BrokenStore:
        def append_event_autonomous(self, **_kwargs):
            raise RuntimeError("store unavailable")

    repo, real_store, restore = _install(
        tmp_path, draft=_draft("draft"), stage_store=BrokenStore()
    )
    try:
        blocked = main_module._r7_mapping_confirmation_gate(PROJECT)
        assert blocked is not None
        assert blocked["code"] == "mapping_confirmation_required"
        assert "draft-m2" in blocked["message"]
        assert real_store.list_events(PROJECT, "") == []
    finally:
        restore()


def test_gate_blocked_events_accumulate_per_invocation(tmp_path: Path) -> None:
    """门是求值不是变迁：同请求重复触发允许多条（如实记录每次阻断）。"""

    repo, _real_store, restore = _install(tmp_path, draft=_draft("draft"))
    try:
        assert main_module._r7_mapping_confirmation_gate(PROJECT) is not None
        assert main_module._r7_mapping_confirmation_gate(PROJECT) is not None
        events = repo.stage_store.list_events(
            PROJECT, "", stage="mapping_confirmation"
        )
        assert len(events) == 2
    finally:
        restore()


def test_confirmed_draft_passes_gate_without_event(tmp_path: Path) -> None:
    """confirmed→放行返回None，零事件（只在阻断时留痕）。"""

    repo, _real_store, restore = _install(tmp_path, draft=_draft("confirmed"))
    try:
        assert main_module._r7_mapping_confirmation_gate(PROJECT) is None
        assert repo.stage_store.list_events(PROJECT, "") == []
    finally:
        restore()
