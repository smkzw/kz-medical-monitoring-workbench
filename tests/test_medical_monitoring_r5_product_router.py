from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.medical_monitoring_r5_product_router import (
    R5_PRODUCT_PREFIX,
    create_medical_monitoring_r5_product_router,
)
from services.api.app.medical_monitoring_r5_product_adapter import response_snapshot_sha256
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)


PROJECT = "s7-synthetic-project-001"
RUN = "s7-run-current-001"
SNAPSHOT = "s7-snapshot-current-001"
CUTOFF = "2026-03-31"


def _client(*, principal: MonitoringAuthenticatedPrincipal | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r5_product_router(
            synthetic_fixture_mode=True,
            principal_resolver=(lambda _request: principal),
        )
    )
    return TestClient(app)


def _principal() -> MonitoringAuthenticatedPrincipal:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "s7-user-001",
            "tenant_id": "s7-tenant-001",
            "roles": ["medical_manager"],
            "project_scope": [PROJECT],
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "authenticated": True,
            "authn_method": "offline-test-session",
            "session_id": "s7-test-session",
            "directory_revision": "s7-test-directory-v1",
            "verification_ref_sha256": "c" * 64,
        },
        now=now,
    )


def _base() -> str:
    return R5_PRODUCT_PREFIX.format(project_id=PROJECT)


def test_router_exposes_exactly_three_get_routes() -> None:
    app = FastAPI()
    app.include_router(create_medical_monitoring_r5_product_router(synthetic_fixture_mode=True))
    routes = {
        (route.path, tuple(sorted(route.methods)))
        for route in app.routes
        if route.path.startswith("/api/projects/") and "/medical-monitoring/r5" in route.path
    }
    assert routes == {
        (f"{R5_PRODUCT_PREFIX}/overview", ("GET",)),
        (f"{R5_PRODUCT_PREFIX}/subject-workspaces/{{subject_id}}", ("GET",)),
        (f"{R5_PRODUCT_PREFIX}/source-evidence", ("GET",)),
    }


def test_three_get_surfaces_return_complete_read_only_envelope() -> None:
    client = _client(principal=_principal())
    responses = [
        client.get(f"{_base()}/overview"),
        client.get(
            f"{_base()}/subject-workspaces/s7-subject-10008",
            params={
                "run_ref": RUN,
                "snapshot_ref": SNAPSHOT,
                "cutoff_ref": CUTOFF,
                "site_ref": "s7-site-010",
                "spine_ref": "s7-spine-10008",
                "window_start": "2026-01-01",
                "window_end": "2026-03-31",
                "risk_instance_ref": "s7-risk-pd-10008",
            },
        ),
        client.get(
            f"{_base()}/source-evidence",
            params={
                "run_ref": RUN,
                "snapshot_ref": SNAPSHOT,
                "cutoff_ref": CUTOFF,
                "risk_instance_ref": "s7-risk-pd-10008",
                "source_locator_ref": "s7-source-pd-10008",
            },
        ),
    ]
    assert [response.status_code for response in responses] == [200, 200, 200]
    for response in responses:
        payload = response.json()
        assert payload["schema"] == "medical-monitoring-r5-s7-product-read-model-v0.1"
        assert payload["read_only"] is True
        assert payload["mutation_applied"] is False
        assert payload["persisted"] is False
        assert payload["aggregate_version_before"] == payload["aggregate_version_after"]
        assert payload["identity"]["project_ref"] == PROJECT
        assert payload["identity"]["run_ref"] == RUN
        assert payload["identity"]["principal_identity_hash"]
        assert payload["identity"]["authorization_decision_sha256"]
        assert payload["identity"]["audit_id"]
        assert payload["response_snapshot_sha256"] == payload["identity"]["response_snapshot_sha256"]
        assert payload["response_snapshot_sha256"] == payload["read_handoff"]["response_snapshot_sha256"]


def test_actual_overview_and_subject_shapes_bind_risk_source_and_tamper_digest() -> None:
    client = _client(principal=_principal())
    overview_response = client.get(f"{_base()}/overview")
    subject_response = client.get(
        f"{_base()}/subject-workspaces/s7-subject-10008",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "site_ref": "s7-site-010",
            "spine_ref": "s7-spine-10008",
            "window_start": "2026-01-01",
            "window_end": "2026-03-31",
            "risk_instance_ref": "s7-risk-pd-10008",
        },
    )
    assert overview_response.status_code == subject_response.status_code == 200
    overview = overview_response.json()
    subject = subject_response.json()

    assert isinstance(overview["projection"]["center_map"], dict)
    assert set(overview["projection"]["center_map"]) == {
        "stable_site_order",
        "cells",
        "projection_instance",
        "content_hash",
    }
    assert overview["projection"]["center_map"]["cells"]
    assert overview["projection"]["current_risks"]
    assert overview["counts"]["current_risk"]["high"] == 2
    assert overview["counts"]["current_risk"]["medium"] == 1
    assert overview["counts"]["change_band_count"] == len(overview["projection"]["change_bands"]) == 3
    assert overview["counts"]["individual_risk"] == len(overview["projection"]["current_risks"])
    overview_risk = next(
        item for item in overview["projection"]["current_risks"] if item["risk_instance_ref"] == "s7-risk-pd-10008"
    )
    assert overview_risk["source_locator_ref"] == "s7-source-pd-10008"
    assert overview_risk["risk_anchor_ref"] == "s7-anchor-pd-10008"

    subject_projection = subject["projection"]
    assert subject_projection["current_risks"]
    subject_risk = next(
        item for item in subject_projection["current_risks"] if item["risk_instance_ref"] == "s7-risk-pd-10008"
    )
    assert subject_risk["source_locator_ref"] == overview_risk["source_locator_ref"]
    assert subject_risk["risk_anchor_ref"] == overview_risk["risk_anchor_ref"]
    assert subject_projection["temporal_spine"]["visits"] == subject_projection["visits"]
    assert subject_projection["temporal_spine"]["pending_dates"] == subject_projection["pending_dates"]
    assert subject_projection["indicators"]
    assert all(indicator["points"] for indicator in subject_projection["indicators"])

    source_response = client.get(
        f"{_base()}/source-evidence",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "risk_instance_ref": subject_risk["risk_instance_ref"],
            "source_locator_ref": subject_risk["source_locator_ref"],
        },
    )
    assert source_response.status_code == 200
    evidence = source_response.json()["projection"]["evidence"]
    assert evidence["record_ref"] == "方案执行 Data Listing 第 10008 行"
    assert evidence["canonical_location"] == "方案执行 Data Listing · 第 10008 行 · 访视日期单元格"
    assert evidence["excerpt"]
    source_ref = source_response.json()["source_refs"]
    assert len(source_ref) == 1
    assert all(source_ref[0][field] == evidence[field] for field in ("record_ref", "canonical_location", "excerpt"))
    assert source_response.json()["projection"]["source_locator_ref"] == subject_risk["source_locator_ref"]
    assert source_response.json()["identity"]["risk_instance_ref"] == subject_risk["risk_instance_ref"]
    assert source_response.json()["identity"]["source_locator_ref"] == subject_risk["source_locator_ref"]
    assert set(source_response.json()["projection"]) == {
        "kind",
        "risk_ref",
        "risk_instance_ref",
        "source_locator_ref",
        "evidence",
        "authority_receipt_ref",
        "content_hash",
    }
    assert "domain_encoding" not in source_response.json()["projection"]
    assert "domain_tracks" not in source_response.json()["projection"]

    assert response_snapshot_sha256(overview) == overview["response_snapshot_sha256"]
    tampered_projection = deepcopy(overview)
    tampered_projection["projection"]["current_risks"][0]["severity"] = "low"
    assert response_snapshot_sha256(tampered_projection) != overview["response_snapshot_sha256"]
    tampered_identity = deepcopy(overview)
    tampered_identity["identity"]["project_ref"] = "s7-other-project"
    assert response_snapshot_sha256(tampered_identity) != overview["response_snapshot_sha256"]
    tampered_missing_count = deepcopy(overview)
    del tampered_missing_count["counts"]["change_band_count"]
    assert response_snapshot_sha256(tampered_missing_count) != overview["response_snapshot_sha256"]


def test_site_scoped_overview_preserves_exact_site_and_source_identity() -> None:
    client = _client(principal=_principal())
    site_response = client.get(
        f"{_base()}/overview",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "site_ref": "s7-site-010",
        },
    )
    assert site_response.status_code == 200
    site_payload = site_response.json()
    site_projection = site_payload["projection"]
    assert site_payload["identity"]["site_ref"] == "s7-site-010"
    assert site_projection["center_map"]["stable_site_order"] == ["s7-site-010"]
    assert all(item["site_ref"] == "s7-site-010" for item in site_projection["center_map"]["cells"])
    assert all(item["site_ref"] == "s7-site-010" for item in site_projection["current_risks"])
    assert all(item["site_ref"] == "s7-site-010" for item in site_projection["subjects"])
    assert site_payload["counts"]["change_band_count"] == len(site_projection["change_bands"]) == 1

    missing_site = client.get(
        f"{_base()}/overview",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "site_ref": "s7-site-not-authoritative",
        },
    )
    assert missing_site.status_code == 409

    source_response = client.get(
        f"{_base()}/source-evidence",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "risk_instance_ref": "s7-risk-pd-10008",
            "source_locator_ref": "s7-source-pd-10008",
        },
    )
    assert source_response.status_code == 200
    source_payload = source_response.json()
    assert source_payload["identity"]["site_ref"] == "s7-site-010"
    assert source_payload["identity"]["risk_instance_ref"] == "s7-risk-pd-10008"
    assert source_payload["identity"]["source_locator_ref"] == "s7-source-pd-10008"
    assert source_payload["projection"]["risk_instance_ref"] == source_payload["identity"]["risk_instance_ref"]
    assert source_payload["projection"]["source_locator_ref"] == source_payload["identity"]["source_locator_ref"]


def test_overview_query_is_optional_as_a_first_authority_read_but_grouped_afterward() -> None:
    client = _client(principal=_principal())
    first = client.get(f"{_base()}/overview")
    complete = client.get(
        f"{_base()}/overview",
        params={"run_ref": RUN, "snapshot_ref": SNAPSHOT, "cutoff_ref": CUTOFF},
    )
    partial = client.get(f"{_base()}/overview?run_ref={RUN}")
    assert first.status_code == complete.status_code == 200
    assert first.json()["identity"]["snapshot_ref"] == complete.json()["identity"]["snapshot_ref"]
    assert partial.status_code == 422


def test_unknown_duplicate_and_body_inputs_fail_closed() -> None:
    client = _client(principal=_principal())
    unknown = client.get(f"{_base()}/overview?debug=1")
    duplicate = client.get(f"{_base()}/overview?run_ref={RUN}&run_ref={RUN}&snapshot_ref={SNAPSHOT}&cutoff_ref={CUTOFF}")
    body = client.request("GET", f"{_base()}/overview", content=b"{}")
    post = client.post(f"{_base()}/overview")
    assert unknown.status_code == 422
    assert duplicate.status_code == 422
    assert body.status_code == 422
    assert post.status_code == 405


def test_subject_and_source_targets_do_not_use_nearest_fallback() -> None:
    client = _client(principal=_principal())
    subject = client.get(
        f"{_base()}/subject-workspaces/s7-subject-10008",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "site_ref": "s7-site-010",
            "spine_ref": "s7-spine-other",
            "window_start": "2026-01-01",
            "window_end": "2026-03-31",
        },
    )
    source = client.get(
        f"{_base()}/source-evidence",
        params={
            "run_ref": RUN,
            "snapshot_ref": SNAPSHOT,
            "cutoff_ref": CUTOFF,
            "risk_instance_ref": "s7-risk-pd-10008",
            "source_locator_ref": "s7-source-ae-06021",
        },
    )
    assert subject.status_code == 409
    assert source.status_code == 409


def test_missing_principal_and_project_scope_are_blocked() -> None:
    missing = _client().get(f"{_base()}/overview")
    other = _principal()
    scoped = MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "s7-user-other",
            "tenant_id": "s7-tenant-001",
            "roles": ["medical_manager"],
            "project_scope": ["s7-other-project"],
            "issued_at": other.issued_at.isoformat(),
            "expires_at": other.expires_at.isoformat(),
            "authenticated": True,
            "authn_method": "offline-test-session",
            "session_id": "s7-test-session-other",
            "directory_revision": "s7-test-directory-v1",
            "verification_ref_sha256": "d" * 64,
        },
        now=other.issued_at,
    )
    denied = _client(principal=scoped).get(f"{_base()}/overview")
    assert missing.status_code == 503
    assert denied.status_code == 403
