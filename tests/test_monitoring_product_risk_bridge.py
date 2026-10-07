"""R24轮（R24-05）：r7产品发布链→聚合风险快照桥的回归测试。

发布链此前只落 frozen read model，聚合面（总看板风险摘要/模块开放风险
数/统一工作收件箱）读到的风险库恒空——已发布监查结果与总看板矛盾。
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

from packages.contracts.workbench_contracts.models import (  # noqa: E402
    RiskSeverity,
)
from services.api.app.medical_risk_repository import (  # noqa: E402
    MedicalRiskRepository,
)
from services.api.app.monitoring_product_risk_bridge import (  # noqa: E402
    PRODUCT_RISK_ENGINE_VERSION,
    product_packet_risk_cases,
    record_publication_risk_snapshot,
)

PROJECT_ID = "proj_user_bridge_test"
CREATED_AT = datetime(2026, 10, 7, 18, 0, tzinfo=timezone.utc)


def _packet() -> SimpleNamespace:
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
                medical_note="源记录依据——严重度：3级。",
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
            SimpleNamespace(
                locator_ref="loc-AE-000018",
                canonical_location="AE!row19",
            ),
            SimpleNamespace(
                locator_ref="loc-CM-000003",
                canonical_location="CM!row4",
            ),
        ],
    )


def test_bridge_maps_packet_risks_to_cases() -> None:
    cases = product_packet_risk_cases(
        _packet(),
        project_id=PROJECT_ID,
        source_revision="product-publication:r7-run-1",
        rule_profile_revision="r5-packet:abc",
        created_at=CREATED_AT,
    )
    assert len(cases) == 2
    by_key = {case.risk_key: case for case in cases}
    ae = by_key["ae:AE:18"]
    assert ae.severity is RiskSeverity.HIGH
    assert ae.subject_id == "21009"
    assert ae.title == "不良事件（受试者21009）"
    assert ae.rationale.startswith("源记录依据")
    assert ae.evidence_span_ids == ["AE!row19"]
    assert ae.engine_version == PRODUCT_RISK_ENGINE_VERSION
    cm = by_key["cm:CM:3"]
    assert cm.severity is RiskSeverity.MEDIUM
    assert cm.rationale == "基于已发布监查结果的风险发现，待医学复核。"


def test_record_is_deterministic_and_idempotent(tmp_path: Any) -> None:
    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    first = record_publication_risk_snapshot(
        project_id=PROJECT_ID,
        run_id="r7-run-1",
        packet=_packet(),
        risk_repository=repository,
        rule_profile_revision="r5-packet:abc",
        created_at=CREATED_AT,
    )
    second = record_publication_risk_snapshot(
        project_id=PROJECT_ID,
        run_id="r7-run-1",
        packet=_packet(),
        risk_repository=repository,
        rule_profile_revision="r5-packet:abc",
        created_at=CREATED_AT,
    )
    assert first["snapshot_id"] == second["snapshot_id"]
    assert first["risk_count"] == 2
    snapshot = repository.current_snapshot(PROJECT_ID)
    risks = repository.list_risks(PROJECT_ID, snapshot.snapshot_id)
    assert len(risks) == 2
    assert {risk.severity for risk in risks} == {
        RiskSeverity.HIGH,
        RiskSeverity.MEDIUM,
    }


class _ManifestService:
    def __init__(self, user_projects: set[str]) -> None:
        self._user_projects = user_projects

    def is_user_created_project(self, project_id: str) -> bool:
        return project_id in self._user_projects

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


def _inbox_service(
    tmp_path: Any,
    repository: MedicalRiskRepository,
) -> Any:
    from services.api.app.workbench_inbox import (
        WorkbenchInboxService,
        WorkbenchInboxStore,
    )

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
        project_source_manifest_service=_ManifestService({PROJECT_ID}),
        medical_risk_repository=repository,
    )


def test_published_snapshot_reaches_inbox(tmp_path: Any) -> None:
    """发布链写入快照后，统一收件箱出现医学监查待决策项。"""

    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    record_publication_risk_snapshot(
        project_id=PROJECT_ID,
        run_id="r7-run-1",
        packet=_packet(),
        risk_repository=repository,
        rule_profile_revision="r5-packet:abc",
        created_at=CREATED_AT,
    )
    service = _inbox_service(tmp_path, repository)
    items = service.monitoring_risk_items(PROJECT_ID)
    assert len(items) == 2
    assert all(item.module == "medical_monitoring" for item in items)
    assert {item.priority for item in items} == {"high", "medium"}
    assert any("21009" in (item.title or "") for item in items)


def test_unpublished_project_keeps_empty_inbox(tmp_path: Any) -> None:
    """从未发布的用户项目收件箱保持为空（无快照→无适配器）。"""

    repository = MedicalRiskRepository(tmp_path / "risks.sqlite3")
    service = _inbox_service(tmp_path, repository)
    assert service.monitoring_risk_items(PROJECT_ID) == []
