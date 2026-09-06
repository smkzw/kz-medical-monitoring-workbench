"""Read-only resolver from the shared registry to monitoring document evidence."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from packages.medical_monitoring.admission.document_evidence import (
    DOCUMENT_ROLES,
    CurrentDocumentBinding,
    DocumentRoleEvidence,
    MonitoringDocumentEvidencePacket,
)
from packages.medical_monitoring.intelligence.primitives import content_hash

from .source_intake import monitoring_authority_receipt_is_complete


_SOURCE_KINDS_BY_ROLE = {
    "protocol": frozenset({
        "protocol_docx", "protocol_document", "protocol_supplement",
    }),
    "investigator_brochure": frozenset({
        "investigator_brochure", "investigator_brochure_supplement",
    }),
    "ecrf": frozenset({
        "ecrf", "ecrf_document", "ecrf_xlsx", "ecrf_supplement",
    }),
    "sap": frozenset({
        "sap", "statistical_analysis_plan", "sap_supplement",
    }),
}
_MEDIA_TYPE_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
}
_RETRIEVAL_SCHEMA_VERSION = "mm-monitoring-document-retrieval-v1"


class MonitoringDocumentEvidenceResolver:
    """Select current monitoring-owned documents without clinical inference."""

    def __init__(self, source_registry: Any) -> None:
        self.source_registry = source_registry

    def _verified_entries(self, project_id: str, roles=DOCUMENT_ROLES) -> list[Any]:
        project_entries = self.source_registry.list_entries(project_id)
        return [
            entry
            for entry in project_entries
            if entry.module == "medical_monitoring"
            and any(
                entry.source_kind in source_kinds
                for source_kinds in (_SOURCE_KINDS_BY_ROLE[role] for role in roles)
            )
            and (
                self.source_registry.monitoring_authority_entry_is_verified(entry)
                if hasattr(
                    self.source_registry,
                    "monitoring_authority_entry_is_verified",
                )
                else monitoring_authority_receipt_is_complete(
                    entry,
                    project_entries,
                )
            )
        ]

    def resolve(
        self,
        *,
        project_id: str,
        listing_admission_date: str | None = None,
        selected_entry_ids: Mapping[str, str] | None = None,
    ) -> MonitoringDocumentEvidencePacket:
        entries = self._verified_entries(project_id)
        spans = self.source_registry.list_spans(project_id)
        registry_revision = content_hash([
            {
                "entry_id": entry.entry_id,
                "source_kind": entry.source_kind,
                "content_hash": entry.content_hash,
                "parser_status": entry.parser_status,
                "parser_version": entry.parser_version,
                "authority_status": str(
                    (entry.metadata or {}).get(
                        "monitoring_authority_status", ""
                    )
                ),
                "document_revision": str(
                    (entry.metadata or {}).get("document_revision", "")
                ),
                "created_at": entry.created_at.isoformat(),
            }
            for entry in sorted(entries, key=lambda item: item.entry_id)
        ])
        role_records = tuple(
            self._role_evidence(
                role,
                entries,
                spans,
                selected_entry_id=str(
                    (selected_entry_ids or {}).get(role, "")
                ).strip(),
            )
            for role in DOCUMENT_ROLES
        )
        return MonitoringDocumentEvidencePacket(
            project_id=project_id,
            listing_admission_date=(
                listing_admission_date or date.today().isoformat()
            ),
            registry_revision_sha256=registry_revision,
            roles=role_records,
        )

    def retrieve_current_excerpts(
        self,
        *,
        project_id: str,
        binding: CurrentDocumentBinding,
        query_terms: Sequence[str],
        limit: int = 24,
    ) -> dict[str, Any]:
        """Retrieve locator-bound excerpts from one still-current file.

        Works per file: ``binding`` may be the role's main binding or any
        supplementary binding of the current composite authority.  The full
        composite must still resolve, so a broken supplementary fails the
        retrieval for every file in the set.
        """

        self.assert_current_binding(project_id=project_id, binding=binding)
        binding_kind = "supplementary" if binding.main_source_entry_id else "main"
        matches = self.source_registry.search_document_spans(
            project_id,
            binding.source_entry_id,
            query_terms,
            limit=limit,
            required_module="medical_monitoring",
            allowed_source_kinds=_SOURCE_KINDS_BY_ROLE[binding.role],
        )
        excerpts = [
            {
                "source_id": str(item["source_id"]),
                "locator": str(item["locator"]),
                "text": str(item["text"]),
                "text_sha256": content_hash(str(item["text"])),
                "matched_keywords": list(item["matched_keywords"]),
            }
            for item in matches
        ]
        payload = {
            "schema_version": _RETRIEVAL_SCHEMA_VERSION,
            "project_id": project_id,
            "role": binding.role,
            "binding_kind": binding_kind,
            "source_entry_id": binding.source_entry_id,
            "content_sha256": binding.content_sha256,
            "locator_index_sha256": binding.locator_index_sha256,
            "query_sha256": content_hash([
                str(term).strip() for term in query_terms
            ]),
            "excerpts": excerpts,
            "clinical_conclusions": [],
        }
        return {
            **payload,
            "packet_sha256": content_hash(payload),
        }

    def assert_current_binding(self, *, project_id: str, binding: CurrentDocumentBinding) -> None:
        """Check the complete frozen authority before any document read."""
        if binding.role not in DOCUMENT_ROLES:
            raise ValueError("monitoring document role is unsupported")
        binding_kind = (
            "supplementary" if binding.main_source_entry_id else "main"
        )
        # A byte-read guard verifies its selected role and every supplementary
        # binding. The outer job revision check still verifies the full packet.
        # Avoid reconstructing three unrelated roles on both sides of each read.
        evidence = self._role_evidence(
            binding.role,
            self._verified_entries(project_id, (binding.role,)),
            self.source_registry.list_spans(project_id),
            selected_entry_id=(
                binding.main_source_entry_id
                if binding_kind == "supplementary"
                else binding.source_entry_id
            ),
        )
        still_current = (
            evidence.status == "current"
            and (
                evidence.binding == binding
                if binding_kind == "main"
                else any(
                    item == binding
                    for item in evidence.supplementary_bindings
                )
            )
        )
        if not still_current:
            raise ValueError("monitoring document binding is no longer current")

    def _role_evidence(
        self,
        role: str,
        entries: list[Any],
        spans: list[Any],
        *,
        selected_entry_id: str,
    ) -> DocumentRoleEvidence:
        candidates = [
            entry
            for entry in entries
            if entry.source_kind in _SOURCE_KINDS_BY_ROLE[role]
        ]
        promoted = [
            entry
            for entry in candidates
            if (entry.metadata or {}).get("monitoring_authority_status")
            == "promoted"
        ]
        if promoted:
            candidates = promoted
        if not candidates:
            return DocumentRoleEvidence(
                role=role,
                status="missing",
                limitation_codes=(f"{role}_not_registered",),
            )
        relations = self._declared_binding_relations(candidates)
        mains = [
            entry
            for entry in candidates
            if entry.entry_id not in relations
        ]
        supplementaries = [
            entry
            for entry in candidates
            if entry.entry_id in relations
        ]
        if selected_entry_id:
            mains = [
                entry
                for entry in mains
                if entry.entry_id == selected_entry_id
            ]
            if not mains:
                return DocumentRoleEvidence(
                    role=role,
                    status="incomplete",
                    limitation_codes=(f"{role}_selection_stale",),
                )
        current = [
            binding
            for entry in mains
            if (binding := self._current_binding(role, entry, spans))
            is not None
        ]
        if not current:
            return DocumentRoleEvidence(
                role=role,
                status="incomplete",
                limitation_codes=(
                    f"{role}_current_effective_source_unresolved",
                ),
            )
        if len(current) != 1:
            return DocumentRoleEvidence(
                role=role,
                status="ambiguous",
                limitation_codes=(f"{role}_current_source_ambiguous",),
            )
        main_binding = current[0]
        bound_supplementaries = []
        for entry in sorted(
            supplementaries,
            key=lambda item: item.entry_id,
        ):
            declared_main = relations[entry.entry_id][1]
            if declared_main != main_binding.source_entry_id:
                # Declared against a superseded main: not part of the
                # current composite authority.
                continue
            binding = self._current_binding(
                role,
                entry,
                spans,
                main_source_entry_id=main_binding.source_entry_id,
            )
            if binding is None:
                return DocumentRoleEvidence(
                    role=role,
                    status="incomplete",
                    limitation_codes=(
                        f"{role}_supplementary_unresolved",
                    ),
                )
            bound_supplementaries.append(binding)
        return DocumentRoleEvidence(
            role=role,
            status="current",
            binding=main_binding,
            supplementary_bindings=tuple(
                sorted(
                    bound_supplementaries,
                    key=lambda item: item.source_entry_id,
                )
            ),
        )

    def _declared_binding_relations(
        self,
        entries: list[Any],
    ) -> dict[str, tuple[str, str]]:
        """Read declared main/supplementary relations from authority receipts.

        Each promoted entry embeds the hash-bound promotion receipt that
        registered it.  A registration row may declare itself a
        supplementary binding with ``binding_kind: "supplementary"`` and an
        anchor ``supplementary_of`` entry id; rows without such a
        declaration remain main candidates.  Relations are only trusted
        when they are self-consistent; the registry remains the authority
        on whether the receipt itself verifies.
        """

        relations: dict[str, tuple[str, str]] = {}
        for entry in entries:
            metadata = dict(entry.metadata or {})
            if metadata.get("monitoring_authority_status") != "promoted":
                continue
            receipt = metadata.get("document_authority_receipt")
            if not isinstance(receipt, Mapping):
                continue
            registrations = receipt.get("registrations")
            if not isinstance(registrations, Sequence) or isinstance(
                registrations, (str, bytes)
            ):
                continue
            for registration in registrations:
                if not isinstance(registration, Mapping):
                    continue
                if (
                    str(registration.get("source_entry_id") or "")
                    != entry.entry_id
                ):
                    continue
                if (
                    str(registration.get("binding_kind") or "").strip()
                    != "supplementary"
                ):
                    continue
                main_entry_id = str(
                    registration.get("supplementary_of") or ""
                ).strip()
                if main_entry_id and main_entry_id != entry.entry_id:
                    relations[entry.entry_id] = (
                        "supplementary",
                        main_entry_id,
                    )
        return relations

    def _current_binding(
        self,
        role: str,
        entry: Any,
        spans: list[Any],
        *,
        main_source_entry_id: str = "",
    ) -> CurrentDocumentBinding | None:
        entry_spans = [
            span
            for span in spans
            if span.entry_id == entry.entry_id
            and span.project_id == entry.project_id
            and span.module == "medical_monitoring"
        ]
        source_ids = [str(span.source_id).strip() for span in entry_spans]
        locators = [str(span.locator).strip() for span in entry_spans]
        span_count = int(getattr(entry, "span_count", 0) or 0)
        metadata = dict(entry.metadata or {})
        expected_locator_count = int(
            metadata.get("expected_locator_count", 0) or 0
        )
        expected_locator_sha256 = str(
            metadata.get("expected_locator_index_sha256") or ""
        ).strip()
        locator_manifest_complete = (
            metadata.get("locator_manifest_complete") is True
        )
        actual_locator_manifest = sorted(
            (
                {"source_id": source_id, "locator": locator}
                for source_id, locator in zip(source_ids, locators)
            ),
            key=lambda item: (item["locator"], item["source_id"]),
        )
        actual_locator_sha256 = hashlib.sha256(
            json.dumps(
                actual_locator_manifest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if (
            not entry_spans
            or not locator_manifest_complete
            or expected_locator_count < 1
            or expected_locator_count != len(entry_spans)
            or expected_locator_sha256 != actual_locator_sha256
            or any(
                not source_id or not locator or len(locator) > 500
                or any(character.isspace() for character in locator)
                for source_id, locator in zip(source_ids, locators)
            )
            or len(source_ids) != len(set(source_ids))
            or len(locators) != len(set(locators))
            or (span_count and span_count != len(entry_spans))
        ):
            return None
        validation = self.source_registry.current_content_validation(
            entry.project_id,
            entry.entry_id,
        )
        validation_usable = (
            validation is not None
            and validation.use_status
            in {"allowed", "confirmed_after_warning"}
            and validation.source_entry_id == entry.entry_id
            and validation.project_id == entry.project_id
            and validation.module == "medical_monitoring"
            and validation.file_sha256 == entry.content_hash
            and validation.technical_status == "ready"
        )
        if entry.parser_status != "parsed" or not validation_usable:
            return None
        try:
            self.source_registry.assert_operational_sources_usable(
                entry.project_id,
                source_ids,
            )
        except (KeyError, ValueError):
            return None
        filename = str(metadata.get("filename") or entry.public_title)
        media_type = str(metadata.get("media_type") or "").strip()
        if not media_type:
            media_type = _MEDIA_TYPE_BY_SUFFIX.get(
                Path(filename).suffix.lower(),
                "",
            )
        if not media_type:
            return None
        locator_index = [
            {
                "source_id": span.source_id,
                "locator": span.locator,
                "preview_sha256": content_hash(span.text_preview),
            }
            for span in sorted(
                entry_spans,
                key=lambda item: (item.locator, item.source_id),
            )
        ]
        ordered_locators = sorted(locators)
        return CurrentDocumentBinding(
            role=role,
            source_entry_id=entry.entry_id,
            source_revision=entry.entry_id,
            content_sha256=entry.content_hash,
            media_type=media_type,
            parser_name=str(
                metadata.get("parser_name") or entry.parser_version
            ),
            parser_version=str(
                metadata.get("parser_version") or entry.parser_version
            ),
            validation_id=validation.validation_id,
            validation_revision=validation.revision,
            validator_version=validation.validator_version,
            validation_context_sha256=validation.expected_context_hash,
            locator_index_sha256=content_hash(locator_index),
            locator_count=len(ordered_locators),
            locator_samples=tuple(
                ordered_locators[index]
                for index in sorted({
                    0,
                    len(ordered_locators) // 2,
                    len(ordered_locators) - 1,
                })
            ),
            selection_basis="registry_current",
            clinical_applicability_resolved=False,
            main_source_entry_id=main_source_entry_id,
        )


__all__ = ["MonitoringDocumentEvidenceResolver"]
