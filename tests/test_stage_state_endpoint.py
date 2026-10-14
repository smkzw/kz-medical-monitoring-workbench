"""状态机专项S7（02_DESIGN §3.5/§5.3/§5.4/§7）：stage-state端点+blocking不变量。

- build_stage_view四阶段聚合+current_stage单向映射；
- §5.3死锁形态参数化（R41阻断组/R3识别失败/疑点未决/确认禁用）——
  自救形态恒产出action_available键；
- 健康等待态不误伤（不500）；
- 端点：projection权限+If-None-Match 304语义。
"""

from __future__ import annotations

import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.admission_stage_view import (  # noqa: E402
    AdmissionStageViewError,
    build_stage_view,
)
from packages.medical_monitoring.api.r7_product import (  # noqa: E402
    mapping_candidate_routes as mcr,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (  # noqa: E402
    MappingCandidateRouteContext,
    register_mapping_candidate_routes,
)


def _view(**overrides):
    base = dict(
        project_id="p1",
        attempt_id="attempt-1",
        documents_state="ready",
        recognition_state="candidates_ready",
        mapping_state="no_draft",
        facts_state="not_generated",
    )
    base.update(overrides)
    return build_stage_view(**base)


def test_full_complete_stage_view() -> None:
    view = _view(
        mapping_state="confirmed",
        facts_state="ready",
    )
    assert view["current_stage"] == "complete"
    assert view["blocking"] == []
    assert view["primary_action_key"] == ""
    assert view["stages"] == {
        "documents": "ready",
        "recognition": "candidates_ready",
        "mapping_confirmation": "confirmed",
        "facts": "ready",
    }


@pytest.mark.parametrize("shape,expected_key", [
    # R41-01实测形态：阻断组恒在→resolve_blocked_groups。
    (
        {"mapping_state": "draft_active", "blocked_group_count": 5},
        "resolve_blocked_groups",
    ),
    # R3实测形态：识别needs_attention→adopt_partial。
    (
        {"recognition_state": "needs_attention"},
        "adopt_partial",
    ),
    # 疑点未决（确认曾被恒禁用的形态）→answer_questions。
    (
        {"mapping_state": "draft_active", "unresolved_question_count": 3},
        "answer_questions",
    ),
    # S5降级形态：generating停滞→adopt_inflight_degraded。
    (
        {
            "documents_state": "in_progress",
            "recognition_state": "generating",
            "inflight_adoption_available": True,
        },
        "adopt_inflight_degraded",
    ),
    # 识别分片终态失败（R32形态）→retry_recognition_failed。
    (
        {"recognition_state": "generating", "recognition_failed_shards": True},
        "retry_recognition_failed",
    ),
])
def test_deadlock_shapes_always_yield_actionable_key(
    shape: dict, expected_key: str
) -> None:
    """§5.3不变量：自救形态必须在blocking[]携带action_available键。"""

    view = _view(**shape)
    assert view["primary_action_key"] == expected_key
    actionable = [
        entry for entry in view["blocking"] if entry["action_available"]
    ]
    assert actionable, f"死锁形态无可用动作键: {shape}"
    assert expected_key in {entry["action_key"] for entry in actionable}


def test_healthy_waiting_states_do_not_fail_closed() -> None:
    """健康等待态（documents核对中/识别推进中）如实等待，不误伤500。"""

    view = _view(
        documents_state="in_progress",
        recognition_state="not_started",
        mapping_state="no_draft",
    )
    assert view["current_stage"] == "documents"
    # in_progress=健康等待：主按钮无动作键（对比not_started的upload）。
    assert view["primary_action_key"] == ""
    recognition_entry = next(
        entry for entry in view["blocking"] if entry["stage"] == "recognition"
    )
    assert recognition_entry["action_available"] is False

    view = _view(
        documents_state="ready",
        recognition_state="generating",
        mapping_state="no_draft",
    )
    assert view["current_stage"] == "recognition"
    assert view["primary_action_key"] == ""


def test_invalid_stage_enum_fails_closed() -> None:
    with pytest.raises(AdmissionStageViewError):
        _view(recognition_state="made_up_state")


def _client_with(tmp_path: Path, *, pipeline, confirmation):
    app = FastAPI()
    router = type(app.router)()
    context = MappingCandidateRouteContext(
        root=tmp_path,
        resolve_project=lambda project_id: project_id,
        authorize=lambda request, *, project_id, action: None,
        acquire_product_write_gate=lambda **_kwargs: None,
        workspace_dir=lambda root, project_id: root / project_id,
        monitoring_action=SimpleNamespace(READ_SOURCE_EVIDENCE="read"),
        admission_mapping_pipeline=pipeline,
        admission_mapping_confirmation=confirmation,
    )
    register_mapping_candidate_routes(router, context)
    # 生产挂载同款前缀（medical_monitoring_r7_product_router.R7_PRODUCT_PREFIX）。
    app.include_router(
        router,
        prefix="/api/projects/{project_id}/modules/medical-monitoring/r7",
    )
    return TestClient(app)


def test_stage_state_endpoint_projection_and_304(tmp_path: Path) -> None:
    documents_payload = {"ready": True, "roles": [{"status": "current"}]}
    pipeline = SimpleNamespace(
        document_readiness=lambda **_kwargs: documents_payload,
    )
    stage_row = {"state": "candidates_ready", "revision": 7}
    confirmation = SimpleNamespace(
        ai_repository=SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: [],
        ),
        _recognition_state_row=lambda *, project_id, attempt_id: stage_row,
        mapping_repository=SimpleNamespace(
            find_draft_for_batch=lambda *_args: SimpleNamespace(
                draft_id="draft-1",
                batch_id="attempt-1",
                status=SimpleNamespace(value="confirmed"),
            ),
        ),
        _facts_status=lambda *, project_id, attempt_id, workspace_dir: {
            "state": "ready", "facts_generated": True,
        },
        task_type=SimpleNamespace(value="listing_field_mapping"),
    )
    client = _client_with(tmp_path, pipeline=pipeline, confirmation=confirmation)
    response = client.get(
        "/api/projects/p1/modules/medical-monitoring/r7/"
        "data-admissions/attempt-1/stage-state"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_stage"] == "complete"
    assert payload["stages"]["recognition"] == "candidates_ready"
    assert payload["revision"] == 7
    assert payload["stages"]["facts"] == "ready"
    etag = response.headers.get("etag")

    # If-None-Match命中→304（轮询省流量，R31-03诱因消除）。
    cached = client.get(
        "/api/projects/p1/modules/medical-monitoring/r7/"
        "data-admissions/attempt-1/stage-state",
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_stage_state_endpoint_documents_in_progress(tmp_path: Path) -> None:
    pipeline = SimpleNamespace(
        document_readiness=lambda **_kwargs: {
            "ready": False, "state": "cross_checking",
        },
    )
    confirmation = SimpleNamespace(
        ai_repository=SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: [],
        ),
        _recognition_state_row=lambda *, project_id, attempt_id: None,
        mapping_repository=None,
        _facts_status=lambda *, project_id, attempt_id, workspace_dir: {
            "facts_generated": False,
        },
        task_type=SimpleNamespace(value="listing_field_mapping"),
    )
    client = _client_with(tmp_path, pipeline=pipeline, confirmation=confirmation)
    response = client.get(
        "/api/projects/p1/modules/medical-monitoring/r7/"
        "data-admissions/attempt-1/stage-state"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_stage"] == "documents"
    assert payload["stages"]["documents"] == "in_progress"
    assert payload["primary_action_key"] == ""
