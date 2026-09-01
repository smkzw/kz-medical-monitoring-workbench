"""Worker_02 workflow bridge tests (follow-up 01): real R1
CapabilityAttemptResult consumption, frozen identity verification, exact
candidate-text parsing, durable provenance, bound scope recommendations, and
explicit user-confirmed activation.

All fixtures are synthetic.  No real model/API/harness is called; port 8911
stays stopped.  Frozen R1/R3 are on sys.path read-only.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping

import pytest

from mm_r1.adapters import ImmutableAdapterBinding
from mm_r1.capability_runtime import (
    ApiCapabilityRuntime,
    CapabilityAttemptResult,
    ExecutionProfile,
    InvocationVersions,
    TransportKind,
)
from mm_r1.domain import CoverageUnit
from mm_r3.rules import (
    EvaluationScope,
    EvaluationScopeKind,
    RuleActivationError,
)
from mm_r3_rule_ai.parser import ParseStatus, parse_rule_candidate
from mm_r3_rule_ai.prompt import build_prompt
from mm_r3_rule_ai.workflow import (
    CAPABILITY_KIND,
    CAPABILITY_VERSION,
    ConversionGate,
    ConversionOutcome,
    ConversionProvenance,
    CapabilityInput,
    activate_draft,
    build_capability_input,
    convert_attempt_to_draft,
    extract_candidate_text,
    normalize_rule_text,
    scope_recommendations,
    simulate_draft,
    verify_extracted_from,
    WorkflowError,
)
from fixtures_catalogs import synthetic_catalog


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

RULE_TEXT = "当不良事件的严重程度为重度时触发风险信号"
CAT = synthetic_catalog()
PROJECT_ID = "synthetic-project-1"
SOURCE_REV = "synthetic-revision-1"
SCOPE_KEY = "candidate-output"
EXPECTED_UNIT = (CoverageUnit(scope="rule_ai", key=SCOPE_KEY),)


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


# ---------------------------------------------------------------------------
# R1 API profile + transport helpers
# ---------------------------------------------------------------------------

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


def _versions() -> InvocationVersions:
    return InvocationVersions(
        source_revision_id=SOURCE_REV,
        rule_version="synthetic-rules-1",
        knowledge_version="synthetic-knowledge-1",
        graph_version="synthetic-graph-1",
        schema_version="synthetic-schema-1",
    )


class SyntheticTransport:
    """Deterministic API transport for tests only.

    Returns a JSON-RPC response with a **string** candidate_payload (the
    model's exact output text) and fully-covered produced units.
    """

    def __init__(
        self,
        candidate_text: str,
        *,
        status: str = "complete",
        produced_status: str = "covered",
        candidate_is_mapping: bool = False,
    ) -> None:
        self.candidate_text = candidate_text
        self.status = status
        self.produced_status = produced_status
        self.candidate_is_mapping = candidate_is_mapping
        self.calls: list = []

    def __call__(self, request: Mapping[str, Any], profile: ExecutionProfile) -> Mapping[str, Any]:
        self.calls.append((request, profile))
        unit = dict(request["params"]["expected_coverage"][0])
        unit["status"] = self.produced_status
        cp: Any = json.loads(self.candidate_text) if self.candidate_is_mapping else self.candidate_text
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "execution_id": "synthetic-execution-1",
            "result": {
                "status": self.status,
                "execution_identity": request["params"]["execution_identity"],
                "candidate_payload": cp,
                "produced_units": [unit],
            },
        }


def _capability_input(
    *,
    rule_text: str = RULE_TEXT,
    project_id: str = PROJECT_ID,
    source_revision_id: str = SOURCE_REV,
) -> CapabilityInput:
    prompt = build_prompt(rule_text, CAT)
    return build_capability_input(
        prompt, catalog=CAT, project_id=project_id, source_revision_id=source_revision_id,
    )


def _invoke_runtime(
    transport: SyntheticTransport,
    *,
    cap_input: CapabilityInput | None = None,
    profile: ExecutionProfile | None = None,
    attempt_id: str = "attempt-001",
    expected_units=EXPECTED_UNIT,
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
        expected_units=expected_units,
    )


def _convert(
    result: CapabilityAttemptResult,
    *,
    cap_input: CapabilityInput | None = None,
    catalog=CAT,
    draft_id: str = "draft-1",
) -> ConversionOutcome:
    if cap_input is None:
        cap_input = _capability_input()
    return convert_attempt_to_draft(
        result,
        capability_input=cap_input,
        catalog=catalog,
        draft_id=draft_id,
    )


# ===========================================================================
# Item 1: Consume the real R1 CapabilityAttemptResult
# ===========================================================================

class TestRealCapabilityAttemptResult:
    def test_e2e_positive_via_api_runtime(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        assert isinstance(result, CapabilityAttemptResult)
        outcome = _convert(result)
        assert outcome.ok
        assert outcome.draft.rule_name == "重度不良事件规则"
        assert outcome.draft.natural_language == RULE_TEXT

    def test_rejects_bare_adapter_run(self):
        """A bare AdapterRun (not a CapabilityAttemptResult) must be rejected."""
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        bare_run = result.adapter_run  # not the full CapabilityAttemptResult
        outcome = _convert(bare_run)
        assert outcome.gate == ConversionGate.R1_NOT_CAPABILITY_ATTEMPT_RESULT

    def test_rejects_arbitrary_object(self):
        outcome = _convert({"not": "a result"})  # type: ignore[arg-type]
        assert outcome.gate == ConversionGate.R1_NOT_CAPABILITY_ATTEMPT_RESULT


# ===========================================================================
# Item 2: Preserve and parse the model's exact candidate text
# ===========================================================================

class TestExactCandidateText:
    def test_string_candidate_accepted(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        text = extract_candidate_text(result)
        assert text == _candidate_text()

    def test_mapping_candidate_rejected_by_extract(self):
        transport = SyntheticTransport(_candidate_text(), candidate_is_mapping=True)
        result = _invoke_runtime(transport)
        with pytest.raises(WorkflowError, match="must be a string"):
            extract_candidate_text(result)

    def test_mapping_candidate_blocks_conversion(self):
        transport = SyntheticTransport(_candidate_text(), candidate_is_mapping=True)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.R1_CANDIDATE_NOT_STRING

    def test_candidate_matches_sealed_raw_evidence(self):
        """The exact candidate string is present in immutable raw_output_json."""
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        text = extract_candidate_text(result)
        raw_json = result.adapter_run.raw_output.raw_output_json
        raw_obj = json.loads(raw_json)
        assert raw_obj["result"]["candidate_payload"] == text

    def test_markdown_fence_blocks_through_real_bridge(self):
        """A model that wraps output in a markdown fence is rejected by the parser."""
        fenced = "```json\n" + _candidate_text() + "\n```"
        transport = SyntheticTransport(fenced)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.PARSE_BLOCKED
        assert outcome.parse_result.status == ParseStatus.MARKDOWN_FENCE

    def test_prose_wrapped_blocks_through_real_bridge(self):
        prose = "结果是：" + _candidate_text() + " 请确认"
        transport = SyntheticTransport(prose)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.PARSE_BLOCKED

    def test_multiple_json_blocks_through_real_bridge(self):
        multi = _candidate_text() + "\n" + _candidate_text()
        transport = SyntheticTransport(multi)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.PARSE_BLOCKED
        assert outcome.parse_result.status == ParseStatus.MULTIPLE_JSON_VALUES

    def test_duplicate_keys_block_through_real_bridge(self):
        dup = '{"rule_name":"A","rule_name":"B","conditions":[],"logical_combination":"all","severity_hint":"","domain_hint":"","assumptions":[],"open_questions":[]}'
        transport = SyntheticTransport(dup)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.PARSE_BLOCKED
        assert outcome.parse_result.status == ParseStatus.DUPLICATE_KEY


# ===========================================================================
# Item 3: Freeze request identity
# ===========================================================================

class TestFrozenIdentity:
    def test_capability_input_is_deterministic(self):
        ci1 = _capability_input()
        ci2 = _capability_input()
        assert ci1.to_payload() == ci2.to_payload()
        assert ci1.prompt_payload_hash == ci2.prompt_payload_hash

    def test_capability_input_includes_all_fields(self):
        ci = _capability_input()
        p = ci.to_payload()
        assert p["capability_kind"] == CAPABILITY_KIND
        assert p["capability_version"] == CAPABILITY_VERSION
        assert p["rule_text"] == RULE_TEXT
        assert p["schema_hash"]
        assert p["catalog_fingerprint"] == CAT.fingerprint
        assert p["prompt_payload_hash"]
        assert "prompt_payload" in p
        assert p["project_id"] == PROJECT_ID
        assert p["source_revision_id"] == SOURCE_REV

    def test_different_catalog_different_prompt_hash(self):
        from mm_r3_rule_ai.catalog import FieldCatalog, FieldSpec, ValueType
        other_cat = FieldCatalog((
            FieldSpec("OTHER_FIELD", "AE", "其他", "其他字段", ValueType.STRING, ("eq",)),
        ))
        prompt = build_prompt("其他规则", other_cat)
        ci = build_capability_input(
            prompt, catalog=other_cat, project_id=PROJECT_ID, source_revision_id=SOURCE_REV,
        )
        ci_default = _capability_input()
        assert ci.prompt_payload_hash != ci_default.prompt_payload_hash

    def test_prompt_catalog_mismatch_rejected(self):
        from mm_r3_rule_ai.catalog import FieldCatalog, FieldSpec, ValueType
        other_cat = FieldCatalog((
            FieldSpec("OTHER_FIELD", "AE", "其他", "其他字段", ValueType.STRING, ("eq",)),
        ))
        prompt = build_prompt(RULE_TEXT, CAT)
        with pytest.raises(WorkflowError, match="catalog_fingerprint"):
            build_capability_input(
                prompt, catalog=other_cat,  # mismatched
                project_id=PROJECT_ID, source_revision_id=SOURCE_REV,
            )

    def test_request_payload_mismatch_blocks(self):
        """A result sealed against one capability input must not convert with a
        capability input carrying a different payload."""
        cap_a = _capability_input(rule_text="当不良事件的结局为死亡时触发风险")
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport, cap_input=cap_a)
        outcome = _convert(result)  # default cap_input != cap_a
        assert outcome.gate == ConversionGate.R1_REQUEST_PAYLOAD_MISMATCH

    def test_source_revision_mismatch_blocks(self):
        """A different source revision in the capability input must block."""
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        bad_cap = _capability_input(source_revision_id="different-revision")
        outcome = _convert(result, cap_input=bad_cap)
        assert outcome.gate == ConversionGate.R1_REQUEST_PAYLOAD_MISMATCH


# ===========================================================================
# Item 4: Durable conversion provenance
# ===========================================================================

class TestDurableProvenance:
    def test_provenance_present_on_success(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.ok
        prov = outcome.provenance
        assert prov is not None
        assert isinstance(prov, ConversionProvenance)
        assert prov.attempt_id == "attempt-001"
        assert prov.monitoring_run_id == "monitoring-run-1"
        assert prov.node_id == "ai-rule-node"
        assert prov.binding_id == "binding-test"
        assert prov.provider == "test-provider"
        assert prov.model == "test-model"
        assert prov.selector == "test-selector"
        assert prov.adapter_version == "test-adapter-1"
        assert prov.input_hash
        assert prov.raw_output_ref
        assert prov.catalog_fingerprint == CAT.fingerprint
        assert prov.schema_hash
        assert prov.prompt_payload_hash
        assert prov.candidate_content_hash

    def test_provenance_is_frozen(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        with pytest.raises(Exception):
            outcome.provenance.attempt_id = "tampered"  # type: ignore[misc]

    def test_provenance_no_secret_values(self):
        transport = SyntheticTransport(_candidate_text())
        profile = _api_profile(credential_ref="SECRET_KEY_VALUE")
        result = _invoke_runtime(transport, profile=profile)
        outcome = _convert(result)
        prov_json = json.dumps(outcome.provenance.to_public_dict(), ensure_ascii=False)
        assert "SECRET_KEY_VALUE" not in prov_json

    def test_provenance_content_hash_matches_candidate(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        from mm_r3_rule_ai.parser import candidate_content_hash
        raw = _candidate_text()
        pr = parse_rule_candidate(raw, CAT)
        assert outcome.provenance.candidate_content_hash == candidate_content_hash(pr.candidate)


# ===========================================================================
# Item 5: No production schema bias (tested in test_w01_contract.py too)
# ===========================================================================

class TestNoSchemaBias:
    def test_convert_requires_field_catalog(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        with pytest.raises(WorkflowError):
            convert_attempt_to_draft(
                result,
                capability_input=_capability_input(),
                catalog="not-a-catalog",  # type: ignore[arg-type]
            )


# ===========================================================================
# Item 6: Bind recommendations to the simulated draft
# ===========================================================================

class TestScopeRecommendationsBound:
    def test_three_recommendations_fixed_order(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [{"_record_id": "r1", "SYN_AE_SEV": "重度"}])
        recs = scope_recommendations(outcome.draft, sim)
        assert len(recs) == 3
        assert tuple(r.scope_kind for r in recs) == ("current_snapshot", "full_history", "future_only")

    def test_stale_simulation_rejected(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        # Simulate a different draft
        other_draft_text = _candidate_text(rule_name="不同的规则")
        transport2 = SyntheticTransport(other_draft_text)
        result2 = _invoke_runtime(transport2, attempt_id="attempt-002")
        outcome2 = _convert(result2)
        sim_for_other = simulate_draft(outcome2.draft, [])
        with pytest.raises(WorkflowError, match="content_hash"):
            scope_recommendations(outcome.draft, sim_for_other)

    def test_project_mismatch_rejected(self):
        """A simulation for a different project must be rejected."""
        cap_a = _capability_input(project_id="project-A")
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport, cap_input=cap_a)
        outcome = _convert(result, cap_input=cap_a)
        # Convert the same candidate under a different project_id
        cap_b = _capability_input(project_id="project-B")
        transport2 = SyntheticTransport(_candidate_text())
        result2 = _invoke_runtime(transport2, cap_input=cap_b, attempt_id="attempt-003")
        outcome2 = _convert(result2, cap_input=cap_b)
        sim_for_b = simulate_draft(outcome2.draft, [])
        with pytest.raises(WorkflowError, match="project_id"):
            scope_recommendations(outcome.draft, sim_for_b)

    def test_full_history_impact_caveat(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [{"_record_id": "r1", "SYN_AE_SEV": "重度"}])
        recs = scope_recommendations(outcome.draft, sim)
        full_rec = [r for r in recs if r.scope_kind == "full_history"][0]
        assert "既往全部数据" in full_rec.impact_summary_zh
        assert "才能确认实际符合条件的数量" in full_rec.impact_summary_zh

    def test_future_only_valid_from_required_when_missing(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [])
        recs = scope_recommendations(outcome.draft, sim, valid_from="")
        future_rec = [r for r in recs if r.scope_kind == "future_only"][0]
        assert "请先选择生效日期" in future_rec.impact_summary_zh
        assert "后续数据" in future_rec.impact_summary_zh

    def test_future_only_with_valid_from(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [])
        recs = scope_recommendations(outcome.draft, sim, valid_from="2026-01-01")
        future_rec = [r for r in recs if r.scope_kind == "future_only"][0]
        assert "2026-01-01" in future_rec.impact_summary_zh


# ===========================================================================
# Distinct terminal-state reasons (retained from prior pass)
# ===========================================================================

class TestDistinctTerminalReasons:
    def test_partial_blocks(self):
        transport = SyntheticTransport(_candidate_text(), produced_status="partial")
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.R1_STATUS_NOT_COMPLETE
        assert "partial" in outcome.reasons[0]

    def test_truncated_blocks(self):
        transport = SyntheticTransport(_candidate_text(), produced_status="truncated")
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.R1_STATUS_NOT_COMPLETE
        assert "truncated" in outcome.reasons[0]

    def test_failed_blocks(self):
        transport = SyntheticTransport(_candidate_text(), produced_status="failed")
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.R1_STATUS_NOT_COMPLETE
        assert "failed" in outcome.reasons[0]

    def test_transport_timeout_blocks(self):
        class TimeoutTransport:
            def __call__(self, request, profile):
                import time
                time.sleep(100)
        runtime = ApiCapabilityRuntime(
            _api_profile(timeout_seconds=1),
            TimeoutTransport(),
            manifest_revision_reader=lambda run_id: 1,
        )
        result = runtime.invoke(
            attempt_id="att-timeout", monitoring_run_id="run-1", node_id="node-1",
            manifest_revision=1, versions=_versions(),
            payload=_capability_input().to_payload(), expected_units=EXPECTED_UNIT,
        )
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.R1_STATUS_NOT_COMPLETE
        assert "timeout" in outcome.reasons[0]


# ===========================================================================
# Assumptions block + extracted_from provenance (retained)
# ===========================================================================

class TestAssumptionsAndExtractedFrom:
    def test_nonempty_assumptions_block(self):
        text = _candidate_text(assumptions=["假设受试者已签署知情同意"])
        transport = SyntheticTransport(text)
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.ASSUMPTIONS_PRESENT

    def test_absent_extracted_from_blocks(self):
        text = _candidate_text()
        obj = json.loads(text)
        obj["conditions"][0]["extracted_from"] = "这条短语原文里没有"
        transport = SyntheticTransport(json.dumps(obj, ensure_ascii=False))
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        assert outcome.gate == ConversionGate.EXTRACTED_FROM_NOT_IN_SOURCE

    def test_original_rule_text_preserved_verbatim(self):
        rule_with_ws = "  当不良事件的\n严重程度为重度时\t触发风险信号  "
        cap = _capability_input(rule_text=rule_with_ws)
        text = _candidate_text()
        transport = SyntheticTransport(text)
        result = _invoke_runtime(transport, cap_input=cap)
        outcome = _convert(result, cap_input=cap)
        assert outcome.ok
        assert outcome.draft.natural_language == rule_with_ws


# ===========================================================================
# Normalization (retained)
# ===========================================================================

class TestNormalization:
    def test_whitespace_collapsed(self):
        assert normalize_rule_text("  严重\n程度  为  重度  ") == "严重 程度 为 重度"

    def test_verify_extracted_from_ok(self):
        raw = _candidate_text()
        pr = parse_rule_candidate(raw, CAT)
        ok, missing = verify_extracted_from(pr.candidate, "当不良事件的严重程度为重度时触发")
        assert ok and missing == []

    def test_verify_extracted_from_missing(self):
        obj = json.loads(_candidate_text())
        obj["conditions"][0]["extracted_from"] = "不存在的短语"
        pr = parse_rule_candidate(json.dumps(obj, ensure_ascii=False), CAT)
        ok, missing = verify_extracted_from(pr.candidate, "完全不同的文本")
        assert not ok
        assert "不存在的短语" in missing[0]


# ===========================================================================
# Simulation + activation (retained)
# ===========================================================================

class TestSimulationAndActivation:
    def test_simulation_local_deterministic(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        records = [
            {"_record_id": "r1", "SYN_AE_SEV": "重度"},
            {"_record_id": "r2", "SYN_AE_SEV": "轻度"},
            {"_record_id": "r3"},
        ]
        sim = simulate_draft(outcome.draft, records, simulation_id="sim-1")
        assert sim.simulation_id == "sim-1"
        assert sim.outcome.n_total == 3
        assert sim.outcome.n_matched == 1
        assert sim.outcome.n_missing_field == 1

    def test_user_activation(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [{"_record_id": "r1", "SYN_AE_SEV": "重度"}])
        act = activate_draft(
            outcome.draft, sim, version="v1",
            evaluation_scope=EvaluationScope(scope_kind=EvaluationScopeKind.CURRENT_SNAPSHOT),
            activated_by="user-01",
        )
        assert act.is_machine is False
        assert act.user_confirmed is True

    def test_empty_version_rejected(self):
        transport = SyntheticTransport(_candidate_text())
        result = _invoke_runtime(transport)
        outcome = _convert(result)
        sim = simulate_draft(outcome.draft, [])
        with pytest.raises(WorkflowError):
            activate_draft(
                outcome.draft, sim, version="",
                evaluation_scope=EvaluationScope(scope_kind=EvaluationScopeKind.CURRENT_SNAPSHOT),
                activated_by="u",
            )

    def test_stale_simulation_blocks_activation(self):
        text1 = _candidate_text()
        text2 = _candidate_text(rule_name="改名后的规则")
        t1 = SyntheticTransport(text1)
        t2 = SyntheticTransport(text2)
        o1 = _convert(_invoke_runtime(t1, attempt_id="a1"))
        o2 = _convert(_invoke_runtime(t2, attempt_id="a2"))
        sim_for_o1 = simulate_draft(o1.draft, [])
        with pytest.raises(RuleActivationError):
            activate_draft(
                o2.draft, sim_for_o1, version="v1",
                evaluation_scope=EvaluationScope(scope_kind=EvaluationScopeKind.CURRENT_SNAPSHOT),
                activated_by="u",
            )
