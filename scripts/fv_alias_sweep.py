#!/usr/bin/env python3
"""fv波路由别名失败自动清扫：仅重试response_model_identity类失败，
单轮语义（既有惯例），12轮×10分钟封顶，全部终态即提前退出。"""
import sqlite3
import sys
import time
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH))
import os
os.environ.setdefault("WORKBENCH_RUNTIME_DIR", str(WORKBENCH / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"))
DB = Path(os.environ["WORKBENCH_RUNTIME_DIR"]) / "medical_monitoring_ai.sqlite3"

from services.api.app.monitoring_ai_repository import MonitoringAiRepository  # noqa: E402

repo = MonitoringAiRepository(DB, lease_seconds=1800)

for round_no in range(1, 13):
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT job_id, failure_code FROM monitoring_ai_jobs "
        "WHERE business_key LIKE 'aemh:facts-snapshot-001.dualvlm-full1-fv%' "
        "AND status='failed'"
    ).fetchall()
    active = conn.execute(
        "SELECT COUNT(*) FROM monitoring_ai_jobs "
        "WHERE business_key LIKE 'aemh:facts-snapshot-001.dualvlm-full1-fv%' "
        "AND status IN ('queued','running')"
    ).fetchone()[0]
    conn.close()
    alias = [jid for jid, code in rows if code == "response_model_identity"]
    other = [(jid, code) for jid, code in rows if code != "response_model_identity"]
    print(f"round {round_no}: failed={len(rows)} (alias={len(alias)} other={len(other)}) active={active}", flush=True)
    for jid in alias:
        sub = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        rev = sub.execute("SELECT input_revision_sha256 FROM monitoring_ai_jobs WHERE job_id=?", (jid,)).fetchone()[0]
        sub.close()
        try:
            repo.retry_terminal("proj_mgk10_sar_real", jid, current_input_revision_sha256=rev)
        except Exception as exc:
            print(f"  retry skip {jid}: {exc}", flush=True)
    if not rows and active == 0:
        print("fv wave fully terminal; sweep exit", flush=True)
        break
    time.sleep(600)
