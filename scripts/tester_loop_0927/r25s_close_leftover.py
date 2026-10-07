"""R25 攻坚：闭环 R24 遗留的 completed+未发布诊断运行（seq 19 diag-r18-03-gate-check-002）。

复现结论（r25s_siege_evidence.jsonl 第一遍）：全新幂等键 prepare-and-start
被 409 in_flight_conflict 拒绝，而同刻 mapping/facts/project/open 全绿——
两侧口径差的落点在 launch_registry_core_mixin.py:326-340
_find_in_flight_locked：`(run_state='completed' AND result_available=0)`
也算 in-flight（5f1a071a 既有产品语义：单运行窗口含结果发布收口）。
registry seq 19（R24 轮次角色 API 驱动的 R18-03 门禁核查诊断运行）停在
completed+result_available=0、publication_state=not_started——它没有走完
设计收口（界面轮询到 completed+not_started 会自动 publishResult，
MedicalMonitoringProductLoop.jsx:1060-1065；该诊断为 API 驱动，止步于发布前）。

最小根因处置：用与界面完全相同的设计端点（POST /runs/{token}/publication，
publication_routes.py:122，READ_AI_RUN 权限、按指纹幂等）把该遗留运行收口，
不跳任何门、不改注册表状态位。收口后 result_available=1，in-flight 消除，
新幂等键应可正常启动——由 r25s_siege_repro.py 全链重验。

用法：python3 r25s_close_leftover.py
证据：追加写入 r25s_siege_evidence.jsonl。
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8911"
PID = "proj_user_6ef58ac151e1"
RUN_TOKEN = "run:4d16d078ea9ae0d29ae898ae"  # registry seq 19
IDEM = "r25s-closure-diag-r18-03-002"
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "r25s_siege_evidence.jsonl"

MM = f"{BASE}/api/projects/{PID}/modules/medical-monitoring/r7"
WS = (
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台"
    "/implementation/workbench/runs/tester_loop_iso_20260928/runtime"
    "/medical_monitoring_r7"
)

s = requests.Session()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **kv) -> None:
    rec = {"ts": _now(), "step": step, "ok": bool(ok)}
    rec.update(kv)
    with EVIDENCE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  [{step}] ok={ok} " + " ".join(
        f"{k}={str(v)[:140]}" for k, v in list(kv.items())[:4]), flush=True)


def _http(step: str, method: str, url: str, *, json_body=None, timeout=300):
    t0 = time.monotonic()
    resp = s.request(method, url, json=json_body, timeout=timeout)
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    try:
        parsed = resp.json()
    except Exception:  # noqa: BLE001
        parsed = {"_raw": resp.text[:1500]}
    _ev(step, 200 <= resp.status_code < 300, kind="http",
        request={"method": method, "url": url},
        http_status=resp.status_code, elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:2500])
    return resp.status_code, parsed, elapsed_ms


def _disk_rows() -> list[dict]:
    conn = sqlite3.connect(f"file:{WS}/{PID}/launch_registry.sqlite3?mode=ro",
                           uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT sequence, run_state, result_available, idempotency_key "
        "FROM r7_launch_registry WHERE sequence>=19 ORDER BY sequence")]
    conn.close()
    return rows


def main() -> int:
    print(f"=== R25 close leftover @ {_now()}", flush=True)

    # 0) 收口前双侧快照：API 发布态 + 磁盘 registry 行
    gs, pub0, _ = _http("c0_publication_before", "GET",
                        f"{MM}/runs/{RUN_TOKEN}/publication")
    rows = _disk_rows()
    _ev("c0_disk_before", True, seq19_plus=rows)

    # 1) 设计收口：POST publication（与界面 publishResult 同端点同语义）
    ps, pub, ps_ms = _http("c1_publication_post", "POST",
                           f"{MM}/runs/{RUN_TOKEN}/publication",
                           json_body={"idempotency_key": IDEM})
    pub_state = str((pub or {}).get("publication_state") or "")
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline and pub_state != "available":
        time.sleep(10)
        _, pub2, _ = _http("c1_publication_get", "GET",
                           f"{MM}/runs/{RUN_TOKEN}/publication")
        pub_state = str((pub2 or {}).get("publication_state") or "")
    _ev("c1_publication_state", pub_state == "available",
        publication_state=pub_state, post_ms=ps_ms, idempotency_key=IDEM)

    # 2) 磁盘复核：result_available 应=1
    rows = _disk_rows()
    _ev("c2_disk_after", rows and rows[0]["result_available"] == 1,
        seq19_plus=rows)

    # 3) 闭环结果可读性留证（该遗留运行自身的结果也要可读）
    es, entry, _ = _http("c3_result_entry", "GET",
                         f"{MM}/runs/{RUN_TOKEN}/result-entry")
    rct = str((entry or {}).get("result_context_token") or "")
    ov_ok, ov_bytes = False, 0
    if rct:
        ovs, overview, _ = _http("c3_result_overview", "GET",
                                 f"{MM}/results/{rct}/overview")
        ov_bytes = len(json.dumps(overview or {}).encode("utf-8"))
        ov_ok = ovs == 200 and ov_bytes > 1000
        _ev("c3_overview_read", ov_ok, overview_bytes=ov_bytes, rct=rct)

    ok = pub_state == "available" and rows and rows[0]["result_available"] == 1 and ov_ok
    print(f"\n=== 闭环结论: ok={ok} pub={pub_state} "
          f"result_available={rows[0]['result_available'] if rows else '?'} "
          f"overview_bytes={ov_bytes}", flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
