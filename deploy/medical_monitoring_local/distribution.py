#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Slice-09E distribution: release inventory, prepare-upgrade drill, uninstall plan.

Reuses 09A backup + maintenance gate and 09B schema inspection. Does not copy
those mechanisms, does not mutate live schema/version on prepare-upgrade, and
never deletes files from uninstall-plan.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

EXIT_OK = 0
EXIT_PREFLIGHT_OR_ARGS = 2
EXIT_PORT_OWNERSHIP = 3
EXIT_UPGRADE_PREP = 4
EXIT_MAINTENANCE_BUSY = 5

RELEASE_SOURCES_SCHEMA = "mm-monitoring-local-release-sources-v1"
RELEASE_MANIFEST_SCHEMA = "mm-monitoring-local-release-manifest-v1"
UNINSTALL_PLAN_SCHEMA = "mm-monitoring-local-uninstall-plan-v1"

PREPARE_STAGING_DIR = ".prepare-upgrade-staging"
MSG_UPGRADE_OK = "升级准备完成：升级保护备份已生成，兼容性预检通过。项目数据未更改。"
MSG_UPGRADE_BLOCKED = "已阻止升级，项目数据未更改，升级保护备份已保留。"
MSG_UPGRADE_FAILED = "升级准备失败，项目数据未更改。"
MSG_UPGRADE_BUSY = "同项目维护任务正在执行，本次升级准备未开始。"
MSG_UNINSTALL_RETAIN = (
    "卸载计划已生成：移除应用，保留项目数据、备份、导出与业务审计。尚未删除任何数据。"
)
MSG_UNINSTALL_CLEAR = (
    "卸载计划已生成：预览同时清除项目数据。尚未删除任何数据。"
)

_EXCLUDED_NAME_MARKERS = (
    "__pycache__",
    "node_modules",
    ".env",
    ".mmbackup-staging",
    ".migration-staging",
    ".migration-rollback",
    ".prepare-upgrade-staging",
    ".maintenance-locks",
    "deploy/medical_writing_local",
)

DEPLOY_DIR = Path(__file__).resolve().parent
WORKBENCH_ROOT = DEPLOY_DIR.parents[1]
_R7_SRC = WORKBENCH_ROOT / "poc" / "medical_monitoring_ai_native_r7" / "src"


def _emit(message: str) -> None:
    sys.stdout.write(message.rstrip() + "\n")


def _emit_err(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def _machine_detail(detail: str) -> None:
    if os.environ.get("MM_MANAGE_MACHINE_DETAIL", "").strip() in {"1", "true", "TRUE"}:
        if detail:
            _emit_err("MACHINE_DETAIL " + detail)


class DistributionError(Exception):
    def __init__(self, exit_code: int, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)
        self.message = str(message)
        self.detail = str(detail or "")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        raw = str(value).encode("utf-8")
    return sha256(raw).hexdigest()


def digest_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_r7_path() -> None:
    root = str(_R7_SRC)
    if root not in sys.path:
        sys.path.insert(0, root)


def _load_release_sources(path: Optional[Path] = None) -> Dict[str, Any]:
    sources_path = path or (DEPLOY_DIR / "release_sources.json")
    try:
        payload = json.loads(sources_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "发布清单源定义缺失或无法读取。",
            f"release_sources_unreadable error={exc}",
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema") != RELEASE_SOURCES_SCHEMA:
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "发布清单源定义无效。",
            "release_sources_schema_mismatch",
        )
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "发布清单源定义为空。",
            "release_sources_empty",
        )
    return payload


def _is_excluded_relative(relative: str) -> bool:
    normalized = relative.replace("\\", "/").strip("/")
    if normalized == "deploy/medical_writing_local" or normalized.startswith(
        "deploy/medical_writing_local/"
    ):
        return True
    parts = normalized.split("/")
    banned_parts = {
        "__pycache__",
        "node_modules",
        ".git",
        ".DS_Store",
        "Thumbs.db",
        ".mmbackup-staging",
        ".migration-staging",
        ".migration-rollback",
        ".prepare-upgrade-staging",
        ".maintenance-locks",
        "cache",
        "logs",
    }
    for part in parts:
        if part in banned_parts or part.startswith(".env"):
            return True
        if part.endswith(
            (".mmbackup", ".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".log")
        ):
            return True
    return False


def _iter_source_files(workbench_root: Path, entries: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源定义无效。",
                "release_sources_entry_invalid",
            )
        relative = entry.strip().replace("\\", "/")
        if relative.startswith("/") or ".." in relative.split("/"):
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源定义无效。",
                f"release_sources_entry_unsafe entry={relative}",
            )
        if _is_excluded_relative(relative):
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源定义包含禁止项。",
                f"release_sources_entry_excluded entry={relative}",
            )
        target = (workbench_root / relative).resolve()
        try:
            target.relative_to(workbench_root.resolve())
        except ValueError as exc:
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源定义无效。",
                f"release_sources_entry_escape entry={relative}",
            ) from exc
        if not target.exists():
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源文件缺失。",
                f"release_sources_missing entry={relative}",
            )
        if target.is_dir():
            for child in sorted(target.rglob("*")):
                if not child.is_file():
                    continue
                rel = child.relative_to(workbench_root).as_posix()
                if _is_excluded_relative(rel):
                    continue
                if rel not in seen:
                    seen.add(rel)
                    files.append(child)
        elif target.is_file():
            if relative not in seen:
                seen.add(relative)
                files.append(target)
        else:
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "发布清单源文件类型无效。",
                f"release_sources_not_file entry={relative}",
            )
    files.sort(key=lambda path: path.relative_to(workbench_root).as_posix().encode("utf-8"))
    return files


def build_release_manifest(
    *,
    workbench_root: Optional[Path] = None,
    sources_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build deterministic release inventory from release_sources.json."""

    root = (workbench_root or WORKBENCH_ROOT).resolve()
    sources = _load_release_sources(sources_path)
    files = _iter_source_files(root, list(sources["entries"]))
    inventory: List[Dict[str, Any]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        inventory.append(
            {
                "path": relative,
                "bytes": int(path.stat().st_size),
                "sha256": digest_file(path),
            }
        )
    body = {
        "schema": RELEASE_MANIFEST_SCHEMA,
        "product_name": sources.get("product_name", "医学监查工作台"),
        "contract_ref": dict(sources.get("contract_ref") or {}),
        "runtime_prerequisites": dict(sources.get("runtime_prerequisites") or {}),
        "scope_declaration": dict(sources.get("scope_declaration") or {}),
        "files": inventory,
        "file_count": len(inventory),
        "total_bytes": sum(int(item["bytes"]) for item in inventory),
    }
    body["manifest_sha256"] = sha256_hex(canonical_json_bytes(body))
    return body


def write_release_manifest(
    output_path: Path,
    *,
    workbench_root: Optional[Path] = None,
    sources_path: Optional[Path] = None,
) -> Dict[str, Any]:
    manifest = build_release_manifest(
        workbench_root=workbench_root, sources_path=sources_path
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _is_temp_or_marked(path: Path) -> bool:
    resolved = path.resolve()
    tmp = Path(tempfile.gettempdir()).resolve()
    try:
        resolved.relative_to(tmp)
        return True
    except ValueError:
        pass
    if (resolved / ".mm_r7_synthetic").is_file():
        return True
    if os.environ.get("MM_09E_SYNTHETIC_OK", "").strip() in {"1", "true", "TRUE"}:
        return True
    return False


def _enforce_acceptance_synthetic(root: Path) -> None:
    flag = os.environ.get("MM_09E_ACCEPTANCE_RUNNER", "").strip()
    if flag not in {"1", "true", "TRUE"}:
        return
    if not _is_temp_or_marked(root):
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "受控验收只接受临时合成工作区。",
            f"non_synthetic_root root={root}",
        )


def _atomic_rmtree(path: Path) -> None:
    if not path.exists():
        return
    # Rename aside then delete so readers never see a half-removed tree.
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    trash = parent / (path.name + ".removing-" + sha256_hex(os.urandom(8))[:12])
    try:
        path.rename(trash)
    except OSError:
        shutil.rmtree(path, ignore_errors=True)
        return
    shutil.rmtree(trash, ignore_errors=True)


def _normalized_abs_path(path: Path) -> str:
    """Canonical absolute path for digest binding only (never user-facing)."""

    return Path(path).expanduser().resolve(strict=False).as_posix()


def _root_identity_digest(
    *,
    distribution_root: Path,
    data_dir: Path,
    sources: Mapping[str, Any],
) -> str:
    # Bind digest to normalized absolute roots so same basename under different
    # install prefixes do not collide. Absolute paths stay inside the hash only.
    payload = {
        "distribution_root": _normalized_abs_path(distribution_root),
        "data_dir": _normalized_abs_path(data_dir),
        "release_sources_schema": sources.get("schema"),
        "contract_ref": dict(sources.get("contract_ref") or {}),
        "entries": list(sources.get("entries") or []),
    }
    return sha256_hex(canonical_json_bytes(payload))


def _pid_is_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but is not signalable by this uid.
        return True
    except OSError:
        return False
    return True


def _read_prepare_marker(staging: Path) -> Optional[Dict[str, Any]]:
    marker = staging / "in_progress.json"
    if not marker.is_file():
        return None
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _prepare_owner_alive(staging: Path) -> bool:
    payload = _read_prepare_marker(staging)
    if payload is None:
        return False
    return _pid_is_alive(payload.get("pid"))


def _remove_owned_prepare_staging(staging: Path, owner_pid: int) -> None:
    """Delete staging only when this process still owns the in-progress marker."""

    if not staging.exists():
        return
    payload = _read_prepare_marker(staging)
    if payload is None:
        # Incomplete claim (dir without readable marker) may be reclaimed.
        if not (staging / "receipt.json").is_file():
            _atomic_rmtree(staging)
        return
    try:
        marker_pid = int(payload.get("pid"))
    except (TypeError, ValueError):
        _atomic_rmtree(staging)
        return
    if marker_pid == int(owner_pid):
        _atomic_rmtree(staging)


def _claim_prepare_staging(
    staging: Path,
    *,
    project_id: str,
    idempotency_key: str,
    owner_pid: int,
) -> None:
    """Exclusively claim prepare-upgrade staging under the held 09A gate.

    Live owner PID => busy (exit 5 path). Dead/missing owner => reclaim.
    """

    staging.parent.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        if _prepare_owner_alive(staging):
            marker = _read_prepare_marker(staging) or {}
            raise DistributionError(
                EXIT_MAINTENANCE_BUSY,
                MSG_UPGRADE_BUSY,
                f"prepare_upgrade_active_owner pid={marker.get('pid')}",
            )
        # Crash leftover or completed receipt tree: safe to reclaim.
        _atomic_rmtree(staging)
    try:
        staging.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        if _prepare_owner_alive(staging):
            raise DistributionError(
                EXIT_MAINTENANCE_BUSY,
                MSG_UPGRADE_BUSY,
                "prepare_upgrade_staging_conflict",
            ) from exc
        raise DistributionError(
            EXIT_MAINTENANCE_BUSY,
            MSG_UPGRADE_BUSY,
            "prepare_upgrade_staging_race",
        ) from exc
    marker_body = {
        "schema": "mm-monitoring-local-prepare-upgrade-staging-v1",
        "project_id": project_id,
        "idempotency_key": idempotency_key,
        "status": "in_progress",
        "pid": int(owner_pid),
    }
    tmp_marker = staging / ("in_progress.json.tmp-" + str(owner_pid))
    tmp_marker.write_text(
        json.dumps(
            marker_body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(str(tmp_marker), str(staging / "in_progress.json"))


def _parse_prepare_upgrade_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="prepare-upgrade",
        description="升级准备：生成升级保护备份并做兼容性预检（不改写原数据）。",
    )
    parser.add_argument("--runtime-root", required=True, help="项目运行根目录（合成工作区）")
    parser.add_argument("--project-id", required=True, help="规范项目标识")
    parser.add_argument(
        "--idempotency-key",
        default="prepare-upgrade",
        help="升级保护备份幂等键",
    )
    try:
        return parser.parse_args(list(argv))
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code == 0:
            raise DistributionError(EXIT_OK, "") from exc
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "升级准备参数不完整，请指定运行根目录与项目标识。",
            "prepare_upgrade_args_invalid",
        ) from exc


def _compatibility_precheck(workspace: Path) -> Tuple[bool, str]:
    """Return (ok, detail_code) using 09B schema inspection only (no mutation)."""

    _ensure_r7_path()
    from mm_r7.migration import MigrationPlan  # noqa: WPS433
    from mm_r7.schema_manifest import SchemaClassification, inspect_project_schema  # noqa: WPS433

    inspection = inspect_project_schema(workspace)
    classification = inspection.classification
    if classification is SchemaClassification.CURRENT:
        return True, "already_current"
    if classification is SchemaClassification.LEGACY:
        if not inspection.can_view or not inspection.can_upgrade:
            return False, "legacy_not_upgradeable"
        try:
            MigrationPlan.from_inspection(inspection)
        except Exception as exc:  # noqa: BLE001 - fail closed into blocked upgrade
            return False, f"migration_plan_rejected:{type(exc).__name__}"
        return True, "legacy_upgradeable"
    return False, f"incompatible:{classification.value}:{inspection.reason_code}"


def prepare_upgrade_main(argv: Sequence[str], paths: Any = None) -> int:
    """CLI hook for manage.py prepare-upgrade."""

    try:
        args = _parse_prepare_upgrade_args(argv)
        runtime_root = Path(args.runtime_root).expanduser().resolve()
        project_id = str(args.project_id)
        idempotency_key = str(args.idempotency_key or "prepare-upgrade")
        _enforce_acceptance_synthetic(runtime_root)

        workspace = runtime_root / project_id
        if not workspace.is_dir():
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "升级准备参数不完整，请指定有效的合成项目工作区。",
                f"workspace_missing path={workspace}",
            )

        _ensure_r7_path()
        from mm_r7.maintenance_gate import (  # noqa: WPS433
            ProjectBusyError,
            ProjectMaintenanceGate,
        )
        from mm_r7.project_backup import (  # noqa: WPS433
            STATUS_AVAILABLE,
            ProjectBackupError,
            ProjectBackupManager,
        )

        staging_root = runtime_root / PREPARE_STAGING_DIR
        staging = staging_root / project_id
        owner_pid = os.getpid()
        gate = ProjectMaintenanceGate(runtime_root, project_id, wait_seconds=0.0)
        permit = None
        claimed = False
        try:
            try:
                permit = gate.acquire(True)
            except ProjectBusyError as exc:
                _emit_err(MSG_UPGRADE_BUSY)
                _machine_detail(f"prepare_upgrade_busy code={exc.code}")
                return EXIT_MAINTENANCE_BUSY

            _claim_prepare_staging(
                staging,
                project_id=project_id,
                idempotency_key=idempotency_key,
                owner_pid=owner_pid,
            )
            claimed = True

            # Release before 09A backup to avoid same-process dual-fd flock deadlock.
            # Single-writer prepare-upgrade continues via PID marker after release.
            permit.release()
            permit = None

            manager = ProjectBackupManager(
                runtime_root,
                project_id,
                project_dir=workspace,
                wait_seconds=0.0,
            )
            try:
                backup = manager.backup(idempotency_key)
            except ProjectBackupError as exc:
                _remove_owned_prepare_staging(staging, owner_pid)
                if exc.code == "project_busy_retry_later":
                    _emit_err(MSG_UPGRADE_BUSY)
                    _machine_detail(f"backup_busy code={exc.code}")
                    return EXIT_MAINTENANCE_BUSY
                _emit_err(MSG_UPGRADE_FAILED)
                _machine_detail(f"backup_failed code={exc.code}")
                return EXIT_UPGRADE_PREP
            finally:
                try:
                    manager.ledger.close()
                except Exception:  # noqa: BLE001
                    pass

            if backup.status != STATUS_AVAILABLE or backup.package_path is None:
                _remove_owned_prepare_staging(staging, owner_pid)
                _emit_err(MSG_UPGRADE_FAILED)
                _machine_detail(f"backup_incomplete status={backup.status}")
                return EXIT_UPGRADE_PREP
            ok, detail = _compatibility_precheck(workspace)
            if not ok:
                _remove_owned_prepare_staging(staging, owner_pid)
                _emit(MSG_UPGRADE_BLOCKED)
                _machine_detail(
                    "prepare_upgrade_blocked "
                    f"detail={detail} package_id={backup.package_id}"
                )
                return EXIT_UPGRADE_PREP

            receipt = {
                "schema": "mm-monitoring-local-prepare-upgrade-receipt-v1",
                "status": "ready",
                "compatibility": detail,
                "package_id": backup.package_id,
                "source_workspace_fingerprint": backup.source_workspace_fingerprint,
                "backup_contract_version": "FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3",
            }
            receipt_path = staging / "receipt.json"
            receipt_path.write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (staging / "in_progress.json").unlink(missing_ok=True)
            # Keep completed receipt directory as evidence; not an incomplete staging.
            _emit(MSG_UPGRADE_OK)
            _machine_detail(
                "prepare_upgrade_ok "
                f"compatibility={detail} package_id={backup.package_id}"
            )
            return EXIT_OK
        except DistributionError as err:
            if claimed and err.exit_code != EXIT_MAINTENANCE_BUSY:
                _remove_owned_prepare_staging(staging, owner_pid)
            raise
        except Exception as exc:  # noqa: BLE001
            if claimed:
                _remove_owned_prepare_staging(staging, owner_pid)
            raise DistributionError(
                EXIT_UPGRADE_PREP,
                MSG_UPGRADE_FAILED,
                f"prepare_upgrade_exception error={exc}",
            ) from exc
        finally:
            if permit is not None:
                try:
                    permit.release()
                except Exception:  # noqa: BLE001
                    pass
    except DistributionError as err:
        if err.message:
            _emit_err(err.message)
        _machine_detail(err.detail)
        return err.exit_code


def _parse_uninstall_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="uninstall-plan",
        description="生成卸载数据处置预览计划（不删除任何数据）。",
    )
    parser.add_argument(
        "--include-project-data",
        action="store_true",
        help="预览同时清除项目数据（默认保留项目数据、备份、导出与业务审计）",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="预览计划输出目录（须显式指定）",
    )
    try:
        return parser.parse_args(list(argv))
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code == 0:
            raise DistributionError(EXIT_OK, "") from exc
        raise DistributionError(
            EXIT_PREFLIGHT_OR_ARGS,
            "卸载计划参数不完整，请显式指定输出目录。",
            "uninstall_plan_args_invalid",
        ) from exc


def build_uninstall_plan(
    *,
    distribution_root: Path,
    data_dir: Path,
    include_project_data: bool,
    sources: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    loaded = dict(sources or _load_release_sources())
    application_objects = [
        {"kind": "distribution_shell", "role": "管理入口"},
        {"kind": "frontend_runtime", "role": "桌面前端"},
        {"kind": "start_scripts", "role": "启动脚本"},
        {"kind": "runtime_config", "role": "运行配置"},
    ]
    retained_objects = [
        {"kind": "project_data", "role": "项目数据"},
        {"kind": "backups", "role": "备份"},
        {"kind": "exports", "role": "导出"},
        {"kind": "business_audit", "role": "业务审计"},
    ]
    if include_project_data:
        disposition_mode = "include_project_data"
        planned_clear_objects = list(application_objects) + list(retained_objects)
        retained_objects = []
    else:
        disposition_mode = "retain_project_data"
        planned_clear_objects = list(application_objects)

    root_digest = _root_identity_digest(
        distribution_root=distribution_root,
        data_dir=data_dir,
        sources=loaded,
    )
    business = {
        "schema": UNINSTALL_PLAN_SCHEMA,
        "disposition_mode": disposition_mode,
        "application_objects": application_objects,
        "retained_objects": retained_objects,
        "planned_clear_objects": planned_clear_objects,
        "root_identity_digest": root_digest,
        "deletion_executed": False,
        "future_delete_tool_required": True,
    }
    plan_sha256 = sha256_hex(canonical_json_bytes(business))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    plan = dict(business)
    plan["generated_at"] = generated_at
    plan["plan_sha256"] = plan_sha256
    # Basename hints only — absolute roots are bound into root_identity_digest,
    # never emitted into preview JSON.
    plan["machine"] = {
        "distribution_root_name": Path(distribution_root).name,
        "data_dir_name": Path(data_dir).name,
    }
    return plan


def uninstall_plan_main(argv: Sequence[str], paths: Any = None) -> int:
    """CLI hook for manage.py uninstall-plan. Preview only; never deletes."""

    try:
        args = _parse_uninstall_args(argv)
        output_dir = Path(args.output_dir).expanduser().resolve()
        include_project_data = bool(args.include_project_data)

        if paths is not None:
            distribution_root = Path(paths.root).resolve()
            data_dir = Path(paths.data_dir).resolve()
        else:
            distribution_root = DEPLOY_DIR.resolve()
            data_dir = distribution_root / "data"

        _enforce_acceptance_synthetic(distribution_root)
        _enforce_acceptance_synthetic(output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DistributionError(
                EXIT_PREFLIGHT_OR_ARGS,
                "卸载计划输出目录不可用。",
                f"output_dir_unusable error={exc}",
            ) from exc

        plan = build_uninstall_plan(
            distribution_root=distribution_root,
            data_dir=data_dir,
            include_project_data=include_project_data,
        )
        target = output_dir / "uninstall_plan.json"
        target.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if include_project_data:
            _emit(MSG_UNINSTALL_CLEAR)
        else:
            _emit(MSG_UNINSTALL_RETAIN)
        _machine_detail(
            "uninstall_plan_ok "
            f"mode={plan['disposition_mode']} plan_sha256={plan['plan_sha256']}"
        )
        return EXIT_OK
    except DistributionError as err:
        if err.message:
            _emit_err(err.message)
        _machine_detail(err.detail)
        return err.exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="distribution",
        description="医学监查本地分发：发布清单、升级准备与卸载预览。",
    )
    sub = parser.add_subparsers(dest="command")
    build = sub.add_parser("build-release-manifest", help="生成发布清单")
    build.add_argument("--output", required=True, help="清单输出路径")
    build.add_argument(
        "--workbench-root",
        default=str(WORKBENCH_ROOT),
        help="工作台根目录",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv_list:
        parser.print_help(sys.stderr)
        return EXIT_PREFLIGHT_OR_ARGS
    try:
        args = parser.parse_args(argv_list)
    except SystemExit as exc:
        code = int(exc.code or 0)
        return EXIT_OK if code == 0 else EXIT_PREFLIGHT_OR_ARGS
    if args.command == "build-release-manifest":
        try:
            manifest = write_release_manifest(
                Path(args.output).expanduser(),
                workbench_root=Path(args.workbench_root).expanduser(),
            )
            _emit(f"发布清单已生成，文件数 {manifest['file_count']}。")
            return EXIT_OK
        except DistributionError as err:
            _emit_err(err.message)
            _machine_detail(err.detail)
            return err.exit_code
    parser.print_help(sys.stderr)
    return EXIT_PREFLIGHT_OR_ARGS


if __name__ == "__main__":
    sys.exit(main())
