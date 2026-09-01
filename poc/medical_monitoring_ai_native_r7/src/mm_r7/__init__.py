"""mm_r7: R7 product-integration seam (slice-01 + slice-02 run entry).

Slice 01 (accepted with limited scope; Codex owns acceptance):

* ``mm_r7.profile_store`` -- immutable versioned ExecutionProfile layer
  persistence (global_default / capability_agent / project / run_override),
  SQLite close/reopen parity, and public/audit projections that never accept
  or emit credential values.
* ``mm_r7.run_binding`` -- effective-profile freeze and immutable Monitoring
  Run binding (separate create-only path).

Slice 02 (limited acceptance pending final Codex record):

* ``mm_r7.run_entry`` -- explicit idempotent workspace bootstrap, four-layer
  scope resolution, effective-profile freeze, Run bind/replay/conflict, and
  public projections with stable Chinese errors. Does not mount product
  services, open ports, call models, or touch real projects / medical-writing.

This package does not modify product services, frontend, medical-writing, real
projects, or R1-R6 source.

Acceptance is pinned in
``context/medical_monitoring_r7_slice_01_execution_profile_run_binding_acceptance_record_20260828.md``
for slice-01. Slice-02 acceptance is owned by Codex after worker delivery.
Python standard library only for persistence. Deterministic under any
``PYTHONHASHSEED`` and optimizer level (``-O``/``-OO``).
"""

from __future__ import annotations

from . import (
    api,
    continuity,
    continuity_bridge,
    harness_runtime,
    launch_registry,
    profile_store,
    run_binding,
    run_entry,
    run_setup,
    migration,
    project_lifecycle,
    project_audit,
    project_verifier,
    technical_log,
    schema_manifest,
)

__version__ = "0.2"

__all__ = [
    "profile_store",
    "harness_runtime",
    "api",
    "run_binding",
    "run_entry",
    "launch_registry",
    "run_setup",
    "continuity",
    "continuity_bridge",
    "schema_manifest",
    "migration",
    "project_lifecycle",
    "__version__",
    "technical_log",
    "project_audit",
    "project_verifier",
]
