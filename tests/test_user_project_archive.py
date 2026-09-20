"""项目归档契约（测试轮清洁空间要求）：软删除=列表隐藏+可恢复。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.contracts.workbench_contracts.models import (  # noqa: E402
    UserProjectCreateRequest,
)
from services.api.app.user_project_store import UserProjectStore  # noqa: E402


@pytest.fixture()
def store(tmp_path: Path) -> UserProjectStore:
    return UserProjectStore(tmp_path / "user_projects.sqlite3")


def test_archive_hides_and_restore_recovers(store: UserProjectStore) -> None:
    record = store.create(
        UserProjectCreateRequest(
            project_code="TEST-P1",
            project_name="测试项目一",
            indication="适应症",
            product_name="药品",
            study_phase="III期",
            idempotency_key="test-archive-p1",
        )
    )
    pid = record.project_id
    assert store.archive_project(pid)
    assert pid in store.archived_project_ids()
    assert store.restore_project(pid)
    assert pid not in store.archived_project_ids()


def test_archive_is_idempotent_and_isolated(store: UserProjectStore) -> None:
    record = store.create(
        UserProjectCreateRequest(
            project_code="TEST-P2",
            project_name="测试项目二",
            indication="适应症",
            product_name="药品",
            study_phase="II期",
            idempotency_key="test-archive-p2",
        )
    )
    pid = record.project_id
    store.archive_project(pid)
    store.archive_project(pid)  # 幂等
    assert store.archived_project_ids() == {pid}  # 不影响其他项目
