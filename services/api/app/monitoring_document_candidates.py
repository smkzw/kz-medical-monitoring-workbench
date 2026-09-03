from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

from openpyxl.utils.exceptions import InvalidFileException

from packages.contracts.workbench_contracts import WritingReferenceDocumentArtifact

from .listing_file_parser import parse_listing_file
from .writing_reference_docx import extract_docx_sections


CANDIDATE_MANIFEST_VERSION = "monitoring-document-candidate-v1"
MAX_EXCERPTS = 12
MAX_EXCERPT_CHARS = 500
MAX_OCR_PAGE_SAMPLES = 100
ROLE_HYPOTHESES_BY_SUFFIX = {
    ".xlsx": ("ecrf",),
    ".docx": ("protocol", "investigator_brochure", "sap"),
    ".pdf": ("investigator_brochure", "sap"),
}
MEDIA_TYPE_BY_SUFFIX = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}
LOCAL_PATH_SIGNAL_RE = re.compile(
    r"(?:file://|\\\\|\b[A-Za-z]:[\\/]|(?<![A-Za-z0-9])/[A-Za-z0-9._-]+)",
    re.IGNORECASE,
)


class CandidateMalformedInputError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateExcerpt:
    locator: str
    text: str
    text_sha256: str


@dataclass(frozen=True)
class CandidateSheetEvidence:
    locator: str
    sheet_name: str
    row_count: int
    headers: tuple[str, ...]
    visibility: str
    used_range: str
    parser_warnings: tuple[str, ...]


@dataclass(frozen=True)
class MonitoringDocumentCandidate:
    manifest_version: str
    candidate_id: str
    file_id: str
    filename: str
    content_sha256: str
    size_bytes: int
    media_type: str
    role_hypotheses: tuple[str, ...]
    parser_name: str
    parser_version: str
    technical_status: Literal["ready", "failed"]
    content_status: Literal["not_assessed"]
    use_status: Literal["candidate_only"]
    authority_status: Literal["not_promoted"]
    extraction_status: Literal["parsed", "needs_ocr", "unreadable"]
    page_count: int
    locator_count: int
    locator_index_sha256: str
    excerpts: tuple[CandidateExcerpt, ...] = ()
    sheets: tuple[CandidateSheetEvidence, ...] = ()
    zero_text_page_count: int = 0
    zero_text_page_samples: tuple[int, ...] = ()
    limitation_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MonitoringDocumentCandidateBatch:
    manifest_version: str
    batch_id: str
    candidates: tuple[MonitoringDocumentCandidate, ...]
    authority_status: Literal["not_adjudicated"] = "not_adjudicated"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class MonitoringDocumentCandidateDecomposer:
    """Create isolated structural evidence without selecting document authority."""

    def __init__(self, candidate_root: Path):
        self.candidate_root = Path(candidate_root)

    def decompose_many(
        self, files: list[tuple[str, bytes]]
    ) -> MonitoringDocumentCandidateBatch:
        candidates = tuple(
            sorted(
                (self.decompose(filename, content) for filename, content in files),
                key=lambda item: item.candidate_id,
            )
        )
        batch_digest = hashlib.sha256(
            _stable_json([candidate.candidate_id for candidate in candidates])
        ).hexdigest()
        batch = MonitoringDocumentCandidateBatch(
            manifest_version=CANDIDATE_MANIFEST_VERSION,
            batch_id=f"mmbatch_{batch_digest[:24]}",
            candidates=candidates,
        )
        self._persist_batch(batch)
        return batch

    def decompose(self, filename: str, content: bytes) -> MonitoringDocumentCandidate:
        safe_name = Path(str(filename).replace("\\", "/")).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ROLE_HYPOTHESES_BY_SUFFIX:
            raise ValueError("unsupported monitoring document candidate type")
        if not content:
            raise ValueError("monitoring document candidate is empty")

        content_sha256 = hashlib.sha256(content).hexdigest()
        file_id = f"mmfile_{content_sha256}"
        identity = _stable_json(
            {"content_sha256": content_sha256, "filename": safe_name}
        )
        candidate_id = "mmcandidate_" + hashlib.sha256(identity).hexdigest()[:24]
        self._persist_file(content_sha256, suffix, content)

        try:
            if suffix == ".xlsx":
                candidate = self._decompose_xlsx(
                    candidate_id, file_id, safe_name, content, content_sha256
                )
            else:
                candidate = self._decompose_text_document(
                    candidate_id, file_id, safe_name, content, content_sha256, suffix
                )
        except CandidateMalformedInputError:
            candidate = self._unreadable_candidate(
                candidate_id, file_id, safe_name, content_sha256, len(content), suffix
            )

        self._persist_manifest(candidate)
        return candidate

    def _decompose_xlsx(
        self,
        candidate_id: str,
        file_id: str,
        filename: str,
        content: bytes,
        content_sha256: str,
    ) -> MonitoringDocumentCandidate:
        _validate_ooxml_package(
            content,
            required_members=("[Content_Types].xml", "xl/workbook.xml"),
        )
        try:
            sheets = parse_listing_file(filename, content)
        except (
            EOFError,
            InvalidFileException,
            ValueError,
            ElementTree.ParseError,
            zipfile.BadZipFile,
        ) as exc:
            raise CandidateMalformedInputError("XLSX candidate cannot be parsed") from exc
        evidence = tuple(
            CandidateSheetEvidence(
                locator=f"xlsx:sheet:{index}",
                sheet_name=_bounded_text(sheet.sheet_name),
                row_count=len(sheet.rows),
                headers=(
                    tuple(_bounded_text(str(value)) for value in sheet.source_headers)
                    if sheet.header_detection_status == "detected" and sheet.rows
                    else ()
                ),
                visibility=str(sheet.sheet_visibility or "unknown"),
                used_range=str(sheet.used_range or ""),
                parser_warnings=tuple(
                    _bounded_text(value) for value in sheet.parser_warnings
                ),
            )
            for index, sheet in enumerate(sheets, start=1)
        )
        locators = [item.locator for item in evidence]
        parser_versions = sorted(
            {str(sheet.parser_version or "unknown") for sheet in sheets}
        )
        return MonitoringDocumentCandidate(
            manifest_version=CANDIDATE_MANIFEST_VERSION,
            candidate_id=candidate_id,
            file_id=file_id,
            filename=filename,
            content_sha256=content_sha256,
            size_bytes=len(content),
            media_type=MEDIA_TYPE_BY_SUFFIX[".xlsx"],
            role_hypotheses=ROLE_HYPOTHESES_BY_SUFFIX[".xlsx"],
            parser_name="listing_file_parser",
            parser_version="+".join(parser_versions),
            technical_status="ready",
            content_status="not_assessed",
            use_status="candidate_only",
            authority_status="not_promoted",
            extraction_status="parsed",
            page_count=0,
            locator_count=len(locators),
            locator_index_sha256=_locator_digest(locators),
            sheets=evidence,
        )

    def _decompose_text_document(
        self,
        candidate_id: str,
        file_id: str,
        filename: str,
        content: bytes,
        content_sha256: str,
        suffix: str,
    ) -> MonitoringDocumentCandidate:
        artifact = WritingReferenceDocumentArtifact(
            artifact_id=candidate_id,
            project_id="monitoring-document-candidate",
            snapshot_id="candidate-decomposition",
            nct_id="candidate",
            source_document_id=file_id,
            document_type="unresolved",
            filename=filename,
            requested_url="isolated-candidate",
            final_url="isolated-candidate",
            content_type=MEDIA_TYPE_BY_SUFFIX[suffix],
            declared_size=len(content),
            actual_size=len(content),
            content_sha256=content_sha256,
            source_status="user_uploaded",
            created_by="monitoring_candidate_decomposer",
            created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
        )
        if suffix == ".pdf":
            parser_name, parser_version, page_count, zero_text_pages, blocks = (
                _extract_pdf_candidate_blocks(content, candidate_id)
            )
        else:
            _validate_ooxml_package(
                content,
                required_members=("[Content_Types].xml", "word/document.xml"),
            )
            try:
                extracted = extract_docx_sections(content, artifact)
            except (EOFError, ValueError, ElementTree.ParseError) as exc:
                raise CandidateMalformedInputError(
                    "DOCX candidate cannot be parsed"
                ) from exc
            parser_name = extracted.parser_name
            parser_version = extracted.parser_version
            page_count = extracted.page_count
            zero_text_pages = extracted.zero_text_pages
            blocks = [
                (span.source_locator, span.source_text) for span in extracted.spans
            ]
        locators = [locator for locator, _text in blocks]
        excerpts = tuple(_candidate_excerpt(locator, text) for locator, text in blocks[:MAX_EXCERPTS])
        needs_ocr = suffix == ".pdf" and not blocks and bool(zero_text_pages)
        limitations = ("native_text_absent_ocr_required",) if needs_ocr else ()
        return MonitoringDocumentCandidate(
            manifest_version=CANDIDATE_MANIFEST_VERSION,
            candidate_id=candidate_id,
            file_id=file_id,
            filename=filename,
            content_sha256=content_sha256,
            size_bytes=len(content),
            media_type=MEDIA_TYPE_BY_SUFFIX[suffix],
            role_hypotheses=ROLE_HYPOTHESES_BY_SUFFIX[suffix],
            parser_name=parser_name,
            parser_version=parser_version,
            technical_status="ready",
            content_status="not_assessed",
            use_status="candidate_only",
            authority_status="not_promoted",
            extraction_status="needs_ocr" if needs_ocr else "parsed",
            page_count=page_count,
            locator_count=len(locators),
            locator_index_sha256=_locator_digest(locators),
            excerpts=excerpts,
            zero_text_page_count=len(zero_text_pages),
            zero_text_page_samples=tuple(zero_text_pages[:MAX_OCR_PAGE_SAMPLES]),
            limitation_codes=limitations,
        )

    def _unreadable_candidate(
        self,
        candidate_id: str,
        file_id: str,
        filename: str,
        content_sha256: str,
        size_bytes: int,
        suffix: str,
    ) -> MonitoringDocumentCandidate:
        return MonitoringDocumentCandidate(
            manifest_version=CANDIDATE_MANIFEST_VERSION,
            candidate_id=candidate_id,
            file_id=file_id,
            filename=filename,
            content_sha256=content_sha256,
            size_bytes=size_bytes,
            media_type=MEDIA_TYPE_BY_SUFFIX[suffix],
            role_hypotheses=ROLE_HYPOTHESES_BY_SUFFIX[suffix],
            parser_name="unavailable",
            parser_version="unavailable",
            technical_status="failed",
            content_status="not_assessed",
            use_status="candidate_only",
            authority_status="not_promoted",
            extraction_status="unreadable",
            page_count=0,
            locator_count=0,
            locator_index_sha256=_locator_digest([]),
            limitation_codes=("candidate_parse_failed",),
        )

    def _persist_file(self, content_sha256: str, suffix: str, content: bytes) -> None:
        path = self.candidate_root / "files" / f"{content_sha256}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != content_sha256:
                raise RuntimeError("isolated candidate file hash mismatch")
            return
        path.write_bytes(content)

    def _persist_manifest(self, candidate: MonitoringDocumentCandidate) -> None:
        path = self.candidate_root / "manifests" / f"{candidate.candidate_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _stable_json(candidate.to_dict()) + b"\n"
        if path.exists():
            if path.read_bytes() != payload:
                raise RuntimeError("immutable candidate manifest mismatch")
            return
        path.write_bytes(payload)

    def _persist_batch(self, batch: MonitoringDocumentCandidateBatch) -> None:
        path = self.candidate_root / "batches" / f"{batch.batch_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _stable_json(batch.to_dict()) + b"\n"
        if path.exists():
            if path.read_bytes() != payload:
                raise RuntimeError("immutable candidate batch mismatch")
            return
        path.write_bytes(payload)


def _bounded_text(value: str) -> str:
    stripped = value.strip()
    redacted = (
        "[local_path_redacted]"
        if LOCAL_PATH_SIGNAL_RE.search(stripped)
        else stripped
    )
    if len(redacted) <= MAX_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_EXCERPT_CHARS] + "...[truncated]"


def _candidate_excerpt(locator: str, source_text: str) -> CandidateExcerpt:
    text = _bounded_text(source_text)
    return CandidateExcerpt(
        locator=locator,
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _extract_pdf_candidate_blocks(
    payload: bytes, candidate_id: str
) -> tuple[str, str, int, list[int], list[tuple[str, str]]]:
    """Extract candidate-only native text without loading writing runtime services."""

    import pymupdf

    try:
        document = pymupdf.open(stream=payload, filetype="pdf")
    except pymupdf.FileDataError as exc:
        raise CandidateMalformedInputError("PDF candidate cannot be parsed") from exc
    try:
        if len(document) == 0 or len(document) > 2000:
            raise CandidateMalformedInputError(
                "PDF page count is outside the supported range"
            )
        blocks: list[tuple[str, str]] = []
        zero_text_pages: list[int] = []
        for page_number, page in enumerate(document, start=1):
            page_blocks = [
                re.sub(r"\s+", " ", str(block[4] or "")).strip()
                for block in page.get_text("blocks", sort=True)
                if len(block) >= 5
                and (len(block) < 7 or block[6] == 0)
                and str(block[4] or "").strip()
            ]
            if not page_blocks:
                zero_text_pages.append(page_number)
                continue
            blocks.extend(
                (
                    f"candidate:{candidate_id}:p{page_number}:b{block_index}",
                    text,
                )
                for block_index, text in enumerate(page_blocks)
            )
        version = f"pymupdf_{pymupdf.__version__}_candidate_blocks_v1"
        return "pymupdf_candidate_blocks", version, len(document), zero_text_pages, blocks
    finally:
        document.close()


def _validate_ooxml_package(
    payload: bytes, *, required_members: tuple[str, ...]
) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = set(archive.namelist())
    except (EOFError, zipfile.BadZipFile) as exc:
        raise CandidateMalformedInputError("OOXML candidate is not a ZIP package") from exc
    if any(member not in names for member in required_members):
        raise CandidateMalformedInputError("OOXML candidate is missing required parts")


def _locator_digest(locators: list[str]) -> str:
    return hashlib.sha256(_stable_json(locators)).hexdigest()


def _stable_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
