"""R38轮（R38-03）回归：方案事实与规则发布准备核对报英文错误。

根因：研究文件按内容幂等登记（同内容=同entry_id），内容一致性校验只在
登记时计算；项目登记信息（registered_project_identifiers，R35-02引入）
在登记后发生变更时，已存校验的expected_context_hash过期→证据检索的
可用性门把全部候选判为不可用→直出英文内部诊断
「registered document authority is incomplete for evidence search」，
「重新读取」原样重现且无恢复指引。

修复后契约：
1. 过期场景给中文如实归因+指向真实恢复路径（重新核对研究文件=重新登记
   并刷新校验）；
2. 重新登记同一内容（重新核对/重传路径）后校验刷新，检索恢复可用；
3. 英文内部诊断不再直出。
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest

from services.api.app.source_content_validation import (
    SourceContentValidationService,
    SourceContentValidationStore,
    SourceContentValidationConfirmationRequest,
    SourceExpectedContext,
)
from services.api.app.source_intake import (
    SourceRegistryService,
    SourceRegistryStore,
)

from tests.test_source_registry import _minimal_docx_bytes

PROJECT_ID = "proj-user-evidence-stale"


def _confirm_current_warning(registry: SourceRegistryService, entry_id: str) -> None:
    """最小夹具的文件角色证据偏弱会产生可确认warning——按真实界面流程确认。"""

    validation = registry.current_content_validation(PROJECT_ID, entry_id)
    registry.content_validation_service.confirm_after_warning(
        PROJECT_ID,
        entry_id,
        SourceContentValidationConfirmationRequest(
            reason="测试夹具：确认为研究方案",
            acknowledged_check_codes=[
                check.check_code
                for check in validation.checks
                if check.outcome == "warning"
            ],
            expected_revision=validation.revision,
            idempotency_key=f"test-confirm-{entry_id}-{validation.revision}",
        ),
    )


def _registry(
    tmp_path: Path, state: dict[str, Any]
) -> SourceRegistryService:
    def resolver(project_id: str, module: str, source_kind: str):
        return SourceExpectedContext(
            project_identifiers=tuple(state.get("identifiers", ())),
            expected_file_role=(
                "protocol" if source_kind == "protocol_docx" else ""
            ),
            registered_project_identifiers=tuple(
                state.get("registered_identifiers", ())
            ),
        )

    return SourceRegistryService(
        SourceRegistryStore(tmp_path / "registry.jsonl"),
        content_validation_service=SourceContentValidationService(
            SourceContentValidationStore(tmp_path / "validations.sqlite3")
        ),
        expected_context_resolver=resolver,
    )


def test_stale_validation_reports_honestly_and_recovers_after_reregistration(
    tmp_path,
) -> None:
    state: dict[str, Any] = {"registered_identifiers": ("CMS-D001",)}
    registry = _registry(tmp_path, state)
    docx_bytes = _minimal_docx_bytes()

    result = registry.register_monitoring_mapping_document(
        PROJECT_ID,
        "protocol.docx",
        docx_bytes,
        document_role="protocol",
    )
    entry_id = result.entry.entry_id
    _confirm_current_warning(registry, entry_id)

    # 登记时校验与当前基准一致：证据检索正常（不因可用性门失败）。
    registry.search_document_spans(PROJECT_ID, entry_id, ["知情同意"], limit=5)

    # 项目登记信息在登记后扩充（如补登记方案编号）→ 旧校验过期。
    state["registered_identifiers"] = ("CMS-D001", "PROTO-2026-01")
    with pytest.raises(ValueError) as excinfo:
        registry.search_document_spans(
            PROJECT_ID, entry_id, ["知情同意"], limit=5
        )
    message = str(excinfo.value)
    assert "registered document authority is incomplete" not in message
    assert "内容一致性校验" in message
    assert "重新核对研究文件" in message

    # 重新登记同一内容（重新核对/重传的真实效果）：校验按当前基准刷新，
    # 确认后检索恢复。
    registry.register_monitoring_mapping_document(
        PROJECT_ID,
        "protocol.docx",
        docx_bytes,
        document_role="protocol",
    )
    _confirm_current_warning(registry, entry_id)
    registry.search_document_spans(PROJECT_ID, entry_id, ["知情同意"], limit=5)
