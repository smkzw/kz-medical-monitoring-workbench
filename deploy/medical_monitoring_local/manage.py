#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""医学监查工作台本地管理入口（Slice-09E）。

中文启停/状态/首次启动检查与退出码合同。升级准备与卸载计划委托同目录
``distribution`` 模块（由发布清单 worker 实现）。不启动模型、不读取真实项目、
不修改医学写作分发目录。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

EXIT_OK = 0
EXIT_PREFLIGHT_OR_ARGS = 2
EXIT_PORT_OWNERSHIP = 3
EXIT_UPGRADE_PREP = 4
EXIT_MAINTENANCE_BUSY = 5

PORT_BACKEND = 8911
PORT_FRONTEND = 5174
PORT_AUX = 8984
MANAGED_PORTS: Tuple[int, ...] = (PORT_BACKEND, PORT_FRONTEND, PORT_AUX)

RUNTIME_CONFIG_NAME = "runtime_config.json"
RUNTIME_SCHEMA = "mm-monitoring-local-runtime-v1"
PRODUCT_NAME = "医学监查工作台"

# User-visible success phrases must stay free of ports, paths, digests, and PIDs.
MSG_PREFLIGHT_OK = "首次启动检查通过，医学监查工作台可以启动。"
MSG_STATUS_RUNNING = "医学监查工作台运行状态：已启动。"
MSG_STATUS_STOPPED = "医学监查工作台运行状态：未启动。"
MSG_STATUS_NOT_READY = "医学监查工作台运行状态：未就绪。"
MSG_STATUS_PARTIAL = "医学监查工作台运行状态：部分运行，请先停止后再启动。"
MSG_START_OK = "医学监查工作台已启动。"
MSG_START_ALREADY = "医学监查工作台已在运行。"
MSG_STOP_OK = "医学监查工作台已停止。"
MSG_STOP_IDLE = "医学监查工作台未在运行。"
MSG_SYNTHETIC_START_STOP_RESTART = "合成离线演练已验证启动、停止和重启信号。"
MSG_SYNTHETIC_READY = "合成离线演练已验证就绪信号。"
MSG_SYNTHETIC_FAILURE = "合成离线演练已验证失败信号。"
MSG_SYNTHETIC_PARTIAL = "合成离线演练已验证部分运行信号。"
MSG_SYNTHETIC_FOREIGN = "合成离线演练已验证外部归属拒绝信号。"
MSG_SYNTHETIC_G4_NOTIFICATION = (
    "合成离线演练已验证通知终态投影、幂等记录与只导航意图。"
)
MSG_SYNTHETIC_G4_15_4_PASSED = "合成离线演练已验证十三项程序全部通过。"
MSG_SYNTHETIC_G4_15_4_FAILED = "合成离线十三项程序未全部通过，请查看机器详情。"

DEPLOY_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Paths:
    root: Path
    frontend: Path
    data_dir: Path
    runtime_config: Path
    start_backend: Path
    start_frontend: Path
    start_aux: Path


@dataclass(frozen=True)
class Listener:
    port: int
    pid: int
    cwd: Optional[Path]


class ManageError(Exception):
    def __init__(self, exit_code: int, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)
        self.message = str(message)
        self.detail = str(detail or "")


def _env_path(name: str) -> Optional[Path]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def resolve_paths(root_override: Optional[Path] = None) -> Paths:
    """Resolve distribution paths. Identity comes from config/env, never hard-coded projects."""

    if root_override is not None:
        root = root_override.resolve()
    else:
        env_root = _env_path("MM_MONITORING_LOCAL_ROOT")
        root = (env_root or Path(__file__).resolve().parent).resolve()

    runtime_config = (_env_path("MM_RUNTIME_CONFIG") or (root / RUNTIME_CONFIG_NAME)).resolve()
    frontend = (_env_path("MM_FRONTEND_DIR") or (root / "frontend")).resolve()
    data_dir = _env_path("MM_DATA_DIR")
    if data_dir is None and runtime_config.is_file():
        try:
            payload = json.loads(runtime_config.read_text(encoding="utf-8"))
            configured = payload.get("data_dir")
            if isinstance(configured, str) and configured.strip():
                candidate = Path(configured.strip()).expanduser()
                data_dir = candidate if candidate.is_absolute() else (root / candidate)
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            data_dir = None
    if data_dir is None:
        data_dir = root / "data"

    return Paths(
        root=root,
        frontend=frontend,
        data_dir=data_dir.resolve(),
        runtime_config=runtime_config,
        start_backend=root / "bin" / "start_backend.zsh",
        start_frontend=root / "bin" / "start_frontend.zsh",
        start_aux=root / "bin" / "start_aux.zsh",
    )


def strict_owned_cwd(cwd: Optional[Path], paths: Paths) -> bool:
    """True only when cwd is exactly the distribution root or frontend (contract boundary)."""

    if cwd is None:
        return False
    try:
        resolved = cwd.resolve()
    except OSError:
        return False
    return resolved in {paths.root.resolve(), paths.frontend.resolve()}


def _run_capture(argv: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            list(argv),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return ""
    return completed.stdout or ""


def listener_pids(port: int) -> List[int]:
    text = _run_capture(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"])
    pids: List[int] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    # Preserve order, drop duplicates.
    seen = set()
    unique: List[int] = []
    for pid in pids:
        if pid not in seen:
            seen.add(pid)
            unique.append(pid)
    return unique


def process_cwd(pid: int) -> Optional[Path]:
    text = _run_capture(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
    for line in text.splitlines():
        if line.startswith("n"):
            raw = line[1:].strip()
            if not raw:
                continue
            try:
                return Path(raw).resolve()
            except OSError:
                return Path(raw)
    return None


def inspect_port(port: int) -> List[Listener]:
    listeners: List[Listener] = []
    for pid in listener_pids(port):
        listeners.append(Listener(port=port, pid=pid, cwd=process_cwd(pid)))
    return listeners


def classify_ports(paths: Paths) -> Dict[str, List[Listener]]:
    owned: List[Listener] = []
    foreign: List[Listener] = []
    for port in MANAGED_PORTS:
        for item in inspect_port(port):
            if strict_owned_cwd(item.cwd, paths):
                owned.append(item)
            else:
                foreign.append(item)
    return {"owned": owned, "foreign": foreign}


def required_ports_from_config(payload: dict) -> frozenset[int]:
    """Required owned ports for “fully running”; aux only when aux_enabled is explicitly true."""

    ports = frozenset({PORT_BACKEND, PORT_FRONTEND})
    if payload.get("aux_enabled") is True:
        return ports | frozenset({PORT_AUX})
    return ports


def _try_load_runtime_config(path: Path) -> Optional[dict]:
    try:
        return _load_runtime_config(path)
    except ManageError:
        return None


def _emit(message: str) -> None:
    sys.stdout.write(message.rstrip() + "\n")


def _emit_err(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def _machine_detail(detail: str) -> None:
    """Machine evidence only; not part of ordinary user success copy."""

    if not detail:
        return
    if os.environ.get("MM_MANAGE_MACHINE_DETAIL", "").strip() in {"1", "true", "yes"}:
        _emit_err("MACHINE_DETAIL " + detail)


def _which_python() -> Optional[str]:
    candidates = [
        os.environ.get("MM_PYTHON", "").strip(),
        sys.executable,
        shutil.which("python3") or "",
        shutil.which("python") or "",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return item
    return None


def _which_node() -> Optional[str]:
    override = os.environ.get("MM_NODE", "").strip()
    if override and Path(override).exists():
        return override
    return shutil.which("node")


def _load_runtime_config(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "缺少运行配置，请先完成医学监查工作台发布准备后再执行首次启动检查。",
            f"missing_runtime_config path={path}",
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "运行配置无效，请修复运行配置后重新执行首次启动检查。",
            f"invalid_runtime_config error={exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "运行配置无效，请修复运行配置后重新执行首次启动检查。",
            "runtime_config_not_object",
        )
    schema = payload.get("schema")
    if schema != RUNTIME_SCHEMA:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "运行配置版本不匹配，请使用当前医学监查工作台发布包中的运行配置。",
            f"runtime_schema={schema!r}",
        )
    return payload


def _ensure_writable_dir(path: Path) -> None:
    if not path.exists():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "数据目录不存在或不可写，请创建可写数据目录后重新执行首次启动检查。",
            f"missing_data_dir path={path}",
        )
    if not path.is_dir():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "数据目录不存在或不可写，请创建可写数据目录后重新执行首次启动检查。",
            f"data_dir_not_directory path={path}",
        )

    probe = path / ".preflight_write_probe"
    try:
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "数据目录不存在或不可写，请创建可写数据目录后重新执行首次启动检查。",
            f"data_dir_not_writable path={path} error={exc}",
        ) from exc


def run_preflight(paths: Paths, *, require_start_scripts: bool = False) -> dict:
    """Fail-closed first-start checks. Never starts services or calls models."""

    if os.environ.get("MM_MONITORING_OFFLINE", "").strip() in {"1", "true", "TRUE"}:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线模式下不能执行真实启动检查，请改用合成离线演练入口。",
            "offline_mode_blocks_preflight",
        )

    runtime = _load_runtime_config(paths.runtime_config)
    if _which_python() is None:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "未找到可用的 Python，请先安装 Python 3 后重新执行首次启动检查。",
            "python_missing",
        )
    if _which_node() is None:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "未找到 Node.js，请先安装 Node.js 后重新执行首次启动检查。",
            "node_missing",
        )
    if not paths.frontend.is_dir():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "前端目录缺失，请使用完整的医学监查工作台发布包。",
            f"missing_frontend path={paths.frontend}",
        )
    node_modules = paths.frontend / "node_modules"
    if not node_modules.is_dir():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "前端依赖尚未安装，请先在前端目录安装依赖后重新执行首次启动检查。",
            f"missing_node_modules path={node_modules}",
        )
    _ensure_writable_dir(paths.data_dir)
    classified = classify_ports(paths)
    if classified["foreign"]:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "运行入口已被其他应用占用，请先释放后再执行首次启动检查。",
            "foreign_ports="
            + ",".join(str(p) for p in sorted({item.port for item in classified["foreign"]})),
        )
    if require_start_scripts:
        for script in (paths.start_backend, paths.start_frontend, paths.start_aux):
            if runtime.get("aux_enabled") is not True and script == paths.start_aux:
                continue
            if not script.is_file():
                raise ManageError(
                    EXIT_PREFLIGHT_OR_ARGS,
                    "启动入口缺失，请使用完整的医学监查工作台发布包。",
                    f"missing_start_script script={script.name}",
                )
    return runtime


def cmd_preflight(paths: Paths) -> int:
    run_preflight(paths, require_start_scripts=False)
    _emit(MSG_PREFLIGHT_OK)
    return EXIT_OK


def cmd_status(paths: Paths) -> int:
    runtime = _try_load_runtime_config(paths.runtime_config)
    if runtime is None:
        _emit(MSG_STATUS_NOT_READY)
        return EXIT_OK
    classified = classify_ports(paths)
    if classified["foreign"]:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "运行入口被其他应用占用，无法确定医学监查工作台运行状态。",
            "foreign_ports="
            + ",".join(str(p) for p in sorted({item.port for item in classified["foreign"]})),
        )
    required = required_ports_from_config(runtime)
    owned_ports = {item.port for item in classified["owned"]}
    if owned_ports.issuperset(required):
        _emit(MSG_STATUS_RUNNING)
    elif owned_ports:
        _emit(MSG_STATUS_PARTIAL)
    else:
        _emit(MSG_STATUS_STOPPED)
    return EXIT_OK


def _stop_listener(listener: Listener, paths: Paths) -> None:
    if not strict_owned_cwd(listener.cwd, paths):
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "停止对象不归本应用，已拒绝停止操作。",
            f"foreign_stop port={listener.port} pid={listener.pid}",
        )
    try:
        os.kill(listener.pid, 15)
    except ProcessLookupError:
        return
    except OSError as exc:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "停止医学监查工作台时遇到问题，请稍后重试。",
            f"stop_failed port={listener.port} pid={listener.pid} error={exc}",
        ) from exc
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if listener.pid not in listener_pids(listener.port):
            return
        time.sleep(0.1)
    try:
        os.kill(listener.pid, 9)
    except (ProcessLookupError, OSError):
        pass


def cmd_stop(paths: Paths) -> int:
    _load_runtime_config(paths.runtime_config)
    classified = classify_ports(paths)
    if classified["foreign"]:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "运行入口被其他应用占用，无法安全停止医学监查工作台。",
            "foreign_ports_on_stop="
            + ",".join(str(p) for p in sorted({item.port for item in classified["foreign"]})),
        )
    owned = classified["owned"]
    if not owned:
        _emit(MSG_STOP_IDLE)
        return EXIT_OK
    for listener in owned:
        _stop_listener(listener, paths)
    _emit(MSG_STOP_OK)
    return EXIT_OK


def _spawn_start_script(script: Path, paths: Paths) -> None:
    if not script.is_file():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "无法启动医学监查工作台，请检查启动入口后重试。",
            f"missing_script script={script.name}",
        )
    try:
        subprocess.Popen(
            ["/bin/zsh", str(script)],
            cwd=str(paths.root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "无法启动医学监查工作台，请检查启动入口后重试。",
            f"spawn_failed script={script.name} error={exc}",
        ) from exc


def cmd_start(paths: Paths) -> int:
    if os.environ.get("MM_MONITORING_OFFLINE", "").strip() in {"1", "true", "TRUE"}:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "离线验收模式下不能启动真实服务，请改用合成离线演练入口。",
            "offline_mode_blocks_start",
        )
    runtime = run_preflight(paths, require_start_scripts=True)
    required = required_ports_from_config(runtime)
    classified = classify_ports(paths)
    if classified["foreign"]:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "启动所需运行入口已被其他应用占用，请先释放后再启动医学监查工作台。",
            "foreign_ports="
            + ",".join(str(p) for p in sorted({item.port for item in classified["foreign"]})),
        )
    owned_ports = {item.port for item in classified["owned"]}
    if owned_ports.issuperset(required):
        _emit(MSG_START_ALREADY)
        return EXIT_OK
    if owned_ports:
        raise ManageError(
            EXIT_PORT_OWNERSHIP,
            "医学监查工作台处于部分运行状态，请先停止后再启动。",
            "partial_owned_ports=" + ",".join(str(p) for p in sorted(owned_ports)),
        )

    refreshed = resolve_paths(paths.root)
    scripts = [refreshed.start_backend, refreshed.start_frontend]
    if runtime.get("aux_enabled") is True:
        scripts.append(refreshed.start_aux)
    for script in scripts:
        _spawn_start_script(script, refreshed)
    _emit(MSG_START_OK)
    return EXIT_OK


def _load_synthetic_lifecycle():
    deploy_dir = DEPLOY_DIR
    if str(deploy_dir) not in sys.path:
        sys.path.insert(0, str(deploy_dir))
    try:
        import synthetic_lifecycle  # type: ignore
    except ImportError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线生命周期演练功能尚未就绪，请检查医学监查分发包。",
            f"synthetic_lifecycle_import_failed error={exc}",
        ) from exc
    return synthetic_lifecycle


def cmd_synthetic_lifecycle(scenario: str) -> int:
    module = _load_synthetic_lifecycle()
    try:
        evidence = module.run_synthetic_lifecycle(scenario)
    except (ValueError, TypeError) as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线生命周期演练参数无效，请查看帮助后重试。",
            f"synthetic_lifecycle_invalid error={exc}",
        ) from exc

    messages = {
        "start-stop-restart": MSG_SYNTHETIC_START_STOP_RESTART,
        "ready": MSG_SYNTHETIC_READY,
        "failure": MSG_SYNTHETIC_FAILURE,
        "partial": MSG_SYNTHETIC_PARTIAL,
        "foreign-ownership": MSG_SYNTHETIC_FOREIGN,
    }
    _emit(messages.get(str(evidence["scenario"]), "合成离线演练已完成。"))
    _machine_detail(
        "synthetic_scenario=%s final_status=%s"
        % (evidence["scenario"], evidence["final"]["status"])
    )
    return EXIT_OK


def _is_synthetic_runtime_root(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    if resolved in temp_roots:
        return False
    return any(resolved.is_relative_to(tmp) for tmp in temp_roots)


def _enforce_g4_runtime_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == DEPLOY_DIR.resolve():
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线程序不接受医学监查分发根目录，请使用临时合成工作区。",
            "g4_runtime_root_is_distribution_root",
        )
    if not _is_synthetic_runtime_root(resolved):
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线程序只接受临时合成工作区，请使用测试框架提供的临时目录。",
            "g4_runtime_root_not_synthetic root=%s" % resolved,
        )
    return resolved


def _load_synthetic_notification():
    deploy_dir = DEPLOY_DIR
    if str(deploy_dir) not in sys.path:
        sys.path.insert(0, str(deploy_dir))
    try:
        import synthetic_notification  # type: ignore
    except ImportError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线通知演练功能尚未就绪，请检查医学监查分发包。",
            f"synthetic_notification_import_failed error={exc}",
        ) from exc
    return synthetic_notification


def cmd_synthetic_g4_notification() -> int:
    module = _load_synthetic_notification()
    project = "opaque-project:synth-g4-cli-001"
    admission = "opaque-admission:synth-g4-cli-001"
    run_id = "opaque-run:synth-g4-cli-001"
    revision = "rev-synth-g4-cli-001"
    binding_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000001"
    )
    source_manifest_digest = "sha256:" + "2" * 64
    output_manifest_digest = "sha256:" + "3" * 64

    store = module.NotificationStore()
    adapter = module.SyntheticNotificationAdapter(
        capability_by_admission={admission: "authorized"},
        default_capability="authorized",
    )
    binding = module.AdmissionBinding(
        project_ref=project,
        admission_id=admission,
        admission_status="accepted",
        binding_digest=binding_digest,
        contract_version=module.CONTRACT_VERSION,
        app_version="synth-g4-cli-app-1",
        registered_project_display_name="合成演示项目",
        binding_valid=True,
    )
    event = module.TerminalEvent(
        project_ref=project,
        admission_id=admission,
        run_id=run_id,
        terminal_status="complete",
        terminal_revision=revision,
    )
    accessibility = module.TargetAccessibility(
        current_terminal_revision=revision,
        binding_digest=binding_digest,
        source_manifest_digest=source_manifest_digest,
        output_manifest_digest=output_manifest_digest,
        target_exists=True,
        result_accessible=True,
        explanation_accessible=True,
    )
    result = module.process_terminal_event(event, binding, accessibility, store, adapter)
    if result.status != "ok" or result.fact is None:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线通知演练未通过，请查看机器详情。",
            "g4_notification_projection_failed reason=%s" % (result.reason or "unknown"),
        )

    replay = module.process_terminal_event(event, binding, accessibility, store, adapter)
    if replay.status != "ok" or replay.created is not False:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线通知演练未通过，请查看机器详情。",
            "g4_notification_idempotency_failed",
        )

    navigation = module.build_navigation_intent(
        result.fact,
        binding,
        accessibility,
        store,
        adapter,
        click_count=2,
    )
    if navigation.status != "ok" or navigation.intent is None:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线通知演练未通过，请查看机器详情。",
            "g4_notification_navigation_failed",
        )
    if navigation.intent.get("action") != "navigate_only":
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线通知演练未通过，请查看机器详情。",
            "g4_notification_navigation_not_navigate_only",
        )

    module.validate_notification_fact(result.fact)
    _emit(MSG_SYNTHETIC_G4_NOTIFICATION)
    _machine_detail(
        "g4_notification_status=%s capability=%s channel=%s"
        % (
            result.fact["notification_status"],
            result.fact["capability_state"],
            result.fact["channel_evidence"],
        )
    )
    return EXIT_OK


def _load_synthetic_15_4():
    deploy_dir = DEPLOY_DIR
    if str(deploy_dir) not in sys.path:
        sys.path.insert(0, str(deploy_dir))
    try:
        import synthetic_15_4  # type: ignore
    except ImportError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线十三项程序功能尚未就绪，请检查医学监查分发包。",
            f"synthetic_15_4_import_failed error={exc}",
        ) from exc
    return synthetic_15_4


def cmd_synthetic_g4_15_4_run(runtime_root: Path, *, project_id: str) -> int:
    module = _load_synthetic_15_4()
    root = _enforce_g4_runtime_root(runtime_root)
    try:
        manifest = module.run_section_15_4(root, project_id=str(project_id))
    except module.Section154Error as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线十三项程序参数无效，请查看帮助后重试。",
            f"g4_15_4_invalid error={exc}",
        ) from exc

    passed = manifest.get("status") == module.RESULT_PASSED
    _emit(MSG_SYNTHETIC_G4_15_4_PASSED if passed else MSG_SYNTHETIC_G4_15_4_FAILED)
    _machine_detail(
        "g4_15_4_status=%s manifest_digest=%s"
        % (manifest.get("status"), manifest.get("manifest_digest"))
    )
    return EXIT_OK if passed else EXIT_UPGRADE_PREP


def cmd_synthetic_g4_15_4_replay(input_path: str, *, strict: bool) -> int:
    module = _load_synthetic_15_4()
    if input_path == "-":
        try:
            payload = json.load(sys.stdin)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ManageError(
                EXIT_PREFLIGHT_OR_ARGS,
                "合成离线十三项程序 replay 输入无效。",
                f"g4_15_4_replay_stdin_invalid error={exc}",
            ) from exc
    else:
        try:
            with open(input_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ManageError(
                EXIT_PREFLIGHT_OR_ARGS,
                "合成离线十三项程序 replay 输入无效。",
                f"g4_15_4_replay_input_invalid error={exc}",
            ) from exc
    try:
        result = module.replay_section_15_4(payload, strict=strict)
    except module.Section154Error as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线十三项程序 replay 未通过。",
            f"g4_15_4_replay_failed error={exc}",
        ) from exc
    if not result.valid:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "合成离线十三项程序 replay 未通过。",
            "g4_15_4_replay_invalid errors=" + ",".join(result.errors),
        )
    _emit("合成离线十三项程序 replay 已通过。")
    _machine_detail("g4_15_4_replay_status=%s" % (result.status or "unknown"))
    return EXIT_OK


def _load_distribution():
    deploy_dir = DEPLOY_DIR
    if str(deploy_dir) not in sys.path:
        sys.path.insert(0, str(deploy_dir))
    try:
        import distribution  # type: ignore
    except ImportError as exc:
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "升级准备或卸载计划功能尚未就绪，请先完成发布清单与数据处置实现。",
            f"distribution_import_failed error={exc}",
        ) from exc
    return distribution


def cmd_prepare_upgrade(argv: Sequence[str], paths: Paths) -> int:
    distribution = _load_distribution()
    handler = getattr(distribution, "prepare_upgrade_main", None)
    if not callable(handler):
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "升级准备功能尚未就绪，请先完成发布清单与数据处置实现。",
            "prepare_upgrade_main_missing",
        )
    code = handler(list(argv), paths=paths)
    return int(code)


def cmd_uninstall_plan(argv: Sequence[str], paths: Paths) -> int:
    distribution = _load_distribution()
    handler = getattr(distribution, "uninstall_plan_main", None)
    if not callable(handler):
        raise ManageError(
            EXIT_PREFLIGHT_OR_ARGS,
            "卸载计划功能尚未就绪，请先完成发布清单与数据处置实现。",
            "uninstall_plan_main_missing",
        )
    code = handler(list(argv), paths=paths)
    return int(code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage",
        description=(
            "医学监查工作台本地管理入口：启动、停止、运行状态、首次启动检查、"
            "合成离线生命周期演练、G4 合成离线通知与 §15.4 程序、升级准备与卸载计划。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "退出码：0 成功；2 首次启动条件缺失或参数不完整；"
            "3 运行入口被其他应用占用或停止对象不归本应用；"
            "4 升级准备失败且项目数据未更改；"
            "5 同项目维护任务正在执行。"
        ),
    )
    parser.add_argument(
        "--root",
        dest="root",
        default=None,
        help="医学监查分发根目录（默认本脚本所在目录，也可由 MM_MONITORING_LOCAL_ROOT 指定）",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="启动医学监查工作台")
    sub.add_parser("stop", help="停止医学监查工作台")
    sub.add_parser("status", help="查看医学监查工作台运行状态")
    sub.add_parser("preflight", help="首次启动检查")
    synthetic = sub.add_parser("synthetic-lifecycle", help="合成离线一键生命周期演练")
    synthetic.add_argument(
        "--scenario",
        choices=(
            "start-stop-restart",
            "ready",
            "failure",
            "partial",
            "foreign-ownership",
        ),
        default="start-stop-restart",
        help="演练场景（仅内存合成 adapter）",
    )
    sub.add_parser(
        "synthetic-g4-notification",
        help="合成离线 G4 通知 seam 演练（仅内存，不读取项目）",
    )
    g4_154 = sub.add_parser(
        "synthetic-g4-15-4",
        help="合成离线 G4 §15.4 十三项程序（仅临时合成根）",
    )
    g4_154_sub = g4_154.add_subparsers(dest="g4_154_command")
    g4_run = g4_154_sub.add_parser("run", help="运行十三项程序")
    g4_run.add_argument(
        "--runtime-root",
        required=True,
        help="临时合成运行根（须位于系统临时目录）",
    )
    g4_run.add_argument("--project-id", default="synth-g4-cli-154", help="合成项目标识")
    g4_replay = g4_154_sub.add_parser("replay", help="独立 replay canonical manifest")
    g4_replay.add_argument("input", help="manifest JSON 路径；使用 - 从标准输入读取")
    g4_replay.add_argument("--strict", action="store_true", help="遇到不一致时以错误退出")

    prep = sub.add_parser("prepare-upgrade", help="升级准备（保留项目数据保护）")
    prep.add_argument("prep_args", nargs=argparse.REMAINDER, help="升级准备参数")

    uninst = sub.add_parser("uninstall-plan", help="生成卸载数据处置预览计划")
    uninst.add_argument(
        "--include-project-data",
        action="store_true",
        help="预览同时清除项目数据（默认保留项目数据、备份、导出与业务审计）",
    )
    uninst.add_argument(
        "--output-dir",
        default=None,
        help="预览计划输出目录（须显式指定；测试使用临时目录）",
    )
    uninst.add_argument("uninstall_args", nargs=argparse.REMAINDER, help="其他卸载计划参数")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv_list:
        parser.print_help(sys.stderr)
        _emit_err(
            "请指定操作：start、stop、status、preflight、synthetic-lifecycle、"
            "synthetic-g4-notification、synthetic-g4-15-4、prepare-upgrade 或 uninstall-plan。"
        )
        return EXIT_PREFLIGHT_OR_ARGS

    try:
        args, unknown = parser.parse_known_args(argv_list)
    except SystemExit as exc:
        code = int(exc.code or 0)
        return EXIT_OK if code == 0 else EXIT_PREFLIGHT_OR_ARGS

    if args.command is None:
        parser.print_help(sys.stderr)
        _emit_err(
            "请指定操作：start、stop、status、preflight、synthetic-lifecycle、"
            "synthetic-g4-notification、synthetic-g4-15-4、prepare-upgrade 或 uninstall-plan。"
        )
        return EXIT_PREFLIGHT_OR_ARGS

    try:
        if args.command == "synthetic-lifecycle":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_synthetic_lifecycle(str(args.scenario))

        if args.command == "synthetic-g4-notification":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_synthetic_g4_notification()

        if args.command == "synthetic-g4-15-4":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            g4_cmd = getattr(args, "g4_154_command", None)
            if g4_cmd == "run":
                return cmd_synthetic_g4_15_4_run(
                    Path(str(args.runtime_root)),
                    project_id=str(args.project_id),
                )
            if g4_cmd == "replay":
                return cmd_synthetic_g4_15_4_replay(str(args.input), strict=bool(args.strict))
            raise ManageError(
                EXIT_PREFLIGHT_OR_ARGS,
                "请指定 synthetic-g4-15-4 子命令：run 或 replay。",
                "g4_15_4_missing_subcommand",
            )

        root = Path(args.root).expanduser() if args.root else None
        paths = resolve_paths(root)

        if args.command == "preflight":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_preflight(paths)
        if args.command == "status":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_status(paths)
        if args.command == "stop":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_stop(paths)
        if args.command == "start":
            if unknown:
                raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
            return cmd_start(paths)
        if args.command == "prepare-upgrade":
            forwarded = list(getattr(args, "prep_args", []) or [])
            if forwarded and forwarded[0] == "--":
                forwarded = forwarded[1:]
            forwarded = list(unknown) + forwarded
            return cmd_prepare_upgrade(forwarded, paths)
        if args.command == "uninstall-plan":
            forwarded: List[str] = []
            if getattr(args, "include_project_data", False):
                forwarded.append("--include-project-data")
            if getattr(args, "output_dir", None):
                forwarded.extend(["--output-dir", str(args.output_dir)])
            rest = list(getattr(args, "uninstall_args", []) or [])
            if rest and rest[0] == "--":
                rest = rest[1:]
            forwarded.extend(list(unknown) + rest)
            return cmd_uninstall_plan(forwarded, paths)
        raise ManageError(EXIT_PREFLIGHT_OR_ARGS, "参数不完整或无法识别，请查看帮助后重试。")
    except ManageError as err:
        _emit_err(err.message)
        _machine_detail(err.detail)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
