"""第3步状态机专项：入舱四阶段的附加事件流与阶段状态行存储（02_DESIGN §2/§4）。

权威存储不动（A2 jobs/drafts、A4 facts、A1+A3+A5 文档三组）；本模块只是
与 A2 同文件（medical_monitoring_ai.sqlite3）的两张**附加**表：
- ``monitoring_admission_stage_events``：append-only 变迁留痕（审计/F5 恢复
  对账/影子校验/死锁取证）。事件不是权威：判定永远读权威行。
- ``monitoring_admission_stage_state``：阶段状态行（识别聚合态持久化 +
  F5 恢复锚点）。运行门（B5/B6）永不读物化行，门判定仍直读权威。

写入纪律（02_DESIGN §2.3）：事件与状态行的写入必须传入外层 ``conn``，
与权威行的写**同一 sqlite 事务**；跨库点（A4/A5）由各自步骤 best-effort
维护，留痕完整性 < 权威正确性。
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

STAGE_DOCUMENTS = "documents"
STAGE_RECOGNITION = "recognition"
STAGE_MAPPING_CONFIRMATION = "mapping_confirmation"
STAGE_FACTS = "facts"
STAGES = frozenset(
    {
        STAGE_DOCUMENTS,
        STAGE_RECOGNITION,
        STAGE_MAPPING_CONFIRMATION,
        STAGE_FACTS,
    }
)

EVENT_STATE_CHANGED = "state_changed"
EVENT_FAILURE_RECORDED = "failure_recorded"
EVENT_RECOVERY_ACTION = "recovery_action"
EVENT_DEGRADATION = "degradation"
EVENT_GATE_BLOCKED = "gate_blocked"
EVENT_STAGE_VIEW_DIVERGENCE = "stage_view_divergence"
EVENT_TYPES = frozenset(
    {
        EVENT_STATE_CHANGED,
        EVENT_FAILURE_RECORDED,
        EVENT_RECOVERY_ACTION,
        EVENT_DEGRADATION,
        EVENT_GATE_BLOCKED,
        EVENT_STAGE_VIEW_DIVERGENCE,
    }
)

FAILURE_CLASSES = frozenset({"", "infra", "content", "contract"})

# 识别链两个cohort的business_key前缀（mapping_gate.py契约常量；此处字面
# 引用会引入packages依赖，仓储层保持自包含，落地时与契约测试互锁）。
_RECOGNITION_BUSINESS_KEY_PREFIXES = (
    "listing-field-mapping-verifier:",
    "listing-field-mapping:",
)

# 02_DESIGN §5.1：基础设施/提供方类失败码（R11判据上收为库层共享常量，
# 与 monitoring_document_authority_workflow 的 _INFRA_FAILURE_CODES 同源）。
INFRA_FAILURE_CODES = frozenset(
    {
        "provider_runtime_error",
        "provider_sse_error_event",
        "provider_unavailable",
        "provider_timeout",
        "provider_rate_limited",
        "provider_auth_error",
        "provider_overloaded",
        "ai_not_configured",
        "network_error",
        "proxy_error",
    }
)

# 02_DESIGN §2.1/§2.2：两张附加表的DDL。由 MonitoringAiRepository.
# _initialize 在同库内执行（随既有建表路径，幂等）。
STAGE_TABLES_DDL = """
CREATE TABLE IF NOT EXISTS monitoring_admission_stage_events (
    event_id      TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL,
    attempt_id    TEXT NOT NULL DEFAULT '',
    stage         TEXT NOT NULL
                  CHECK(stage IN ('documents','recognition','mapping_confirmation','facts')),
    event_type    TEXT NOT NULL,
    from_state    TEXT NOT NULL DEFAULT '',
    to_state      TEXT NOT NULL DEFAULT '',
    reason_code   TEXT NOT NULL DEFAULT '',
    failure_class TEXT NOT NULL DEFAULT ''
                  CHECK(failure_class IN ('','infra','content','contract')),
    actor         TEXT NOT NULL DEFAULT '',
    detail_json   TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stage_events_attempt
    ON monitoring_admission_stage_events(project_id, attempt_id, created_at);
CREATE TRIGGER IF NOT EXISTS trg_stage_events_no_update BEFORE UPDATE ON monitoring_admission_stage_events
BEGIN SELECT RAISE(ABORT,'admission stage event is immutable'); END;
CREATE TRIGGER IF NOT EXISTS trg_stage_events_no_delete BEFORE DELETE ON monitoring_admission_stage_events
BEGIN SELECT RAISE(ABORT,'admission stage event deletion is forbidden'); END;

CREATE TABLE IF NOT EXISTS monitoring_admission_stage_state (
    project_id  TEXT NOT NULL,
    attempt_id  TEXT NOT NULL,
    stage       TEXT NOT NULL
                CHECK(stage IN ('documents','recognition','mapping_confirmation','facts')),
    state       TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    revision    INTEGER NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (project_id, attempt_id, stage)
);
"""

_ULID_ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ulid() -> str:
    """26字符ULID：48位毫秒时间戳+80位随机，Crockford base32，时序可排序。"""

    value = ((int(time.time() * 1000) & ((1 << 48) - 1)) << 80) | int.from_bytes(
        os.urandom(10), "big"
    )
    return "".join(
        _ULID_ENCODING[(value >> (5 * shift)) & 0x1F] for shift in range(25, -1, -1)
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def recognition_attempt_id(business_key: str) -> str:
    """从识别链business_key解析attempt_id（``{prefix}:{attempt}:{suffix}``）。

    非识别链business_key返回空串——调用方据此跳过事件/状态行写入。
    """

    text = str(business_key or "")
    for prefix in _RECOGNITION_BUSINESS_KEY_PREFIXES:
        if text.startswith(prefix):
            remainder = text[len(prefix):]
            attempt_id = remainder.split(":", 1)[0].strip()
            return attempt_id
    return ""


def failure_class_for(failure_code: str) -> str:
    """02_DESIGN §5.1：infra类失败码→infra；其余失败按内容性归content。

    空失败码（非失败路径）归空串。契约退役由 contract_retirement_code
    表达，不在failure_class里推断。
    """

    code = str(failure_code or "").strip()
    if not code:
        return ""
    return "infra" if code in INFRA_FAILURE_CODES else "content"


# 与 mapping_pipeline._project 的派生口径逐字一致（02_DESIGN §3.2：
# 「三态语义与B1现契约逐字保持」）。行序无关；空cohort→not_started。
_TERMINAL_STATUSES = frozenset(
    {"completed", "failed", "blocked", "stale_input", "cancelled"}
)
_FAILED_TERMINAL_STATUSES = frozenset({"failed", "blocked", "stale_input", "cancelled"})


def aggregate_recognition_state(statuses: Sequence[str]) -> str:
    """识别cohort聚合态：B1派生契约的唯一权威表达（02_DESIGN §3.2）。"""

    values = [str(status or "") for status in statuses]
    if not values:
        return "not_started"
    if all(value == "completed" for value in values):
        return "candidates_ready"
    if all(value in _TERMINAL_STATUSES for value in values) and any(
        value in _FAILED_TERMINAL_STATUSES for value in values
    ):
        return "needs_attention"
    return "generating"


class AdmissionStageStore:
    """入舱阶段事件流与阶段状态行的同库写入/读取。

    ``connect`` 与宿主仓共用同一 sqlite 文件的连接工厂（MonitoringAiRepository
    语义：WAL + 30s超时）。``append_event``/``bump_stage`` 接收外层事务的
    ``conn``，不自行 commit——提交时机归权威写入方。
    """

    def __init__(
        self,
        connect: Callable[[], sqlite3.Connection],
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._connect = connect
        self.clock = clock

    def append_event(
        self,
        conn: sqlite3.Connection,
        *,
        project_id: str,
        attempt_id: str = "",
        stage: str,
        event_type: str,
        from_state: str = "",
        to_state: str = "",
        reason_code: str = "",
        failure_class: str = "",
        actor: str = "system",
        detail: Mapping[str, Any] | None = None,
    ) -> str:
        if stage not in STAGES:
            raise ValueError(f"admission stage is invalid: {stage!r}")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"admission stage event type is invalid: {event_type!r}")
        if failure_class not in FAILURE_CLASSES:
            raise ValueError(
                f"admission stage failure class is invalid: {failure_class!r}"
            )
        event_id = _ulid()
        conn.execute(
            """
            INSERT INTO monitoring_admission_stage_events(
                event_id, project_id, attempt_id, stage, event_type,
                from_state, to_state, reason_code, failure_class,
                actor, detail_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                str(project_id),
                str(attempt_id or ""),
                stage,
                event_type,
                str(from_state or ""),
                str(to_state or ""),
                str(reason_code or "")[:160],
                failure_class,
                str(actor or "system"),
                json.dumps(dict(detail or {}), ensure_ascii=False, sort_keys=True),
                _iso(self.clock()),
            ),
        )
        return event_id

    def bump_stage(
        self,
        conn: sqlite3.Connection,
        *,
        project_id: str,
        attempt_id: str,
        stage: str,
        state: str,
        detail: Mapping[str, Any] | None = None,
    ) -> int:
        """Upsert阶段状态行；revision行级单调自增（轮询If-None-Match/F5对账）。"""

        if stage not in STAGES:
            raise ValueError(f"admission stage is invalid: {stage!r}")
        row = conn.execute(
            """
            SELECT revision FROM monitoring_admission_stage_state
            WHERE project_id = ? AND attempt_id = ? AND stage = ?
            """,
            (str(project_id), str(attempt_id), stage),
        ).fetchone()
        revision = (int(row["revision"]) if row is not None else 0) + 1
        conn.execute(
            """
            INSERT INTO monitoring_admission_stage_state(
                project_id, attempt_id, stage, state, detail_json,
                revision, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, attempt_id, stage) DO UPDATE SET
                state = excluded.state,
                detail_json = excluded.detail_json,
                revision = excluded.revision,
                updated_at = excluded.updated_at
            """,
            (
                str(project_id),
                str(attempt_id),
                stage,
                str(state),
                json.dumps(dict(detail or {}), ensure_ascii=False, sort_keys=True),
                revision,
                _iso(self.clock()),
            ),
        )
        return revision

    def get_stage(
        self, project_id: str, attempt_id: str, stage: str
    ) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT * FROM monitoring_admission_stage_state
                WHERE project_id = ? AND attempt_id = ? AND stage = ?
                """,
                (str(project_id), str(attempt_id), stage),
            ).fetchone()

    def list_events(
        self,
        project_id: str,
        attempt_id: str,
        *,
        after: str = "",
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """时序事件读取；``after``=返回created_at严格晚于该ISO串的事件。"""

        clauses = ["project_id = ?", "attempt_id = ?"]
        parameters: list[Any] = [str(project_id), str(attempt_id)]
        if str(after or "").strip():
            clauses.append("created_at > ?")
            parameters.append(str(after).strip())
        parameters.append(max(1, min(int(limit), 1000)))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM monitoring_admission_stage_events
                WHERE """
                + " AND ".join(clauses)
                + " ORDER BY created_at, event_id LIMIT ?",
                tuple(parameters),
            ).fetchall()
        return [dict(row) for row in rows]
