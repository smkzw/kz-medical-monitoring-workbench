"""Single DDL source for the R7 root operation and project-audit ledger."""

ROOT_OPERATION_DDL = """
CREATE TABLE IF NOT EXISTS backup_operations (
    operation_id TEXT PRIMARY KEY NOT NULL,
    operation_kind TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    canonical_project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    progress_percent INTEGER NOT NULL,
    current_step TEXT NOT NULL,
    package_id TEXT,
    source_workspace_fingerprint TEXT,
    terminal_outcome TEXT,
    error_code TEXT,
    error_message TEXT,
    rollback_path TEXT,
    staging_path TEXT,
    package_path TEXT,
    maintenance_state TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(operation_kind, idempotency_key, canonical_project_id)
);
CREATE INDEX IF NOT EXISTS backup_operations_project_idx
    ON backup_operations(canonical_project_id, updated_at, operation_id);
CREATE INDEX IF NOT EXISTS backup_operations_package_idx
    ON backup_operations(canonical_project_id, package_id);
"""

PROJECT_AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS project_audit_events (
    canonical_project_id TEXT NOT NULL,
    project_seq INTEGER NOT NULL CHECK(project_seq >= 1),
    event_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    operation_kind TEXT NOT NULL DEFAULT '',
    operation_ref TEXT NOT NULL DEFAULT '',
    boundary_token TEXT NOT NULL DEFAULT '',
    principal_snapshot_hash TEXT NOT NULL,
    authorization_decision_hash TEXT NOT NULL,
    before_digest TEXT NOT NULL DEFAULT '',
    after_digest TEXT NOT NULL DEFAULT '',
    domain_anchors_json TEXT NOT NULL,
    result_code TEXT NOT NULL DEFAULT '',
    reason_code TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,
    PRIMARY KEY(canonical_project_id, project_seq)
);
CREATE INDEX IF NOT EXISTS project_audit_events_project_idx
    ON project_audit_events(canonical_project_id, project_seq);
CREATE INDEX IF NOT EXISTS project_audit_events_operation_idx
    ON project_audit_events(canonical_project_id, operation_ref, boundary_token, event_kind);
CREATE UNIQUE INDEX IF NOT EXISTS project_audit_boundary_key_idx
    ON project_audit_events(operation_ref, boundary_token, event_kind)
    WHERE operation_ref <> '' AND boundary_token <> '';
CREATE TABLE IF NOT EXISTS project_audit_heads (
    canonical_project_id TEXT PRIMARY KEY NOT NULL,
    head_seq INTEGER NOT NULL CHECK(head_seq >= 0),
    head_hash TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS project_audit_events_no_update
BEFORE UPDATE ON project_audit_events
BEGIN
    SELECT RAISE(ABORT, 'project_audit_events_append_only');
END;
CREATE TRIGGER IF NOT EXISTS project_audit_events_no_delete
BEFORE DELETE ON project_audit_events
BEGIN
    SELECT RAISE(ABORT, 'project_audit_events_append_only');
END;
"""

ROOT_LEDGER_DDL = ROOT_OPERATION_DDL + PROJECT_AUDIT_DDL
