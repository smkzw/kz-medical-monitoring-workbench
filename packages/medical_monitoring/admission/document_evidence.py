"""Typed authority snapshot for documents used by listing interpretation.

This module binds document identity and locator completeness only.  It does
not extract clinical facts, choose CTCAE grades, assess risk, join clinical
domains, or generate queries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import re
from typing import Any, Mapping, Sequence

from ..intelligence.primitives import content_hash


DOCUMENT_EVIDENCE_SCHEMA_VERSION = "mm-c3-document-evidence-v2"
DOCUMENT_ROLES = (
    "protocol",
    "investigator_brochure",
    "ecrf",
    "sap",
)
MAPPING_REQUIRED_DOCUMENT_ROLES = frozenset({"protocol", "ecrf"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:@/-]{2,240}$")
_MEDIA_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})
_CURRENT_STATUS = "current"
_NON_CURRENT_STATUSES = frozenset({"missing", "ambiguous", "incomplete"})


class DocumentEvidenceError(ValueError):
    """Raised when a document authority snapshot cannot be trusted."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def _required(value: Any, field_name: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise DocumentEvidenceError(f"{field_name}_required")
    return value


def _identifier(value: Any, field_name: str) -> str:
    value = _required(value, field_name)
    if _SAFE_ID_RE.fullmatch(value) is None:
        raise DocumentEvidenceError(f"{field_name}_invalid")
    return value


def _sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise DocumentEvidenceError(f"{field_name}_invalid")
    return value


def _date(value: Any, field_name: str) -> str:
    value = _required(value, field_name)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise DocumentEvidenceError(f"{field_name}_invalid") from exc


def _text_tuple(
    values: Any,
    field_name: str,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise DocumentEvidenceError(f"{field_name}_invalid")
    result = tuple(str(item or "").strip() for item in values)
    if any(not item for item in result) or (required and not result):
        raise DocumentEvidenceError(f"{field_name}_invalid")
    return result


@dataclass(frozen=True)
class CurrentDocumentBinding:
    """One current registry document and its complete locator index."""

    role: str
    source_entry_id: str
    source_revision: str
    content_sha256: str
    media_type: str
    parser_name: str
    parser_version: str
    validation_id: str
    validation_revision: int
    validator_version: str
    validation_context_sha256: str
    locator_index_sha256: str
    locator_count: int
    locator_samples: tuple[str, ...]
    selection_basis: str
    operational_effective_from: str = ""
    operational_effective_to: str = ""
    clinical_applicability_resolved: bool = False
    main_source_entry_id: str = ""

    def __post_init__(self) -> None:
        role = _required(self.role, "document_role")
        if role not in DOCUMENT_ROLES:
            raise DocumentEvidenceError("document_role_invalid")
        media_type = _required(self.media_type, "media_type")
        if media_type not in _MEDIA_TYPES:
            raise DocumentEvidenceError("media_type_invalid")
        basis = _required(self.selection_basis, "selection_basis")
        if basis not in {"registry_current", "effective_interval"}:
            raise DocumentEvidenceError("selection_basis_invalid")
        if (
            not isinstance(self.locator_count, int)
            or isinstance(self.locator_count, bool)
            or self.locator_count < 1
        ):
            raise DocumentEvidenceError("locator_count_invalid")
        locator_samples = _text_tuple(
            self.locator_samples,
            "locator_samples",
            required=True,
        )
        if len(locator_samples) > 16:
            raise DocumentEvidenceError("locator_samples_too_large")
        if len(locator_samples) != len(set(locator_samples)):
            raise DocumentEvidenceError("document_locators_duplicated")
        if len(locator_samples) > self.locator_count:
            raise DocumentEvidenceError("locator_samples_exceed_count")
        start = (
            _date(self.operational_effective_from, "operational_effective_from")
            if self.operational_effective_from
            else ""
        )
        end = (
            _date(self.operational_effective_to, "operational_effective_to")
            if self.operational_effective_to
            else ""
        )
        if start and end and end < start:
            raise DocumentEvidenceError("document_effective_interval_invalid")
        if self.clinical_applicability_resolved and (
            basis != "effective_interval" or not start
        ):
            raise DocumentEvidenceError("clinical_applicability_unproven")
        object.__setattr__(self, "role", role)
        object.__setattr__(
            self,
            "source_entry_id",
            _identifier(self.source_entry_id, "source_entry_id"),
        )
        object.__setattr__(
            self,
            "source_revision",
            _identifier(self.source_revision, "source_revision"),
        )
        object.__setattr__(
            self,
            "content_sha256",
            _sha256(self.content_sha256, "content_sha256"),
        )
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(
            self, "parser_name", _identifier(self.parser_name, "parser_name")
        )
        object.__setattr__(
            self,
            "parser_version",
            _identifier(self.parser_version, "parser_version"),
        )
        object.__setattr__(
            self,
            "validation_id",
            _identifier(self.validation_id, "validation_id"),
        )
        if (
            not isinstance(self.validation_revision, int)
            or isinstance(self.validation_revision, bool)
            or self.validation_revision < 1
        ):
            raise DocumentEvidenceError("validation_revision_invalid")
        object.__setattr__(
            self,
            "validator_version",
            _identifier(self.validator_version, "validator_version"),
        )
        object.__setattr__(
            self,
            "validation_context_sha256",
            _sha256(
                self.validation_context_sha256,
                "validation_context_sha256",
            ),
        )
        object.__setattr__(
            self,
            "locator_index_sha256",
            _sha256(self.locator_index_sha256, "locator_index_sha256"),
        )
        object.__setattr__(self, "locator_samples", locator_samples)
        object.__setattr__(self, "selection_basis", basis)
        object.__setattr__(self, "operational_effective_from", start)
        object.__setattr__(self, "operational_effective_to", end)
        object.__setattr__(
            self,
            "clinical_applicability_resolved",
            bool(self.clinical_applicability_resolved),
        )
        main_source_entry_id = str(self.main_source_entry_id or "").strip()
        if main_source_entry_id:
            if main_source_entry_id == self.source_entry_id:
                raise DocumentEvidenceError(
                    "document_supplementary_relation_invalid"
                )
            main_source_entry_id = _identifier(
                main_source_entry_id,
                "main_source_entry_id",
            )
        object.__setattr__(
            self,
            "main_source_entry_id",
            main_source_entry_id,
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["locator_samples"] = list(self.locator_samples)
        return value


@dataclass(frozen=True)
class DocumentRoleEvidence:
    """One accounted role: current evidence or an explicit limitation.

    A current role binds one main document plus zero or more effective
    supplementary documents (errata, revision notes).  Every supplementary
    binding must anchor to the main binding so the composite authority
    stays closed and per-file retrieval stays resolvable.
    """

    role: str
    status: str
    binding: CurrentDocumentBinding | None = None
    supplementary_bindings: tuple[CurrentDocumentBinding, ...] = ()
    limitation_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        role = _required(self.role, "document_role")
        if role not in DOCUMENT_ROLES:
            raise DocumentEvidenceError("document_role_invalid")
        status = _required(self.status, "document_status")
        limitations = _text_tuple(self.limitation_codes, "limitation_codes")
        supplementary = tuple(self.supplementary_bindings)
        if any(
            not isinstance(item, CurrentDocumentBinding)
            for item in supplementary
        ):
            raise DocumentEvidenceError(
                "document_supplementary_binding_invalid"
            )
        if status == _CURRENT_STATUS:
            if self.binding is None or self.binding.role != role:
                raise DocumentEvidenceError("current_document_binding_invalid")
            if limitations:
                raise DocumentEvidenceError("current_document_has_limitation")
            if self.binding.main_source_entry_id:
                raise DocumentEvidenceError(
                    "document_supplementary_relation_invalid"
                )
            bound_ids = [self.binding.source_entry_id]
            for item in supplementary:
                if item.role != role:
                    raise DocumentEvidenceError(
                        "document_supplementary_role_invalid"
                    )
                if item.main_source_entry_id != self.binding.source_entry_id:
                    raise DocumentEvidenceError(
                        "document_supplementary_relation_invalid"
                    )
                bound_ids.append(item.source_entry_id)
            if len(bound_ids) != len(set(bound_ids)):
                raise DocumentEvidenceError(
                    "document_supplementary_duplicated"
                )
        elif status in _NON_CURRENT_STATUSES:
            if self.binding is not None or not limitations:
                raise DocumentEvidenceError("limited_document_role_invalid")
            if supplementary:
                raise DocumentEvidenceError("limited_document_role_invalid")
        else:
            raise DocumentEvidenceError("document_status_invalid")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "limitation_codes", limitations)
        object.__setattr__(self, "supplementary_bindings", supplementary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "status": self.status,
            "binding": self.binding.to_dict() if self.binding else None,
            "supplementary_bindings": [
                item.to_dict() for item in self.supplementary_bindings
            ],
            "limitation_codes": list(self.limitation_codes),
        }


def _binding_from_dict(payload: Mapping[str, Any]) -> CurrentDocumentBinding:
    if not isinstance(payload, Mapping):
        raise DocumentEvidenceError("document_binding_invalid")
    return CurrentDocumentBinding(
        role=payload.get("role", ""),
        source_entry_id=payload.get("source_entry_id", ""),
        source_revision=payload.get("source_revision", ""),
        content_sha256=payload.get("content_sha256", ""),
        media_type=payload.get("media_type", ""),
        parser_name=payload.get("parser_name", ""),
        parser_version=payload.get("parser_version", ""),
        validation_id=payload.get("validation_id", ""),
        validation_revision=payload.get("validation_revision", 0),
        validator_version=payload.get("validator_version", ""),
        validation_context_sha256=payload.get(
            "validation_context_sha256", ""
        ),
        locator_index_sha256=payload.get("locator_index_sha256", ""),
        locator_count=payload.get("locator_count", 0),
        locator_samples=tuple(payload.get("locator_samples") or ()),
        selection_basis=payload.get("selection_basis", ""),
        operational_effective_from=payload.get(
            "operational_effective_from", ""
        ),
        operational_effective_to=payload.get("operational_effective_to", ""),
        clinical_applicability_resolved=payload.get(
            "clinical_applicability_resolved", False
        ),
        main_source_entry_id=payload.get("main_source_entry_id", ""),
    )


def _supplementary_bindings_from_dict(
    raw_items: Any,
) -> tuple[CurrentDocumentBinding, ...]:
    if not isinstance(raw_items, Sequence) or isinstance(
        raw_items, (str, bytes)
    ):
        raise DocumentEvidenceError("document_supplementary_binding_invalid")
    return tuple(
        _binding_from_dict(item)
        for item in raw_items
    )


@dataclass(frozen=True)
class MonitoringDocumentEvidencePacket:
    """Complete four-role snapshot bound to one project and registry revision."""

    project_id: str
    listing_admission_date: str
    registry_revision_sha256: str
    roles: tuple[DocumentRoleEvidence, ...]
    schema_version: str = DOCUMENT_EVIDENCE_SCHEMA_VERSION
    packet_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        project_id = _identifier(self.project_id, "project_id")
        listing_admission_date = _date(
            self.listing_admission_date,
            "listing_admission_date",
        )
        if self.schema_version != DOCUMENT_EVIDENCE_SCHEMA_VERSION:
            raise DocumentEvidenceError("document_schema_version_invalid")
        roles = tuple(self.roles)
        if any(not isinstance(item, DocumentRoleEvidence) for item in roles):
            raise DocumentEvidenceError("document_roles_invalid")
        if tuple(item.role for item in roles) != DOCUMENT_ROLES:
            raise DocumentEvidenceError("document_roles_incomplete_or_unordered")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(
            self,
            "listing_admission_date",
            listing_admission_date,
        )
        object.__setattr__(
            self,
            "registry_revision_sha256",
            _sha256(
                self.registry_revision_sha256,
                "registry_revision_sha256",
            ),
        )
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "packet_sha256", content_hash(self._payload()))

    @property
    def mapping_context_ready(self) -> bool:
        return all(
            item.status == _CURRENT_STATUS
            for item in self.roles
            if item.role in MAPPING_REQUIRED_DOCUMENT_ROLES
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "listing_admission_date": self.listing_admission_date,
            "registry_revision_sha256": self.registry_revision_sha256,
            "roles": [item.to_dict() for item in self.roles],
            "mapping_required_roles": sorted(MAPPING_REQUIRED_DOCUMENT_ROLES),
            "mapping_context_ready": self.mapping_context_ready,
            "clinical_boundary": (
                "document_identity_and_locator_authority_only;"
                "no_ctcae_grade_risk_query_or_clinical_join"
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "packet_sha256": self.packet_sha256}

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> "MonitoringDocumentEvidencePacket":
        if not isinstance(payload, Mapping):
            raise DocumentEvidenceError("document_packet_invalid")
        raw_roles = payload.get("roles")
        if not isinstance(raw_roles, Sequence) or isinstance(
            raw_roles, (str, bytes)
        ):
            raise DocumentEvidenceError("document_roles_invalid")
        roles = []
        for raw in raw_roles:
            if not isinstance(raw, Mapping):
                raise DocumentEvidenceError("document_role_invalid")
            binding_payload = raw.get("binding")
            binding = None
            if binding_payload is not None:
                binding = _binding_from_dict(binding_payload)
            roles.append(
                DocumentRoleEvidence(
                    role=raw.get("role", ""),
                    status=raw.get("status", ""),
                    binding=binding,
                    supplementary_bindings=(
                        _supplementary_bindings_from_dict(
                            raw.get("supplementary_bindings", ())
                        )
                    ),
                    limitation_codes=tuple(raw.get("limitation_codes") or ()),
                )
            )
        packet = cls(
            project_id=payload.get("project_id", ""),
            listing_admission_date=payload.get(
                "listing_admission_date", ""
            ),
            registry_revision_sha256=payload.get(
                "registry_revision_sha256", ""
            ),
            roles=tuple(roles),
            schema_version=payload.get("schema_version", ""),
        )
        declared = payload.get("packet_sha256")
        if declared not in (None, "") and declared != packet.packet_sha256:
            raise DocumentEvidenceError("document_packet_sha256_mismatch")
        if payload.get("mapping_context_ready") not in (
            None,
            packet.mapping_context_ready,
        ):
            raise DocumentEvidenceError("document_readiness_mismatch")
        return packet


def validate_document_evidence_packet(
    payload: Mapping[str, Any],
    *,
    project_id: str,
    require_mapping_context: bool,
) -> dict[str, Any]:
    packet = MonitoringDocumentEvidencePacket.from_dict(payload)
    if packet.project_id != project_id:
        raise DocumentEvidenceError("document_packet_project_mismatch")
    if require_mapping_context and not packet.mapping_context_ready:
        raise DocumentEvidenceError("mapping_document_evidence_incomplete")
    return packet.to_dict()


__all__ = [
    "DOCUMENT_EVIDENCE_SCHEMA_VERSION",
    "DOCUMENT_ROLES",
    "MAPPING_REQUIRED_DOCUMENT_ROLES",
    "CurrentDocumentBinding",
    "DocumentEvidenceError",
    "DocumentRoleEvidence",
    "MonitoringDocumentEvidencePacket",
    "validate_document_evidence_packet",
]
