"""Synthetic, stdlib-only R7 Slice-07C-1 run-setup contracts.

This module owns data selection and deterministic projections only.  It does
not prepare or start runs, publish results, call providers, or open services.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


SCHEMA_VERSION = "mm-r7-slice07c1-run-setup-v1"
RUN_SETUP_SCHEMA_VERSION = SCHEMA_VERSION
TEMPLATE_VERSION = "mm-r7-slice07c1-mode-template-v1"

MODE_DAILY = "daily"
MODE_PRE_LOCK = "pre_lock"
MODE_POST_LOCK_PRE_CFDI = "post_lock_pre_cfdi"
SUPPORTED_MODES = (MODE_DAILY, MODE_PRE_LOCK, MODE_POST_LOCK_PRE_CFDI)

BASIS_FULL = "full"
BASIS_INCREMENTAL = "incremental"
SUPPORTED_EXECUTION_BASES = (BASIS_FULL, BASIS_INCREMENTAL)

DIFF_ADDED = "added"
DIFF_REVISED = "revised"
DIFF_UNCHANGED = "unchanged"
DIFF_DELETED = "deleted"
DIFF_CANNOT_COMPARE = "cannot_compare"
DIFF_STATUSES = (
    DIFF_ADDED,
    DIFF_REVISED,
    DIFF_UNCHANGED,
    DIFF_DELETED,
    DIFF_CANNOT_COMPARE,
)

_DIFF_TEXT = {
    DIFF_ADDED: "新增",
    DIFF_REVISED: "修订",
    DIFF_UNCHANGED: "未变化",
    DIFF_DELETED: "删除/不再出现",
    DIFF_CANNOT_COMPARE: "无法比较",
}
_MODE_TEXT = {
    MODE_DAILY: "日常监查",
    MODE_PRE_LOCK: "锁库前监查",
    MODE_POST_LOCK_PRE_CFDI: "核查前监查",
}
_BASIS_TEXT = {BASIS_FULL: "全量", BASIS_INCREMENTAL: "增量"}
_ERROR_MESSAGES = {
    "invalid_project_id": "医学监查项目标识无效。",
    "invalid_mode": "不支持的监查运行模式。",
    "invalid_execution_basis": "不支持的运行基准。",
    "invalid_snapshot": "数据批次定义无效。",
    "run_data_not_ready": "当前项目的数据仍在核对字段对应关系，确认完成前不会启动医学监查。",
    "invalid_baseline": "既往比较基线定义无效。",
    "baseline_not_published": "比较基线必须是已发布的同项目结果。",
    "baseline_mode_mismatch": "比较基线必须与本次监查使用相同模式。",
    "no_stable_business_key": "当前数据尚不能与上次结果逐项比较。",
    "ambiguous_business_key": "当前数据的业务键存在歧义，尚不能逐项比较。",
    "empty_risk_rule": "特殊关注点不能为空。",
    "ambiguous_risk_rule": "特殊关注点无法可靠拆解，请选择解释候选。",
    "risk_rule_not_confirmed": "特殊关注规则尚未确认，不能登记。",
    "risk_rule_preview_not_found": "待确认的关注规则已失效，请重新预览后再确认。",
    "risk_rule_project_mismatch": "特殊关注规则不属于当前项目。",
    "risk_rule_not_found": "未找到指定的特殊关注规则修订。",
    "risk_rule_conflict": "特殊关注规则修订发生冲突，拒绝覆盖。",
    "invalid_rule_revision": "特殊关注规则修订无效。",
    "invalid_work_units": "模式工作范围定义无效。",
    "incremental_requires_diff": "日常增量运行必须提供可比较的数据差异。",
    "incremental_not_supported_for_mode": "该监查模式只支持全量运行。",
}


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("canonical mappings require string keys")
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not accept non-finite numbers")
        return value
    raise TypeError("unsupported canonical value: %s" % type(value).__name__)


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def public_revision_token(revision_token: str) -> str:
    """Project an internal revision identity to its stable product token."""
    token = _required_text(revision_token, "invalid_rule_revision")
    return "rule-revision:" + content_digest(token)[:24]


def _opaque_token(prefix: str, value: Any) -> str:
    return "%s:%s" % (prefix, content_digest(value)[:24])


class RunSetupError(ValueError):
    """Fail-closed data-contract error with a stable code and Chinese text."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = str(code)
        self.message = message or _ERROR_MESSAGES.get(self.code, "运行设置无效。")
        super().__init__("%s: %s" % (self.code, self.message))

    def as_error_body(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def _required_text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise RunSetupError(code)
    return value


def _copy_row(value: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RunSetupError("invalid_snapshot")
    try:
        return _jsonable(value)
    except (TypeError, ValueError) as exc:
        raise RunSetupError("invalid_snapshot") from exc


def _normalize_fields(fields: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    normalized = (fields,) if isinstance(fields, str) else tuple(fields)
    if any(not isinstance(item, str) or not item.strip() for item in normalized):
        raise RunSetupError("invalid_snapshot")
    return normalized


@dataclass(frozen=True)
class DataSnapshot:
    snapshot_ref: str
    project_id: str
    data_cutoff: str
    rows: Tuple[Mapping[str, Any], ...] = ()
    key_fields: Tuple[str, ...] = ()
    imported_at: str = ""
    scope_description: str = "当前完整数据快照"
    source_revision_id: Optional[str] = None

    def __post_init__(self) -> None:
        _required_text(self.snapshot_ref, "invalid_snapshot")
        _required_text(self.project_id, "invalid_project_id")
        _required_text(self.data_cutoff, "invalid_snapshot")
        fields = _normalize_fields(self.key_fields)
        rows = tuple(_copy_row(row) for row in self.rows)
        if not fields and rows:
            if all("canonical_key" in row for row in rows):
                fields = ("canonical_key",)
            elif all("business_key" in row for row in rows):
                fields = ("business_key",)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "key_fields", fields)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, project_id: str = "") -> "DataSnapshot":
        if isinstance(value, DataSnapshot):
            return value
        if not isinstance(value, Mapping):
            raise RunSetupError("invalid_snapshot")
        fields = value.get("key_fields", value.get("business_key_fields", ())) or ()
        if isinstance(fields, str):
            fields = (fields,)
        return cls(
            snapshot_ref=str(value.get("snapshot_ref", value.get("snapshot_token", value.get("ref", ""))) or ""),
            project_id=str(value.get("project_id", project_id) or ""),
            data_cutoff=str(value.get("data_cutoff", value.get("cutoff", "")) or ""),
            rows=tuple(value.get("rows", value.get("listing", value.get("data", ()))) or ()),
            key_fields=tuple(fields),
            imported_at=str(value.get("imported_at", value.get("import_time", "")) or ""),
            scope_description=str(value.get("scope_description", value.get("scope", "当前完整数据快照")) or ""),
            source_revision_id=(
                str(value["source_revision_id"]) if value.get("source_revision_id") is not None else None
            ),
        )

    @property
    def snapshot_token(self) -> str:
        return _opaque_token("snapshot", {"project_id": self.project_id, "snapshot_ref": self.snapshot_ref})

    def public_projection(self) -> Dict[str, Any]:
        return {
            "snapshot_token": self.snapshot_token,
            "data_cutoff": self.data_cutoff,
            "imported_at": self.imported_at,
            "scope_description": self.scope_description,
            "row_count": len(self.rows),
            "can_compare": _rows_have_stable_keys(self.rows, self.key_fields),
        }

    def as_dict(self) -> Dict[str, Any]:
        return self.public_projection()

    def internal_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_ref": self.snapshot_ref,
            "project_id": self.project_id,
            "data_cutoff": self.data_cutoff,
            "rows": _jsonable(self.rows),
            "key_fields": list(self.key_fields),
            "imported_at": self.imported_at,
            "scope_description": self.scope_description,
            "source_revision_id": self.source_revision_id,
        }


@dataclass(frozen=True)
class PublishedBaseline:
    project_id: str
    mode: str
    snapshot_ref: str
    data_cutoff: str
    run_id: str = ""
    published: bool = True
    published_at: str = ""
    scope_description: str = ""
    fixed_total: bool = False
    rows: Tuple[Mapping[str, Any], ...] = ()
    key_fields: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required_text(self.project_id, "invalid_project_id")
        if self.mode not in SUPPORTED_MODES:
            raise RunSetupError("invalid_mode")
        fields = _normalize_fields(self.key_fields)
        rows = tuple(_copy_row(row) for row in self.rows)
        if not fields and rows:
            if all("canonical_key" in row for row in rows):
                fields = ("canonical_key",)
            elif all("business_key" in row for row in rows):
                fields = ("business_key",)
        if not isinstance(self.published, bool) or not isinstance(self.fixed_total, bool):
            raise RunSetupError("invalid_baseline")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "key_fields", fields)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, project_id: str = "") -> "PublishedBaseline":
        if isinstance(value, PublishedBaseline):
            return value
        if not isinstance(value, Mapping):
            raise RunSetupError("invalid_baseline")
        fields = value.get("key_fields", value.get("business_key_fields", ())) or ()
        if isinstance(fields, str):
            fields = (fields,)
        status = value.get("status")
        return cls(
            project_id=str(value.get("project_id", project_id) or ""),
            mode=str(value.get("mode", "") or ""),
            snapshot_ref=str(value.get("snapshot_ref", value.get("snapshot_token", value.get("snapshot_id", ""))) or ""),
            data_cutoff=str(value.get("data_cutoff", value.get("cutoff", "")) or ""),
            run_id=str(value.get("run_id", value.get("run_token", "")) or ""),
            published=bool(value.get("published", status == "published")),
            published_at=str(value.get("published_at", value.get("published_time", "")) or ""),
            scope_description=str(value.get("scope_description", value.get("scope", "")) or ""),
            fixed_total=bool(value.get("fixed_total", value.get("is_fixed_total", False))),
            rows=tuple(value.get("rows", value.get("listing", ())) or ()),
            key_fields=tuple(fields),
        )

    @property
    def baseline_token(self) -> str:
        return _opaque_token(
            "baseline",
            {"project_id": self.project_id, "mode": self.mode, "snapshot_ref": self.snapshot_ref, "run_id": self.run_id},
        )

    @property
    def snapshot_token(self) -> str:
        return self.baseline_token

    def public_projection(self, *, recommended: bool = False) -> Dict[str, Any]:
        return {
            "baseline_token": self.baseline_token,
            "mode": self.mode,
            "mode_text": _MODE_TEXT[self.mode],
            "data_cutoff": self.data_cutoff,
            "published_at": self.published_at,
            "scope_description": self.scope_description or "同项目已发布结果",
            "recommended": bool(recommended),
            "selectable": bool(self.published and not self.fixed_total),
        }

    def as_dict(self) -> Dict[str, Any]:
        return self.public_projection()


def _key_fields_for(rows: Sequence[Mapping[str, Any]], key_fields: Optional[Sequence[str]]) -> Tuple[str, ...]:
    if key_fields is not None:
        fields = _normalize_fields(key_fields)
        if not fields:
            raise RunSetupError("no_stable_business_key")
        return fields
    for row in rows:
        if "canonical_key" in row:
            return ("canonical_key",)
        if "business_key" in row:
            return ("business_key",)
    return ()


def _row_key(row: Mapping[str, Any], fields: Tuple[str, ...]) -> str:
    values = []
    for name in fields:
        if name not in row or row[name] is None or (isinstance(row[name], str) and not row[name].strip()):
            raise RunSetupError("no_stable_business_key")
        values.append(_jsonable(row[name]))
    return canonical_json({"fields": list(fields), "values": values})


def _rows_have_stable_keys(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bool:
    if not fields:
        return False
    seen = set()
    try:
        for row in rows:
            key = _row_key(row, tuple(fields))
            if key in seen:
                return False
            seen.add(key)
    except (RunSetupError, TypeError, ValueError):
        return False
    return True


def _query_attribution(row: Optional[Mapping[str, Any]]) -> str:
    if row and row.get("revision_attribution") == "query_driven":
        evidence = row.get("query_ref", row.get("query_id", row.get("query_reference")))
        if isinstance(evidence, str) and evidence.strip():
            return "Query 后修订影响"
    return "本轮数据修订变化"


@dataclass(frozen=True)
class CanonicalDiffRow:
    key: str
    status: str
    current: Optional[Mapping[str, Any]]
    prior: Optional[Mapping[str, Any]]
    changed_fields: Tuple[str, ...] = ()
    attribution_text: str = ""

    def __post_init__(self) -> None:
        if self.status not in DIFF_STATUSES[:-1]:
            raise RunSetupError("invalid_snapshot")
        if self.current is not None:
            object.__setattr__(self, "current", _copy_row(self.current))
        if self.prior is not None:
            object.__setattr__(self, "prior", _copy_row(self.prior))
        object.__setattr__(self, "changed_fields", tuple(sorted(self.changed_fields)))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "canonical_key": self.key,
            "status": self.status,
            "status_text": _DIFF_TEXT[self.status],
            "current": _jsonable(self.current),
            "prior": _jsonable(self.prior),
            "changed_fields": list(self.changed_fields),
            "attribution_text": self.attribution_text,
        }


@dataclass(frozen=True)
class CanonicalKeyedDiff:
    key_fields: Tuple[str, ...]
    rows: Tuple[CanonicalDiffRow, ...]
    comparable: bool
    reason: str = ""

    @property
    def status(self) -> str:
        return "comparable" if self.comparable else DIFF_CANNOT_COMPARE

    @property
    def digest(self) -> str:
        return content_digest(self.as_dict(include_digest=False))

    @property
    def counts(self) -> Dict[str, int]:
        result = {status: 0 for status in DIFF_STATUSES}
        for row in self.rows:
            result[row.status] += 1
        return result

    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = {
            "key_fields": list(self.key_fields),
            "comparable": self.comparable,
            "status": self.status,
            "reason": self.reason,
            "rows": [row.as_dict() for row in self.rows],
            "counts": self.counts,
        }
        if include_digest:
            body["diff_digest"] = self.digest
        return body


def canonical_keyed_diff(
    current_rows: Iterable[Mapping[str, Any]],
    prior_rows: Iterable[Mapping[str, Any]],
    key_fields: Optional[Sequence[str]] = None,
) -> CanonicalKeyedDiff:
    try:
        current = tuple(_copy_row(row) for row in current_rows)
        prior = tuple(_copy_row(row) for row in prior_rows)
    except (TypeError, ValueError) as exc:
        raise RunSetupError("no_stable_business_key") from exc
    fields = _key_fields_for(current + prior, key_fields)
    if not fields:
        if not current and not prior:
            return CanonicalKeyedDiff((), (), True)
        return CanonicalKeyedDiff((), (), False, _ERROR_MESSAGES["no_stable_business_key"])

    def index(rows: Sequence[Mapping[str, Any]]) -> Tuple[Dict[str, Mapping[str, Any]], Optional[str]]:
        result: Dict[str, Mapping[str, Any]] = {}
        for row in rows:
            try:
                key = _row_key(row, fields)
            except RunSetupError:
                return {}, _ERROR_MESSAGES["no_stable_business_key"]
            if key in result:
                return {}, _ERROR_MESSAGES["ambiguous_business_key"]
            result[key] = row
        return result, None

    current_by_key, current_error = index(current)
    prior_by_key, prior_error = index(prior)
    if current_error or prior_error:
        return CanonicalKeyedDiff(fields, (), False, current_error or prior_error or _ERROR_MESSAGES["ambiguous_business_key"])

    rows: List[CanonicalDiffRow] = []
    for key in sorted(set(current_by_key) | set(prior_by_key)):
        now = current_by_key.get(key)
        before = prior_by_key.get(key)
        if before is None:
            status, changed = DIFF_ADDED, ()
        elif now is None:
            status, changed = DIFF_DELETED, ()
        elif canonical_json(now) == canonical_json(before):
            status, changed = DIFF_UNCHANGED, ()
        else:
            status = DIFF_REVISED
            changed = tuple(sorted(
                name for name in set(now) | set(before)
                if name not in fields and canonical_json(now.get(name)) != canonical_json(before.get(name))
            ))
        rows.append(CanonicalDiffRow(
            key=key,
            status=status,
            current=now,
            prior=before,
            changed_fields=changed,
            attribution_text=_query_attribution(now) if status == DIFF_REVISED else "",
        ))
    return CanonicalKeyedDiff(fields, tuple(rows), True)


@dataclass(frozen=True)
class RiskRuleCandidate:
    candidate_id: str
    subject: str
    condition: str
    applicable_scope: str
    starting_run: str
    explanation: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "subject": self.subject,
            "condition": self.condition,
            "applicable_scope": self.applicable_scope,
            "starting_run": self.starting_run,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RiskRulePreview:
    project_id: str
    source_text: str
    state: str
    candidates: Tuple[RiskRuleCandidate, ...]
    reason: str = ""
    preview_token: str = ""

    @property
    def confirmable(self) -> bool:
        return self.state == "ready" and len(self.candidates) == 1

    def as_dict(self) -> Dict[str, Any]:
        token = self.preview_token or _opaque_token(
            "rule-preview",
            {"project_id": self.project_id, "source_text": self.source_text},
        )
        return {
            "project_id": self.project_id,
            "preview_token": token,
            "status": "待确认的关注规则",
            "state": self.state,
            "confirmable": self.confirmable,
            "source_text": self.source_text,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RiskRuleRevision:
    project_id: str
    revision: int
    candidate_id: str
    subject: str
    condition: str
    applicable_scope: str
    starting_run: str
    summary: str
    created_at: str = ""
    revision_token: str = ""
    rule_digest: str = ""
    selectable: bool = True

    def __post_init__(self) -> None:
        _required_text(self.project_id, "invalid_project_id")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision <= 0:
            raise RunSetupError("invalid_rule_revision")
        if not self.subject or not self.condition or not self.summary:
            raise RunSetupError("invalid_rule_revision")
        token = self.revision_token or "rule-revision:%s:%d" % (self.project_id, self.revision)
        digest = self.rule_digest or content_digest({
            "project_id": self.project_id,
            "revision": self.revision,
            "candidate_id": self.candidate_id,
            "subject": self.subject,
            "condition": self.condition,
            "applicable_scope": self.applicable_scope,
            "starting_run": self.starting_run,
            "summary": self.summary,
        })
        object.__setattr__(self, "revision_token", token)
        object.__setattr__(self, "rule_digest", digest)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "revision_token": self.revision_token,
            "summary": self.summary,
            "applicable_scope": self.applicable_scope,
            "starting_run": self.starting_run,
            "selectable": bool(self.selectable),
            "created_at": self.created_at,
        }


def _candidate_for_text(text: str, scope: str, starting_run: str) -> Tuple[RiskRuleCandidate, ...]:
    lowered = text.casefold()
    if "alt" in lowered or "ast" in lowered or "肝" in text:
        return (RiskRuleCandidate("hepatic-data", "肝功能相关数据", text, scope, starting_run, "按用户输入保留肝功能相关数据条件，待确认。"),)
    if any(token in text for token in ("发热", "感染", "体温")):
        return (RiskRuleCandidate("infection-event", "感染/发热相关事件", text, scope, starting_run, "按用户输入保留事件关注条件，待确认。"),)
    if any(token in text for token in ("出血", "血栓", "心电", "QT")) or "qt" in lowered:
        return (RiskRuleCandidate("safety-event", "安全性事件或检查", text, scope, starting_run, "按用户输入保留安全性关注条件，待确认。"),)
    return (
        RiskRuleCandidate("value-or-event", "数据值变化", text, scope, starting_run, "可按数据值变化解释。"),
        RiskRuleCandidate("event-or-action", "事件或处置记录", text, scope, starting_run, "可按事件或处置记录解释。"),
    )


def preview_risk_rule(
    project_id: str,
    source_text: str,
    *,
    applicable_scope: str = "项目内全部适用范围",
    starting_run: str = "本次确认后明确选择的运行",
) -> RiskRulePreview:
    project = _required_text(project_id, "invalid_project_id")
    if not isinstance(source_text, str) or not source_text.strip():
        raise RunSetupError("empty_risk_rule")
    text = source_text.strip()
    scope = _required_text(applicable_scope, "invalid_rule_revision")
    start = _required_text(starting_run, "invalid_rule_revision")
    candidates = _candidate_for_text(text, scope, start)
    state = "ready" if len(candidates) == 1 else "ambiguous"
    return RiskRulePreview(
        project_id=project,
        source_text=text,
        state=state,
        candidates=candidates,
        reason="" if state == "ready" else _ERROR_MESSAGES["ambiguous_risk_rule"],
    )


def _assert_current_schema(path_value: Optional[Union[str, Path]]) -> None:
    """Reject an existing non-current risk-rule database before writes."""
    if path_value is None or str(path_value) == ":memory:":
        return
    path = Path(path_value)
    if not path.exists():
        return
    from .schema_manifest import SchemaClassification, inspect_member

    report = inspect_member(path, "risk_rules")
    if report.classification is not SchemaClassification.CURRENT:
        raise RunSetupError("unsupported_schema_version")


class RiskRuleRegistry:
    """Append-only project rule revisions backed by optional SQLite."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        _assert_current_schema(db_path)
        self.db_path = str(db_path) if db_path is not None else ":memory:"
        self._lock = threading.RLock()
        self._previews: Dict[str, RiskRulePreview] = {}
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS r7_risk_rule_revisions (
                project_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                revision_token TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                condition TEXT NOT NULL,
                applicable_scope TEXT NOT NULL,
                starting_run TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                rule_digest TEXT NOT NULL,
                selectable INTEGER NOT NULL,
                idempotency_key TEXT,
                idempotency_fingerprint TEXT,
                PRIMARY KEY(project_id, revision),
                UNIQUE(project_id, revision_token),
                UNIQUE(project_id, idempotency_key)
            )"""
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "RiskRuleRegistry":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def preview(self, project_id: str, source_text: str, **kwargs: Any) -> RiskRulePreview:
        value = preview_risk_rule(project_id, source_text, **kwargs)
        with self._lock:
            self._previews[value.as_dict()["preview_token"]] = value
        return value

    def _draft(self, project_id: str, draft: Union[RiskRulePreview, Mapping[str, Any], str]) -> RiskRulePreview:
        if isinstance(draft, RiskRulePreview):
            return draft
        if isinstance(draft, str):
            with self._lock:
                value = self._previews.get(draft)
            if value is None:
                raise RunSetupError("risk_rule_preview_not_found")
            return value
        if not isinstance(draft, Mapping):
            raise RunSetupError("risk_rule_not_confirmed")
        token = draft.get("preview_token")
        if token and not draft.get("candidates"):
            with self._lock:
                value = self._previews.get(str(token))
            if value is None:
                raise RunSetupError("risk_rule_preview_not_found")
            return value
        candidates = tuple(
            item if isinstance(item, RiskRuleCandidate) else RiskRuleCandidate(
                candidate_id=str(item.get("candidate_id", "")),
                subject=str(item.get("subject", "")),
                condition=str(item.get("condition", "")),
                applicable_scope=str(item.get("applicable_scope", "")),
                starting_run=str(item.get("starting_run", "")),
                explanation=str(item.get("explanation", "")),
            )
            for item in draft.get("candidates", ())
            if isinstance(item, Mapping)
        )
        return RiskRulePreview(
            project_id=str(draft.get("project_id", "")),
            source_text=str(draft.get("source_text", "")),
            state=str(draft.get("state", "ambiguous")),
            candidates=candidates,
            reason=str(draft.get("reason", "")),
            preview_token=str(draft.get("preview_token", "")),
        )

    def append_revision(
        self,
        project_id: str,
        draft: Union[RiskRulePreview, Mapping[str, Any], str],
        *,
        candidate_id: Optional[str] = None,
        starting_run: Optional[str] = None,
        created_at: str = "",
        idempotency_key: Optional[str] = None,
    ) -> RiskRuleRevision:
        project = _required_text(project_id, "invalid_project_id")
        preview = self._draft(project, draft)
        if preview.project_id != project:
            raise RunSetupError("risk_rule_project_mismatch")
        if not preview.confirmable:
            raise RunSetupError("ambiguous_risk_rule" if preview.state == "ambiguous" else "risk_rule_not_confirmed")
        candidate = preview.candidates[0]
        chosen = candidate_id or candidate.candidate_id
        if chosen != candidate.candidate_id:
            raise RunSetupError("risk_rule_not_confirmed")
        start = starting_run or candidate.starting_run
        if idempotency_key is not None:
            idem = _required_text(idempotency_key, "invalid_rule_revision")
        else:
            idem = None
        fingerprint = content_digest({
            "project_id": project,
            "candidate_id": candidate.candidate_id,
            "subject": candidate.subject,
            "condition": candidate.condition,
            "applicable_scope": candidate.applicable_scope,
            "starting_run": start,
        })
        with self._lock:
            if idem is not None:
                prior = self._conn.execute(
                    "SELECT revision, idempotency_fingerprint FROM r7_risk_rule_revisions WHERE project_id = ? AND idempotency_key = ?",
                    (project, idem),
                ).fetchone()
                if prior is not None:
                    if prior["idempotency_fingerprint"] != fingerprint:
                        raise RunSetupError("risk_rule_conflict")
                    return self.get_revision(project, int(prior["revision"]))
            row = self._conn.execute(
                "SELECT COALESCE(MAX(revision), 0) AS revision FROM r7_risk_rule_revisions WHERE project_id = ?",
                (project,),
            ).fetchone()
            revision = int(row["revision"]) + 1
            summary = "%s：%s" % (candidate.subject, candidate.condition)
            record = RiskRuleRevision(
                project_id=project,
                revision=revision,
                revision_token="rule-revision:%s:%d" % (project, revision),
                candidate_id=candidate.candidate_id,
                subject=candidate.subject,
                condition=candidate.condition,
                applicable_scope=candidate.applicable_scope,
                starting_run=start,
                summary=summary,
                created_at=created_at,
                rule_digest=content_digest({
                    "project_id": project,
                    "revision": revision,
                    "candidate_id": candidate.candidate_id,
                    "subject": candidate.subject,
                    "condition": candidate.condition,
                    "applicable_scope": candidate.applicable_scope,
                    "starting_run": start,
                    "summary": summary,
                }),
            )
            try:
                self._conn.execute(
                    """INSERT INTO r7_risk_rule_revisions
                    (project_id, revision, revision_token, candidate_id, subject,
                     condition, applicable_scope, starting_run, summary, created_at,
                     rule_digest, selectable, idempotency_key, idempotency_fingerprint)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.project_id, record.revision, record.revision_token,
                        record.candidate_id, record.subject, record.condition,
                        record.applicable_scope, record.starting_run, record.summary,
                        record.created_at, record.rule_digest, int(record.selectable),
                        idem, fingerprint if idem is not None else None,
                    ),
                )
                self._conn.commit()
            except sqlite3.IntegrityError as exc:
                self._conn.rollback()
                raise RunSetupError("risk_rule_conflict") from exc
            return record

    def _row_to_revision(self, row: sqlite3.Row) -> RiskRuleRevision:
        return RiskRuleRevision(
            project_id=str(row["project_id"]),
            revision=int(row["revision"]),
            revision_token=str(row["revision_token"]),
            candidate_id=str(row["candidate_id"]),
            subject=str(row["subject"]),
            condition=str(row["condition"]),
            applicable_scope=str(row["applicable_scope"]),
            starting_run=str(row["starting_run"]),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
            rule_digest=str(row["rule_digest"]),
            selectable=bool(row["selectable"]),
        )

    def get_revision(self, project_id: str, revision: int) -> RiskRuleRevision:
        project = _required_text(project_id, "invalid_project_id")
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM r7_risk_rule_revisions WHERE project_id = ? AND revision = ?",
                (project, int(revision)),
            ).fetchone()
        if row is None:
            raise RunSetupError("risk_rule_not_found")
        return self._row_to_revision(row)

    def list_revisions(self, project_id: str) -> Tuple[RiskRuleRevision, ...]:
        project = _required_text(project_id, "invalid_project_id")
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM r7_risk_rule_revisions WHERE project_id = ? ORDER BY revision ASC",
                (project,),
            ).fetchall()
        return tuple(self._row_to_revision(row) for row in rows)

    def resolve_public_token(
        self, project_id: str, token: str
    ) -> RiskRuleRevision:
        """Resolve a public token to one confirmed revision in this project."""
        public_token = _required_text(token, "invalid_rule_revision")
        for revision in self.list_revisions(project_id):
            if public_revision_token(revision.revision_token) == public_token:
                return revision
        raise RunSetupError("risk_rule_not_found")

    def public_revisions(self, project_id: str) -> List[Dict[str, Any]]:
        return [revision.as_dict() for revision in self.list_revisions(project_id)]


@dataclass(frozen=True)
class ModeOption:
    mode: str
    label: str
    description: str
    execution_basis_options: Tuple[str, ...]
    default_execution_basis: str
    published_baselines: Tuple[PublishedBaseline, ...] = ()
    available: bool = True
    disabled_reason: str = ""
    recommended: bool = False
    recommendation_reason: str = ""
    basis_disabled_reasons: Mapping[str, str] = field(default_factory=dict)

    def public_projection(self) -> Dict[str, Any]:
        latest = self.published_baselines[0] if self.published_baselines else None
        return {
            "mode": self.mode,
            "label": self.label,
            "description": self.description,
            "execution_basis_options": [
                {
                    "value": basis,
                    "label": _BASIS_TEXT[basis],
                    "available": basis not in self.basis_disabled_reasons,
                    "disabled_reason": self.basis_disabled_reasons.get(basis, ""),
                }
                for basis in self.execution_basis_options
            ],
            "default_execution_basis": self.default_execution_basis,
            "requires_published_same_mode_baseline": self.mode == MODE_DAILY and self.default_execution_basis == BASIS_INCREMENTAL,
            "baseline_options": [
                item.public_projection(recommended=item is latest) for item in self.published_baselines
            ],
            "available": bool(self.available),
            "disabled_reason": self.disabled_reason,
            "recommended": bool(self.recommended),
            "recommendation_reason": self.recommendation_reason,
        }

    def as_dict(self) -> Dict[str, Any]:
        return self.public_projection()


@dataclass(frozen=True)
class RunSetupOptions:
    project_id: str
    data_batches: Tuple[DataSnapshot, ...]
    current_data: Optional[DataSnapshot]
    modes: Tuple[ModeOption, ...]
    rule_revisions: Tuple[RiskRuleRevision, ...] = ()
    recommended_mode: str = MODE_DAILY
    recommendation_reason: str = ""

    def public_projection(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "project_id": self.project_id,
            "data_batches": [batch.public_projection() for batch in self.data_batches],
            "current_data": self.current_data.public_projection() if self.current_data else None,
            "modes": [mode.public_projection() for mode in self.modes],
            "rule_revisions": [revision.as_dict() for revision in self.rule_revisions],
            "recommended_mode": self.recommended_mode,
            "recommendation_reason": self.recommendation_reason,
        }

    def as_dict(self) -> Dict[str, Any]:
        return self.public_projection()


class RunSetupCatalog:
    def __init__(
        self,
        *,
        project_id: str = "",
        snapshots: Iterable[Union[DataSnapshot, Mapping[str, Any]]] = (),
        published_baselines: Iterable[Union[PublishedBaseline, Mapping[str, Any]]] = (),
        risk_rule_registry: Optional[RiskRuleRegistry] = None,
        last_mode_by_project: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.project_id = project_id
        if project_id:
            _required_text(project_id, "invalid_project_id")
        self.snapshots = tuple(
            item if isinstance(item, DataSnapshot) else DataSnapshot.from_mapping(item, project_id=project_id)
            for item in snapshots
        )
        self.published_baselines = tuple(
            item if isinstance(item, PublishedBaseline) else PublishedBaseline.from_mapping(item, project_id=project_id)
            for item in published_baselines
        )
        self.risk_rule_registry = risk_rule_registry or RiskRuleRegistry()
        self.last_mode_by_project = dict(last_mode_by_project or {})

    def _for_project(self, project_id: str) -> Tuple[Tuple[DataSnapshot, ...], Tuple[PublishedBaseline, ...]]:
        project = _required_text(project_id, "invalid_project_id")
        return (
            tuple(item for item in self.snapshots if item.project_id == project),
            tuple(item for item in self.published_baselines if item.project_id == project),
        )

    @staticmethod
    def _sorted_snapshots(items: Iterable[DataSnapshot]) -> Tuple[DataSnapshot, ...]:
        return tuple(sorted(items, key=lambda item: (item.data_cutoff, item.imported_at, item.snapshot_ref), reverse=True))

    @staticmethod
    def _eligible_baselines(items: Iterable[PublishedBaseline], mode: str) -> Tuple[PublishedBaseline, ...]:
        return tuple(sorted(
            (item for item in items if item.mode == mode and item.published and not item.fixed_total),
            key=lambda item: (item.published_at, item.data_cutoff, item.snapshot_ref),
            reverse=True,
        ))

    def get_options(
        self,
        project_id: str,
        *,
        current_snapshot_ref: Optional[str] = None,
        current_snapshot_token: Optional[str] = None,
    ) -> RunSetupOptions:
        project = _required_text(project_id, "invalid_project_id")
        snapshots, all_baselines = self._for_project(project)
        ordered_snapshots = self._sorted_snapshots(snapshots)
        selector = current_snapshot_token or current_snapshot_ref
        current: Optional[DataSnapshot] = None
        if selector is not None:
            current = next((item for item in ordered_snapshots if item.snapshot_ref == selector or item.snapshot_token == selector), None)
            if current is None:
                raise RunSetupError("invalid_snapshot")
        elif ordered_snapshots:
            current = ordered_snapshots[0]

        selected_mode = self.last_mode_by_project.get(project, MODE_DAILY)
        if selected_mode not in SUPPORTED_MODES:
            selected_mode = MODE_DAILY
        daily = self._eligible_baselines(all_baselines, MODE_DAILY)
        pre_lock = self._eligible_baselines(all_baselines, MODE_PRE_LOCK)
        current_comparable = current is not None and _rows_have_stable_keys(current.rows, current.key_fields)
        daily_available = bool(daily) and current_comparable and all(_rows_have_stable_keys(item.rows, item.key_fields) for item in daily)
        if daily_available:
            daily_basis = BASIS_INCREMENTAL
            daily_reason = "默认使用同项目最近一次已发布的日常监查结果进行逐项比较。"
            daily_disabled = ""
        elif not daily:
            daily_basis = BASIS_FULL
            daily_reason = "暂无同项目已发布的日常监查基线，本次可先重新全面分析。"
            daily_disabled = "暂无合格同项目已发布基线，增量方案不可选。"
        else:
            daily_basis = BASIS_FULL
            daily_reason = "当前数据尚不能与上次结果逐项比较，本次可重新全面分析。"
            daily_disabled = _ERROR_MESSAGES["no_stable_business_key"]
        modes = (
            ModeOption(
                MODE_DAILY, _MODE_TEXT[MODE_DAILY], "默认分析本次新增或修订的数据；首次运行可重新全面分析。",
                (BASIS_INCREMENTAL, BASIS_FULL), daily_basis, daily, True, daily_disabled,
                selected_mode == MODE_DAILY, daily_reason,
                {BASIS_INCREMENTAL: daily_disabled} if daily_disabled else {},
            ),
            ModeOption(
                MODE_PRE_LOCK, _MODE_TEXT[MODE_PRE_LOCK], "使用当前完整数据全面复核，并可比较上一轮锁库前监查。",
                (BASIS_FULL,), BASIS_FULL, pre_lock, True, "", selected_mode == MODE_PRE_LOCK,
                "优先推荐最近一次已发布的同项目锁库前结果作为比较基线。" if pre_lock else "可直接进行首次锁库前全面复核，尚无已发布比较基线。",
            ),
            ModeOption(
                MODE_POST_LOCK_PRE_CFDI, _MODE_TEXT[MODE_POST_LOCK_PRE_CFDI], "固定当前完整数据范围，形成核查前全面复核与现场自查清单。",
                (BASIS_FULL,), BASIS_FULL, (), True, "", selected_mode == MODE_POST_LOCK_PRE_CFDI,
                "核查前监查只使用当前完整数据，不选择其他模式结果作为比较基线。",
            ),
        )
        return RunSetupOptions(
            project,
            ordered_snapshots,
            current,
            modes,
            self.risk_rule_registry.list_revisions(project),
            selected_mode,
            next(item.recommendation_reason for item in modes if item.mode == selected_mode),
        )

    def preview_risk_rule(self, project_id: str, source_text: str, **kwargs: Any) -> RiskRulePreview:
        return self.risk_rule_registry.preview(project_id, source_text, **kwargs)

    def append_risk_rule(self, project_id: str, draft: Union[RiskRulePreview, Mapping[str, Any], str], **kwargs: Any) -> RiskRuleRevision:
        return self.risk_rule_registry.append_revision(project_id, draft, **kwargs)

    def list_risk_rules(self, project_id: str) -> Tuple[RiskRuleRevision, ...]:
        return self.risk_rule_registry.list_revisions(project_id)

    def baseline_candidates(self, project_id: str, mode: str) -> Tuple[PublishedBaseline, ...]:
        if mode not in SUPPORTED_MODES:
            raise RunSetupError("invalid_mode")
        _, baselines = self._for_project(project_id)
        return self._eligible_baselines(baselines, mode)

    def snapshot_for_token(self, project_id: str, snapshot_selector: str) -> DataSnapshot:
        project = _required_text(project_id, "invalid_project_id")
        selector = _required_text(snapshot_selector, "invalid_snapshot")
        snapshots, _ = self._for_project(project)
        for item in snapshots:
            if item.snapshot_ref == selector or item.snapshot_token == selector:
                return item
        raise RunSetupError("invalid_snapshot")

    def baseline_for_token(self, project_id: str, mode: str, baseline_selector: str) -> PublishedBaseline:
        selector = _required_text(baseline_selector, "invalid_baseline")
        for item in self.baseline_candidates(project_id, mode):
            if item.snapshot_ref == selector or item.baseline_token == selector:
                return item
        raise RunSetupError("baseline_not_published")

    def close(self) -> None:
        self.risk_rule_registry.close()


@dataclass(frozen=True)
class TemplateNode:
    node_key: str
    stage: str
    label: str
    scope: str = "项目范围"
    target_ref: str = "project"
    mandatory: bool = True


@dataclass(frozen=True)
class ModeTemplate:
    mode: str
    version: str
    nodes: Tuple[TemplateNode, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "version": self.version,
            "nodes": [asdict(node) for node in self.nodes],
        }


_COMMON_TEMPLATE_NODES = (
    TemplateNode("protocol-controls", "common", "资料与方案控制点"),
    TemplateNode("data-integrity", "common", "数据结构与完整性"),
    TemplateNode("patient-journey", "common", "Patient Journey"),
    TemplateNode("safety-domains", "common", "AE/MH/CM/IP/PD 风险"),
    TemplateNode("eligibility-labs", "common", "入排与检验检查"),
    TemplateNode("project-site-summary", "common", "项目与中心汇总"),
    TemplateNode("quality-control", "common", "全流程 QC"),
)
_MODE_TEMPLATE_NODES = {
    MODE_DAILY: (
        TemplateNode("daily-data-change", MODE_DAILY, "新增/修订数据逻辑与科学性核查"),
        TemplateNode("daily-trend-change", MODE_DAILY, "风险、疗效与安全性趋势变化"),
        TemplateNode("daily-query-draft", MODE_DAILY, "结构化 Query 草稿"),
    ),
    MODE_PRE_LOCK: (
        TemplateNode("pre-lock-full-risk", MODE_PRE_LOCK, "当前全量风险"),
        TemplateNode("pre-lock-query-impact", MODE_PRE_LOCK, "Query 后修订影响"),
        TemplateNode("pre-lock-open-issues", MODE_PRE_LOCK, "多轮未关闭问题"),
        TemplateNode("pre-lock-package", MODE_PRE_LOCK, "锁库前核查包"),
    ),
    MODE_POST_LOCK_PRE_CFDI: (
        TemplateNode("post-lock-fixed-report", MODE_POST_LOCK_PRE_CFDI, "固定总量全量报告"),
        TemplateNode("post-lock-concentration", MODE_POST_LOCK_PRE_CFDI, "中心/受试者风险集中视图"),
        TemplateNode("post-lock-site-checklist", MODE_POST_LOCK_PRE_CFDI, "现场自查 checklist"),
        TemplateNode("post-lock-external-review", MODE_POST_LOCK_PRE_CFDI, "外部报告审阅"),
    ),
}
MODE_TEMPLATES = {
    mode: ModeTemplate(mode, TEMPLATE_VERSION, _COMMON_TEMPLATE_NODES + nodes)
    for mode, nodes in _MODE_TEMPLATE_NODES.items()
}


def get_mode_template(mode: str) -> ModeTemplate:
    if mode not in MODE_TEMPLATES:
        raise RunSetupError("invalid_mode")
    return MODE_TEMPLATES[mode]


@dataclass(frozen=True)
class WorkUnit:
    work_unit_id: str
    stage: str
    label: str
    scope: str
    target_ref: str
    ordinal: int
    mandatory: bool = True
    depends_on: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "work_unit_id": self.work_unit_id,
            "stage": self.stage,
            "label": self.label,
            "scope": self.scope,
            "target_ref": self.target_ref,
            "ordinal": self.ordinal,
            "mandatory": self.mandatory,
            "depends_on": list(self.depends_on),
        }


# R7 runtime consumers use the R1 ManifestWorkUnit shape; this alias keeps the
# generated contract directly usable without importing a second adapter type.
ManifestWorkUnit = WorkUnit


@dataclass(frozen=True)
class WorkUnitManifest:
    mode: str
    execution_basis: str
    template_version: str
    current_snapshot_token: str
    prior_baseline_token: Optional[str]
    units: Tuple[WorkUnit, ...]
    source_diff_digest: Optional[str] = None

    @property
    def denominator(self) -> int:
        return len(self.units)

    @property
    def manifest_digest(self) -> str:
        return content_digest(self.as_dict(include_digest=False))

    def as_list(self) -> List[Dict[str, Any]]:
        return [unit.as_dict() for unit in self.units]

    def as_dict(self, *, include_digest: bool = True) -> Dict[str, Any]:
        body = {
            "mode": self.mode,
            "execution_basis": self.execution_basis,
            "template_version": self.template_version,
            "current_snapshot_token": self.current_snapshot_token,
            "prior_baseline_token": self.prior_baseline_token,
            "denominator": self.denominator,
            "work_units": self.as_list(),
            "source_diff_digest": self.source_diff_digest,
        }
        if include_digest:
            body["manifest_digest"] = self.manifest_digest
        return body

    def __getitem__(self, index: int) -> WorkUnit:
        return self.units[index]

    def __iter__(self):
        return iter(self.units)

    def __len__(self) -> int:
        return len(self.units)


def _coerce_diff(value: Optional[Union[CanonicalKeyedDiff, Mapping[str, Any]]]) -> Optional[CanonicalKeyedDiff]:
    if value is None or isinstance(value, CanonicalKeyedDiff):
        return value
    if not isinstance(value, Mapping):
        raise RunSetupError("incremental_requires_diff")
    rows = []
    for raw in value.get("rows", ()):
        if not isinstance(raw, Mapping):
            raise RunSetupError("incremental_requires_diff")
        rows.append(CanonicalDiffRow(
            key=str(raw.get("canonical_key", raw.get("key", ""))),
            status=str(raw.get("status", "")),
            current=raw.get("current"),
            prior=raw.get("prior"),
            changed_fields=tuple(raw.get("changed_fields", ())),
            attribution_text=str(raw.get("attribution_text", "")),
        ))
    return CanonicalKeyedDiff(tuple(value.get("key_fields", ())), tuple(rows), bool(value.get("comparable", False)), str(value.get("reason", "")))


def _coerce_rule_revision(value: Union[RiskRuleRevision, Mapping[str, Any], str]) -> Tuple[str, str]:
    if isinstance(value, RiskRuleRevision):
        return value.revision_token, value.summary
    if isinstance(value, Mapping):
        token = str(value.get("revision_token", value.get("rule_token", value.get("revision", ""))))
        if not token.strip():
            raise RunSetupError("invalid_rule_revision")
        return token, str(value.get("summary", value.get("label", "特殊关注规则")))
    token = str(value)
    if not token.strip():
        raise RunSetupError("invalid_rule_revision")
    return token, "特殊关注规则"


def generate_work_units(
    mode: str,
    execution_basis: str,
    *,
    current_snapshot_token: str = "current",
    prior_baseline_token: Optional[str] = None,
    diff: Optional[Union[CanonicalKeyedDiff, Mapping[str, Any]]] = None,
    rule_revisions: Iterable[Union[RiskRuleRevision, Mapping[str, Any], str]] = (),
) -> WorkUnitManifest:
    if mode not in SUPPORTED_MODES:
        raise RunSetupError("invalid_mode")
    if execution_basis not in SUPPORTED_EXECUTION_BASES:
        raise RunSetupError("invalid_execution_basis")
    if mode != MODE_DAILY and execution_basis != BASIS_FULL:
        raise RunSetupError("incremental_not_supported_for_mode")
    current_token = _required_text(current_snapshot_token, "invalid_snapshot")
    if prior_baseline_token is not None:
        prior_baseline_token = _required_text(prior_baseline_token, "invalid_baseline")
    canonical_diff = _coerce_diff(diff)
    if execution_basis == BASIS_INCREMENTAL:
        if canonical_diff is None:
            raise RunSetupError("incremental_requires_diff")
        if not canonical_diff.comparable:
            raise RunSetupError("no_stable_business_key")
        if not prior_baseline_token:
            raise RunSetupError("baseline_not_published")

    template = get_mode_template(mode)
    units: List[WorkUnit] = []
    previous_id: Optional[str] = None

    def append_unit(unit_id: str, stage: str, label: str, scope: str, target_ref: str, mandatory: bool = True) -> None:
        nonlocal previous_id
        unit = WorkUnit(
            unit_id, stage, label, scope, target_ref, len(units) + 1,
            mandatory, (previous_id,) if previous_id else (),
        )
        units.append(unit)
        previous_id = unit_id

    for node in template.nodes:
        append_unit(
            "r7:%s:%s:%s" % (mode, template.version, node.node_key),
            node.stage, node.label, node.scope, node.target_ref, node.mandatory,
        )

    if execution_basis == BASIS_INCREMENTAL:
        changed = tuple(row for row in canonical_diff.rows if row.status in (DIFF_ADDED, DIFF_REVISED, DIFF_DELETED))
        if not changed:
            append_unit(
                "r7:%s:%s:diff-empty" % (mode, template.version),
                "daily_diff", "日常增量范围：本次无新增、修订或删除数据", "未变化数据不重复分析", "diff:empty",
            )
        else:
            for row in changed:
                status_text = _DIFF_TEXT[row.status]
                append_unit(
                    "r7:%s:%s:diff:%s" % (mode, template.version, content_digest(row.key)[:16]),
                    "daily_diff", "日常增量：%s数据" % status_text,
                    "%s（业务键已规范化）" % status_text, row.key,
                )

    rules = {}
    for raw_rule in rule_revisions:
        token, summary = _coerce_rule_revision(raw_rule)
        rules.setdefault(token, summary)
    for token in sorted(rules):
        append_unit(
            "r7:%s:%s:rule:%s" % (mode, template.version, content_digest(token)[:16]),
            "special_risk_rule", "特殊关注：%s" % rules[token], "项目级已确认规则", token,
        )

    return WorkUnitManifest(
        mode, execution_basis, template.version, current_token, prior_baseline_token,
        tuple(units), canonical_diff.digest if canonical_diff is not None else None,
    )


__all__ = [
    "SCHEMA_VERSION", "RUN_SETUP_SCHEMA_VERSION", "TEMPLATE_VERSION",
    "MODE_DAILY", "MODE_PRE_LOCK", "MODE_POST_LOCK_PRE_CFDI", "SUPPORTED_MODES",
    "BASIS_FULL", "BASIS_INCREMENTAL", "SUPPORTED_EXECUTION_BASES",
    "DIFF_ADDED", "DIFF_REVISED", "DIFF_UNCHANGED", "DIFF_DELETED", "DIFF_CANNOT_COMPARE",
    "RunSetupError", "canonical_json", "canonical_json_bytes", "content_digest", "public_revision_token",
    "DataSnapshot", "PublishedBaseline", "CanonicalDiffRow", "CanonicalKeyedDiff", "canonical_keyed_diff",
    "RiskRuleCandidate", "RiskRulePreview", "RiskRuleRevision", "preview_risk_rule", "RiskRuleRegistry",
    "ModeOption", "RunSetupOptions", "RunSetupCatalog", "TemplateNode", "ModeTemplate", "MODE_TEMPLATES",
    "get_mode_template", "WorkUnit", "ManifestWorkUnit", "WorkUnitManifest", "generate_work_units",
]
