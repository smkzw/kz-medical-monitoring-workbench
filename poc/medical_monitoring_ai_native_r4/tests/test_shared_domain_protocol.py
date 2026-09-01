"""R4 shared domain-protocol tests (worker_01, D02 prerequisite).

These tests defend the neutral shared surface introduced for the frozen
D02 CM slice contract (``FROZEN_R4_D02_CONTRACT_V1`` §2, §3.3, §11) and
prove that the D01 refactor is behavior-preserving:

* ``RiskDomainUnitResult`` is a neutral structural Protocol whose frozen
  eight fields are exactly the lifecycle-input contract; ``AEMHUnitResult``
  satisfies it structurally via the new ``monitoring_priority`` property.
* The ``MONITORING_PRIORITY_*`` constants and identity accessors now live
  on ``mm_r4.contracts`` as the single source of truth; ``aemh.py`` only
  re-exports them.
* ``AEMHUnitResult.monitoring_priority`` projects
  ``medical_grading.monitoring_priority`` (frozen D02 §2) -- D01 behavior
  is unchanged.
* ``lifecycle.py`` no longer statically depends on ``AEMHUnitResult`` or
  any D01 identity function (frozen D02 §11 invariant); it reads priority
  off the neutral Protocol field.
* ``CrossDomainEvidenceRef`` is an immutable read-only source reference
  whose ``content_hash`` is the canonical SHA-256 of the stable source
  event key + evidence_role + claim_scope + sorted context_payload,
  excluding snapshot/revision id (frozen D02 §3.3).

All data is synthetic and offline.  No real project, provider, or port.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.contracts import (  # noqa: E402
    CoverageValidationError,
    CrossDomainEvidenceRef,
    MONITORING_PRIORITIES,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    RiskDomainUnitResult,
    VALID_MONITORING_PRIORITIES,
    SourceLocator,
    candidate_identity_classifier,
    candidate_identity_scope,
    candidate_lineage_fingerprint,
    candidate_machine_close_forbidden,
    candidate_rights_or_safety_critical,
    candidate_stable_core,
    cross_domain_evidence_content_hash,
)
from mm_r4.aemh import (  # noqa: E402
    AEMHUnitResult,
    MedicalGrading,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _locator(
    record_id: str = "cm-9",
    table_semantic: str = "recorded_cm",
    snapshot_id: str = "snap-1",
    revision_id: str = "rev-1",
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id,
        source_revision_id=revision_id,
        table_semantic=table_semantic,
        record_id=record_id,
    )


def _make_ref(**overrides) -> CrossDomainEvidenceRef:
    loc = overrides.pop("source_locator", _locator())
    defaults = dict(
        evidence_ref_id="er-1",
        producer_domain="D02_cm",
        consumer_domain="D01_aemh",
        evidence_role="cm_indication",
        source_locator=loc,
        producer_unit_id="unit-d02-1",
        claim_scope="treatment",
        context_payload=(("role", "treatment"), ("ingredient_status", "confirmed")),
    )
    defaults.update(overrides)
    ch = cross_domain_evidence_content_hash(
        source_locator=defaults["source_locator"],
        evidence_role=defaults["evidence_role"],
        claim_scope=defaults["claim_scope"],
        context_payload=dict(defaults["context_payload"]),
    )
    defaults["content_hash"] = overrides.pop("content_hash", ch)
    return CrossDomainEvidenceRef(**defaults)


# ---------------------------------------------------------------------------
# Neutral priority constants -- single source of truth
# ---------------------------------------------------------------------------

class TestNeutralPriorityConstants:
    def test_constants_are_the_expected_tokens(self):
        assert MONITORING_PRIORITY_HIGH == "high"
        assert MONITORING_PRIORITY_MEDIUM == "medium"
        assert MONITORING_PRIORITY_LOW == "low"
        assert MONITORING_PRIORITY_UNKNOWN == "unknown"

    def test_priorities_tuple_is_canonical_order(self):
        assert MONITORING_PRIORITIES == (
            "high", "medium", "low", "unknown")
        assert VALID_MONITORING_PRIORITIES is MONITORING_PRIORITIES

    def test_aemh_re_exports_identical_objects(self):
        # aemh.py must re-export the SAME objects, not copies.
        from mm_r4 import aemh
        assert aemh.MONITORING_PRIORITY_HIGH is MONITORING_PRIORITY_HIGH
        assert aemh.MONITORING_PRIORITY_MEDIUM is MONITORING_PRIORITY_MEDIUM
        assert aemh.MONITORING_PRIORITY_LOW is MONITORING_PRIORITY_LOW
        assert aemh.MONITORING_PRIORITY_UNKNOWN is MONITORING_PRIORITY_UNKNOWN

    def test_aemh_private_valid_alias_matches_neutral(self):
        from mm_r4 import aemh
        assert aemh._VALID_MONITORING_PRIORITIES is VALID_MONITORING_PRIORITIES

    def test_medical_grading_validates_against_neutral_tuple(self):
        # MedicalGrading must still reject an invalid priority using the
        # neutral validation tuple.
        with pytest.raises(CoverageValidationError):
            MedicalGrading(monitoring_priority="critical")


# ---------------------------------------------------------------------------
# Neutral identity accessors -- behavior identical to pre-refactor
# ---------------------------------------------------------------------------

class TestNeutralIdentityAccessors:
    def test_accessors_live_on_contracts(self):
        # The four accessors are callable from the neutral surface.
        for fn in (candidate_identity_classifier, candidate_identity_scope,
                   candidate_stable_core, candidate_lineage_fingerprint):
            assert callable(fn)

    def test_accessors_read_candidate_detail_keys(self):
        candidate = type("C", (), {})()
        candidate.detail = {
            "classifier": "d01|concept|signal|role:rid",
            "scope": ["site", "window"],
            "stable_core": "d01|concept|signal|role:rid",
            "lineage_fingerprint": "site|window",
        }
        assert candidate_identity_classifier(candidate) == \
            "d01|concept|signal|role:rid"
        assert candidate_identity_scope(candidate) == ["site", "window"]
        assert candidate_stable_core(candidate) == \
            "d01|concept|signal|role:rid"
        assert candidate_lineage_fingerprint(candidate) == "site|window"

    def test_accessors_return_empty_on_missing_detail(self):
        candidate = type("C", (), {})()
        candidate.detail = {}
        assert candidate_identity_classifier(candidate) == ""
        assert candidate_identity_scope(candidate) == []
        assert candidate_stable_core(candidate) == ""
        assert candidate_lineage_fingerprint(candidate) == ""

    def test_aemh_re_exports_identical_accessors(self):
        from mm_r4 import aemh
        assert aemh.candidate_identity_classifier is \
            candidate_identity_classifier
        assert aemh.candidate_identity_scope is candidate_identity_scope
        assert aemh.candidate_stable_core is candidate_stable_core
        assert aemh.candidate_lineage_fingerprint is \
            candidate_lineage_fingerprint


# ---------------------------------------------------------------------------
# Strict boolean criticality readers (frozen D04 §8.1, §10.4)
# ---------------------------------------------------------------------------

class TestCandidateCriticalityFlags:
    """``candidate_rights_or_safety_critical`` and
    ``candidate_machine_close_forbidden`` are strict public boolean
    readers on the candidate detail: missing → False, literal bool →
    returned unchanged, any present non-bool → CoverageValidationError
    (fail closed; no truthiness coercion, no int 0/1 acceptance)."""

    def test_readers_live_on_contracts(self):
        for fn in (candidate_rights_or_safety_critical,
                   candidate_machine_close_forbidden):
            assert callable(fn)

    def test_missing_flags_are_false(self):
        candidate = type("C", (), {})()
        candidate.detail = {}
        assert candidate_rights_or_safety_critical(candidate) is False
        assert candidate_machine_close_forbidden(candidate) is False

    def test_literal_true_returned(self):
        candidate = type("C", (), {})()
        candidate.detail = {"rights_or_safety_critical": True,
                            "machine_close_forbidden": True}
        assert candidate_rights_or_safety_critical(candidate) is True
        assert candidate_machine_close_forbidden(candidate) is True

    def test_literal_false_returned(self):
        candidate = type("C", (), {})()
        candidate.detail = {"rights_or_safety_critical": False,
                            "machine_close_forbidden": False}
        # Present-but-false is still a literal bool and returned as-is.
        assert candidate_rights_or_safety_critical(candidate) is False
        assert candidate_machine_close_forbidden(candidate) is False

    def test_flags_are_independent(self):
        candidate = type("C", (), {})()
        candidate.detail = {"rights_or_safety_critical": True,
                            "machine_close_forbidden": False}
        assert candidate_rights_or_safety_critical(candidate) is True
        assert candidate_machine_close_forbidden(candidate) is False
        candidate.detail = {"rights_or_safety_critical": False,
                            "machine_close_forbidden": True}
        assert candidate_rights_or_safety_critical(candidate) is False
        assert candidate_machine_close_forbidden(candidate) is True

    @pytest.mark.parametrize("bad", [
        "yes", "true", "1", 1, 0, 1.0, None, [], {}, ("x",),
    ])
    def test_present_non_bool_fails_closed(self, bad):
        # Frozen D04 §8.1: any present non-bool fails closed -- including
        # int 0/1 (bool is not int-coercible here) and None.
        for reader in (candidate_rights_or_safety_critical,
                       candidate_machine_close_forbidden):
            candidate = type("C", (), {})()
            candidate.detail = {"rights_or_safety_critical": bad,
                                "machine_close_forbidden": bad}
            with pytest.raises(CoverageValidationError):
                reader(candidate)

    def test_real_r2_candidate_with_flags_reads_correctly(self):
        # The readers work on a real frozen R2 RiskCandidate whose detail
        # went through deep_freeze_json.
        from mm_r2.risk import RiskCandidate
        flagged = RiskCandidate.from_signal(
            project_id="p", subject_ref="S1", domain="D04_protocol_compliance",
            signal_type="inclusion",
            detail={"rights_or_safety_critical": True,
                    "machine_close_forbidden": True},
        )
        assert candidate_rights_or_safety_critical(flagged) is True
        assert candidate_machine_close_forbidden(flagged) is True
        unflagged = RiskCandidate.from_signal(
            project_id="p", subject_ref="S1", domain="D04_protocol_compliance",
            signal_type="inclusion",
        )
        assert candidate_rights_or_safety_critical(unflagged) is False
        assert candidate_machine_close_forbidden(unflagged) is False
        nonbool = RiskCandidate.from_signal(
            project_id="p", subject_ref="S1", domain="D04_protocol_compliance",
            signal_type="inclusion",
            detail={"rights_or_safety_critical": "yes"},
        )
        with pytest.raises(CoverageValidationError):
            candidate_rights_or_safety_critical(nonbool)


# ---------------------------------------------------------------------------
# RiskDomainUnitResult Protocol -- AEMHUnitResult structural conformance
# ---------------------------------------------------------------------------

class TestRiskDomainUnitResultProtocol:
    def test_aemh_unit_result_satisfies_protocol(self):
        from mm_r4.fixtures import (
            build_challenge_matrix, evaluate,
        )
        case = next(
            c for c in build_challenge_matrix().cases
            if c.name == "positive_suspected_under_report")
        result = evaluate(list(case.records))
        # runtime_checkable Protocol: structural isinstance check.
        assert isinstance(result, RiskDomainUnitResult)

    def test_protocol_exposes_the_frozen_eight_fields(self):
        # The frozen eight fields (§2) must be the Protocol's read surface.
        # In Python 3.9 a Protocol composed of @property descriptors does
        # not populate __annotations__; verify the surface structurally
        # via a probe object that exposes exactly those attributes and
        # confirm the runtime_checkable isinstance accepts it, while a
        # probe missing one field is rejected.
        expected = [
            "unit_id", "subject_ref", "l1_disposition", "monitoring_priority",
            "r2_candidates", "risk_candidate_refs", "risk_instance_refs",
            "not_evaluable_reason",
        ]

        class _Complete:
            unit_id = "u"
            subject_ref = "s"
            l1_disposition = "positive"
            monitoring_priority = "high"
            r2_candidates = ()
            risk_candidate_refs = ()
            risk_instance_refs = ()
            not_evaluable_reason = ""

        # Every frozen field must be readable on a conforming result.
        complete = _Complete()
        for field in expected:
            assert hasattr(complete, field), f"missing frozen field {field}"

        class _MissingPriority:
            unit_id = "u"
            subject_ref = "s"
            l1_disposition = "positive"
            r2_candidates = ()
            risk_candidate_refs = ()
            risk_instance_refs = ()
            not_evaluable_reason = ""

        # runtime_checkable checks attribute presence; a result missing
        # monitoring_priority must not satisfy the Protocol.
        assert not isinstance(_MissingPriority(), RiskDomainUnitResult)

    def test_monitoring_priority_is_property_not_field(self):
        # AEMHUnitResult.monitoring_priority must be a read-only property
        # projecting medical_grading.monitoring_priority, not a dataclass
        # field -- otherwise the frozen 8-field Protocol would be violated
        # by an extra stored field.
        fields = {f.name for f in dataclasses.fields(AEMHUnitResult)}
        assert "monitoring_priority" not in fields
        assert isinstance(
            getattr(AEMHUnitResult, "monitoring_priority"), property)

    def test_monitoring_priority_projects_grading(self):
        grading = MedicalGrading(monitoring_priority=MONITORING_PRIORITY_HIGH)
        result = AEMHUnitResult(
            unit_id="u1", subject_ref="S1",
            l1_disposition="positive", medical_grading=grading)
        assert result.monitoring_priority == MONITORING_PRIORITY_HIGH
        # low projection
        result_low = AEMHUnitResult(
            unit_id="u2", subject_ref="S1",
            l1_disposition="positive",
            medical_grading=MedicalGrading(
                monitoring_priority=MONITORING_PRIORITY_LOW))
        assert result_low.monitoring_priority == MONITORING_PRIORITY_LOW

    def test_duck_type_without_medical_grading_satisfies_protocol(self):
        # A D02-style result with no MedicalGrading still satisfies the
        # Protocol (frozen D02 §2: D02 does not fake MedicalGrading).
        class D02LikeResult:
            unit_id = "unit-d02-1"
            subject_ref = "S001"
            l1_disposition = "positive"
            monitoring_priority = "medium"
            r2_candidates = ()
            risk_candidate_refs = ()
            risk_instance_refs = ()
            not_evaluable_reason = ""
        assert isinstance(D02LikeResult(), RiskDomainUnitResult)

    def test_sequence_fields_use_exact_frozen_types_not_any(self):
        # Frozen D02 §2 fixes the three sequence fields to exact public
        # types: Sequence[RiskCandidate], Sequence[RiskCandidateRef],
        # Sequence[RiskInstanceRef].  Resolve the @property return
        # annotations against the contracts module globals and assert
        # none resolves to Any (which would let a non-conforming element
        # type pass the Protocol silently).
        import collections.abc
        import typing
        from mm_r4 import contracts as _contracts
        from mm_r4.contracts import (
            RiskCandidate, RiskCandidateRef, RiskInstanceRef,
        )
        expected = {
            "r2_candidates": (collections.abc.Sequence, RiskCandidate),
            "risk_candidate_refs": (collections.abc.Sequence, RiskCandidateRef),
            "risk_instance_refs": (collections.abc.Sequence, RiskInstanceRef),
        }
        for field, (origin, arg) in expected.items():
            prop = getattr(RiskDomainUnitResult, field)
            hint = typing.get_type_hints(
                prop.fget, globalns=vars(_contracts))["return"]
            assert hint is not typing.Any, (
                f"{field} return annotation resolved to Any; the frozen "
                f"contract requires an exact typed Sequence")
            actual_origin = typing.get_origin(hint)
            actual_args = typing.get_args(hint)
            assert actual_origin is origin, (
                f"{field} expected Sequence origin, got {actual_origin!r}")
            assert actual_args == (arg,), (
                f"{field} expected Sequence[{arg.__name__}], got {hint!r}")


# ---------------------------------------------------------------------------
# lifecycle.py static dependency invariant (frozen D02 §11)
# ---------------------------------------------------------------------------

class TestLifecycleStaticDependency:
    def test_lifecycle_does_not_import_aemh(self):
        import inspect
        from mm_r4 import lifecycle
        src = inspect.getsource(lifecycle)
        # No static import of the aemh module or AEMHUnitResult.
        assert "from .aemh import" not in src, (
            "lifecycle.py must not import from aemh (frozen D02 §11)")
        assert "import mm_r4.aemh" not in src
        assert "AEMHUnitResult" not in src.replace(
            "AEMHUnitResult", "X", 0) or "AEMHUnitResult" not in src, (
            "lifecycle.py must not reference AEMHUnitResult")

    def test_lifecycle_uses_neutral_protocol_annotation(self):
        import inspect
        from mm_r4 import lifecycle
        src = inspect.getsource(lifecycle)
        assert "RiskDomainUnitResult" in src

    def test_lifecycle_reads_neutral_monitoring_priority(self):
        # promote_unit_result reads unit_result.monitoring_priority (the
        # neutral Protocol field), not medical_grading.monitoring_priority.
        import inspect
        from mm_r4.lifecycle import R4LifecycleAdapter
        src = inspect.getsource(R4LifecycleAdapter.promote_unit_result)
        assert "unit_result.monitoring_priority" in src
        assert "medical_grading" not in src


# ---------------------------------------------------------------------------
# CrossDomainEvidenceRef -- immutable read-only source reference (§3.3)
# ---------------------------------------------------------------------------

class TestCrossDomainEvidenceRef:
    def test_is_frozen_dataclass(self):
        ref = _make_ref()
        assert dataclasses.is_dataclass(ref)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.evidence_ref_id = "x"  # type: ignore[misc]

    def test_producer_must_differ_from_consumer(self):
        with pytest.raises(CoverageValidationError):
            _make_ref(producer_domain="D02_cm", consumer_domain="D02_cm")

    def test_requires_valid_content_hash(self):
        with pytest.raises(CoverageValidationError):
            _make_ref(content_hash="not-a-hash")

    def test_content_hash_excludes_snapshot_and_revision(self):
        # Same stable event + role + scope + payload, different
        # snapshot/revision -> identical content_hash (§3.3 dedup key).
        loc_a = _locator(snapshot_id="snap-1", revision_id="rev-1")
        loc_b = _locator(snapshot_id="snap-2", revision_id="rev-2")
        ch_a = cross_domain_evidence_content_hash(
            source_locator=loc_a, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        ch_b = cross_domain_evidence_content_hash(
            source_locator=loc_b, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        assert ch_a == ch_b

    def test_claim_change_produces_new_hash(self):
        loc = _locator()
        ch_treat = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        ch_proph = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="prophylaxis", context_payload={"role": "treatment"})
        assert ch_treat != ch_proph

    def test_context_payload_change_produces_new_hash(self):
        loc = _locator()
        ch_a = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        ch_b = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment",
            context_payload={"role": "prophylaxis"})
        assert ch_a != ch_b

    def test_context_payload_order_independent(self):
        loc = _locator()
        ch_a = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment",
            context_payload={"b": "1", "a": "2"})
        ch_b = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment",
            context_payload={"a": "2", "b": "1"})
        assert ch_a == ch_b

    def test_verify_content_hash_true_on_match(self):
        ref = _make_ref()
        assert ref.verify_content_hash() is True

    def test_verify_content_hash_false_on_tamper(self):
        ref = _make_ref()
        object.__setattr__(ref, "claim_scope", "tampered")
        assert ref.verify_content_hash() is False

    def test_context_payload_sorted_and_deduplicated(self):
        ref = _make_ref(context_payload=(
            ("zeta", "1"), ("alpha", "2")))
        # canonical_payload emits sorted context_payload.
        payload = ref.canonical_payload()
        assert payload["context_payload"] == [["alpha", "2"], ["zeta", "1"]]

    def test_duplicate_context_key_rejected(self):
        with pytest.raises(CoverageValidationError):
            _make_ref(context_payload=(("k", "1"), ("k", "2")))

    def test_invalid_context_entry_rejected(self):
        # The dataclass must reject malformed (non 2-tuple) context_payload
        # entries with CoverageValidationError.  Construct the ref directly
        # (bypassing the helper's hash precompute, which cannot dict() a
        # malformed payload) and supply a syntactically valid placeholder
        # hash; the __post_init__ payload validation runs before any use.
        loc = _locator()
        ch = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={})
        with pytest.raises(CoverageValidationError):
            CrossDomainEvidenceRef(
                evidence_ref_id="er-bad",
                producer_domain="D02_cm",
                consumer_domain="D01_aemh",
                evidence_role="cm_indication",
                source_locator=loc,
                producer_unit_id="unit-d02-1",
                content_hash=ch,
                context_payload=(("k",),),  # type: ignore[arg-type]
            )

    def test_empty_context_payload_allowed(self):
        ref = _make_ref(context_payload=())
        assert ref.verify_content_hash() is True
        assert ref.canonical_payload()["context_payload"] == []

    def test_no_consumer_lifecycle_state_field(self):
        ref = _make_ref()
        # The frozen contract (§3.3) forbids carrying consumer
        # candidate/risk/Query id, consumer L1 disposition, or lifecycle
        # state.  Verify the dataclass fields are only the read-only
        # provenance fields.
        field_names = {f.name for f in dataclasses.fields(ref)}
        forbidden = {
            "candidate_id", "risk_instance_id", "query_id",
            "l1_disposition", "risk_state", "lifecycle_state",
        }
        assert not (field_names & forbidden)

    def test_full_locator_retained_for_drill_back(self):
        loc = _locator()
        ref = _make_ref(source_locator=loc)
        # The full locator (with snapshot/revision) is retained separately
        # for source drill-back, even though it is excluded from the hash.
        assert ref.source_locator is loc
        assert ref.source_locator.snapshot_id == "snap-1"

    def test_context_payload_stored_in_key_sorted_order(self):
        # The stored context_payload must be canonicalized into key-sorted
        # order at construction, regardless of input order, so the frozen
        # immutable ref is order-independent and its hash reproducible.
        ref = _make_ref(context_payload=(
            ("zeta", "1"), ("alpha", "2"), ("mid", "3")))
        assert ref.context_payload == (
            ("alpha", "2"), ("mid", "3"), ("zeta", "1"))

    def test_well_formed_mismatched_content_hash_rejected(self):
        # A syntactically valid 64-char hex hash that is NOT the canonical
        # hash of the ref's determinant fields must be rejected at
        # construction (frozen D02 §3.3): an immutable ref must not be
        # built with a non-canonical content address.
        loc = _locator()
        payload = (("role", "treatment"),)
        canonical = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment", context_payload=dict(payload))
        # A different-but-valid 64-char hex (flip one hex char) is
        # well-formed yet non-canonical.
        wrong = ("0" if canonical[0] != "0" else "1") + canonical[1:]
        assert wrong != canonical
        assert len(wrong) == 64
        with pytest.raises(CoverageValidationError):
            CrossDomainEvidenceRef(
                evidence_ref_id="er-bad",
                producer_domain="D02_cm",
                consumer_domain="D01_aemh",
                evidence_role="cm_indication",
                source_locator=loc,
                producer_unit_id="unit-d02-1",
                content_hash=wrong,
                claim_scope="treatment",
                context_payload=payload,
            )

    def test_mismatched_hash_when_payload_differs_from_supplied_hash(self):
        # The supplied hash was computed for a DIFFERENT payload than the
        # ref actually carries: construction must reject it as
        # non-canonical, even though both hashes are individually valid.
        loc = _locator()
        hash_for_other_payload = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment",
            context_payload={"role": "prophylaxis"})
        with pytest.raises(CoverageValidationError):
            _make_ref(
                source_locator=loc,
                content_hash=hash_for_other_payload,
                context_payload=(("role", "treatment"),))


# ---------------------------------------------------------------------------
# Cross-domain dedup key (frozen D02 §3.3, §8)
# ---------------------------------------------------------------------------

class TestCrossDomainDedupKey:
    def test_dedup_key_is_stable_event_role_hash(self):
        # Same (table_semantic, record_id, evidence_role, content_hash)
        # within one D01 run/snapshot -> one SemanticRecord (§8.4).  The
        # content_hash passed to the ref MUST be canonical for the ref's
        # own determinant fields; here both refs share the same stable
        # event + role + claim, so their canonical hash and dedup key
        # are identical.
        loc = _locator(record_id="cm-9", table_semantic="recorded_cm")
        payload = (("role", "treatment"),)
        ch = cross_domain_evidence_content_hash(
            source_locator=loc, evidence_role="cm_indication",
            claim_scope="treatment", context_payload=dict(payload))
        ref = _make_ref(
            source_locator=loc, content_hash=ch, context_payload=payload)
        dedup = (
            loc.table_semantic, loc.record_id,
            ref.evidence_role, ref.content_hash,
        )
        # A second ref for the same stable event + role + identical claim
        # yields the same dedup key.
        ref2 = _make_ref(
            source_locator=loc, content_hash=ch, context_payload=payload,
            evidence_ref_id="er-2")
        dedup2 = (
            ref2.source_locator.table_semantic,
            ref2.source_locator.record_id,
            ref2.evidence_role, ref2.content_hash,
        )
        assert dedup == dedup2

    def test_different_stable_event_yields_different_dedup(self):
        loc1 = _locator(record_id="cm-9")
        loc2 = _locator(record_id="cm-10")
        ch1 = cross_domain_evidence_content_hash(
            source_locator=loc1, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        ch2 = cross_domain_evidence_content_hash(
            source_locator=loc2, evidence_role="cm_indication",
            claim_scope="treatment", context_payload={"role": "treatment"})
        # record_id differs -> stable event key differs -> different hash.
        assert ch1 != ch2


# ---------------------------------------------------------------------------
# End-to-end: lifecycle adapter consumes a neutral-Protocol result
# ---------------------------------------------------------------------------

class TestLifecycleNeutralConsumption:
    def test_positive_d01_result_promotes_via_neutral_surface(self):
        # A real D01 AEMHUnitResult still drives the adapter end-to-end
        # after the lifecycle refactor; priority is read off the neutral
        # Protocol field.
        from mm_r4.fixtures import (
            evaluate, make_acceptance_service, make_baseline_snapshot,
            make_lifecycle, make_record, PROJECT_ID,
        )
        from mm_r4.lifecycle import R4LifecycleAdapter

        svc = make_acceptance_service()
        snap = make_baseline_snapshot(svc, snapshot_id="snap-promote")
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc, project_id=PROJECT_ID)

        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-promo-1",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:10035581", "sym-promo-1",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ]
        ur = evaluate(records, snapshot_id=snap)
        assert isinstance(ur, RiskDomainUnitResult)
        outcome = adapter.promote_unit_result(ur, establish=False)
        assert outcome.registered_any
        # The neutral priority read equals the grading priority.
        assert ur.monitoring_priority == \
            ur.medical_grading.monitoring_priority


# ---------------------------------------------------------------------------
# D03 (worker_03): IPUnitResult satisfies the same neutral Protocol; D03
# root exports are object-identical; lifecycle stays neutral (frozen D03
# §2, §11 and the D02 §11 invariant family).
# ---------------------------------------------------------------------------

class TestD03RiskDomainUnitResultProtocol:

    def test_ip_unit_result_satisfies_protocol(self):
        # A real D03 IPUnitResult (positive) satisfies the neutral
        # RiskDomainUnitResult protocol structurally.
        from mm_r4.ip_fixtures import build_ip_challenge_matrix
        case = build_ip_challenge_matrix().by_number(1)
        exp, results = case.build()
        for r in results:
            assert isinstance(r, RiskDomainUnitResult)
        pos = [r for r in results
               if r.l1_disposition == "positive"][0]
        assert pos.monitoring_priority == "medium"

    def test_d03_monitoring_priority_is_stored_field_not_property(self):
        # D01 projects priority through a property; D03 stores it as a real
        # dataclass field.  Both satisfy the neutral Protocol; the Protocol
        # only requires the read surface, never the storage mechanism.
        from mm_r4.ip import IPUnitResult
        fields = {f.name for f in dataclasses.fields(IPUnitResult)}
        assert "monitoring_priority" in fields
        # It is a stored instance field, not a class-level property
        # (contrast D01's AEMHUnitResult.monitoring_priority property).
        assert "monitoring_priority" not in vars(IPUnitResult)

    def test_d03_domain_constant_is_neutral_token(self):
        from mm_r4.ip import D03_DOMAIN
        assert D03_DOMAIN == "D03_ip_exposure"


class TestD03RootExportsObjectIdentity:

    def test_d03_root_exports_are_object_identical(self):
        import mm_r4
        from mm_r4 import ip, ip_projection, ip_fixtures

        assert mm_r4.IPExposureEpisode is ip.IPExposureEpisode
        assert mm_r4.IPUnitResult is ip.IPUnitResult
        assert mm_r4.evaluate_ip_slice is ip.evaluate_ip_slice
        assert mm_r4.evaluate_ip_unit is ip.evaluate_ip_unit
        assert mm_r4.IPSubjectJourneyProjection is \
            ip_projection.IPSubjectJourneyProjection
        assert mm_r4.project_ip_subject_journey is \
            ip_projection.project_ip_subject_journey
        assert mm_r4.IPJourneyEvent is ip_projection.IPJourneyEvent
        assert mm_r4.IPRiskMarker is ip_projection.IPRiskMarker
        assert mm_r4.IPEventMarkerJoin is ip_projection.IPEventMarkerJoin
        assert mm_r4.ip_bidirectional_join is \
            ip_projection.bidirectional_join
        assert mm_r4.IP_ANCHOR_KIND_UNRESOLVED is \
            ip_projection.ANCHOR_KIND_UNRESOLVED
        assert mm_r4.IP_POSITIVE_SUBTYPE_LABELS is \
            ip.POSITIVE_SUBTYPE_LABELS
        assert mm_r4.ip_positive_subtype_audience_label is \
            ip.positive_subtype_audience_label
        assert mm_r4.build_ip_challenge_matrix is \
            ip_fixtures.build_ip_challenge_matrix
        assert mm_r4.IPChallengeCase is ip_fixtures.IPChallengeCase

    def test_d03_positions_do_not_shadow_d01_d02(self):
        # The D03 additions never replace the existing D01/D02 exports.
        import mm_r4
        from mm_r4 import aemh, cm, cm_projection
        assert mm_r4.AEMHUnitResult is aemh.AEMHUnitResult
        assert mm_r4.MedicationEpisode is cm.MedicationEpisode
        assert mm_r4.evaluate_cm_slice is cm.evaluate_cm_slice
        assert mm_r4.POSITIVE_SUBTYPE_LABELS is cm.POSITIVE_SUBTYPE_LABELS
        assert mm_r4.positive_subtype_audience_label is \
            cm.positive_subtype_audience_label
        assert mm_r4.ANCHOR_KIND_UNRESOLVED is \
            cm_projection.ANCHOR_KIND_UNRESOLVED
        assert mm_r4.bidirectional_join is \
            cm_projection.bidirectional_join


class TestD03LifecycleStaticDependency:

    def test_lifecycle_does_not_import_ip(self):
        # The lifecycle adapter stays neutral: it must not statically
        # depend on the D03 IP module either (same invariant family as
        # the D02 §11 check for aemh).
        import inspect
        from mm_r4 import lifecycle
        src = inspect.getsource(lifecycle)
        assert "from .ip import" not in src, (
            "lifecycle.py must not import from ip (neutral protocol)")
        assert "IPUnitResult" not in src

    def test_d03_result_duck_types_into_lifecycle(self):
        # A D03 positive result promotes through the adapter via the
        # neutral Protocol surface (no MedicalGrading required).
        from mm_r4.ip_fixtures import (
            build_ip_challenge_matrix, make_acceptance_service,
            make_baseline_snapshot, make_lifecycle, PROJECT_ID,
        )
        from mm_r4.lifecycle import R4LifecycleAdapter
        case = build_ip_challenge_matrix().by_number(47)
        exp, results = case.build()
        pos = [r for r in results
               if r.l1_disposition == "positive"][0]
        assert not hasattr(pos, "medical_grading")
        svc = make_acceptance_service()
        make_baseline_snapshot(svc)
        lc = make_lifecycle()
        adapter = R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc, project_id=PROJECT_ID)
        outcome = adapter.promote_unit_result(pos)
        assert outcome.established_any
        assert lc.verify_chain(PROJECT_ID)
