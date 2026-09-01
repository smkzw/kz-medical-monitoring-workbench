"""R7 slice-01 profile-layer persistence contract tests (worker_03)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mm_r7 import profile_store as ps

REQUIRED_PROFILE_APIS = (
    "ProfileStore",
    "ProfileStoreError",
    "ProfileLayerRecord",
    "LAYER_GLOBAL_DEFAULT",
    "LAYER_CAPABILITY_AGENT",
    "LAYER_PROJECT",
    "LAYER_RUN_OVERRIDE",
    "LAYER_PRECEDENCE",
    "GLOBAL_SCOPE_KEY",
    "public_projection",
    "audit_projection",
)


def _fields(**overrides: Any) -> dict:
    base = {
        "profile_id": "monitoring_harness_default_mtplx_qwen38_medium",
        "capability_id": "medical_monitoring_harness",
        "user_config_name": (
            "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
        ),
        "requested_provider": "mtplx",
        "requested_model": "Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality",
        "reasoning_effort": "medium",
        "timeout_seconds": 120,
        "allowed_tools": ["read"],
        "context_isolation": "omp_print_no_session_no_skills_no_rules",
        "credential_ref": "env:OMP_CREDENTIAL_REF",
        "adapter_id": "omp_print_v1",
        "adapter_version": "1.0.0",
        "fallback_profile_ids": [],
    }
    base.update(overrides)
    return base


def test_required_profile_store_apis_present():
    missing = [name for name in REQUIRED_PROFILE_APIS if not hasattr(ps, name)]
    assert missing == []


def test_layer_precedence_order_is_contractual():
    assert tuple(ps.LAYER_PRECEDENCE) == (
        ps.LAYER_GLOBAL_DEFAULT,
        ps.LAYER_CAPABILITY_AGENT,
        ps.LAYER_PROJECT,
        ps.LAYER_RUN_OVERRIDE,
    )
    assert ps.GLOBAL_SCOPE_KEY == "*"


def test_append_creates_immutable_revisions(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        r1 = store.append_revision(
            ps.LAYER_GLOBAL_DEFAULT, "*", _fields(timeout_seconds=120)
        )
        r2 = store.append_revision(
            ps.LAYER_GLOBAL_DEFAULT, "*", _fields(timeout_seconds=180)
        )
        assert r1.revision != r2.revision
        assert r1.content_digest != r2.content_digest
        hist = store.list_revisions(ps.LAYER_GLOBAL_DEFAULT, "*")
        assert len(hist) == 2
        assert hist[0].revision == r1.revision
        assert hist[1].revision == r2.revision
        again = store.get_revision(ps.LAYER_GLOBAL_DEFAULT, "*", r1.revision)
        assert again.content_digest == r1.content_digest
        assert again.fields["timeout_seconds"] == 120
        latest = store.latest_revision(ps.LAYER_GLOBAL_DEFAULT, "*")
        assert latest is not None
        assert latest.revision == r2.revision
        assert latest.fields["timeout_seconds"] == 180
    finally:
        store.close()


def test_four_layer_kinds_persist_independently(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        g = store.append_revision(ps.LAYER_GLOBAL_DEFAULT, "*", _fields())
        c = store.append_revision(
            ps.LAYER_CAPABILITY_AGENT,
            "medical_monitoring_harness",
            _fields(timeout_seconds=90),
        )
        p = store.append_revision(
            ps.LAYER_PROJECT,
            "proj-synthetic-001",
            _fields(reasoning_effort="medium"),
        )
        o = store.append_revision(
            ps.LAYER_RUN_OVERRIDE,
            "run-synthetic-001",
            _fields(
                profile_id="monitoring_harness_deepseek_v4_flash_max",
                user_config_name="deepseek/DeepSeek V4 flash",
                requested_provider="deepseek",
                requested_model="deepseek-v4-flash",
                reasoning_effort="max",
            ),
        )
        assert g.layer_kind == ps.LAYER_GLOBAL_DEFAULT
        assert c.layer_kind == ps.LAYER_CAPABILITY_AGENT
        assert p.layer_kind == ps.LAYER_PROJECT
        assert o.layer_kind == ps.LAYER_RUN_OVERRIDE
        assert store.latest_revision(ps.LAYER_PROJECT, "proj-synthetic-001")
        assert (
            store.latest_revision(ps.LAYER_RUN_OVERRIDE, "run-synthetic-001")
            .fields["reasoning_effort"]
            == "max"
        )
        ordered = store.load_precedence_layers(
            capability_scope="medical_monitoring_harness",
            project_scope="proj-synthetic-001",
            run_scope="run-synthetic-001",
        )
        assert ordered[0] is not None
        assert ordered[3].fields["reasoning_effort"] == "max"
    finally:
        store.close()


@pytest.mark.parametrize(
    "banned_key,banned_value",
    [
        ("credential_value", "sk-SECRETVALUE123"),
        ("credential", "sk-SECRETVALUE123"),
        ("api_key", "sk-SECRETVALUE123"),
        ("password", "hunter2"),
        ("secret", "topsecret"),
        ("token", "Bearer abc"),
    ],
)
def test_credential_value_fields_fail_closed(db_path: Path, banned_key, banned_value):
    store = ps.ProfileStore(db_path)
    try:
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision(
                ps.LAYER_GLOBAL_DEFAULT, "*", _fields(**{banned_key: banned_value})
            )
    finally:
        store.close()


def test_empty_required_values_fail_closed(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision(
                ps.LAYER_GLOBAL_DEFAULT, "*", _fields(profile_id="")
            )
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision(
                ps.LAYER_GLOBAL_DEFAULT, "*", _fields(credential_ref="")
            )
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision("not_a_layer", "*", _fields())
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision(ps.LAYER_PROJECT, "", _fields())
        with pytest.raises(ps.ProfileStoreError):
            store.append_revision(ps.LAYER_GLOBAL_DEFAULT, "*", {})
        for field in (
            "profile_id",
            "user_config_name",
            "requested_provider",
            "requested_model",
            "effective_selector",
            "reasoning_effort",
            "adapter_id",
        ):
            with pytest.raises(ps.ProfileStoreError):
                store.append_revision(
                    ps.LAYER_PROJECT,
                    "proj-whitespace",
                    {field: "   ", "credential_ref": "env:OMP_CREDENTIAL_REF"},
                )
        for value in ("   ", "\n", "\t", " env:OMP_CREDENTIAL_REF "):
            with pytest.raises(ps.ProfileStoreError, match="empty_credential_ref"):
                store.append_revision(
                    ps.LAYER_PROJECT,
                    "proj-credential-whitespace",
                    {"credential_ref": value},
                )
    finally:
        store.close()


@pytest.mark.parametrize(
    "payload,error",
    [
        (
            {"timeout_seconds": 111, "credential_ref": "sk-SECRETVALUE12345678"},
            "credential_ref_must_not_be_secret_value",
        ),
        (
            {"timeout_seconds": 50, "credential_value": "sk-SECRETVALUE12345678"},
            "credential_value_field_forbidden",
        ),
        (
            {"profile_id": "   ", "credential_ref": "env:OMP_CREDENTIAL_REF"},
            "empty_required_field",
        ),
        (
            {"credential_ref": " env:OMP_CREDENTIAL_REF "},
            "empty_credential_ref",
        ),
    ],
)
def test_reopen_revalidates_coordinated_stored_payload(
    db_path: Path, payload: dict, error: str
):
    store = ps.ProfileStore(db_path)
    try:
        original = store.append_revision(
            ps.LAYER_PROJECT, "proj-corrupt", _fields()
        )
        digest = ps.content_digest(payload)
        record_id = ps._record_id_for(
            original.layer_kind, original.scope_key, original.revision, digest
        )
        store._conn.execute(
            "UPDATE profile_layer_versions SET payload_json = ?, content_digest = ?, "
            "record_id = ? WHERE layer_kind = ? AND scope_key = ? AND revision = ?",
            (
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                digest,
                record_id,
                original.layer_kind,
                original.scope_key,
                original.revision,
            ),
        )
        store._conn.commit()
        store.reopen()
        with pytest.raises(ps.ProfileStoreError, match=error):
            store.get_revision(
                original.layer_kind, original.scope_key, original.revision
            )
    finally:
        store.close()


def test_public_and_audit_projections(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        rev = store.append_revision(ps.LAYER_GLOBAL_DEFAULT, "*", _fields())
        public = store.public_projection(rev)
        audit = store.audit_projection(rev)
        pub_blob = json.dumps(public, ensure_ascii=False)
        aud_blob = json.dumps(audit, ensure_ascii=False)
        assert public["credential_ref"] == "env:OMP_CREDENTIAL_REF"
        assert "user_config_name" in public
        assert "credential_value" not in public
        assert "credential_value" not in audit
        assert "effective_selector" not in public
        assert "requested_provider" not in public
        assert "effective_selector" in audit or "requested_provider" in audit
        assert "content_digest" in audit
        for banned in ("sk-", "SECRETVALUE", "hunter2"):
            assert banned not in pub_blob
            assert banned not in aud_blob
        ps.assert_projection_has_no_credential_values(public)
        ps.assert_projection_has_no_credential_values(audit)
    finally:
        store.close()


def test_sqlite_close_reopen_parity(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        rev = store.append_revision(
            ps.LAYER_PROJECT, "proj-reopen", _fields(timeout_seconds=111)
        )
        digest = rev.content_digest
        revision = rev.revision
        public = store.public_projection(rev)
        audit = store.audit_projection(rev)
    finally:
        store.close()

    store2 = ps.ProfileStore(db_path)
    try:
        again = store2.get_revision(ps.LAYER_PROJECT, "proj-reopen", revision)
        assert again.content_digest == digest
        assert again.fields["timeout_seconds"] == 111
        assert store2.public_projection(again) == public
        assert store2.audit_projection(again) == audit
        latest = store2.latest_revision(ps.LAYER_PROJECT, "proj-reopen")
        assert latest is not None
        assert latest.content_digest == digest
        store2.reopen()
        assert store2.latest_revision(ps.LAYER_PROJECT, "proj-reopen").content_digest == digest
    finally:
        store2.close()


def test_omit_fields_allowed_partial_layer(db_path: Path):
    store = ps.ProfileStore(db_path)
    try:
        rev = store.append_revision(
            ps.LAYER_RUN_OVERRIDE,
            "run-sparse",
            {"credential_ref": "env:OMP_CREDENTIAL_REF", "timeout_seconds": 60},
        )
        assert rev.fields.get("timeout_seconds") == 60
        assert "profile_id" not in rev.fields
    finally:
        store.close()
