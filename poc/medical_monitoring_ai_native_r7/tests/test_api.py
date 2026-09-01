"""R7 slice-02 isolated FastAPI router contract tests (worker_03).

Uses ``create_isolated_app`` with a zero-arg factory so SQLite opens on the
ASGI/TestClient thread (landed api._resolve_entry contract).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from mm_r7 import api as api_mod  # noqa: E402
from mm_r7 import profile_store as ps  # noqa: E402
from mm_r7 import run_entry as re  # noqa: E402

REQUIRED_API_APIS = (
    "API_PREFIX",
    "create_router",
    "create_isolated_app",
    "install_exception_handlers",
    "chinese_message_for",
)

PREFIX = "/api/medical-monitoring/r7"
MTPLX_CONFIG = "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
DEEPSEEK_CONFIG = "deepseek/DeepSeek V4 flash"

FORBIDDEN_VALUE_TOKENS = (
    "super-secret-value",
    "env-value-leaked",
    "sk-",
    "modeoutput",
    "risk_instance",
    "patientjourney",
    "query_draft",
    "canonical_fact",
    "report_claim",
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "api-ws"
    root.mkdir()
    return root


@pytest.fixture
def client(workspace: Path) -> TestClient:
    def factory():
        return re.MonitoringRunEntry(workspace)

    app = api_mod.create_isolated_app(factory)
    return TestClient(app)


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _assert_error_body(payload: Mapping[str, Any], *, status_code: int) -> None:
    assert status_code >= 400
    assert isinstance(payload.get("code"), str) and payload["code"].strip()
    assert isinstance(payload.get("message"), str) and payload["message"].strip()
    assert _has_chinese(payload["message"])
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_VALUE_TOKENS:
        assert token not in blob


def _assert_public_clean(payload: Mapping[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_VALUE_TOKENS:
        assert token not in blob
    assert "effective_selector" not in payload
    assert "requested_provider" not in payload
    assert "requested_model" not in payload


def _deepseek_body() -> dict:
    return {
        "profile_id": "monitoring_harness_deepseek_v4_flash_max",
        "capability_id": "medical_monitoring_harness",
        "user_config_name": DEEPSEEK_CONFIG,
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-flash",
        "reasoning_effort": "max",
        "timeout_seconds": 120,
        "allowed_tools": ["read"],
        "context_isolation": "omp_print_no_session_no_skills_no_rules",
        "credential_ref": "env:OMP_CREDENTIAL_REF",
        "adapter_id": "omp_print_v1",
        "adapter_version": "1.0.0",
        "fallback_profile_ids": [],
    }


def _run_body(**overrides: Any) -> dict:
    base = {
        "run_id": "run-api-001",
        "project_id": "proj-api",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "cutoff-sha256:api-aaa",
        "source_revision_id": "src-sha256:api-bbb",
        "prior_accepted_snapshot_ref": None,
    }
    base.update(overrides)
    return base


def test_required_api_apis_present():
    missing = [name for name in REQUIRED_API_APIS if not hasattr(api_mod, name)]
    assert missing == []
    assert api_mod.API_PREFIX == PREFIX


def test_factory_owned_entry_is_closed_after_each_call():
    closed = []

    class Entry:
        def get_run(self, run_id):
            return {"run_id": run_id}

        def close(self):
            closed.append(True)

    assert api_mod._invoke(Entry, "get_run", "run-close") == {
        "run_id": "run-close"
    }
    assert closed == [True]


def test_bootstrap_endpoint_idempotent(client: TestClient):
    r1 = client.post(f"{PREFIX}/workspace/bootstrap")
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    _assert_public_clean(body1)
    assert body1.get("replayed") is False
    assert body1.get("layer_kind") == ps.LAYER_GLOBAL_DEFAULT
    assert body1.get("user_config_name") == MTPLX_CONFIG
    assert body1.get("reasoning_effort") == "medium"

    r2 = client.post(f"{PREFIX}/workspace/bootstrap")
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2.get("replayed") is True
    assert body2.get("revision") == body1.get("revision")
    assert body2.get("record_id") == body1.get("record_id")


def test_execution_profile_post_get_and_missing(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200

    created = client.post(
        f"{PREFIX}/execution-profiles/{ps.LAYER_PROJECT}/proj-api",
        json={
            "timeout_seconds": 88,
            "credential_ref": "env:OMP_CREDENTIAL_REF",
        },
    )
    assert created.status_code == 200, created.text
    created_body = created.json()
    _assert_public_clean(created_body)
    assert created_body.get("layer_kind") == ps.LAYER_PROJECT
    assert created_body.get("scope_key") == "proj-api"

    got = client.get(f"{PREFIX}/execution-profiles/{ps.LAYER_PROJECT}/proj-api")
    assert got.status_code == 200
    got_body = got.json()
    _assert_public_clean(got_body)
    assert got_body.get("revision") == created_body.get("revision")

    missing = client.get(
        f"{PREFIX}/execution-profiles/{ps.LAYER_PROJECT}/does-not-exist"
    )
    assert missing.status_code >= 400
    _assert_error_body(missing.json(), status_code=missing.status_code)


def test_runs_post_get_replay_conflict_and_modes(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200

    for mode in ("daily", "pre_lock", "post_lock_pre_cfdi"):
        resp = client.post(
            f"{PREFIX}/runs",
            json=_run_body(run_id=f"run-api-mode-{mode}", mode=mode),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        _assert_public_clean(body)
        assert body.get("mode") == mode
        assert body.get("replayed") is False

    first = client.post(f"{PREFIX}/runs", json=_run_body())
    assert first.status_code == 200
    first_body = first.json()
    replay = client.post(f"{PREFIX}/runs", json=_run_body())
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body.get("replayed") is True
    assert replay_body.get("run_id") == first_body.get("run_id")

    conflict = client.post(
        f"{PREFIX}/runs",
        json=_run_body(data_cutoff="cutoff-sha256:CHANGED"),
    )
    assert conflict.status_code >= 400
    _assert_error_body(conflict.json(), status_code=conflict.status_code)

    got = client.get(f"{PREFIX}/runs/run-api-001")
    assert got.status_code == 200
    _assert_public_clean(got.json())
    assert got.json().get("run_id") == "run-api-001"

    missing = client.get(f"{PREFIX}/runs/no-such-run")
    assert missing.status_code >= 400
    _assert_error_body(missing.json(), status_code=missing.status_code)


def test_incremental_and_full_basis_rules_via_api(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200

    ok = client.post(
        f"{PREFIX}/runs",
        json=_run_body(
            run_id="run-api-incr",
            execution_basis="incremental",
            prior_accepted_snapshot_ref="snap-accepted-api",
        ),
    )
    assert ok.status_code == 200, ok.text
    assert ok.json().get("execution_basis") == "incremental"

    bad_incr = client.post(
        f"{PREFIX}/runs",
        json=_run_body(
            run_id="run-api-incr-bad",
            execution_basis="incremental",
            prior_accepted_snapshot_ref=None,
        ),
    )
    assert bad_incr.status_code >= 400
    _assert_error_body(bad_incr.json(), status_code=bad_incr.status_code)

    bad_full = client.post(
        f"{PREFIX}/runs",
        json=_run_body(
            run_id="run-api-full-bad",
            execution_basis="full",
            prior_accepted_snapshot_ref="snap-should-not",
        ),
    )
    assert bad_full.status_code >= 400
    _assert_error_body(bad_full.json(), status_code=bad_full.status_code)


def test_secret_fields_rejected_without_value_leak(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200
    resp = client.post(
        f"{PREFIX}/execution-profiles/{ps.LAYER_PROJECT}/proj-secret",
        json={
            "timeout_seconds": 70,
            "credential_ref": "env:OMP_CREDENTIAL_REF",
            "credential_value": "super-secret-value",
            "api_key": "env-value-leaked",
        },
    )
    assert resp.status_code >= 400
    _assert_error_body(resp.json(), status_code=resp.status_code)


def test_explicit_deepseek_profile_via_api(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200
    created = client.post(
        f"{PREFIX}/execution-profiles/{ps.LAYER_RUN_OVERRIDE}/run-api-ds",
        json=_deepseek_body(),
    )
    assert created.status_code == 200, created.text
    _assert_public_clean(created.json())
    assert created.json().get("user_config_name") == DEEPSEEK_CONFIG

    bound = client.post(
        f"{PREFIX}/runs",
        json=_run_body(
            run_id="run-api-ds",
            project_id="proj-api-ds",
            data_cutoff="cutoff-sha256:ds-api",
            source_revision_id="src-sha256:ds-api",
            run_override_scope_key="run-api-ds",
        ),
    )
    assert bound.status_code == 200, bound.text
    body = bound.json()
    _assert_public_clean(body)
    assert body.get("user_config_name") == DEEPSEEK_CONFIG


def test_explicit_deepseek_name_only_via_api(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200
    created = client.post(
        f"{PREFIX}/execution-profiles/{ps.LAYER_RUN_OVERRIDE}/run-api-ds-name",
        json={"user_config_name": DEEPSEEK_CONFIG},
    )
    assert created.status_code == 200, created.text

    bound = client.post(
        f"{PREFIX}/runs",
        json=_run_body(
            run_id="run-api-ds-name",
            project_id="proj-api-ds-name",
            data_cutoff="cutoff-sha256:ds-name",
            source_revision_id="src-sha256:ds-name",
            run_override_scope_key="run-api-ds-name",
        ),
    )
    assert bound.status_code == 200, bound.text
    assert bound.json()["user_config_name"] == DEEPSEEK_CONFIG


def test_router_prefix_is_isolated_not_product_main(client: TestClient):
    for path in ("/", "/health", "/api/medical-writing"):
        resp = client.get(path)
        assert resp.status_code in {404, 405, 422} or resp.status_code >= 400
    resp = client.post(f"{PREFIX}/workspace/bootstrap")
    assert resp.status_code == 200, resp.text


def test_strict_dto_rejects_unknown_run_fields(client: TestClient):
    assert client.post(f"{PREFIX}/workspace/bootstrap").status_code == 200
    resp = client.post(
        f"{PREFIX}/runs",
        json={
            **_run_body(run_id="run-api-extra"),
            "medical_fact": "should-not-pass",
            "risk_instance": {"id": "x"},
        },
    )
    assert resp.status_code >= 400
    body = resp.json()
    if "code" in body and "message" in body:
        _assert_error_body(body, status_code=resp.status_code)
    else:
        blob = json.dumps(body, ensure_ascii=False).lower()
        assert "super-secret-value" not in blob
        assert "sk-" not in blob


def test_create_router_from_run_entry_wires(workspace: Path):
    if not hasattr(api_mod, "create_router_from_run_entry"):
        pytest.skip("create_router_from_run_entry not exported")
    router = api_mod.create_router_from_run_entry(workspace)
    assert router.prefix == PREFIX
    assert any(
        getattr(route, "path", "").endswith("/workspace/bootstrap")
        for route in router.routes
    )


def test_app_from_run_entry_keeps_chinese_error_envelope(workspace: Path):
    app = api_mod.create_isolated_app_from_run_entry(workspace)
    response = TestClient(app).post(f"{PREFIX}/runs", json={"unexpected": 1})
    assert response.status_code == 422
    _assert_error_body(response.json(), status_code=response.status_code)
    assert "detail" not in response.json()
