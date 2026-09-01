"""Continuity-plan persistence and retrieval."""

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
from .launch_registry_contracts import _normalize_nonnegative_int, _required_text

class LaunchRegistryContinuityMixin:
    """Cohesive methods extracted from the launch registry."""

    @staticmethod
    def _coerce_continuity_plan(value: Any) -> CarryForwardPlan:
        if isinstance(value, CarryForwardPlan):
            plan = value
        elif isinstance(value, Mapping):
            try:
                plan = CarryForwardPlan.from_mapping(value)
            except (PlanValidationError, TypeError, ValueError) as exc:
                raise LaunchRegistryError("invalid_continuity_plan") from exc
        else:
            raise LaunchRegistryError("invalid_continuity_plan")
        try:
            validate_carry_forward_plan(plan)
        except (PlanValidationError, TypeError, ValueError) as exc:
            raise LaunchRegistryError("invalid_continuity_plan") from exc
        return plan

    @staticmethod
    def _continuity_plan_id(plan: CarryForwardPlan) -> str:
        return derive_continuity_plan_id(plan)

    @staticmethod
    def _continuity_plan_json(plan: CarryForwardPlan) -> str:
        payload = plan.as_dict()
        payload["items"] = [item.as_dict() for item in plan.items]
        if plan.baseline is not None:
            payload["baseline"] = plan.baseline.as_dict()
        return canonical_json(payload)

    @staticmethod
    def _continuity_item_evidence_json(item: CarryForwardItem) -> str:
        return canonical_json(
            {
                "evidence_summary": item.evidence_summary,
                "evidence_refs": list(item.evidence_refs),
                "closure_evidence_refs": list(item.closure_evidence_refs),
            }
        )

    @staticmethod
    def _decode_continuity_json(value: Any) -> Any:
        try:
            return json.loads(str(value))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LaunchRegistryError("store_closed") from exc

    @classmethod
    def _decode_continuity_mapping(cls, value: Any) -> Mapping[str, Any]:
        decoded = cls._decode_continuity_json(value)
        if not isinstance(decoded, Mapping):
            raise LaunchRegistryError("store_closed")
        return decoded

    @classmethod
    def _row_to_continuity_plan(
        cls,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> CarryForwardPlan:
        try:
            payload = cls._decode_continuity_mapping(row["plan_json"])
            plan = CarryForwardPlan.from_mapping(payload)
            expected_plan_id = cls._continuity_plan_id(plan)
            if (
                str(row["plan_id"]) != expected_plan_id
                or str(row["project_id"]) != plan.project_id
                or str(row["target_run_id"]) != plan.target_run_id
                or str(row["mode"]) != plan.mode
                or str(row["execution_basis"]) != plan.execution_basis
                or str(row["target_snapshot_id"]) != plan.target_snapshot_id
                or str(row["target_data_cutoff"]) != plan.target_data_cutoff
                or str(row["target_decision_version"]) != plan.target_decision_version
                or str(row["target_rule_revision_ids_json"])
                != canonical_json(list(plan.target_rule_revision_ids))
                or str(row["baseline_source_run_id"]) != plan.baseline_source_run_id
                or str(row["baseline_source_publication_id"])
                != plan.baseline_source_publication_id
                or str(row["baseline_source_public_run_token"])
                != plan.baseline_source_public_run_token
                or str(row["r5_authority_digest"]) != plan.r5_authority_digest
                or str(row["r6_publication_digest"]) != plan.r6_publication_digest
                or str(row["r6_receipt_digest"]) != plan.r6_receipt_digest
                or (
                    "r6_output_set_digest" in row.keys()
                    and str(row["r6_output_set_digest"]) != plan.r6_output_set_digest
                )
                or str(row["plan_digest"]) != plan.plan_digest
                or str(row["status"]) != plan.status
                or str(row["counts_json"]) != canonical_json(plan.counts)
                or str(row["created_at"]) != plan.created_at
                or str(row["updated_at"]) != plan.updated_at
                or str(row["plan_json"]) != cls._continuity_plan_json(plan)
            ):
                raise LaunchRegistryError("store_closed")
            baseline = plan.baseline
            expected_source = (
                (
                    baseline.source_run_id,
                    baseline.source_publication_id,
                    baseline.source_public_run_token,
                )
                if baseline is not None
                else (
                    plan.baseline_source_run_id,
                    plan.baseline_source_publication_id,
                    plan.baseline_source_public_run_token,
                )
            )
            if (
                str(row["source_run_id"]) != expected_source[0]
                or str(row["source_publication_id"]) != expected_source[1]
                or str(row["source_public_run_token"]) != expected_source[2]
            ):
                raise LaunchRegistryError("store_closed")
            target_launch = connection.execute(
                "SELECT public_run_token, mode, execution_basis, "
                "current_snapshot_token, data_cutoff "
                "FROM r7_launch_registry WHERE project_id = ? AND run_id = ?",
                (plan.project_id, plan.target_run_id),
            ).fetchone()
            stored_target_token = row["target_public_run_token"]
            if target_launch is None:
                if stored_target_token is not None:
                    raise LaunchRegistryError("store_closed")
            elif (
                stored_target_token != target_launch["public_run_token"]
                or str(target_launch["mode"]) != plan.mode
                or str(target_launch["execution_basis"])
                != plan.execution_basis
                or str(target_launch["current_snapshot_token"])
                != plan.target_snapshot_id
                or str(target_launch["data_cutoff"]) != plan.target_data_cutoff
            ):
                raise LaunchRegistryError("store_closed")
            item_rows = connection.execute(
                "SELECT * FROM r7_continuity_items "
                "WHERE plan_id = ? ORDER BY ordinal ASC, sequence ASC",
                (expected_plan_id,),
            ).fetchall()
            if len(item_rows) != len(plan.items):
                raise LaunchRegistryError("store_closed")
            for expected, item_row in zip(plan.items, item_rows):
                item_payload = cls._decode_continuity_mapping(item_row["item_json"])
                item = CarryForwardItem.from_mapping(item_payload)
                expected_evidence = cls._continuity_item_evidence_json(expected)
                denormalized = (
                    int(item_row["ordinal"]) == expected.ordinal
                    and str(item_row["object_type"]) == expected.object_type
                    and str(item_row["object_ref"]) == expected.object_ref
                    and str(item_row["disposition"]) == expected.disposition
                    and str(item_row["source_run_id"]) == expected.source_run_id
                    and str(item_row["source_publication_id"])
                    == expected.source_publication_id
                    and str(item_row["source_public_run_token"])
                    == expected.source_public_run_token
                    and str(item_row["source_object_id"]) == expected.source_object_id
                    and str(item_row["target_object_id"]) == expected.target_object_id
                    and str(item_row["source_artifact_id"])
                    == expected.source_artifact_id
                    and str(item_row["source_artifact_sha256"])
                    == expected.source_artifact_sha256
                    and (
                        item_row["prior_risk_state"] == expected.prior_risk_state
                    )
                    and (
                        item_row["current_risk_state"] == expected.current_risk_state
                    )
                    and item_row["prior_severity"] == expected.prior_severity
                    and item_row["current_severity"] == expected.current_severity
                    and str(item_row["governing_rule_revision_ids_json"])
                    == canonical_json(list(expected.governing_rule_revision_ids))
                    and str(item_row["changed_applicable_rule_ids_json"])
                    == canonical_json(list(expected.changed_applicable_rule_ids))
                    and str(item_row["attribution"]) == expected.attribution
                    and str(item_row["evidence_json"]) == expected_evidence
                    and str(item_row["item_digest"]) == expected.item_digest
                    and item == expected
                    and str(item_row["item_json"])
                    == canonical_json(expected.as_dict())
                )
                if (
                    str(item_row["plan_id"]) != expected_plan_id
                    or not denormalized
                ):
                    raise LaunchRegistryError("store_closed")
            return plan
        except LaunchRegistryError:
            raise
        except (PlanValidationError, TypeError, ValueError, KeyError) as exc:
            raise LaunchRegistryError("store_closed") from exc

    @staticmethod
    def _continuity_plan_row(
        connection: sqlite3.Connection,
        project: str,
        *,
        target_run_id: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> Optional[sqlite3.Row]:
        if plan_id is not None:
            query = (
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? AND plan_id = ?"
            )
            params: list[Any] = [project, plan_id]
            if target_run_id is not None:
                query += " AND target_run_id = ?"
                params.append(target_run_id)
            return connection.execute(query, tuple(params)).fetchone()
        if target_run_id is not None:
            return connection.execute(
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? AND target_run_id = ?",
                (project, target_run_id),
            ).fetchone()
        raise LaunchRegistryError("continuity_plan_not_found")

    def _continuity_lookup(
        self,
        project_id: Optional[str],
        target_run_id: Optional[str],
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        if isinstance(project_id, CarryForwardPlan):
            plan_value = project_id
            project_id = plan_value.project_id
            if target_run_id is None:
                target_run_id = plan_value.target_run_id
            if plan_id is None:
                plan_id = self._continuity_plan_id(plan_value)
        # With a default project, a single positional value is naturally a
        # target-run selector.  With no default project callers use
        # (project_id, target_run_id), matching the publication API.
        if (
            target_run_id is None
            and plan_id is None
            and selector is None
            and run_id is None
            and project_id is not None
            and self._default_project_id
        ):
            target_run_id = project_id
            project_id = None
        if (
            plan_id is None
            and target_run_id is not None
            and isinstance(target_run_id, str)
            and target_run_id.startswith("r7-plan-")
        ):
            plan_id = target_run_id
            target_run_id = None
        if run_id is not None:
            if target_run_id is not None and target_run_id != run_id:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
            target_run_id = run_id
        if selector is not None:
            selector_text = _required_text(
                selector, "continuity_plan_not_found"
            )
            if (
                target_run_id is not None
                and target_run_id != selector_text
                or plan_id is not None
                and plan_id != selector_text
            ):
                raise LaunchRegistryError("continuity_plan_cas_conflict")
            if plan_id is None and target_run_id is None:
                if selector_text.startswith("r7-plan-"):
                    plan_id = selector_text
                else:
                    target_run_id = selector_text
        project = self._project(project_id)
        normalized_plan_id = (
            _required_text(plan_id, "continuity_plan_not_found")
            if plan_id is not None
            else None
        )
        normalized_target = (
            _required_text(target_run_id, "continuity_plan_not_found")
            if target_run_id is not None
            else None
        )
        if normalized_plan_id is None and normalized_target is None:
            raise LaunchRegistryError("continuity_plan_not_found")
        return project, normalized_target, normalized_plan_id

    def save_continuity_plan(
        self,
        plan: Any,
        project_id: Optional[str] = None,
        *,
        target_run_id: Optional[str] = None,
    ) -> CarryForwardPlan:
        # Also accept save_continuity_plan(project_id, plan) for consistency
        # with the older project-first registry methods.
        if isinstance(plan, str) and isinstance(
            project_id, (CarryForwardPlan, Mapping)
        ):
            plan, project_id = project_id, plan
        prepared = self._coerce_continuity_plan(plan)
        if prepared.status != CONTINUITY_PLAN_STATE_STAGING:
            raise LaunchRegistryError("invalid_continuity_plan")
        project = self._project(
            project_id if project_id is not None else prepared.project_id
        )
        if prepared.project_id != project:
            raise LaunchRegistryError("invalid_project_id")
        if target_run_id is not None and (
            _required_text(target_run_id, "continuity_plan_not_found")
            != prepared.target_run_id
        ):
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        plan_id = self._continuity_plan_id(prepared)
        plan_json = self._continuity_plan_json(prepared)
        counts_json = canonical_json(prepared.counts)
        baseline = prepared.baseline
        source_run_id = (
            baseline.source_run_id
            if baseline is not None
            else prepared.baseline_source_run_id
        )
        source_publication_id = (
            baseline.source_publication_id
            if baseline is not None
            else prepared.baseline_source_publication_id
        )
        source_public_run_token = (
            baseline.source_public_run_token
            if baseline is not None
            else prepared.baseline_source_public_run_token
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._continuity_plan_row(
                    connection, project, target_run_id=prepared.target_run_id
                )
                if existing is not None:
                    if str(existing["plan_digest"]) != prepared.plan_digest:
                        raise IdempotencyConflictError()
                    existing_plan = self._row_to_continuity_plan(
                        connection, existing
                    )
                    connection.commit()
                    return existing_plan
                publication_row = connection.execute(
                    "SELECT publication_state FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ?",
                    (project, prepared.target_run_id, PUBLICATION_REVISION),
                ).fetchone()
                if (
                    publication_row is not None
                    and str(publication_row["publication_state"])
                    == PUBLICATION_STATE_AVAILABLE
                ):
                    raise LaunchRegistryError(
                        "continuity_publication_conflict"
                    )
                target_row = connection.execute(
                    "SELECT public_run_token, mode, execution_basis, "
                    "current_snapshot_token, data_cutoff "
                    "FROM r7_launch_registry "
                    "WHERE project_id = ? AND run_id = ?",
                    (project, prepared.target_run_id),
                ).fetchone()
                if target_row is not None and (
                    str(target_row["mode"]) != prepared.mode
                    or str(target_row["execution_basis"])
                    != prepared.execution_basis
                    or str(target_row["current_snapshot_token"])
                    != prepared.target_snapshot_id
                    or str(target_row["data_cutoff"])
                    != prepared.target_data_cutoff
                ):
                    raise LaunchRegistryError("continuity_publication_conflict")
                target_public_run_token = (
                    str(target_row["public_run_token"])
                    if target_row is not None
                    else None
                )
                connection.execute(
                    """INSERT INTO r7_continuity_plans(
                        plan_id, project_id, target_run_id,
                        target_public_run_token, source_run_id,
                        source_publication_id, source_public_run_token, mode,
                        execution_basis, target_snapshot_id, target_data_cutoff,
                        target_rule_revision_ids_json, target_decision_version,
                        baseline_source_run_id, baseline_source_publication_id,
                        baseline_source_public_run_token, r5_authority_digest,
                        r6_publication_digest, r6_receipt_digest, r6_output_set_digest, plan_digest,
                        status, counts_json, plan_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        plan_id,
                        project,
                        prepared.target_run_id,
                        target_public_run_token,
                        source_run_id,
                        source_publication_id,
                        source_public_run_token,
                        prepared.mode,
                        prepared.execution_basis,
                        prepared.target_snapshot_id,
                        prepared.target_data_cutoff,
                        canonical_json(list(prepared.target_rule_revision_ids)),
                        prepared.target_decision_version,
                        prepared.baseline_source_run_id,
                        prepared.baseline_source_publication_id,
                        prepared.baseline_source_public_run_token,
                        prepared.r5_authority_digest,
                        prepared.r6_publication_digest,
                        prepared.r6_receipt_digest,
                        prepared.r6_output_set_digest,
                        prepared.plan_digest,
                        prepared.status,
                        counts_json,
                        plan_json,
                        prepared.created_at,
                        prepared.updated_at,
                    ),
                )
                self._inject_failure("continuity.after_plan_insert")
                self._inject_failure("continuity.save.after_plan")
                for item in prepared.items:
                    connection.execute(
                        """INSERT INTO r7_continuity_items(
                            plan_id, ordinal, object_type, object_ref,
                            disposition, source_run_id, source_publication_id,
                            source_public_run_token, source_object_id,
                            target_object_id, source_artifact_id,
                            source_artifact_sha256, prior_risk_state,
                            current_risk_state, prior_severity, current_severity,
                            governing_rule_revision_ids_json,
                            changed_applicable_rule_ids_json, attribution,
                            evidence_json, item_digest, item_json,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                  ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            plan_id,
                            item.ordinal,
                            item.object_type,
                            item.object_ref,
                            item.disposition,
                            item.source_run_id,
                            item.source_publication_id,
                            item.source_public_run_token,
                            item.source_object_id,
                            item.target_object_id,
                            item.source_artifact_id,
                            item.source_artifact_sha256,
                            item.prior_risk_state,
                            item.current_risk_state,
                            item.prior_severity,
                            item.current_severity,
                            canonical_json(
                                list(item.governing_rule_revision_ids)
                            ),
                            canonical_json(
                                list(item.changed_applicable_rule_ids)
                            ),
                            item.attribution,
                            self._continuity_item_evidence_json(item),
                            item.item_digest,
                            canonical_json(item.as_dict()),
                            prepared.created_at,
                            prepared.updated_at,
                        ),
                    )
                    self._inject_failure(
                        "continuity.after_item_insert"
                    )
                    self._inject_failure(
                        "continuity.save.after_item_%d" % item.ordinal
                    )
                self._inject_failure("continuity.save.before_commit")
                self._inject_failure("continuity.before_commit")
                connection.commit()
                row = self._continuity_plan_row(
                    connection, project, target_run_id=prepared.target_run_id
                )
                if row is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                return self._row_to_continuity_plan(connection, row)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
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

    persist_continuity_plan = save_continuity_plan
    store_continuity_plan = save_continuity_plan
    create_continuity_plan = save_continuity_plan
    save_carry_forward_plan = save_continuity_plan
    persist_carry_forward_plan = save_continuity_plan

    def get_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> CarryForwardPlan:
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        with self._lock:
            row = self._continuity_plan_row(
                self._require_conn(),
                project,
                target_run_id=target,
                plan_id=continuity_id,
            )
            if row is None:
                raise LaunchRegistryError("continuity_plan_not_found")
            return self._row_to_continuity_plan(self._require_conn(), row)

    load_continuity_plan = get_continuity_plan
    get_carry_forward_plan = get_continuity_plan
    load_carry_forward_plan = get_continuity_plan
    get_plan = get_continuity_plan

    def get_continuity_plan_by_id(
        self, plan_id: str, *, project_id: Optional[str] = None
    ) -> CarryForwardPlan:
        return self.get_continuity_plan(
            project_id, plan_id=plan_id
        )

    def get_continuity_plan_by_target(
        self, target_run_id: str, *, project_id: Optional[str] = None
    ) -> CarryForwardPlan:
        return self.get_continuity_plan(
            project_id, target_run_id=target_run_id
        )

    def list_continuity_plans(
        self,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Tuple[CarryForwardPlan, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            connection = self._require_conn()
            rows = connection.execute(
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(
                self._row_to_continuity_plan(connection, row) for row in rows
            )

    list_carry_forward_plans = list_continuity_plans

    def list_continuity_items(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Tuple[CarryForwardItem, ...]:
        return self.get_continuity_plan(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        ).items

    get_continuity_items = list_continuity_items
    list_carry_forward_items = list_continuity_items
    get_carry_forward_items = list_continuity_items

    def get_continuity_item(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        ordinal: int = 0,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> CarryForwardItem:
        ordinal_value = _normalize_nonnegative_int(
            ordinal, "continuity_item_not_found"
        )
        items = self.list_continuity_items(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        for item in items:
            if item.ordinal == ordinal_value:
                return item
        raise LaunchRegistryError("continuity_item_not_found")
