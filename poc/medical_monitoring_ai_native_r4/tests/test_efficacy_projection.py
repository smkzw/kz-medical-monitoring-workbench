"""R4-D06 audience payload validation and journey projection QC tests.

Focused tests for the frozen audience-payload contract (§10) and the
renderer-neutral journey projection:

* every emitted audience payload passes the frozen per-kind schema and
  Chinese-native content checks (``依据：/发现：/行动项：`` for queries,
  Chinese visit axis + endpoint lane for journeys);
* forbidden lexicon wording (``positive``/``candidate``/``正式事实``/
  ``候选信号``/``backend``/``QC``/...) fails validation and suppresses the
  payload while recording the exact forbidden-fragment hits and visible
  display-string paths;
* internal display keys (``*_id``/``*_hash``/``ref``/``classifier``/...) are
  never projected as visible labels;
* the journey projection never collapses distinct reporter types into a
  generic "已记录事项" label;
* PD wording is only permitted for ``enrolled_or_post_enrollment`` query
  contexts;
* failed payloads never leak into the outcome.

All data is synthetic and offline; expected values come from the frozen
catalog oracle (test-side).
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

from mm_r4.efficacy import (  # noqa: E402
    AUDIENCE_LEXICON_HASH,
    AUDIENCE_LEXICON_VERSION,
    AUDIENCE_VALIDATOR_HASH,
    AUDIENCE_VALIDATOR_VERSION,
    AudiencePayloadValidationError,
    validate_audience_payload_schema,
)
from mm_r4.efficacy_fixtures import build_d06_challenge_matrix  # noqa: E402
from mm_r4.efficacy_projection import (  # noqa: E402
    journey_audience_payload,
    query_audience_payload,
    risk_label_audience_payload,
)

MATRIX = build_d06_challenge_matrix()

AUDIENCE_CASES = (31, 46, 121, 122, 123, 124, 139, 159, 169, 187, 188, 216)
PASSING_PROJECTION_CASES = (31, 46, 169)
FAILING_AUDIENCE_CASES = (121, 122, 123, 124, 139, 187)


def _outcome(number: int):
    return MATRIX.by_number(number).assemble()


# ---------------------------------------------------------------------------
# Audience payload schema
# ---------------------------------------------------------------------------


class TestAudiencePayloadSchema:
    def test_journey_payload_schema_passes(self):
        payload = journey_audience_payload()
        assert validate_audience_payload_schema(payload) == ("d06-journey-audience-v1")

    def test_query_payload_three_sentences(self):
        payload = query_audience_payload(
            "enrolled_or_post_enrollment",
            "依据：方案 V2.0。",
            "发现：总分重算不一致。",
            "行动项：请核实并说明差异。",
        )
        assert validate_audience_payload_schema(payload) == ("d06-query-audience-v1")

    def test_query_missing_sentence_fails(self):
        payload = query_audience_payload(
            "enrolled_or_post_enrollment", "依据：x。", "发现：y。", ""
        )
        with pytest.raises(AudiencePayloadValidationError):
            validate_audience_payload_schema(payload)

    def test_query_pd_wording_only_for_enrolled(self):
        for context in (
            "enrollment_not_occurred",
            "enrollment_state_unresolved",
        ):
            payload = query_audience_payload(
                context,
                "依据：当前资料显示尚未入组。",
                "发现：记录需核实。",
                "行动项：请核实并更正相关记录。",
            )
            # PD wording ("方案偏离") is forbidden for non-enrolled contexts.
            assert "方案偏离" not in " ".join(str(v) for v in payload.values())

    def test_unknown_payload_kind_fails(self):
        with pytest.raises(AudiencePayloadValidationError):
            validate_audience_payload_schema({"payload_kind": "mystery"})

    def test_risk_label_payload(self):
        payload = risk_label_audience_payload(
            "量表计分待核实", "中", "总分重算不一致", "受试者历时资料"
        )
        assert validate_audience_payload_schema(payload) == (
            "d06-risk_label-audience-v1"
        )


# ---------------------------------------------------------------------------
# Frozen validator identity
# ---------------------------------------------------------------------------


class TestValidatorIdentity:
    def test_validator_version_and_hash_are_frozen(self):
        for number in AUDIENCE_CASES:
            outcome = _outcome(number)
            result = outcome["audience_validation_result"]
            assert result["validator_version"] == AUDIENCE_VALIDATOR_VERSION
            assert result["validator_hash"] == AUDIENCE_VALIDATOR_HASH
            assert result["lexicon_version"] == AUDIENCE_LEXICON_VERSION
            assert result["forbidden_lexicon_hash"] == AUDIENCE_LEXICON_HASH
            assert result["payload_schema"] is True

    def test_validation_state_matches_top_level(self):
        for number in AUDIENCE_CASES:
            outcome = _outcome(number)
            assert (
                outcome["audience_validation_state"]
                == (outcome["audience_validation_result"]["validation_state"])
            )


# ---------------------------------------------------------------------------
# Passing projections
# ---------------------------------------------------------------------------


class TestPassingProjections:
    @pytest.mark.parametrize("number", PASSING_PROJECTION_CASES)
    def test_passing_projection_emits_journey_payload(self, number):
        outcome = _outcome(number)
        assert outcome["output_kind"] == "projection"
        assert outcome["audience_validation_state"] == "passed"
        assert outcome["audience_payload_absent"] is False
        payload = outcome["audience_payload"]
        assert payload["payload_kind"] == "journey"
        assert payload["visit_axis_label"] == "访视轴"
        lane = payload["endpoint_lanes"][0]
        assert lane["endpoint_label"]
        assert lane["marker_label"]
        assert lane["source_jump_target"]
        paths = outcome["audience_validation_result"]["validated_display_string_paths"]
        assert "display_text" in paths
        assert "visit_axis_label" in paths
        assert any("endpoint_lanes" in path for path in paths)

    def test_out_of_cutoff_record_still_projects(self):
        outcome = _outcome(31)
        assert outcome["output_kind"] == "projection"
        assert outcome["audience_validation_state"] == "passed"


# ---------------------------------------------------------------------------
# Failed / suppressed payloads
# ---------------------------------------------------------------------------


class TestFailedPayloads:
    @pytest.mark.parametrize("number", FAILING_AUDIENCE_CASES)
    def test_failed_payload_is_suppressed(self, number):
        outcome = _outcome(number)
        assert "audience_payload" not in outcome
        assert outcome["audience_payload_absent"] is True
        assert outcome["audience_validation_result"]["validation_state"] == ("failed")
        assert outcome["audience_validation_result"]["payload_schema_version"] == "none"

    def test_lexicon_hits_recorded_exactly(self):
        outcome = _outcome(124)
        hits = outcome["audience_validation_result"]["forbidden_fragment_hits"]
        assert set(hits) == {"positive", "candidate", "正式事实", "候选信号"}

    def test_backend_qc_positive_hits(self):
        outcome = _outcome(216)
        hits = outcome["audience_validation_result"]["forbidden_fragment_hits"]
        assert set(hits) == {"positive", "candidate", "backend", "qc"}
        assert sorted(outcome["domain_assertions"]["forbidden_fragment_hits"]) == (
            ["backend", "candidate", "positive", "qc"]
        )
        assert outcome["domain_assertions"]["audience_validation_state"] == ("failed")

    def test_recorded_matters_collapse_rejected(self):
        outcome = _outcome(123)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "AudiencePayloadValidationError"
        assert outcome["audience_validation_result"]["validation_state"] == "failed"

    def test_not_evaluable_never_generates_query(self):
        outcome = _outcome(122)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06ContractViolationError"
        assert outcome["audience_validation_result"]["validation_state"] == "failed"

    def test_query_missing_sections_fails_audience(self):
        outcome = _outcome(121)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "AudiencePayloadValidationError"

    def test_statistical_claim_rejected(self):
        outcome = _outcome(139)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "AudiencePayloadValidationError"

    def test_binding_error_fails_audience(self):
        outcome = _outcome(187)
        assert outcome["output_kind"] == "error"
        assert outcome["error_type"] == "D06BindingContractError"
        assert outcome["audience_validation_state"] == "failed"


# ---------------------------------------------------------------------------
# PD wording gating
# ---------------------------------------------------------------------------


class TestPdWordingGating:
    def test_page_flag_conflict_forbids_pd_wording(self):
        outcome = _outcome(188)
        assert outcome["output_kind"] == "projection"
        assert outcome["audience_validation_state"] == "passed"
        assert outcome["domain_assertions"]["query_context"] == (
            "enrollment_state_unresolved"
        )
        assert outcome["domain_assertions"]["pd_wording_valid"] is False
        assert outcome["domain_assertions"]["forbidden_query_fragments"] == (
            ["方案偏离", "PD"]
        )

    def test_variant_matrix_pd_wording_only_enrolled(self):
        outcome = _outcome(162)
        outcomes = outcome["domain_assertions"]["query_context_outcomes"]
        assert outcomes["enrolled_or_post_enrollment"]["pd_wording_valid"] is True
        assert outcomes["enrollment_not_occurred"]["pd_wording_valid"] is False
        assert outcomes["enrollment_state_unresolved"]["pd_wording_valid"] is False


# ---------------------------------------------------------------------------
# No internal vocabulary leaks
# ---------------------------------------------------------------------------


class TestNoInternalVocabulary:
    def test_no_internal_keys_in_visible_paths(self):
        for number in PASSING_PROJECTION_CASES:
            outcome = _outcome(number)
            paths = outcome["audience_validation_result"][
                "validated_display_string_paths"
            ]
            for path in paths:
                for forbidden in (
                    "_id",
                    "_hash",
                    "_ref",
                    "classifier",
                    "payload",
                    "lineage",
                    "backend",
                    "log",
                ):
                    assert forbidden not in path, (
                        f"internal key leaked into display path: {path}"
                    )

    def test_payload_has_no_forbidden_visible_keys(self):
        from mm_r4.efficacy import forbidden_audience_keys

        for number in PASSING_PROJECTION_CASES:
            outcome = _outcome(number)
            assert not forbidden_audience_keys(outcome["audience_payload"])

    def test_internal_terms_never_reach_journey_labels(self):
        outcome = _outcome(31)
        payload = outcome["audience_payload"]
        rendered = str(payload)
        for forbidden in (
            "正式事实",
            "候选信号",
            "只读投影",
            "规则命中",
            "后端",
            "模型置信度",
            "算法异常",
            "模型判断",
        ):
            assert forbidden not in rendered
