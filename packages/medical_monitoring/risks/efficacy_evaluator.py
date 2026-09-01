"""R4-D06 efficacy slice -- deterministic evaluator pipeline and entrypoints.

Frozen source of truth: ``FROZEN_R4_D06_CONTRACT_V1_16``.  This module owns
the D06 **evaluation pipeline** consuming the typed fixture surface
(:class:`D06Fixture`) and emitting typed
:class:`~mm_r4.efficacy.D06ChallengeOutcome` objects:

1. **Scope/identity validation** (contract §5.3 order): the frozen Run/
   snapshot/cutoff identity, accepted assessment/item/result inventory,
   versioned definitions, owner routing, D05 occurrence/timing binding and
   shared temporal spine are validated before any medical expected-set is
   formed; wrong/missing/conflicting authority fails closed.
2. **Gates**: applicability/routing/definition/algorithm/baseline/
   unit_or_scale/dependency/cutoff_scope gates with the closed
   open+boundary|not_evaluable+blocks / closed+resolved truth table; an
   open gate never enters the medical expected-set.
3. **Deterministic unit evaluation** across the closed unit kinds (item
   completeness, item value validity, score recalculation, baseline
   selection, change recalculation, response classification, endpoint
   composition, repeat selection, rater/mode consistency, individual trend
   pattern, accepted report consistency) with the five exclusive L1
   dispositions.
4. **Priority resolution** via the frozen five-step first-match policy,
   and -- only for positive roots -- the emitted
   ``D06PriorityDecision`` / ``D06RiskBinding`` / ``PublicR4RiskIdentity``
   with exact content addressing.
5. **Enrollment-aware three-part Chinese Query drafts** and coverage-gap
   notices (``not_evaluable`` never emits a Query).
6. **Audience payload validation** with the frozen ``d06-audience-zh-v1``
   lexicon; failed/forbidden payloads are suppressed.

Entrypoints exposed here map 1:1 to the frozen catalog entrypoint ids:
``d06.efficacy_evaluator``, ``d06.gate_evaluator``,
``d06.contract_schema_validator``, ``d06.audience_projection_validator``,
``d06.challenge_registry_validator`` (the last lives in
:mod:`mm_r4.efficacy_fixtures`).

The runtime never imports the frozen catalog/oracle/registry and never
branches on challenge number, fixture id, test id, expected text or
expected outcome.  All data is synthetic and offline.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..projections.efficacy import (
    project_efficacy_journey,
    journey_audience_payload_from_projection,
)
from .efficacy import (
    AUDIENCE_LEXICON_HASH,
    AUDIENCE_LEXICON_VERSION,
    AUDIENCE_VALIDATOR_HASH,
    AUDIENCE_VALIDATOR_VERSION,
    CANONICAL_PRIORITY_POLICY,
    COVERAGE_COVERED,
    COVERAGE_NOT_APPLICABLE,
    COVERAGE_NOT_EVALUABLE,
    D06AudienceValidationResult,
    D06BindingContractError,
    D06ChallengeOutcome,
    D06ContractViolationError,
    D06Error,
    D06PriorityDecision,
    D06PriorityResolverInput,
    D06RiskBinding,
    D06UnitStableCore,
    DECISION_MULTI_FEASIBLE_BOUNDARY,
    DECISION_NOT_EVALUABLE,
    DECISION_UNIQUE,
    DIRECTIONALITIES,
    ENDPOINT_ROLES,
    GATE_ALGORITHM,
    GATE_APPLICABILITY,
    GATE_CUTOFF_SCOPE,
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_DEFINITION,
    GATE_DEPENDENCY,
    GATE_OPEN,
    GATE_ROUTING,
    GATE_UNIT_OR_SCALE,
    L1_BOUNDARY,
    L1_NOT_APPLICABLE,
    L1_NOT_EVALUABLE,
    L1_POSITIVE,
    L1_NEGATIVE,
    L2_COVERAGE_NOTICES,
    L2_QUERIES,
    L2_RISKS,
    OUTPUT_KIND_DEFINITION_BINDING,
    OUTPUT_KIND_ERROR,
    OUTPUT_KIND_GATE,
    OUTPUT_KIND_PROJECTION,
    OUTPUT_KIND_RESULT,
    PRIORITY_REASON_BY_STEP,
    ProjectionContractError,
    QUERY_CONTEXT_ENROLLED,
    SchemaContractError,
    OwnerScopeContractError,
    QUERY_CONTEXT_NOT_OCCURRED,
    QUERY_CONTEXT_UNRESOLVED,
    SCOPE_IDENTITY_FIELDS,
    SCOPE_IN_SCOPE,
    SCOPE_NOT_EVALUABLE,
    SCOPE_OUT_OF_CUTOFF,
    TTE_STATUS_BOUNDARY,
    TTE_STATUS_CENSORED,
    TTE_STATUS_COMPETING_EVENT,
    TTE_STATUS_EVENT,
    TRACE_EDGES_ALL,
    UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY,
    UNIT_KIND_BASELINE_SELECTION,
    UNIT_KIND_CHANGE_RECALCULATION,
    UNIT_KIND_ENDPOINT_COMPOSITION,
    UNIT_KIND_INDIVIDUAL_TREND_PATTERN,
    UNIT_KIND_ITEM_COMPLETENESS,
    UNIT_KIND_ITEM_VALUE_VALIDITY,
    UNIT_KIND_RATER_OR_MODE_CONSISTENCY,
    UNIT_KIND_REPEAT_SELECTION,
    UNIT_KIND_RESPONSE_CLASSIFICATION,
    UNIT_KIND_SCORE_RECALCULATION,
    UNIT_KIND_TO_SUBTYPE,
    _audience_normalize,
    AUDIENCE_PHRASES,
    AudiencePayloadValidationError,
    ChallengeAssertionContractError,
    ChallengeRegistryIntegrityError,
    audience_display_view,
    audience_phrase_hits,
    audience_string_paths,
    audience_visible_strings,
    attempted_display_view,
    d06_canonical_json,
    d06_content_hash,
    d06_sha256_text,
    resolve_priority_step,
    scope_identity_matches,
    validate_audience_payload_schema,
    verify_content_hash,
    verify_embedded_hash,
    verify_lineage_hash,
)

from .efficacy_contracts import *
from .efficacy_contracts import _GateRaised, _RunContext
from .efficacy_output_gates import *
from .efficacy_resolution import *
from .efficacy_resolution import _canonical_decimal
from .efficacy_pipeline_mixin import EfficacyPipelineMixin
from .efficacy_unit_mixin import EfficacyUnitEvaluationMixin
from .efficacy_tte_query_mixin import EfficacyTteQueryMixin
from .efficacy_output_mixin import EfficacyOutputMixin


class EfficacyEngine(
    EfficacyPipelineMixin,
    EfficacyUnitEvaluationMixin,
    EfficacyTteQueryMixin,
    EfficacyOutputMixin,
):
    """Deterministic D06 evaluation pipeline."""

def evaluate_efficacy_fixture(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.efficacy_evaluator`` -- the full deterministic pipeline."""
    engine = EfficacyEngine(fixture, "d06.efficacy_evaluator")
    return engine.run()


def evaluate_gate(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.gate_evaluator`` -- gate-focused evaluation."""
    engine = EfficacyEngine(fixture, "d06.gate_evaluator")
    return engine.run()


def validate_contract_schema(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.contract_schema_validator`` -- typed-schema validation."""
    engine = EfficacyEngine(fixture, "d06.contract_schema_validator")
    return engine.run()


def validate_audience_projection(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.audience_projection_validator`` -- audience payload QC."""
    engine = EfficacyEngine(fixture, "d06.audience_projection_validator")
    return engine.run()


def validate_challenge_registry_input(
    fixture: D06Fixture,
) -> D06ChallengeOutcome:
    """``d06.challenge_registry_validator`` runtime entrypoint."""
    return EfficacyEngine(fixture, "d06.challenge_registry_validator").run_registry()
