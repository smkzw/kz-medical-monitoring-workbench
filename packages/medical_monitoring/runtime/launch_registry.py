"""Synthetic/offline R7 Slice-07C-3/4 and Slice-08A registry.

The registry is the durable, project-scoped boundary for product
``prepare-and-start`` requests and the single atomic result-publication row.
It reserves one internal run and one opaque public navigation token before
preparation or background start work runs.  Publication identity is frozen
independently from completion-dependent receipt and authority facts.

This module intentionally uses only the Python standard library.  It does not
prepare manifests, bind runs, start workers, build authority packets, or open
a service.  Those operations consume this registry through the small durable
state API below.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import sqlite3
import threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, Union
from uuid import uuid4

from .continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    PlanValidationError,
    validate_carry_forward_plan,
)

from .launch_schema import (
    BASE_DDL as _BASE_DDL,
    CONTINUITY_DDL as _CONTINUITY_DDL,
    CONTINUITY_INDEX_DDL as _CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL as _CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL as _CONTINUITY_PLANS_DDL,
    LAUNCH_DDL as _DDL,
    PUBLICATION_DDL as _PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL as _RESULT_CONTEXT_INDEX_DDL,
)

from .launch_registry_contracts import *
from .launch_registry_core_mixin import LaunchRegistryCoreMixin
from .launch_registry_publication_mixin import LaunchRegistryPublicationMixin
from .launch_registry_publication_state_mixin import LaunchRegistryPublicationStateMixin
from .launch_registry_continuity_mixin import LaunchRegistryContinuityMixin
from .launch_registry_state_mixin import LaunchRegistryStateMixin


class LaunchRegistry(
    LaunchRegistryCoreMixin,
    LaunchRegistryPublicationMixin,
    LaunchRegistryPublicationStateMixin,
    LaunchRegistryContinuityMixin,
    LaunchRegistryStateMixin,
):
    """Project-scoped SQLite launch, publication and continuity registry."""

# Store naming aliases used by adjacent R7 code and tests.
LaunchRegistryStore = LaunchRegistry
ResultPublicationStore = LaunchRegistry
PublicationStore = LaunchRegistry
RunLaunchRegistry = LaunchRegistry
LaunchResult = LaunchReservation
PublicRunRecord = LaunchRecord
PublicationResult = ResultPublication
request_fingerprint = compute_request_fingerprint
publication_fingerprint = compute_publication_fingerprint


__all__ = [
    "SCHEMA_VERSION_V1",
    "SCHEMA_VERSION_V2",
    "SCHEMA_VERSION_V3",
    "SCHEMA_VERSION_V4",
    "SCHEMA_VERSION_V5",
    "SCHEMA_VERSION",
    "LAUNCH_REGISTRY_DB_NAME",
    "BUSY_TIMEOUT_MS",
    "DEFAULT_HISTORY_LIMIT",
    "MAX_HISTORY_LIMIT",
    "RESULT_CONTEXT_TOKEN_PREFIX",
    "PUBLICATION_REVISION",
    "RESULT_PUBLICATION_REVISION",
    "RESULT_PUBLICATION_PUBLISHING",
    "RESULT_PUBLICATION_AVAILABLE",
    "RESULT_PUBLICATION_RECOVERABLE_FAILED",
    "RESULT_PUBLICATION_BLOCKED",
    "PUBLICATION_STATE_PUBLISHING",
    "PUBLICATION_STATE_AVAILABLE",
    "PUBLICATION_STATE_RECOVERABLE_FAILED",
    "PUBLICATION_STATE_BLOCKED",
    "PUBLICATION_STATE_VALUES",
    "PUBLICATION_PUBLISHING",
    "PUBLICATION_AVAILABLE",
    "PUBLICATION_RECOVERABLE_FAILED",
    "PUBLICATION_BLOCKED",
    "RESULT_PUBLICATION_STATE_VALUES",
    "MODE_DAILY",
    "MODE_PRE_LOCK",
    "MODE_POST_LOCK_PRE_CFDI",
    "CONTINUITY_PLAN_STATE_STAGING",
    "CONTINUITY_PLAN_STATE_VERIFIED",
    "CONTINUITY_PLAN_STATE_PUBLISHED",
    "CONTINUITY_PLAN_STATE_BLOCKED",
    "CONTINUITY_PLAN_STATE_VALUES",
    "CONTINUITY_PLAN_STATUS_STAGING",
    "CONTINUITY_PLAN_STATUS_VERIFIED",
    "CONTINUITY_PLAN_STATUS_PUBLISHED",
    "CONTINUITY_PLAN_STATUS_BLOCKED",
    "CONTINUITY_PLAN_STATUS_VALUES",
    "CONTINUITY_PLAN_STAGING",
    "CONTINUITY_PLAN_VERIFIED",
    "CONTINUITY_PLAN_PUBLISHED",
    "CONTINUITY_PLAN_BLOCKED",
    "SUPPORTED_MODES",
    "BASIS_FULL",
    "BASIS_INCREMENTAL",
    "SUPPORTED_EXECUTION_BASES",
    "STATE_WAITING_START",
    "STATE_RUNNING",
    "STATE_STOPPING",
    "STATE_INTERRUPTED_RESUMABLE",
    "STATE_COMPLETED",
    "STATE_ENDED_INCOMPLETE",
    "STATE_FAILED",
    "RUN_STATE_VALUES",
    "LaunchRegistryError",
    "IdempotencyConflictError",
    "LaunchRequest",
    "LaunchRecord",
    "CarryForwardItem",
    "CarryForwardPlan",
    "PlanValidationError",
    "LaunchReservation",
    "ResultPublication",
    "PublicationResult",
    "canonical_json",
    "content_digest",
    "normalize_request",
    "canonical_request_fingerprint",
    "compute_request_fingerprint",
    "publication_fingerprint_payload",
    "compute_publication_fingerprint",
    "canonical_publication_fingerprint",
    "compute_result_publication_fingerprint",
    "public_run_token",
    "request_fingerprint",
    "publication_fingerprint",
    "derive_public_run_token",
    "derive_continuity_plan_id",
    "LaunchRegistry",
    "LaunchRegistryStore",
    "ResultPublicationStore",
    "PublicationStore",
    "RunLaunchRegistry",
    "LaunchResult",
    "PublicRunRecord",
]
