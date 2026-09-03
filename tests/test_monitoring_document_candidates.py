from __future__ import annotations

import io
import json
from pathlib import Path

import docx
import openpyxl
import pymupdf
import pytest

import services.api.app.monitoring_document_candidates as candidates_module
from services.api.app.monitoring_document_candidates import (
    MonitoringDocumentCandidateDecomposer,
)


def _docx_bytes(*paragraphs: str) -> bytes:
    document = docx.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


def _xlsx_bytes() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "不良事件"
    sheet.append(["受试者编号", "事件名称", "严重程度"])
    sheet.append(["SUBJECT-SECRET", "HEADACHE", "MILD"])
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


def _pdf_bytes(*, text: str = "") -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    payload = document.tobytes()
    document.close()
    return payload


def _image_only_pdf_bytes() -> bytes:
    source = pymupdf.open()
    source_page = source.new_page(width=32, height=32)
    source_page.draw_rect(source_page.rect, fill=(0, 0, 0))
    image = source_page.get_pixmap().tobytes("png")
    source.close()
    document = pymupdf.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=image)
    payload = document.tobytes()
    document.close()
    return payload


def test_xlsx_candidate_exposes_structure_without_row_values(tmp_path: Path) -> None:
    decomposer = MonitoringDocumentCandidateDecomposer(tmp_path / "candidates")

    candidate = decomposer.decompose("/private/incoming/eCRF.xlsx", _xlsx_bytes())
    serialized = json.dumps(candidate.to_dict(), ensure_ascii=False)

    assert candidate.filename == "eCRF.xlsx"
    assert candidate.role_hypotheses == ("ecrf",)
    assert candidate.authority_status == "not_promoted"
    assert candidate.sheets[0].sheet_name == "不良事件"
    assert candidate.sheets[0].headers == ("受试者编号", "事件名称", "严重程度")
    assert "SUBJECT-SECRET" not in serialized
    assert "HEADACHE" not in serialized
    assert "/private/incoming" not in serialized


def test_candidate_metadata_redacts_paths_from_excel_structure(tmp_path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "路径检查"
    sheet.append(["/Users/example/source", r"C:\private\column"])
    sheet.append(["SECRET", "VALUE"])
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()

    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose(r"C:\private\ecrf.xlsx", stream.getvalue())
    serialized = json.dumps(candidate.to_dict(), ensure_ascii=False)

    assert candidate.filename == "ecrf.xlsx"
    assert "/Users/example" not in serialized
    assert r"C:\private" not in serialized
    assert "SECRET" not in serialized


def test_headerless_xlsx_does_not_expose_first_row_as_headers(tmp_path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["SUBJECT-SECRET", "HEADACHE", "MILD"])
    sheet.append(["SUBJECT-SECOND", "NAUSEA", "MODERATE"])
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()

    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose("headerless.xlsx", stream.getvalue())
    serialized = json.dumps(candidate.to_dict(), ensure_ascii=False)

    assert candidate.sheets[0].headers == ()
    assert "SUBJECT-SECRET" not in serialized
    assert "HEADACHE" not in serialized


def test_marker_like_headerless_values_are_not_exposed(tmp_path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["SUBJID", "SITEID", "VISIT"])
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()

    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose("headerless-markers.xlsx", stream.getvalue())

    assert candidate.sheets[0].headers == ()


def test_docx_candidate_is_deterministic_and_redacts_local_paths(tmp_path: Path) -> None:
    content = _docx_bytes(
        "研究方案摘要",
        "路径 /Users/example/a.docx /private/x/b.pdf /home/u/c.pdf ",
        r"/Volumes/data/d.pdf C:\private\e.docx \\server\share\f.pdf ",
        "file:///tmp/g.pdf 均仅用于定位。",
        r"/secret C:\Users\Alice Smith\h.docx \\server\shared folder\i.pdf",
        "file:///Users/Alice Smith/j.docx",
    )
    decomposer = MonitoringDocumentCandidateDecomposer(tmp_path / "candidates")

    first = decomposer.decompose("protocol.docx", content)
    second = decomposer.decompose("protocol.docx", content)

    assert first == second
    assert first.role_hypotheses == (
        "protocol",
        "investigator_brochure",
        "ecrf",
        "sap",
    )
    assert first.extraction_status == "parsed"
    assert first.locator_count == 6
    assert "[local_path_redacted]" in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "/Users/example" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "/private/x" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "/home/u" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "/Volumes/data" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert r"C:\private" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert r"\\server\share" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "file:///tmp" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "/secret" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "Alice Smith" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert "shared folder" not in json.dumps(first.to_dict(), ensure_ascii=False)
    assert len(list((tmp_path / "candidates" / "files").iterdir())) == 1
    assert len(list((tmp_path / "candidates" / "manifests").iterdir())) == 1


def test_pdf_candidate_distinguishes_native_text_from_ocr_need(tmp_path: Path) -> None:
    decomposer = MonitoringDocumentCandidateDecomposer(tmp_path / "candidates")

    native = decomposer.decompose("ib.pdf", _pdf_bytes(text="Investigator Brochure"))
    scanned = decomposer.decompose("sap.pdf", _pdf_bytes())

    assert native.extraction_status == "parsed"
    assert native.role_hypotheses == (
        "protocol",
        "investigator_brochure",
        "ecrf",
        "sap",
    )
    assert native.locator_count == 1
    assert scanned.extraction_status == "needs_ocr"
    assert scanned.technical_status == "ready"
    assert scanned.zero_text_page_count == 1
    assert scanned.limitation_codes == ("native_text_absent_ocr_required",)

    image_only = decomposer.decompose("scan.pdf", _image_only_pdf_bytes())
    assert image_only.extraction_status == "needs_ocr"
    assert image_only.locator_count == 0


def test_malformed_supported_file_is_retained_as_unreadable_candidate(
    tmp_path: Path,
) -> None:
    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose("unknown.pdf", b"not-a-pdf")

    assert candidate.extraction_status == "unreadable"
    assert candidate.technical_status == "failed"
    assert candidate.use_status == "candidate_only"
    assert candidate.limitation_codes == ("candidate_parse_failed",)


def test_malformed_xlsx_is_retained_as_unreadable_candidate(tmp_path: Path) -> None:
    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose("unknown.xlsx", b"not-an-xlsx")

    assert candidate.extraction_status == "unreadable"
    assert candidate.technical_status == "failed"
    manifest = tmp_path / "candidates" / "manifests" / f"{candidate.candidate_id}.json"
    assert manifest.exists()


def test_unexpected_parser_failure_is_not_persisted_as_file_damage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    decomposer = MonitoringDocumentCandidateDecomposer(tmp_path / "candidates")

    def fail_unexpectedly(*_args: object) -> None:
        raise RuntimeError("programming defect")

    monkeypatch.setattr(decomposer, "_decompose_xlsx", fail_unexpectedly)
    with pytest.raises(RuntimeError, match="programming defect"):
        decomposer.decompose("valid.xlsx", _xlsx_bytes())

    assert not (tmp_path / "candidates" / "manifests").exists()


def test_crc_damaged_xlsx_is_normalized_as_malformed_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_with_crc_error(*_args: object) -> None:
        raise candidates_module.zipfile.BadZipFile("bad CRC")

    monkeypatch.setattr(candidates_module, "parse_listing_file", fail_with_crc_error)
    candidate = MonitoringDocumentCandidateDecomposer(
        tmp_path / "candidates"
    ).decompose("damaged.xlsx", _xlsx_bytes())

    assert candidate.extraction_status == "unreadable"
    assert candidate.limitation_codes == ("candidate_parse_failed",)


def test_candidate_batch_identity_does_not_depend_on_upload_order(tmp_path: Path) -> None:
    files = [
        ("protocol.docx", _docx_bytes("Protocol")),
        ("ecrf.xlsx", _xlsx_bytes()),
    ]
    decomposer = MonitoringDocumentCandidateDecomposer(tmp_path / "candidates")

    first = decomposer.decompose_many(files)
    second = decomposer.decompose_many(list(reversed(files)))

    assert first == second
    assert first.authority_status == "not_adjudicated"
    assert [candidate.candidate_id for candidate in first.candidates] == sorted(
        candidate.candidate_id for candidate in first.candidates
    )
    persisted = json.loads(
        (
            tmp_path
            / "candidates"
            / "batches"
            / f"{first.batch_id}.json"
        ).read_text(encoding="utf-8")
    )
    assert persisted == json.loads(json.dumps(first.to_dict(), ensure_ascii=False))
