"""R5D 预置·复核收敛驱动：轮询作业队列→驱动adjudicate→confirm→facts。

设计逻辑（与界面用户手势一致）：
  - 轮询 AI 作业队列直到全部终态（queued/running 清零）；
  - POST mapping-draft/adjudicate 推进复核（系统自动恢复失败分片、
    bounded-gap 转换可见缺口、必要时提交新一轮双队列——全部系统设计行为）；
  - adjudication state=complete 时 POST confirm；confirm 200 后 POST facts；
  - 任何一步不可推进（连续N轮无进展）则如实退出并留痕，不伪造状态。

退出码：0=confirmed+facts 完成；10=预算耗尽仍在推进；2=阻断（留痕原因）。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8911"
PROJECT = "proj_user_9ce08d6a722d"
ATTEMPT = "stg-68d7a08f01b3472196931402184b53c4"
DRAFT = "monmapdraft_0173cdeeed8a9196d4bfc37edd6e"

MM = f"{BASE}/api/projects/{PROJECT}/modules/medical-monitoring/r7"
ATT = f"{MM}/data-admissions/{ATTEMPT}"
AI = f"{BASE}/api/projects/{PROJECT}/modules/medical-monitoring/ai"

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "r5d_seed_evidence.jsonl"

TOTAL_BUDGET_S = 9000.0   # 2.5h 总预算
POLL_INTERVAL_S = 60.0
NO_PROGRESS_ROUNDS = 6    # 连续6轮无进展（无作业消耗且remaining不变）→退出


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    with EVIDENCE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": _now(), "run": "r5d_seed", "step": step, "ok": bool(ok), **detail,
        }, ensure_ascii=False) + "\n")


def _http(step: str, method: str, url: str, payload=None, timeout=600):
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except Exception as exc:  # noqa: BLE001
        _ev(step, False, error=f"{type(exc).__name__}: {exc}"[:300])
        return 0, {}
    try:
        parsed = json.loads(raw.decode())
    except Exception:  # noqa: BLE001
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:1200]}
    _ev(step, status in (200, 201), kind="http",
        request={"method": method, "url": url},
        http_status=status, elapsed_ms=int((time.monotonic() - started) * 1000),
        response=json.dumps(parsed, ensure_ascii=False)[:1200])
    return status, parsed


def _job_counts() -> tuple[dict, int]:
    status, body = _http("queue_jobs_read", "GET", f"{AI}/jobs?limit=200")
    jobs = (body or {}).get("items") or []
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    return counts, len(jobs)


def _adjudicate() -> dict:
    status, body = _http("adjudicate_drive", "POST",
                         f"{ATT}/mapping-draft/adjudicate",
                         payload={"draft_id": DRAFT})
    adj = (body or {}).get("adjudication") or {}
    rs = (body or {}).get("review_summary") or {}
    return {"adj_state": adj.get("state"),
            "remaining": adj.get("remaining_question_count"),
            "system_adjudicated": rs.get("system_adjudicated_count"),
            "http": status}


def main() -> int:
    t0 = time.monotonic()
    last_remaining = None
    no_progress = 0
    confirmed = False

    while time.monotonic() - t0 < TOTAL_BUDGET_S:
        counts, total = _job_counts()
        inflight = counts.get("queued", 0) + counts.get("running", 0)
        print(f"[{time.monotonic()-t0:7.0f}s] jobs={counts} total={total} inflight={inflight}",
              flush=True)
        if inflight == 0:
            r = _adjudicate()
            print(f"    adjudicate -> {r}", flush=True)
            if r["adj_state"] == "complete":
                break
            if r["http"] == 0:
                time.sleep(30)
                continue
            # 进展判定：remaining下降 或 system_adjudicated上升 或 新作业入队
            sig = (r.get("remaining"), r.get("system_adjudicated"))
            if sig == last_remaining:
                no_progress += 1
            else:
                no_progress = 0
                last_remaining = sig
            c2, _ = _job_counts()
            if c2.get("queued", 0) + c2.get("running", 0) > 0:
                no_progress = 0  # 新一轮在跑=有进展
            if no_progress >= NO_PROGRESS_ROUNDS:
                _ev("converge_stalled", False, last=r, counts=counts)
                print("STALL: 连续多轮无进展，如实退出", flush=True)
                return 2
        time.sleep(POLL_INTERVAL_S)
    else:
        _ev("converge_budget_exhausted", False)
        print("BUDGET EXHAUSTED", flush=True)
        return 10

    # ── confirm ─────────────────────────────────────────────────────
    _, gb = _http("pre_confirm_version", "GET", f"{ATT}/mapping-candidates?focus=all")
    version = int(((gb or {}).get("draft") or {}).get("version") or 1)
    for attempt in range(5):
        status, body = _http("draft_confirm_final", "POST",
                             f"{ATT}/mapping-draft/confirm",
                             payload={
                                 "draft_id": DRAFT,
                                 "expected_version": version,
                                 "confirmation_reason": (
                                     "R5D开考位预置：双队列映射候选经系统复核与批量"
                                     "裁决收敛（失败分片按bounded-gap设计转为可见缺"
                                     "口）后，确认字段对应关系进入事实物化。"
                                 ),
                                 "idempotency_key": f"r5d-final-confirm-{uuid.uuid4().hex[:12]}",
                                 "automatic": True,
                             })
        if status == 200:
            confirmed = True
            break
        code = (body or {}).get("code") or (body or {}).get("detail", {}).get("code")
        print(f"    confirm -> {status} {code}", flush=True)
        _ev("confirm_retry", False, status=status, code=code)
        _, gb = _http("pre_confirm_version", "GET", f"{ATT}/mapping-candidates?focus=all")
        version = int(((gb or {}).get("draft") or {}).get("version") or version)
        r = _adjudicate()  # 再推一轮复核再试
        time.sleep(10)
    if not confirmed:
        print("CONFIRM BLOCKED", flush=True)
        return 2

    # ── facts ────────────────────────────────────────────────────────
    status, body = _http("facts_materialize_final", "POST", f"{ATT}/facts",
                         payload={}, )
    if status not in (200, 201):
        print(f"FACTS BLOCKED {status} {(body or {}).get('code')}", flush=True)
        return 2
    print("FACTS OK:", json.dumps(body, ensure_ascii=False)[:400], flush=True)
    _ev("seed_complete", True, facts=body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
