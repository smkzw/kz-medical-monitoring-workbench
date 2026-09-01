"""Synthetic/offline project-open DTO, facade, and router boundary tests."""

from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
import sys

WORKBENCH_ROOT = Path(__file__).resolve().parents[3]
if str(WORKBENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_ROOT))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fixtures_schema_manifest import make_project
from mm_r7.project_lifecycle import (
    DATA_COVERAGE_COMPLETE,
    DATA_COVERAGE_INCOMPLETE,
    OPEN_MODE_BLOCKED,
    OPEN_MODE_EDIT,
    OPEN_MODE_READONLY,
    ProjectOpenResult,
    ProjectCompatibilityError,
    ProjectReadOnlyError,
    ProjectUpgradeProgress,
    ReadOnlyProjectView,
    inspect_project_schema,
    open_project_result,
    open_read_only_project_view,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from mm_r7.run_entry import MonitoringRunEntry, RunEntryError
from mm_r7.schema_manifest import SchemaClassification
from services.api.app.medical_monitoring_r7_product_router import (
    LEGACY_WORKFLOW_WRITE_ROUTES,
    R7_PRODUCT_PREFIX,
    create_medical_monitoring_r7_product_router,
)

def _workspace_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        if path.name.endswith(("-wal", "-shm", "-journal")):
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

_WRITER_CLASS_SOURCES = {
    "Store": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py",
        {
            "append_audit",
            "create_project",
            "add_source_revision",
            "add_listing_snapshot",
            "transition_snapshot_acceptance",
            "set_acceptance_ambiguity",
            "clear_acceptance_ambiguity",
            "create_run",
            "update_run_state",
            "complete_analysis",
            "publish",
            "set_manifest",
            "begin_work_unit",
            "bind_capability_attempt_to_work_unit",
            "complete_work_unit",
            "complete_capability_work_unit",
            "begin_node_run",
            "complete_node_run",
            "recover_expired_capability_attempts",
            "stage_artifact",
            "commit_artifact",
            "commit_facts",
            "put_domain_object",
            "save_checkpoint",
            "recover",
            "cleanup_orphan_artifacts",
        },
    ),
    "ProfileStore": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r7/src/mm_r7/profile_store.py",
        {
            "open",
            "reopen",
            "append_revision",
            "append_layer",
            "seed_builtin_global_default",
            "seed_deepseek_capability_layer",
        },
    ),
    "RunBindingStore": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r7/src/mm_r7/run_binding.py",
        {"open", "reopen", "bind"},
    ),
    "LaunchRegistry": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py",
        {
            "open",
            "reopen",
            "reserve",
            "reserve_publication",
            "bind_publication_runtime_manifest",
            "record_publication_failure",
            "retry_publication",
            "update_publication_state",
            "finalize_publication",
            "save_continuity_plan",
            "update_continuity_plan_status",
            "publish_continuity_plan",
            "set_run_state",
            "update_state",
            "mark_waiting_start",
            "mark_running",
            "mark_started",
            "mark_completed",
            "mark_failed",
            "record_start_failure",
            "record_manifest",
        },
    ),
    "RiskRuleRegistry": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r7/src/mm_r7/run_setup.py",
        {"append_revision"},
    ),
}

_BACKGROUND_WRITER_SOURCES = {
    "BackgroundProgressFacade": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r1/src/mm_r1/background_progress.py",
        {"_work", "_sweep", "_process", "_process_locked"},
    ),
    "BackgroundRecoveryAdapter": (
        WORKBENCH_ROOT / "poc/medical_monitoring_ai_native_r7/src/mm_r7/background_recovery.py",
        {"_worker_main_locked", "_worker_main", "_process_unit", "_process_ai_unit"},
    ),
}


def _source_class_method_names(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return {
        node.name
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("__")
    }


def _source_snapshot() -> dict[tuple[str, str], tuple[str, tuple[str, ...]]]:
    snapshot: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {}
    for class_name, (path, _) in _WRITER_CLASS_SOURCES.items():
        snapshot[(class_name, str(path))] = (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            tuple(sorted(_source_class_method_names(path, class_name))),
        )
    for class_name, (path, _) in _BACKGROUND_WRITER_SOURCES.items():
        snapshot[(class_name, str(path))] = (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            tuple(sorted(_source_class_method_names(path, class_name))),
        )
    return snapshot


def _source_writer_names(
    sources: dict[str, tuple[Path, set[str]]],
) -> set[str]:
    return {
        method
        for class_name, (path, expected) in sources.items()
        for method in _source_class_method_names(path, class_name)
        if method in expected
    }


def _source_background_writer_names() -> set[str]:
    return {
        method
        for class_name, (path, expected) in _BACKGROUND_WRITER_SOURCES.items()
        for method in _source_class_method_names(path, class_name)
        if method in expected
    }


def _source_writer_methods_snapshot() -> dict[str, tuple[str, ...]]:
    return {
        class_name: tuple(
            sorted(
                method
                for method in _source_class_method_names(path, class_name)
                if method in expected
            )
        )
        for class_name, (path, expected) in _WRITER_CLASS_SOURCES.items()
    }


def _source_background_methods_snapshot() -> dict[str, tuple[str, ...]]:
    return {
        class_name: tuple(
            sorted(
                method
                for method in _source_class_method_names(path, class_name)
                if method in expected
            )
        )
        for class_name, (path, expected) in _BACKGROUND_WRITER_SOURCES.items()
    }


def test_legacy_facade_mutation_surface_is_source_derived_and_write_free(
    tmp_path: Path,
) -> None:
    source_before = _source_snapshot()
    assert _source_writer_methods_snapshot() == {
        class_name: tuple(sorted(expected))
        for class_name, (_, expected) in _WRITER_CLASS_SOURCES.items()
    }
    assert _source_background_methods_snapshot() == {
        class_name: tuple(sorted(expected))
        for class_name, (_, expected) in _BACKGROUND_WRITER_SOURCES.items()
    }

    workspace = make_project(tmp_path / "legacy", runtime_version="5")
    before = _workspace_digest(workspace)
    with open_read_only_project_view(workspace) as view:
        source_writer_names = _source_writer_names(_WRITER_CLASS_SOURCES)
        background_writer_names = _source_background_writer_names()
        for method in source_writer_names | background_writer_names:
            candidate = getattr(view, method, None)
            if candidate is None:
                continue
            assert getattr(candidate, "__func__", None) is ReadOnlyProjectView._reject_write
            with pytest.raises(ProjectReadOnlyError):
                candidate()

        for method, args in (
            ("append_revision", (workspace,)),
            ("bind", ("run-1",)),
            ("reserve", ("run-1",)),
            ("update_state", ("run-1",)),
        ):
            with pytest.raises(ProjectReadOnlyError):
                getattr(view, method)(*args)
    assert _workspace_digest(workspace) == before
    assert _source_snapshot() == source_before



@pytest.mark.parametrize(
    "named_state",
    (
        "current",
        "legacy_complete",
        "legacy_required_missing",
        "future",
        "marker3",
        "corrupt",
        "upgrade_in_progress",
        "upgrade_rolled_back",
        "upgrade_unresolved",
    ),
)
def test_named_dto_acceptance_matrix_is_explicit_and_closed(
    tmp_path: Path,
    named_state: str,
) -> None:
    if named_state in {
        "upgrade_in_progress",
        "upgrade_rolled_back",
        "upgrade_unresolved",
    }:
        if named_state == "upgrade_in_progress":
            body = upgrade_progress_from_operation(
                SimpleNamespace(status="migrating", progress_percent=72)
            ).as_dict()
            assert body["state"] == "upgrading"
            assert set(body) == {"state", "phaseLabel", "percent", "message"}
        else:
            source_state = {
                "upgrade_rolled_back": "rolled_back",
                "upgrade_unresolved": "retained_for_triage",
            }[named_state]
            body = upgrade_result_from_state(source_state).as_dict()
            expected = {
                "upgrade_rolled_back": (
                    "rolled_back",
                    OPEN_MODE_READONLY,
                    DATA_COVERAGE_COMPLETE,
                    True,
                    False,
                ),
                "upgrade_unresolved": (
                    "unresolved",
                    OPEN_MODE_BLOCKED,
                    DATA_COVERAGE_INCOMPLETE,
                    False,
                    False,
                ),
            }[named_state]
            assert (
                body["state"],
                body["openMode"],
                body["dataCoverage"],
                body["canView"],
                body["canEdit"],
            ) == expected
            assert set(body) == {
                "state",
                "openMode",
                "dataCoverage",
                "canView",
                "canEdit",
                "requiresReopen",
                "message",
                "nextAction",
            }
    else:
        workspace = make_project(
            tmp_path / named_state,
            runtime_version="5" if named_state != "current" else "6",
        )
        if named_state == "legacy_required_missing":
            (workspace / "monitoring_run_bindings.sqlite3").unlink()
        elif named_state in {"future", "marker3"}:
            marker = "99" if named_state == "future" else "3"
            with sqlite3.connect(
                workspace / "runtime" / "monitoring_runtime.sqlite3"
            ) as connection:
                connection.execute(
                    "UPDATE meta SET value=? WHERE key='schema_version'",
                    (marker,),
                )
                connection.commit()
        elif named_state == "corrupt":
            with sqlite3.connect(workspace / "execution_profiles.sqlite3") as connection:
                connection.execute(
                    "ALTER TABLE profile_layer_versions ADD COLUMN drift TEXT"
                )
                connection.commit()
        body = open_project_result(inspect_project_schema(workspace)).as_dict()
        expected = {
            "current": ("current", OPEN_MODE_EDIT, DATA_COVERAGE_COMPLETE, True, True),
            "legacy_complete": (
                "legacy_readonly",
                OPEN_MODE_READONLY,
                DATA_COVERAGE_COMPLETE,
                True,
                False,
            ),
            "legacy_required_missing": (
                "blocked",
                OPEN_MODE_BLOCKED,
                DATA_COVERAGE_INCOMPLETE,
                False,
                False,
            ),
            "future": (
                "blocked",
                OPEN_MODE_BLOCKED,
                DATA_COVERAGE_INCOMPLETE,
                False,
                False,
            ),
            "marker3": (
                "blocked",
                OPEN_MODE_BLOCKED,
                DATA_COVERAGE_INCOMPLETE,
                False,
                False,
            ),
            "corrupt": (
                "blocked",
                OPEN_MODE_BLOCKED,
                DATA_COVERAGE_INCOMPLETE,
                False,
                False,
            ),
        }[named_state]
        assert (
            body["state"],
            body["openMode"],
            body["dataCoverage"],
            body["canView"],
            body["canEdit"],
        ) == expected
        assert set(body) == {
            "state",
            "openMode",
            "dataCoverage",
            "canView",
            "canEdit",
            "message",
            "nextAction",
        }

    blob = json.dumps(body, ensure_ascii=False).casefold()
    assert "limited" not in blob
    assert "operation" not in blob
    assert "medical data" not in blob
    assert "原始医学记录" not in blob

def test_product_dtos_have_fixed_clean_keys_and_deterministic_bytes() -> None:
    opening = ProjectOpenResult(
        state="current",
        open_mode=OPEN_MODE_EDIT,
        data_coverage=DATA_COVERAGE_COMPLETE,
        can_view=True,
        can_edit=True,
        message="项目格式正常，可以继续使用。",
        next_action="继续使用项目",
    )
    progress = ProjectUpgradeProgress(
        state="verifying",
        phase_label="正在检查升级结果",
        percent=86,
        message="正在检查升级结果，完成后可重新打开项目。",
    )
    result = upgrade_result_from_state("completed")

    assert set(opening.as_dict()) == {
        "state",
        "openMode",
        "dataCoverage",
        "canView",
        "canEdit",
        "message",
        "nextAction",
    }
    assert set(progress.as_dict()) == {
        "state",
        "phaseLabel",
        "percent",
        "message",
    }
    assert set(result.as_dict()) == {
        "state",
        "openMode",
        "dataCoverage",
        "canView",
        "canEdit",
        "requiresReopen",
        "message",
        "nextAction",
    }
    assert result.as_dict()["requiresReopen"] is True
    first = hashlib.sha256(_canonical_json(result.as_dict())).hexdigest()
    second = hashlib.sha256(_canonical_json(result.as_dict())).hexdigest()
    assert first == second

    with pytest.raises(ValueError):
        ProjectOpenResult(
            state="current",
            open_mode=OPEN_MODE_EDIT,
            data_coverage=DATA_COVERAGE_COMPLETE,
            can_view=True,
            can_edit=True,
            message="项目格式正常，可以继续使用。",
            next_action="limited supportCode operation_id",
        )

    with pytest.raises(ValueError):
        ProjectUpgradeProgress(
            state="verifying",
            phase_label="sqlite schema operation_id",
            percent=86,
            message="正在检查升级结果。",
        )


def test_supported_legacy_is_complete_readonly_and_write_free(tmp_path: Path) -> None:
    workspace = make_project(tmp_path / "legacy", runtime_version="5")
    inspection = inspect_project_schema(workspace)
    assert inspection.classification is SchemaClassification.LEGACY

    opening = open_project_result(inspection)
    assert opening.open_mode == OPEN_MODE_READONLY
    assert opening.data_coverage == DATA_COVERAGE_COMPLETE
    assert opening.can_view is True
    assert opening.can_edit is False

    before = _workspace_digest(workspace)
    with open_read_only_project_view(workspace, inspection=inspection) as view:
        assert isinstance(view, ReadOnlyProjectView)
        assert view.read_only is True
        assert view.can_view is True
        assert view.can_edit is False
        assert not hasattr(view, "store")
        assert not hasattr(view, "profile_store")
        assert not hasattr(view, "run_binding_store")
        assert view.list_execution_profiles() == ()
        assert view.list_run_bindings() == ()
        with pytest.raises(ProjectReadOnlyError):
            view.append_revision(workspace)
        with pytest.raises(ProjectReadOnlyError):
            view.bind_run("run-1")
    assert _workspace_digest(workspace) == before

    with pytest.raises(RunEntryError) as exc_info:
        MonitoringRunEntry(workspace)
    assert exc_info.value.code == "project_read_only"
    assert _workspace_digest(workspace) == before


def test_marker_three_future_and_corrupt_projects_are_blocked_distinctly(
    tmp_path: Path,
) -> None:
    marker_three = make_project(tmp_path / "marker-three", runtime_version="5")
    runtime_path = marker_three / "runtime" / "monitoring_runtime.sqlite3"
    with sqlite3.connect(runtime_path) as connection:
        connection.execute(
            "UPDATE meta SET value='3' WHERE key='schema_version'"
        )
        connection.commit()
    marker_three_result = open_project_result(inspect_project_schema(marker_three))
    assert marker_three_result.open_mode == OPEN_MODE_BLOCKED
    assert "较早" in marker_three_result.message

    future = make_project(tmp_path / "future", runtime_version="5")
    runtime_path = future / "runtime" / "monitoring_runtime.sqlite3"
    with sqlite3.connect(runtime_path) as connection:
        connection.execute(
            "UPDATE meta SET value='99' WHERE key='schema_version'"
        )
        connection.commit()
    future_result = open_project_result(inspect_project_schema(future))
    assert future_result.open_mode == OPEN_MODE_BLOCKED
    assert "更新版本" in future_result.message

    corrupt = make_project(tmp_path / "corrupt", runtime_version="5")
    with sqlite3.connect(
        corrupt / "execution_profiles.sqlite3"
    ) as connection:
        connection.execute(
            "ALTER TABLE profile_layer_versions ADD COLUMN drift TEXT"
        )
        connection.commit()
    corrupt_result = open_project_result(inspect_project_schema(corrupt))
    assert corrupt_result.open_mode == OPEN_MODE_BLOCKED
    assert "安全打开" in corrupt_result.message


def test_progress_states_and_failure_results_do_not_leak_internal_fields() -> None:
    expected = {
        "inspecting": ("preparing", 12),
        "migrating": ("upgrading", 72),
        "staged_verified": ("verifying", 86),
        "rollback_in_progress": ("restoring", 86),
        "rolled_back": ("restoring", 86),
    }
    for status, (public_state, percent) in expected.items():
        dto = upgrade_progress_from_operation(
            SimpleNamespace(status=status, progress_percent=86)
        )
        body = dto.as_dict()
        assert body["state"] == public_state
        assert body["percent"] == percent
        assert set(body) == {"state", "phaseLabel", "percent", "message"}
        assert "operation" not in json.dumps(body, ensure_ascii=False)

    inconsistent = upgrade_progress_from_operation(
        SimpleNamespace(status="inspecting", progress_percent=100)
    )
    assert inconsistent.percent == 12
    restoring = upgrade_progress_from_operation(
        SimpleNamespace(status="rolling_back", progress_percent=100)
    )
    assert restoring.percent == 94
    unknown = upgrade_progress_from_operation(
        SimpleNamespace(status="unrecognized", progress_percent=100)
    )
    assert unknown.percent is None

    rolled_back = upgrade_result_from_state("rolled_back").as_dict()
    unresolved = upgrade_result_from_state("retained_for_triage").as_dict()
    assert rolled_back["openMode"] == OPEN_MODE_READONLY
    assert rolled_back["dataCoverage"] == DATA_COVERAGE_COMPLETE
    assert unresolved["openMode"] == OPEN_MODE_BLOCKED
    assert unresolved["dataCoverage"] == DATA_COVERAGE_INCOMPLETE
    assert rolled_back["requiresReopen"] is False
    assert unresolved["requiresReopen"] is False


def test_product_router_opens_legacy_readonly_and_blocks_writes(tmp_path: Path) -> None:
    workspace = make_project(tmp_path / "medical_monitoring_r7" / "legacy", runtime_version="5")
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    before = _workspace_digest(workspace)
    with TestClient(app) as client:
        opened = client.get(f"{base}/project/open")
        assert opened.status_code == 200
        assert opened.json()["openMode"] == OPEN_MODE_READONLY
        assert opened.json()["dataCoverage"] == DATA_COVERAGE_COMPLETE

        upgrade = client.post(
            f"{base}/project/upgrade",
            json={"confirmation": False, "idempotency_key": "legacy-check"},
        )
        assert upgrade.status_code == 200
        assert upgrade.json()["state"] == "legacy_readonly"
        assert "operation_id" not in upgrade.text

        blocked = client.post(
            f"{base}/execution-profiles/project/legacy",
            json={"fields": {"reasoning_effort": "high"}},
        )
        assert blocked.status_code == 409
        assert blocked.json()["code"] == "project_read_only"
    assert _workspace_digest(workspace) == before


def test_legacy_get_routes_use_readonly_facade_without_optional_db_creation(
    tmp_path: Path,
) -> None:
    workspace = make_project(
        tmp_path / "medical_monitoring_r7" / "legacy",
        runtime_version="5",
    )
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    risk_path = workspace / "risk_rules.sqlite3"
    launch_path = workspace / "launch_registry.sqlite3"
    before = _workspace_digest(workspace)
    with TestClient(app) as client:
        setup = client.get(f"{base}/run-setup/options")
        assert setup.status_code == 200, setup.text
        assert setup.json()["rule_revisions"] == []

        rules = client.get(f"{base}/risk-rules")
        assert rules.status_code == 200, rules.text
        assert rules.json()["rule_revisions"] == []

        history = client.get(f"{base}/runs")
        assert history.status_code == 200, history.text
        assert history.json() == {"runs": []}

        missing_profile = client.get(
            f"{base}/execution-profiles/project/legacy"
        )
        assert missing_profile.status_code == 404
        assert missing_profile.json()["code"] == "profile_layer_not_found"

        missing_run = client.get(f"{base}/runs/run-1")
        assert missing_run.status_code == 404
        assert missing_run.json()["code"] == "run_binding_not_found"

        missing_progress = client.get(f"{base}/runs/run-1/progress")
        assert missing_progress.status_code == 404
        assert missing_progress.json()["code"] == "run_binding_not_found"

        missing_publication = client.get(
            f"{base}/runs/run:missing/publication"
        )
        assert missing_publication.status_code == 404
        assert missing_publication.json()["code"] == "public_run_not_found"
        missing_result_entry = client.get(
            f"{base}/runs/run:missing/result-entry"
        )
        assert missing_result_entry.status_code == 404
        assert missing_result_entry.json()["code"] == "public_run_not_found"

        missing_result = client.get(
            f"{base}/results/result-context-missing/overview"
        )
        assert missing_result.status_code == 409
        assert missing_result.json()["code"] == "result_context_unavailable"

    assert not risk_path.exists()
    assert not launch_path.exists()
    assert _workspace_digest(workspace) == before

def test_legacy_identity_drift_blocks_open_and_read_routes(tmp_path: Path) -> None:
    workspace = make_project(
        tmp_path / "medical_monitoring_r7" / "legacy",
        runtime_version="5",
    )
    with sqlite3.connect(workspace / "runtime" / "monitoring_runtime.sqlite3") as connection:
        connection.execute(
            "INSERT INTO projects(project_id,name,is_synthetic,config_json,created_at) "
            "VALUES (?,?,?,?,?)",
            ("other-project", "错误项目", 1, "{}", "2026-08-30"),
        )
        connection.commit()

    with pytest.raises(ProjectCompatibilityError):
        open_read_only_project_view(workspace)

    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    with TestClient(app) as client:
        opened = client.get(f"{base}/project/open")
        assert opened.status_code == 200
        assert opened.json()["openMode"] == OPEN_MODE_BLOCKED
        history = client.get(f"{base}/runs")
        assert history.status_code == 409
        assert history.json()["code"] == "project_open_blocked"


def test_product_router_upgrade_success_requires_reopen(tmp_path: Path) -> None:
    workspace = make_project(
        tmp_path / "medical_monitoring_r7" / "legacy",
        runtime_version="5",
    )
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
            maintenance_wait_seconds=2.0,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    with TestClient(app) as client:
        upgraded = client.post(
            f"{base}/project/upgrade",
            json={"confirmation": True, "idempotency_key": "upgrade-1"},
        )
        assert upgraded.status_code == 200, upgraded.text
        body = upgraded.json()
        assert body["state"] == "succeeded"
        assert body["openMode"] == OPEN_MODE_EDIT
        assert body["dataCoverage"] == DATA_COVERAGE_COMPLETE
        assert body["canEdit"] is True
        assert body["requiresReopen"] is True
        assert "operation_id" not in upgraded.text

        reopened = client.get(f"{base}/project/open")
        assert reopened.status_code == 200
        assert reopened.json()["state"] == "current"
        assert reopened.json()["openMode"] == OPEN_MODE_EDIT
        assert reopened.json()["canEdit"] is True

    assert inspect_project_schema(workspace).classification is SchemaClassification.CURRENT


@pytest.mark.parametrize(
    "write_path",
    (
        "/workspace/bootstrap",
        "/risk-rules/preview",
        "/risk-rules",
        "/execution-profiles/project/legacy",
        "/runs/prepare-and-start",
        "/runs",
        "/runs/run-1/execution/prepare",
        "/runs/run-1/execution/start",
        "/runs/run-1/execution/resume",
        "/runs/run-1/execution/cancel",
        "/runs/public-token/publication",
    ),
)
def test_all_product_write_routes_block_supported_legacy(
    tmp_path: Path,
    write_path: str,
) -> None:
    workspace = make_project(
        tmp_path / "medical_monitoring_r7" / "legacy",
        runtime_version="5",
    )
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    before = _workspace_digest(workspace)
    with TestClient(app) as client:
        response = client.post(f"{base}{write_path}", json={})
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "project_read_only"
    assert _workspace_digest(workspace) == before


def test_legacy_workflow_write_allowlist_is_positive_and_scoped(
    tmp_path: Path,
) -> None:
    workspace = make_project(
        tmp_path / "medical_monitoring_r7" / "legacy",
        runtime_version="5",
    )
    assert LEGACY_WORKFLOW_WRITE_ROUTES == {
        "/project/upgrade",
        "/backups",
        "/restores/preflight",
        "/restores",
    }
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=tmp_path,
            require_server_principal=False,
        )
    )
    base = R7_PRODUCT_PREFIX.format(project_id="legacy")
    before = _workspace_digest(workspace)
    with TestClient(app) as client:
        upgrade = client.post(
            f"{base}/project/upgrade",
            json={"confirmation": False, "idempotency_key": "allowlist-upgrade"},
        )
        assert upgrade.status_code == 200
        assert upgrade.json()["state"] == "legacy_readonly"

        backup = client.post(
            f"{base}/backups",
            json={"idempotency_key": "allowlist-backup"},
        )
        assert backup.status_code == 200, backup.text
        assert "status_label" in backup.json()

        preflight = client.post(f"{base}/restores/preflight", json={})
        assert preflight.status_code == 422
        assert preflight.json()["code"] == "request_validation_failed"

        restore = client.post(f"{base}/restores", json={})
        assert restore.status_code == 422
        assert restore.json()["code"] == "request_validation_failed"

        ordinary = client.post(f"{base}/risk-rules", json={})
        assert ordinary.status_code == 409
        assert ordinary.json()["code"] == "project_read_only"
    assert _workspace_digest(workspace) == before
