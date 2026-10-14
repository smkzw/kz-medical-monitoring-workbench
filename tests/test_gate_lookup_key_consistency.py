"""状态机专项S4（02_DESIGN §6.2/§7）：运行门查找键收口。

- 新attempt未确认→B5门409（含最新导入语义）；
- 旧attempt confirmed不放行新attempt（R18-03语义回归）；
- attempt归属函数共享（latest_attempt_id）；
- 投影confirmation_scope显式披露两查找键（不暗中打架，门语义不变）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.admission_stage_view import (  # noqa: E402
    apply_single_source,
    confirmation_scope,
)
from packages.medical_monitoring.admission import fact_materialization as fm  # noqa: E402
from services.api.app.main import _r7_mapping_confirmation_gate  # noqa: E402
from services.api.app import main as _main  # noqa: E402


def _draft(draft_id: str, batch_id: str, status: str):
    """MonitoringMappingDraft形状桩：status为枚举（.value取值）。"""

    return SimpleNamespace(
        draft_id=draft_id,
        batch_id=batch_id,
        status=SimpleNamespace(value=status),
    )


def test_gate_blocks_new_attempt_unconfirmed(monkeypatch) -> None:
    """新attempt草稿未确认（project-latest键）→门409阻断。"""

    latest = _draft("draft-new", "attempt-2", "draft")
    monkeypatch.setattr(
        _main.monitoring_mapping_draft_repository,
        "latest_draft_for_project",
        lambda _project_id: latest,
    )
    blocked = _r7_mapping_confirmation_gate("proj-s4")
    assert blocked is not None
    assert blocked["code"] == "mapping_confirmation_required"
    assert "attempt-2" in blocked["message"] or "draft-new" in blocked["message"]


def test_gate_blocks_when_latest_attempt_confirmed_not_the_latest(
    monkeypatch,
) -> None:
    """旧attempt confirmed但latest是更未确认的新attempt→不放行（R18-03）。"""

    # 门只读project-latest键：latest=新attempt未确认草稿即阻断，
    # 与旧attempt是否存在/是否confirmed无关。
    latest = _draft("draft-new", "attempt-3", "draft")
    monkeypatch.setattr(
        _main.monitoring_mapping_draft_repository,
        "latest_draft_for_project",
        lambda _project_id: latest,
    )
    blocked = _r7_mapping_confirmation_gate("proj-s4")
    assert blocked is not None
    assert blocked["code"] == "mapping_confirmation_required"

    # latest=confirmed→放行（R18-03回归基线）。
    monkeypatch.setattr(
        _main.monitoring_mapping_draft_repository,
        "latest_draft_for_project",
        lambda _project_id: _draft("draft-old", "attempt-2", "confirmed"),
    )
    assert _r7_mapping_confirmation_gate("proj-s4") is None

    # 无任何draft→阻断（尚未确认）。
    monkeypatch.setattr(
        _main.monitoring_mapping_draft_repository,
        "latest_draft_for_project",
        lambda _project_id: None,
    )
    blocked = _r7_mapping_confirmation_gate("proj-s4")
    assert blocked is not None
    assert blocked["code"] == "mapping_confirmation_required"


def test_gate_and_projection_share_lookup_keys(monkeypatch) -> None:
    """门（project-latest键）与投影（attempt键+latest披露）同库同源。"""

    attempt_draft = _draft("draft-old", "attempt-2", "confirmed")
    latest = _draft("draft-new", "attempt-3", "draft")
    monkeypatch.setattr(
        _main.monitoring_mapping_draft_repository,
        "latest_draft_for_project",
        lambda _project_id: latest,
    )
    blocked = _r7_mapping_confirmation_gate("proj-s4")
    assert blocked is not None  # 门按latest键阻断

    scope = confirmation_scope(draft=attempt_draft, latest_draft=latest)
    # 投影显式披露：本attempt confirmed但项目存在更新导入。
    assert scope["scope"] == "superseded_by_newer_attempt"
    assert scope["latest_draft_attempt_id"] == "attempt-3"
    assert "更新导入" in scope["note"]


def test_confirmation_scope_same_draft_is_confirmed() -> None:
    draft = _draft("draft-1", "attempt-1", "confirmed")
    scope = confirmation_scope(draft=draft, latest_draft=draft)
    assert scope["scope"] == "confirmed"


def test_confirmation_scope_active_draft_pending() -> None:
    draft = _draft("draft-2", "attempt-1", "draft")
    scope = confirmation_scope(draft=draft, latest_draft=draft)
    assert scope["scope"] == "pending"


def test_apply_single_source_emits_scope() -> None:
    payload = {
        "state": "candidates_ready",
        "summary": {"candidate_count": 1},
        "candidates": [],
    }
    projected = apply_single_source(
        payload,
        draft=_draft("draft-1", "attempt-1", "confirmed"),
        facts_status=None,
        latest_draft=_draft("draft-2", "attempt-2", "confirmed"),
    )
    assert projected["confirmation_scope"]["scope"] == (
        "superseded_by_newer_attempt"
    )
    # 本attempt权威行状态仍如实（confirmed），披露靠scope字段。
    assert projected["confirmation_status"] == "confirmed"


def test_latest_attempt_id_shared_function(tmp_path: Path, monkeypatch) -> None:
    """B6门与投影共享的attempt归属函数：created_at最新者胜。"""

    admission_dir = tmp_path / "admissions"
    admission_dir.mkdir()

    def _attempt(attempt_id: str, created_at: str) -> SimpleNamespace:
        return SimpleNamespace(attempt_id=attempt_id, created_at=created_at)

    attempts = {
        "attempt-a": _attempt("attempt-a", "2026-10-01T00:00:00+00:00"),
        "attempt-b": _attempt("attempt-b", "2026-10-02T00:00:00+00:00"),
    }
    monkeypatch.setattr(
        fm, "list_attempt_ids", lambda _dir: ["attempt-a", "attempt-b"]
    )
    monkeypatch.setattr(fm, "load_attempt", lambda _dir, _id, verify_files: attempts[_id])
    assert fm.latest_attempt_id("proj-s4", tmp_path) == "attempt-b"

    monkeypatch.setattr(fm, "list_attempt_ids", lambda _dir: [])
    assert fm.latest_attempt_id("proj-s4", tmp_path) == ""
