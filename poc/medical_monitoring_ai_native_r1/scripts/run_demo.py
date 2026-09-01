#!/usr/bin/env python3
"""Run the isolated synthetic R1 slice and write inspectable evidence.

The demo is deliberately a caller-output-path command.  It creates no service,
does not call a provider, and refuses to overwrite an existing demo database.
All data is synthetic and is written below the path supplied by the caller.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional


POC_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = POC_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mm_r1 import domain  # noqa: E402
from mm_r1.ae_mh import build_ae_mh_artifact, run_ae_mh_vertical_slice  # noqa: E402
from mm_r1.domain import (  # noqa: E402
    ACCEPTANCE_CHAIN,
    AnalysisState,
    ExecutionManifest,
    ManifestNode,
    NodeStatus,
    NodeType,
    OutputState,
    to_jsonable,
)
from mm_r1.fixtures import create_synthetic_run, seed_synthetic_snapshots  # noqa: E402
from mm_r1.projections import build_projections, persist_projections  # noqa: E402
from mm_r1.report_review import review_report, synthetic_report_fixture  # noqa: E402
from mm_r1.store import Store  # noqa: E402


OUTPUT_FILENAMES = (
    "acceptance.json",
    "audit.json",
    "progress.json",
    "projections.json",
    "recovery.json",
    "report_ledger.json",
    "run.json",
    "summary.json",
    "r1.sqlite3",
)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(to_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_output_dir(value: Optional[str]) -> Path:
    if not value:
        raise SystemExit("an output path is required: use --output-dir PATH or a positional PATH")
    output_dir = Path(value).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    conflicts = [name for name in OUTPUT_FILENAMES if (output_dir / name).exists()]
    if conflicts:
        raise SystemExit(
            "refusing to overwrite existing demo output: "
            + ", ".join(sorted(conflicts))
        )
    return output_dir


def run_demo(output_dir: Path) -> Dict[str, Any]:
    """Build one synthetic run and return the summary written to disk."""
    db_path = output_dir / "r1.sqlite3"
    artifact_dir = output_dir / "artifacts"
    facts_node_id = "SYNTHETIC-FACTS-NODE"
    candidate_node_id = "SYNTHETIC-AE-MH-CANDIDATE-NODE"
    report_node_id = "SYNTHETIC-REPORT-LEDGER-NODE"

    with Store(db_path, artifact_dir) as store:
        bundle = seed_synthetic_snapshots(store)

        # Acceptance evidence is read from the authoritative Store.  The demo
        # does not pass a caller-supplied acceptance claim into the evidence.
        acceptance = {
            snapshot_id: store.get_acceptance(snapshot_id)
            for snapshot_id in (bundle.snapshot_n.snapshot_id, bundle.snapshot_n1.snapshot_id)
        }
        baseline_proof = {
            snapshot_id: store.baseline_eligibility_proof(snapshot_id)
            for snapshot_id in acceptance
        }

        run = create_synthetic_run(store, bundle)
        manifest = ExecutionManifest(
            run_id=run.run_id,
            nodes=[
                ManifestNode(facts_node_id, NodeType.DETERMINISTIC_SERVICE, artifact_required=False),
                ManifestNode(candidate_node_id, NodeType.AI_CANDIDATE),
                ManifestNode(report_node_id, NodeType.DETERMINISTIC_SERVICE),
            ],
            source_coverage=["SYNTHETIC-full-listing", "SYNTHETIC-AE-MH"],
            identity_algorithm="synthetic-ae-mh-identity-v1",
            graph_id="SYNTHETIC-DEMO-GRAPH",
            graph_version="SYNTHETIC-DEMO-GRAPH-V1",
            schema_version="SYNTHETIC-DEMO-SCHEMA-V1",
        )
        store.set_manifest(manifest)
        store.update_run_state(run.run_id, analysis=AnalysisState.RUNNING)

        result_n = run_ae_mh_vertical_slice(
            bundle.listing_n,
            project_id=bundle.project_id,
            run_id="SYNTHETIC-DEMO-RUN-N",
            snapshot_version="SYNTHETIC-N",
            store=store,
            snapshot_id=bundle.snapshot_n.snapshot_id,
        )
        result_n1 = run_ae_mh_vertical_slice(
            bundle.listing_n1,
            project_id=bundle.project_id,
            run_id=run.run_id,
            snapshot_version="SYNTHETIC-N1",
            previous_result=result_n,
            store=store,
            snapshot_id=bundle.snapshot_n1.snapshot_id,
        )

        store.begin_node_run(run.run_id, facts_node_id, NodeType.DETERMINISTIC_SERVICE,
                             "SYNTHETIC-DEMO-FACTS-KEY")
        store.complete_node_run(
            run.run_id,
            facts_node_id,
            "SYNTHETIC-DEMO-FACTS-KEY",
            NodeStatus.PASSED,
            output={"fixture_marker": "SYNTHETIC", "facts_source": "AE/MH result"},
        )

        candidate_artifact = replace(
            build_ae_mh_artifact(result_n1),
            node_id=candidate_node_id,
        )
        store.begin_node_run(run.run_id, candidate_node_id, NodeType.AI_CANDIDATE,
                             "SYNTHETIC-DEMO-CANDIDATE-KEY")
        store.complete_node_run(
            run.run_id,
            candidate_node_id,
            "SYNTHETIC-DEMO-CANDIDATE-KEY",
            NodeStatus.PASSED,
            envelope=candidate_artifact,
            output={
                "fixture_marker": "SYNTHETIC",
                "candidate_count": result_n1.candidate_count,
                "reported_fact_count": result_n1.reported_ae_mh_count,
            },
        )

        report_review = review_report(
            synthetic_report_fixture(
                run_id=run.run_id,
                report_artifact_id="SYNTHETIC-DEMO-REPORT-ARTIFACT",
                cutoff="SYNTHETIC-N1-CUTOFF",
            )
        )
        report_artifact = report_review.ledger.to_artifact_envelope(node_id=report_node_id)
        store.begin_node_run(run.run_id, report_node_id, NodeType.DETERMINISTIC_SERVICE,
                             "SYNTHETIC-DEMO-REPORT-KEY")
        store.complete_node_run(
            run.run_id,
            report_node_id,
            "SYNTHETIC-DEMO-REPORT-KEY",
            NodeStatus.PASSED,
            envelope=report_artifact,
            output={"fixture_marker": "SYNTHETIC", "full_report_reviewed": report_review.full_report_reviewed},
        )

        # Facts and projections are persisted through their shared Store APIs;
        # the adapter/demo never promotes a candidate directly to a fact.
        from mm_r1.ae_mh import persist_ae_mh_result

        persisted_counts = persist_ae_mh_result(
            store,
            result_n1,
            facts_node_id=facts_node_id,
        )
        projections = build_projections(result_n1)
        persisted_projection_count = persist_projections(store, projections)

        store.update_run_state(run.run_id, evidence=domain.EvidenceState.COMPLETE)
        completed = store.complete_analysis(run.run_id, reason="SYNTHETIC demo completion")
        published = store.publish(
            run.run_id,
            OutputState.DRAFT_EXPORTABLE,
            reason="SYNTHETIC demo draft evidence",
        )
        recovery = store.recover()
        audit_ok, audit_first_bad, audit_count = store.verify_audit_chain()

        acceptance_payload = {
            snapshot_id: {
                "state": record.state.value,
                "accepted_by": record.accepted_by,
                "blocked": record.blocked,
                "ambiguity": record.ambiguity,
                "derived_baseline_eligible": baseline_proof[snapshot_id].is_baseline_eligible,
                "evidence_hash": baseline_proof[snapshot_id].evidence_hash,
            }
            for snapshot_id, record in acceptance.items()
        }
        progress = store.manifest_progress(run.run_id)
        audit = store.audit_trail()
        run_payload = store.get_run(run.run_id)
        artifact_payload = store.list_artifacts(run.run_id)
        recovery_payload = {
            "audit_ok_before_recovery_event": recovery.audit_ok,
            "audit_first_bad_seq": recovery.audit_first_bad_seq,
            "audit_count_before_recovery_event": recovery.audit_count,
            "orphan_artifacts": recovery.orphan_artifacts,
            "integrity_violations": recovery.integrity_violations,
            "incomplete_runs": recovery.incomplete_runs,
        }
        summary: Dict[str, Any] = {
            "fixture_marker": "SYNTHETIC",
            "demo": "medical_monitoring_ai_native_r1",
            "sqlite_version": sqlite3.sqlite_version,
            "output_dir": str(output_dir),
            "sqlite_path": str(db_path),
            "artifact_dir": str(artifact_dir),
            "acceptance_chain": [state.value for state in ACCEPTANCE_CHAIN],
            "acceptance": acceptance_payload,
            "run": run_payload,
            "completed_run": completed,
            "published_run": published,
            "progress": progress,
            "audit": {
                "verified_after_recovery": audit_ok,
                "first_bad_seq": audit_first_bad,
                "count_after_recovery": audit_count,
                "event_count_in_file": len(audit),
            },
            "artifacts": [item.artifact_id for item in artifact_payload],
            "ae_mh": {
                "snapshot_n_candidate_count": result_n.candidate_count,
                "snapshot_n1_candidate_count": result_n1.candidate_count,
                "reported_ae_mh_count": result_n1.reported_ae_mh_count,
                "persisted_counts": persisted_counts,
                "candidate_fact_separation": result_n1.candidate_fact_separation(),
            },
            "report": {
                "full_report_reviewed": report_review.full_report_reviewed,
                "reasons": list(report_review.reasons),
                "ledger_id": report_review.ledger.ledger_id,
            },
            "projection_count": persisted_projection_count,
            "service_started": False,
            "provider_called": False,
            "real_project_data": False,
        }

    _write_json(output_dir / "acceptance.json", acceptance_payload)
    _write_json(output_dir / "audit.json", audit)
    _write_json(output_dir / "progress.json", progress)
    _write_json(output_dir / "projections.json", projections.as_dict())
    _write_json(output_dir / "recovery.json", recovery_payload)
    _write_json(output_dir / "report_ledger.json", report_review.ledger.to_dict())
    _write_json(output_dir / "run.json", run_payload)
    _write_json(output_dir / "summary.json", summary)
    return summary


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="caller-supplied output directory")
    parser.add_argument("--output-dir", dest="output_dir", help="caller-supplied output directory")
    args = parser.parse_args(argv)
    if args.path and args.output_dir:
        parser.error("provide either PATH or --output-dir, not both")
    output_dir = _resolve_output_dir(args.output_dir or args.path)
    summary = run_demo(output_dir)
    print("SYNTHETIC_R1_DEMO_OK")
    print("OUTPUT_DIR=" + str(output_dir))
    print("SQLITE=" + str(output_dir / "r1.sqlite3"))
    print("JSON_SUMMARY=" + str(output_dir / "summary.json"))
    print("PROGRESS=" + str(output_dir / "progress.json"))
    print("AUDIT=" + str(output_dir / "audit.json"))
    print("PROJECTIONS=" + str(output_dir / "projections.json"))
    print("RUN_OUTPUT_STATE=" + str(summary["published_run"].output_state.value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
