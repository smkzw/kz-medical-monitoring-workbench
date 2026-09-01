"""SQLite authoritative store facade with capability-focused mixins."""

from .store_common import *
from .store_common import (
    _runtime_schema_shape,
    _shape_from_ddl,
    _ANALYSIS_TRANSITIONS,
    _REVIEW_TRANSITIONS,
    _OUTPUT_ORDER,
    _WORK_UNIT_IDENTITY_KEYS,
    _IMMUTABLE_DOMAIN_OBJECT_KINDS,
    _CAPABILITY_ASSIGNMENT_KIND,
    _CAPABILITY_ASSIGNMENT_SCHEMA,
    _RESERVED_INTERNAL_AUDIT_EVENTS,
    _IdempotencyLedgerConflict,
    _RuntimeAttemptJournal,
    _SCHEMA,
    _build_current_runtime_schema_shape,
    _CURRENT_RUNTIME_SCHEMA_SHAPE,
    _assert_current_schema,
)
from .store_base import StoreBaseMixin
from .store_manifest import StoreManifestMixin
from .store_work_units import StoreWorkUnitMixin
from .store_attempts import StoreAttemptMixin
from .store_artifacts import StoreArtifactMixin


class Store(
    StoreBaseMixin,
    StoreManifestMixin,
    StoreWorkUnitMixin,
    StoreAttemptMixin,
    StoreArtifactMixin,
):
    """Single SQLite store authority; mixins share one connection/transaction boundary."""
