"""R7 slice-02: isolated product run-entry over ProfileStore + RunBindingStore.

Explicit workspace bootstrap seeds the built-in global default. Constructors
perform no business writes. Effective profiles freeze from four-layer scope
resolution; Monitoring Run bindings are immutable with same-input replay and
fail-closed conflict. Public projections never emit credential values or
medical-object payloads. Stable errors expose ``code`` + Chinese ``message``.

Does not mount product ``main.py``, open ports, call models, or touch real
projects / medical-writing. Stdlib + accepted R7 slice-01 / R6 adapter only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from . import profile_store as ps
from . import run_binding as rb
from .agent_harness import AgentHarnessError, resolve_alias

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "mm-r7-run-entry-v1"
API_PREFIX = "/api/medical-monitoring/r7"

PROFILE_DB_NAME = "execution_profiles.sqlite3"
RUN_BINDING_DB_NAME = "monitoring_run_bindings.sqlite3"

BUILTIN_DEFAULT_USER_CONFIG_NAME = (
    "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
)
BUILTIN_DEFAULT_REASONING_EFFORT = "medium"

# Identity fields cleared from lower layers once a higher layer selects a
# different registered profile / user config. R6 freeze merges
# ``registered_base + layers``; otherwise a lower-layer selector poisons an
# explicit DeepSeek override that omits those keys.
_IDENTITY_OVERRIDE_FIELDS = frozenset(
    {
        "profile_id",
        "profile_revision",
        "user_config_name",
        "requested_provider",
        "requested_model",
        "effective_selector",
        "reasoning_effort",
    }
)

_ERROR_MESSAGES: Dict[str, str] = {
    "global_default_missing": (
        "尚未完成工作区初始化，缺少全局默认执行配置。请先执行工作区引导。"
    ),
    "missing_global_default": (
        "尚未完成工作区初始化，缺少全局默认执行配置。请先执行工作区引导。"
    ),
    "profile_layer_not_found": "未找到指定的执行配置。",
    "profile_not_found": "未找到指定的执行配置。",
    "execution_profile_not_found": "未找到指定的执行配置。",
    "run_binding_not_found": "未找到指定的监查运行绑定。",
    "run_not_found": "未找到指定的监查运行绑定。",
    "unknown_layer_kind": "不支持的执行配置层类型。",
    "global_default_scope_must_be_star": "全局默认配置的作用域必须为「*」。",
    "empty_or_illegal_scope_key": "作用域标识无效或为空。",
    "illegal_scope_key_type": "作用域标识类型无效。",
    "forbidden_secret_field": "不允许写入凭据明文，仅可使用凭据引用。",
    "credential_ref_must_not_be_secret_value": "凭据引用不得包含机密原文。",
    "unknown_override_field": "包含不允许的执行配置字段。",
    "empty_override_payload": "执行配置内容为空，无法保存。",
    "empty_credential_ref": "凭据引用不能为空。",
    "empty_required_field": "必填配置字段为空或非法。",
    "illegal_timeout": "超时时间必须为正整数。",
    "illegal_tuple_field": "工具或回退配置列表格式非法。",
    "illegal_tool_or_fallback_token": "工具或回退标识含有非法字符。",
    "illegal_revision": "修订号非法。",
    "revision_not_found": "未找到指定修订的执行配置。",
    "append_conflict": "追加执行配置修订时发生冲突。",
    "store_closed": "存储已关闭，无法继续操作。",
    "agent_harness_unavailable_for_builtin_seed": "无法加载内置默认执行配置（相邻适配层不可用）。",
    "unsupported_schema_version": "执行配置存储架构版本不受支持。",
    "invalid_payload_type": "执行配置载荷类型无效。",
    "unknown_mode": "不支持的监查运行模式。",
    "unknown_execution_basis": "不支持的执行基线（仅支持全量或增量）。",
    "incremental_requires_prior_accepted_snapshot_ref": (
        "增量运行必须引用先前已接受的快照。"
    ),
    "full_forbids_prior_accepted_snapshot_ref": (
        "全量运行不得携带先前已接受快照引用。"
    ),
    "invalid_run_id": "运行标识无效。",
    "invalid_project_id": "项目标识无效。",
    "invalid_mode": "运行模式无效。",
    "invalid_execution_basis": "执行基线无效。",
    "invalid_data_cutoff": "数据截止标识无效。",
    "invalid_source_revision_id": "数据源修订标识无效。",
    "invalid_prior_accepted_snapshot_ref": "先前已接受快照引用无效。",
    "effective_profile_freeze_failed": "无法冻结有效执行配置。",
    "forged_frozen_profile": "执行配置身份校验失败，已拒绝绑定。",
    "forged_or_corrupt_frozen_profile": "执行配置数据损坏或被篡改。",
    "conflicting_replay_effective_profile": (
        "同一运行标识已绑定不同的执行配置，拒绝覆盖。"
    ),
    "conflicting_replay_data_identity": (
        "同一运行标识已绑定不同的数据身份，拒绝覆盖。"
    ),
    "conflicting_replay": "同一运行标识的绑定冲突，拒绝覆盖。",
    "auto_fallback_forbidden": "禁止隐式回退到其他执行配置，请显式选择。",
    "projection_leaks_secret_pattern": "公共投影疑似泄漏机密内容。",
    "projection_forbidden_field": "公共投影包含禁止字段。",
    "projection_medical_leak": "公共投影不得包含医学对象字段。",
    "builtin_default_mismatch": "内置默认执行配置与合同约定不一致。",
    "invalid_workspace_path": "工作区路径无效。",
    "project_read_only": "项目格式较旧，当前可以只读查看。",
    "project_open_blocked": "暂时无法安全打开此项目，请保留原项目并联系支持。",
    "internal_error": "运行入口内部错误。",
}


class RunEntryError(RuntimeError):
    """Fail-closed product run-entry error with stable code + Chinese message."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = str(code)
        self.message = (
            message
            if message is not None
            else _ERROR_MESSAGES.get(self.code, _ERROR_MESSAGES["internal_error"])
        )
        super().__init__("%s: %s" % (self.code, self.message))

    def as_error_body(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def _split_exc_code(raw: str) -> Tuple[str, str]:
    if ":" in raw:
        head, rest = raw.split(":", 1)
        return head, rest
    return raw, ""


def _raise_mapped(exc: BaseException) -> None:
    """Re-raise as RunEntryError; never returns."""
    if isinstance(exc, RunEntryError):
        raise exc
    raw = str(exc)
    code, detail = _split_exc_code(raw)

    if "auto_fallback" in raw or "automatic fallback" in raw.lower():
        raise RunEntryError("auto_fallback_forbidden") from exc

    alias = {
        "profile_not_found": "profile_layer_not_found",
        "execution_profile_not_found": "profile_layer_not_found",
        "missing_global_default": "global_default_missing",
        "run_not_found": "run_binding_not_found",
        "credential_value_field_forbidden": "forbidden_secret_field",
        "projection_contains_credential_value_field": "forbidden_secret_field",
        "public_projection_leaked_credential_material": "projection_leaks_secret_pattern",
        "audit_projection_leaked_credential_material": "projection_leaks_secret_pattern",
    }.get(code, code)

    if alias in _ERROR_MESSAGES:
        # Public errors deliberately omit adapter exception details. Those
        # strings contain backend identifiers and may later include user input;
        # the stable code remains available for diagnostics and UI mapping.
        raise RunEntryError(alias, _ERROR_MESSAGES[alias]) from exc

    raise RunEntryError("internal_error", _ERROR_MESSAGES["internal_error"]) from exc


def _layers_for_freeze(
    records: Tuple[Optional[ps.ProfileLayerRecord], ...],
) -> Tuple[Optional[rb.ExecutionProfileLayer], ...]:
    """Build freeze layers; strip lower-layer identity below a profile switch."""
    dicts: list = []
    for rec in records:
        if rec is None:
            dicts.append(None)
        else:
            dicts.append(dict(rec.as_override_dict()))

    winner_idx: Optional[int] = None
    for idx, payload in enumerate(dicts):
        if payload is None:
            continue
        if "profile_id" in payload or "user_config_name" in payload:
            winner_idx = idx

    if winner_idx is not None:
        winner = dicts[winner_idx]
        if (
            winner is not None
            and "user_config_name" in winner
            and "profile_id" not in winner
        ):
            try:
                winner["profile_id"] = resolve_alias(
                    str(winner["user_config_name"])
                ).profile_id
            except AgentHarnessError as exc:
                _raise_mapped(exc)

    if winner_idx is not None:
        for idx in range(winner_idx):
            payload = dicts[idx]
            if payload is None:
                continue
            for key in list(payload.keys()):
                if key in _IDENTITY_OVERRIDE_FIELDS:
                    del payload[key]
            if not payload:
                dicts[idx] = None

    out = []
    for payload in dicts:
        if payload is None:
            out.append(None)
        else:
            out.append(rb.ExecutionProfileLayer(**payload))
    return tuple(out)


@dataclass(frozen=True)
class BootstrapResult:
    """Result of explicit workspace bootstrap."""

    profile: Dict[str, Any]
    replayed: bool
    record_id: str
    revision: int

    @property
    def projection(self) -> Dict[str, Any]:
        """Alias for API unwrap helpers that expect ``projection``."""
        return self.profile


@dataclass(frozen=True)
class ProfileWriteResult:
    """Result of appending one execution-profile revision."""

    profile: Dict[str, Any]
    record_id: str
    revision: int

    @property
    def projection(self) -> Dict[str, Any]:
        return self.profile


@dataclass(frozen=True)
class BindRunResult:
    """Result of immutable Monitoring Run bind (or same-input replay)."""

    binding: Dict[str, Any]
    replayed: bool
    binding_digest: str
    execution_profile_id: str
    execution_profile_digest: str

    @property
    def projection(self) -> Dict[str, Any]:
        """Alias for API unwrap helpers that expect ``projection``."""
        return self.binding


# ---------------------------------------------------------------------------
# Workspace run entry
# ---------------------------------------------------------------------------


class MonitoringRunEntry:
    """Product-facing run entry for one isolated workspace directory.

    Construction opens stores only; it does **not** seed defaults. Call
    :meth:`bootstrap_workspace` explicitly (idempotent).
    """

    def __init__(
        self,
        workspace_dir: Union[str, Path],
        *,
        profile_db_name: str = PROFILE_DB_NAME,
        run_binding_db_name: str = RUN_BINDING_DB_NAME,
    ) -> None:
        root = Path(workspace_dir)
        runtime_path = root / "runtime" / "monitoring_runtime.sqlite3"
        member_paths = (
            (root / profile_db_name, "profile_store"),
            (root / run_binding_db_name, "run_binding"),
            (root / "launch_registry.sqlite3", "launch_registry"),
            (root / "risk_rules.sqlite3", "risk_rules"),
        )
        if root.exists() and runtime_path.exists():
            from .schema_manifest import SchemaClassification, inspect_project_schema
            inspection = inspect_project_schema(root)
            if inspection.classification is not SchemaClassification.CURRENT:
                raise RunEntryError(
                    "project_read_only"
                    if inspection.classification is SchemaClassification.LEGACY
                    else "project_open_blocked"
                )
        elif root.exists():
            from .schema_manifest import SchemaClassification, inspect_member
            for path, member in member_paths:
                if not path.exists():
                    continue
                report = inspect_member(path, member)
                if report.classification is not SchemaClassification.CURRENT:
                    raise RunEntryError(
                        "project_read_only"
                        if report.classification is SchemaClassification.LEGACY
                        else "project_open_blocked"
                    )
        if str(workspace_dir).strip() == "":
            raise RunEntryError("invalid_workspace_path")
        if root.is_file() or root.suffix == ".sqlite3":
            raise RunEntryError("invalid_workspace_path")
        self.workspace_dir = root
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.profile_store = ps.ProfileStore(self.workspace_dir / profile_db_name)
        self.run_binding_store = rb.RunBindingStore(
            self.workspace_dir / run_binding_db_name
        )

    def close(self) -> None:
        self.profile_store.close()
        self.run_binding_store.close()

    def reopen(self) -> None:
        self.profile_store.reopen()
        self.run_binding_store.reopen()

    def __enter__(self) -> "MonitoringRunEntry":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- bootstrap ----------------------------------------------------------

    def bootstrap_workspace(self) -> BootstrapResult:
        """Explicitly seed built-in global_default; idempotent (no new revision)."""
        try:
            latest = self.profile_store.latest_revision(
                ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY
            )
            if latest is None:
                record = self.profile_store.seed_builtin_global_default()
                replayed = False
            else:
                # Bootstrap owns revision 1. Later global-default revisions are
                # normal configuration overlays and must not make an otherwise
                # initialized workspace impossible to bootstrap again.
                record = self.profile_store.get_revision(
                    ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY, 1
                )
                replayed = True
            self._assert_builtin_default(record)
            projection = self.profile_store.public_projection(record)
            ps.assert_projection_has_no_credential_values(projection)
            return BootstrapResult(
                profile=projection,
                replayed=replayed,
                record_id=record.record_id,
                revision=record.revision,
            )
        except (ps.ProfileStoreError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    @staticmethod
    def _assert_builtin_default(record: ps.ProfileLayerRecord) -> None:
        fields = record.fields
        name = str(fields.get("user_config_name", ""))
        effort = str(fields.get("reasoning_effort", ""))
        if name != BUILTIN_DEFAULT_USER_CONFIG_NAME:
            raise RunEntryError("builtin_default_mismatch")
        if effort != BUILTIN_DEFAULT_REASONING_EFFORT:
            raise RunEntryError("builtin_default_mismatch")
        if "deepseek" in name.lower():
            raise RunEntryError("builtin_default_mismatch")

    # -- execution profiles -------------------------------------------------

    def append_execution_profile(
        self,
        layer_kind: str,
        scope_key: str,
        fields: Mapping[str, Any],
    ) -> ProfileWriteResult:
        """Append one versioned layer revision; return public projection."""
        try:
            record = self.profile_store.append_revision(layer_kind, scope_key, fields)
            projection = self.profile_store.public_projection(record)
            ps.assert_projection_has_no_credential_values(projection)
            return ProfileWriteResult(
                profile=projection,
                record_id=record.record_id,
                revision=record.revision,
            )
        except (ps.ProfileStoreError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    def get_execution_profile(
        self, layer_kind: str, scope_key: str
    ) -> Dict[str, Any]:
        """Return latest public projection for ``(layer_kind, scope_key)``."""
        try:
            record = self.profile_store.latest_revision(layer_kind, scope_key)
            if record is None:
                raise RunEntryError("profile_layer_not_found")
            projection = self.profile_store.public_projection(record)
            ps.assert_projection_has_no_credential_values(projection)
            return projection
        except (ps.ProfileStoreError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    def resolve_scope_layers(
        self,
        *,
        capability_scope_key: str = "",
        project_scope_key: str = "",
        run_override_scope_key: str = "",
        require_global_default: bool = True,
    ) -> Tuple[Optional[ps.ProfileLayerRecord], ...]:
        """Load four layers by precedence; fail closed on missing references.

        Empty scope keys skip that optional layer. A non-empty scope with no
        stored revision is ``profile_layer_not_found``. Missing
        ``global_default/*`` fails when ``require_global_default`` is true.
        """
        try:
            global_rec = self.profile_store.latest_revision(
                ps.LAYER_GLOBAL_DEFAULT, ps.GLOBAL_SCOPE_KEY
            )
            if require_global_default and global_rec is None:
                raise RunEntryError("global_default_missing")

            def _required(kind: str, scope: str) -> Optional[ps.ProfileLayerRecord]:
                if not scope:
                    return None
                rec = self.profile_store.latest_revision(kind, scope)
                if rec is None:
                    raise RunEntryError(
                        "profile_layer_not_found",
                        "%s（%s/%s）"
                        % (_ERROR_MESSAGES["profile_layer_not_found"], kind, scope),
                    )
                return rec

            return (
                global_rec,
                _required(ps.LAYER_CAPABILITY_AGENT, capability_scope_key),
                _required(ps.LAYER_PROJECT, project_scope_key),
                _required(ps.LAYER_RUN_OVERRIDE, run_override_scope_key),
            )
        except (ps.ProfileStoreError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    def freeze_effective_profile_for_scopes(
        self,
        *,
        run_id: str,
        capability_scope_key: str = "",
        project_scope_key: str = "",
        run_override_scope_key: str = "",
    ) -> rb.FrozenExecutionProfile:
        """Resolve four layers and freeze one effective R6 profile."""
        records = self.resolve_scope_layers(
            capability_scope_key=capability_scope_key,
            project_scope_key=project_scope_key,
            run_override_scope_key=run_override_scope_key,
            require_global_default=True,
        )
        layers = _layers_for_freeze(records)
        try:
            frozen = rb.freeze_effective_profile(*layers, run_id=run_id)
            if list(frozen.fallback_profile_ids):
                raise RunEntryError("auto_fallback_forbidden")
            return frozen
        except (rb.RunBindingError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    # -- runs ---------------------------------------------------------------

    def bind_run(
        self,
        *,
        run_id: str,
        project_id: str,
        mode: str,
        execution_basis: str,
        data_cutoff: str,
        source_revision_id: str,
        prior_accepted_snapshot_ref: Optional[str] = None,
        capability_scope_key: str = "",
        project_scope_key: str = "",
        run_override_scope_key: str = "",
    ) -> BindRunResult:
        """Freeze effective profile from scopes and immutable-bind the Run."""
        try:
            existed_before = False
            try:
                self.run_binding_store.get(run_id)
                existed_before = True
            except rb.RunBindingError as exc:
                code, _ = _split_exc_code(str(exc))
                if code != "run_binding_not_found":
                    _raise_mapped(exc)

            frozen = self.freeze_effective_profile_for_scopes(
                run_id=run_id,
                capability_scope_key=capability_scope_key,
                project_scope_key=project_scope_key,
                run_override_scope_key=run_override_scope_key,
            )
            binding = self.run_binding_store.bind(
                run_id=run_id,
                project_id=project_id,
                mode=mode,
                execution_basis=execution_basis,
                data_cutoff=data_cutoff,
                source_revision_id=source_revision_id,
                frozen=frozen,
                prior_accepted_snapshot_ref=prior_accepted_snapshot_ref,
            )
            projection = rb.public_projection(binding)
            return BindRunResult(
                binding=projection,
                replayed=existed_before,
                binding_digest=binding.binding_digest,
                execution_profile_id=binding.execution_profile_id,
                execution_profile_digest=binding.execution_profile_digest,
            )
        except (ps.ProfileStoreError, rb.RunBindingError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Return public projection for an existing Monitoring Run binding."""
        try:
            binding = self.run_binding_store.get(run_id)
            return rb.public_projection(binding)
        except (rb.RunBindingError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    def reopen_and_validate_run(self, run_id: str) -> Dict[str, Any]:
        """Close/reopen binding store and return public projection."""
        try:
            binding = self.run_binding_store.reopen_and_validate(run_id)
            self.profile_store.reopen()
            return rb.public_projection(binding)
        except (rb.RunBindingError, ps.ProfileStoreError, RunEntryError) as exc:
            _raise_mapped(exc)
            raise  # pragma: no cover

    # Aliases for worker_02 RunEntryPort / adapter duck-typing.
    def bind_monitoring_run(self, **kwargs: Any) -> BindRunResult:
        return self.bind_run(**kwargs)

    def get_monitoring_run(self, run_id: str) -> Dict[str, Any]:
        return self.get_run(run_id)


# Peer aliases (api create_app probes RunEntry / ProductRunEntry).
ProductRunEntry = MonitoringRunEntry
RunEntry = MonitoringRunEntry


__all__ = [
    "SCHEMA_VERSION",
    "API_PREFIX",
    "PROFILE_DB_NAME",
    "RUN_BINDING_DB_NAME",
    "BUILTIN_DEFAULT_USER_CONFIG_NAME",
    "BUILTIN_DEFAULT_REASONING_EFFORT",
    "RunEntryError",
    "BootstrapResult",
    "ProfileWriteResult",
    "BindRunResult",
    "MonitoringRunEntry",
    "ProductRunEntry",
    "RunEntry",
]
