"""Composition of source readers available to one product model job."""
from contextlib import contextmanager
from pathlib import Path

from packages.medical_monitoring.admission.document_evidence import MonitoringDocumentEvidencePacket
from packages.medical_monitoring.admission.source_tools import FrozenListingEvidenceTools, SourceToolError
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME


def _schema(properties, required):
    return {"type": "object", "properties": properties, "required": required,
            "additionalProperties": False}


class MonitoringEvidenceToolset:
    def __init__(self, reader, *, document_resolver=None, document_reader=None, visual_reader=None):
        self.reader = reader
        self.document_resolver = document_resolver
        self.document_reader = document_reader
        self.visual_reader = visual_reader
        self.visual_inputs = {}
        self.schemas = {
            "sample_rows": _schema({
                "table_binding_id": {"type": "string"},
                "filter_column_index": {"type": "integer", "minimum": 0},
                "raw_value": {},
                "column_indexes": {"type": "array", "minItems": 1, "maxItems": 12,
                                   "items": {"type": "integer", "minimum": 0}},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 12, "default": 12},
            }, ["table_binding_id", "filter_column_index", "raw_value", "column_indexes"]),
            "read_source_region": _schema({
                "table_binding_id": {"type": "string"},
                "row_start": {"type": "integer", "minimum": 0, "default": 0},
                "row_count": {"type": "integer", "minimum": 1, "maximum": 40, "default": 20},
                "column_indexes": {"type": "array", "minItems": 1, "maxItems": 12,
                                   "items": {"type": "integer", "minimum": 0}},
            }, ["table_binding_id", "column_indexes"]),
            "get_column_profile": _schema({
                "table_binding_id": {"type": "string"},
                "column_index": {"type": "integer", "minimum": 0},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }, ["table_binding_id", "column_index"]),
        }
        self.document_bindings = {}
        document_packet = reader.profile.get("document_evidence")
        if document_resolver is not None and document_packet:
            packet = MonitoringDocumentEvidencePacket.from_dict(document_packet)
            if packet.project_id != reader.project_id:
                raise SourceToolError("source_read_identity_mismatch")
            for role in packet.roles:
                if role.status != "current" or role.binding is None:
                    continue
                for binding in (role.binding, *role.supplementary_bindings):
                    self.document_bindings[binding.source_entry_id] = binding
            if self.document_bindings:
                if visual_reader is not None:
                    self.schemas["render_pdf_region"] = _schema({
                        "source_entry_id": {"type": "string", "enum": sorted(self.document_bindings)},
                        "page_index": {"type": "integer", "minimum": 0},
                        "bbox": {"type": "array", "minItems": 4, "maxItems": 4,
                                 "items": {"type": "number"}},
                        "dpi": {"type": "integer", "minimum": 36, "maximum": 300, "default": 150},
                    }, ["source_entry_id", "page_index"])
                    self.schemas["extract_word_embedded_image"] = _schema({
                        "source_entry_id": {"type": "string", "enum": sorted(self.document_bindings)},
                        "source_locator": {"type": "string"},
                    }, ["source_entry_id", "source_locator"])
                if document_reader is not None:
                    self.schemas["read_document_units"] = _schema({
                        "source_entry_id": {"type": "string", "enum": sorted(self.document_bindings)},
                        "offset": {"type": "integer", "minimum": 0, "default": 0},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 8, "default": 4},
                        "text_offset": {"type": "integer", "minimum": 0, "default": 0},
                        "text_limit": {"type": "integer", "minimum": 1, "maximum": 24000, "default": 16000},
                        "column_start": {"type": "integer", "minimum": 0, "default": 0},
                        "column_count": {"type": "integer", "minimum": 1, "maximum": 24, "default": 12},
                    }, ["source_entry_id"])
                self.schemas["search_document"] = _schema({
                    "source_entry_id": {"type": "string", "enum": sorted(self.document_bindings)},
                    "query_terms": {"type": "array", "minItems": 1, "maxItems": 12,
                                    "items": {"type": "string"}},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 24, "default": 12},
                }, ["source_entry_id", "query_terms"])

    def execute(self, name, arguments):
        if name not in self.schemas or not isinstance(arguments, dict):
            raise SourceToolError("source_tool_not_available")
        schema = self.schemas[name]
        if (set(arguments) - set(schema["properties"])
                or not set(schema["required"]).issubset(arguments)):
            raise SourceToolError("source_tool_arguments_invalid")
        try:
            if name in {"render_pdf_region", "extract_word_embedded_image"}:
                binding = self.document_bindings.get(arguments["source_entry_id"])
                if binding is None:
                    raise SourceToolError("document_not_bound")
                extraction = getattr(self.visual_reader, name)(
                    binding=binding, **{key: value for key, value in arguments.items() if key != "source_entry_id"})
                from .monitoring_visual_transport import (
                    MonitoringVisualImage, MonitoringVisualValidationError,
                    MONITORING_VISUAL_MAX_IMAGES, MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES,
                )
                try:
                    MonitoringVisualImage(data=extraction.image.image_bytes,
                                          sha256=extraction.image.image_sha256,
                                          media_type=extraction.image.media_type, locator=extraction.locator)
                except MonitoringVisualValidationError as exc:
                    raise SourceToolError(str(exc).split(":", 1)[0]) from exc
                pending = {**self.visual_inputs, extraction.extraction_sha256: extraction}
                if (len(pending) > MONITORING_VISUAL_MAX_IMAGES
                        or sum(len(item.image.image_bytes) for item in pending.values()) > MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES):
                    raise SourceToolError("visual_input_attempt_budget_exhausted")
                # Pixels remain in this job-local object, never in a durable
                # JSON receipt. The model transport must attach these exact
                # bytes before this tool can be enabled for a product job.
                self.visual_inputs[extraction.extraction_sha256] = extraction
                return {**extraction.public_dict(), "visual_ref": extraction.extraction_sha256,
                        "coverage": "partial", "coverage_scope": extraction.extraction_kind,
                        "absence_claim_supported": False}
            if name == "read_document_units":
                binding = self.document_bindings.get(arguments["source_entry_id"])
                if binding is None:
                    raise SourceToolError("document_not_bound")
                return self.document_reader.read_document_units(
                    binding=binding, **{key: value for key, value in arguments.items() if key != "source_entry_id"})
            if name == "search_document":
                binding = self.document_bindings.get(arguments["source_entry_id"])
                terms = arguments["query_terms"]
                limit = arguments.get("limit", 12)
                if (binding is None or not isinstance(terms, list) or not 1 <= len(terms) <= 12
                        or any(not isinstance(term, str) or not term.strip() for term in terms)
                        or type(limit) is not int or not 1 <= limit <= 24):
                    raise SourceToolError("source_tool_arguments_invalid")
                result = self.document_resolver.retrieve_current_excerpts(
                    project_id=self.reader.project_id, binding=binding, query_terms=terms, limit=limit)
                return {**result, "input_revision_sha256": self.reader.input_revision,
                        "coverage": "partial", "coverage_scope": "matched_document_excerpts",
                        "absence_claim_supported": False, "result_limit": limit,
                        "possibly_truncated": len(result["excerpts"]) == limit}
            return getattr(self.reader, name)(**arguments)
        except (SourceToolError, ValueError, KeyError, TypeError) as exc:
            # A read failure is evidence about availability, not an empty
            # clinical result. The model may request another bounded region.
            return {"input_revision_sha256": self.reader.input_revision,
                    "project_id": self.reader.project_id, "status": "unavailable",
                    "coverage": "none", "absence_claim_supported": False,
                    "failure_code": str(exc) if isinstance(exc, SourceToolError) else "source_read_failed"}


@contextmanager
def open_monitoring_evidence_toolset(job, input_payload, *, workspace_dir: Path,
                                     document_resolver=None):
    store = Store(workspace_dir / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
                  workspace_dir / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME)
    try:
        reader = FrozenListingEvidenceTools(
            store, project_id=job.project_id, input_revision=job.input_revision_sha256,
            field_profile=input_payload["field_profile"],
        )
        from .monitoring_frozen_document_tools import FrozenDocumentEvidenceTools
        documents = FrozenDocumentEvidenceTools(
            candidate_root=workspace_dir / "document_authority_candidates",
            project_id=job.project_id, input_revision=job.input_revision_sha256,
            resolver=document_resolver,
        ) if document_resolver is not None else None
        from packages.medical_monitoring.admission.evidence_tool_contract import VISUAL_MAPPING_PROMPT_VERSIONS
        visuals = None
        if document_resolver is not None and job.prompt_version in VISUAL_MAPPING_PROMPT_VERSIONS:
            from .monitoring_document_visual_regions import FrozenDocumentVisualRegionTools
            visuals = FrozenDocumentVisualRegionTools(
                candidate_root=workspace_dir / "document_authority_candidates",
                project_id=job.project_id, input_revision=job.input_revision_sha256,
                resolver=document_resolver,
            )
        yield MonitoringEvidenceToolset(reader, document_resolver=document_resolver,
                                        document_reader=documents, visual_reader=visuals)
    finally:
        store.close()
