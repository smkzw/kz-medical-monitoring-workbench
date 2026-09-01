#!/usr/bin/env python3
"""Run the integrated synthetic R1 closure and write inspectable evidence.

Usage:
    .venv/bin/python poc/medical_monitoring_ai_native_r1/scripts/run_integrated_closure.py \\
        --output-dir /path/to/a/new/synthetic-closure-output

The script requires a caller-supplied absent or empty directory; it refuses to
write into any non-empty directory. It starts no service, calls no provider,
and reads no real project data.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Optional


POC_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = POC_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mm_r1.domain import to_jsonable  # noqa: E402
from mm_r1.integrated_closure import (  # noqa: E402
    CLOSURE_MARKER,
    SyntheticClosureTransport,
    run_integrated_closure,
)
from mm_r1.store import Store  # noqa: E402

import json  # noqa: E402


OUTPUT_FILENAMES = (
    "r1.sqlite3",
    "closure_summary.json",
    "identity_chain.json",
    "audience_progress.json",
    "ae_mh_result.json",
    "projections.json",
    "recovery.json",
)


def _write_json(path: Path, value: Any) -> None:
    """Write JSON using the domain serializer, not default=str."""
    path.write_text(
        json.dumps(to_jsonable(value), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _resolve_output_dir(value: Optional[str]) -> Path:
    if not value:
        raise SystemExit("--output-dir is required (caller-supplied new directory)")
    output_dir = Path(value).resolve()
    if output_dir.exists():
        children = [p for p in output_dir.iterdir()]
        if children:
            raise SystemExit(
                "refusing to write into non-empty directory: %s" % output_dir
            )
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_closure(output_dir: Path) -> Dict[str, Any]:
    """Build one synthetic integrated closure run and return the summary."""

    db_path = output_dir / "r1.sqlite3"
    artifact_dir = output_dir / "artifacts"

    with Store(db_path, artifact_dir) as store:
        result = run_integrated_closure(store)

        recovery = store.recover()
        audit_ok, audit_first_bad, audit_count = store.verify_audit_chain()
        run_payload = store.get_run(result.run_id)
        artifact_payload = store.list_artifacts(result.run_id)
        progress = store.manifest_progress(result.run_id)

        ae_mh_dict = result.ae_mh_result.as_dict()
        projections_dict = result.projections.as_dict()
        audience = result.audience_progress
        identity = result.identity_chain

        recovery_payload = {
            "audit_ok": recovery.audit_ok,
            "audit_first_bad_seq": recovery.audit_first_bad_seq,
            "audit_count": recovery.audit_count,
            "orphan_artifacts": recovery.orphan_artifacts,
            "integrity_violations": recovery.integrity_violations,
            "incomplete_runs": recovery.incomplete_runs,
        }
        summary: Dict[str, Any] = {
            "fixture_marker": CLOSURE_MARKER,
            "closure": "medical_monitoring_r1_integrated_closure",
            "sqlite_version": sqlite3.sqlite_version,
            "output_dir": str(output_dir),
            "sqlite_path": str(db_path),
            "artifact_dir": str(artifact_dir),
            "run_id": result.run_id,
            "project_id": result.project_id,
            "snapshot_n_id": result.snapshot_n_id,
            "snapshot_n1_id": result.snapshot_n1_id,
            "manifest_revision": result.manifest_revision,
            "run_output_state": result.run_output_state,
            "evidence_state": result.evidence_state,
            "transport_call_count": result.transport_call_count,
            "facts_committed": result.facts_committed,
            "candidates_persisted": result.candidates_persisted,
            "queries_persisted": result.queries_persisted,
            "spines_persisted": result.spines_persisted,
            "projections_persisted": result.projections_persisted,
            "ai_status": (
                result.ai_attempt_result.status.value
                if result.ai_attempt_result is not None
                else "skipped"
            ),
            "run": {
                "analysis_state": run_payload.analysis_state.value,
                "evidence_state": run_payload.evidence_state.value,
                "output_state": run_payload.output_state.value,
                "manifest_revision": run_payload.manifest_revision,
            },
            "progress": progress,
            "audit": {
                "verified": audit_ok,
                "first_bad_seq": audit_first_bad,
                "count": audit_count,
            },
            "artifacts": [item.artifact_id for item in artifact_payload],
            "recovery": recovery_payload,
            "identity_chain": identity,
            "service_started": False,
            "provider_called": False,
            "real_project_data": False,
        }

    _write_json(output_dir / "closure_summary.json", summary)
    _write_json(output_dir / "identity_chain.json", identity)
    _write_json(output_dir / "audience_progress.json", audience)
    _write_json(output_dir / "ae_mh_result.json", ae_mh_dict)
    _write_json(output_dir / "projections.json", projections_dict)
    _write_json(output_dir / "recovery.json", recovery_payload)
    return summary


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        help="caller-supplied absent or empty directory for closure output",
    )
    parser.add_argument(
        "output_dir_pos",
        nargs="?",
        help="positional alias for --output-dir",
    )
    args = parser.parse_args(argv)

    output_dir = _resolve_output_dir(args.output_dir or args.output_dir_pos)
    summary = run_closure(output_dir)

    print("SYNTHETIC_CLOSURE_OK")
    print("OUTPUT_DIR=%s" % output_dir)
    print("SQLITE=%s" % (output_dir / "r1.sqlite3"))
    print("SUMMARY=%s" % (output_dir / "closure_summary.json"))
    print("RUN_STATE=%s" % summary["run_output_state"])
    print("EVIDENCE_STATE=%s" % summary["evidence_state"])
    print("PROGRESS=%s/%s" % (summary["progress"]["completed"], summary["progress"]["total"]))
    print("TRANSPORT_CALLS=%d" % summary["transport_call_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
