"""Manager remediation adversarial tests (2026-08-10).

Codex-required source-level gaps.  Tests are added first as counterexamples;
implementation must make them pass without touching frozen R1/R2/R3 trees.
"""

from __future__ import annotations

import copy
import dataclasses
import json
from typing import Any, Dict, Mapping

import pytest

from mm_r1.adapters import ImmutableAdapterBinding
from mm_r1.capability_runtime import (
    ApiCapabilityRuntime,
    CapabilityAttemptResult,
    CapabilityRequest,
    ExecutionProfile,
    InvocationVersions,
    TransportKind,
)
from mm_r1.domain import (
    CoverageManifest,
    CoverageUnit,
    CoverageUnitStatus,
    content_hash,
)
from mm_r3_rule_ai.parser import ParseStatus, parse_rule_candidate
from mm_r3_rule_ai.prompt import (
    SYSTEM_PROMPT_ZH,
    PromptPayload,
    build_prompt,
    prompt_payload_hash,
)
from mm_r3_rule_ai.schema import schema_content_hash
from mm_r3_rule_ai.workflow import (
    CAPABILITY_KIND,
    CAPABILITY_VERSION,
    CapabilityInput,
    ConversionGate,
    ConversionOutcome,
    ConversionProvenance,
    WorkflowError,
    build_capability_input,
    convert_attempt_to_draft,
    scope_recommendations,
    simulate_draft,
)
from fixtures_catalogs import synthetic_catalog


RULE_TEXT = "当不良事件的严重程度为重度时触发风险信号"
CAT = synthetic_catalog()
PROJECT_ID = "synthetic-project-1"
SOURCE_REV = "synthetic-revision-1"
SCOPE_KEY = "candidate-output"
EXPECTED_UNIT = (CoverageUnit(scope="rule_ai", key=SCOPE_KEY),)

FORBIDDEN_TERMS = (
    "合成记录",
    "当前快照",
    "全历史",
    "仅未来",
    "valid_from",
    "fingerprint",
    "content_hash",
    "input_hash",
    "adapter",
    "binding",
    "payload",
    "schema_hash",
)


def _candidate_text(**overrides: Any) -> str:
    obj: Dict[str, Any] = {
        "rule_name": "重度不良事件规则",
        "conditions": [
            {
                "field": "SYN_AE_SEV",
                "operator": "eq",
                "threshold": "重度",
                "extracted_from": "严重程度为重度",
            }
        ],
        "logical_combination": "all",
        "severity_hint": "serious",
        "domain_hint": "AE",
        "assumptions": [],
        "open_questions": [],
    }
    obj.update(overrides)
    return json.dumps(obj, ensure_ascii=False)


def _binding(**overrides: Any) -> ImmutableAdapterBinding:
    kw: Dict[str, Any] = dict(
        binding_id="binding-test",
        capability="rule_extract",
        provider="test-provider",
        model="test-model",
        selector="test-selector",
        effort="test-effort",
        adapter_version="test-adapter-1",
        allowed_tools=("read_synthetic_input",),
        isolation="fresh_context",
        endpoint="external",
    )
    kw.update(overrides)
    return ImmutableAdapterBinding(**kw)


def _api_profile(**overrides: Any) -> ExecutionProfile:
    kw: Dict[str, Any] = dict(
        profile_id="profile-test-1",
        transport=TransportKind.API,
        binding=_binding(),
        api_route="user-configured://synthetic-rule-extract",
        credential_ref="opaque-keychain-ref",
        runtime_revision="test-runtime-rev-1",
        timeout_seconds=10,
    )
    kw.update(overrides)
    return ExecutionProfile(**kw)


def _versions(**overrides: Any) -> InvocationVersions:
    kw = dict(
        source_revision_id=SOURCE_REV,
        rule_version="synthetic-rules-1",
        knowledge_version="synthetic-knowledge-1",
        graph_version="synthetic-graph-1",
        schema_version="synthetic-schema-1",
    )
    kw.update(overrides)
    return InvocationVersions(**kw)


class SyntheticTransport:
    def __init__(
        self,
        candidate_text: str,
        *,
        status: str = "complete",
        produced_status: str = "covered",
    ) -> None:
        self.candidate_text = candidate_text
        self.status = status
        self.produced_status = produced_status

    def __call__(self, request: Mapping[str, Any], profile: ExecutionProfile) -> Mapping[str, Any]:
        unit = dict(request["params"]["expected_coverage"][0])
        unit["status"] = self.produced_status
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "execution_id": "synthetic-execution-1",
            "result": {
                "status": self.status,
                "execution_identity": request["params"]["execution_identity"],
                "candidate_payload": self.candidate_text,
                "produced_units": [unit],
            },
        }


def _capability_input(
    *,
    rule_text: str = RULE_TEXT,
    project_id: str = PROJECT_ID,
    source_revision_id: str = SOURCE_REV,
    business_context: str = "",
) -> CapabilityInput:
    prompt = build_prompt(rule_text, CAT, business_context=business_context)
    return build_capability_input(
        prompt, catalog=CAT, project_id=project_id, source_revision_id=source_revision_id,
    )


def _invoke_runtime(
    transport: SyntheticTransport,
    *,
    cap_input: CapabilityInput | None = None,
    profile: ExecutionProfile | None = None,
    attempt_id: str = "attempt-001",
) -> CapabilityAttemptResult:
    if cap_input is None:
        cap_input = _capability_input()
    runtime = ApiCapabilityRuntime(
        profile or _api_profile(),
        transport,
        manifest_revision_reader=lambda run_id: 1,
    )
    return runtime.invoke(
        attempt_id=attempt_id,
        monitoring_run_id="monitoring-run-1",
        node_id="ai-rule-node",
        manifest_revision=1,
        versions=_versions(),
        payload=cap_input.to_payload(),
        expected_units=EXPECTED_UNIT,
    )


def _convert(
    result: CapabilityAttemptResult,
    *,
    cap_input: CapabilityInput | None = None,
) -> ConversionOutcome:
    if cap_input is None:
        cap_input = _capability_input()
    return convert_attempt_to_draft(
        result,
        capability_input=cap_input,
        catalog=CAT,
        draft_id="draft-1",
    )


def _ok_result(
    *,
    profile: ExecutionProfile | None = None,
    cap_input: CapabilityInput | None = None,
) -> tuple[CapabilityAttemptResult, CapabilityInput]:
    if cap_input is None:
        cap_input = _capability_input()
    result = _invoke_runtime(
        SyntheticTransport(_candidate_text()),
        cap_input=cap_input,
        profile=profile,
    )
    return result, cap_input


# ===========================================================================
# 1. Recompute R1 frozen request identity
# ===========================================================================

class TestRequestIdentityRecompute:
    def test_honest_result_passes_recompute(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        assert outcome.ok

    def test_payload_mutation_preserving_copied_hashes_blocks(self):
        """Mutate payload while keeping request/run/analysis input_hash copies."""
        result, cap = _ok_result()
        # Tamper payload but keep capability_input aligned so payload gate alone
        # is not the only defense; then freeze stale hashes on request/run/analysis.
        tampered_payload = cap.to_payload()
        tampered_payload["rule_text"] = RULE_TEXT + "【额外说明】"
        # Rebuild a capability input that matches the tampered payload's outer
        # contract would fail prompt rebuild; instead keep original cap_input
        # and only forge the result's request payload + preserved hashes.
        forged_request = dataclasses.replace(
            result.request,
            payload=tampered_payload,
            # keep input_hash / binding / versions as-is (forged agreement)
        )
        forged = dataclasses.replace(result, request=forged_request)
        outcome = _convert(forged, cap_input=cap)
        # Either payload mismatch (cap vs request) or identity recompute.
        assert outcome.blocked
        assert outcome.gate in (
            ConversionGate.R1_REQUEST_PAYLOAD_MISMATCH,
            ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH,
            ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH,
        )

    def test_versions_mutation_preserving_copied_hashes_blocks(self):
        result, cap = _ok_result()
        stale_versions = _versions(rule_version="forged-rules-999")
        forged_request = dataclasses.replace(result.request, versions=stale_versions)
        # Keep run/analysis/request input_hash copies identical (already are).
        forged = dataclasses.replace(result, request=forged_request)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH

    def test_expected_units_mutation_preserving_copied_hashes_blocks(self):
        result, cap = _ok_result()
        other_unit = (CoverageUnit(scope="rule_ai", key="forged-extra-unit"),)
        forged_request = dataclasses.replace(result.request, expected_units=other_unit)
        forged = dataclasses.replace(result, request=forged_request)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH

    def test_profile_fingerprint_field_mutation_preserving_hashes_blocks(self):
        result, cap = _ok_result()
        # Forge request.profile_fingerprint while keeping copied input hashes.
        forged_request = dataclasses.replace(
            result.request,
            profile_fingerprint="b" * 64,
        )
        forged = dataclasses.replace(result, request=forged_request)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate in (
            ConversionGate.R1_PROFILE_FINGERPRINT_MISMATCH,
            ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH,
        )


# ===========================================================================
# 2. Profile / request / run stable binding identity + empty selector
# ===========================================================================

class TestProfileBindingAndEmptySelector:
    def test_empty_selector_e2e_succeeds(self):
        profile = _api_profile(binding=_binding(selector=""))
        result, cap = _ok_result(profile=profile)
        outcome = _convert(result, cap_input=cap)
        assert outcome.ok
        assert outcome.provenance.selector == ""

    def test_profile_provider_drift_blocks(self):
        result, cap = _ok_result()
        drifted = dataclasses.replace(
            result.profile.binding,
            provider="forged-provider",
        )
        forged_profile = dataclasses.replace(result.profile, binding=drifted)
        forged = dataclasses.replace(result, profile=forged_profile)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate in (
            ConversionGate.R1_PROFILE_BINDING_MISMATCH,
            ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH,
            ConversionGate.R1_PROFILE_FINGERPRINT_MISMATCH,
        )

    def test_provenance_allows_empty_selector(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        prov = outcome.provenance.to_public_dict()
        prov["selector"] = ""
        # profile_fingerprint must remain 64-hex
        rebuilt = ConversionProvenance(**prov)
        assert rebuilt.selector == ""


# ===========================================================================
# 3. Exact candidate artifact linkage
# ===========================================================================

class TestExactCandidateArtifactLinkage:
    def test_forged_extra_evidence_ref_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        assert art is not None
        forged_art = copy.copy(art)
        forged_art.evidence_refs = list(art.evidence_refs) + ["extra-ref-forged"]
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("evidence_refs_exact" in r for r in outcome.reasons)

    def test_forged_extra_input_hash_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        forged_art.input_hashes = list(art.input_hashes) + ["c" * 64]
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("input_hashes_exact" in r for r in outcome.reasons)

    def test_substituted_coverage_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        # Independently fully-covered but different from adapter_run.coverage.
        other = CoverageManifest(
            expected=[
                CoverageUnit(
                    scope="rule_ai",
                    key="other-unit",
                    expected=True,
                    status=CoverageUnitStatus.COVERED,
                )
            ],
            produced=[
                CoverageUnit(
                    scope="rule_ai",
                    key="other-unit",
                    expected=True,
                    status=CoverageUnitStatus.COVERED,
                )
            ],
            reconciled=True,
        )
        ok, _ = other.is_fully_covered()
        assert ok
        forged_art = copy.copy(art)
        forged_art.coverage = other
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("coverage_does_not_match" in r for r in outcome.reasons)

    def test_forged_commit_id_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        forged_art.artifact_id = "d" * 64  # plausible hex, wrong vs canonical
        forged_art.content_hash = "d" * 64
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("artifact_id_mismatch" in r for r in outcome.reasons)

    @pytest.mark.parametrize("present_field", ["artifact_id", "content_hash"])
    def test_half_committed_artifact_identity_blocks(self, present_field):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        setattr(forged_art, present_field, art.canonical_hash())
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("requires_id_and_hash_together" in r for r in outcome.reasons)

    def test_extra_candidate_payload_key_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        forged_art.payload = copy.deepcopy(art.payload)
        forged_art.payload["unexpected_internal_flag"] = True
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("payload_keys_exact" in r for r in outcome.reasons)

    def test_candidate_authority_true_blocks(self):
        result, cap = _ok_result()
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        forged_art.payload = copy.deepcopy(art.payload)
        forged_art.payload["authority"]["may_publish"] = True
        forged_run = dataclasses.replace(
            result.adapter_run, candidate_artifact=forged_art,
        )
        forged = dataclasses.replace(result, adapter_run=forged_run)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY
        assert any("authority_must_be_exactly_all_false" in r for r in outcome.reasons)


class TestRawResponseEnvelopeBinding:
    def _forge_raw(self, mutator):
        result, cap = _ok_result()
        raw = result.adapter_run.raw_output
        raw_obj = json.loads(raw.raw_output_json)
        mutator(raw_obj)
        raw_json = json.dumps(
            raw_obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        raw_hash = content_hash({"raw_output": raw_obj})
        raw_ref = f"raw-output:{raw.run_id}:{raw_hash}"
        forged_raw = dataclasses.replace(
            raw,
            raw_output_json=raw_json,
            content_hash=raw_hash,
            raw_output_ref=raw_ref,
        )
        art = result.adapter_run.candidate_artifact
        forged_art = copy.copy(art)
        forged_art.payload = copy.deepcopy(art.payload)
        forged_art.payload["raw_output_ref"] = raw_ref
        forged_art.evidence_refs = [raw_ref]
        forged_run = dataclasses.replace(
            result.adapter_run,
            raw_output=forged_raw,
            candidate_artifact=forged_art,
        )
        return dataclasses.replace(result, adapter_run=forged_run), cap

    def test_raw_attempt_id_mismatch_blocks(self):
        forged, cap = self._forge_raw(lambda raw: raw.__setitem__("id", "other-attempt"))
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_RAW_PROVENANCE_MISMATCH
        assert "raw_response_attempt_id_mismatch" in outcome.reasons

    def test_raw_execution_identity_mismatch_blocks(self):
        def mutate(raw):
            raw["result"]["execution_identity"]["provider"] = "other-provider"

        forged, cap = self._forge_raw(mutate)
        outcome = _convert(forged, cap_input=cap)
        assert outcome.gate == ConversionGate.R1_RAW_PROVENANCE_MISMATCH
        assert "raw_response_execution_identity_mismatch" in outcome.reasons


# ===========================================================================
# 4. Prompt / capability identity
# ===========================================================================

class TestPromptCapabilityIdentity:
    def test_semantically_equal_noncanonical_payload_rejected(self):
        cap = _capability_input()
        noncanonical = json.dumps(cap.to_payload(), ensure_ascii=False)
        assert noncanonical != cap._payload_canon
        with pytest.raises(WorkflowError, match="canonical JSON serialization"):
            CapabilityInput(
                _payload_canon=noncanonical,
                catalog_fingerprint=cap.catalog_fingerprint,
                schema_hash=cap.schema_hash,
                prompt_payload_hash=cap.prompt_payload_hash,
            )

    def test_capability_version_must_equal_constant(self):
        prompt = build_prompt(RULE_TEXT, CAT)
        payload = {
            "capability_kind": CAPABILITY_KIND,
            "capability_version": "999",  # non-empty but wrong
            "project_id": PROJECT_ID,
            "source_revision_id": SOURCE_REV,
            "rule_text": RULE_TEXT,
            "schema_hash": prompt.schema_hash,
            "catalog_fingerprint": CAT.fingerprint,
            "prompt_payload_hash": prompt_payload_hash(prompt),
            "prompt_payload": prompt.to_public_dict(),
        }
        with pytest.raises(WorkflowError, match="capability_version"):
            CapabilityInput(
                _payload_canon=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                catalog_fingerprint=CAT.fingerprint,
                schema_hash=prompt.schema_hash,
                prompt_payload_hash=prompt_payload_hash(prompt),
            )

    def test_tampered_system_prompt_with_matching_hash_rejected_at_build(self):
        prompt = build_prompt(RULE_TEXT, CAT)
        tampered = PromptPayload(
            system_prompt=SYSTEM_PROMPT_ZH + "\n【篡改】",
            user_prompt=prompt.user_prompt,
            schema_hash=prompt.schema_hash,
            catalog_fingerprint=prompt.catalog_fingerprint,
            rule_text=prompt.rule_text,
            business_context=prompt.business_context,
            schema_json=prompt.schema_json,
        )
        with pytest.raises(WorkflowError, match="rebuild|system_prompt|public payload"):
            build_capability_input(
                tampered, catalog=CAT, project_id=PROJECT_ID, source_revision_id=SOURCE_REV,
            )

    def test_direct_construction_tampered_system_prompt_rejected(self):
        prompt = build_prompt(RULE_TEXT, CAT)
        pp = prompt.to_public_dict()
        pp["system_prompt"] = SYSTEM_PROMPT_ZH + "TAMPER"
        # Recompute hash so hash self-consistency alone would pass.
        from mm_r3_rule_ai.workflow import prompt_payload_hash_dict
        pp_hash = prompt_payload_hash_dict(pp)
        payload = {
            "capability_kind": CAPABILITY_KIND,
            "capability_version": CAPABILITY_VERSION,
            "project_id": PROJECT_ID,
            "source_revision_id": SOURCE_REV,
            "rule_text": RULE_TEXT,
            "schema_hash": schema_content_hash(),
            "catalog_fingerprint": CAT.fingerprint,
            "prompt_payload_hash": pp_hash,
            "prompt_payload": pp,
        }
        with pytest.raises(WorkflowError, match="system_prompt"):
            CapabilityInput(
                _payload_canon=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                catalog_fingerprint=CAT.fingerprint,
                schema_hash=schema_content_hash(),
                prompt_payload_hash=pp_hash,
            )

    def test_conversion_rebuilds_prompt_and_blocks_embedded_drift(self):
        result, cap = _ok_result()
        # Forge request payload prompt_payload with tampered user_prompt but
        # keep outer hashes looking consistent with a rebuilt hash.
        payload = cap.to_payload()
        pp = dict(payload["prompt_payload"])
        pp["user_prompt"] = pp["user_prompt"] + "\n【篡改】"
        from mm_r3_rule_ai.workflow import prompt_payload_hash_dict
        pp_hash = prompt_payload_hash_dict(pp)
        payload["prompt_payload"] = pp
        payload["prompt_payload_hash"] = pp_hash
        # CapabilityInput construction itself should reject (system ok but
        # wait - user_prompt drift: __post_init__ only checks system/schema
        # constants and recomputed hash of embedded pp).  So direct
        # CapabilityInput with matching hash over tampered user_prompt may
        # construct if system/schema match — conversion rebuild must block.
        try:
            forged_cap = CapabilityInput(
                _payload_canon=json.dumps(
                    payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ),
                catalog_fingerprint=CAT.fingerprint,
                schema_hash=schema_content_hash(),
                prompt_payload_hash=pp_hash,
            )
        except WorkflowError:
            # Construction already blocked — also acceptable.
            return
        # Recompute would fail because input_hash is stale relative to payload.
        # Force input_hash agreement by also rebuilding request properly... but
        # then conversion rebuild gate is what we want.  Rebuild request fully:
        honest = CapabilityRequest.build(
            attempt_id=result.request.attempt_id,
            monitoring_run_id=result.request.monitoring_run_id,
            node_id=result.request.node_id,
            manifest_revision=result.request.manifest_revision,
            profile=result.profile,
            versions=result.request.versions,
            payload=forged_cap.to_payload(),
            expected_units=result.request.expected_units,
            continued_from=result.request.continued_from,
        )
        # Rebuild run binding/analysis hashes to match new input_hash so earlier
        # gates pass and prompt rebuild is reached.
        new_binding = result.adapter_run.binding.with_input_hash(honest.input_hash)
        new_analysis = dataclasses.replace(
            result.adapter_run.analysis, input_hash=honest.input_hash,
        )
        raw = result.adapter_run.raw_output
        new_raw = dataclasses.replace(raw, input_hash=honest.input_hash) if raw else None
        art = result.adapter_run.candidate_artifact
        new_art = copy.copy(art)
        new_art.input_hashes = [honest.input_hash]
        forged_run = dataclasses.replace(
            result.adapter_run,
            binding=new_binding,
            analysis=new_analysis,
            raw_output=new_raw,
            candidate_artifact=new_art,
        )
        forged = dataclasses.replace(result, request=honest, adapter_run=forged_run)
        outcome = convert_attempt_to_draft(
            forged, capability_input=forged_cap, catalog=CAT, draft_id="draft-1",
        )
        assert outcome.gate == ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH


# ===========================================================================
# 5. ConversionOutcome / ConversionProvenance construction
# ===========================================================================

class TestOutcomeConstructionTightening:
    def test_unknown_gate_rejected(self):
        with pytest.raises(WorkflowError, match="unknown conversion gate"):
            ConversionOutcome(gate="not_a_real_gate", reasons=("x",))

    def test_blocked_without_reasons_rejected(self):
        with pytest.raises(WorkflowError, match="requires reasons"):
            ConversionOutcome(gate=ConversionGate.PARSE_BLOCKED)

    def test_reasons_frozen_as_tuple(self):
        outcome = ConversionOutcome(
            gate=ConversionGate.PARSE_BLOCKED,
            reasons=["a", "b"],  # type: ignore[arg-type]
        )
        assert isinstance(outcome.reasons, tuple)
        assert outcome.reasons == ("a", "b")

    @pytest.mark.parametrize("bad_reasons", ["single reason", b"bytes"])
    def test_scalar_reason_text_rejected(self, bad_reasons):
        with pytest.raises(WorkflowError, match="sequence of strings"):
            ConversionOutcome(
                gate=ConversionGate.PARSE_BLOCKED,
                reasons=bad_reasons,  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize("bad_reasons", [("",), (1,)])
    def test_reasons_require_nonempty_strings(self, bad_reasons):
        with pytest.raises(WorkflowError, match="non-empty strings"):
            ConversionOutcome(
                gate=ConversionGate.PARSE_BLOCKED,
                reasons=bad_reasons,  # type: ignore[arg-type]
            )

    def test_provenance_profile_fingerprint_must_be_hex64(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        prov = outcome.provenance.to_public_dict()
        prov["profile_fingerprint"] = "not-hex"
        with pytest.raises(WorkflowError, match="profile_fingerprint"):
            ConversionProvenance(**prov)


# ===========================================================================
# 6. BOOL_AS_INT classification
# ===========================================================================

class TestBoolAsIntStatus:
    def test_bool_threshold_returns_bool_as_int(self):
        raw = json.dumps({
            "rule_name": "布尔规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "eq", "threshold": True,
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.BOOL_AS_INT

    def test_ordinary_type_mismatch_distinct(self):
        raw = json.dumps({
            "rule_name": "类型规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "eq", "threshold": "不是数字",
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.THRESHOLD_TYPE_MISMATCH

    def test_bool_inside_number_list_returns_bool_as_int(self):
        raw = json.dumps({
            "rule_name": "数值列表布尔规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "in", "threshold": [1, True],
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.BOOL_AS_INT

    def test_non_finite_distinct(self):
        raw = json.dumps({
            "rule_name": "无穷规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "gt", "threshold": 1e999,
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.NON_FINITE_NUMBER


# ===========================================================================
# 7. User-facing Chinese vocabulary
# ===========================================================================

class TestUserFacingScopeChinese:
    def test_native_titles(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        sim = simulate_draft(outcome.draft, [{"SYN_AE_SEV": "重度"}, {"SYN_AE_SEV": "轻度"}])
        recs = scope_recommendations(outcome.draft, sim)
        assert [r.title_zh for r in recs] == ["本次数据", "全部历史数据", "仅后续数据"]

    def test_impact_wording(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        sim = simulate_draft(outcome.draft, [{"SYN_AE_SEV": "重度"}, {"SYN_AE_SEV": "轻度"}])
        recs = scope_recommendations(outcome.draft, sim)
        assert "按本次数据试算：共 2 条记录，符合条件 1 条" in recs[0].impact_summary_zh
        assert recs[0].reason_zh == "只检查本次导入的数据，适合先确认规则是否符合预期。"
        assert recs[1].reason_zh == "重新检查项目既往全部数据，适合新增规则也可能命中早期数据时使用。"
        assert "需重新检查项目既往全部数据" in recs[1].impact_summary_zh
        assert recs[2].reason_zh == "从生效日期起检查后续数据，不回查此前数据。"
        assert "后续数据尚未产生" in recs[2].impact_summary_zh

    def test_valid_from_wording(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        sim = simulate_draft(outcome.draft, [])
        missing = scope_recommendations(outcome.draft, sim, valid_from="")
        present = scope_recommendations(outcome.draft, sim, valid_from="2026-01-01")
        assert "请先选择生效日期" in missing[2].impact_summary_zh
        assert "自 2026-01-01 起生效" in present[2].impact_summary_zh

    def test_forbidden_terminology_over_all_fields(self):
        result, cap = _ok_result()
        outcome = _convert(result, cap_input=cap)
        sim = simulate_draft(outcome.draft, [{"SYN_AE_SEV": "重度"}])
        for valid_from in ("", "2026-01-01"):
            recs = scope_recommendations(outcome.draft, sim, valid_from=valid_from)
            for rec in recs:
                for field in (rec.title_zh, rec.reason_zh, rec.impact_summary_zh):
                    for term in FORBIDDEN_TERMS:
                        assert term not in field, f"forbidden {term!r} in {field!r}"
