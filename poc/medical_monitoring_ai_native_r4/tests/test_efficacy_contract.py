"""R4-D06 domain model / canonical identity contract tests.

Focused tests for the D06 domain surface (:mod:`mm_r4.efficacy`,
:mod:`mm_r4.efficacy_projection`):

* canonical serialization and content addressing reproduce the frozen
  generator's canonical JSON (Unicode NFC, sorted keys, compact
  separators, NaN/Infinity rejection, ``-0``/``1``/``1.0``/``1.00``
  canonicalization);
* the frozen audience lexicon and validator identity
  (``d06-audience-zh-v1``, ``d06-audience-validator-v1``) match their
  frozen hashes;
* the canonical priority policy is content-addressed and its frozen
  five-step resolution reproduces every precedence tier;
* typed identity objects (priority resolver input, priority decision,
  D06 unit stable core, public R4 risk identity, risk binding) carry
  exact, self-consistent content addresses;
* the renderer-neutral journey projection keeps baseline / threshold /
  actual-point / risk markers distinct and separates pending and
  out-of-cutoff areas without exposing internal vocabulary.

All data is synthetic and offline.
"""

from __future__ import annotations

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

from mm_r4 import efficacy as ef  # noqa: E402
from mm_r4 import efficacy_projection as ep  # noqa: E402


# ---------------------------------------------------------------------------
# Canonical serialization
# ---------------------------------------------------------------------------


class TestCanonicalSerialization:
    def test_nfc_normalization_affects_hash(self):
        composed = "\u00e9"  # e + combining acute
        decomposed = "e\u0301"  # precomposed é
        assert ef.d06_content_hash({"label": composed}) == (
            ef.d06_content_hash({"label": decomposed})
        )

    def test_sorted_keys_and_compact_separators(self):
        payload = {"b": 1, "a": [2, 3]}
        rendered = ef.d06_canonical_json(payload)
        assert rendered == '{"a":[2,3],"b":1}'

    def test_nan_infinity_rejected(self):
        with pytest.raises(ValueError):
            ef.d06_canonical_json({"x": float("nan")})
        with pytest.raises(ValueError):
            ef.d06_canonical_json({"x": float("inf")})

    def test_negative_zero_and_equivalent_decimals_canonicalize(self):
        from mm_r4.efficacy_evaluator import _canonical_decimal

        assert _canonical_decimal("1") == _canonical_decimal("1.0")
        assert _canonical_decimal("1.0") == _canonical_decimal("1.00")
        assert _canonical_decimal("-0") == _canonical_decimal("0") == "0"
        assert _canonical_decimal("2.350") == "2.35"

    def test_unicode_key_normalization(self):
        assert ef.d06_content_hash({"a\u0301": 1}) == (
            ef.d06_content_hash({"\u00e1": 1})
        )


# ---------------------------------------------------------------------------
# Audience lexicon and validator identity
# ---------------------------------------------------------------------------


class TestAudienceLexicon:
    def test_lexicon_hash_is_frozen(self):
        calculated = ef.d06_sha256_text(
            ef.d06_canonical_json(
                {
                    "display_keys": list(ef.AUDIENCE_DISPLAY_KEYS),
                    "phrases": list(ef.AUDIENCE_PHRASES),
                }
            )
        )
        assert calculated == ef.AUDIENCE_LEXICON_HASH
        assert ef.AUDIENCE_LEXICON_HASH == (
            "d73a3da6fb9e5643c17673273bff042af5df75259979dcc59cb8adff917e5a75"
        )

    def test_validator_hash_is_content_addressed(self):
        assert ef.AUDIENCE_VALIDATOR_HASH == ef.d06_sha256_text(
            ef.d06_canonical_json(ef.AUDIENCE_VALIDATOR_DEFINITION)
        )

    def test_phrase_hits_ascii_token_sequence(self):
        # "backend-qc-positive" hits three phrases; "阳性结果" must NOT hit
        # the English "positive".
        hits = ef.audience_phrase_hits(["backend-qc-positive", "阳性结果"])
        assert hits == ["positive", "backend", "qc"]

    def test_phrase_hits_chinese_substring(self):
        hits = ef.audience_phrase_hits(["这是候选信号文本"])
        assert hits == ["候选信号"]

    def test_display_key_forbidden_scan(self):
        hits = ef.forbidden_audience_keys(
            {"label": "可见", "risk_id": "R-1", "payload_hash": "abc"}
        )
        assert "risk_id" in hits
        assert "payload_hash" in hits
        assert "label" not in hits

    def test_query_payload_schema_requires_three_parts(self):
        payload = {
            "payload_kind": "query",
            "payload_schema_version": "d06-query-audience-v1",
            "query_context": "enrolled_or_post_enrollment",
            "basis_sentence": "依据：方案 V2.0。",
            "finding_sentence": "发现：记录需核实。",
            "action_sentence": "行动项：请核实。",
        }
        assert ef.validate_audience_payload_schema(payload) == ("d06-query-audience-v1")
        broken = dict(payload)
        broken.pop("finding_sentence")
        with pytest.raises(ef.AudiencePayloadValidationError):
            ef.validate_audience_payload_schema(broken)


# ---------------------------------------------------------------------------
# Priority policy
# ---------------------------------------------------------------------------


class TestPriorityPolicy:
    def test_policy_hash_is_content_addressed(self):
        policy = ef.CANONICAL_PRIORITY_POLICY
        core = {key: value for key, value in policy.items() if key != "policy_hash"}
        assert policy["policy_hash"] == (
            f"sha256:{ef.d06_sha256_text(ef.d06_canonical_json(core))}"
        )
        assert policy["policy_hash"] == (
            "sha256:9f05a1b83c171d04698d4f4b6efdeec5c3b4ab0e0b2617461d4a86768a8d6bac"
        )

    def test_five_step_resolution(self):
        cases = [
            # (impact, resolution, recurrence, recoverability, actionability)
            # -> (priority, step, machine_close_forbidden)
            (
                "rights_safety",
                "resolved",
                "single",
                "unknown",
                "actionable",
                ("high", 1, True),
            ),
            (
                "critical_treatment",
                "resolved",
                "single",
                "recoverable",
                "actionable",
                ("high", 1, True),
            ),
            (
                "primary_endpoint",
                "unresolved",
                "single",
                "recoverable",
                "actionable",
                ("unknown", 2, False),
            ),
            (
                "primary_endpoint",
                "resolved",
                "single",
                "recoverable",
                "context_only",
                ("unknown", 2, False),
            ),
            (
                "primary_endpoint",
                "resolved",
                "single",
                "recoverable",
                "actionable",
                ("medium", 3, False),
            ),
            (
                "primary_endpoint",
                "resolved",
                "single",
                "irrecoverable",
                "actionable",
                ("high", 3, True),
            ),
            (
                "mandatory_critical_sample",
                "resolved",
                "single",
                "time_critical",
                "actionable",
                ("high", 3, True),
            ),
            (
                "key_secondary_endpoint",
                "resolved",
                "repeated_subject",
                "recoverable",
                "actionable",
                ("medium", 4, False),
            ),
            (
                "key_secondary_endpoint",
                "resolved",
                "repeated_site",
                "recoverable",
                "actionable",
                ("high", 4, True),
            ),
            (
                "other_required",
                "resolved",
                "single",
                "irrecoverable",
                "actionable",
                ("high", 4, True),
            ),
            (
                "administrative",
                "resolved",
                "single",
                "recoverable",
                "actionable",
                ("low", 5, False),
            ),
            (
                "administrative",
                "resolved",
                "repeated_subject",
                "recoverable",
                "actionable",
                ("medium", 5, False),
            ),
            (
                "administrative",
                "resolved",
                "repeated_site",
                "recoverable",
                "actionable",
                ("high", 5, True),
            ),
            (
                "administrative",
                "resolved",
                "single",
                "time_critical",
                "actionable",
                ("high", 5, True),
            ),
        ]
        for (
            impact,
            resolution,
            recurrence,
            recoverability,
            actionability,
            expected,
        ) in cases:
            assert (
                ef.resolve_priority_step(
                    impact, resolution, recurrence, recoverability, actionability
                )
                == expected
            )

    def test_undefined_role_never_defaults_to_low(self):
        assert (
            ef.resolve_priority_step(
                None, "unresolved", "single", "recoverable", "actionable"
            )[0]
            == "unknown"
        )


# ---------------------------------------------------------------------------
# Typed identity objects
# ---------------------------------------------------------------------------

_SCOPE = dict(ef.CANONICAL_SYNTHETIC_SCOPE)


class TestTypedIdentityObjects:
    def test_resolver_input_content_addressed(self):
        resolver = ef.D06PriorityResolverInput(
            scope=_SCOPE,
            endpoint_definition_id="EP-001",
            stable_endpoint_key="SYN-ENDPOINT",
            stable_timepoint_key="WEEK-4",
            endpoint_role="secondary",
            impact_resolution_state="resolved",
            impact_class="other_required",
            recurrence_class="single",
            recoverability="recoverable",
            actionability="actionable",
            monitoring_priority="medium",
            matched_precedence_step=4,
            reason_codes=("key_secondary_or_other_required",),
            machine_close_forbidden=False,
            priority_policy_id="D06-PRIORITY-V1",
            priority_policy_version="1.0",
            priority_policy_hash=ef.CANONICAL_PRIORITY_POLICY["policy_hash"],
            source_locator_ids=("SYN-LOC-PRIORITY-INPUT-001",),
        )
        assert resolver.hash == (
            "sha256:db35ba3c2b2dffd440e481abbb9c0a496215c56f2947c312c88496ec03be608e"
        )
        assert ef.verify_embedded_hash(resolver.to_plain(), "resolver") == (
            resolver.hash
        )

    def test_public_identity_tuple_hash_is_frozen(self):
        identity = ef.PublicR4RiskIdentity(
            project_ref="SYN-D06-PROJECT",
            domain_id="D06",
            scope_type="subject_endpoint_timepoint_episode",
            scope_key=("SYN-D06-SUBJECT-001", "SYN-D06-SITE-001", "EPISODE-001"),
            stable_source_or_event_identity="ASM-W4-A",
            normalized_concept=(
                "efficacy_evaluation",
                "score_recalculation",
                "SYN-ENDPOINT",
                "SYN-SCALE",
                "WEEK-4",
                "none",
            ),
            temporal_window=("WEEK-4", "EPISODE-001"),
            rule_or_knowledge_lineage="ALG-001@1.0",
            public_identity_version="1.0",
            risk_id="RISK-001",
            unit_id="UNIT-001",
            scope_binding_id="SYN-D06-SCOPE-001",
            cutoff="2026-01-31T23:59:59+08:00",
        )
        assert identity.public_identity_hash == (
            "sha256:608dce8d729efdbde6ca45e418c3dec2bf7e7d5e4a49760e55854bb70e83306d"
        )
        assert identity.public_r4_risk_identity_id == "R4ID-55854bb70e83306d"

    def test_stable_core_normalized_concept(self):
        core = ef.D06UnitStableCore(
            unit_id="UNIT-001",
            domain_id="D06",
            classifier="efficacy_evaluation",
            unit_kind="score_recalculation",
            stable_endpoint_key="SYN-ENDPOINT",
            stable_instrument_key_or_none="SYN-SCALE",
            stable_timepoint_key="WEEK-4",
            stable_item_or_component_key_or_none="none",
            stable_source_record_id="ASM-W4-A",
            temporal_window=("WEEK-4", "EPISODE-001"),
            rule_or_knowledge_lineage="ALG-001@1.0",
        )
        assert core.normalized_concept == [
            "efficacy_evaluation",
            "score_recalculation",
            "SYN-ENDPOINT",
            "SYN-SCALE",
            "WEEK-4",
            "none",
        ]
        assert ef.verify_embedded_hash(core.to_plain(), "stable core") == (core.hash)

    def test_subtype_to_unit_kind_mapping_is_frozen(self):
        assert ef.SUBTYPE_TO_UNIT_KIND["score_inconsistent"] == ("score_recalculation")
        assert ef.SUBTYPE_TO_UNIT_KIND["baseline_inconsistent"] == (
            "baseline_selection"
        )
        assert ef.SUBTYPE_TO_UNIT_KIND["individual_trend_inconsistent"] == (
            "individual_trend_pattern"
        )
        assert ef.UNIT_KIND_TO_SUBTYPE["endpoint_composition"] == (
            "endpoint_composition_inconsistent"
        )

    def test_scope_object_fields_exclude_snapshot_as_of(self):
        payload = ef.object_scope_fields(_SCOPE)
        assert "snapshot_as_of" not in payload
        assert payload["cutoff"] == "2026-01-31T23:59:59+08:00"
        assert payload["project_ref"] == "SYN-D06-PROJECT"


# ---------------------------------------------------------------------------
# Renderer-neutral journey projection
# ---------------------------------------------------------------------------


def _minimal_decision(fixture, risk_id="RISK-001", monitoring_priority="medium"):
    """Typed priority decision stand-in for positive journey builds."""
    from mm_r4.efficacy import D06PriorityDecision

    return D06PriorityDecision(
        scope=dict(fixture.scope),
        unit_id="UNIT-001",
        risk_id=risk_id,
        priority_decision_id="PRIORITY-DEC-001",
        endpoint_definition_id="EP-001",
        stable_endpoint_key="SYN-ENDPOINT",
        stable_timepoint_key="WEEK-4",
        endpoint_role="primary_efficacy",
        impact_resolution_state="resolved",
        impact_class="score_inconsistent",
        recurrence_class="single_occurrence",
        recoverability="recoverable",
        actionability="actionable",
        monitoring_priority=monitoring_priority,
        matched_precedence_step=5,
        reason_codes=("SCORE_INCONSISTENT",),
        machine_close_forbidden=True,
        priority_policy_id="D06-PRIORITY-POLICY-001",
        priority_policy_version="1.0",
        priority_policy_hash="sha256:" + "0" * 64,
        priority_resolver_input_hash="sha256:" + "0" * 64,
        source_locator_ids=("SYN-LOC-PRIORITY-001",),
    )


class _MinimalFixture:
    """Tiny typed-fixture stand-in for the projection builder."""

    def __init__(self, cutoff: str = "2026-01-31T23:59:59+08:00"):
        self.scope = {
            "project_ref": "SYN-D06-PROJECT",
            "run_ref": "SYN-D06-RUN-001",
            "subject_ref": "SYN-D06-SUBJECT-001",
            "site_ref": "SYN-D06-SITE-001",
            "episode_key": "EPISODE-001",
            "scope_binding_id": "SYN-D06-SCOPE-001",
            "clinical_event_cutoff": cutoff,
        }
        self.bindings = {
            "shared_temporal_spine_binding": {
                "object_type": "SharedTemporalSpineBinding",
                "spine_binding_id": "D05-SPINE-BIND-001",
                "project_ref": "SYN-D06-PROJECT",
                "run_ref": "SYN-D06-RUN-001",
                "subject_ref": "SYN-D06-SUBJECT-001",
                "site_ref": "SYN-D06-SITE-001",
                "episode_key": "EPISODE-001",
                "scope_binding_id": "SYN-D06-SCOPE-001",
                "monitoring_mode": "full",
                "source_revision": "SYN-REV-001",
                "accepted_snapshot_ref": "SYN-SNAPSHOT-001",
                "cutoff": cutoff,
                "axis_hash": "sha256:" + "0" * 64,
            }
        }
        self.definitions = {
            "endpoint": {"stable_key": "SYN-ENDPOINT"},
            "timepoint": {"key": "WEEK-4"},
            "threshold": {"comparator": "ge", "value": "30", "unit": "percent"},
        }
        self.records = {
            "assessments": [
                {
                    "id": "ASM-BASE-D7",
                    "time": "2025-12-24T09:00:00+08:00",
                    "source_locator_ids": ["SYN-LOC-BASE-001"],
                },
                {
                    "id": "ASM-BASE-D1",
                    "time": "2026-01-08T09:00:00+08:00",
                    "source_locator_ids": ["SYN-LOC-BASE-002"],
                },
                {
                    "id": "ASM-W4-A",
                    "time": "2026-01-29T09:00:00+08:00",
                    "source_locator_ids": ["SYN-LOC-W4-A"],
                },
                {
                    "id": "ASM-W4-B",
                    "time": "2026-02-01T09:00:00+08:00",
                    "source_locator_ids": ["SYN-LOC-W4-B"],
                },
            ],
            "trend_points": [
                {"id": "TP-1", "time": "2026-01-08T09:00:00+08:00", "value": "12"},
                {"id": "TP-2", "time": "2026-01-15T09:00:00+08:00", "value": "8"},
            ],
        }


class TestJourneyProjection:
    def test_visit_axis_and_lanes_present(self):
        projection = ep.project_efficacy_journey(_MinimalFixture())
        assert projection.visit_axis_label == "访视轴"
        assert projection.visit_axis
        assert projection.endpoint_lanes == ("主要疗效终点", "量表", "反应", "个体趋势")

    def test_marker_kinds_are_distinct(self):
        projection = ep.project_efficacy_journey(_MinimalFixture())
        kinds = {marker.marker_kind for marker in projection.markers}
        assert ep.MARKER_BASELINE in kinds
        assert ep.MARKER_THRESHOLD_BAND in kinds
        assert ep.MARKER_ACTUAL_POINT in kinds

    def test_cutoff_later_record_goes_to_out_of_cutoff_area(self):
        projection = ep.project_efficacy_journey(_MinimalFixture())
        out_of_cutoff = [
            marker
            for marker in projection.out_of_cutoff_markers
            if marker.marker_kind == ep.MARKER_OUT_OF_CUTOFF
        ]
        assert out_of_cutoff
        assert projection.after_cutoff_section_label == "截止日后记录"

    def test_undated_record_goes_to_pending_area(self):
        fixture = _MinimalFixture()
        fixture.records["assessments"].append({"id": "ASM-UNDATED", "time": ""})
        projection = ep.project_efficacy_journey(fixture)
        pending = [
            marker
            for marker in projection.pending_markers
            if marker.marker_kind == ep.MARKER_PENDING
        ]
        assert pending
        assert projection.data_gap_section_label == "资料待补充"
        assert any(marker.anchor_state == "pending_time" for marker in pending)

    def test_risk_marker_has_anchor_and_jump(self):
        fixture = _MinimalFixture()
        projection = ep.project_efficacy_journey(
            fixture,
            unit_l1="positive",
            priority_decision=_minimal_decision(fixture),
        )
        risk_markers = [
            marker
            for marker in projection.markers
            if marker.marker_kind == ep.MARKER_RISK
        ]
        assert risk_markers
        marker = risk_markers[0]
        assert marker.risk_anchor == "RISK-001"
        assert marker.marker_id == "MRK-RISK-001"
        assert marker.monitoring_priority == "medium"
        assert marker.source_jump_target

    def test_no_internal_vocabulary_in_labels(self):
        fixture = _MinimalFixture()
        projection = ep.project_efficacy_journey(
            fixture,
            unit_l1="positive",
            priority_decision=_minimal_decision(fixture),
        )
        labels = [marker.audience_label for marker in projection.markers]
        labels += [marker.audience_label for marker in projection.pending_markers]
        labels += [marker.audience_label for marker in projection.out_of_cutoff_markers]
        for label in labels:
            for forbidden in (
                "正式事实",
                "候选信号",
                "只读投影",
                "规则命中",
                "positive",
                "candidate",
                "backend",
                "log",
            ):
                assert forbidden not in label, f"internal vocabulary leaked: {label!r}"

    def test_never_collapses_into_recorded_matters(self):
        projection = ep.project_efficacy_journey(_MinimalFixture())
        labels = [marker.audience_label for marker in projection.markers]
        assert "已记录事项" not in labels

    def test_projection_payload_hash_deterministic(self):
        first = ep.project_efficacy_journey(_MinimalFixture())
        second = ep.project_efficacy_journey(_MinimalFixture())
        assert first.payload_hash() == second.payload_hash()

    def test_journey_audience_payload_is_frozen(self):
        payload = ep.journey_audience_payload()
        assert payload["payload_kind"] == "journey"
        assert payload["payload_schema_version"] == "d06-journey-audience-v1"
        assert payload["visit_axis_label"] == "访视轴"
        assert "依据：" not in str(payload)
        assert ef.validate_audience_payload_schema(payload) == (
            "d06-journey-audience-v1"
        )
