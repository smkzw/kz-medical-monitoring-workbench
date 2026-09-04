from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal
from xml.etree import ElementTree

from openpyxl.utils.exceptions import InvalidFileException

from packages.contracts.workbench_contracts import WritingReferenceDocumentArtifact

from .listing_file_parser import parse_listing_file
from .writing_reference_docx import extract_docx_sections


CANDIDATE_MANIFEST_VERSION = "monitoring-document-candidate-v1"
MAX_EXCERPTS = 12
MAX_EXCERPT_CHARS = 500
MAX_OCR_PAGE_SAMPLES = 100
MAX_CONTENT_FINGERPRINTS = 128
ROLE_HYPOTHESES_BY_SUFFIX = {
    ".xlsx": ("ecrf",),
    ".docx": ("protocol", "investigator_brochure", "ecrf", "sap"),
    ".pdf": ("protocol", "investigator_brochure", "ecrf", "sap"),
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


class CandidateOcrUnavailableError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        requested_model: str = "",
        provider: str = "",
    ) -> None:
        super().__init__(message)
        self.requested_model = requested_model
        self.provider = provider


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
class CandidateOcrPageEvidence:
    page_number: int
    dpi: int
    image_sha256: str
    locator: str
    requested_model: str
    actual_model: str
    provider: str
    fell_back: bool
    status: Literal["recovered", "empty", "failed"]
    failure_code: str
    text_sha256: str
    character_count: int


@dataclass(frozen=True)
class CandidateContentProfile:
    normalized_text_sha256: str
    normalized_character_count: int
    represented_locator_count: int
    represented_page_count: int
    total_page_count: int
    represented_coverage_per_mille: int
    fingerprint_sha256: tuple[str, ...]


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
    ocr_recovery_pages: tuple[CandidateOcrPageEvidence, ...] = ()
    limitation_codes: tuple[str, ...] = ()
    evidence_revision_sha256: str = ""
    content_profile: CandidateContentProfile | None = None

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

    def __init__(
        self,
        candidate_root: Path,
        *,
        ocr_runner: Callable[[int, int, str, bytes], Any] | None = None,
        ocr_model: str = "GLM-OCR-bf16",
        ocr_dpi: int = 200,
    ):
        self.candidate_root = Path(candidate_root)
        self.ocr_runner = ocr_runner
        self.ocr_model = str(ocr_model).strip()
        self.ocr_dpi = int(ocr_dpi)
        if self.ocr_runner is not None and (
            not self.ocr_model or self.ocr_dpi < 200
        ):
            raise ValueError("monitoring candidate OCR configuration is invalid")

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
            _stable_json([
                {
                    "candidate_id": candidate.candidate_id,
                    "evidence_revision_sha256": candidate.evidence_revision_sha256,
                }
                for candidate in candidates
            ])
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

        candidate = replace(
            candidate,
            evidence_revision_sha256=_candidate_evidence_revision(candidate),
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
        profile_blocks = []
        for index, (sheet, item) in enumerate(zip(sheets, evidence), start=1):
            profile_blocks.append(
                (item.locator, " ".join((item.sheet_name, *item.headers)))
            )
            profile_blocks.extend(
                (
                    f"xlsx:sheet:{index}:row:{row_number}",
                    json.dumps(row, ensure_ascii=False, sort_keys=True),
                )
                for row_number, row in zip(sheet.row_numbers, sheet.rows)
            )
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
            content_profile=_content_profile(profile_blocks, page_count=0),
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
            all_blocks = list(blocks)
            ocr_evidence: tuple[CandidateOcrPageEvidence, ...] = ()
            ocr_page_limit = (
                min(len(zero_text_pages), MAX_EXCERPTS)
                if self.ocr_runner is not None
                else 0
            )
            blocks = blocks[: MAX_EXCERPTS - ocr_page_limit]
            if zero_text_pages and ocr_page_limit:
                recovered, ocr_evidence = _recover_pdf_candidate_pages(
                    content,
                    candidate_id,
                    zero_text_pages[:ocr_page_limit],
                    runner=self.ocr_runner,
                    model=self.ocr_model,
                    dpi=self.ocr_dpi,
                )
                blocks.extend(recovered)
                all_blocks.extend(recovered)
                parser_version += "+page_ocr_v1"
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
            all_blocks = [
                (span.source_locator, span.source_text) for span in extracted.spans
            ]
            blocks = all_blocks[:MAX_EXCERPTS]
            ocr_evidence = ()
        locators = [locator for locator, _text in blocks]
        excerpts = tuple(_candidate_excerpt(locator, text) for locator, text in blocks[:MAX_EXCERPTS])
        recovered_pages = {
            item.page_number for item in ocr_evidence if item.status == "recovered"
        }
        unresolved_ocr_pages = set(zero_text_pages) - recovered_pages
        needs_ocr = suffix == ".pdf" and bool(unresolved_ocr_pages)
        if not needs_ocr:
            limitations: tuple[str, ...] = ()
        elif self.ocr_runner is None:
            limitations = ("native_text_absent_ocr_required",)
        elif any(item.status == "failed" for item in ocr_evidence):
            limitations = ("ocr_recovery_failed",)
        elif len(ocr_evidence) < len(zero_text_pages):
            limitations = ("ocr_evidence_budget_exhausted",)
        else:
            limitations = ("ocr_recovery_empty",)
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
            ocr_recovery_pages=ocr_evidence,
            limitation_codes=limitations,
            content_profile=_content_profile(all_blocks, page_count=page_count),
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
        path = (
            self.candidate_root
            / "manifests"
            / candidate.candidate_id
            / f"{candidate.evidence_revision_sha256}.json"
        )
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
    redacted = _redact_local_path_suffix(value)
    if len(redacted) <= MAX_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_EXCERPT_CHARS] + "...[truncated]"


def _redact_local_path_suffix(value: str) -> str:
    stripped = value.strip()
    match = LOCAL_PATH_SIGNAL_RE.search(stripped)
    if match is None:
        redacted = stripped
    else:
        prefix = stripped[: match.start()].strip(" \t:：-—")
        redacted = (
            f"{prefix} [local_path_redacted]"
            if _has_substantive_text(prefix)
            else "[local_path_redacted]"
        )
    return redacted


def _candidate_excerpt(locator: str, source_text: str) -> CandidateExcerpt:
    text = _bounded_text(source_text)
    return CandidateExcerpt(
        locator=locator,
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _has_substantive_text(value: str) -> bool:
    return bool(re.search(r"[A-Za-z0-9\u3400-\u9fff]", value)) and value != (
        "[local_path_redacted]"
    )


def _normalize_content_text(value: str) -> str:
    return " ".join(
        re.findall(r"[a-z0-9]+|[\u3400-\u9fff]", value.casefold())
    )


def _content_profile(
    blocks: list[tuple[str, str]], *, page_count: int
) -> CandidateContentProfile:
    normalized_blocks = [
        _normalize_content_text(_redact_local_path_suffix(text))
        for _locator, text in blocks
        if _has_substantive_text(_redact_local_path_suffix(text))
    ]
    normalized_text = " ".join(value for value in normalized_blocks if value)
    tokens = normalized_text.split()
    fingerprints = {
        hashlib.sha256(" ".join(tokens[index : index + 5]).encode("utf-8")).hexdigest()
        for index in range(max(0, len(tokens) - 4))
    }
    represented_pages = {
        int(match.group(1))
        for locator, _text in blocks
        if (match := re.search(r":p([0-9]+)(?::|$)", locator))
    }
    represented_count = len(represented_pages)
    coverage = (
        min(1000, represented_count * 1000 // page_count)
        if page_count > 0
        else (1000 if normalized_text else 0)
    )
    return CandidateContentProfile(
        normalized_text_sha256=hashlib.sha256(
            normalized_text.encode("utf-8")
        ).hexdigest(),
        normalized_character_count=len(normalized_text),
        represented_locator_count=len(blocks),
        represented_page_count=represented_count,
        total_page_count=page_count,
        represented_coverage_per_mille=coverage,
        fingerprint_sha256=tuple(sorted(fingerprints)[:MAX_CONTENT_FINGERPRINTS]),
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


def _recover_pdf_candidate_pages(
    payload: bytes,
    candidate_id: str,
    page_numbers: list[int],
    *,
    runner: Callable[[int, int, str, bytes], Any],
    model: str,
    dpi: int,
) -> tuple[list[tuple[str, str]], tuple[CandidateOcrPageEvidence, ...]]:
    """Recover native-zero PDF pages without changing file-bound identity."""

    import pymupdf

    document = pymupdf.open(stream=payload, filetype="pdf")
    blocks: list[tuple[str, str]] = []
    evidence: list[CandidateOcrPageEvidence] = []
    try:
        for page_number in page_numbers:
            image_bytes = document[page_number - 1].get_pixmap(dpi=dpi).tobytes("png")
            image_sha256 = hashlib.sha256(image_bytes).hexdigest()
            try:
                result = runner(page_number, dpi, model, image_bytes)
                text = _bounded_text(re.sub(
                    r"\s+", " ", str(getattr(result, "text", result) or "")
                ).strip())
                if not _has_substantive_text(text):
                    text = ""
                status: Literal["recovered", "empty", "failed"] = (
                    "recovered" if text else "empty"
                )
                actual_model = str(getattr(result, "model", model) or model)
                provider = str(getattr(result, "provider", "") or "")
                fell_back = bool(getattr(result, "fell_back", False))
                failure_code = ""
            except CandidateOcrUnavailableError as exc:
                text = ""
                status = "failed"
                model = exc.requested_model or model
                actual_model = ""
                provider = exc.provider
                fell_back = False
                failure_code = "ocr_runtime_unavailable"
            locator = (
                f"candidate:{candidate_id}:p{page_number}:ocr" if text else ""
            )
            text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            evidence.append(
                CandidateOcrPageEvidence(
                    page_number=page_number,
                    dpi=dpi,
                    image_sha256=image_sha256,
                    locator=locator,
                    requested_model=str(
                        getattr(result, "requested_model", model) or model
                    ) if status != "failed" else model,
                    actual_model=actual_model,
                    provider=provider,
                    fell_back=fell_back,
                    status=status,
                    failure_code=failure_code,
                    text_sha256=text_sha256,
                    character_count=len(text),
                )
            )
            if text:
                blocks.append((locator, text))
    finally:
        document.close()
    return blocks, tuple(evidence)


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


def _candidate_evidence_revision(candidate: MonitoringDocumentCandidate) -> str:
    payload = candidate.to_dict()
    payload.pop("evidence_revision_sha256", None)
    return hashlib.sha256(_stable_json(payload)).hexdigest()


def _stable_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
