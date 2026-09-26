"""Result-publication transitions, failure handling and finalization."""

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
    _PUBLICATION_ALLOWED_TRANSITIONS, _RESULT_MAIN_ACTION, _json_token_list,
    _normalize_publication_tokens, _normalize_result_context_token,
    _optional_text, _required_text,
)

class LaunchRegistryPublicationStateMixin:
    """Cohesive methods extracted from the launch registry."""

    @staticmethod
    def _publication_failure_state(value: Any) -> str:
        target = _required_text(value, "invalid_publication_state")
        if target not in (
            PUBLICATION_STATE_RECOVERABLE_FAILED,
            PUBLICATION_STATE_BLOCKED,
        ):
            raise LaunchRegistryError("invalid_publication_state")
        return target

    def record_publication_failure(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: Any = PUBLICATION_REVISION,
        state: Optional[str] = None,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        failure_state: Optional[str] = None,
        target_state: Optional[str] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        current_state: Optional[str] = None,
        error_code: Optional[str] = None,
        failure_code: Optional[str] = None,
        code: Optional[str] = None,
        error_message: Optional[str] = None,
        failure_message: Optional[str] = None,
        message: Optional[str] = None,
        reason_code: Optional[str] = None,
        reason: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> ResultPublication:
        # A compact positional form permits
        # ``record_publication_failure(project, run, "blocked")``.
        if isinstance(publication_revision, str) and state is None:
            state = publication_revision
            publication_revision = PUBLICATION_REVISION
        target = self._publication_failure_state(
            self._coalesce_publication_alias(
                state,
                self._coalesce_publication_alias(
                    failure_state,
                    target_state,
                    "invalid_publication_state",
                ),
                "invalid_publication_state",
            )
            or PUBLICATION_STATE_RECOVERABLE_FAILED
        )
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected_value = self._coalesce_publication_alias(
            expected_state,
            self._coalesce_publication_alias(
                expected_publication_state,
                current_state,
                "invalid_publication_state",
            ),
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else None
        )
        if expected is not None and expected not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        code_value = self._coalesce_publication_alias(
            error_code,
            self._coalesce_publication_alias(
                failure_code,
                self._coalesce_publication_alias(
                    code,
                    reason_code,
                    "invalid_publication_metadata",
                ),
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        message_value = self._coalesce_publication_alias(
            error_message,
            self._coalesce_publication_alias(
                failure_message,
                self._coalesce_publication_alias(
                    message,
                    self._coalesce_publication_alias(
                        reason,
                        failure_reason,
                        "invalid_publication_metadata",
                    ),
                    "invalid_publication_metadata",
                ),
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        code_text = (
            _required_text(code_value, "invalid_publication_metadata")
            if code_value is not None
            else None
        )
        message_text = (
            _required_text(message_value, "invalid_publication_metadata")
            if message_value is not None
            else None
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if current.publication_state == target:
                    if code_text is None and message_text is None:
                        connection.commit()
                        return current
                elif target not in _PUBLICATION_ALLOWED_TRANSITIONS.get(
                    current.publication_state, frozenset()
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                effective_code = (
                    code_text if code_text is not None else current.failure_code
                )
                effective_message = (
                    message_text
                    if message_text is not None
                    else current.failure_message
                )
                updated_at = self._now()
                where = (
                    "project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?"
                )
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, failure_code = ?, "
                    "failure_message = ?, updated_at = ? WHERE " + where,
                    (
                        target,
                        effective_code,
                        effective_message,
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? AND publication_revision = ?",
                    (project_text, launch.run_id, revision_text),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
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
    record_publication_error = record_publication_failure
    mark_publication_failure = record_publication_failure

    def retry_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
    ) -> ResultPublication:
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected = (
            _required_text(expected_state, "invalid_publication_state")
            if expected_state is not None
            else None
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if current.publication_state == PUBLICATION_STATE_PUBLISHING:
                    connection.commit()
                    return current
                if current.publication_state not in (
                    PUBLICATION_STATE_RECOVERABLE_FAILED,
                    PUBLICATION_STATE_BLOCKED,
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, failure_code = NULL, "
                    "failure_message = NULL, updated_at = ? "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?",
                    (
                        PUBLICATION_STATE_PUBLISHING,
                        self._now(),
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                connection.commit()
                return self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
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
    resume_publication = retry_publication

    def update_publication_state(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        state: str = PUBLICATION_STATE_PUBLISHING,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
    ) -> ResultPublication:
        target = _required_text(state, "invalid_publication_state")
        if target not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        if target == PUBLICATION_STATE_AVAILABLE:
            raise LaunchRegistryError("illegal_publication_transition")
        if target in (
            PUBLICATION_STATE_RECOVERABLE_FAILED,
            PUBLICATION_STATE_BLOCKED,
        ):
            return self.record_publication_failure(
                project,
                run,
                publication_revision,
                target,
                project_id=project_id,
                run_id=run_id,
                revision=revision,
                expected_state=expected_state,
            )
        return self.retry_publication(
            project,
            run,
            publication_revision,
            project_id=project_id,
            run_id=run_id,
            revision=revision,
            expected_state=expected_state,
        )

    set_publication_state = update_publication_state
    cas_publication_state = update_publication_state

    def finalize_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        current_state: Optional[str] = None,
        fingerprint: Optional[str] = None,
        expected_fingerprint: Optional[str] = None,
        expected_publication_fingerprint: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        receipt_identities: Optional[Iterable[Any]] = None,
        receipt_set: Optional[Iterable[Any]] = None,
        receipt_set_digest: Optional[str] = None,
        receipt_digest: Optional[str] = None,
        r5_authority_packet_id: Optional[str] = None,
        r5_authority_packet_identity: Optional[str] = None,
        r5_packet_id: Optional[str] = None,
        r5_authority_packet_digest: Optional[str] = None,
        r5_packet_digest: Optional[str] = None,
        s4_authority_packet_identities: Optional[Iterable[Any]] = None,
        s4_packet_identities: Optional[Iterable[Any]] = None,
        s4_authority_packet_digests: Optional[Iterable[Any]] = None,
        s4_packet_digests: Optional[Iterable[Any]] = None,
        r6_output_set_digest: Optional[str] = None,
        artifact_member_ids: Optional[Iterable[Any]] = None,
        artifact_members: Optional[Iterable[Any]] = None,
        artifact_member_set: Optional[Iterable[Any]] = None,
        artifact_member_set_digest: Optional[str] = None,
        artifact_members_digest: Optional[str] = None,
        frozen_read_model_artifact_id: Optional[str] = None,
        frozen_read_model_sha256: Optional[str] = None,
        require_continuity_plan: bool = False,
        expected_plan_digest: Optional[str] = None,
    ) -> ResultPublication:
        """Atomically make a publication available and open its result flag.

        The publication CAS and launch-row update share one ``BEGIN
        IMMEDIATE`` transaction.  A failure between either update and commit
        rolls both changes back, preventing a one-sided result entry.
        """
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected_value = self._coalesce_publication_alias(
            expected_state,
            self._coalesce_publication_alias(
                expected_publication_state,
                current_state,
                "invalid_publication_state",
            ),
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else None
        )
        if expected is not None and expected not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        fingerprint_value = self._coalesce_publication_alias(
            fingerprint,
            self._coalesce_publication_alias(
                expected_fingerprint,
                self._coalesce_publication_alias(
                    expected_publication_fingerprint,
                    request_fingerprint,
                    "invalid_publication_fingerprint",
                ),
                "invalid_publication_fingerprint",
            ),
            "invalid_publication_fingerprint",
        )
        if fingerprint_value is not None:
            fingerprint_text = _required_text(
                fingerprint_value, "invalid_publication_fingerprint"
            )
        else:
            fingerprint_text = None
        receipt_value = self._coalesce_publication_alias(
            receipt_identities, receipt_set, "invalid_publication_metadata"
        )
        receipt_tuple = (
            None
            if receipt_value is None
            else _normalize_publication_tokens(receipt_value)
        )
        digest_value = self._coalesce_publication_alias(
            receipt_set_digest,
            receipt_digest,
            "invalid_publication_metadata",
        )
        receipt_digest_text = (
            _optional_text(digest_value, "invalid_publication_metadata")
            if digest_value is not None
            else None
        )
        r5_id_value = self._coalesce_publication_alias(
            r5_authority_packet_id,
            self._coalesce_publication_alias(
                r5_authority_packet_identity,
                r5_packet_id,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        r5_digest_value = self._coalesce_publication_alias(
            r5_authority_packet_digest,
            r5_packet_digest,
            "invalid_publication_metadata",
        )
        r5_id = (
            _optional_text(r5_id_value, "invalid_publication_metadata")
            if r5_id_value is not None
            else None
        )
        r5_digest = (
            _optional_text(r5_digest_value, "invalid_publication_metadata")
            if r5_digest_value is not None
            else None
        )
        s4_identity_value = self._coalesce_publication_alias(
            s4_authority_packet_identities,
            s4_packet_identities,
            "invalid_publication_metadata",
        )
        s4_digest_value = self._coalesce_publication_alias(
            s4_authority_packet_digests,
            s4_packet_digests,
            "invalid_publication_metadata",
        )
        s4_identity_tuple = (
            None
            if s4_identity_value is None
            else _normalize_publication_tokens(s4_identity_value)
        )
        s4_digest_tuple = (
            None
            if s4_digest_value is None
            else _normalize_publication_tokens(s4_digest_value)
        )
        r6_out_digest_val = self._coalesce_publication_alias(
            r6_output_set_digest, None, "invalid_publication_metadata"
        )
        r6_output_set_digest_text = (
            _optional_text(r6_out_digest_val, "invalid_publication_metadata")
            if r6_out_digest_val is not None
            else None
        )
        if r6_output_set_digest_text is not None:
            if len(r6_output_set_digest_text) != 64 or any(c not in "0123456789abcdef" for c in r6_output_set_digest_text.lower()):
                raise LaunchRegistryError("invalid_publication_metadata")
            r6_output_set_digest_text = r6_output_set_digest_text.lower()

        member_ids_val = self._coalesce_publication_alias(
            artifact_member_ids,
            self._coalesce_publication_alias(
                artifact_members, artifact_member_set, "invalid_publication_metadata"
            ),
            "invalid_publication_metadata",
        )
        if member_ids_val is not None:
            raw_members = [str(x).strip() for x in member_ids_val]
            if any(not m for m in raw_members):
                raise LaunchRegistryError("invalid_publication_metadata")
            if not raw_members:
                raise LaunchRegistryError("invalid_publication_metadata")
            if sorted(raw_members) != raw_members or len(set(raw_members)) != len(raw_members):
                raise LaunchRegistryError("invalid_publication_metadata")
            member_ids_tuple = tuple(raw_members)
        else:
            member_ids_tuple = None

        member_set_digest_val = self._coalesce_publication_alias(
            artifact_member_set_digest,
            artifact_members_digest,
            "invalid_publication_metadata",
        )
        member_set_digest_text = (
            _optional_text(member_set_digest_val, "invalid_publication_metadata")
            if member_set_digest_val is not None
            else None
        )
        if member_set_digest_text is not None:
            if len(member_set_digest_text) != 64 or any(c not in "0123456789abcdef" for c in member_set_digest_text.lower()):
                raise LaunchRegistryError("invalid_publication_metadata")
            member_set_digest_text = member_set_digest_text.lower()
            if member_ids_tuple is not None:
                expected_member_digest = content_digest(list(member_ids_tuple))
                if member_set_digest_text != expected_member_digest:
                    raise LaunchRegistryError("invalid_publication_metadata")

        # W01-R26（20260926）：冻结read model引用。二者必须成对出现，
        # sha256必须是小写64位十六进制（与发布行锚点同强度）。
        frozen_artifact_text = (
            _optional_text(
                frozen_read_model_artifact_id, "invalid_publication_metadata"
            )
            if frozen_read_model_artifact_id is not None
            else None
        )
        frozen_sha_text = (
            _optional_text(
                frozen_read_model_sha256, "invalid_publication_metadata"
            )
            if frozen_read_model_sha256 is not None
            else None
        )
        if (frozen_artifact_text is None) != (frozen_sha_text is None):
            raise LaunchRegistryError("invalid_publication_metadata")
        if frozen_sha_text is not None:
            if len(frozen_sha_text) != 64 or any(
                c not in "0123456789abcdef" for c in frozen_sha_text.lower()
            ):
                raise LaunchRegistryError("invalid_publication_metadata")
            frozen_sha_text = frozen_sha_text.lower()

        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                continuity_row = self._continuity_plan_row(
                    connection,
                    project_text,
                    target_run_id=launch.run_id,
                )
                if continuity_row is None:
                    if require_continuity_plan or expected_plan_digest is not None:
                        raise LaunchRegistryError("continuity_plan_not_found")
                    continuity_plan = None
                else:
                    continuity_plan = self._row_to_continuity_plan(
                        connection, continuity_row
                    )
                    if continuity_plan.status not in (
                        CONTINUITY_PLAN_STATE_VERIFIED,
                        CONTINUITY_PLAN_STATE_PUBLISHED,
                    ):
                        raise LaunchRegistryError(
                            "continuity_plan_not_verified"
                        )
                    if expected_plan_digest is not None:
                        expected_digest = _required_text(
                            expected_plan_digest,
                            "continuity_plan_cas_conflict",
                        )
                        if continuity_plan.plan_digest != expected_digest:
                            raise LaunchRegistryError(
                                "continuity_plan_cas_conflict"
                            )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if continuity_plan is not None:
                    if (
                        continuity_plan.status
                        == CONTINUITY_PLAN_STATE_PUBLISHED
                        and current.publication_state
                        != PUBLICATION_STATE_AVAILABLE
                    ):
                        raise LaunchRegistryError(
                            "continuity_publication_conflict"
                        )
                    if (
                        continuity_plan.status
                        == CONTINUITY_PLAN_STATE_VERIFIED
                        and current.publication_state
                        not in (
                            PUBLICATION_STATE_PUBLISHING,
                            PUBLICATION_STATE_AVAILABLE,
                        )
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                if continuity_plan is not None:
                    effective_r5_digest = (
                        r5_digest
                        if r5_digest is not None
                        else current.r5_authority_packet_digest
                    )
                    effective_receipt_digest = (
                        receipt_digest_text
                        if receipt_digest_text is not None
                        else current.receipt_set_digest
                    )
                    effective_r6_output_set_digest = (
                        r6_output_set_digest_text
                        if r6_output_set_digest_text is not None
                        else current.r6_output_set_digest
                    )
                    if (
                        continuity_plan.r5_authority_digest != effective_r5_digest
                        or continuity_plan.r6_publication_digest
                        != current.publication_fingerprint
                        or continuity_plan.r6_receipt_digest
                        != effective_receipt_digest
                        or (continuity_plan.r6_output_set_digest and continuity_plan.r6_output_set_digest != effective_r6_output_set_digest)
                        or (effective_r6_output_set_digest and continuity_plan.r6_output_set_digest != effective_r6_output_set_digest)
                    ):
                        raise LaunchRegistryError(
                            "continuity_publication_conflict"
                        )
                if (
                    fingerprint_text is not None
                    and current.publication_fingerprint != fingerprint_text
                ):
                    raise IdempotencyConflictError()
                if current.publication_state == PUBLICATION_STATE_AVAILABLE:
                    if (
                        receipt_tuple is not None
                        and receipt_tuple != current.receipt_identities
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        receipt_digest_text is not None
                        and receipt_digest_text != current.receipt_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if r5_id is not None and r5_id != current.r5_authority_packet_id:
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        r5_digest is not None
                        and r5_digest != current.r5_authority_packet_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        s4_identity_tuple is not None
                        and s4_identity_tuple
                        != current.s4_authority_packet_identities
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        s4_digest_tuple is not None
                        and s4_digest_tuple
                        != current.s4_authority_packet_digests
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        r6_output_set_digest_text is not None
                        and r6_output_set_digest_text != current.r6_output_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        member_ids_tuple is not None
                        and member_ids_tuple != current.artifact_member_ids
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        member_set_digest_text is not None
                        and member_set_digest_text != current.artifact_member_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        frozen_artifact_text is not None
                        and frozen_artifact_text
                        != current.frozen_read_model_artifact_id
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        frozen_sha_text is not None
                        and frozen_sha_text
                        != current.frozen_read_model_sha256
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        continuity_plan is not None
                        and continuity_plan.status
                        == CONTINUITY_PLAN_STATE_VERIFIED
                    ):
                        self._mark_continuity_plan_published_locked(
                            connection,
                            project_text,
                            continuity_plan,
                        )
                    self._inject_failure("finalize.before_commit")
                    connection.commit()
                    return ResultPublication(
                        **{**current.__dict__, "replayed": True}
                    )
                if current.publication_state not in (
                    PUBLICATION_STATE_PUBLISHING,
                    PUBLICATION_STATE_RECOVERABLE_FAILED,
                    PUBLICATION_STATE_BLOCKED,
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                if launch.run_state != STATE_COMPLETED:
                    raise LaunchRegistryError("run_not_completed")
                result_context_token = _normalize_result_context_token(
                    current.result_context_token
                )
                if result_context_token is None:
                    for _ in range(16):
                        candidate = (
                            RESULT_CONTEXT_TOKEN_PREFIX + uuid4().hex
                        )
                        occupied = connection.execute(
                            "SELECT 1 FROM r7_result_publications "
                            "WHERE project_id = ? AND result_context_token = ?",
                            (project_text, candidate),
                        ).fetchone()
                        if occupied is None:
                            result_context_token = candidate
                            break
                    if result_context_token is None:
                        raise LaunchRegistryError("store_closed")


                def _effective_tuple(
                    provided: Optional[Tuple[str, ...]],
                    existing: Tuple[str, ...],
                ) -> Tuple[str, ...]:
                    # Completion-dependent receipt/member facts are bound by
                    # finalize, not by the request fingerprint.  A retry may
                    # therefore replace a provisional pre-finalize value.
                    return existing if provided is None else provided

                effective_receipts = _effective_tuple(
                    receipt_tuple, current.receipt_identities
                )
                effective_s4_ids = _effective_tuple(
                    s4_identity_tuple, current.s4_authority_packet_identities
                )
                effective_s4_digests = _effective_tuple(
                    s4_digest_tuple, current.s4_authority_packet_digests
                )
                def _effective_text(
                    provided: Optional[str], existing: Optional[str]
                ) -> Optional[str]:
                    return existing if provided is None else provided

                effective_receipt_digest = _effective_text(
                    receipt_digest_text, current.receipt_set_digest
                )
                effective_r5_id = _effective_text(
                    r5_id, current.r5_authority_packet_id
                )
                effective_r5_digest = _effective_text(
                    r5_digest, current.r5_authority_packet_digest
                )
                effective_r6_output_set_digest = _effective_text(
                    r6_output_set_digest_text, current.r6_output_set_digest
                )
                effective_member_ids = (
                    member_ids_tuple
                    if member_ids_tuple is not None
                    else current.artifact_member_ids
                )
                effective_member_set_digest = _effective_text(
                    member_set_digest_text, current.artifact_member_set_digest
                )
                effective_frozen_artifact = _effective_text(
                    frozen_artifact_text,
                    current.frozen_read_model_artifact_id,
                )
                effective_frozen_sha = _effective_text(
                    frozen_sha_text, current.frozen_read_model_sha256
                )
                if effective_member_ids and effective_member_set_digest is None:
                    effective_member_set_digest = content_digest(list(effective_member_ids))
                if (
                    len(effective_member_ids) != 4
                    or effective_r6_output_set_digest is None
                    or len(effective_r6_output_set_digest) != 64
                    or effective_member_set_digest
                    != content_digest(list(effective_member_ids))
                ):
                    raise LaunchRegistryError("invalid_publication_metadata")

                updated_at = self._now()
                where = (
                    "project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?"
                )
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, result_context_token = ?, "
                    "receipt_identities_json = ?, "
                    "receipt_set_digest = ?, r5_authority_packet_id = ?, "
                    "r5_authority_packet_digest = ?, "
                    "s4_authority_packet_identities_json = ?, "
                    "s4_authority_packet_digests_json = ?, "
                    "r6_output_set_digest = ?, "
                    "artifact_member_ids_json = ?, "
                    "artifact_member_set_digest = ?, "
                    "frozen_read_model_artifact_id = ?, "
                    "frozen_read_model_sha256 = ?, "
                    "failure_code = NULL, failure_message = NULL, "
                    "updated_at = ? WHERE " + where,
                    (
                        PUBLICATION_STATE_AVAILABLE,
                        result_context_token,
                        _json_token_list(effective_receipts),
                        effective_receipt_digest,
                        effective_r5_id,
                        effective_r5_digest,
                        _json_token_list(effective_s4_ids),
                        _json_token_list(effective_s4_digests),
                        effective_r6_output_set_digest,
                        _json_token_list(effective_member_ids),
                        effective_member_set_digest,
                        effective_frozen_artifact,
                        effective_frozen_sha,
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure("finalize.after_publication_update")
                launch_updated = connection.execute(
                    "UPDATE r7_launch_registry SET "
                    "result_available = 1, main_action = ?, updated_at = ? "
                    "WHERE project_id = ? AND sequence = ? "
                    "AND run_state = ?",
                    (
                        _RESULT_MAIN_ACTION,
                        updated_at,
                        project_text,
                        launch.sequence,
                        STATE_COMPLETED,
                    ),
                )
                if launch_updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure("finalize.after_launch_update")
                if (
                    continuity_plan is not None
                    and continuity_plan.status
                    == CONTINUITY_PLAN_STATE_VERIFIED
                ):
                    self._mark_continuity_plan_published_locked(
                        connection,
                        project_text,
                        continuity_plan,
                        updated_at=updated_at,
                    )
                self._inject_failure("finalize.before_commit")
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ?",
                    (project_text, launch.run_id, revision_text),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
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
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
