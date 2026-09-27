"""SAR重跑·阶段4(run_start)：prepare-and-start启动SAR运行（幂等）。

模式（CSU w04/dualvlm_finalize._publish 实测沿用）：
  1. GET  r7/run-setup/options → current_snapshot_token（已核验事实快照）
     + modes可用性 + rule_revisions
  2. POST r7/runs/prepare-and-start
     {mode, execution_basis, current_snapshot_token, risk_rule_tokens,
      idempotency_key} → public_run_token（幂等键一次性持久化，重跑安全）
  3. 启动后读 r7_launch_registry（运行快照）+ MM_DB run_manifests/work_units
     → 工作单元规模。

快照口径：current_snapshot_token由API返回（阶段0/阶段4双次实测一致），
scope=已核验事实快照62表/148788行/3950919值100%往返校验——独立于映射lane
（映射lane的candidates/draft/facts是并行轨道，见阶段3）。

台账：运行启动（时间+规模+token）。
退出码：0=已启动；2=前置/启动失败。
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
R = WORKBENCH_ROOT / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
PROJECT = "proj_mgk10_sar_real"

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "stage4_evidence.jsonl"
STATE = HERE / "stage4_state.json"
LEDGER = HERE / "run_ledger.jsonl"
LAUNCH_DB = R / "medical_monitoring_r7" / PROJECT / "launch_registry.sqlite3"

BASE = f"http://127.0.0.1:8910/api/projects/{PROJECT}/modules/medical-monitoring/r7"
OPTIONS_URL = f"{BASE}/run-setup/options"
START_URL = f"{BASE}/runs/prepare-and-start"

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")
FAILURES: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _evidence_fh.write(
        json.dumps(
            {"ts": _now(), "stage": "run_start", "step": step, "ok": bool(ok),
             **detail}, ensure_ascii=False) + "\n")
    _evidence_fh.flush()


def _assert(step: str, label: str, ok: bool, detail: object) -> None:
    _ev(step, ok, assertion=label, detail=detail)
    if not ok:
        FAILURES.append(f"{step}:{label}={detail!r}")


def _http(step: str, method: str, url: str, *, payload=None, timeout=300):
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", "Bearer local")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _ev(step, False, kind="http", url=url, error=str(exc)[:250])
        FAILURES.append(f"{step}:http_error={exc}")
        return 0, {}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        parsed = json.loads(raw.decode())
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:1500]}
    _ev(step, True, kind="http", request={"method": method, "url": url},
        http_status=status, elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:2600])
    return status, parsed


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prior = {}
    if STATE.is_file():
        try:
            prior = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            prior = {}

    # ── 1. run-setup/options：读快照token与模式（SAR项目状态） ──────
    status, options = _http("run_setup_options", "GET", OPTIONS_URL)
    _assert("run_setup_options", "http_ok", status == 200, status)
    cur = options.get("current_data") or {}
    snapshot_token = cur.get("snapshot_token")
    modes = {m.get("mode"): m for m in options.get("modes", [])}
    daily = modes.get("daily") or {}
    full_available = any(
        o.get("value") == "full" and o.get("available")
        for o in daily.get("execution_basis_options", [])
    )
    _assert("run_setup_options", "snapshot_token_present", bool(snapshot_token),
            snapshot_token)
    _assert("run_setup_options", "daily_full_available", full_available,
            daily.get("execution_basis_options"))
    _assert(
        "run_setup_options",
        "snapshot_matches_verified_62_tables",
        "62表" in str(cur.get("scope_description", "")),
        cur.get("scope_description"),
    )
    if FAILURES:
        _ev("stage_failed", False, failures=FAILURES)
        print(json.dumps({"ok": False, "failures": FAILURES}, ensure_ascii=False))
        return 2

    # ── 2. prepare-and-start（幂等：服务端按idempotency_key去重） ────
    idem = prior.get("idempotency_key") or f"sar-rerun-stage4-{stamp}"
    start_payload = {
        "mode": "daily",
        "execution_basis": "full",
        "current_snapshot_token": snapshot_token,
        "risk_rule_tokens": [],
        "idempotency_key": idem,
    }
    status, body = _http("prepare_and_start", "POST", START_URL,
                         payload=start_payload, timeout=600)
    _assert("prepare_and_start", "http_ok", status in (200, 201, 202), status)
    if status not in (200, 201, 202):
        code = body.get("code") if isinstance(body.get("code"), str) else None
        _ev("stage_failed", False, failures=FAILURES, code=code,
            detail=str(body)[:600])
        print(json.dumps({"ok": False, "code": code,
                          "failures": FAILURES}, ensure_ascii=False))
        return 2
    run_token = body.get("public_run_token")
    run_id = body.get("run_id")
    _assert("prepare_and_start", "run_token_present", bool(run_token),
            {"public_run_token": run_token, "run_id": run_id,
             "response_keys": sorted(body.keys())})
    _ledger({
        "ts_utc": _now(), "stage": "run_start.prepare_and_start",
        "project": PROJECT, "run_token": run_token, "run_id": run_id,
        "paid": True,
        "scale": {
            "snapshot_token": snapshot_token,
            "snapshot_scope": cur.get("scope_description"),
            "mode": "daily", "execution_basis": "full",
            "risk_rule_tokens": [],
        },
        "note": "prepare-and-start启动SAR重跑运行（常设授权条款登记：时间+规模）",
    })

    # ── 3. 启动后：registry快照 + 工作单元规模 ────────────────────────
    conn = sqlite3.connect(f"file:{LAUNCH_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reg = conn.execute(
        "SELECT run_id, public_run_token, mode, execution_basis, "
        "current_snapshot_token, run_state, result_available, manifest_digest "
        "FROM r7_launch_registry WHERE run_id=? OR public_run_token=? "
        "ORDER BY sequence DESC LIMIT 1",
        (run_id or "!", run_token or "!"),
    ).fetchone()
    conn.close()
    registry_row = dict(reg) if reg else None
    _ev("registry_row", registry_row is not None, registry=registry_row)

    mm = R / "medical_monitoring_r7" / PROJECT / "runtime" / "monitoring_runtime.sqlite3"
    work_units = {}
    if run_id:
        mconn = sqlite3.connect(f"file:{mm}?mode=ro", uri=True)
        mconn.row_factory = sqlite3.Row
        try:
            work_units["manifests"] = mconn.execute(
                "SELECT COUNT(*) FROM run_manifests WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            work_units["node_runs"] = mconn.execute(
                "SELECT COUNT(*) FROM node_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            work_units["work_unit_runs"] = mconn.execute(
                "SELECT COUNT(*) FROM work_unit_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            work_units["nodes"] = mconn.execute(
                "SELECT COUNT(*) FROM node_attempts WHERE run_id=?", (run_id,)
            ).fetchone()[0]
        except sqlite3.Error as exc:
            work_units["error"] = str(exc)[:160]
        mconn.close()

    STATE.write_text(json.dumps(
        {"idempotency_key": idem, "run_token": run_token, "run_id": run_id,
         "snapshot_token": snapshot_token, "registry": registry_row,
         "work_units": work_units, "updated_at": _now()},
        ensure_ascii=False, indent=1), encoding="utf-8")

    scale = {"snapshot": cur.get("scope_description"),
             "work_units": work_units,
             "manifest_digest": (registry_row or {}).get("manifest_digest")}
    _ev("stage_done", not FAILURES, run_token=run_token, scale=scale,
        failures=FAILURES)
    _evidence_fh.close()
    print(json.dumps({"ok": not FAILURES, "run_token": run_token,
                      "run_id": run_id, "scale": scale}, ensure_ascii=False))
    return 0 if not FAILURES else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["run_start"]:
        print("usage: sar_run_start.py [--stage run_start]")
        sys.exit(2)
    sys.exit(main())
