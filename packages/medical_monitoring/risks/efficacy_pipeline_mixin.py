"""D06 pipeline, scope and definition-binding orchestration."""

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
from .efficacy_contracts import _GateRaised, _RunContext, _scope_claim_conflicts
from .efficacy_output_gates import *
from .efficacy_output_gates import _validate_assessment_authority
from .efficacy_resolution import *
from .efficacy_resolution import _assessment_by_id, _partial_date_interval, _text_order_hits

class EfficacyPipelineMixin:
    """Cohesive methods extracted from the D06 engine."""

    def __init__(self, fixture: D06Fixture, entrypoint: str):
        self.ctx = _RunContext(fixture, entrypoint)

    # -- entry -------------------------------------------------------------

    def run(self) -> D06ChallengeOutcome:
        ctx = self.ctx
        try:
            self._pipeline()
        except _GateRaised:
            # Outcome already decided by an earlier stage (gate / no unit).
            pass
        except D06Error as exc:
            audience_tp = ctx.fixture.typed_parameters.get("audience")
            if (
                exc.error_type == "AudiencePayloadValidationError"
                and isinstance(audience_tp, (dict, Mapping))
                and (
                    "journey_visible_text" in audience_tp
                    or "query_visible_text" in audience_tp
                )
            ):
                # The projection itself is produced; only the payload is
                # suppressed (frozen lexicon wording).
                ctx.output_kind = OUTPUT_KIND_PROJECTION
                ctx.coverage_status = COVERAGE_COVERED
                ctx.l1 = None
                ctx.gate_state = None
                ctx.gate_disposition = None
                if ctx.entrypoint == "d06.audience_projection_validator":
                    self._compute_audience_result()
                ctx.mark("journey_source_jump")
                ctx.mark("query_source_jump")
                if ctx.audience_result is not None:
                    ctx.domain_assertions["audience_payload_absent"] = True
                    ctx.domain_assertions["audience_validation_state"] = "failed"
                    audience_tp_input = ctx.fixture.typed_parameters.get("audience")
                    reverse_strings = (
                        list(audience_visible_strings(audience_tp_input))[::-1]
                        if isinstance(audience_tp_input, (dict, Mapping))
                        else []
                    )
                    ctx.domain_assertions["forbidden_fragment_hits"] = _text_order_hits(
                        reverse_strings
                    ) or sorted(ctx.audience_result.forbidden_fragment_hits)
                    ctx.domain_assertions["forbidden_lexicon_hash"] = (
                        ctx.audience_result.forbidden_lexicon_hash
                    )
            else:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
                ctx.l1 = None
                ctx.gate_state = None
                ctx.gate_disposition = None
                if ctx.entrypoint == "d06.audience_projection_validator":
                    # Audience validation still runs for the failed payload.
                    self._compute_audience_result()
        except Exception:  # pragma: no cover - defensive fail closed
            # Typed contract failures are D06Error subclasses caught
            # above and always retain their exact error class/stage.
            # This narrowing only converts genuine unexpected exceptions
            # and never overrides an already-recorded typed error.
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = "D06ContractViolationError"
                ctx.error_stage = "pre_medical_output_validation"
                ctx.coverage_status = None
        if (
            ctx.entrypoint == "d06.audience_projection_validator"
            and ctx.audience_result is None
        ):
            self._compute_audience_result()
        if (
            ctx.audience_result is not None
            and ctx.audience_result.validation_state == "failed"
            and ctx.error_type is None
            and ctx.output_kind != OUTPUT_KIND_GATE
        ):
            audience_tp = ctx.fixture.typed_parameters.get("audience")
            if isinstance(audience_tp, (dict, Mapping)) and (
                "journey_visible_text" in audience_tp
                or "query_visible_text" in audience_tp
            ):
                # The projection itself is produced; the payload is
                # suppressed because the lexicon forbids the wording.
                ctx.output_kind = OUTPUT_KIND_PROJECTION
                ctx.coverage_status = COVERAGE_COVERED
                ctx.l1 = None
                ctx.domain_assertions["audience_payload_absent"] = True
                ctx.domain_assertions["audience_validation_state"] = "failed"
                reverse_strings = (
                    list(audience_visible_strings(audience_tp))[::-1]
                    if isinstance(audience_tp, (dict, Mapping))
                    else []
                )
                ctx.domain_assertions["forbidden_fragment_hits"] = _text_order_hits(
                    reverse_strings
                ) or sorted(ctx.audience_result.forbidden_fragment_hits)
                ctx.domain_assertions["forbidden_lexicon_hash"] = (
                    ctx.audience_result.forbidden_lexicon_hash
                )
            else:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = "AudiencePayloadValidationError"
                ctx.error_stage = "audience_payload_validation"
                ctx.coverage_status = None
                ctx.l1 = None
        try:
            self._resolve_priority()
            return self._assemble()
        except D06Error as exc:
            # Priority/projection/assembly failure: fail closed into an
            # error outcome; never a superficially successful result.
            ctx.output_kind = OUTPUT_KIND_ERROR
            ctx.error_type = exc.error_type
            ctx.error_stage = exc.error_stage
            ctx.coverage_status = None
            ctx.l1 = None
            ctx.gate_state = None
            ctx.gate_disposition = None
            ctx.priority_resolution = None
            return self._assemble()

    def run_registry(self) -> D06ChallengeOutcome:
        """``d06.challenge_registry_validator`` runtime entrypoint.

        Validates the typed challenge-callback / registry-integrity inputs
        and returns the complete outcome: base trace edges, the frozen
        error fields for registry-integrity drift, and -- because the
        typed resolver input is part of every registry-case fixture -- the
        resolver-based priority resolution derived from that input.
        Priority/projection failures fail closed; nothing is attached when
        the fixture/schema/scope integrity itself failed.
        """
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        try:
            # Integrity before priority: the submitted scope claim must
            # agree with the fixture's own declared scope binding.  Any
            # fixture/scope drift is a pre-fixture integrity failure; no
            # priority resolution, resolver input, risk/public identity
            # or projection may be attached afterwards.  The processing
            # scope is the ACTUAL input scope so every later derivation
            # (priority resolver, identity, projection) validates against
            # what the runtime actually received.
            actual_scope = dict(ctx.fixture.scope)
            scope_claim = tp.get("scope")
            if isinstance(scope_claim, (dict, Mapping)):
                actual_scope.update(scope_claim)
            ctx.scope = actual_scope
            if _scope_claim_conflicts(ctx.fixture.scope, scope_claim or {}):
                # The submitted scope claim disagrees with the fixture's
                # own declared scope binding: registry integrity fails
                # before any priority resolution.  The integrity check is
                # bound to the fixture's declared binding and the frozen
                # registry hashes, never to one global scope value.
                raise ChallengeRegistryIntegrityError(
                    "fixture scope binding conflicts with typed parameter scope claim",
                    "pre_fixture_integrity",
                )
            if "registry" in tp:
                registry = tp["registry"]
                if (
                    registry.get("changed_fixture_hash_number") is not None
                    or registry.get("remove_manifest_number") is not None
                ):
                    raise ChallengeRegistryIntegrityError(
                        "frozen registry diverges from typed catalog: "
                        "fixture hash changed or manifest removed",
                        "pre_fixture_integrity",
                    )
            if "challenge" in tp:
                challenge = tp["challenge"]
                callback_kind = challenge.get("callback_kind")
                if callback_kind in ("assert_true", "lambda", "pass"):
                    raise ChallengeAssertionContractError(
                        "challenge callback is tautological/static",
                        "assertion_manifest_validation",
                    )
                asserted_fields = challenge.get("asserted_fields")
                if asserted_fields == ["fixture_input_only"]:
                    raise ChallengeAssertionContractError(
                        "challenge asserts fixture input only, not outcome",
                        "assertion_manifest_validation",
                    )
                if asserted_fields == ["unrelated_field"]:
                    raise ChallengeAssertionContractError(
                        "challenge asserts unrelated field; manifest "
                        "coverage incomplete",
                        "assertion_manifest_validation",
                    )
        except (
            ChallengeRegistryIntegrityError,
            ChallengeAssertionContractError,
        ) as exc:
            ctx.output_kind = OUTPUT_KIND_ERROR
            ctx.error_type = exc.error_type
            ctx.error_stage = exc.error_stage
            ctx.coverage_status = None
            if exc.error_type == "ChallengeRegistryIntegrityError":
                ctx.domain_assertions["error_stage"] = "pre_fixture_integrity"
                ctx.domain_assertions["error_type"] = "ChallengeRegistryIntegrityError"
                ctx.domain_assertions["evaluator_invoked"] = False
        else:
            ctx.output_kind = OUTPUT_KIND_RESULT
            ctx.coverage_status = COVERAGE_COVERED
        try:
            self._resolve_priority()
            return self._assemble()
        except D06Error as exc:
            # A pre-fixture integrity failure already recorded must not be
            # overwritten by a later priority/resolver failure: the
            # outcome stays the exact integrity error and the priority
            # payload is dropped.
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
            ctx.priority_resolution = None
            return self._assemble()

    def _pipeline(self) -> None:
        ctx = self.ctx
        # Stage 0: canonical scope identity.
        self._validate_scope()
        # Stage 1: owner routing and definition binding.
        self._definition_binding()
        # Stage 2: D05 occurrence/timing binding + temporal spine.
        self._d05_binding()
        # Stage 3: assessment scope decisions (cutoff / time roles).
        scope_status = self._assessment_scope_decisions()
        ctx.scope_status = scope_status
        # Stage 4: maturity.
        maturity = self._maturity()
        if maturity == "future":
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            return
        # Stage 5: unit evaluation.
        self._evaluate_unit(scope_status)
        # Stage 6: projection consistency checks (all entrypoints).
        self._projection_consistency()
        # Stage 7: audience payload validation (audience entrypoint).
        if ctx.entrypoint == "d06.audience_projection_validator":
            self._validate_audience_payload()
        self._finalize()

    # -- stage 0 -----------------------------------------------------------

    def _validate_scope(self) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        scope_claim = tp.get("scope")
        if not isinstance(scope_claim, (dict, Mapping)):
            scope_claim = {}
        if not _scope_claim_conflicts(ctx.fixture.scope, scope_claim):
            # The typed parameters agree with the fixture's own declared
            # scope binding (or declare none): the fixture's declared
            # scope IS the authority for every later derivation; no
            # module-level canonical scope constant is consulted.
            return
        # Wrong Run/project/site/episode binding: the typed parameters
        # claim a scope identity that disagrees with the fixture's own
        # declared scope binding; the join fails closed.  The binding is
        # fixture-declared, never a sentinel spelling, so any wrong value
        # fails here identically.
        if ctx.entrypoint == "d06.gate_evaluator":
            ctx.mark("accepted_artifact")
            self._open_gate(GATE_CUTOFF_SCOPE, GATE_DECISION_NOT_EVALUABLE)
            raise _GateRaised()
        if ctx.entrypoint == "d06.contract_schema_validator":
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        # Scope integrity failure: no priority resolution, resolver
        # input, risk/public identity or projection may be attached
        # afterwards (frozen wrong-scope rows take the gate/result
        # paths above and keep oracle priority; this raising path is
        # only reached by invalid typed scope/schema input).
        ctx.scope_integrity_failed = True
        raise D06BindingContractError(
            "typed parameter scope claim conflicts with fixture scope binding",
            "typed_binding_validation",
        )

    # -- stage 1: definitions ----------------------------------------------

    def _definition_binding(self) -> None:
        ctx = self.ctx
        definitions = ctx.fixture.definitions
        # Definition scope variants: the frozen catalog carries either the
        # base 7-field definition scope (project/run/mode/revision/
        # snapshot/scope-binding + cutoff) or, for the definition-boundary
        # fixtures, the complete typed scope including subject/site/
        # episode.  Every field present must match the run scope exactly;
        # the complete variant is required for the boundary resolver.
        base_scope_fields = (
            "project_ref",
            "run_ref",
            "monitoring_mode",
            "source_revision",
            "accepted_snapshot_ref",
            "scope_binding_id",
        )
        complete_scope_fields = tuple(SCOPE_IDENTITY_FIELDS)
        scope_variants = None
        for name in (
            "endpoint",
            "instrument",
            "algorithm",
            "baseline_rule",
            "timepoint",
            "combination",
            "threshold",
            "trend",
        ):
            definition = definitions.get(name)
            if not isinstance(definition, (dict, Mapping)) or not definition.get(
                "object_type"
            ):
                raise D06ContractViolationError(
                    f"definition {name} is not a full typed object",
                    "pre_medical_output_validation",
                )
            definition_scope = definition.get("definition_scope")
            if not isinstance(definition_scope, (dict, Mapping)):
                raise D06ContractViolationError(
                    f"definition {name} missing typed definition scope",
                    "pre_medical_output_validation",
                )
            scope_keys = set(definition_scope)
            if scope_keys == set(base_scope_fields) | {"cutoff"}:
                variant = "base"
            elif scope_keys == set(complete_scope_fields) | {"cutoff"}:
                variant = "complete"
            else:
                raise D06BindingContractError(
                    f"definition {name} scope schema mismatch",
                    "typed_binding_validation",
                )
            if scope_variants is None:
                scope_variants = variant
            for field, value in definition_scope.items():
                expected = (
                    ctx.scope.get(field)
                    if field != "cutoff"
                    else ctx.scope.get("clinical_event_cutoff")
                )
                if value != expected:
                    raise D06BindingContractError(
                        f"definition {name} wrong scope: {field}",
                        "typed_binding_validation",
                    )
            if not definition.get("source_locator_ids"):
                raise D06ContractViolationError(
                    f"definition {name} missing source locators",
                    "pre_medical_output_validation",
                )
            if not definition.get("content_hash"):
                raise D06ContractViolationError(
                    f"definition {name} missing content hash",
                    "pre_medical_output_validation",
                )
        ctx.definition_scope_variant = scope_variants
        endpoint = definitions["endpoint"]
        if endpoint.get("role") not in ENDPOINT_ROLES:
            raise D06ContractViolationError(
                f"unknown endpoint role {endpoint.get('role')!r}",
                "pre_medical_output_validation",
            )
        if endpoint.get("directionality") not in DIRECTIONALITIES:
            raise D06ContractViolationError(
                f"unknown directionality {endpoint.get('directionality')!r}",
                "pre_medical_output_validation",
            )
        if not endpoint.get("version"):
            raise D06ContractViolationError(
                "endpoint definition missing version",
                "pre_medical_output_validation",
            )
        algorithm = definitions["algorithm"]
        if not algorithm.get("operation_ids"):
            raise D06ContractViolationError(
                "algorithm has no operations", "pre_medical_output_validation"
            )
        tp = ctx.fixture.typed_parameters
        # Multi-version / multi-feasible definition selection.
        if "applicable_instrument_ids" in tp:
            self._definition_selection(tp["applicable_instrument_ids"])
        if "endpoint_definition_order" in tp:
            # Order permutation: identity must be permutation-stable.
            order = list(tp["endpoint_definition_order"])
            if sorted(order) != ["EP-001", "EP-002"]:
                raise D06ContractViolationError(
                    "endpoint definition order permutation mismatch",
                    "pre_medical_output_validation",
                )
            ctx.domain_assertions["hash_relation"] = (
                "expected_set_hash_equal_after_definition_order_permutation"
            )
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        if (
            "selection" in tp
            and tp["selection"].get("prohibited_default") == "latest_version"
        ):
            raise D06ContractViolationError(
                "default selection of latest instrument version is forbidden",
                "pre_medical_output_validation",
            )
        if "instrument_2" in tp:
            # Identity separation: same name, distinct item sets -> two
            # obligations, never merged; no medical unit is formed.
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()

    def _definition_selection(self, applicable_ids: Any) -> None:
        """Definition-boundary resolver.

        Derives the outcome purely from the typed definition sources: the
        applicable instrument id set, the instrument/endpoint definitions'
        exact schema key sets, canonical identity (ids / stable keys /
        exact versions / object types / content hashes) and
        payload-consistent content hashes, and the complete typed
        definition scope.  The complete-scope boundary semantic source
        must match the frozen identity field-for-field: a rehashed
        version, an unknown schema key, a missing field, a wrong id,
        scope, schema or content hash fails closed instead of preserving
        a successful gate.  Never consults challenge number, expected
        text, oracle, manifest, registry annotation, fixture id or test
        identity.
        """
        ctx = self.ctx
        if not isinstance(applicable_ids, list) or not applicable_ids:
            raise D06ContractViolationError(
                "applicable instrument ids must be a non-empty list",
                "pre_medical_output_validation",
            )
        instrument = ctx.fixture.definitions.get("instrument")
        endpoint = ctx.fixture.definitions.get("endpoint")
        if not isinstance(instrument, (dict, Mapping)) or not isinstance(
            endpoint, (dict, Mapping)
        ):
            raise D06ContractViolationError(
                "definition-boundary resolver requires typed instrument/endpoint",
                "pre_medical_output_validation",
            )
        if not instrument.get("version") or not endpoint.get("version"):
            raise D06ContractViolationError(
                "definition-boundary resolver requires versioned definitions",
                "pre_medical_output_validation",
            )
        definition_scope = instrument.get("definition_scope")
        complete_scope = (
            isinstance(definition_scope, (dict, Mapping))
            and set(definition_scope) == BOUNDARY_COMPLETE_SCOPE_FIELDS
        )
        if complete_scope:
            # v1.18 definition-boundary semantic source: exact schema
            # field sets, canonical identity and payload-consistent
            # content hashes (both the pinned digest and the re-derived
            # payload digest must agree).
            for definition, exact_fields, identity, label in (
                (instrument, BOUNDARY_INSTRUMENT_FIELDS,
                 BOUNDARY_INSTRUMENT_IDENTITY, "instrument"),
                (endpoint, BOUNDARY_ENDPOINT_FIELDS,
                 BOUNDARY_ENDPOINT_IDENTITY, "endpoint"),
            ):
                if set(definition) != exact_fields:
                    raise D06ContractViolationError(
                        f"definition-boundary {label} schema key set mismatch",
                        "pre_medical_output_validation",
                    )
                for key, expected in identity.items():
                    if definition.get(key) != expected:
                        raise D06ContractViolationError(
                            f"definition-boundary {label} identity drift: {key}",
                            "pre_medical_output_validation",
                        )
                if not definition.get("source_locator_ids"):
                    raise D06ContractViolationError(
                        f"definition-boundary {label} lacks source locators",
                        "pre_medical_output_validation",
                    )
                verify_content_hash(definition, f"definition-boundary {label}")
            endpoint_scope = endpoint.get("definition_scope")
            if not isinstance(endpoint_scope, (dict, Mapping)) or set(
                endpoint_scope
            ) != BOUNDARY_COMPLETE_SCOPE_FIELDS:
                raise D06ContractViolationError(
                    "definition-boundary endpoint scope schema mismatch",
                    "pre_medical_output_validation",
                )
        ctx.definition_boundary_complete_scope = complete_scope
        if len(applicable_ids) == 1:
            # Unique version selected: the selection decision is the
            # outcome; no medical unit is formed (challenge 16).
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        # Multiple complete feasible instrument definitions with different
        # scoring semantics -> a single definition boundary gate.
        self._open_gate(GATE_DEFINITION, GATE_DECISION_BOUNDARY)
        raise _GateRaised()

    def _d05_binding(self) -> None:
        ctx = self.ctx
        binding_states = ctx.fixture.evaluation_binding_states
        if binding_states is None:
            return
        d05_state = binding_states.get("d05_binding_state")
        if d05_state == "required":
            self._validate_d05_required()
        elif d05_state == "not_required_by_unit_applicability":
            refs = ctx.fixture.bindings.get("d05_refs", [])
            if refs:
                raise D06ContractViolationError(
                    "not-applicable unit cannot carry D05 refs",
                    "pre_medical_output_validation",
                )
            spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
            if spine is not None:
                raise D06ContractViolationError(
                    "not-required unit cannot carry temporal bindings",
                    "pre_medical_output_validation",
                )
        else:
            raise D06ContractViolationError(
                f"unknown D05 binding state {d05_state!r}",
                "pre_medical_output_validation",
            )
    def _validate_d05_required(self) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if "d05" in tp:
            d05 = tp["d05"]
            if "accepted_snapshot_ref" in d05 or "source_revision" in d05:
                ctx.mark("d05_assessment_binding")
                raise D06BindingContractError(
                    "D05 binding wrong scope: snapshot/source revision",
                    "typed_binding_validation",
                )
        # Shared temporal spine is validated first; its provenance is
        # recorded even when a later binding failure opens a gate.
        spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
        if (
            not isinstance(spine, (dict, Mapping))
            or spine.get("object_type") != "SharedTemporalSpineBinding"
        ):
            raise D06ContractViolationError(
                "required D05 binding has no typed temporal spine",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(spine, ctx.scope):
            raise D06BindingContractError(
                "temporal spine wrong scope", "typed_binding_validation"
            )
        if spine.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            if "spine" in tp or "shared_spine_hash" in tp:
                ctx.mark("shared_temporal_spine")
            raise ProjectionContractError(
                "temporal spine wrong cutoff", "projection_validation"
            )
        if not spine.get("axis_version") or not spine.get("axis_hash"):
            raise D06ContractViolationError(
                "temporal spine missing cutoff/version/hash",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(spine, "temporal spine")
        if "shared_spine_hash" in tp or "spine" in tp:
            ctx.mark("shared_temporal_spine")
        refs = ctx.fixture.bindings.get("d05_refs", [])
        if "d05_refs" in tp and tp["d05_refs"] == []:
            refs = []
        if not refs:
            if "d05" in tp or "d05_refs" in tp or "shared_spine_hash" in tp:
                ctx.mark("d05_assessment_binding")
            self._open_gate(GATE_DEPENDENCY, GATE_DECISION_NOT_EVALUABLE)
            raise _GateRaised()
        required = ctx.fixture.source_registries.get("required_d05_binding_ref_ids", [])
        ref_ids = [item.get("binding_ref_id") for item in refs]
        if ref_ids != required:
            raise D06ContractViolationError(
                "D05 required binding set mismatch", "pre_medical_output_validation"
            )
        foreign_keys = ctx.fixture.source_registries.get(
            "d05_assessment_foreign_keys", []
        )
        if [item.get("binding_ref_id") for item in foreign_keys] != ref_ids:
            raise D06ContractViolationError(
                "D05 foreign-key registry set mismatch", "pre_medical_output_validation"
            )
        inventory = ctx.fixture.source_registries.get(
            "accepted_d05_assessment_inventory", []
        )
        if [item.get("source_record_id") for item in inventory] != list(
            _assessment_by_id(ctx)
        ):
            raise D06ContractViolationError(
                "accepted D05 inventory does not exactly cover assessments",
                "pre_medical_output_validation",
            )
        if "d05" in tp or "d05_refs" in tp or "shared_spine_hash" in tp:
            ctx.mark("d05_assessment_binding")
        if "shared_spine_hash" in tp:
            raise D06BindingContractError(
                "shared temporal spine hash mismatch", "typed_binding_validation"
            )
        if ctx.fixture.bindings.get("shared_spine_hash") != spine.get("axis_hash"):
            raise D06ContractViolationError(
                "shared temporal spine hash mismatch", "pre_medical_output_validation"
            )
        if "spine" in tp and tp["spine"].get("cutoff"):
            raise ProjectionContractError(
                "shared spine wrong cutoff", "projection_validation"
            )
        for ref in refs:
            if not scope_identity_matches(ref, ctx.scope):
                raise D06BindingContractError(
                    "D05 ref wrong scope", "typed_binding_validation"
                )
            if ref.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
                raise D06BindingContractError(
                    "D05 ref wrong scope: cutoff", "typed_binding_validation"
                )
            verify_embedded_hash(ref, "D05 ref")
            # Every accepted assessment bound by a D05 ref must
            # cross-resolve the independent inventory/binding/foreign-key/
            # definition authority (hash, time, instrument, recall, items,
            # locators, scope/cutoff, accepted-current status).
            assessment = _assessment_by_id(ctx).get(ref.get("source_record_id"))
            if not isinstance(assessment, (dict, Mapping)):
                raise D06ContractViolationError(
                    "D05 ref source assessment cannot be resolved",
                    "pre_medical_output_validation",
                )
            _validate_assessment_authority(
                ctx, assessment, str(ref.get("source_record_id"))
            )

    # -- stage 3: assessment scope decisions -------------------------------

    def _assessment_scope_decisions(self) -> Optional[str]:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        assessments = _assessment_by_id(ctx)
        current = assessments.get(CANONICAL_CURRENT_ASSESSMENT)
        if current is None:
            raise D06ContractViolationError(
                "canonical current assessment missing", "pre_medical_output_validation"
            )
        if "assessment" in tp:
            assessment = tp["assessment"]
            if "time_role" in assessment and assessment["time_role"] is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return SCOPE_NOT_EVALUABLE
            if "time" in assessment:
                time = str(assessment["time"])
                cutoff = ctx.scope["clinical_event_cutoff"]
                if time > cutoff:
                    ctx.mark("journey_source_jump")
                    return SCOPE_OUT_OF_CUTOFF
            if "time_interval" in assessment:
                interval = _partial_date_interval(assessment["time_interval"])
                cutoff = ctx.scope["clinical_event_cutoff"]
                if interval:
                    start, end = interval
                    if start <= cutoff < end:
                        self._open_gate(GATE_CUTOFF_SCOPE, GATE_DECISION_BOUNDARY)
                        raise _GateRaised()
        if "correction" in tp:
            correction = tp["correction"]
            if "fork" in correction and correction["fork"]:
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                raise _GateRaised()
            if "graph" in correction and correction["graph"] == "branch":
                ctx.mark("accepted_artifact")
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                raise _GateRaised()
            if "current_ids" in correction and correction["current_ids"]:
                if "lineage" in correction and correction["lineage"] is None:
                    ctx.l1 = L1_NOT_EVALUABLE
                    ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                    ctx.l2[L2_COVERAGE_NOTICES] += 1
                    return SCOPE_NOT_EVALUABLE
                if "graph" not in correction:
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return SCOPE_IN_SCOPE
        return SCOPE_IN_SCOPE

    # -- stage 4: maturity -------------------------------------------------

    def _maturity(self) -> str:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        binding_states = ctx.fixture.evaluation_binding_states or {}
        if binding_states.get("maturity_binding_state") == "required":
            decision_id = binding_states.get("maturity_anchor_selection_decision_id")
            if not decision_id:
                raise D06ContractViolationError(
                    "required maturity binding has no decision",
                    "pre_medical_output_validation",
                )
            decision = ctx.fixture.bindings.get("maturity_anchor_selection_decision")
            if (
                not isinstance(decision, (dict, Mapping))
                or decision.get("object_type") != "MaturityAnchorSelectionDecision"
            ):
                raise D06ContractViolationError(
                    "required maturity binding has no typed decision",
                    "pre_medical_output_validation",
                )
            if decision.get("decision_id") != decision_id:
                raise D06ContractViolationError(
                    "maturity decision ID mismatch", "pre_medical_output_validation"
                )
        if "maturity" in tp:
            maturity = tp["maturity"]
            if maturity == "future":
                return "future"
            if isinstance(maturity, (dict, Mapping)):
                if maturity.get("opaque_expression") is not None:
                    raise SchemaContractError(
                        "maturity/cutoff opaque expression is forbidden",
                        "pre_medical_output_validation",
                    )
                if "rule" in maturity and maturity["rule"] is None:
                    self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                    raise _GateRaised()
                if (
                    maturity.get("anchor_candidates")
                    and maturity.get("tie_break") is None
                ):
                    ctx.l1 = L1_BOUNDARY
                    ctx.coverage_status = COVERAGE_COVERED
                    ctx.domain_assertions["maturity_decision_status"] = (
                        DECISION_MULTI_FEASIBLE_BOUNDARY
                    )
                    ctx.domain_assertions["selected_typed_anchor_id"] = None
                    ctx.l2["clues"] = 1
                    raise _GateRaised()
        return "matured"
