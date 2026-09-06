from copy import deepcopy

import pytest

from services.api.app.ai_gateway import AiPromptEnvelope, AiTaskType
from services.api.app.monitoring_evidence_tool_loop import (
    TOOL_REQUEST_SCHEMA, EvidenceToolLoopError, run_evidence_tool_loop,
)


def envelope():
    return AiPromptEnvelope(task_id="job-test", task_type=list(AiTaskType)[0],
                            prompt_version="tool-test-v1", system_prompt="original contract",
                            payload={"frozen_source": {"revision": "rev-one"}})


def request(**changes):
    result = {"schema_version": TOOL_REQUEST_SCHEMA, "task_id": "job-test",
              "input_revision_sha256": "rev-one", "tool_requests": [{
                  "request_id": "read-1", "name": "read_source_region",
                  "arguments": {"table_binding_id": "table-one", "column_indexes": [0]},
              }]}
    result.update(changes)
    return result


def run(outputs, **overrides):
    calls, checks, reads = [], [], []
    responses = iter(outputs)
    def model(value):
        calls.append(deepcopy(value))
        return next(responses)
    def execute(name, arguments):
        reads.append((name, arguments))
        return {"input_revision_sha256": "rev-one", "data": {"coverage": "partial", "value": 0}}
    options = dict(input_revision="rev-one", call_model=model,
                   validate_current=lambda: checks.append("revision"),
                   validate_model=lambda: checks.append("model"),
                   tool_schemas={"read_source_region": {"type": "object"}}, execute_tool=execute)
    options.update(overrides)
    original = envelope()
    before = deepcopy(original)
    result = run_evidence_tool_loop(original, **options)
    assert original == before
    return result, calls, checks, reads


def test_model_requests_frozen_evidence_before_final_answer():
    final = {"candidates": [{"explanation": "model-authored interpretation"}]}
    result, calls, checks, reads = run([request(), final])
    assert result.output == final
    assert result.model_turns == 2
    assert len(reads) == 1
    assert calls[1].payload["evidence_tool_results"][0]["result"]["data"] == {"coverage": "partial", "value": 0}
    assert calls[1].payload["frozen_source"] == calls[0].payload["frozen_source"]
    assert checks.count("model") == 2
    assert checks.count("revision") == 6


def test_no_cross_model_context_is_shared_between_sessions():
    first, *_ = run([request(), {"candidates": [{"label": "primary"}]}])
    second, calls, *_ = run([{"candidates": [{"label": "blind verifier"}]}])
    assert first.receipts
    assert not second.receipts
    assert "evidence_tool_results" not in calls[0].payload


@pytest.mark.parametrize("bad", [
    request(task_id="different-job"), request(input_revision_sha256="stale"),
    request(candidates=[]), request(tool_requests=[]),
    request(tool_requests=[{"request_id": "x", "name": "unavailable", "arguments": {}}]),
])
def test_invalid_or_unbound_tool_requests_cannot_be_accepted(bad):
    with pytest.raises(EvidenceToolLoopError):
        run([bad])


def test_budget_exhaustion_does_not_return_last_request_as_success():
    with pytest.raises(EvidenceToolLoopError, match="budget_exhausted"):
        run([request()], max_model_turns=1)


def test_duplicate_request_id_does_not_repeat_the_read():
    with pytest.raises(EvidenceToolLoopError, match="duplicate"):
        run([request(), request()])


def test_result_from_different_revision_is_not_given_to_model():
    with pytest.raises(EvidenceToolLoopError, match="result_revision_mismatch"):
        run([request()], execute_tool=lambda *_: {"input_revision_sha256": "different"})


def test_changed_source_after_model_call_prevents_tool_execution():
    validations = 0
    def validate():
        nonlocal validations
        validations += 1
        if validations == 2:
            raise ValueError("changed source")
    def forbidden(*_):
        pytest.fail("read executed after evidence changed")
    with pytest.raises(ValueError, match="changed source"):
        run([request()], validate_current=validate, execute_tool=forbidden)


def test_model_identity_checked_even_when_it_only_requests_a_tool():
    def reject():
        raise ValueError("wrong model")
    def forbidden(*_):
        pytest.fail("read executed after model identity mismatch")
    with pytest.raises(ValueError, match="wrong model"):
        run([request()], validate_model=reject, execute_tool=forbidden)


def test_one_protocol_repair_uses_existing_turn_budget_without_executing_invalid_request():
    final = {"candidates": []}
    result, calls, _, reads = run([request(task_id="wrong"), request(), final],
                                 max_protocol_repairs=1, max_model_turns=3)
    assert result.model_turns == 3
    assert len(reads) == 1
    assert calls[1].payload["evidence_tool_protocol_repair"]["error_code"] == "tool_request_identity_or_shape_mismatch"
    assert calls[1].payload["evidence_tool_protocol"]["remaining_model_turns"] == 2
    with pytest.raises(EvidenceToolLoopError):
        run([request(task_id="wrong"), request(task_id="wrong")], max_protocol_repairs=1)


def test_echoed_budget_counters_never_expand_harness_budgets():
    echoed = request(remaining_tool_calls=999999, remaining_model_turns=999999)
    result, _, _, reads = run([echoed, {"candidates": []}], max_model_turns=2, max_tool_calls=1)
    assert len(reads) == 1 and result.model_turns == 2
    with pytest.raises(EvidenceToolLoopError, match="budget_exhausted"):
        run([echoed], max_model_turns=1)
    with pytest.raises(EvidenceToolLoopError):
        run([request(remaining_tool_calls="unlimited")])
