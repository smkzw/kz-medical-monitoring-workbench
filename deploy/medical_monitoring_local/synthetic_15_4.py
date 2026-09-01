#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G4 System Design §15.4 合成离线编排与 canonical replay。

只调用或验证已接受的 R7 09A/09B/09E 公共入口，输出固定十三项顺序的 evidence
manifest。不复制备份/迁移/回滚状态机，不启动服务、不调用模型、不读取真实项目。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from canonical_evidence import digest_ref

SECTION_15_4_SCHEMA = "mm-monitoring-r8-g4-synthetic-15-4-v1"
SECTION_15_4_VERSION = "1"
CONTRACT_REF = "medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1"
ADAPTER_ID = "synthetic-15-4-orchestrator"
ADAPTER_VERSION = "1"

FROZEN_FAULT_POINT = "migration.runtime.marker.before"
FROZEN_ROLLBACK_FAULT_POINT = "migration.switch.staging_to_live.before"

RESULT_PASSED = "passed"
RESULT_FAILED = "failed"
RESULT_NOT_EVALUABLE = "not_evaluable"
ALLOWED_RESULTS = frozenset({RESULT_PASSED, RESULT_FAILED, RESULT_NOT_EVALUABLE})

DEPLOY_DIR = Path(__file__).resolve().parent
WORKBENCH_ROOT = DEPLOY_DIR.parents[1]
_R7_SRC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "src"
_R7_TESTS = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "tests"

ITEM_SPECS: Tuple[Dict[str, Any], ...] = (
    {"index": 1, "key": "export_import", "title": "导出/导入"},
    {"index": 2, "key": "manifest_identity_lineage", "title": "manifest/identity/lineage"},
    {"index": 3, "key": "backup_corruption", "title": "备份损坏"},
    {"index": 4, "key": "clean_restore", "title": "干净恢复"},
    {"index": 5, "key": "pre_upgrade_protection", "title": "升级前保护"},
    {"index": 6, "key": "migration_success", "title": "迁移成功"},
    {"index": 7, "key": "critical_boundary_failure", "title": "关键边界失败"},
    {"index": 8, "key": "original_version_usable", "title": "原版本保持可用"},
    {"index": 9, "key": "actual_rollback", "title": "实际 rollback"},
    {"index": 10, "key": "credentials_not_exported_plaintext", "title": "凭据不明文导出"},
    {"index": 11, "key": "default_uninstall_retains_data", "title": "默认卸载保留数据"},
    {"index": 12, "key": "explicit_clear_preview_confirm_cancel", "title": "显式清除预览/确认/取消"},
    {"index": 13, "key": "mixed_version_late_callback_fence", "title": "混合版本与迟到回调"},
)

_PATH_FORBIDDEN = re.compile(
    r"(/Users/|/tmp/|/var/|/home/|/private/|\.mmbackup|\.sqlite3|[A-Za-z]:\\)"
)

_CREDENTIAL_FIELD_RE = re.compile(
    r'"(credential_value|password|secret|api_key|private_key)"\s*:',
    re.IGNORECASE,
)
_ENV_MEMBER_RE = re.compile(r"(^|/)\.env(\.|/|$)")
_SYNTHETIC_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class Section154Error(ValueError):
    """§15.4 合成证据、编排或 replay 无效。"""


@dataclass(frozen=True)
class ReplayResult:
    valid: bool
    status: Optional[str] = None
    errors: Tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "status": self.status,
            "errors": list(self.errors),
        }


def _copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Section154Error("%s_must_be_object" % field)
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Section154Error("%s_must_be_non_empty_string" % field)
    return value.strip()


def _sanitize_summary(text: str) -> str:
    normalized = _require_string(text, "summary")
    if _PATH_FORBIDDEN.search(normalized):
        raise Section154Error("summary_contains_path")
    return normalized


def _ensure_r7_path() -> None:
    candidates = (
        DEPLOY_DIR,
        _R7_SRC,
        _R7_TESTS,
        *(
            WORKBENCH_ROOT / "poc" / f"medical_monitoring_ai_native_{rev}" / "src"
            for rev in ("r6", "r5", "r4", "r3", "r3_rule_ai", "r2", "r1")
        ),
    )
    for root in candidates:
        path = str(root)
        if root.exists() and path not in sys.path:
            sys.path.insert(0, path)


def _mark_synthetic_root(root: Path) -> None:
    resolved = root.expanduser().resolve()
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    if resolved in temp_roots:
        raise Section154Error("runtime_root_must_be_temp_child")
    if not any(resolved.is_relative_to(temp_root) for temp_root in temp_roots):
        raise Section154Error("runtime_root_not_temporary")
    root = resolved
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".mm_r7_synthetic"
    if not marker.is_file():
        marker.write_text("synthetic/offline\n", encoding="utf-8")


def _normalize_synthetic_project_id(value: str) -> str:
    project_id = _require_string(value, "project_id")
    if not _SYNTHETIC_PROJECT_ID_RE.fullmatch(project_id):
        raise Section154Error("project_id_not_synthetic_safe")
    return project_id


def _item_body(
    spec: Mapping[str, Any],
    result: str,
    *,
    evidence_ref: str,
    summary: str,
) -> Dict[str, Any]:
    if result not in ALLOWED_RESULTS:
        raise Section154Error("invalid_result:%s" % result)
    body = {
        "index": int(spec["index"]),
        "key": _require_string(spec["key"], "key"),
        "title": _require_string(spec["title"], "title"),
        "result": result,
        "evidence_ref": _require_string(evidence_ref, "evidence_ref"),
        "summary": _sanitize_summary(summary),
    }
    digest_input = {
        "index": body["index"],
        "key": body["key"],
        "result": body["result"],
        "evidence_ref": body["evidence_ref"],
        "summary": body["summary"],
    }
    body["item_digest"] = digest_ref(digest_input)
    return body


def _passed(spec: Mapping[str, Any], evidence_ref: str, summary: str) -> Dict[str, Any]:
    return _item_body(spec, RESULT_PASSED, evidence_ref=evidence_ref, summary=summary)


def _failed(spec: Mapping[str, Any], evidence_ref: str, summary: str) -> Dict[str, Any]:
    return _item_body(spec, RESULT_FAILED, evidence_ref=evidence_ref, summary=summary)


def _spec(key: str) -> Dict[str, Any]:
    for row in ITEM_SPECS:
        if row["key"] == key:
            return dict(row)
    raise Section154Error("unknown_item_key:%s" % key)


def _make_distribution_root(root: Path) -> Any:
    import manage as manage_mod  # noqa: WPS433

    frontend = root / "frontend"
    data_dir = root / "data"
    (frontend / "node_modules").mkdir(parents=True)
    data_dir.mkdir(parents=True)
    (frontend / "package.json").write_text(
        json.dumps({"name": "mm-frontend-synthetic", "private": True}, ensure_ascii=False),
        encoding="utf-8",
    )
    runtime = {
        "schema": manage_mod.RUNTIME_SCHEMA,
        "product_name": "医学监查工作台",
        "data_dir": str(data_dir),
    }
    (root / manage_mod.RUNTIME_CONFIG_NAME).write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manage_mod.resolve_paths(root)


def _workspace_fingerprint(runtime_root: Path, project_id: str) -> str:
    from mm_r7.project_backup import ProjectBackupManager  # noqa: WPS433

    manager = ProjectBackupManager(runtime_root, project_id, wait_seconds=0.0)
    try:
        return manager.snapshot_workspace("154-fingerprint").fingerprint
    finally:
        manager.ledger.close()


def _scan_package_for_credential_leaks(package_path: Path) -> Tuple[bool, str]:
    from mm_r7.profile_store import assert_projection_has_no_credential_values  # noqa: WPS433

    with zipfile.ZipFile(package_path, "r") as archive:
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            if _ENV_MEMBER_RE.search(name):
                return False, "env_member_present"
            if info.is_dir():
                continue
            payload = archive.read(info)
            if name.endswith("manifest.json"):
                manifest = json.loads(payload.decode("utf-8"))
                assert_projection_has_no_credential_values(manifest)
                if isinstance(manifest.get("project_summary"), Mapping):
                    assert_projection_has_no_credential_values(manifest["project_summary"])
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if _CREDENTIAL_FIELD_RE.search(text):
                return False, "credential_field_in_member"
            if re.search(r"\bsk-[A-Za-z0-9]{8,}\b", text):
                return False, "secret_like_value"
    return True, "clean"


def _check_export_import(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("export_import")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.project_backup import (  # noqa: WPS433
        ProjectBackupManager,
        STATUS_AVAILABLE,
        STATUS_COMPLETED,
    )

    source_root = root / "item01-source"
    clean_root = root / "item01-clean"
    _mark_synthetic_root(source_root)
    _mark_synthetic_root(clean_root)
    make_project(source_root / project_id, runtime_version="6")
    source_fp = _workspace_fingerprint(source_root, project_id)

    source_mgr = ProjectBackupManager(source_root, project_id, wait_seconds=0.0)
    try:
        backup = source_mgr.backup("154-export")
        if backup.status != STATUS_AVAILABLE or backup.package_path is None:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.backup", "备份未完成")
        package = backup.package_path
    finally:
        source_mgr.ledger.close()

    target_mgr = ProjectBackupManager(clean_root, project_id, wait_seconds=0.0)
    try:
        preflight = target_mgr.preflight(package, "154-preflight")
        if preflight.manifest.get("source_workspace_fingerprint") != source_fp:
            return _failed(
                spec,
                "mm_r7.project_backup:PreflightResult.manifest",
                "备份 manifest 与导出前 lineage 不一致",
            )
        restored = target_mgr.restore(
            package,
            "154-restore",
            confirmation=True,
            preflight_result=preflight,
        )
        if restored.operation.status != STATUS_COMPLETED:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.restore", "恢复未完成")
        if not (clean_root / project_id).is_dir():
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.restore", "干净根无工作区")
    finally:
        target_mgr.ledger.close()

    return _passed(
        spec,
        "mm_r7.project_backup:ProjectBackupManager.backup+restore",
        "09A 确定性备份包导出并在干净合成根完成恢复",
    )


def _check_manifest_identity_lineage(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("manifest_identity_lineage")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.project_backup import ProjectBackupManager, STATUS_AVAILABLE  # noqa: WPS433

    case_root = root / "item02"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="6")
    live_fp = _workspace_fingerprint(case_root, project_id)

    manager = ProjectBackupManager(case_root, project_id, wait_seconds=0.0)
    try:
        backup = manager.backup("154-manifest")
        if backup.status != STATUS_AVAILABLE or backup.package_path is None:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.backup", "备份未完成")
        preflight = manager.preflight(backup.package_path, "154-manifest-preflight")
        manifest = dict(preflight.manifest)
        if manifest.get("canonical_project_id") != project_id:
            return _failed(spec, "mm_r7.project_backup:PreflightResult.manifest", "identity 不匹配")
        if manifest.get("source_workspace_fingerprint") != live_fp:
            return _failed(spec, "mm_r7.project_backup:PreflightResult.manifest", "lineage 指纹不匹配")
        if not isinstance(manifest.get("members"), list) or not manifest["members"]:
            return _failed(spec, "mm_r7.project_backup:PreflightResult.manifest", "manifest 成员缺失")
        replay = manager.preflight(backup.package_path, "154-manifest-replay")
        if replay.manifest.get("content_digest") != manifest.get("content_digest"):
            return _failed(spec, "mm_r7.project_backup:PreflightResult.manifest", "manifest 重放不一致")
    finally:
        manager.ledger.close()

    return _passed(
        spec,
        "mm_r7.project_backup:PreflightResult.manifest",
        "包 manifest、项目 identity 与来源恢复 lineage 可精确重放",
    )


def _check_backup_corruption(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("backup_corruption")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.project_backup import ProjectBackupError, ProjectBackupManager, STATUS_AVAILABLE  # noqa: WPS433

    case_root = root / "item03"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="6")
    before = _workspace_fingerprint(case_root, project_id)

    manager = ProjectBackupManager(case_root, project_id, wait_seconds=0.0)
    try:
        backup = manager.backup("154-corrupt-source")
        if backup.status != STATUS_AVAILABLE or backup.package_path is None:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.backup", "备份未完成")
        entries: List[Tuple[zipfile.ZipInfo, bytes]] = []
        with zipfile.ZipFile(backup.package_path, "r") as archive:
            for info in archive.infolist():
                data = archive.read(info)
                if info.filename == "manifest.json":
                    data = data[:-1]
                entries.append((info, data))
        broken = case_root / "broken.mmbackup"
        with zipfile.ZipFile(broken, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for info, data in entries:
                out.writestr(info, data)
        try:
            manager.preflight(broken, "154-corrupt-preflight")
        except ProjectBackupError as exc:
            if _workspace_fingerprint(case_root, project_id) != before:
                return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.preflight", "live 工作区被切换")
            if exc.code not in {"package_corrupt", "manifest_semantic_mismatch"}:
                return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.preflight", "错误码不符合预期")
        else:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.preflight", "损坏包未被拒绝")
    finally:
        manager.ledger.close()

    return _passed(
        spec,
        "mm_r7.project_backup:ProjectBackupManager.preflight",
        "成员或 manifest 损坏被拒绝且 live workspace 未切换",
    )


def _check_clean_restore(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("clean_restore")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.project_backup import ProjectBackupManager, STATUS_AVAILABLE, STATUS_COMPLETED  # noqa: WPS433
    from mm_r7.project_verifier import ProjectVerifier, RESULT_RECORD_COMPLETE  # noqa: WPS433

    source_root = root / "item04-source"
    target_root = root / "item04-target"
    _mark_synthetic_root(source_root)
    _mark_synthetic_root(target_root)
    make_project(source_root / project_id, runtime_version="6")

    source_mgr = ProjectBackupManager(source_root, project_id, wait_seconds=0.0)
    try:
        backup = source_mgr.backup("154-clean-source")
        if backup.status != STATUS_AVAILABLE or backup.package_path is None:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.backup", "备份未完成")
        package = backup.package_path
    finally:
        source_mgr.ledger.close()

    target_mgr = ProjectBackupManager(target_root, project_id, wait_seconds=0.0)
    try:
        preflight = target_mgr.preflight(package, "154-clean-preflight")
        restored = target_mgr.restore(
            package,
            "154-clean-restore",
            confirmation=True,
            preflight_result=preflight,
        )
        if restored.operation.status != STATUS_COMPLETED:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.restore", "恢复未完成")
    finally:
        target_mgr.ledger.close()

    with ProjectVerifier(target_root, project_id) as verifier:
        result = verifier.verify()
    if result.result != RESULT_RECORD_COMPLETE:
        return _failed(spec, "mm_r7.project_verifier:ProjectVerifier.verify", "verifier 未给出记录完整")

    return _passed(
        spec,
        "mm_r7.project_verifier:ProjectVerifier.verify",
        "干净根恢复后由既有 verifier 与 manifest 证明一致",
    )


def _check_pre_upgrade_protection(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("pre_upgrade_protection")
    import distribution as dist  # noqa: WPS433
    from fixtures_schema_manifest import make_project  # noqa: WPS433

    case_root = root / "item05"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="5")
    before = _workspace_fingerprint(case_root, project_id)
    os.environ["MM_09E_ACCEPTANCE_RUNNER"] = "1"
    try:
        code = dist.prepare_upgrade_main(
            [
                "--runtime-root",
                str(case_root),
                "--project-id",
                project_id,
                "--idempotency-key",
                "154-prepare",
            ],
        )
        if code != dist.EXIT_OK:
            return _failed(spec, "distribution:prepare_upgrade_main", "升级准备未成功")
        packages = list(case_root.rglob("*.mmbackup"))
        if not packages:
            return _failed(spec, "distribution:prepare_upgrade_main", "未生成保护备份")
        if _workspace_fingerprint(case_root, project_id) != before:
            return _failed(spec, "distribution:prepare_upgrade_main", "升级准备改写了 live 数据")
        ok, detail = _scan_package_for_credential_leaks(packages[0])
        if not ok:
            return _failed(spec, "distribution:prepare_upgrade_main", "保护备份扫描失败:" + detail)
    finally:
        os.environ.pop("MM_09E_ACCEPTANCE_RUNNER", None)

    return _passed(
        spec,
        "distribution:prepare_upgrade_main",
        "09E prepare-upgrade 先生成可验证保护备份且未改写 live 数据",
    )


def _check_migration_success(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("migration_success")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.migration import MigrationRunner, STATUS_COMPLETED  # noqa: WPS433
    from mm_r7.schema_manifest import RUNTIME_V4  # noqa: WPS433

    case_root = root / "item06"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version=RUNTIME_V4)

    runner = MigrationRunner(case_root, project_id, wait_seconds=0.0)
    try:
        result = runner.start_upgrade("154-upgrade")
        if result.state != STATUS_COMPLETED:
            return _failed(spec, "mm_r7.migration:MigrationRunner.start_upgrade", "迁移未完成")
        inspection = runner.inspect()
        if inspection.classification.value != "current":
            return _failed(spec, "mm_r7.migration:MigrationRunner.inspect", "迁移后非 current")
        if inspection.members["runtime"].schema_version != "6":
            return _failed(spec, "mm_r7.migration:MigrationRunner.inspect", "runtime 未升到 current")
    finally:
        runner.close()

    return _passed(
        spec,
        "mm_r7.migration:MigrationRunner.start_upgrade",
        "09B legacy 合成 workspace 迁移到 current",
    )


def _check_critical_boundary_failure(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("critical_boundary_failure")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.migration import MigrationError, MigrationRunner, STATUS_RETRYABLE_FAILED  # noqa: WPS433

    case_root = root / "item07"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="5")

    def fail_once(point: str) -> None:
        if point == FROZEN_FAULT_POINT:
            raise RuntimeError("injected_fault")

    runner = MigrationRunner(case_root, project_id, failure_hook=fail_once, wait_seconds=0.0)
    try:
        try:
            runner.start_upgrade("154-fault")
        except MigrationError:
            pass
        else:
            return _failed(spec, "mm_r7.migration:MigrationRunner.start_upgrade", "边界失败未触发")
        records = runner.ledger.list_for_project(project_id)
        if not records:
            return _failed(spec, "mm_r7.migration:MigrationOperationLedger", "无操作记录")
        if records[-1].status != STATUS_RETRYABLE_FAILED:
            return _failed(spec, "mm_r7.migration:MigrationOperationLedger", "终态非 retryable_failed")
    finally:
        runner.close()

    return _passed(
        spec,
        "mm_r7.migration:MigrationRunner+failure_hook",
        "在冻结 fault point 注入失败并保留明确终态",
    )


def _check_original_version_usable(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("original_version_usable")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.migration import MigrationError, MigrationRunner  # noqa: WPS433
    from mm_r7.schema_manifest import SchemaClassification  # noqa: WPS433

    case_root = root / "item08"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="5")
    before = _workspace_fingerprint(case_root, project_id)

    def fail_once(point: str) -> None:
        if point == FROZEN_FAULT_POINT:
            raise RuntimeError("injected_fault")

    runner = MigrationRunner(case_root, project_id, failure_hook=fail_once, wait_seconds=0.0)
    try:
        try:
            runner.start_upgrade("154-open-after-fault")
        except MigrationError:
            pass
        opened = runner.open_project()
        if opened.classification is not SchemaClassification.LEGACY:
            return _failed(spec, "mm_r7.migration:MigrationRunner.open_project", "原版本不可打开")
        if _workspace_fingerprint(case_root, project_id) != before:
            return _failed(spec, "mm_r7.migration:MigrationRunner.open_project", "原 workspace 字节已变")
    finally:
        runner.close()

    return _passed(
        spec,
        "mm_r7.migration:MigrationRunner.open_project",
        "迁移边界失败后旧 workspace 仍可打开",
    )


def _check_actual_rollback(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("actual_rollback")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.migration import MigrationRunner, STATUS_ROLLED_BACK  # noqa: WPS433

    case_root = root / "item09"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="5")

    def fail_switch(point: str) -> None:
        if point == FROZEN_ROLLBACK_FAULT_POINT:
            raise RuntimeError("switch_fault")

    runner = MigrationRunner(case_root, project_id, failure_hook=fail_switch, wait_seconds=0.0)
    try:
        result = runner.start_upgrade("154-rollback")
        if result.state != STATUS_ROLLED_BACK:
            return _failed(spec, "mm_r7.migration:MigrationRunner.start_upgrade", "未进入 rolled_back")
        if runner.inspect().members["runtime"].schema_version != "5":
            return _failed(spec, "mm_r7.migration:MigrationRunner.inspect", "rollback 后 schema 未恢复")
        record = runner.ledger.list_for_project(project_id)[-1]
        if record.status != STATUS_ROLLED_BACK:
            return _failed(spec, "mm_r7.migration:MigrationOperationLedger", "ledger 仅标记未实回滚")
    finally:
        runner.close()

    return _passed(
        spec,
        "mm_r7.migration:MigrationRunner.start_upgrade",
        "09B 目录切换失败触发实际 rollback",
    )


def _check_credentials_not_exported_plaintext(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("credentials_not_exported_plaintext")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.project_backup import ProjectBackupManager, STATUS_AVAILABLE  # noqa: WPS433

    case_root = root / "item10"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="6")

    manager = ProjectBackupManager(case_root, project_id, wait_seconds=0.0)
    try:
        backup = manager.backup("154-credential-scan")
        if backup.status != STATUS_AVAILABLE or backup.package_path is None:
            return _failed(spec, "mm_r7.project_backup:ProjectBackupManager.backup", "备份未完成")
        ok, detail = _scan_package_for_credential_leaks(backup.package_path)
        if not ok:
            return _failed(spec, "mm_r7.profile_store:assert_projection_has_no_credential_values", detail)
    finally:
        manager.ledger.close()

    return _passed(
        spec,
        "mm_r7.profile_store:assert_projection_has_no_credential_values",
        "普通包成员与 manifest 扫描未发现凭据字段值或 env 成员",
    )


def _check_default_uninstall_retains_data(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("default_uninstall_retains_data")
    import distribution as dist  # noqa: WPS433

    case_root = root / "item11"
    _mark_synthetic_root(case_root)
    paths = _make_distribution_root(case_root)
    plan = dist.build_uninstall_plan(
        distribution_root=paths.root,
        data_dir=paths.data_dir,
        include_project_data=False,
    )
    if plan.get("disposition_mode") != "retain_project_data":
        return _failed(spec, "distribution:build_uninstall_plan", "默认模式非 retain")
    retained = {row.get("kind") for row in plan.get("retained_objects") or []}
    expected = {"project_data", "backups", "exports", "business_audit"}
    if not expected.issubset(retained):
        return _failed(spec, "distribution:build_uninstall_plan", "保留对象清单不完整")
    if plan.get("deletion_executed") is not False:
        return _failed(spec, "distribution:build_uninstall_plan", "预览不应执行删除")

    return _passed(
        spec,
        "distribution:build_uninstall_plan",
        "09E 默认 uninstall plan 明确保留项目数据、备份、导出与审计",
    )


def _check_explicit_clear_preview_confirm_cancel(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("explicit_clear_preview_confirm_cancel")
    import distribution as dist  # noqa: WPS433

    cancel_root = root / "item12-cancel"
    confirm_root = root / "item12-confirm"
    _mark_synthetic_root(cancel_root)
    _mark_synthetic_root(confirm_root)
    cancel_paths = _make_distribution_root(cancel_root)
    confirm_paths = _make_distribution_root(confirm_root)
    (cancel_paths.data_dir / "sentinel.bin").write_bytes(b"cancel")
    (confirm_paths.data_dir / "sentinel.bin").write_bytes(b"confirm")

    preview = dist.build_uninstall_plan(
        distribution_root=cancel_paths.root,
        data_dir=cancel_paths.data_dir,
        include_project_data=True,
    )
    if preview.get("disposition_mode") != "include_project_data":
        return _failed(spec, "distribution:build_uninstall_plan", "显式清除预览态不正确")
    if preview.get("deletion_executed") is not False or not cancel_paths.data_dir.exists():
        return _failed(spec, "distribution:build_uninstall_plan", "预览阶段改写了合成数据")

    cancelled = _apply_synthetic_clear(
        cancel_paths.root,
        cancel_paths.data_dir,
        preview,
        confirmed=False,
    )
    if cancelled != "cancelled" or not cancel_paths.data_dir.exists():
        return _failed(spec, "synthetic_15_4:_apply_synthetic_clear", "取消态未保留数据")

    confirm_plan = dist.build_uninstall_plan(
        distribution_root=confirm_paths.root,
        data_dir=confirm_paths.data_dir,
        include_project_data=True,
    )
    confirmed = _apply_synthetic_clear(
        confirm_paths.root,
        confirm_paths.data_dir,
        confirm_plan,
        confirmed=True,
    )
    if confirmed != "confirmed_and_cleared" or confirm_paths.data_dir.exists():
        return _failed(spec, "synthetic_15_4:_apply_synthetic_clear", "确认态未清除合成数据")

    return _passed(
        spec,
        "distribution:build_uninstall_plan",
        "preview、显式 confirm、cancel 三态均有证据且仅在临时合成根演练",
    )


def _apply_synthetic_clear(
    distribution_root: Path,
    data_dir: Path,
    plan: Mapping[str, Any],
    *,
    confirmed: bool,
) -> str:
    """只在临时合成根执行确认/取消；不属于真实卸载工具。"""

    root = distribution_root.expanduser().resolve()
    data = data_dir.expanduser().resolve()
    _mark_synthetic_root(root)
    try:
        data.relative_to(root)
    except ValueError as exc:
        raise Section154Error("clear_data_dir_outside_synthetic_root") from exc
    import distribution as dist  # noqa: WPS433

    expected = dist.build_uninstall_plan(
        distribution_root=root,
        data_dir=data,
        include_project_data=True,
    )
    if plan.get("plan_sha256") != expected.get("plan_sha256"):
        raise Section154Error("clear_plan_mismatch")
    if plan.get("disposition_mode") != "include_project_data":
        raise Section154Error("clear_plan_not_explicit")
    if not confirmed:
        return "cancelled"
    if data.exists():
        shutil.rmtree(data)
    return "confirmed_and_cleared"


def _check_mixed_version_late_callback_fence(root: Path, project_id: str) -> Dict[str, Any]:
    spec = _spec("mixed_version_late_callback_fence")
    from fixtures_schema_manifest import make_project  # noqa: WPS433
    from mm_r7.migration import (  # noqa: WPS433
        MigrationError,
        MigrationRunner,
        STATUS_COMPLETED,
        STATUS_MIGRATION_OPERATION_CONFLICT,
        STATUS_ROLLED_BACK,
    )

    case_root = root / "item13"
    _mark_synthetic_root(case_root)
    make_project(case_root / project_id, runtime_version="5")

    runner = MigrationRunner(case_root, project_id, wait_seconds=0.0)
    try:
        result = runner.start_upgrade("154-mixed")
        if result.state != STATUS_COMPLETED or result.operation is None:
            return _failed(spec, "mm_r7.migration:MigrationRunner.start_upgrade", "基线迁移未完成")
        operation = result.operation
        assert operation.plan_digest is not None
        try:
            runner.apply_callback(
                operation.operation_id,
                plan_digest=operation.plan_digest,
                expected_state="migrating",
                status=STATUS_ROLLED_BACK,
            )
        except MigrationError as late:
            if late.code != STATUS_MIGRATION_OPERATION_CONFLICT:
                return _failed(spec, "mm_r7.migration:MigrationRunner.apply_callback", "迟到回调未 fenced")
        else:
            return _failed(spec, "mm_r7.migration:MigrationRunner.apply_callback", "迟到回调未拒绝")
        if runner.ledger.get(operation.operation_id).status != STATUS_COMPLETED:
            return _failed(spec, "mm_r7.migration:MigrationOperationLedger", "current 被污染")
        wrong_digest = "sha256:" + ("0" * 64)
        try:
            runner.apply_callback(
                operation.operation_id,
                plan_digest=wrong_digest,
                expected_state=STATUS_COMPLETED,
                status=STATUS_ROLLED_BACK,
            )
        except MigrationError as mixed:
            if mixed.code != STATUS_MIGRATION_OPERATION_CONFLICT:
                return _failed(spec, "mm_r7.migration:MigrationRunner.apply_callback", "混合 plan 未 blocked")
        else:
            return _failed(spec, "mm_r7.migration:MigrationRunner.apply_callback", "混合 plan 未拒绝")
    finally:
        runner.close()

    return _passed(
        spec,
        "mm_r7.migration:MigrationRunner.apply_callback",
        "09B 混合版本与迟到回调 fence 阻断陈旧提交且不污染 current",
    )


CHECKERS: Tuple[Callable[[Path, str], Dict[str, Any]], ...] = (
    _check_export_import,
    _check_manifest_identity_lineage,
    _check_backup_corruption,
    _check_clean_restore,
    _check_pre_upgrade_protection,
    _check_migration_success,
    _check_critical_boundary_failure,
    _check_original_version_usable,
    _check_actual_rollback,
    _check_credentials_not_exported_plaintext,
    _check_default_uninstall_retains_data,
    _check_explicit_clear_preview_confirm_cancel,
    _check_mixed_version_late_callback_fence,
)


def _overall_status(items: Sequence[Mapping[str, Any]]) -> str:
    if len(items) != len(ITEM_SPECS):
        return RESULT_FAILED
    if any(item.get("result") != RESULT_PASSED for item in items):
        return RESULT_FAILED
    return RESULT_PASSED


def build_evidence_manifest(items: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    normalized: List[Dict[str, Any]] = []
    for expected, item in zip(ITEM_SPECS, items):
        row = dict(_require_mapping(item, "item"))
        if row.get("index") != expected["index"] or row.get("key") != expected["key"]:
            raise Section154Error("item_order_mismatch")
        normalized.append(row)
    if len(normalized) != len(ITEM_SPECS):
        raise Section154Error("item_count_mismatch")
    status = _overall_status(normalized)
    body: Dict[str, Any] = {
        "schema": SECTION_15_4_SCHEMA,
        "version": SECTION_15_4_VERSION,
        "contract_ref": CONTRACT_REF,
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "synthetic_only": True,
        "offline": True,
        "item_count": len(ITEM_SPECS),
        "items": normalized,
        "status": status,
        "checks": {
            "synthetic_only": True,
            "offline": True,
            "real_project_paths": False,
            "services_started": False,
            "models_called": False,
        },
    }
    body["manifest_digest"] = ""
    body["manifest_digest"] = digest_ref(body)
    return _copy_json(body)


def validate_evidence_manifest(value: Mapping[str, Any]) -> Dict[str, Any]:
    raw = dict(_require_mapping(value, "manifest"))
    if raw.get("schema") != SECTION_15_4_SCHEMA:
        raise Section154Error("schema_mismatch")
    if raw.get("version") != SECTION_15_4_VERSION:
        raise Section154Error("version_mismatch")
    digest = raw.get("manifest_digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise Section154Error("manifest_digest_invalid")
    body = dict(raw)
    body["manifest_digest"] = ""
    if digest_ref(body) != digest:
        raise Section154Error("manifest_digest_mismatch")
    items = raw.get("items")
    if not isinstance(items, list):
        raise Section154Error("items_must_be_list")
    normalized: List[Dict[str, Any]] = []
    for expected, item in zip(ITEM_SPECS, items):
        row = dict(_require_mapping(item, "item"))
        for field in ("index", "key", "title", "result", "evidence_ref", "summary", "item_digest"):
            if field not in row:
                raise Section154Error("item_missing_field:%s" % field)
        if row["index"] != expected["index"] or row["key"] != expected["key"]:
            raise Section154Error("item_key_order_mismatch")
        if row["result"] not in ALLOWED_RESULTS:
            raise Section154Error("item_result_invalid")
        _sanitize_summary(str(row["summary"]))
        digest_input = {
            "index": row["index"],
            "key": row["key"],
            "result": row["result"],
            "evidence_ref": row["evidence_ref"],
            "summary": row["summary"],
        }
        if digest_ref(digest_input) != row["item_digest"]:
            raise Section154Error("item_digest_mismatch")
        normalized.append(row)
    if len(normalized) != len(ITEM_SPECS):
        raise Section154Error("item_count_mismatch")
    status = _require_string(raw.get("status"), "status")
    if status != _overall_status(normalized):
        raise Section154Error("status_mismatch")
    checks = _require_mapping(raw.get("checks"), "checks")
    if checks.get("synthetic_only") is not True or checks.get("offline") is not True:
        raise Section154Error("checks_boundary_mismatch")
    return _copy_json(raw)


def replay_section_15_4(value: Any, *, strict: bool = False) -> ReplayResult:
    errors: List[str] = []
    status: Optional[str] = None
    try:
        manifest = validate_evidence_manifest(_require_mapping(value, "replay"))
        status = str(manifest.get("status"))
    except (Section154Error, TypeError, ValueError) as exc:
        errors.append(str(exc))
        if strict:
            raise Section154Error(str(exc)) from exc
    return ReplayResult(valid=not errors, status=status, errors=tuple(errors))


independent_replay = replay_section_15_4
replay_15_4_evidence = replay_section_15_4


def run_section_15_4(
    runtime_root: Path,
    *,
    project_id: str = "synth-154",
) -> Dict[str, Any]:
    """在临时合成根上运行十三项 §15.4 程序并返回 canonical manifest。"""

    _ensure_r7_path()
    root = Path(runtime_root).expanduser().resolve()
    project_id = _normalize_synthetic_project_id(project_id)
    _mark_synthetic_root(root)
    items: List[Dict[str, Any]] = []
    for checker in CHECKERS:
        try:
            items.append(checker(root, project_id))
        except Exception as exc:  # noqa: BLE001 - item-level fail closed
            spec = ITEM_SPECS[len(items)]
            items.append(
                _failed(
                    spec,
                    "synthetic_15_4:orchestrator",
                    "检查异常:%s" % type(exc).__name__,
                )
            )
    return build_evidence_manifest(items)


run_synthetic_15_4 = run_section_15_4
build_synthetic_15_4_evidence = run_section_15_4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthetic_15_4",
        description="医学监查工作台 G4 §15.4 合成离线程序（仅临时合成根）",
    )
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="运行十三项程序")
    run.add_argument(
        "--runtime-root",
        required=True,
        help="临时合成运行根（须位于系统临时目录）",
    )
    run.add_argument("--project-id", default="synth-154", help="合成项目标识")
    replay = sub.add_parser("replay", help="独立 replay canonical manifest")
    replay.add_argument("input", help="manifest JSON 路径；使用 - 从标准输入读取")
    replay.add_argument("--strict", action="store_true", help="遇到不一致时以错误退出")
    return parser


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Section154Error("input_unreadable:%s" % type(exc).__name__) from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit as exc:
        code = int(exc.code or 0)
        return 0 if code == 0 else 2

    if args.command == "run":
        try:
            manifest = run_section_15_4(Path(args.runtime_root), project_id=str(args.project_id))
        except Section154Error as exc:
            sys.stderr.write(str(exc) + "\n")
            return 2
        sys.stdout.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        return 0 if manifest.get("status") == RESULT_PASSED else 4

    if args.command == "replay":
        try:
            result = replay_section_15_4(_load_json(args.input), strict=bool(args.strict))
        except Section154Error as exc:
            sys.stderr.write(str(exc) + "\n")
            return 2
        sys.stdout.write(json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n")
        return 0 if result.valid else 2

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
