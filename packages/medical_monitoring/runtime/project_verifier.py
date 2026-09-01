"""Public facade for project verification and recovery coordination."""
from __future__ import annotations

from .project_recovery import RecoveryCoordinator, startup_recovery_scan
from .project_verification import ProjectVerifier
from .project_verifier_core import (
    AUDIT_SCHEMA_VERSION,
    RESULT_ANOMALY,
    RESULT_RECORD_COMPLETE,
    RESULT_RECOVERY_REQUIRED,
    VERIFIER_VERSION,
    BoundaryReceipt,
    ProjectAuditBridge,
    ProjectVerificationDTO,
    ProjectVerificationError,
    ProjectVerificationResult,
    RecoveryCoordinationError,
)

ProjectRecoveryCoordinator = RecoveryCoordinator
ProjectAuditEventBridge = ProjectAuditBridge
ProjectVerifierResult = ProjectVerificationResult

__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "BoundaryReceipt",
    "ProjectAuditBridge",
    "ProjectAuditEventBridge",
    "ProjectRecoveryCoordinator",
    "ProjectVerificationDTO",
    "ProjectVerificationError",
    "ProjectVerificationResult",
    "ProjectVerifierResult",
    "RecoveryCoordinationError",
    "RecoveryCoordinator",
    "RESULT_ANOMALY",
    "RESULT_RECORD_COMPLETE",
    "RESULT_RECOVERY_REQUIRED",
    "VERIFIER_VERSION",
    "ProjectVerifier",
    "startup_recovery_scan",
]
