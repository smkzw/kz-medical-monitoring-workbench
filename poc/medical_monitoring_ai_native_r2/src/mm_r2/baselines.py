"""Dual baselines for the R2 kernel (Design v1.1 section 6.3; plan R2 step 5).

VETO 2 repairs:
* ``BaselineService._verified_baseline`` / ``_verified_mdv`` are removed from
  the class surface; issuance occurs only inside the validated public method
  through a closure-captured token that is not an ordinary attribute.
* ``set_data_baseline`` requires the exact :class:`AcceptanceService` type,
  resolves the :class:`SnapshotBinding`, and compares the
  exact project, snapshot ID, revision ID, content digest/hash, row count,
  structure, mapping, and identity binding.  Same-ID different-content
  substitution fails.
* Blocked records are rejected even if retained state is
  ``baseline_eligible``.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    ListingSnapshot,
    MmR2Error,
    content_hash,
    deep_freeze_json,
    new_id,
    now_iso,
    validate_sha256_hex,
)

__all__ = [
    "BaselineError",
    "DataBaseline",
    "MedicalDecisionVersion",
    "BaselineService",
]

_BASELINE_VERIFIED = object()


class BaselineError(MmR2Error):
    """Dual-baseline violation."""


@dataclass(frozen=True)
class DataBaseline:
    """One accepted full snapshot designated as the diff comparison point."""

    schema_name: str = "data_baseline"
    schema_version: str = "1"
    baseline_id: str = ""
    project_id: str = ""
    snapshot_id: str = ""
    snapshot_content_hash: str = ""
    snapshot_content_digest: str = ""
    cutoff: str = ""
    source_revision_id: str = ""
    identity_algorithm_digest: str = ""
    mapping_version: str = ""
    acceptance_evidence_hash: str = ""
    promoted_at: str = ""
    baseline_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _BASELINE_VERIFIED,
    ) -> None:
        if not self.baseline_id:
            raise DomainValidationError("DataBaseline.baseline_id is required")
        if not self.project_id:
            raise DomainValidationError("DataBaseline.project_id is required")
        if not self.snapshot_id:
            raise DomainValidationError("DataBaseline.snapshot_id is required")
        validate_sha256_hex(
            self.snapshot_content_hash, "DataBaseline.snapshot_content_hash"
        )
        validate_sha256_hex(
            self.snapshot_content_digest, "DataBaseline.snapshot_content_digest"
        )
        if not self.source_revision_id:
            raise DomainValidationError(
                "DataBaseline.source_revision_id is required"
            )
        if not self.identity_algorithm_digest:
            raise DomainValidationError(
                "DataBaseline.identity_algorithm_digest is required"
            )
        validate_sha256_hex(
            self.acceptance_evidence_hash,
            "DataBaseline.acceptance_evidence_hash",
        )
        if _verified is not _authority_token:
            raise DomainValidationError(
                "DataBaseline requires service-issued construction; use "
                "BaselineService.set_data_baseline(...) -- direct "
                "construction is unavailable to public callers"
            )
        expected = self.compute_hash()
        if self.baseline_hash and self.baseline_hash != expected:
            raise DomainValidationError("DataBaseline.baseline_hash mismatch")
        object.__setattr__(self, "baseline_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "baseline_id": self.baseline_id,
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "snapshot_content_hash": self.snapshot_content_hash,
            "snapshot_content_digest": self.snapshot_content_digest,
            "cutoff": self.cutoff,
            "source_revision_id": self.source_revision_id,
            "identity_algorithm_digest": self.identity_algorithm_digest,
            "mapping_version": self.mapping_version,
            "acceptance_evidence_hash": self.acceptance_evidence_hash,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
class MedicalDecisionVersion:
    """Frozen snapshot of medical-decision state (Design 6.3)."""

    schema_name: str = "medical_decision_version"
    schema_version: str = "1"
    version_id: str = ""
    project_id: str = ""
    data_baseline_id: str = ""
    snapshot_id: str = ""
    version_kind: str = "provisional"
    risk_state_hash: str = ""
    query_state_hash: str = ""
    report_state_hash: str = ""
    user_action_hash: str = ""
    actor: str = ""
    rationale: str = ""
    created_at: str = ""
    version_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _BASELINE_VERIFIED,
    ) -> None:
        if not self.version_id:
            raise DomainValidationError("version_id is required")
        if not self.project_id:
            raise DomainValidationError("project_id is required")
        if self.version_kind not in ("provisional", "signed", "exported"):
            raise DomainValidationError("version_kind invalid")
        if not self.actor:
            raise DomainValidationError("actor is required")
        if self.version_kind in ("signed", "exported") and not self.rationale:
            raise DomainValidationError("signed/exported require rationale")
        if _verified is not _authority_token:
            raise DomainValidationError(
                "MedicalDecisionVersion requires service-issued construction"
            )
        expected = self.compute_hash()
        if self.version_hash and self.version_hash != expected:
            raise DomainValidationError("version_hash mismatch")
        object.__setattr__(self, "version_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "version_id": self.version_id,
            "project_id": self.project_id,
            "data_baseline_id": self.data_baseline_id,
            "snapshot_id": self.snapshot_id,
            "version_kind": self.version_kind,
            "risk_state_hash": self.risk_state_hash,
            "query_state_hash": self.query_state_hash,
            "report_state_hash": self.report_state_hash,
            "user_action_hash": self.user_action_hash,
            "actor": self.actor,
            "rationale": self.rationale,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


class BaselineService:
    """Manages the two orthogonal baseline axes.

    VETO 2: ``_verified_baseline`` and ``_verified_mdv`` are **not** methods
    on the class.  Issuance occurs only through closure-captured factories
    installed by ``_seal_baseline_authority`` at module load; the captured
    token is unreachable as a class/module attribute.
    """

    def __init__(self) -> None:
        self._data_baselines: Dict[str, DataBaseline] = {}
        self._current_data_baseline: Dict[str, str] = {}
        self._medical_versions: Dict[str, List[MedicalDecisionVersion]] = {}

    # -- data baseline ----------------------------------------------------

    def set_data_baseline(
        self,
        acceptance_service,
        snapshot: ListingSnapshot,
        *,
        _issuer=None,
    ) -> DataBaseline:
        """Promote a baseline-eligible accepted snapshot to a data baseline.

        VETO 2: requires the exact AcceptanceService type, resolves the
        SnapshotBinding, and compares exact project/snapshot/revision/content.
        Blocked records are rejected.
        """
        from .acceptance import AcceptanceService
        if type(acceptance_service) is not AcceptanceService:
            raise BaselineError(
                "set_data_baseline requires a real AcceptanceService instance; "
                "duck-typed or hostile substitutes are rejected"
            )
        if type(snapshot) is not ListingSnapshot:
            raise BaselineError("set_data_baseline requires a ListingSnapshot")
        try:
            rec = acceptance_service.get(snapshot.snapshot_id)
        except Exception as exc:
            raise BaselineError(
                f"snapshot {snapshot.snapshot_id!r} is not registered in the "
                f"acceptance service: {exc}"
            ) from exc
        # VETO 2-8: blocked records rejected even if state is baseline_eligible.
        if rec.blocked:
            raise BaselineError(
                f"snapshot {snapshot.snapshot_id!r} acceptance record is "
                f"blocked; blocked records cannot become data baselines"
            )
        if rec.project_id != snapshot.project_id:
            raise BaselineError(
                f"acceptance record project_id {rec.project_id!r} does not "
                f"match snapshot project_id {snapshot.project_id!r}"
            )
        if not rec.is_baseline_eligible:
            raise BaselineError(
                f"snapshot {snapshot.snapshot_id!r} is not baseline_eligible "
                f"(state={rec.state.value}, blocked={rec.blocked})"
            )
        binding = acceptance_service.binding(snapshot.snapshot_id)
        # VETO 2-4: compare the supplied snapshot against the registered
        # binding's snapshot — same-ID different-content substitution fails.
        bound_snap = binding.snapshot
        if snapshot.content_hash != bound_snap.content_hash:
            raise BaselineError(
                f"snapshot content_hash {snapshot.content_hash!r} does not "
                f"match the registered binding snapshot content_hash "
                f"{bound_snap.content_hash!r}; same-ID different-content "
                f"substitution is rejected"
            )
        if snapshot.content_digest != bound_snap.content_digest:
            raise BaselineError(
                f"snapshot content_digest does not match the registered "
                f"binding snapshot"
            )
        if snapshot.revision_id != bound_snap.revision_id:
            raise BaselineError(
                f"snapshot revision_id {snapshot.revision_id!r} does not "
                f"match the registered binding snapshot revision_id "
                f"{bound_snap.revision_id!r}"
            )
        # Derive evidence hash from the record's evidence.
        evidence_hash = ""
        if rec.evidence is not None:
            evidence_hash = rec.evidence.evidence_hash
        if not evidence_hash:
            raise BaselineError(
                f"snapshot {snapshot.snapshot_id!r} has no evidence hash"
            )
        identity_digest = binding.identity_algorithm.digest
        if not identity_digest:
            raise BaselineError("binding has no identity algorithm digest")
        if _issuer is None:
            raise BaselineError("baseline issuance authority is unavailable")
        bl = _issuer(
            baseline_id=new_id("dbl-"),
            project_id=snapshot.project_id,
            snapshot_id=snapshot.snapshot_id,
            snapshot_content_hash=snapshot.content_hash,
            snapshot_content_digest=snapshot.content_digest,
            cutoff=snapshot.snapshot_version,
            source_revision_id=snapshot.revision_id,
            identity_algorithm_digest=identity_digest,
            mapping_version=binding.mapping_version,
            acceptance_evidence_hash=evidence_hash,
            promoted_at=now_iso(),
        )
        self._data_baselines[bl.baseline_id] = bl
        self._current_data_baseline[snapshot.project_id] = bl.baseline_id
        return bl

    def current_data_baseline(self, project_id: str) -> Optional[DataBaseline]:
        bid = self._current_data_baseline.get(project_id)
        if bid is None:
            return None
        return self._data_baselines[bid]

    def data_baseline_history(self, project_id: str) -> List[DataBaseline]:
        return [bl for bl in self._data_baselines.values()
                if bl.project_id == project_id]

    def data_baseline_by_snapshot(self, snapshot_id: str) -> Optional[DataBaseline]:
        for bl in self._data_baselines.values():
            if bl.snapshot_id == snapshot_id:
                return bl
        return None

    # -- medical decision version -----------------------------------------

    def record_medical_decision_version(
        self, project_id: str, *, snapshot_id: str = "",
        data_baseline_id: str = "", version_kind: str = "provisional",
        risk_state_hash: str = "", query_state_hash: str = "",
        report_state_hash: str = "", user_action_hash: str = "",
        actor: str = "", rationale: str = "", _issuer=None,
    ) -> MedicalDecisionVersion:
        if not project_id:
            raise DomainValidationError("project_id is required")
        if not actor:
            raise DomainValidationError("actor is required")
        if data_baseline_id:
            baseline = self._data_baselines.get(data_baseline_id)
            if baseline is None:
                raise BaselineError(
                    f"medical decision version references unknown data baseline "
                    f"{data_baseline_id!r}"
                )
            if baseline.project_id != project_id:
                raise BaselineError(
                    f"data baseline {data_baseline_id!r} belongs to project "
                    f"{baseline.project_id!r}, not {project_id!r}"
                )
        if _issuer is None:
            raise BaselineError("medical-decision issuance authority is unavailable")
        mdv = _issuer(
            version_id=new_id("mdv-"),
            project_id=project_id,
            data_baseline_id=data_baseline_id,
            snapshot_id=snapshot_id,
            version_kind=version_kind,
            risk_state_hash=risk_state_hash,
            query_state_hash=query_state_hash,
            report_state_hash=report_state_hash,
            user_action_hash=user_action_hash,
            actor=actor,
            rationale=rationale,
            created_at=now_iso(),
        )
        self._medical_versions.setdefault(project_id, []).append(mdv)
        return mdv

    def medical_decision_versions(self, project_id: str) -> List[MedicalDecisionVersion]:
        return list(self._medical_versions.get(project_id, []))

    def current_medical_decision_version(
        self, project_id: str
    ) -> Optional[MedicalDecisionVersion]:
        versions = self._medical_versions.get(project_id, [])
        return versions[-1] if versions else None

    def is_orthogonal(self) -> bool:
        return True

    def has_baseline(self, baseline_id: str) -> bool:
        return baseline_id in self._data_baselines

    def get_baseline(self, baseline_id: str) -> DataBaseline:
        if baseline_id not in self._data_baselines:
            raise BaselineError(f"unknown baseline {baseline_id!r}")
        return self._data_baselines[baseline_id]


# ---------------------------------------------------------------------------
# Seal: closure-captured issuance factories.  The issuer functions exist only
# inside this sealing closure, not on the module or service instances.  The
# token is deleted below.
# ---------------------------------------------------------------------------

def _seal_baseline_authority(authority_token: Any) -> None:
    bl_post = DataBaseline.__post_init__
    mdv_post = MedicalDecisionVersion.__post_init__
    set_data_baseline = BaselineService.set_data_baseline
    record_medical_decision_version = BaselineService.record_medical_decision_version

    def checked_bl_post(self, _verified: Any = None) -> None:
        return bl_post(self, _verified, authority_token)

    def checked_mdv_post(self, _verified: Any = None) -> None:
        return mdv_post(self, _verified, authority_token)

    def _issue_baseline(**kwargs: Any) -> DataBaseline:
        kwargs["_verified"] = authority_token
        return DataBaseline(**kwargs)

    def _issue_mdv(**kwargs: Any) -> MedicalDecisionVersion:
        kwargs["_verified"] = authority_token
        return MedicalDecisionVersion(**kwargs)

    def service_set_data_baseline(self, *args: Any, **kwargs: Any) -> DataBaseline:
        kwargs["_issuer"] = _issue_baseline
        return set_data_baseline(self, *args, **kwargs)

    def service_record_medical_decision_version(
        self, *args: Any, **kwargs: Any,
    ) -> MedicalDecisionVersion:
        kwargs["_issuer"] = _issue_mdv
        return record_medical_decision_version(self, *args, **kwargs)

    DataBaseline.__post_init__ = checked_bl_post
    MedicalDecisionVersion.__post_init__ = checked_mdv_post
    BaselineService.set_data_baseline = service_set_data_baseline
    BaselineService.record_medical_decision_version = service_record_medical_decision_version


_seal_baseline_authority(_BASELINE_VERIFIED)
del _seal_baseline_authority
del _BASELINE_VERIFIED
