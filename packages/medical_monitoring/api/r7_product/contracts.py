"""Request contracts for the medical-monitoring R7 product API."""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...runtime import run_setup as rs
from ...runtime.project_lifecycle import (
    ProjectOpenDTO,
    ProjectUpgradeProgressDTO,
    ProjectUpgradeResultDTO,
)
from ...runtime.runtime_progress import (
    RuntimeProgressError,
    validate_public_data_cutoff,
)

class ProductPublicationError(RuntimeError):
    """Stable product publication-gate failure without lower-layer details."""

    def __init__(self, code: str, *, recoverable: bool = False) -> None:
        self.code = str(code)
        self.recoverable = bool(recoverable)
        super().__init__(self.code)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

def _validate_operation_reference(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None
    ):
        raise ValueError("request_validation_failed")
    return value


def _validate_optional_idempotency_key(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("request_validation_failed")
    return value


class ProductBackupRequest(_StrictModel):
    """Optional caller idempotency key for project backup creation."""

    idempotency_key: Optional[str] = None

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: Optional[str]) -> Optional[str]:
        return _validate_optional_idempotency_key(value)


class ProductRestorePreflightRequest(_StrictModel):
    """Server-resolved backup operation used for restore impact preview."""

    backup_operation_id: Optional[str] = None
    operation_id: Optional[str] = None
    idempotency_key: Optional[str] = None

    @field_validator("backup_operation_id", "operation_id")
    @classmethod
    def validate_operation_id(cls, value: Optional[str]) -> Optional[str]:
        return _validate_operation_reference(value)

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: Optional[str]) -> Optional[str]:
        return _validate_optional_idempotency_key(value)


class ProductRestoreRequest(_StrictModel):
    """Restore request carrying opaque operation references only."""

    backup_operation_id: Optional[str] = None
    operation_id: Optional[str] = None
    preflight_operation_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    confirmation: bool = False

    @field_validator(
        "backup_operation_id", "operation_id", "preflight_operation_id"
    )
    @classmethod
    def validate_operation_id(cls, value: Optional[str]) -> Optional[str]:
        return _validate_operation_reference(value)

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: Optional[str]) -> Optional[str]:
        return _validate_optional_idempotency_key(value)

    @field_validator("confirmation", mode="before")
    @classmethod
    def validate_confirmation(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("request_validation_failed")
        return value


class ProductProjectUpgradeRequest(_StrictModel):
    """Explicit confirmation and opaque retry key for project upgrade."""

    idempotency_key: Optional[str] = None
    confirmation: bool = True

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: Optional[str]) -> Optional[str]:
        return _validate_optional_idempotency_key(value)

    @field_validator("confirmation", mode="before")
    @classmethod
    def validate_confirmation(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("request_validation_failed")
        return value


ProjectOpenResult = ProjectOpenDTO
ProjectUpgradeProgress = ProjectUpgradeProgressDTO
ProjectUpgradeResult = ProjectUpgradeResultDTO


class ProductBootstrapRequest(_StrictModel):
    """Empty body; present so unknown fields fail closed."""

class ProductCreateRunRequest(_StrictModel):
    """Product DTO: path supplies project identity; scopes are auto-selected."""

    run_id: str
    mode: str
    execution_basis: str
    data_cutoff: str
    source_revision_id: str
    prior_accepted_snapshot_ref: Optional[str] = None
    capability_scope_key: str = ""

    @field_validator("run_id", "data_cutoff", "source_revision_id")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError("invalid_identity")
        return value

    @field_validator("data_cutoff")
    @classmethod
    def validate_data_cutoff(cls, value: str) -> str:
        try:
            return validate_public_data_cutoff(value)
        except RuntimeProgressError as exc:
            raise ValueError(exc.code) from exc

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in {"daily", "pre_lock", "post_lock_pre_cfdi"}:
            raise ValueError("unknown_mode")
        return value

    @field_validator("execution_basis")
    @classmethod
    def validate_basis(cls, value: str) -> str:
        if value not in {"full", "incremental"}:
            raise ValueError("unknown_execution_basis")
        return value

    @field_validator("prior_accepted_snapshot_ref")
    @classmethod
    def validate_prior_ref(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("invalid_prior_accepted_snapshot_ref")
        return value

    @field_validator("capability_scope_key")
    @classmethod
    def validate_capability_scope(cls, value: str) -> str:
        if value is None:
            return ""
        if not isinstance(value, str) or value != value.strip():
            raise ValueError("empty_or_illegal_scope_key")
        return value


class ProductPrepareExecutionRequest(_StrictModel):
    """Explicit work-unit definition for one offline preparation."""

    work_units: list[dict[str, Any]]
    execution_kind: Literal["deterministic", "harness", "ai_candidate"] = (
        "deterministic"
    )
    execution_mode: Optional[
        Literal["deterministic", "harness", "ai_candidate"]
    ] = None


class ProductExecutionActionRequest(_StrictModel):
    """Execution actions have no client-controlled fields."""


class ProductRiskRulePreviewRequest(_StrictModel):
    """Natural-language special-risk draft; confirmation is a separate route."""

    source_text: str
    applicable_scope: str = "项目内全部适用范围"
    starting_run: str = "本次确认后明确选择的运行"


class ProductRiskRuleRequest(_StrictModel):
    """Confirmed risk-rule draft or a previously returned preview token."""

    preview_token: Optional[str] = None
    candidate_id: Optional[str] = None
    starting_run: Optional[str] = None
    created_at: str = ""
    idempotency_key: Optional[str] = None
    # A nested draft is accepted for clients that retain the full preview
    # projection; path identity is checked by the registry.
    draft: Optional[dict[str, Any]] = None
    preview: Optional[dict[str, Any]] = None


class ProductPrepareAndStartRequest(_StrictModel):
    """Product launch DTO; the server derives all run identity and work units."""

    current_snapshot_token: str
    mode: str
    execution_basis: str
    baseline_token: Optional[str] = None
    risk_rule_tokens: list[str] = Field(default_factory=list)
    idempotency_key: str

    @field_validator("current_snapshot_token", "idempotency_key")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError("request_validation_failed")
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in rs.SUPPORTED_MODES:
            raise ValueError("unknown_mode")
        return value

    @field_validator("execution_basis")
    @classmethod
    def validate_execution_basis(cls, value: str) -> str:
        if value not in rs.SUPPORTED_EXECUTION_BASES:
            raise ValueError("unknown_execution_basis")
        return value

    @field_validator("baseline_token")
    @classmethod
    def validate_baseline(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (
            not isinstance(value, str) or not value.strip() or value != value.strip()
        ):
            raise ValueError("request_validation_failed")
        return value

    @field_validator("risk_rule_tokens")
    @classmethod
    def validate_rule_tokens(cls, value: list[str]) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("request_validation_failed")
        for token in value:
            if (
                not isinstance(token, str)
                or not token.strip()
                or token != token.strip()
            ):
                raise ValueError("request_validation_failed")
        return value


class ProductPublicationRequest(_StrictModel):
    """Publication retries carry only a caller-owned retry handle."""

    idempotency_key: str

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
        ):
            raise ValueError("request_validation_failed")
        return value

__all__ = [
    "ProductPublicationError",
    "_StrictModel",
    "ProductBackupRequest",
    "ProductRestorePreflightRequest",
    "ProductRestoreRequest",
    "ProductProjectUpgradeRequest",
    "ProjectOpenResult",
    "ProjectUpgradeProgress",
    "ProjectUpgradeResult",
    "ProductBootstrapRequest",
    "ProductCreateRunRequest",
    "ProductPrepareExecutionRequest",
    "ProductExecutionActionRequest",
    "ProductRiskRulePreviewRequest",
    "ProductRiskRuleRequest",
    "ProductPrepareAndStartRequest",
    "ProductPublicationRequest",
]

