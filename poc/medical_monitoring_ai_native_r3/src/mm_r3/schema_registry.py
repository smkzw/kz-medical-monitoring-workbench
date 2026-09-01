"""Schema registry -- the sole schema/version declaration point for the R3
kernel (worker_01-owned, R3-A).

Mirrors the R2 ``schema_registry`` contract: explicit, append-only, frozen
after construction.  R3 declares its own independent schema namespace so the
R3 POC never mutates the frozen R2 registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Dict, List, Optional, Tuple

__all__ = [
    "SchemaRegistry",
    "SchemaRegistryError",
    "SchemaVersion",
    "default_registry",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SchemaRegistryError(Exception):
    """Fail-closed schema/version violation."""


# ---------------------------------------------------------------------------
# Version descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SchemaVersion:
    """A single registered version of an R3 domain schema."""

    schema_name: str
    version: str
    deprecated: bool = False
    reads: Tuple[str, ...] = ()
    description: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class SchemaRegistry:
    """Explicit, append-only registry of every R3 domain schema version.

    Populated once at process start and frozen thereafter.  Mirrors R2 but is
    a fully independent registry/namespace.
    """

    _by_name: Dict[str, Dict[str, SchemaVersion]] = field(default_factory=dict)
    _frozen: bool = False

    def register(self, sv: SchemaVersion) -> None:
        if self._frozen:
            raise SchemaRegistryError(
                f"registry is frozen; cannot register {sv.schema_name!r}"
                f"@{sv.version!r}"
            )
        versions = self._by_name.setdefault(sv.schema_name, {})
        existing = versions.get(sv.version)
        if existing is not None and existing != sv:
            raise SchemaRegistryError(
                f"schema {sv.schema_name!r} version {sv.version!r} already "
                f"registered with a different descriptor; registry is frozen"
            )
        versions[sv.version] = sv

    def register_many(self, svs: List[SchemaVersion]) -> None:
        for sv in svs:
            self.register(sv)

    def freeze(self) -> None:
        object.__setattr__(self, "_frozen", True)
        inner = {
            name: MappingProxyType(dict(versions))
            for name, versions in self._by_name.items()
        }
        object.__setattr__(self, "_by_name", MappingProxyType(inner))

    @property
    def frozen(self) -> bool:
        return self._frozen

    def known(self, schema_name: str, version: str) -> bool:
        return version in self._by_name.get(schema_name, {})

    def get(self, schema_name: str, version: str) -> SchemaVersion:
        sv = self._by_name.get(schema_name, {}).get(version)
        if sv is None:
            raise SchemaRegistryError(
                f"unknown schema/version: {schema_name!r}@{version!r}"
            )
        return sv

    def current_version(self, schema_name: str) -> str:
        versions = self._by_name.get(schema_name)
        if not versions:
            raise SchemaRegistryError(f"unknown schema: {schema_name!r}")
        current = [v for v in versions.values() if not v.deprecated]
        if len(current) != 1:
            names = sorted(v.version for v in current)
            raise SchemaRegistryError(
                f"schema {schema_name!r} must have exactly one current "
                f"(non-deprecated) version, found {names}"
            )
        return current[0].version

    def is_current(self, schema_name: str, version: str) -> bool:
        sv = self.get(schema_name, version)
        return not sv.deprecated

    def assert_writable(self, schema_name: str, version: str) -> None:
        current = self.current_version(schema_name)
        if version != current:
            raise SchemaRegistryError(
                f"incompatible write: {schema_name!r}@{version!r} is not the "
                f"current version (current={current!r}); new objects must use "
                f"the current version"
            )

    def declared_schemas(self) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for name, versions in self._by_name.items():
            for v in versions:
                out.append((name, v))
        return sorted(out)


# ---------------------------------------------------------------------------
# Default frozen registry
# ---------------------------------------------------------------------------

def _build_default_registry() -> SchemaRegistry:
    """Construct the one explicit registry for the R3 kernel.

    R3-A seeds this registry with the source/knowledge/claim/conflict
    schemas.  R3-B and R3-C append their own schemas here (still the single
    declaration point).
    """
    reg = SchemaRegistry()
    reg.register_many([
        # R3-A (worker_01)
        SchemaVersion("r3_source_revision", "1"),
        SchemaVersion("r3_source_classification", "1"),
        SchemaVersion("r3_knowledge_pack", "1"),
        SchemaVersion("r3_claim", "1"),
        SchemaVersion("r3_claim_authority", "1"),
        SchemaVersion("r3_source_conflict", "1"),
        SchemaVersion("r3_conflict_resolution", "1"),
        # R3-B (worker_02)
        SchemaVersion("r3_workbook_profile", "1"),
        SchemaVersion("r3_table_profile", "1"),
        SchemaVersion("r3_field_profile", "1"),
        SchemaVersion("r3_mapping_candidate", "1"),
        SchemaVersion("r3_field_mapping", "1"),
        SchemaVersion("r3_mapping_result", "1"),
        SchemaVersion("r3_identity_algorithm", "1"),
        SchemaVersion("r3_record_identity", "1"),
        SchemaVersion("r3_identity_resolution", "1"),
        SchemaVersion("r3_normalized_value", "1"),
        # R3-C (worker_03)
        SchemaVersion("r3_snapshot_facts", "1"),
        SchemaVersion("r3_snapshot_diff", "1"),
        SchemaVersion("r3_change_record", "1"),
        SchemaVersion("r3_impact_propagation", "1"),
        SchemaVersion("r3_rule_draft", "1"),
        SchemaVersion("r3_rule_simulation", "1"),
        SchemaVersion("r3_rule_activation", "1"),
        SchemaVersion("r3_evaluation_scope", "1"),
    ])
    reg.freeze()
    return reg


_DEFAULT: Optional[SchemaRegistry] = None


def default_registry() -> SchemaRegistry:
    """Return the process-wide frozen default registry (lazily built once)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = _build_default_registry()
    return _DEFAULT
