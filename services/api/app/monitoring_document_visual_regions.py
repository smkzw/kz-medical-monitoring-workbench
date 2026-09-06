"""Bounded visual-input extraction from frozen monitoring documents.

This module only turns still-current frozen documents into image bytes:

- PDF: renders an explicitly addressed page (zero-based ``page_index``) or a
  page-coordinate region (``bbox`` in PDF points, top-left origin) to PNG at
  a bounded dpi.  Out-of-range pages and out-of-page regions are rejected,
  never silently clipped to a smaller coverage.
- Word: returns the exact embedded bytes of the one image selected by its
  ``docx:drawing:...`` ``source_locator``.  An unknown locator is an error;
  no other image is ever substituted.

Every read re-verifies the current authority through
``resolver.assert_current_binding`` before and after the candidate file is
touched, and checks the candidate copy sha256 against
``binding.content_sha256``.

This is visual INPUT extraction only: no OCR, no image-semantics
completion, and no medical judgement happens here.  The downstream product
model owns every interpretation of the returned image.  Image bytes stay in
the typed result (excluded from ``repr``) and are never part of
``public_dict``, logs, or other JSON surfaces.
"""
from __future__ import annotations

import base64
import hashlib
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

from packages.medical_monitoring.admission.source_tools import SourceToolError
from packages.medical_monitoring.intelligence.primitives import content_hash

from .protocol_text_extractor import parse_protocol_docx


SCHEMA_VERSION = "mm-frozen-document-visual-input-v1"

_PDF_MEDIA_TYPE = "application/pdf"
_DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)

_DEFAULT_DPI = 150
_MIN_DPI = 36
_MAX_DPI = 300
_MAX_PAGE_INDEX = 10_000
_MAX_RENDER_PIXELS = 16_000_000
_MAX_IMAGE_BYTES = 10_000_000
_MAX_WORD_LOCATOR_LENGTH = 200
# Absorb float noise at page edges; anything clearly outside the page is
# rejected instead of clipped.
_PAGE_BOUND_TOLERANCE = 0.01

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_SEMANTIC_BOUNDARY_CODE = "visual_input_extract_only_no_ocr_or_semantics"


def _require_int(value: Any, *, minimum: int, maximum: int, code: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SourceToolError(code)
    return value


@dataclass(frozen=True)
class FrozenVisualImage:
    """Exact image bytes with the digest needed to verify them elsewhere.

    ``image_bytes`` is excluded from ``repr`` so logs and tracebacks can
    never carry the payload.
    """

    image_bytes: bytes = field(repr=False, compare=False)
    image_sha256: str
    media_type: str


@dataclass(frozen=True)
class VisualRegionExtraction:
    """One bounded visual input taken from a still-current frozen document.

    PDF renders carry page geometry; Word extractions carry the embedded
    part identity.  ``semantic_interpretation`` is always
    ``not_performed``: this module extracts pixels, it does not read them.
    """

    schema_version: str
    project_id: str
    input_revision_sha256: str
    source_entry_id: str
    source_content_sha256: str
    locator_index_sha256: str
    extraction_kind: str
    locator: str
    image: FrozenVisualImage
    page_size_points: Optional[Tuple[float, float]] = None
    requested_bbox: Optional[Tuple[float, float, float, float]] = None
    render_dpi: Optional[int] = None
    pixel_width: Optional[int] = None
    pixel_height: Optional[int] = None
    word_part_name: str = ""
    word_relationship_id: str = ""
    semantic_interpretation: str = "not_performed"
    limitation_codes: Tuple[str, ...] = ()
    extraction_sha256: str = ""

    def public_dict(self) -> Dict[str, Any]:
        """JSON-safe view of this extraction; image bytes are never included."""
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "input_revision_sha256": self.input_revision_sha256,
            "source_entry_id": self.source_entry_id,
            "source_content_sha256": self.source_content_sha256,
            "locator_index_sha256": self.locator_index_sha256,
            "extraction_kind": self.extraction_kind,
            "locator": self.locator,
            "image_sha256": self.image.image_sha256,
            "image_media_type": self.image.media_type,
            "page_size_points": (
                list(self.page_size_points) if self.page_size_points else None
            ),
            "requested_bbox": (
                list(self.requested_bbox) if self.requested_bbox else None
            ),
            "render_dpi": self.render_dpi,
            "pixel_width": self.pixel_width,
            "pixel_height": self.pixel_height,
            "word_part_name": self.word_part_name,
            "word_relationship_id": self.word_relationship_id,
            "semantic_interpretation": self.semantic_interpretation,
            "limitation_codes": list(self.limitation_codes),
            "extraction_sha256": self.extraction_sha256,
        }


class FrozenDocumentVisualRegionTools:
    """Read-only visual inputs from the monitoring candidate copy store."""

    def __init__(
        self,
        *,
        candidate_root: Path,
        project_id: str,
        input_revision: str,
        resolver: Any,
    ) -> None:
        self.candidate_root = Path(candidate_root)
        self.project_id = project_id
        self.input_revision = input_revision
        self.resolver = resolver

    def render_pdf_region(
        self,
        *,
        binding: Any,
        page_index: int,
        bbox: Optional[Sequence[float]] = None,
        dpi: int = _DEFAULT_DPI,
    ) -> VisualRegionExtraction:
        """Render one zero-based PDF page or page-coordinate region to PNG.

        ``bbox`` is ``(x0, y0, x1, y1)`` in PDF points on the page's
        top-left-origin coordinate space.  Without ``bbox`` the whole page
        is rendered.  Requests outside the page are rejected rather than
        cropped.
        """
        _require_int(
            page_index,
            minimum=0,
            maximum=_MAX_PAGE_INDEX,
            code="visual_page_index_out_of_range",
        )
        _require_int(
            dpi,
            minimum=_MIN_DPI,
            maximum=_MAX_DPI,
            code="visual_render_dpi_out_of_range",
        )
        self._assert_binding(binding)
        if str(binding.media_type) != _PDF_MEDIA_TYPE:
            raise SourceToolError("document_format_not_supported")
        content = self._read_frozen_copy(binding)
        import pymupdf

        with pymupdf.open(stream=content, filetype="pdf") as document:
            if not 0 <= page_index < len(document):
                raise SourceToolError("visual_page_index_out_of_range")
            page = document[page_index]
            page_rect = page.rect
            clip = _validated_bbox(bbox, page_rect)
            zoom = dpi / 72.0
            source_rect = clip if clip is not None else page_rect
            pixel_width = math.ceil(source_rect.width * zoom)
            pixel_height = math.ceil(source_rect.height * zoom)
            if (
                pixel_width < 1
                or pixel_height < 1
                or pixel_width * pixel_height > _MAX_RENDER_PIXELS
            ):
                raise SourceToolError("visual_region_pixel_budget_exceeded")
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(zoom, zoom),
                clip=clip,
                alpha=False,
            )
            png = pixmap.tobytes("png")
            actual_pixel_width = pixmap.width
            actual_pixel_height = pixmap.height
            if actual_pixel_width * actual_pixel_height > _MAX_RENDER_PIXELS:
                raise SourceToolError("visual_region_pixel_budget_exceeded")
        if not png.startswith(_PNG_MAGIC):
            raise SourceToolError("visual_region_render_invalid")
        if len(png) > _MAX_IMAGE_BYTES:
            raise SourceToolError("visual_region_bytes_budget_exceeded")
        if clip is None:
            locator = f"pdf:page:{page_index + 1}"
            extraction_kind = "pdf_page_render"
        else:
            locator = (
                f"pdf:page:{page_index + 1}:region:"
                f"{clip.x0:.2f},{clip.y0:.2f},{clip.x1:.2f},{clip.y1:.2f}"
            )
            extraction_kind = "pdf_region_render"
        result = VisualRegionExtraction(
            schema_version=SCHEMA_VERSION,
            project_id=self.project_id,
            input_revision_sha256=self.input_revision,
            source_entry_id=str(binding.source_entry_id),
            source_content_sha256=str(binding.content_sha256),
            locator_index_sha256=str(binding.locator_index_sha256),
            extraction_kind=extraction_kind,
            locator=locator,
            image=FrozenVisualImage(
                image_bytes=png,
                image_sha256=hashlib.sha256(png).hexdigest(),
                media_type="image/png",
            ),
            page_size_points=(page_rect.width, page_rect.height),
            requested_bbox=(
                (clip.x0, clip.y0, clip.x1, clip.y1)
                if clip is not None
                else None
            ),
            render_dpi=dpi,
            pixel_width=actual_pixel_width,
            pixel_height=actual_pixel_height,
            limitation_codes=(_SEMANTIC_BOUNDARY_CODE,),
        )
        self._assert_binding(binding)
        return _with_extraction_hash(result)

    def extract_word_embedded_image(
        self,
        *,
        binding: Any,
        source_locator: str,
    ) -> VisualRegionExtraction:
        """Return the exact embedded bytes of one Word image by locator.

        The locator must match exactly one embedded image of the parsed
        document.  Unknown locators raise instead of falling back to any
        other image.
        """
        locator = str(source_locator or "").strip()
        if not locator or len(locator) > _MAX_WORD_LOCATOR_LENGTH:
            raise SourceToolError("word_embedded_image_locator_unknown")
        self._assert_binding(binding)
        if str(binding.media_type) != _DOCX_MEDIA_TYPE:
            raise SourceToolError("document_format_not_supported")
        content = self._read_frozen_copy(binding)
        document = parse_protocol_docx("frozen.docx", content)
        matches = [
            image
            for image in document.embedded_images
            if image.source_locator == locator
        ]
        if len(matches) != 1:
            raise SourceToolError("word_embedded_image_locator_unknown")
        embedded = matches[0]
        image_bytes = base64.b64decode(embedded.image_base64, validate=True)
        if len(image_bytes) > _MAX_IMAGE_BYTES:
            raise SourceToolError("visual_region_bytes_budget_exceeded")
        if hashlib.sha256(image_bytes).hexdigest() != embedded.image_sha256:
            raise SourceToolError("word_embedded_image_hash_mismatch")
        result = VisualRegionExtraction(
            schema_version=SCHEMA_VERSION,
            project_id=self.project_id,
            input_revision_sha256=self.input_revision,
            source_entry_id=str(binding.source_entry_id),
            source_content_sha256=str(binding.content_sha256),
            locator_index_sha256=str(binding.locator_index_sha256),
            extraction_kind="word_embedded_image",
            locator=embedded.source_locator,
            image=FrozenVisualImage(
                image_bytes=image_bytes,
                image_sha256=embedded.image_sha256,
                media_type=embedded.media_type,
            ),
            word_part_name=embedded.part_name,
            word_relationship_id=embedded.relationship_id,
            limitation_codes=(
                "word_embedded_original_bytes_no_page_render",
                _SEMANTIC_BOUNDARY_CODE,
            ),
        )
        self._assert_binding(binding)
        return _with_extraction_hash(result)

    def _assert_binding(self, binding: Any) -> None:
        self.resolver.assert_current_binding(
            project_id=self.project_id,
            binding=binding,
        )

    def _read_frozen_copy(self, binding: Any) -> bytes:
        suffix = {
            _PDF_MEDIA_TYPE: ".pdf",
            _DOCX_MEDIA_TYPE: ".docx",
        }.get(str(binding.media_type))
        if suffix is None:
            raise SourceToolError("document_format_not_supported")
        path = self.candidate_root / "files" / (binding.content_sha256 + suffix)
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise SourceToolError("frozen_document_unavailable") from exc
        if hashlib.sha256(content).hexdigest() != binding.content_sha256:
            raise SourceToolError("frozen_document_content_changed")
        return content


def _validated_bbox(bbox: Any, page_rect: Any) -> Optional[Any]:
    if bbox is None:
        return None
    values = list(bbox)
    if len(values) != 4:
        raise SourceToolError("visual_region_invalid")
    coordinates = []
    for value in values:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise SourceToolError("visual_region_invalid")
        coordinates.append(float(value))
    x0, y0, x1, y1 = coordinates
    if x1 <= x0 or y1 <= y0:
        raise SourceToolError("visual_region_invalid")
    tolerance = _PAGE_BOUND_TOLERANCE
    if (
        x0 < page_rect.x0 - tolerance
        or y0 < page_rect.y0 - tolerance
        or x1 > page_rect.x1 + tolerance
        or y1 > page_rect.y1 + tolerance
    ):
        raise SourceToolError("visual_region_out_of_page_bounds")
    import pymupdf

    return pymupdf.Rect(x0, y0, x1, y1)


def _with_extraction_hash(
    result: VisualRegionExtraction,
) -> VisualRegionExtraction:
    payload = result.public_dict()
    payload.pop("extraction_sha256")
    return replace(result, extraction_sha256=content_hash(payload))


__all__ = [
    "FrozenDocumentVisualRegionTools",
    "FrozenVisualImage",
    "SCHEMA_VERSION",
    "VisualRegionExtraction",
]
