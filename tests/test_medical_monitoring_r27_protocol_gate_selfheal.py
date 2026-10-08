"""R27攻坚回归：方案版本门自愈必现挂（applicability_status 非法枚举）。

根因：``main._auto_register_confirmed_protocol_version``（R26-05 运行门
判定前的自愈）与 ``medical_monitoring_router`` GET /protocol-versions 的
R22-01 抽屉自愈都传 ``applicability_status="active"``——非法枚举（合法值
仅 version_date_only / project_effective_confirmed / site_specific，
``monitoring_protocol_rules.PROTOCOL_APPLICABILITY_STATUSES``），
``register_protocol_version`` 在 ``ProtocolSourceVersion.create`` 必抛
``MonitoringProtocolRuleError``；两处 ``except Exception: pass`` 把异常
静默吞掉 → 门照旧 409 protocol_version_required / 抽屉恒空。前端无
POST /protocol-versions 调用（medicalMonitoringApi.mjs 仅 GET 路径），
故已登记且内容校验通过的方案docx项目不存在任何用户可达的确认路径。

本文件用沙箱（tmp_path 注册表/校验库/规则库）直接驱动真实
``_r7_protocol_version_gate``，钉住该缺陷类：自愈必须真的种入
confirmed 版本并放行，而不是吞异常后 409。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from packages.contracts.workbench_contracts import (
    SourceContentValidationCheck,
    SourceContentValidationRecord,
    SourceRegistryEntry,
    SourceRegistrationResult,
)
from services.api.app import main as app_main
from services.api.app.monitoring_protocol_rule_repository import (
    MonitoringProtocolRuleRepository,
)
from services.api.app.monitoring_protocol_rules import (
    PROTOCOL_APPLICABILITY_STATUSES,
)
from services.api.app.monitoring_rule_authoring_service import (
    MonitoringRuleAuthoringService,
)
from services.api.app.source_content_validation import (
    SourceContentValidationService,
    SourceContentValidationStore,
)
from services.api.app.source_intake import (
    SourceRegistryService,
    SourceRegistryStore,
)

_PROJECT = "proj_r27_gate_selfheal"
_SHA = "ab" * 32


class _UnusedDependency:
    """register_protocol_version 路径不触达的构造参数占位。"""

    def __getattr__(self, name):  # pragma: no cover - 防误用
        raise RuntimeError(f"unexpected dependency access: {name}")


def _sandbox_authoring(tmp_path: Path) -> tuple[MonitoringRuleAuthoringService,
                                                MonitoringProtocolRuleRepository]:
    validation_service = SourceContentValidationService(
        SourceContentValidationStore(tmp_path / "source_content_validations.sqlite3")
    )
    registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "source_registry.jsonl"),
        allowed_roots=[tmp_path],
        artifact_root=tmp_path / "source_artifacts",
        content_validation_service=validation_service,
    )
    repo = MonitoringProtocolRuleRepository(tmp_path / "monitoring_protocol_rules.sqlite3")
    authoring = MonitoringRuleAuthoringService(
        repository=repo,
        lifecycle_service=_UnusedDependency(),
        protocol_rule_service=_UnusedDependency(),
        ai_repository=_UnusedDependency(),
        source_registry=registry,
    )
    return authoring, repo


def _register_validated_protocol_docx(
    authoring: MonitoringRuleAuthoringService,
    *,
    entry_id: str = "src_r27_protocol_docx_0001",
    use_status: str = "allowed",
) -> str:
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    entry = SourceRegistryEntry(
        entry_id=entry_id,
        project_id=_PROJECT,
        module="medical_monitoring",
        source_kind="protocol_docx",
        public_title="R27攻坚_临床研究方案_V1.0.docx",
        content_hash=_SHA,
        size_bytes=1024,
        parser_status="parsed",
        created_at=now,
    )
    authoring.source_registry.store.append(SourceRegistrationResult(entry=entry))
    record = SourceContentValidationRecord(
        validation_id=f"srcval_{entry_id}",
        project_id=_PROJECT,
        source_entry_id=entry_id,
        module="medical_monitoring",
        revision=1,
        technical_status="ready",
        content_status="matched",
        use_status=use_status,
        file_sha256=_SHA,
        expected_context_hash=_SHA,
        checks=[
            SourceContentValidationCheck(
                check_code="technical_readability",
                label="文件技术可读性",
                observed_value="DOCX可读取",
                outcome="match",
                overridable=False,
            )
        ],
        summary="文件基本信息与当前项目使用场景一致。",
        actor="system_validator",
        created_at=now,
    )
    authoring.source_registry.content_validation_service.store.save_assessment(
        record
    )
    return entry_id


def test_r27_gate_self_heal_registers_confirmed_version_and_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """已核验（parsed+ready+allowed）的方案docx：运行门自愈必须种入
    confirmed 方案版本并放行（返回None），而不是吞掉非法枚举异常后409。"""

    authoring, repo = _sandbox_authoring(tmp_path)
    entry_id = _register_validated_protocol_docx(authoring)
    monkeypatch.setattr(app_main, "monitoring_rule_authoring_service", authoring)
    monkeypatch.setattr(app_main, "monitoring_protocol_rule_repository", repo)

    # 修复前：register 必抛 MonitoringProtocolRuleError（applicability_status
    # ="active" 非法），被 except Exception: pass 吞掉 → 本断言拿到 409 dict。
    assert app_main._r7_protocol_version_gate(_PROJECT) is None

    versions = list(repo.list_protocol_versions(_PROJECT))
    assert len(versions) == 1
    version = versions[0]
    assert version.status == "confirmed"
    assert version.source_entry_id == entry_id
    # 注册值必须是合法枚举成员（缺陷本体），且与传入的生效日语义一致。
    assert version.applicability_status in PROTOCOL_APPLICABILITY_STATUSES
    assert version.applicability_status == "project_effective_confirmed"
    assert version.operational_effective_from != ""

    # 幂等：同项目再次过门不重复注册（R22-01承诺的幂等自愈）。
    assert app_main._r7_protocol_version_gate(_PROJECT) is None
    assert len(list(repo.list_protocol_versions(_PROJECT))) == 1


def test_r27_gate_still_fails_closed_without_parsed_protocol_docx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """无方案docx来源时门保持 fail-closed 409（修复不得放宽门禁）。"""

    authoring, repo = _sandbox_authoring(tmp_path)
    monkeypatch.setattr(app_main, "monitoring_rule_authoring_service", authoring)
    monkeypatch.setattr(app_main, "monitoring_protocol_rule_repository", repo)

    blocked = app_main._r7_protocol_version_gate(_PROJECT)

    assert blocked is not None
    assert blocked["code"] == "protocol_version_required"
    assert list(repo.list_protocol_versions(_PROJECT)) == []
