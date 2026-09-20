from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterable, Optional
from uuid import uuid4

from packages.contracts.workbench_contracts import UserProjectCreateRequest


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class UserProjectRecord:
    project_id: str
    project_code: str
    project_name: str
    indication: str
    product_name: str
    study_phase: str
    protocol_id: str
    protocol_version: str
    protocol_date: str
    entry_mode: str
    status: str
    created_by: str
    created_at: str
    updated_at: str
    modules: tuple[str, ...] = ("medical_writing",)


class UserProjectStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create(self, request: UserProjectCreateRequest) -> UserProjectRecord:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM user_projects WHERE idempotency_key = ?",
                (request.idempotency_key,),
            ).fetchone()
            if existing is not None:
                return self._record(existing)
            duplicate = connection.execute(
                "SELECT project_id FROM user_projects WHERE lower(project_code) = lower(?)",
                (request.project_code,),
            ).fetchone()
            if duplicate is not None:
                raise ValueError(f"项目编号已存在：{request.project_code}")
            now = datetime.now(timezone.utc).isoformat()
            project_id = f"proj_user_{uuid4().hex[:12]}"
            modules = getattr(request, "modules", None) or ["medical_writing"]
            import json as _json
            connection.execute(
                """
                INSERT INTO user_projects (
                    project_id, project_code, project_name, indication, product_name,
                    study_phase, protocol_id, protocol_version, protocol_date,
                    entry_mode, status, created_by, idempotency_key, created_at, updated_at,
                    modules
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    request.project_code,
                    request.project_name,
                    request.indication,
                    request.product_name,
                    request.study_phase,
                    request.protocol_id,
                    request.protocol_version,
                    request.protocol_date,
                    request.entry_mode,
                    request.actor,
                    request.idempotency_key,
                    now,
                    now,
                    _json.dumps(list(modules), ensure_ascii=False),
                ),
            )
            row = connection.execute(
                "SELECT * FROM user_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            return self._record(row)

    def get(self, project_id: str) -> Optional[UserProjectRecord]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM user_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return self._record(row) if row is not None else None

    def archive_project(self, project_id: str) -> bool:
        """归档项目（软删除）：列表/选择器隐藏，磁盘数据保留可逆。"""
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO project_visibility (project_id, archived_at) "
                "VALUES (?, ?)",
                (project_id, _utcnow_iso()),
            )
            connection.commit()
        return True

    def restore_project(self, project_id: str) -> bool:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM project_visibility WHERE project_id = ?", (project_id,)
            )
            connection.commit()
        return True

    def project_modules(self, project_id: str) -> tuple[str, ...]:
        record = self.get(project_id)
        return record.modules if record else ()

    def set_project_modules(self, project_id: str, modules: list[str]) -> bool:
        import json as _json
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE user_projects SET modules = ?, updated_at = ? WHERE project_id = ?",
                (_json.dumps(list(modules), ensure_ascii=False), _utcnow_iso(), project_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def archived_project_ids(self) -> set[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT project_id FROM project_visibility"
            ).fetchall()
        return {str(row["project_id"]) for row in rows}

    def records(self) -> Iterable[UserProjectRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM user_projects ORDER BY created_at DESC, project_id"
            ).fetchall()
        return [self._record(row) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_visibility (
                    project_id TEXT PRIMARY KEY,
                    archived_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_projects (
                    project_id TEXT PRIMARY KEY,
                    project_code TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    indication TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    study_phase TEXT NOT NULL,
                    protocol_id TEXT NOT NULL,
                    protocol_version TEXT NOT NULL,
                    protocol_date TEXT NOT NULL,
                    entry_mode TEXT NOT NULL CHECK(entry_mode IN ('from_zero', 'synopsis_import')),
                    status TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS user_projects_code_ci ON user_projects(lower(project_code))"
            )
            # 迁移：modules列（JSON数组，旧行默认写作）
            columns = connection.execute("PRAGMA table_info(user_projects)").fetchall()
            if all(str(col[1]) != "modules" for col in columns):
                connection.execute(
                    "ALTER TABLE user_projects ADD COLUMN modules TEXT NOT NULL DEFAULT '[\"medical_writing\"]'"
                )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _record(row: sqlite3.Row) -> UserProjectRecord:
        import json as _json
        fields = {}
        for field in UserProjectRecord.__dataclass_fields__:
            if field == "modules":
                try:
                    fields[field] = tuple(_json.loads(row["modules"] or "[]")) or ("medical_writing",)
                except (TypeError, ValueError, KeyError):
                    fields[field] = ("medical_writing",)
            elif field in row.keys():
                fields[field] = row[field]
        return UserProjectRecord(**fields)
