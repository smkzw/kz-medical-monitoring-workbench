"""Schema registry -- the sole schema/version declaration point for the R2
domain kernel (Design v1.1 section 5; implementation plan R2 steps 1-2).

Every R2 domain object carries a ``(schema_name, schema_version)`` pair that
must be registered here before the object can be materialized or validated.
The registry is frozen at construction: there is exactly one explicit
declaration table per process.  Compatibility is strict and fail-closed:

* a known ``(schema_name, version)`` read is deterministic;
* an unknown version (or unknown schema) fails closed with
  :class:`SchemaRegistryError`;
* a "backward read" of an older compatible version is allowed only when the
  registered :attr:`SchemaVersion.reads` explicitly lists it;
* writing an object at an incompatible (non-current, non-declared) version
  always fails.

The registry carries no domain semantics: it only decides whether a
(schema_name, version) pair is known, current, and read/write-compatible.
Domain objects consult the registry via :func:`assert_known` /
:func:`assert_writable` / :func:`assert_readable` at construction and
deserialization time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Dict, List, Optional, Set, Tuple

__all__ = [
    "SchemaVersion",
    "SchemaRegistry",
    "SchemaRegistryError",
    "default_registry",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SchemaRegistryError(Exception):
    """Fail-closed schema/version violation.

    Raised for unknown schemas, unknown versions, incompatible backward reads,
    and incompatible writes.  The message always names the schema/version and
    the registry's decision.
    """


# ---------------------------------------------------------------------------
# Version descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SchemaVersion:
    """A single registered version of a domain schema.

    ``reads`` lists older versions whose objects this version may read
    (backward-compatible deserialization).  It is *not* transitive and it is
    *not* symmetric: writing always requires the current version.

    ``deprecated`` marks versions that are still readable but must never be
    written by new code.
    """

    schema_name: str
    version: str
    reads: Tuple[str, ...] = ()
    deprecated: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SchemaRegistry:
    """Explicit, append-only registry of every R2 domain schema version.

    The registry is the single declaration surface.  It is populated once at
    process start (:func:`default_registry`) and treated as frozen thereafter:
    :meth:`register` rejects duplicate declarations so accidental drift is
    detected rather than silently absorbed.
    """

    _by_name: Dict[str, Dict[str, SchemaVersion]] = field(default_factory=dict)
    _frozen: bool = False

    # -- declaration -------------------------------------------------------

    def register(self, sv: SchemaVersion) -> None:
        """Declare a schema version.

        Re-declaring the exact same ``(schema_name, version)`` idempotently is
        allowed only if the descriptor is byte-identical; any difference fails
        closed (the registry is a frozen contract, not a mutable config).

        Once :meth:`freeze` is called, *any* new declaration fails closed --
        the default process-wide registry is frozen after construction so
        callers cannot append rogue schemas at runtime.  Local registries
        remain mutable until explicitly frozen.
        """
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
        """Freeze this registry so no further declarations are accepted.

        Freezing also *deeply* freezes the declaration table: the outer
        ``_by_name`` mapping and every inner per-schema mapping become
        read-only dict views, so a caller cannot insert a schema/version by
        bypassing :meth:`register` (e.g. ``reg._by_name["rogue"] = {...}``).
        """
        object.__setattr__(self, "_frozen", True)
        inner = {
            name: MappingProxyType(dict(versions))
            for name, versions in self._by_name.items()
        }
        object.__setattr__(self, "_by_name", MappingProxyType(inner))

    @property
    def frozen(self) -> bool:
        return self._frozen

    # -- queries -----------------------------------------------------------

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
        """Return the non-deprecated current version for a schema.

        A schema must have exactly one non-deprecated version: the write
        target.  Zero or multiple current versions is a registry-consistency
        error, not a caller error.
        """
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

    # -- compatibility decisions ------------------------------------------

    def assert_known(self, schema_name: str, version: str) -> None:
        """Fail closed if ``(schema_name, version)`` is not declared."""
        self.get(schema_name, version)

    def assert_writable(self, schema_name: str, version: str) -> None:
        """Fail closed unless ``version`` is the current (non-deprecated) one.

        Writing historical or deprecated versions is forbidden: the registry
        is the source of truth for which version new objects may carry.
        """
        current = self.current_version(schema_name)
        if version != current:
            raise SchemaRegistryError(
                f"incompatible write: {schema_name!r}@{version!r} is not the "
                f"current version (current={current!r}); new objects must use "
                f"the current version"
            )

    def assert_readable(self, schema_name: str, version: str) -> None:
        """Fail closed unless ``version`` is known and read-compatible.

        A version is readable if it is the current version or if the current
        version's ``reads`` tuple explicitly lists it (backward read).
        Reading a deprecated version is allowed (audit/migration), reading an
        unknown version is not.
        """
        self.assert_known(schema_name, version)
        current = self.current_version(schema_name)
        if version == current:
            return
        sv = self.get(schema_name, current)
        if version in sv.reads:
            return
        raise SchemaRegistryError(
            f"incompatible read: {schema_name!r}@{version!r} is not the "
            f"current version ({current!r}) and is not declared as backward-"
            f"readable by it"
        )

    def declared_schemas(self) -> List[Tuple[str, str]]:
        """Snapshot of all declared ``(schema_name, version)`` pairs, sorted."""
        out: List[Tuple[str, str]] = []
        for name, versions in self._by_name.items():
            for v in versions:
                out.append((name, v))
        return sorted(out)


# ---------------------------------------------------------------------------
# Default frozen registry
# ---------------------------------------------------------------------------

def _build_default_registry() -> SchemaRegistry:
    """Construct the one explicit registry for the R2 kernel.

    Batch A owns the domain-object schemas declared here.  Batches B and C
    add their own schemas by extending this function (still the single
    declaration point).  Each schema has exactly one current version; older
    versions, if any, are listed in ``reads``.
    """
    reg = SchemaRegistry()
    reg.register_many([
        SchemaVersion("study_project", "1"),
        SchemaVersion("source_revision", "1"),
        SchemaVersion("listing_snapshot", "1"),
        SchemaVersion("study_knowledge_pack", "1"),
        SchemaVersion("rule_activation", "1"),
        SchemaVersion("mapping_definition", "1"),
        SchemaVersion("mapping_result", "1"),
        SchemaVersion("canonical_fact", "1"),
        SchemaVersion("snapshot_acceptance", "1"),
        SchemaVersion("artifact_envelope", "1"),
        SchemaVersion("acceptance_decision_record", "1"),
        SchemaVersion("identity_algorithm", "1"),
        SchemaVersion("provenance", "1"),
        # Batch B (worker_02): risk lifecycle, adjudication, baselines,
        # modes, and diff contracts.
        SchemaVersion("risk_candidate", "1"),
        SchemaVersion("risk_instance", "1"),
        SchemaVersion("risk_transition", "1"),
        SchemaVersion("adjudication_record", "1"),
        SchemaVersion("data_baseline", "1"),
        SchemaVersion("medical_decision_version", "1"),
        SchemaVersion("mode_contract", "1"),
        SchemaVersion("monitoring_run", "1"),
        SchemaVersion("snapshot_diff", "1"),
        SchemaVersion("diff_entry", "1"),
        # Batch C (worker_03): persistence, audit, migration, legacy adapter.
        SchemaVersion("publication_revision", "1"),
        SchemaVersion("audit_event_v1", "1"),
        SchemaVersion("monitoring_result_snapshot", "1"),
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
