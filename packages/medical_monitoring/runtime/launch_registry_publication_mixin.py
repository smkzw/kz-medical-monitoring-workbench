"""Result-publication reservation, binding and retrieval."""

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
    _json_token_list, _manifest_work_unit_mapping, _normalize_nonnegative_int,
    _normalize_optional_positive_int, _normalize_publication_object,
    _normalize_publication_revision, _normalize_publication_tokens,
    _normalize_result_context_token, _optional_text, _required_text,
    _coalesce_publication_alias,
)

class LaunchRegistryPublicationMixin:
    """Cohesive methods extracted from the launch registry."""

    _coalesce_publication_alias = staticmethod(_coalesce_publication_alias)

    def _publication_project_run(
        self,
        project: Optional[str],
        run: Optional[str],
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
    ) -> Tuple[str, LaunchRecord]:
        project_value = self._coalesce_publication_alias(
            project, project_id, "invalid_project_id"
        )
        run_alias = self._coalesce_publication_alias(
            run_id, public_run_token, "run_not_found"
        )
        run_value = self._coalesce_publication_alias(
            run, run_alias, "run_not_found"
        )
        project_text = self._project(project_value)
        if run_value is None:
            raise LaunchRegistryError("run_not_found")
        return project_text, self._resolve_publication_run(project_text, run_value)

    @staticmethod
    def _publication_revision_alias(
        publication_revision: Any, revision: Optional[int]
    ) -> int:
        if revision is not None:
            if (
                publication_revision is not None
                and publication_revision != PUBLICATION_REVISION
                and publication_revision != revision
            ):
                raise LaunchRegistryError("invalid_publication_revision")
            publication_revision = revision
        if publication_revision is None:
            publication_revision = PUBLICATION_REVISION
        return _normalize_publication_revision(publication_revision)

    @staticmethod
    def _publication_text_alias(
        primary: Any, alias: Any, code: str
    ) -> Optional[str]:
        value = LaunchRegistry._coalesce_publication_alias(primary, alias, code)
        return _optional_text(value, code) if value is not None else None

    def reserve_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        key: Optional[str] = None,
        fingerprint: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        publication_fingerprint: Optional[str] = None,
        revision: Optional[int] = None,
        snapshot_token: Optional[str] = None,
        current_snapshot_token: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        current_snapshot_ref: Optional[str] = None,
        source_revision_id: Optional[str] = None,
        source_revision: Optional[str] = None,
        data_cutoff: Optional[str] = None,
        setup_manifest_digest: Optional[str] = None,
        manifest_revision: Optional[int] = None,
        runtime_manifest_revision: Optional[int] = None,
        manifest_digest: Optional[str] = None,
        runtime_manifest_digest: Optional[str] = None,
        mandatory_denominator: int = 0,
        site_coverage: Optional[Iterable[Any]] = None,
        sites: Optional[Iterable[Any]] = None,
        setup_manifest_identity: Any = None,
        setup_manifest_work_unit_identity: Any = None,
        runtime_manifest_identity: Any = None,
        runtime_manifest_work_unit_identity: Any = None,
        receipt_identities: Optional[Iterable[Any]] = None,
        receipt_set: Optional[Iterable[Any]] = None,
        receipt_set_digest: Optional[str] = None,
        r5_authority_packet_id: Optional[str] = None,
        r5_authority_packet_identity: Optional[str] = None,
        r5_packet_id: Optional[str] = None,
        r5_authority_packet_digest: Optional[str] = None,
        r5_packet_digest: Optional[str] = None,
        s4_authority_packet_identities: Optional[Iterable[Any]] = None,
        s4_packet_identities: Optional[Iterable[Any]] = None,
        s4_authority_packet_digests: Optional[Iterable[Any]] = None,
        s4_packet_digests: Optional[Iterable[Any]] = None,
    ) -> ResultPublication:
        """Reserve the one immutable publication identity for a run.

        The run identity is authoritative; an idempotency key is only a
        retry handle.  Therefore a second key with the same frozen fingerprint
        returns the original row instead of creating a second publication.
        """
        # Runtime manifest, receipt, and authority facts are completion-
        # dependent.  They must be read and bound after this reservation, not
        # smuggled into the initial publication identity.
        prebound_values = (
            manifest_revision,
            runtime_manifest_revision,
            manifest_digest,
            runtime_manifest_digest,
            runtime_manifest_identity,
            runtime_manifest_work_unit_identity,
            receipt_identities,
            receipt_set,
            receipt_set_digest,
            r5_authority_packet_id,
            r5_authority_packet_identity,
            r5_packet_id,
            r5_authority_packet_digest,
            r5_packet_digest,
            s4_authority_packet_identities,
            s4_packet_identities,
            s4_authority_packet_digests,
            s4_packet_digests,
        )
        if any(value is not None for value in prebound_values):
            raise LaunchRegistryError("invalid_publication_metadata")

        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        if public_run_token is not None and _required_text(
            public_run_token, "invalid_publication_metadata"
        ) != launch.public_run_token:
            raise LaunchRegistryError("invalid_publication_metadata")
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        key_value = self._coalesce_publication_alias(
            key, idempotency_key, "invalid_idempotency_key"
        )
        if key_value is None:
            raise LaunchRegistryError("invalid_idempotency_key")
        key_text = _required_text(key_value, "invalid_idempotency_key")
        fingerprint_value = self._coalesce_publication_alias(
            fingerprint,
            self._coalesce_publication_alias(
                request_fingerprint,
                publication_fingerprint,
                "invalid_publication_fingerprint",
            ),
            "invalid_publication_fingerprint",
        )
        if fingerprint_value is None:
            raise LaunchRegistryError("invalid_publication_fingerprint")
        fingerprint_text = _required_text(
            fingerprint_value, "invalid_publication_fingerprint"
        )
        snapshot_value = self._coalesce_publication_alias(
            snapshot_token, current_snapshot_token, "invalid_snapshot_token"
        )
        snapshot_text = (
            _required_text(snapshot_value, "invalid_snapshot_token")
            if snapshot_value is not None
            else launch.current_snapshot_token
        )
        snapshot_ref_value = self._coalesce_publication_alias(
            snapshot_ref, current_snapshot_ref, "invalid_snapshot_token"
        )
        snapshot_ref_text = (
            _required_text(snapshot_ref_value, "invalid_snapshot_token")
            if snapshot_ref_value is not None
            else None
        )
        source_value = self._coalesce_publication_alias(
            source_revision_id,
            source_revision,
            "invalid_publication_metadata",
        )
        source_text = _optional_text(source_value, "invalid_publication_metadata")
        cutoff_text = (
            _required_text(data_cutoff, "invalid_data_cutoff")
            if data_cutoff is not None
            else launch.data_cutoff
        )
        setup_digest = (
            _optional_text(setup_manifest_digest, "invalid_manifest_digest")
            if setup_manifest_digest is not None
            else launch.manifest_digest
        )
        manifest_revision_value = self._coalesce_publication_alias(
            manifest_revision,
            runtime_manifest_revision,
            "invalid_publication_revision",
        )
        manifest_revision_value = _normalize_optional_positive_int(
            manifest_revision_value, "invalid_publication_revision"
        )
        manifest_digest_value = self._coalesce_publication_alias(
            manifest_digest,
            runtime_manifest_digest,
            "invalid_manifest_digest",
        )
        manifest_digest_value = (
            _required_text(manifest_digest_value, "invalid_manifest_digest")
            if manifest_digest_value is not None
            else None
        )
        denominator = _normalize_nonnegative_int(
            mandatory_denominator, "invalid_publication_metadata"
        )
        sites_value = self._coalesce_publication_alias(
            site_coverage, sites, "invalid_publication_metadata"
        )
        sites_tuple = _normalize_publication_tokens(
            sites_value, allow_single_text=False
        )
        setup_identity_value = self._coalesce_publication_alias(
            setup_manifest_identity,
            setup_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        runtime_identity_value = self._coalesce_publication_alias(
            runtime_manifest_identity,
            runtime_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        setup_identity = _normalize_publication_object(setup_identity_value)
        runtime_identity = _normalize_publication_object(runtime_identity_value)
        receipt_value = self._coalesce_publication_alias(
            receipt_identities, receipt_set, "invalid_publication_metadata"
        )
        receipt_tuple = _normalize_publication_tokens(receipt_value)
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
        s4_identity_tuple = _normalize_publication_tokens(s4_identity_value)
        s4_digest_tuple = _normalize_publication_tokens(s4_digest_value)
        receipt_digest = _optional_text(
            receipt_set_digest, "invalid_publication_metadata"
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
        r5_id = _optional_text(r5_id_value, "invalid_publication_metadata")
        r5_digest = _optional_text(
            r5_digest_value, "invalid_publication_metadata"
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing_for_key = self._find_publication_by_key(
                    project_text, key_text
                )
                if (
                    existing_for_key is not None
                    and existing_for_key.run_id != launch.run_id
                ):
                    raise IdempotencyConflictError()
                existing_for_run = self._find_publication_by_run(
                    project_text, launch.run_id
                )
                existing = existing_for_run or existing_for_key
                if existing is not None:
                    if (
                        existing.publication_revision != revision_text
                        or existing.publication_fingerprint != fingerprint_text
                    ):
                        raise IdempotencyConflictError()
                    connection.commit()
                    return ResultPublication(
                        **{
                            **existing.__dict__,
                            "replayed": True,
                        }
                    )
                now = self._now()
                connection.execute(
                    """INSERT INTO r7_result_publications(
                        project_id, run_id, public_run_token, idempotency_key,
                        publication_revision, publication_fingerprint,
                        mode, execution_basis, snapshot_token, snapshot_ref,
                        source_revision_id, data_cutoff, setup_manifest_digest,
                        manifest_revision, manifest_digest, mandatory_denominator,
                        site_coverage_json, setup_manifest_identity_json,
                        runtime_manifest_identity_json, receipt_identities_json,
                        receipt_set_digest, r5_authority_packet_id,
                        r5_authority_packet_digest,
                        s4_authority_packet_identities_json,
                        s4_authority_packet_digests_json, publication_state,
                        failure_code, failure_message, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project_text,
                        launch.run_id,
                        launch.public_run_token,
                        key_text,
                        revision_text,
                        fingerprint_text,
                        launch.mode,
                        launch.execution_basis,
                        snapshot_text,
                        snapshot_ref_text,
                        source_text,
                        cutoff_text,
                        setup_digest,
                        manifest_revision_value,
                        manifest_digest_value,
                        denominator,
                        _json_token_list(sites_tuple),
                        canonical_json(setup_identity),
                        canonical_json(runtime_identity),
                        _json_token_list(receipt_tuple),
                        receipt_digest,
                        r5_id,
                        r5_digest,
                        _json_token_list(s4_identity_tuple),
                        _json_token_list(s4_digest_tuple),
                        PUBLICATION_STATE_PUBLISHING,
                        None,
                        None,
                        now,
                        now,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ?",
                    (project_text, launch.run_id),
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
            except sqlite3.IntegrityError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                existing = self._find_publication_by_run(
                    project_text, launch.run_id
                )
                if (
                    existing is not None
                    and existing.publication_revision == revision_text
                    and existing.publication_fingerprint == fingerprint_text
                ):
                    return ResultPublication(
                        **{
                            **existing.__dict__,
                            "replayed": True,
                        }
                    )
                raise IdempotencyConflictError()
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

    reserve_result_publication = reserve_publication

    def bind_publication_runtime_manifest(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: Any = PUBLICATION_REVISION,
        runtime_manifest_revision: Optional[int] = None,
        runtime_manifest_identity: Any = None,
        runtime_manifest_digest: Optional[str] = None,
        mandatory_denominator: Optional[int] = None,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        fingerprint: Optional[str] = None,
        expected_fingerprint: Optional[str] = None,
        expected_publication_fingerprint: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        manifest_revision: Optional[int] = None,
        manifest_digest: Optional[str] = None,
        runtime_manifest_work_unit_identity: Any = None,
        runtime_manifest: Any = None,
        runtime_mandatory_denominator: Optional[int] = None,
        denominator: Optional[int] = None,
        setup_manifest_identity: Any = None,
        setup_manifest_work_unit_identity: Any = None,
    ) -> ResultPublication:
        """CAS-bind the runtime manifest after reserving a publication.

        Runtime identity is deliberately bound in its own transaction.  The
        product publication path must reserve first, read runtime progress and
        manifest facts second, and only then evaluate the receipt/R5 gates.
        This method never opens the launch result flag.
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
            expected_publication_state,
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else PUBLICATION_STATE_PUBLISHING
        )
        if expected not in PUBLICATION_STATE_VALUES:
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
        expected_fingerprint_text = (
            _required_text(fingerprint_value, "invalid_publication_fingerprint")
            if fingerprint_value is not None
            else None
        )

        runtime_revision_value = self._coalesce_publication_alias(
            runtime_manifest_revision,
            manifest_revision,
            "invalid_publication_revision",
        )
        if runtime_revision_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_revision_text = _normalize_optional_positive_int(
            runtime_revision_value, "invalid_publication_revision"
        )
        if runtime_revision_text is None:
            raise LaunchRegistryError("invalid_publication_metadata")

        runtime_identity_value = self._coalesce_publication_alias(
            runtime_manifest_identity,
            self._coalesce_publication_alias(
                runtime_manifest_work_unit_identity,
                runtime_manifest,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        if runtime_identity_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_identity = _normalize_publication_object(runtime_identity_value)
        if not runtime_identity:
            raise LaunchRegistryError("invalid_publication_metadata")
        try:
            runtime_work_units = _manifest_work_unit_mapping(runtime_identity)
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("invalid_publication_metadata") from exc
        if not runtime_work_units:
            raise LaunchRegistryError("invalid_publication_metadata")

        runtime_digest_value = self._coalesce_publication_alias(
            runtime_manifest_digest,
            manifest_digest,
            "invalid_manifest_digest",
        )
        if runtime_digest_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_digest_text = _required_text(
            runtime_digest_value, "invalid_manifest_digest"
        )

        denominator_value = self._coalesce_publication_alias(
            mandatory_denominator,
            self._coalesce_publication_alias(
                runtime_mandatory_denominator,
                denominator,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        derived_denominator = sum(
            1 for _, mandatory in runtime_work_units if mandatory
        )
        denominator_text = (
            _normalize_nonnegative_int(
                denominator_value, "invalid_publication_metadata"
            )
            if denominator_value is not None
            else derived_denominator
        )
        if denominator_text != derived_denominator:
            raise LaunchRegistryError("publication_cas_conflict")

        setup_identity_value = self._coalesce_publication_alias(
            setup_manifest_identity,
            setup_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        supplied_setup_identity = (
            _normalize_publication_object(setup_identity_value)
            if setup_identity_value is not None
            else None
        )

        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if (
                    expected_fingerprint_text is not None
                    and current.publication_fingerprint != expected_fingerprint_text
                ):
                    raise IdempotencyConflictError()
                if current.publication_state != PUBLICATION_STATE_PUBLISHING:
                    raise LaunchRegistryError("illegal_publication_transition")

                try:
                    setup_work_units = _manifest_work_unit_mapping(
                        current.setup_manifest_identity
                    )
                except LaunchRegistryError as exc:
                    raise LaunchRegistryError("publication_cas_conflict") from exc
                if current.setup_manifest_identity:
                    if setup_work_units != runtime_work_units:
                        raise LaunchRegistryError("publication_cas_conflict")
                    setup_denominator = sum(
                        1 for _, mandatory in setup_work_units if mandatory
                    )
                    if setup_denominator != denominator_text:
                        raise LaunchRegistryError("publication_cas_conflict")
                if supplied_setup_identity is not None:
                    try:
                        supplied_setup_work_units = _manifest_work_unit_mapping(
                            supplied_setup_identity
                        )
                    except LaunchRegistryError as exc:
                        raise LaunchRegistryError(
                            "invalid_publication_metadata"
                        ) from exc
                    if supplied_setup_work_units != runtime_work_units:
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        current.setup_manifest_identity
                        and supplied_setup_identity
                        != current.setup_manifest_identity
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                if current.setup_manifest_identity:
                    if current.mandatory_denominator != denominator_text:
                        raise LaunchRegistryError("publication_cas_conflict")
                elif (
                    current.mandatory_denominator != 0
                    and current.mandatory_denominator != denominator_text
                ):
                    raise LaunchRegistryError("publication_cas_conflict")

                already_bound = (
                    current.manifest_revision is not None
                    or current.manifest_digest is not None
                    or bool(current.runtime_manifest_identity)
                )
                bound_values_match = (
                    current.manifest_revision == runtime_revision_text
                    and current.manifest_digest == runtime_digest_text
                    and current.runtime_manifest_identity == runtime_identity
                    and current.mandatory_denominator == denominator_text
                )
                if already_bound:
                    if not bound_values_match:
                        raise LaunchRegistryError("publication_cas_conflict")
                    connection.commit()
                    return ResultPublication(
                        **{**current.__dict__, "replayed": True}
                    )

                updated_at = self._now()
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "manifest_revision = ?, manifest_digest = ?, "
                    "mandatory_denominator = ?, runtime_manifest_identity_json = ?, "
                    "updated_at = ? WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ? "
                    "AND publication_fingerprint = ?",
                    (
                        runtime_revision_text,
                        runtime_digest_text,
                        denominator_text,
                        canonical_json(runtime_identity),
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        PUBLICATION_STATE_PUBLISHING,
                        current.publication_fingerprint,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure(
                    "bind_publication_runtime_manifest.after_update"
                )
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

    bind_runtime_manifest = bind_publication_runtime_manifest
    bind_publication_manifest = bind_publication_runtime_manifest

    def get_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
    ) -> ResultPublication:
        selector = self._coalesce_publication_alias(
            run_id,
            public_run_token,
            "run_not_found",
        )
        project_text, launch = self._publication_project_run(
            project, run, project_id=project_id, run_id=selector
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        with self._lock:
            publication = self._find_publication_by_run(project_text, launch.run_id)
        if publication is None or publication.publication_revision != revision_text:
            raise LaunchRegistryError("publication_not_found")
        return publication

    get_result_publication = get_publication
    get_publication_by_run = get_publication
    get_publication_for_run = get_publication
    publication_for_run = get_publication

    def get_publication_by_public_token(
        self,
        public_run_token: str,
        *,
        project_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        revision: Optional[int] = None,
    ) -> ResultPublication:
        return self.get_publication(
            project_id=project_id,
            run=public_run_token,
            publication_revision=publication_revision,
            revision=revision,
        )

    publication_by_public_token = get_publication_by_public_token

    def get_publication_by_result_context_token(
        self,
        result_context_token: str,
        *,
        project_id: Optional[str] = None,
    ) -> ResultPublication:
        project = self._project(project_id)
        token = _normalize_result_context_token(
            result_context_token, "publication_not_found"
        )
        if token is None:
            raise LaunchRegistryError("publication_not_found")
        with self._lock:
            row = self._require_conn().execute(
                "SELECT * FROM r7_result_publications "
                "WHERE project_id = ? AND result_context_token = ?",
                (project, token),
            ).fetchone()
        if row is None:
            raise LaunchRegistryError("publication_not_found")
        return self._row_to_publication(row)
    get_result_publication_by_context_token = (
        get_publication_by_result_context_token
    )
    publication_by_result_context_token = (
        get_publication_by_result_context_token
    )
    get_by_result_context_token = get_publication_by_result_context_token
    resolve_result_context_token = get_publication_by_result_context_token
    get_publication_by_context_token = get_publication_by_result_context_token
    publication_for_result_context = get_publication_by_result_context_token

    def get_publication_by_idempotency(
        self,
        idempotency_key: str,
        *,
        project_id: Optional[str] = None,
    ) -> ResultPublication:
        project = self._project(project_id)
        key = _required_text(idempotency_key, "invalid_idempotency_key")
        with self._lock:
            publication = self._find_publication_by_key(project, key)
        if publication is None:
            raise LaunchRegistryError("publication_not_found")
        return publication

    def list_publications(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Tuple[ResultPublication, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            rows = self._require_conn().execute(
                "SELECT * FROM r7_result_publications "
                "WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(self._row_to_publication(row) for row in rows)

    result_publications = list_publications
    list_result_publications = list_publications
    publication_history = list_publications

    def _publication_row_for_update(
        self,
        connection: sqlite3.Connection,
        project: str,
        run_id: str,
        revision: int,
    ) -> ResultPublication:
        row = connection.execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND run_id = ? AND publication_revision = ?",
            (project, run_id, revision),
        ).fetchone()
        if row is None:
            raise LaunchRegistryError("publication_not_found")
        return self._row_to_publication(row)
