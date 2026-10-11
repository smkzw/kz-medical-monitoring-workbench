"""R32-05回归：缺eCRF配对不得被表述为「文件为扫描版或损坏」。

R32实测（report_C.md发现1/2）：用户声明「本次未提供电子病例报告表」后，
生成字段映射被证据门拒绝（此前code=mapping_document_evidence_incomplete），
界面/响应体文案却称「未能从这组文件中读取到可核对的内容（如全部为扫描
版或文件损坏）」——对已被系统成功识别为「研究方案：已识别」的合法docx
构成不实完整性指控。修复后：
- 配对未就绪走独立代码 ``mapping_document_evidence_roles_unmet``（422），
  消息如实指认「缺件」并明确与文件是否损坏无关；
- 旧 ``mapping_document_evidence_incomplete`` 不再由配对缺失路径触发，
  文案改为中性，不再包含扫描版/损坏指控。
"""

from __future__ import annotations

from packages.medical_monitoring.admission.document_evidence import (
    CurrentDocumentBinding,
    DocumentEvidenceError,
    DocumentRoleEvidence,
    MonitoringDocumentEvidencePacket,
    validate_document_evidence_packet,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    _MAPPING_MESSAGES,
    _MAPPING_STATUS_CODES,
    _mapping_error,
)


def _binding(role: str) -> CurrentDocumentBinding:
    return CurrentDocumentBinding(
        role=role,
        source_entry_id=f"source-{role}",
        source_revision=f"revision-{role}",
        content_sha256="c" * 64,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if role == "ecrf"
            else "application/pdf"
        ),
        parser_name="document-parser",
        parser_version="v1",
        validation_id=f"validation-{role}",
        validation_revision=1,
        validator_version="source-content-consistency-v2",
        validation_context_sha256="8" * 64,
        locator_index_sha256="f" * 64,
        locator_count=2,
        locator_samples=(f"{role}:page:1", f"{role}:page:2"),
        selection_basis="registry_current",
    )


def _packet(*, ecrf_current: bool) -> dict:
    # 角色清单必须按 DOCUMENT_ROLES 顺序完整在档：
    # (protocol, investigator_brochure, ecrf, sap)。
    records = [
        DocumentRoleEvidence(role="protocol", status="current", binding=_binding("protocol")),
        DocumentRoleEvidence(
            role="investigator_brochure",
            status="missing",
            limitation_codes=("investigator_brochure_not_registered",),
        ),
    ]
    if ecrf_current:
        records.append(
            DocumentRoleEvidence(role="ecrf", status="current", binding=_binding("ecrf")),
        )
    else:
        # 用户声明「本次未提供电子病例报告表」后的在档形态：missing+限制码。
        records.append(
            DocumentRoleEvidence(
                role="ecrf",
                status="missing",
                limitation_codes=("user_declared_missing",),
            ),
        )
    records.append(
        DocumentRoleEvidence(
            role="sap",
            status="missing",
            limitation_codes=("sap_not_registered",),
        ),
    )
    return MonitoringDocumentEvidencePacket(
        project_id="proj-r32-05",
        listing_admission_date="2026-10-10",
        registry_revision_sha256="a" * 64,
        roles=tuple(records),
    ).to_dict()


def test_missing_ecrf_declares_roles_unmet_not_file_corruption() -> None:
    try:
        validate_document_evidence_packet(
            _packet(ecrf_current=False),
            project_id="proj-r32-05",
            require_mapping_context=True,
        )
        raise AssertionError("expected DocumentEvidenceError")
    except DocumentEvidenceError as exc:
        assert exc.code == "mapping_document_evidence_roles_unmet"
        assert getattr(exc, "missing_roles", ()) == ("ecrf",)


def test_complete_pairing_passes_gate() -> None:
    result = validate_document_evidence_packet(
        _packet(ecrf_current=True),
        project_id="proj-r32-05",
        require_mapping_context=True,
    )
    assert result["mapping_context_ready"] is True


def test_route_error_copy_is_honest() -> None:
    response = _mapping_error("mapping_document_evidence_roles_unmet")
    assert response.status_code == 422
    message = _MAPPING_MESSAGES["mapping_document_evidence_roles_unmet"]
    # 不实指控句式必须消失；「与文件是否损坏无关」是澄清而非指控。
    for false_accusation in (
        "全部为扫描版或文件损坏",
        "未能从这组文件中读取到可核对的内容",
        "更换为可读取的文件版本",
    ):
        assert false_accusation not in message
    assert "扫描版" not in message
    assert "电子病例报告表" in message
    assert "已上传且识别成功的文件完好可用" in message
    # 旧代码保留兼容映射，但文案不再作不实指控。
    legacy = _MAPPING_MESSAGES["mapping_document_evidence_incomplete"]
    for false_accusation in (
        "全部为扫描版或文件损坏",
        "未能从这组文件中读取到可核对的内容",
    ):
        assert false_accusation not in legacy
    assert _MAPPING_STATUS_CODES["mapping_document_evidence_roles_unmet"] == 422
