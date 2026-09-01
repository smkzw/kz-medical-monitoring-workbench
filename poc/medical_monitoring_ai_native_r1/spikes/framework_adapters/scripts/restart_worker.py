#!/usr/bin/env python3
"""Subprocess entrypoint for the framework-neutral restart/replay harness.

Invoked by :func:`mm_r1_spike.restart_harness.run_subprocess_worker` as a FRESH
interpreter process (so its PID differs from the parent and from any sibling
process).  It opens the persisted authoritative Store + separate work-event
store + JSON checkpoint file, runs synthetic nodes up to an optional injected
boundary (``--stop-after-node``), writes a JSON result line, and exits.

It performs NO domain authority promotion: work events and the JSON checkpoint
are separate operational persistence; the slice1 Store is the sole domain
authority.  Only JSON-compatible synthetic state is used.

This script is owned by worker_01 and must not import LangGraph or Microsoft
Agent Framework.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from mm_r1.store import Store

from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.restart_harness import (
    NODE_A,
    NODE_B,
    NODE_C,
    bootstrap_run,
    run_nodes_up_to_boundary,
)
from mm_r1_spike.work_events import WorkEventStore


def _store_paths(work_dir: Path):
    work_dir = Path(work_dir)
    store_db = work_dir / "authoritative.sqlite3"
    artifact_dir = work_dir / "artifacts"
    events_db = work_dir / "work_events.sqlite3"
    return store_db, artifact_dir, events_db


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="framework-neutral restart worker")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stop-after-node", default=None,
                        help="inject a stop boundary after this node id")
    parser.add_argument("--invocation-marker", default=None,
                        help="stable marker echoed in the result for boundary evidence")
    parser.add_argument("--bootstrap", action="store_true",
                        help="create the synthetic project/run/manifest first (first process only)")
    parser.add_argument("--manifest-revision", type=int, default=1)
    args = parser.parse_args(argv)

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    store_db, artifact_dir, events_db = _store_paths(work_dir)

    store = Store(store_db, artifact_dir)
    events = WorkEventStore(events_db)
    try:
        if args.bootstrap:
            manifest = bootstrap_run(store, args.run_id,
                                     manifest_revision=args.manifest_revision)
        else:
            manifest = store.get_manifest(args.run_id)
            if manifest is None:
                raise RuntimeError(f"no manifest frozen for run {args.run_id}")

        contract = ConformanceContract.from_manifest(manifest)
        results = run_nodes_up_to_boundary(
            store=store,
            events=events,
            contract=contract,
            work_dir=work_dir,
            run_id=args.run_id,
            stop_after_node=args.stop_after_node,
            rev=manifest.revision,
        )

        progress = store.manifest_progress(args.run_id)
        result = {
            "pid": __import__("os").getpid(),
            "ppid": __import__("os").getppid(),
            "run_id": args.run_id,
            "invocation_marker": args.invocation_marker,
            "manifest_revision": contract.manifest_revision,
            "nodes": [
                {"node_id": r.node_id, "status": r.status, "reused": r.reused,
                 "work_event_sequence": r.work_event_sequence}
                for r in results
            ],
            "progress": progress,
            "stop_after_node": args.stop_after_node,
            "work_event_count": events.count(args.run_id),
            "distinct_idempotency_keys": events.distinct_idempotency_keys(args.run_id),
        }
        # Single JSON result line for easy parsing by the parent/tests.
        sys.stdout.write("RESTART_WORKER_RESULT=" + json.dumps(result, sort_keys=True) + "\n")
        sys.stdout.flush()
        return 0
    finally:
        events.close()
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
