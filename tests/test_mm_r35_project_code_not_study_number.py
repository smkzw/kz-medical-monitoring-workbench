"""R35轮（R35-02）：项目管理代号尾段不得被误当研究编号做内容比对。

R35B实测（report_B.md发现2）：项目名「MX循R35B-RUX」的尾段R35B-RUX被
`_study_code_tokens` 从项目名挖出成为唯一期望标识，与文件名/正文中真实
方案号RUX-03-002比对，对两份与项目完全匹配的文件（方案docx、eCRF pdf）
各生成一条「文件内容与当前项目不一致」假阳性差异；差异卡「当前项目：
R35B-RUX」对CRA有语义误导——管理代号≠研究编号。

修复：SourceExpectedContext新增registered_project_identifiers（建项登记的
项目代号/方案编号）；「不一致」结论只在登记基准存在且全部缺席时成立；
仅名称启发式token未命中降为warning（提示）。
"""

from __future__ import annotations

import docx
import io

from services.api.app.protocol_text_extractor import parse_protocol_docx
from services.api.app.source_content_validation import (
    SourceContentValidationService,
    SourceContentValidationStore,
    SourceExpectedContext,
)


def _protocol_bytes(*paragraphs: str) -> bytes:
    document = docx.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _assess(expected: SourceExpectedContext, *, filename: str, title_line: str):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = SourceContentValidationStore(Path(tmp) / "state.sqlite3")
        service = SourceContentValidationService(store)
        content = _protocol_bytes(
            title_line,
            "研究设计",
            "入选标准",
            "排除标准",
        )
        document = parse_protocol_docx(filename, content)
        return service.assess_protocol(
            project_id="proj_r35b",
            source_entry_id="src_r35b_protocol",
            module="medical_monitoring",
            filename=filename,
            file_sha256="7" * 64,
            document=document,
            expected=expected,
            actor="system_validator",
        )


def _project_check(record):
    return {check.check_code: check for check in record.checks}["project_identity"]


def test_management_code_only_expectation_cannot_produce_mismatch() -> None:
    """唯一期望值来自项目名尾段（管理代号）时，真实方案文件只能是提示。"""

    record = _assess(
        SourceExpectedContext(
            # 名称挖出的管理代号token（旧实现唯一比对基准）
            project_identifiers=("R35B-RUX",),
            indication_terms=("慢性自发性荨麻疹",),
            expected_file_role="protocol_docx",
            expected_protocol_version="V1.3",
            # 建项未登记方案编号/项目代号 → 登记基准为空
            registered_project_identifiers=(),
        ),
        filename="MG-K10-CSU-001_临床研究方案_V1.3.docx",
        title_line="MG-K10-CSU-001 临床研究方案",
    )
    check = _project_check(record)
    assert check.outcome == "warning"
    assert "RUX-03-002" in "MG-K10-CSU-001 临床研究方案" or check.observed_value
    assert record.content_status != "mismatch"


def test_registered_identifier_absence_still_produces_mismatch() -> None:
    """登记基准（项目代号/方案编号）存在且全部缺席 → 维持「不一致」。"""

    record = _assess(
        SourceExpectedContext(
            project_identifiers=("RUX-03-002",),
            indication_terms=(),
            expected_file_role="protocol_docx",
            expected_protocol_version="",
            registered_project_identifiers=("RUX-03-002",),
        ),
        filename="CMS-D001_protocol.docx",
        title_line="CMS-D001 银屑病临床研究方案",
    )
    assert _project_check(record).outcome == "mismatch"


def test_registered_identifier_match_still_produces_match() -> None:
    record = _assess(
        SourceExpectedContext(
            project_identifiers=("RUX-03-002", "R35B-RUX"),
            indication_terms=(),
            expected_file_role="protocol_docx",
            expected_protocol_version="",
            registered_project_identifiers=("RUX-03-002",),
        ),
        filename="RUX-03-002_protocol.docx",
        title_line="RUX-03-002 临床研究方案",
    )
    assert _project_check(record).outcome == "match"


def test_listing_project_check_demotes_management_code_only_to_warning() -> None:
    """数据表STUDYID与登记基准不兼容才判不一致；管理代号未命中降为提示。"""

    check = SourceContentValidationService._listing_project_check(
        [{"studyid": "RUX-03-002"}],
        ("R35B-RUX",),
        "edc_data_listing",
        registered_identifiers=(),
    )
    assert check.outcome == "warning"

    mismatch = SourceContentValidationService._listing_project_check(
        [{"studyid": "RUX-03-002"}],
        ("R35B-RUX",),
        "edc_data_listing",
        registered_identifiers=("CMS-D001",),
    )
    assert mismatch.outcome == "mismatch"

    match = SourceContentValidationService._listing_project_check(
        [{"studyid": "RUX-03-002"}],
        ("RUX-03-002", "R35B-RUX"),
        "edc_data_listing",
        registered_identifiers=("RUX-03-002",),
    )
    assert match.outcome == "match"
