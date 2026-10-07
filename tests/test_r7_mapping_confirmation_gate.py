"""R24轮（R18-03收尾）：fail-open语义修正的回归测试。

R19实测：facts旁路存在时，未确认映射的运行照常执行（fail-open）——
以未确认映射产出医学结论比停滞责任更大。运行启动前必须核对最近一次
字段映射草稿的确认状态：无草稿/未确认→阻断；已确认→放行。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
)


def _empty_repository(tmp_path: Path) -> MonitoringMappingDraftRepository:
    return MonitoringMappingDraftRepository(
        tmp_path / "medical_monitoring_ai.sqlite3"
    )


def test_latest_draft_for_project_none_when_never_started(tmp_path: Path) -> None:
    repository = _empty_repository(tmp_path)
    assert repository.latest_draft_for_project("proj_user_never") is None


def test_latest_draft_prefers_most_recent_update(tmp_path: Path) -> None:
    """重新导入产生新attempt草稿后，latest指向新草稿（旧确认不再覆盖新数据）。"""

    from services.api.app.monitoring_ai_contracts import (
        MonitoringAiInputRevision,
        canonical_json,
    )
    from services.api.app.monitoring_mapping_draft_repository import (
        _mapping_draft_id,
    )

    repository = _empty_repository(tmp_path)
    revision = MonitoringAiInputRevision.model_validate(
        {"project_id": "proj_user_gate", "batch_revision": "stg-rev-001"}
    )
    input_revision = canonical_json(revision)
    revision_sha = revision.revision_sha256
    connection = repository._connect()
    try:
        for batch_id, profile_sha, status, moment in (
            ("stg-old", "a" * 64, "confirmed", "2026-10-01T00:00:00+00:00"),
            ("stg-new", "e" * 64, "draft", "2026-10-07T00:00:00+00:00"),
        ):
            draft_id = _mapping_draft_id(
                project_id="proj_user_gate",
                batch_id=batch_id,
                full_profile_sha256=profile_sha,
                input_revision_sha256=revision_sha,
                source_set_sha256="d" * 64,
            )
            connection.execute(
                """
                INSERT INTO monitoring_mapping_drafts (
                    draft_id, project_id, batch_id, full_profile_sha256,
                    full_input_sha256, input_revision_json,
                    input_revision_sha256, source_set_sha256, status, version,
                    fields_json, expected_job_ids_json, confirmed_revision_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft_id,
                    "proj_user_gate",
                    batch_id,
                    profile_sha,
                    "b" * 64,
                    input_revision,
                    revision_sha,
                    "d" * 64,
                    status,
                    1,
                    "[]",
                    "[]",
                    "",
                    moment,
                    moment,
                ),
            )
        connection.commit()
    finally:
        connection.close()
    latest = repository.latest_draft_for_project("proj_user_gate")
    assert latest is not None
    assert latest.batch_id == "stg-new"
    assert str(getattr(latest.status, "value", latest.status)) == "draft"


def test_gate_semantics_via_status_value(tmp_path: Path) -> None:
    """str-Enum的str()不等于成员值——判据必须经.value比较（防回归）。"""

    from services.api.app.monitoring_mapping_draft_repository import (
        MonitoringMappingDraftStatus,
    )

    confirmed = MonitoringMappingDraftStatus.CONFIRMED
    # 这是曾经的写法陷阱：str(confirmed) == "MonitoringMappingDraftStatus.CONFIRMED"
    assert str(confirmed) != "confirmed"
    assert str(getattr(confirmed, "value", confirmed)) == "confirmed"
