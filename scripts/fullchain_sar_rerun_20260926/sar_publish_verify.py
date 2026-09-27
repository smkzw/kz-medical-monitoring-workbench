"""SAR重跑·阶段5(publish+verify)：发布结果并做A24验收统计。

链路：
  1. POST r7/runs/{token}/publication  {idempotency_key:带时间戳}
     → 幂等；轮询GET直至publication_state=available（dualvlm模式）
  2. GET  r7/runs/{token}/result-entry → result_context_token与结果入口
  3. GET  r7/results/{result_context_token}/overview → A24验收统计
     （发现数量/载荷规模等），与9月历史数字分开如实记录。
退出码：0=发布available且验收数据已取；2=失败（evidence含原因）。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
PROJECT = "proj_mgk10_sar_real"

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "stage5_evidence.jsonl"
STATE = HERE / "stage5_state.json"
LEDGER = HERE / "run_ledger.jsonl"

BASE = f"http://127.0.0.1:8910/api/projects/{PROJECT}/modules/medical-monitoring/r7"
RUN_TOKEN = "run:e3da89b9c1cade4dd0ea4def"
PUB_URL = f"{BASE}/runs/{RUN_TOKEN}/publication"
ENTRY_URL = f"{BASE}/runs/{RUN_TOKEN}/result-entry"

PUB_POLL_BUDGET_S = 600.0
PUB_POLL_INTERVAL_S = 10.0

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")
FAILURES: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _evidence_fh.write(
        json.dumps(
            {"ts": _now(), "stage": "publish_verify", "step": step,
             "ok": bool(ok), **detail}, ensure_ascii=False) + "\n")
    _evidence_fh.flush()


def _ledger(entry: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


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

    # ── 1. 发布（幂等键带时间戳） ────────────────────────────────────
    status, body = _http(
        "publication_post", "POST", PUB_URL,
        payload={"idempotency_key": f"sar-rerun-stage5-pub-{stamp}"},
        timeout=600,
    )
    _assert("publication_post", "http_ok", status in (200, 201, 202), status)
    pub_state = str(body.get("publication_state") or "")
    if status not in (200, 201, 202):
        _ev("stage_failed", False, failures=FAILURES, code=body.get("code"),
            message=str(body.get("message"))[:200])
        print(json.dumps({"ok": False, "failures": FAILURES,
                          "code": body.get("code")}, ensure_ascii=False))
        return 2

    # ── 2. 轮询至available ──────────────────────────────────────────
    deadline = time.time() + PUB_POLL_BUDGET_S
    pub = body
    while pub_state not in {"available"} and time.time() < deadline:
        time.sleep(PUB_POLL_INTERVAL_S)
        gstatus, pub = _http("publication_get", "GET", PUB_URL)
        pub_state = str(pub.get("publication_state") or "")
        if pub_state == "available":
            break
        if pub_state in {"failed"}:
            _assert("publication_poll", "not_failed", False, pub)
            break
    _ev("publication_poll_done", True, publication_state=pub_state,
        failures=FAILURES)
    if pub_state != "available":
        print(json.dumps({"ok": False, "publication_state": pub_state,
                          "note": "发布未完成，重跑本阶段续轮询"}, ensure_ascii=False))
        return 2

    result_context_token = str(pub.get("result_context_token") or "")

    # ── 3. result-entry + overview（A24验收数据） ────────────────────
    entry_status, entry = _http("result_entry", "GET", ENTRY_URL)
    _assert("result_entry", "http_ok", entry_status == 200, entry_status)
    entry_summary = {}
    if isinstance(entry, dict):
        for k in ("result_context_token", "public_run_token", "headline",
                  "mode_text", "data_cutoff_text", "comparison_range_text",
                  "generated_at", "finding_count", "summary"):
            if k in entry:
                entry_summary[k] = entry[k]

    overview = None
    if result_context_token:
        ov_url = (f"{BASE}/results/{result_context_token}/overview")
        ov_status, overview = _http("result_overview", "GET", ov_url, timeout=300)
        _assert("result_overview", "http_ok", ov_status == 200, ov_status)

    STATE.write_text(json.dumps(
        {"run_token": RUN_TOKEN, "publication_state": "available",
         "result_context_token": result_context_token,
         "entry_summary": entry_summary, "updated_at": _now()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    _ledger({
        "ts_utc": _now(), "stage": "publish_verify.published",
        "project": PROJECT, "run_token": RUN_TOKEN,
        "result_context_token": result_context_token,
        "publication_state": "available",
        "idempotency_key": f"sar-rerun-stage5-pub-{stamp}",
        "note": "结果发布available（幂等键带时间戳）",
    })
    _ev("stage_done", not FAILURES, failures=FAILURES,
        result_context_token=result_context_token)
    _evidence_fh.close()
    print(json.dumps({"ok": not FAILURES,
                      "publication_state": "available",
                      "result_context_token": result_context_token,
                      "entry_summary": entry_summary,
                      "overview_keys": (list(overview.keys()) if isinstance(overview, dict) else None)},
                     ensure_ascii=False))
    return 0 if not FAILURES else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["publish_verify"]:
        print("usage: sar_publish_verify.py [--stage publish_verify]")
        sys.exit(2)
    sys.exit(main())
