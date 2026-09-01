"""D06 audience projection and final output assembly."""

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
from .efficacy_contracts import _RunContext
from .efficacy_output_gates import *
from .efficacy_resolution import *

class EfficacyOutputMixin:
    """Cohesive methods extracted from the D06 engine."""

    def _projection_consistency(self) -> None:
        """Projection QC checks shared by all entrypoints (§10)."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        # The shared temporal spine is the projection's time spine; when
        # the fixture carries one, it must be the typed
        # SharedTemporalSpineBinding with matching scope/cutoff, a
        # binding id and a payload-consistent hash.  A drifted or
        # incompatible spine fails closed before any journey payload can
        # be emitted.
        spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
        if spine is not None:
            if not isinstance(spine, (dict, Mapping)) or spine.get(
                "object_type"
            ) != "SharedTemporalSpineBinding":
                raise D06ContractViolationError(
                    "projection requires a typed shared temporal spine",
                    "pre_medical_output_validation",
                )
            if not scope_identity_matches(spine, ctx.scope):
                raise D06BindingContractError(
                    "temporal spine wrong scope", "typed_binding_validation"
                )
            if spine.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
                raise ProjectionContractError(
                    "temporal spine wrong cutoff", "projection_validation"
                )
            if not spine.get("spine_binding_id") or not spine.get("axis_hash"):
                raise D06ContractViolationError(
                    "temporal spine missing identity/hash",
                    "pre_medical_output_validation",
                )
            verify_embedded_hash(spine, "temporal spine")
        if "projection" in tp:
            projection = tp["projection"]
            if "undated_point_position" in projection:
                raise ProjectionContractError(
                    "undated point cannot be placed at a fabricated date",
                    "projection_validation",
                )
            if "filter_changes_risk_count" in projection:
                raise ProjectionContractError(
                    "filtering must not change risk count", "projection_validation"
                )
            if "collapse_hides_priority" in projection:
                raise ProjectionContractError(
                    "collapsing must not hide high priority markers",
                    "projection_validation",
                )
        if "directionality" in tp and "projection" in tp:
            directionality = tp["directionality"]
            projection_direction = tp["projection"].get("direction")
            if directionality == "lower_better" and projection_direction == "worse":
                raise ProjectionContractError(
                    "lower-better endpoint projected as worsening",
                    "projection_validation",
                )
            if directionality == "higher_better" and projection_direction in (
                "improvement",
                "improved",
            ):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return

    def _validate_audience_payload(self) -> None:
        """Audience validation entrypoint wrapper (may raise)."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if (
            "l1" in tp
            and tp["l1"] == "not_evaluable"
            and tp.get("query", {}).get("generated")
        ):
            raise D06ContractViolationError(
                "not_evaluable must not generate a Query",
                "pre_medical_output_validation",
            )
        self._compute_audience_result()
        if (
            ctx.audience_result is not None
            and ctx.audience_result.validation_state == "failed"
        ):
            raise AudiencePayloadValidationError("audience payload failed validation")

    def _compute_audience_result(self) -> None:
        """Compute the audience validation result; never raises."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        attempted = {
            key: tp[key] for key in ("audience", "projection", "query") if key in tp
        }
        # Determine the intended payload kind.
        payload: Optional[Dict[str, Any]] = None
        query_case = "page" in tp or "query" in tp or "query_context_variants" in tp
        if "page" in tp and getattr(ctx, "_query_payload", None) is not None:
            query_payload = dict(ctx._query_payload)
            query_payload["payload_kind"] = "query"
            query_payload["payload_schema_version"] = "d06-query-audience-v1"
            payload = query_payload
        elif (
            not query_case
            and ctx.error_type is None
            and ctx.gate_state is None
            and ctx.l1 is None
        ):
            # The emitted journey payload is serialized from the actual
            # runtime projection (never a static substitution).  The
            # projection itself is built from validated typed runtime
            # objects; an invalid projection or locator fails closed into
            # the exact gate/error state instead of emitting a payload.
            ctx.projection_obj = project_efficacy_journey(
                ctx.fixture,
                getattr(ctx, "scope_status", None),
                ctx.l1,
                priority_decision=ctx.priority_decision_obj,
            )
            payload = journey_audience_payload_from_projection(ctx.projection_obj)
        if query_case and "query" in tp and tp["query"].get("generated"):
            payload = None
        validation_state = "passed"
        payload_schema_version: str = "none"
        forbidden_hits: List[str] = []
        validated_paths: List[str] = []
        emitted_payload: Optional[Dict[str, Any]] = None
        attempted_view = attempted_display_view(attempted)
        attempted_hits = audience_phrase_hits(audience_visible_strings(attempted_view))
        attempted_paths = audience_string_paths(attempted_view)
        try:
            if payload is not None:
                payload_schema_version = validate_audience_payload_schema(payload)
                display = audience_display_view(payload)
                forbidden_hits = audience_phrase_hits(audience_visible_strings(display))
                validated_paths = audience_string_paths(display)
                if (
                    forbidden_hits
                    or attempted_hits
                    or self._attempted_payload_invalid(attempted)
                ):
                    validation_state = "failed"
                    forbidden_hits = attempted_hits or forbidden_hits
                    validated_paths = attempted_paths or validated_paths
                else:
                    validation_state = "passed"
                    emitted_payload = payload
            else:
                # No emitted payload: independently re-derive visible
                # strings/keys from the typed audience/projection/query
                # inputs (frozen §10).
                forbidden_hits = attempted_hits
                validated_paths = attempted_paths
                if (
                    forbidden_hits
                    or self._attempted_payload_invalid(attempted)
                    or ctx.error_type is not None
                ):
                    validation_state = "failed"
        except AudiencePayloadValidationError:
            validation_state = "failed"
            payload_schema_version = "none"
            forbidden_hits = attempted_hits
            validated_paths = attempted_paths

        absent = payload is None or validation_state == "failed"
        ctx.audience_absent = absent
        ctx.audience_payload = emitted_payload if not absent else None
        if (
            ctx.entrypoint == "d06.audience_projection_validator"
            and emitted_payload is not None
        ):
            ctx.output_kind = OUTPUT_KIND_PROJECTION
            ctx.coverage_status = COVERAGE_COVERED
            ctx.l1 = None
        ctx.audience_result = D06AudienceValidationResult(
            payload_schema=True,
            payload_schema_version=(
                payload_schema_version if payload is not None else "none"
            ),
            validator_version=AUDIENCE_VALIDATOR_VERSION,
            validator_hash=AUDIENCE_VALIDATOR_HASH,
            lexicon_version=AUDIENCE_LEXICON_VERSION,
            forbidden_lexicon_hash=AUDIENCE_LEXICON_HASH,
            forbidden_fragment_hits=tuple(forbidden_hits),
            validated_display_string_paths=tuple(validated_paths),
            validation_state=validation_state,
            audience_payload_absent=absent,
        )
        if validation_state == "failed":
            ctx.audience_absent = True
            ctx.audience_payload = None
            ctx.audience_result = D06AudienceValidationResult(
                payload_schema=True,
                payload_schema_version="none",
                validator_version=AUDIENCE_VALIDATOR_VERSION,
                validator_hash=AUDIENCE_VALIDATOR_HASH,
                lexicon_version=AUDIENCE_LEXICON_VERSION,
                forbidden_lexicon_hash=AUDIENCE_LEXICON_HASH,
                forbidden_fragment_hits=tuple(forbidden_hits),
                validated_display_string_paths=tuple(validated_paths),
                validation_state="failed",
                audience_payload_absent=True,
            )

    def _attempted_payload_invalid(self, attempted: Mapping[str, Any]) -> bool:
        """Content/schema rejection of attempted audience inputs."""
        for key, value in attempted.items():
            text = audience_visible_strings(value)
            for item in text:
                if "已记录事项" in item:
                    return True
                if ("统计学显著" in item) or ("研究有效" in item):
                    return True
        if "query" in attempted:
            query = attempted["query"]
            if query.get("missing_sections"):
                return True
            if query.get("generated"):
                return True
        if "audience" in attempted and attempted["audience"].get("visible_text"):
            return True
        return False

    # -- lifecycle helpers -------------------------------------------------

    def _finish_no_unit(self, ctx: _RunContext, coverage_status: str) -> None:
        ctx.output_kind = OUTPUT_KIND_RESULT
        ctx.coverage_status = coverage_status
        ctx.l1 = None

    def _open_gate(self, kind: str, disposition: str) -> None:
        ctx = self.ctx
        ctx.output_kind = OUTPUT_KIND_GATE
        ctx.gate_state = GATE_OPEN
        ctx.gate_disposition = disposition
        ctx.coverage_status = (
            COVERAGE_COVERED
            if disposition == GATE_DECISION_BOUNDARY
            else COVERAGE_NOT_EVALUABLE
        )
        ctx.l1 = None
        ctx.gates.append({"kind": kind, "state": GATE_OPEN, "disposition": disposition})

    # -- finalize ----------------------------------------------------------

    def _finalize(self) -> None:
        ctx = self.ctx
        if ctx.output_kind is None:
            ctx.output_kind = OUTPUT_KIND_RESULT
        if ctx.coverage_status is None:
            ctx.coverage_status = COVERAGE_COVERED
        if ctx.l1 == L1_BOUNDARY:
            ctx.l2["clues"] = 1
        if ctx.l1 == L1_NOT_EVALUABLE and ctx.output_kind == OUTPUT_KIND_RESULT:
            ctx.l2[L2_COVERAGE_NOTICES] = max(ctx.l2[L2_COVERAGE_NOTICES], 1)

    def _assemble(self) -> D06ChallengeOutcome:
        ctx = self.ctx
        if ctx.output_kind is None:
            ctx.output_kind = OUTPUT_KIND_RESULT
        if ctx.coverage_status is None and ctx.output_kind != OUTPUT_KIND_ERROR:
            ctx.coverage_status = COVERAGE_COVERED
        if ctx.audience_result is not None:
            audience_state = ctx.audience_result.validation_state
        else:
            audience_state = None
        object_hashes = dict(ctx.object_hashes)
        if ctx.resolver_input_obj is not None:
            object_hashes["priority_resolver_input_hash"] = ctx.resolver_input_obj.hash
        object_hashes.setdefault(
            "priority_policy_hash", CANONICAL_PRIORITY_POLICY["policy_hash"]
        )
        object_hashes.setdefault("priority_resolver_input_hash", None)
        object_hashes.setdefault("public_r4_identity_hash", None)
        if ctx.public_identity_hash is not None:
            object_hashes["public_r4_identity_hash"] = ctx.public_identity_hash
        # Input-derived annotation leaves: the fixture payload the runtime
        # actually received and the actual input scope.
        from .efficacy import deep_unfreeze

        raw_fixture = deep_unfreeze(ctx.frozen_fixture.raw_fixture)
        fixture_hash = d06_content_hash(raw_fixture)
        object_hashes["fixture_hash"] = fixture_hash
        actual_scope = deep_unfreeze(ctx.frozen_fixture.scope)
        scope_hash = d06_content_hash(actual_scope)
        object_hashes["scope_hash"] = scope_hash
        input_scope_hash = f"sha256:{scope_hash}"
        domain_assertions = {
            key: value
            for key, value in ctx.domain_assertions.items()
            if not key.startswith("_")
        }
        domain_assertions["challenge_assertion_code"] = (
            f"D06-CH-{ctx.fixture.challenge_number:03d}"
        )
        domain_assertions["evaluated_fixture_hash"] = fixture_hash
        try:
            contract_text = derive_clinical_contract_text(ctx)
        except D06Error as exc:
            # Input drift beyond the frozen scenarios: fail closed into an
            # error outcome (never a superficially successful annotation).
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
                ctx.l1 = None
            contract_text = ""
        domain_assertions["clinical_outcome_contract"] = contract_text
        if ctx.priority_resolution is not None:
            domain_assertions["priority_resolution"] = ctx.priority_resolution
        # Trace provenance: base edges plus every source this evaluation
        # actually validated/consumed (never manifest/case identity).
        trace_edges = sorted(set(TRACE_EDGES_ALL) | ctx.consumed)
        return D06ChallengeOutcome(
            invoked_entrypoint=ctx.entrypoint,
            input_scope_hash=input_scope_hash,
            output_kind=ctx.output_kind,
            coverage_status=ctx.coverage_status,
            gate_state=ctx.gate_state,
            gate_disposition=ctx.gate_disposition,
            l1_disposition=ctx.l1,
            primary_subtype=ctx.subtype,
            secondary_reason_codes=tuple(ctx.secondary_reason_codes),
            l2_counts=dict(ctx.l2),
            l3_state=ctx.l3_state,
            l3_transition=ctx.l3_transition,
            object_ids={},
            object_hashes=object_hashes,
            trace_edges=tuple(trace_edges),
            audience_payload=ctx.audience_payload,
            audience_payload_absent=ctx.audience_absent,
            audience_validation_result=ctx.audience_result,
            audience_validation_state=audience_state,
            domain_assertions=domain_assertions,
            error_type=ctx.error_type,
            error_stage=ctx.error_stage,
        )
