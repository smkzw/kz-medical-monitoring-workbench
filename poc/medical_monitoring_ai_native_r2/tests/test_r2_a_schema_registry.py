"""Batch A -- schema registry: fail-closed compatibility tests.

Covers: known reads, unknown versions/schemas, compatible backward reads,
incompatible writes, current-version enforcement, frozen re-declaration.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mm_r2.schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaVersion,
    default_registry,
)


# ---------------------------------------------------------------------------
# Default registry (the single declaration point)
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_known_schemas_are_declared(self):
        reg = default_registry()
        for name in [
            "study_project", "source_revision", "listing_snapshot",
            "study_knowledge_pack", "rule_activation", "mapping_definition",
            "mapping_result", "canonical_fact", "snapshot_acceptance",
            "artifact_envelope", "acceptance_decision_record", "identity_algorithm",
            "provenance",
        ]:
            assert reg.known(name, "1"), f"{name}@1 must be registered"

    def test_each_schema_has_exactly_one_current_version(self):
        reg = default_registry()
        for name, _ in reg.declared_schemas():
            # current_version must not raise and must equal "1"
            assert reg.current_version(name) == "1"

    def test_default_registry_is_singleton(self):
        assert default_registry() is default_registry()


# ---------------------------------------------------------------------------
# Known read / unknown version / unknown schema
# ---------------------------------------------------------------------------

class TestKnownAndUnknown:
    def test_known_read_is_deterministic(self):
        reg = default_registry()
        sv1 = reg.get("canonical_fact", "1")
        sv2 = reg.get("canonical_fact", "1")
        assert sv1 is sv2  # same object from the registry
        assert sv1.schema_name == "canonical_fact"
        assert sv1.version == "1"

    def test_unknown_version_fails_closed(self):
        reg = default_registry()
        with pytest.raises(SchemaRegistryError, match="unknown schema/version"):
            reg.get("canonical_fact", "99")
        with pytest.raises(SchemaRegistryError):
            reg.assert_known("canonical_fact", "99")

    def test_unknown_schema_fails_closed(self):
        reg = default_registry()
        with pytest.raises(SchemaRegistryError, match="unknown schema/version"):
            reg.get("no_such_schema", "1")

    def test_known_is_boolean_not_raising(self):
        reg = default_registry()
        assert reg.known("canonical_fact", "1") is True
        assert reg.known("canonical_fact", "99") is False
        assert reg.known("no_such_schema", "1") is False


# ---------------------------------------------------------------------------
# Compatible backward read / incompatible write
# ---------------------------------------------------------------------------

class TestCompatibilityDecisions:
    def test_writable_requires_current_version(self):
        reg = default_registry()
        # current version is writable
        reg.assert_writable("canonical_fact", "1")
        # a hypothetical older version is not writable
        with pytest.raises(SchemaRegistryError, match="incompatible write"):
            reg.assert_writable("canonical_fact", "0")

    def test_readable_current_version_ok(self):
        reg = default_registry()
        reg.assert_readable("canonical_fact", "1")

    def test_readable_unknown_version_fails(self):
        reg = default_registry()
        with pytest.raises(SchemaRegistryError):
            reg.assert_readable("canonical_fact", "2")

    def test_backward_read_when_declared(self):
        # Build a local registry with an explicit backward-read declaration.
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "2", reads=("1",)))
        reg.register(SchemaVersion("widget", "1", deprecated=True))
        # current is "2"
        assert reg.current_version("widget") == "2"
        # "2" is readable (current)
        reg.assert_readable("widget", "2")
        # "1" is readable (backward, declared in reads)
        reg.assert_readable("widget", "1")
        # writing "1" is still forbidden
        with pytest.raises(SchemaRegistryError, match="incompatible write"):
            reg.assert_writable("widget", "1")

    def test_backward_read_not_declared_fails(self):
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "2"))
        reg.register(SchemaVersion("widget", "1", deprecated=True))
        # "1" is NOT in the reads tuple of "2"
        with pytest.raises(SchemaRegistryError, match="incompatible read"):
            reg.assert_readable("widget", "1")

    def test_writing_deprecated_version_fails(self):
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "2"))
        reg.register(SchemaVersion("widget", "1", deprecated=True))
        with pytest.raises(SchemaRegistryError, match="incompatible write"):
            reg.assert_writable("widget", "1")


# ---------------------------------------------------------------------------
# Registry is frozen (no silent drift)
# ---------------------------------------------------------------------------

class TestRegistryFrozen:
    def test_exact_redeclare_is_idempotent(self):
        reg = SchemaRegistry()
        sv = SchemaVersion("widget", "1", description="x")
        reg.register(sv)
        reg.register(sv)  # identical -> idempotent
        assert reg.known("widget", "1")

    def test_conflicting_redeclare_fails(self):
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "1", description="a"))
        with pytest.raises(SchemaRegistryError, match="frozen"):
            reg.register(SchemaVersion("widget", "1", description="b"))

    def test_zero_or_two_current_versions_is_error(self):
        reg = SchemaRegistry()
        # no versions -> current_version raises (unknown schema)
        with pytest.raises(SchemaRegistryError, match="unknown schema"):
            reg.current_version("widget")
        # two non-deprecated -> ambiguity error
        reg.register(SchemaVersion("widget", "1"))
        reg.register(SchemaVersion("widget", "2"))
        with pytest.raises(SchemaRegistryError, match="exactly one current"):
            reg.current_version("widget")

    # -- Blocker 6 regression: default registry is frozen at runtime --------

    def test_default_registry_is_frozen(self):
        reg = default_registry()
        assert reg.frozen is True

    def test_default_registry_rejects_runtime_mutation(self):
        reg = default_registry()
        with pytest.raises(SchemaRegistryError, match="frozen"):
            reg.register(SchemaVersion("rogue", "1"))

    def test_local_registry_mutable_until_frozen(self):
        reg = SchemaRegistry()
        assert reg.frozen is False
        reg.register(SchemaVersion("widget", "1"))
        reg.freeze()
        assert reg.frozen is True
        with pytest.raises(SchemaRegistryError, match="frozen"):
            reg.register(SchemaVersion("gadget", "1"))

    # -- VETO1: deep immutability of the frozen declaration table ----------

    def test_default_registry_by_name_is_immutable(self):
        """VETO1: the outer _by_name mapping cannot be mutated directly."""
        reg = default_registry()
        with pytest.raises(TypeError):
            reg._by_name["rogue"] = {"1": SchemaVersion("rogue", "1")}
        assert reg.known("rogue", "1") is False

    def test_default_registry_inner_mapping_is_immutable(self):
        """VETO1: an inner per-schema mapping cannot be mutated directly."""
        reg = default_registry()
        inner = reg._by_name["canonical_fact"]
        with pytest.raises(TypeError):
            inner["99"] = SchemaVersion("canonical_fact", "99")
        assert reg.known("canonical_fact", "99") is False

    def test_frozen_local_registry_by_name_is_immutable(self):
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "1"))
        reg.freeze()
        with pytest.raises(TypeError):
            reg._by_name["rogue"] = {}
        with pytest.raises(TypeError):
            reg._by_name["widget"]["2"] = SchemaVersion("widget", "2")
        assert reg.known("rogue", "1") is False
        assert reg.known("widget", "2") is False

    def test_frozen_registry_attributes_cannot_be_rebound(self):
        reg = SchemaRegistry()
        reg.register(SchemaVersion("widget", "1"))
        reg.freeze()
        with pytest.raises(FrozenInstanceError):
            reg._by_name = {"rogue": {"1": SchemaVersion("rogue", "1")}}
        with pytest.raises(FrozenInstanceError):
            reg._frozen = False
        assert reg.known("rogue", "1") is False
        assert reg.frozen is True

    def test_default_registry_attributes_cannot_be_rebound(self):
        reg = default_registry()
        with pytest.raises(FrozenInstanceError):
            reg._by_name = {"rogue": {"1": SchemaVersion("rogue", "1")}}
        with pytest.raises(FrozenInstanceError):
            reg._frozen = False
        assert reg.known("rogue", "1") is False
        with pytest.raises(SchemaRegistryError, match="frozen"):
            reg.register(SchemaVersion("rogue", "1"))
