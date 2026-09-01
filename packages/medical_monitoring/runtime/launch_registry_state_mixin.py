"""Continuity transitions and public run-state access."""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import sqlite3
import threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, Union
from uuid import uuid4

from .continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    PlanValidationError,
    validate_carry_forward_plan,
)

from .launch_schema import (
    BASE_DDL as _BASE_DDL,
    CONTINUITY_DDL as _CONTINUITY_DDL,
    CONTINUITY_INDEX_DDL as _CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL as _CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL as _CONTINUITY_PLANS_DDL,
    LAUNCH_DDL as _DDL,
    PUBLICATION_DDL as _PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL as _RESULT_CONTEXT_INDEX_DDL,
)

from .launch_registry_contracts import *
from .launch_registry_contracts import (
    _ALLOWED_TRANSITIONS, _CONTINUITY_ALLOWED_TRANSITIONS, _required_text,
)

class LaunchRegistryStateMixin:
    """Cohesive methods extracted from the launch registry."""

    def _update_continuity_status_locked(
        self,
        connection: sqlite3.Connection,
        project: str,
        plan: CarryForwardPlan,
        target_status: str,
        *,
        expected_status: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
        failure_prefix: str = "continuity.status",
    ) -> CarryForwardPlan:
        if target_status not in CONTINUITY_PLAN_STATE_VALUES:
            raise LaunchRegistryError("illegal_continuity_transition")
        if (
            target_status in (CONTINUITY_PLAN_STATE_VERIFIED, CONTINUITY_PLAN_STATE_PUBLISHED)
            and not plan.r6_output_set_digest
        ):
            raise LaunchRegistryError("continuity_plan_not_verified")
        if expected_status is not None:
            expected_status = _required_text(
                expected_status, "continuity_plan_cas_conflict"
            )
            if plan.status != expected_status:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        if expected_plan_digest is not None:
            expected_plan_digest = _required_text(
                expected_plan_digest, "continuity_plan_cas_conflict"
            )
            if plan.plan_digest != expected_plan_digest:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        if target_status not in _CONTINUITY_ALLOWED_TRANSITIONS[plan.status]:
            raise LaunchRegistryError("illegal_continuity_transition")
        if target_status == plan.status:
            return plan
        if target_status == CONTINUITY_PLAN_STATE_PUBLISHED:
            raise LaunchRegistryError("continuity_plan_not_verified")
        updated_at = self._now()
        transitioned = replace(
            plan,
            status=target_status,
            updated_at=updated_at,
            plan_digest="",
        )
        updated = connection.execute(
            "UPDATE r7_continuity_plans SET status = ?, plan_json = ?, "
            "updated_at = ? WHERE project_id = ? AND plan_id = ? "
            "AND status = ? AND plan_digest = ?",
            (
                transitioned.status,
                self._continuity_plan_json(transitioned),
                transitioned.updated_at,
                project,
                self._continuity_plan_id(plan),
                plan.status,
                plan.plan_digest,
            ),
        )
        if updated.rowcount != 1:
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        self._inject_failure(failure_prefix + ".after_update")
        self._inject_failure("continuity.after_status_update")
        return transitioned
    def _mark_continuity_plan_published_locked(
        self,
        connection: sqlite3.Connection,
        project: str,
        plan: CarryForwardPlan,
        *,
        updated_at: Optional[str] = None,
    ) -> CarryForwardPlan:
        if plan.status == CONTINUITY_PLAN_STATE_PUBLISHED:
            return plan
        if plan.status != CONTINUITY_PLAN_STATE_VERIFIED or not plan.r6_output_set_digest:
            raise LaunchRegistryError("continuity_plan_not_verified")
        transitioned = replace(
            plan,
            status=CONTINUITY_PLAN_STATE_PUBLISHED,
            updated_at=updated_at or self._now(),
            plan_digest="",
        )
        updated = connection.execute(
            "UPDATE r7_continuity_plans SET status = ?, plan_json = ?, "
            "updated_at = ? WHERE project_id = ? AND plan_id = ? "
            "AND status = ? AND plan_digest = ?",
            (
                transitioned.status,
                self._continuity_plan_json(transitioned),
                transitioned.updated_at,
                project,
                self._continuity_plan_id(plan),
                CONTINUITY_PLAN_STATE_VERIFIED,
                plan.plan_digest,
            ),
        )
        if updated.rowcount != 1:
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        self._inject_failure("finalize.after_continuity_update")
        self._inject_failure("continuity.publish.after_update")
        return transitioned

    def update_continuity_plan_status(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        status: str = CONTINUITY_PLAN_STATE_VERIFIED,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_status: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        if (
            plan_id is None
            and self._default_project_id
            and isinstance(project_id, str)
            and project_id.startswith("r7-plan-")
            and target_run_id in CONTINUITY_PLAN_STATE_VALUES
            and status == CONTINUITY_PLAN_STATE_VERIFIED
        ):
            plan_id = project_id
            project_id = None
            status = target_run_id
            target_run_id = None
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        target_status = _required_text(
            status, "illegal_continuity_transition"
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = self._continuity_plan_row(
                    connection,
                    project,
                    target_run_id=target,
                    plan_id=continuity_id,
                )
                if row is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                plan = self._row_to_continuity_plan(connection, row)
                transitioned = self._update_continuity_status_locked(
                    connection,
                    project,
                    plan,
                    target_status,
                    expected_status=expected_status,
                    expected_plan_digest=expected_plan_digest,
                )
                self._inject_failure("continuity.status.before_commit")
                self._inject_failure("continuity.before_commit")
                connection.commit()
                fresh = self._continuity_plan_row(
                    connection,
                    project,
                    target_run_id=plan.target_run_id,
                )
                if fresh is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                return self._row_to_continuity_plan(connection, fresh)
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    set_continuity_plan_status = update_continuity_plan_status
    transition_continuity_plan = update_continuity_plan_status
    set_carry_forward_plan_status = update_continuity_plan_status

    def verify_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_VERIFIED,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    mark_continuity_plan_verified = verify_continuity_plan
    verify_carry_forward_plan = verify_continuity_plan

    def block_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_BLOCKED,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    def reopen_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_STAGING,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    def publish_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ResultPublication:
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        expected_digest = kwargs.pop("expected_plan_digest", None)
        plan = self.get_continuity_plan(
            project,
            target_run_id=target,
            plan_id=continuity_id,
        )
        if target is None:
            target = plan.target_run_id
        if expected_digest is not None:
            expected_digest = _required_text(
                expected_digest, "continuity_plan_cas_conflict"
            )
            if plan.plan_digest != expected_digest:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        return self.finalize_publication(
            project,
            target,
            publication_revision,
            require_continuity_plan=True,
            expected_plan_digest=expected_digest,
            **kwargs,
        )

    publish_carry_forward_plan = publish_continuity_plan
    def get_by_idempotency(
        self, idempotency_key: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        key = _required_text(idempotency_key, "invalid_idempotency_key")
        with self._lock:
            record = self._find_by_key(project, key)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def get_by_public_token(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        token = _required_text(public_run_token, "public_run_not_found")
        with self._lock:
            record = self._find_by_selector(project, token)
        if record is None:
            raise LaunchRegistryError("public_run_not_found")
        return record

    def get(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        value = _required_text(selector, "run_not_found")
        with self._lock:
            record = self._find_by_selector(project, value)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def get_public(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> dict[str, Any]:
        return self.get_by_public_token(public_run_token, project_id=project_id).public_projection()

    def list_records(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Tuple[LaunchRecord, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            rows = self._require_conn().execute(
                "SELECT * FROM r7_launch_registry WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(self._row_to_record(row) for row in rows)

    def list_history(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        return [record.public_projection() for record in self.list_records(project_id, limit=limit)]

    history = list_history
    list_public_history = list_history
    get_public_history = list_history
    def get_public_run(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> dict[str, Any]:
        return self.get_public(public_run_token, project_id=project_id)

    def resolve_public_token(
        self, project_id: str, public_run_token: str
    ) -> LaunchRecord:
        return self.get_by_public_token(public_run_token, project_id=project_id)

    def set_run_state(
        self, project_id: str, selector: str, state: str, **kwargs: Any
    ) -> LaunchRecord:
        return self.update_state(selector, state, project_id=project_id, **kwargs)
    list_runs = list_history

    def _history_limit(self, limit: Optional[int]) -> int:
        value = self._default_history_limit if limit is None else limit
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise LaunchRegistryError("invalid_history_limit")
        return min(value, self._max_history_limit)

    def update_state(
        self,
        selector: str,
        state: str,
        *,
        project_id: Optional[str] = None,
        result_available: Optional[bool] = None,
        main_action: Optional[str] = None,
        manifest_digest: Optional[str] = None,
    ) -> LaunchRecord:
        """Durably update state without changing request identity.

        A same-state update is idempotent.  ``result_available`` is only
        accepted for ``completed`` and remains false throughout Slice-07C-2.
        """
        project = self._project(project_id)
        target = _required_text(state, "invalid_run_state")
        if target not in RUN_STATE_VALUES:
            raise LaunchRegistryError("invalid_run_state")
        selector_text = _required_text(selector, "run_not_found")
        if result_available is not None and not isinstance(result_available, bool):
            raise LaunchRegistryError("invalid_result_state")
        if manifest_digest is not None:
            manifest_digest = _required_text(manifest_digest, "invalid_manifest_digest")
        if main_action is not None:
            main_action = _required_text(main_action, "invalid_result_state")
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._find_by_selector(project, selector_text)
                if current is None:
                    connection.rollback()
                    raise LaunchRegistryError("run_not_found")
                if target not in _ALLOWED_TRANSITIONS[current.run_state]:
                    connection.rollback()
                    raise LaunchRegistryError("illegal_state_transition")
                available = (
                    current.result_available
                    if result_available is None
                    else result_available
                )
                if current.result_available and not available:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                if available and target != STATE_COMPLETED:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                if available and not current.result_available:
                    publication_row = connection.execute(
                        "SELECT publication_state FROM r7_result_publications "
                        "WHERE project_id = ? AND run_id = ? "
                        "AND publication_revision = ?",
                        (project, current.run_id, PUBLICATION_REVISION),
                    ).fetchone()
                    if (
                        publication_row is None
                        or publication_row["publication_state"]
                        != PUBLICATION_STATE_AVAILABLE
                    ):
                        connection.rollback()
                        raise LaunchRegistryError("invalid_result_state")
                expected_action = self._default_action(target, available)
                if main_action is not None and main_action != expected_action:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                effective_action = expected_action
                effective_manifest = (
                    manifest_digest if manifest_digest is not None else current.manifest_digest
                )
                updated_at = self._now()
                updated = connection.execute(
                    "UPDATE r7_launch_registry SET "
                    "run_state = ?, result_available = ?, main_action = ?, "
                    "manifest_digest = ?, updated_at = ? "
                    "WHERE project_id = ? AND sequence = ?",
                    (
                        target,
                        int(available),
                        effective_action,
                        effective_manifest,
                        updated_at,
                        project,
                        current.sequence,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_launch_registry WHERE sequence = ?", (current.sequence,)
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("store_closed")
                return self._row_to_record(row)
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    set_state = update_state

    def mark_waiting_start(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        return self.update_state(selector, STATE_WAITING_START, project_id=project_id)

    def mark_running(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.update_state(selector, STATE_RUNNING, project_id=project_id)

    def mark_started(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.mark_running(selector, project_id=project_id)

    def mark_completed(
        self,
        selector: str,
        *,
        project_id: Optional[str] = None,
        result_available: bool = False,
    ) -> LaunchRecord:
        return self.update_state(
            selector,
            STATE_COMPLETED,
            project_id=project_id,
            result_available=result_available,
        )

    def mark_failed(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.update_state(selector, STATE_FAILED, project_id=project_id)

    def record_start_failure(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        """Keep the reserved run recoverable when background start fails."""
        return self.mark_waiting_start(selector, project_id=project_id)

    def record_manifest(
        self,
        selector: str,
        manifest_digest: str,
        *,
        project_id: Optional[str] = None,
    ) -> LaunchRecord:
        record = self.get(selector, project_id=project_id)
        return self.update_state(
            selector,
            record.run_state,
            project_id=project_id,
            manifest_digest=manifest_digest,
        )
