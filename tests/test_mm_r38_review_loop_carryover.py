"""R38轮（R36-03）：监查运行结果必须持续留在复核管道——收件箱不清零、
决策跨运行结转。

缺陷回顾：发布链每次运行的 source_revision（product-publication:{run_id}）
都会让全部 monitoring 源版本失配，旧快照发现的已读/处置记录只按整串
source_version 精确匹配而被整体出清；前端在收件箱读取在途/失败时按空箱
渲染「0项待决策/当前无未读医学决策项」，监查运行后一次读取失败即呈现
复核管道断裂的假象且无重试入口。

本测试守住端到端口径：新发现→收件箱待决策→已读/复核留痕→计数联动→
新运行后同含义发现结转（含义变化则回到待复核）。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.contracts.workbench_contracts import (  # noqa: E402
    MonitoringRiskDispositionKind,
    RiskSeverity,
    RuxRiskDispositionAction,
    RuxRiskDispositionRecord,
    WorkbenchInboxActionRecord,
    WorkbenchItemAction,
)
from services.api.app.medical_risk_repository import (  # noqa: E402
    MedicalRiskRepository,
)
from services.api.app.monitoring_product_risk_bridge import (  # noqa: E402
    record_publication_risk_snapshot,
)
from services.api.app.workbench_inbox import (  # noqa: E402
    RuxRiskDispositionStore,
    WorkbenchInboxService,
    WorkbenchInboxStore,
    _monitoring_meaning_token,
    _monitoring_source_version,
)

PROJECT_ID = "proj_user_review_loop_test"
ACTOR = "medical_manager"
T0 = datetime(2026, 10, 13, 8, 0, tzinfo=timezone.utc)


def _packet(ae_rationale: str = "源记录依据——严重度：3级。") -> SimpleNamespace:
    return SimpleNamespace(
        risks=[
            SimpleNamespace(
                risk_ref="risk-AE-000018",
                risk_key="ae:AE:18",
                risk_instance_ref="riski-AE-000018",
                subject_ref="subject-21009",
                site_ref="site-site-unknown",
                domain="ae",
                severity="high",
                risk_type_zh="不良事件",
                medical_note=ae_rationale,
                source_locator_refs=("loc-AE-000018",),
            ),
            SimpleNamespace(
                risk_ref="risk-CM-000003",
                risk_key="cm:CM:3",
                risk_instance_ref="riski-CM-000003",
                subject_ref="subject-23003",
                site_ref="site-site-unknown",
                domain="cm",
                severity="medium",
                risk_type_zh="合并用药",
                medical_note="",
                source_locator_refs=("loc-CM-000003",),
            ),
        ],
        sources=[
            SimpleNamespace(locator_ref="loc-AE-000018", canonical_location="AE!row19"),
            SimpleNamespace(locator_ref="loc-CM-000003", canonical_location="CM!row4"),
        ],
    )


class _ManifestService:
    def is_user_created_project(self, project_id: str) -> bool:
        return project_id == PROJECT_ID

    def build_manifest(self, project_id: str) -> Any:
        return SimpleNamespace(
            modules=[
                SimpleNamespace(
                    module="medical_monitoring",
                    label="医学监查",
                    visible_in_dashboard=True,
                )
            ]
        )


class _NullService:
    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> Any:
            if name in {"risks", "approvals"}:
                return []
            return None

        return _noop


def _service(tmp_path: Any, repository: MedicalRiskRepository) -> Any:
    return WorkbenchInboxService(
        _NullService(),
        _NullService(),
        _NullService(),
        _NullService(),
        _NullService(),
        _NullService(),
        _NullService(),
        _NullService(),
        WorkbenchInboxStore(tmp_path / "inbox_actions.jsonl"),
        rux_disposition_store=RuxRiskDispositionStore(tmp_path / "dispositions.jsonl"),
        project_source_manifest_service=_ManifestService(),
        medical_risk_repository=repository,
    )


def _publish(repository: MedicalRiskRepository, run_id: str, packet: Any) -> None:
    record_publication_risk_snapshot(
        project_id=PROJECT_ID,
        run_id=run_id,
        packet=packet,
        risk_repository=repository,
        rule_profile_revision=f"r5-packet:{run_id[:16]}",
        created_at=T0,
    )


def _mm_items(service: Any) -> list:
    """经公开读取口径（含已读态注水）取医学监查收件箱项。"""

    return sorted(
        service.monitoring_risk_items(PROJECT_ID, actor=ACTOR),
        key=lambda item: item.item_id,
    )


def _module_needs_action(service: Any) -> int:
    result = service._hydrate_inbox_result(PROJECT_ID, service._monitoring_risk_items(PROJECT_ID), actor=ACTOR)
    summary = next(m for m in result.module_summaries if m.module == "medical_monitoring")
    return summary.needs_action_count


def test_meaning_token_scope() -> None:
    """含义token只对monitoring源版本有定义，rux口径不受影响。"""

    packet_risk = _packet().risks[0]
    risk = SimpleNamespace(
        project_id=PROJECT_ID,
        rule_id=packet_risk.risk_key,
        title="不良事件（受试者21009）",
        severity=RiskSeverity.HIGH,
        rationale=packet_risk.medical_note,
        recommended_action="进入医学监查结果视图复核该发现。",
        evidence_span_ids=["AE!row19"],
    )
    version = _monitoring_source_version(risk, "product-publication:run-1")
    token = _monitoring_meaning_token(version)
    assert token
    assert _monitoring_meaning_token(version) == _monitoring_meaning_token(
        _monitoring_source_version(risk, "product-publication:run-2")
    )
    assert _monitoring_meaning_token(f"rux-p0:{packet_risk.risk_ref}:abc:def") == ""


def test_new_findings_reach_inbox_and_counts_link(tmp_path: Any) -> None:
    """发布新发现→收件箱待决策→模块计数联动。"""

    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    _publish(repository, "r7-run-1", _packet())
    service = _service(tmp_path, repository)
    items = _mm_items(service)
    assert len(items) == 2
    assert all(item.unread and item.needs_action for item in items)
    assert {item.status for item in items} == {"待医学复核"}
    assert _module_needs_action(service) == 2


def test_read_and_disposition_survive_new_run(tmp_path: Any) -> None:
    """已读/复核留痕在下一轮同含义发现上结转，不随运行出清。"""

    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    _publish(repository, "r7-run-1", _packet())
    service = _service(tmp_path, repository)
    items = {item.risk_key: item for item in _mm_items(service)}
    ae = items["ae:AE:18"]

    # 已读留痕（run-1版本）
    service.store.append(
        WorkbenchInboxActionRecord(
            record_id="rec-read-1",
            project_id=PROJECT_ID,
            item_id=ae.item_id,
            action=WorkbenchItemAction.MARK_READ,
            actor=ACTOR,
            source_version=ae.source_version,
            created_at=T0,
        )
    )
    # 复核留痕：标记医学复核（run-1版本）——reviewed 仍有下一步动作
    # （记录Query草稿），状态标签必须离开「待医学复核」。
    disposition_store = service.rux_disposition_store
    disposition_store.append(
        RuxRiskDispositionRecord(
            record_id="rec-disp-1",
            project_id=PROJECT_ID,
            item_id=ae.item_id,
            risk_id=ae.source_id,
            risk_key=ae.risk_key,
            risk_instance_id=ae.risk_instance_id,
            snapshot_id=ae.snapshot_id,
            subject_id="21009",
            rule_id="ae:AE:18",
            action=RuxRiskDispositionAction.REVIEWED,
            disposition_kind=MonitoringRiskDispositionKind.CENTER_QUERY,
            previous_state="pending_review",
            new_state="reviewed",
            actor=ACTOR,
            source_version=ae.source_version,
            created_at=T0,
        )
    )
    items = {item.risk_key: item for item in _mm_items(service)}
    assert items["ae:AE:18"].status == "已医学复核"

    # 新一轮运行：同 packet 重发布（新 run id ⇒ 新 source_revision）
    _publish(repository, "r7-run-2-different", _packet())
    items = {item.risk_key: item for item in _mm_items(service)}
    assert len(items) == 2
    ae_after = items["ae:AE:18"]
    cm_after = items["cm:CM:3"]
    # 已复核的同含义发现：结转复核态，不随新运行重置回「待医学复核」
    assert ae_after.status == "已医学复核"
    assert ae_after.unread is False
    # 未处置的发现保持待决策入口
    assert cm_after.status == "待医学复核"
    assert cm_after.needs_action is True
    assert cm_after.unread is True
    assert _module_needs_action(service) == 2


def test_meaning_change_returns_to_pending_review(tmp_path: Any) -> None:
    """医学含义变化的发现不沿用旧结论，重新进入待复核。"""

    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    _publish(repository, "r7-run-1", _packet())
    service = _service(tmp_path, repository)
    ae = next(item for item in _mm_items(service) if item.risk_key == "ae:AE:18")
    disposition_store = service.rux_disposition_store
    disposition_store.append(
        RuxRiskDispositionRecord(
            record_id="rec-disp-2",
            project_id=PROJECT_ID,
            item_id=ae.item_id,
            risk_id=ae.source_id,
            risk_key=ae.risk_key,
            risk_instance_id=ae.risk_instance_id,
            snapshot_id=ae.snapshot_id,
            subject_id="21009",
            rule_id="ae:AE:18",
            action=RuxRiskDispositionAction.REVIEWED,
            disposition_kind=None,
            previous_state="pending_review",
            new_state="reviewed",
            actor=ACTOR,
            source_version=ae.source_version,
            created_at=T0,
        )
    )

    # 新一轮运行中该发现医学依据变化（同一 risk_key）
    _publish(
        repository,
        "r7-run-3-changed",
        _packet(ae_rationale="源记录依据——严重度：3级；关系改为可能有关；新增暴露期矛盾提示。"),
    )
    ae_after = next(item for item in _mm_items(service) if item.risk_key == "ae:AE:18")
    assert ae_after.status == "待医学复核"
    assert ae_after.needs_action is True
    assert ae_after.unread is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
