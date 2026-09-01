"""Canonical current R7 launch-registry schema DDL.

This stdlib-only module is the single current-DDL source consumed by the
mutable launch constructor, the 09B staging migrator, and the schema
manifest. Keep the fragments separate because migrations add each target
table/index at explicit marker-last boundaries.
"""

from __future__ import annotations

BASE_DDL = '\nCREATE TABLE IF NOT EXISTS r7_launch_registry_meta (\n    key TEXT PRIMARY KEY NOT NULL,\n    value TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS r7_launch_registry (\n    sequence INTEGER PRIMARY KEY AUTOINCREMENT,\n    project_id TEXT NOT NULL,\n    idempotency_key TEXT NOT NULL,\n    run_id TEXT NOT NULL UNIQUE,\n    public_run_token TEXT NOT NULL UNIQUE,\n    request_fingerprint TEXT NOT NULL,\n    mode TEXT NOT NULL,\n    execution_basis TEXT NOT NULL,\n    current_snapshot_token TEXT NOT NULL,\n    baseline_token TEXT,\n    rule_tokens_json TEXT NOT NULL,\n    data_cutoff TEXT NOT NULL,\n    comparison_range_text TEXT NOT NULL,\n    run_state TEXT NOT NULL,\n    result_available INTEGER NOT NULL DEFAULT 0,\n    main_action TEXT NOT NULL,\n    manifest_digest TEXT,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    UNIQUE(project_id, idempotency_key)\n);\nCREATE INDEX IF NOT EXISTS r7_launch_registry_history_idx\n    ON r7_launch_registry(project_id, created_at DESC, sequence DESC);\n'

PUBLICATION_DDL = "\nCREATE TABLE IF NOT EXISTS r7_result_publications (\n    sequence INTEGER PRIMARY KEY AUTOINCREMENT,\n    project_id TEXT NOT NULL,\n    run_id TEXT NOT NULL,\n    public_run_token TEXT NOT NULL,\n    result_context_token TEXT,\n    idempotency_key TEXT NOT NULL,\n    publication_revision INTEGER NOT NULL DEFAULT 1,\n    publication_fingerprint TEXT NOT NULL,\n    mode TEXT NOT NULL,\n    execution_basis TEXT NOT NULL,\n    snapshot_token TEXT NOT NULL,\n    snapshot_ref TEXT,\n    source_revision_id TEXT,\n    data_cutoff TEXT NOT NULL,\n    setup_manifest_digest TEXT,\n    manifest_revision INTEGER,\n    manifest_digest TEXT,\n    mandatory_denominator INTEGER NOT NULL DEFAULT 0,\n    site_coverage_json TEXT NOT NULL DEFAULT '[]',\n    setup_manifest_identity_json TEXT NOT NULL DEFAULT '{}',\n    runtime_manifest_identity_json TEXT NOT NULL DEFAULT '{}',\n    receipt_identities_json TEXT NOT NULL DEFAULT '[]',\n    receipt_set_digest TEXT,\n    r5_authority_packet_id TEXT,\n    r5_authority_packet_digest TEXT,\n    s4_authority_packet_identities_json TEXT NOT NULL DEFAULT '[]',\n    s4_authority_packet_digests_json TEXT NOT NULL DEFAULT '[]',\n    r6_output_set_digest TEXT,\n    artifact_member_ids_json TEXT NOT NULL DEFAULT '[]',\n    artifact_member_set_digest TEXT,\n    publication_state TEXT NOT NULL,\n    failure_code TEXT,\n    failure_message TEXT,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    UNIQUE(project_id, run_id),\n    UNIQUE(project_id, idempotency_key),\n    CHECK(publication_revision = 1),\n    CHECK(publication_state IN (\n        'publishing',\n        'available',\n        'recoverable_failed',\n        'blocked'\n    ))\n);\nCREATE INDEX IF NOT EXISTS r7_result_publications_project_idx\n    ON r7_result_publications(project_id, created_at DESC, sequence DESC);\n"

RESULT_CONTEXT_INDEX_DDL = '\nCREATE UNIQUE INDEX IF NOT EXISTS r7_result_publications_context_idx\n    ON r7_result_publications(project_id, result_context_token)\n    WHERE result_context_token IS NOT NULL;\n'

CONTINUITY_PLANS_DDL = "\nCREATE TABLE IF NOT EXISTS r7_continuity_plans (\n    sequence INTEGER PRIMARY KEY AUTOINCREMENT,\n    plan_id TEXT NOT NULL UNIQUE,\n    project_id TEXT NOT NULL,\n    target_run_id TEXT NOT NULL,\n    target_public_run_token TEXT,\n    source_run_id TEXT,\n    source_publication_id TEXT,\n    source_public_run_token TEXT,\n    mode TEXT NOT NULL,\n    execution_basis TEXT NOT NULL,\n    target_snapshot_id TEXT NOT NULL,\n    target_data_cutoff TEXT NOT NULL,\n    target_rule_revision_ids_json TEXT NOT NULL,\n    target_decision_version TEXT NOT NULL,\n    baseline_source_run_id TEXT NOT NULL DEFAULT '',\n    baseline_source_publication_id TEXT NOT NULL DEFAULT '',\n    baseline_source_public_run_token TEXT NOT NULL DEFAULT '',\n    r5_authority_digest TEXT NOT NULL,\n    r6_publication_digest TEXT NOT NULL,\n    r6_receipt_digest TEXT NOT NULL,\n    r6_output_set_digest TEXT NOT NULL DEFAULT '',\n    plan_digest TEXT NOT NULL,\n    status TEXT NOT NULL,\n    counts_json TEXT NOT NULL,\n    plan_json TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    UNIQUE(project_id, target_run_id),\n    CHECK(status IN (\n        'staging',\n        'verified',\n        'published',\n        'blocked'\n    ))\n);\n"

CONTINUITY_ITEMS_DDL = "\nCREATE TABLE IF NOT EXISTS r7_continuity_items (\n    sequence INTEGER PRIMARY KEY AUTOINCREMENT,\n    plan_id TEXT NOT NULL,\n    ordinal INTEGER NOT NULL,\n    object_type TEXT NOT NULL,\n    object_ref TEXT NOT NULL,\n    disposition TEXT NOT NULL,\n    source_run_id TEXT NOT NULL DEFAULT '',\n    source_publication_id TEXT NOT NULL DEFAULT '',\n    source_public_run_token TEXT NOT NULL DEFAULT '',\n    source_object_id TEXT NOT NULL DEFAULT '',\n    target_object_id TEXT NOT NULL DEFAULT '',\n    source_artifact_id TEXT NOT NULL DEFAULT '',\n    source_artifact_sha256 TEXT NOT NULL DEFAULT '',\n    prior_risk_state TEXT,\n    current_risk_state TEXT,\n    prior_severity TEXT,\n    current_severity TEXT,\n    governing_rule_revision_ids_json TEXT NOT NULL,\n    changed_applicable_rule_ids_json TEXT NOT NULL,\n    attribution TEXT NOT NULL DEFAULT '',\n    evidence_json TEXT NOT NULL,\n    item_digest TEXT NOT NULL,\n    item_json TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    UNIQUE(plan_id, ordinal),\n    FOREIGN KEY(plan_id) REFERENCES r7_continuity_plans(plan_id) ON DELETE CASCADE,\n    CHECK(ordinal >= 0)\n);\n"

CONTINUITY_INDEX_DDL = '\nCREATE INDEX IF NOT EXISTS r7_continuity_plans_project_idx\n    ON r7_continuity_plans(project_id, created_at DESC, sequence DESC);\nCREATE INDEX IF NOT EXISTS r7_continuity_items_plan_idx\n    ON r7_continuity_items(plan_id, ordinal ASC, sequence ASC);\n'

CONTINUITY_DDL = CONTINUITY_PLANS_DDL + CONTINUITY_ITEMS_DDL

LAUNCH_DDL = (
    BASE_DDL
    + PUBLICATION_DDL
    + RESULT_CONTEXT_INDEX_DDL
    + CONTINUITY_DDL
    + CONTINUITY_INDEX_DDL
)


__all__ = [
    "BASE_DDL",
    "CONTINUITY_DDL",
    "CONTINUITY_INDEX_DDL",
    "CONTINUITY_ITEMS_DDL",
    "CONTINUITY_PLANS_DDL",
    "LAUNCH_DDL",
    "PUBLICATION_DDL",
    "RESULT_CONTEXT_INDEX_DDL",
]
