#!/usr/bin/env python3
"""双VLM全量批跑收尾（v2）：全量裁决（主+盲核合并映射）→定向核实轮
（escalated真对侧盲核）→合并→重发布（daily全量）→写result token。

由自动化在批跑全部终态后调用；幂等——重跑仅覆盖同名工件并重放发布。

映射合并策略（后一代覆盖前一代completed）：
  primary: MTPLX代(batch.primary) ⊆ p2 ⊆ p4
  verifier: MTPLX代(batch.verifier) ⊆ r3

用法：
  python3 scripts/dualvlm_finalize.py            # 全流程（裁决→核实→合并→发布）
  python3 scripts/dualvlm_finalize.py --dry-run  # 仅裁决并打印计数，不发布
"""
import json
import os
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH))

os.environ.setdefault(
    "WORKBENCH_RUNTIME_DIR",
    str(
        WORKBENCH
        / "runs"
        / "phase_c_mgk10_authority_v2_20260905"
        / "runtime"
    ),
)

PROJECT_ID = "proj_mgk10_sar_real"
SNAPSHOT_REF = "facts-snapshot-001.dualvlm-full1"
FOCUSED_REF = "facts-snapshot-001.dualvlm-full1-fv"
BASE = f"http://127.0.0.1:8910/api/projects/{PROJECT_ID}/modules/medical-monitoring/r7"
WORKSPACE = (
    Path(os.environ["WORKBENCH_RUNTIME_DIR"])
    / "medical_monitoring_r7"
    / PROJECT_ID
)
BATCH_DIR = Path("/tmp")


def _load_json(name: str):
    try:
        return json.load(open(BATCH_DIR / name))
    except (OSError, ValueError):
        return None


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    sentinel = Path("/tmp/aemh_dualvlm_finalize_done.flag")
    if sentinel.exists() and not dry_run:
        print("finalize already done (sentinel present); skip")
        return
    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        adjudicate,
        merge_focused_verifications,
        submit_focused_verifications,
    )
    from packages.medical_monitoring.intelligence.primitives import content_hash
    from services.api.app import main

    ai_repository = main.monitoring_ai_repository
    primary_service = main.monitoring_ai_service
    verifier_service = main.monitoring_ai_verifier_service

    batch = _load_json("aemh_dualvlm_batch.json")
    if not batch:
        raise SystemExit("missing /tmp/aemh_dualvlm_batch.json")

    def ok(job_id: str) -> bool:
        try:
            return (
                ai_repository.get(PROJECT_ID, job_id).status == "completed"
            )
        except Exception:
            return False

    # ---- primary 映射：MTPLX ⊆ p2 ⊆ p4（后completed覆盖前） ----
    prim_map = {
        subj: jid
        for subj, jid in zip(batch["subjects"], batch["primary"])
        if ok(jid)
    }
    for override_name in (
        "aemh_dualvlm_batch_p2_primary.json",
        "aemh_dualvlm_batch_p4_primary.json",
    ):
        override = _load_json(override_name)
        if isinstance(override, dict):
            for subj, jid in override.items():
                if ok(jid):
                    prim_map[subj] = jid

    # ---- verifier 映射：MTPLX ⊆ r3 ----
    ver_map = {
        subj: jid
        for subj, jid in zip(batch["subjects"], batch["verifier"])
        if ok(jid)
    }
    r3map = _load_json("aemh_dualvlm_batch_r3_verifier.json")
    if isinstance(r3map, dict):
        for subj, jid in r3map.items():
            if ok(jid):
                ver_map[subj] = jid

    print(
        f"maps: primary={len(prim_map)} verifier={len(ver_map)} "
        f"subjects={len(batch['subjects'])}"
    )
    if not prim_map or not ver_map:
        raise SystemExit("empty cohort maps; abort")

    art = adjudicate(
        ai_repository=ai_repository,
        project_id=PROJECT_ID,
        subject_labels=batch["subjects"],
        facts_snapshot_ref=SNAPSHOT_REF,
        primary_job_by_subject=prim_map,
        verifier_job_by_subject=ver_map,
        artifacts_dir=WORKSPACE / "runtime" / "artifacts",
    )
    print("ADJUDICATE", art["counts"])
    if dry_run:
        return

    # ---- 定向核实轮：escalated条目按提出方发真对侧模型 ----
    escalated = [
        (i, f) for i, f in enumerate(art["findings"]) if f["state"] == "escalated"
    ]
    if escalated:
        domains = main._r7_facts_publication_provider._load_domains()
        job_ids = submit_focused_verifications(
            verifier_service=verifier_service,
            primary_service=primary_service,
            project_id=PROJECT_ID,
            domains=domains,
            escalated=[f for _, f in escalated],
            facts_snapshot_ref=FOCUSED_REF,
        )
        fv_map = {idx: jid for (idx, _), jid in zip(escalated, job_ids)}
        json.dump(fv_map, open("/tmp/aemh_fv_jobs.json", "w"))
        print("FOCUSED submitted:", len(job_ids))
        # 等待聚焦核实轮终态（最多120分钟）
        deadline = time.time() + 120 * 60
        while time.time() < deadline:
            time.sleep(120)
            active = 0
            for jid in fv_map.values():
                try:
                    if (
                        ai_repository.get(PROJECT_ID, jid).status
                        in ("queued", "running")
                    ):
                        active += 1
                except Exception:
                    pass
            print(f"fv active={active}", flush=True)
            if not active:
                break

    # ---- 合并定向核实结果并写工件 ----
    fv_map = _load_json("aemh_fv_jobs.json") or {}
    merged = merge_focused_verifications(
        ai_repository=ai_repository,
        project_id=PROJECT_ID,
        findings=art["findings"],
        focused_job_by_index={int(k): v for k, v in fv_map.items()},
    )
    counts = Counter(f["state"] for f in merged)
    art["findings"] = merged
    art["counts"] = dict(counts)
    art.pop("content_sha256", None)
    art["content_sha256"] = content_hash(art)
    artifact = (
        WORKSPACE
        / "runtime"
        / "artifacts"
        / f"aemh-findings-{SNAPSHOT_REF}.json"
    )
    artifact.write_text(
        json.dumps(art, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    print("MERGED", dict(counts))

    # ---- 重发布（daily全量） ----
    with urllib.request.urlopen(f"{BASE}/run-setup/options", timeout=120) as r:
        snapshot_token = json.loads(r.read())["current_data"]["snapshot_token"]
    body = json.dumps(
        {
            "mode": "daily",
            "execution_basis": "full",
            "current_snapshot_token": snapshot_token,
            "risk_rule_tokens": [],
            "idempotency_key": "dualvlm-full1-publish",
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/runs/prepare-and-start",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        run_token = json.loads(r.read())["public_run_token"]
    print("RUN", run_token)
    time.sleep(8)
    req = urllib.request.Request(
        f"{BASE}/runs/{run_token}/publication",
        data=json.dumps({"idempotency_key": "dualvlm-full1-pub"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        pub = json.loads(r.read())
    print("PUB", pub.get("publication_state"))
    with urllib.request.urlopen(
        f"{BASE}/runs/{run_token}/result-entry", timeout=120
    ) as r:
        entry = json.loads(r.read())
    Path("/tmp/result_token.txt").write_text(entry["result_context_token"])
    sentinel.write_text(entry["result_context_token"])
    print("TOKEN", entry["result_context_token"])


if __name__ == "__main__":
    main()
