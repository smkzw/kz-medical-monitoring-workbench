#!/usr/bin/env python3
"""双VLM全量批跑收尾：全量裁决（主+r3盲核+旧completed盲核合并映射）→
定向核实轮（escalated）→合并→重发布（daily全量）→写token。

由自动化在批跑全部终态后调用；幂等——重跑仅覆盖同名工件与重放发布。
"""
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RUNTIME = Path(__file__).resolve().parent / "runtime"
WORKSPACE = RUNTIME / "medical_monitoring_r7" / "proj_mgk10_sar_real"
BASE = "http://127.0.0.1:8910/api/projects/proj_mgk10_sar_real/modules/medical-monitoring/r7"


def main() -> None:
    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        adjudicate,
        merge_focused_verifications,
        submit_focused_verifications,
    )
    from packages.medical_monitoring.intelligence.primitives import content_hash
    from services.api.app import main

    batch = json.load(open("/tmp/aemh_dualvlm_batch.json"))
    r3map = json.load(open("/tmp/aemh_dualvlm_batch_r3_verifier.json"))

    db = sqlite3.connect(
        f"file:{RUNTIME / 'medical_monitoring_r7' / 'proj_mgk10_sar_real' / 'launch_registry.sqlite3' if False else WORKSPACE.parent}"
    )
    db.close()

    ai_repository = main.monitoring_ai_repository

    def ok(job_id: str) -> bool:
        try:
            return ai_repository.get("proj_mgk10_sar_real", job_id).status == "completed"
        except Exception:
            return False

    prim_map = {
        subj: jid
        for subj, jid in zip(batch["subjects"], batch["primary"])
        if ok(jid)
    }
    # p2主作业（glm-5.3-flash重发代）覆盖MTPLX代的completed
    try:
        p2map = json.load(open("/tmp/aemh_dualvlm_batch_p2_primary.json"))
        for subj, jid in p2map.items():
            if ok(jid):
                prim_map[subj] = jid
    except (OSError, ValueError):
        pass
    ver_map = {
        subj: jid
        for subj, jid in zip(batch["subjects"], batch["verifier"])
        if ok(jid)
    }
    # r3盲核覆盖旧completed（r3是最新命名空间）
    for subj, jid in r3map.items():
        if ok(jid):
            ver_map[subj] = jid

    art = adjudicate(
        ai_repository=ai_repository,
        project_id="proj_mgk10_sar_real",
        subject_labels=batch["subjects"],
        facts_snapshot_ref="facts-snapshot-001.dualvlm-full1",
        primary_job_by_subject=prim_map,
        verifier_job_by_subject=ver_map,
        artifacts_dir=WORKSPACE / "runtime" / "artifacts",
    )
    print("ADJUDICATE", art["counts"])

    # 定向核实轮：escalated条目发对侧模型聚焦核实
    escalated = [
        (i, f) for i, f in enumerate(art["findings"]) if f["state"] == "escalated"
    ]
    if escalated:
        domains = main._r7_facts_publication_provider._load_domains()
        sub = submit_focused_verifications(
            verifier_service=main.monitoring_ai_verifier_service,
            project_id="proj_mgk10_sar_real",
            domains=domains,
            escalated=[f for _, f in escalated],
            facts_snapshot_ref="facts-snapshot-001.dualvlm-full1-fv",
            protocol_workspace=WORKSPACE,
        )
        fv_map = {idx: jid for (idx, _), jid in zip(escalated, sub.verifier_job_ids)}
        json.dump(fv_map, open("/tmp/aemh_fv_jobs.json", "w"))
        print("FOCUSED submitted:", len(sub.verifier_job_ids))
        # 等待聚焦核实轮终态（最多90分钟）
        deadline = time.time() + 90 * 60
        while time.time() < deadline:
            time.sleep(120)
            states = {}
            for jid in fv_map.values():
                try:
                    states[ai_repository.get("proj_mgk10_sar_real", jid).status] = 0
                except Exception:
                    pass
            active = {
                s: 0
                for s in ("queued", "running")
                if any(
                    ai_repository.get("proj_mgk10_sar_real", j).status == s
                    for j in fv_map.values()
                )
            }
            print("fv states:", active or "terminal")
            if not active:
                break

    # 合并定向核实结果
    if escalated:
        fv_map = json.load(open("/tmp/aemh_fv_jobs.json"))
        merged = merge_focused_verifications(
            ai_repository=ai_repository,
            project_id="proj_mgk10_sar_real",
            findings=art["findings"],
            focused_job_by_index=fv_map,
        )
        from collections import Counter

        counts = Counter(f["state"] for f in merged)
        art["findings"] = merged
        art["counts"] = dict(counts)
        art.pop("content_sha256", None)
        art["content_sha256"] = content_hash(art)
        artifact = (
            WORKSPACE / "runtime" / "artifacts"
            / "aemh-findings-facts-snapshot-001.dualvlm-full1.json"
        )
        artifact.write_text(
            json.dumps(art, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        print("MERGED", dict(counts))

    # 重发布
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
    with urllib.request.urlopen(f"{BASE}/runs/{run_token}/result-entry", timeout=120) as r:
        entry = json.loads(r.read())
    Path("/tmp/result_token.txt").write_text(entry["result_context_token"])
    print("TOKEN", entry["result_context_token"])


if __name__ == "__main__":
    main()
