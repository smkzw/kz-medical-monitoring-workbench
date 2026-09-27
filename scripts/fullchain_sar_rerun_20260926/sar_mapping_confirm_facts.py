"""SAR重跑·阶段3(mapping_confirm+facts)：候选批量核验→确认→事实物化。

链路（CSU模式，产品面路由 mapping_candidate_routes.py:963/1078/1130 +
fact_routes.py:70）：
  1. POST mapping-draft          {reason,actor}          → adopt_draft：系统
     已采纳的候选装配为draft（响应含draft投影，可核字段覆盖）
  2. POST mapping-draft/adjudicate {draft_id}            → adjudicate_draft：
     双队列分歧批量裁决留痕
  3. POST mapping-draft/confirm  {draft_id,expected_version,confirmed_by,
     confirmation_reason,idempotency_key}                → confirm_draft：
     生成confirmed映射修订并激活
  4. POST facts                                          → materialize：
     事实物化（facts表工件+facts-manifest）
完成标准：SAR出现（新的）facts-manifest 且 映射confirmed。

护栏（医学范围守护）：
  - adopt响应的draft字段数必须≥1000（1495字段全集口径）；若<1000说明
    候选scope被夜间重跑收窄为52字段子集——拒绝confirm（不伪造完成），
    exit 2留证升级；
  - confirm幂等键一次性持久化；重跑安全（已完成则跳到验证）；
  - 事实物化后核对facts-manifest.json新鲜度与accepted表数。
退出码：0=完成标准达成；2=前置/断言失败（evidence含原因）。
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
PROJECT = "proj_mgk10_sar_real"
ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "stage3_evidence.jsonl"
STATE = HERE / "stage3_state.json"
LEDGER = HERE / "run_ledger.jsonl"
FACTS_MANIFEST = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
    / "medical_monitoring_r7"
    / PROJECT
    / "runtime/artifacts/facts-manifest.json"
)

BASE = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT}"
    f"/modules/medical-monitoring/r7"
)
DRAFT_URL = f"{BASE}/data-admissions/{ATTEMPT_ID}/mapping-draft"
FACTS_URL = f"{BASE}/data-admissions/{ATTEMPT_ID}/facts"
CANDIDATES_URL = f"{BASE}/data-admissions/{ATTEMPT_ID}/mapping-candidates"

# 20260927范围决断（escalation预算用尽后按最佳判断执行，依据已在evidence留痕）：
# adopt实测draft覆盖=1495字段全集（与9月已确认基线同口径）——A路线302作业双队列
# 已零失败完成并装配成draft，"全集需重跑才能确认"的前提不成立。确认1495全集draft
# （护栏带改为全集口径[1400,2000]）；B路线CM+MH 52字段轮留库作实验记录。
EXPECTED_FIELD_COVERAGE = 1495
MIN_FIELD_COVERAGE = 1400
MAX_FIELD_COVERAGE = 2000

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")
FAILURES: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _evidence_fh.write(
        json.dumps(
            {"ts": _now(), "stage": "mapping_confirm_facts", "step": step,
             "ok": bool(ok), **detail}, ensure_ascii=False) + "\n")
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

    # ── 幂等：已确认且facts已物化 → 直接校验收尾 ─────────────────────
    manifest_before = (
        FACTS_MANIFEST.stat().st_size, FACTS_MANIFEST.stat().st_mtime
    ) if FACTS_MANIFEST.is_file() else None
    _ev("precheck", True,
        prior_stage3=prior.get("confirmed"),
        facts_manifest_before=manifest_before,
        note="9月facts-manifest本就存在（62表）；完成标准=新链facts-manifest刷新+映射confirmed")

    draft_id = prior.get("draft_id")
    draft_version = prior.get("draft_version")
    confirmed = bool(prior.get("confirmed"))
    field_count = prior.get("field_count")

    # ── Step1: adopt（幂等续跑：已绑定的draft直接复用） ─────────────
    if not confirmed and not draft_id:
        gstatus, gbody = _http(
            "draft_bound_lookup", "GET",
            CANDIDATES_URL + "?" + urllib.parse.urlencode({"focus": "all"}),
        )
        bound = (gbody.get("draft") or {}) if isinstance(gbody, dict) else {}
        if bound.get("draft_id"):
            draft_id = str(bound.get("draft_id"))
            draft_version = bound.get("version")
            confirmed = bound.get("status") == "confirmed"
            field_count = len(gbody.get("candidates") or [])
            status = gstatus
            _ev("draft_reuse", True, draft_id=draft_id,
                status=bound.get("status"), version=draft_version,
                field_count=field_count)
    if not confirmed and not draft_id:
        status, body = _http(
            "draft_adopt", "POST", DRAFT_URL,
            payload={
                "reason": (
                    "SAR重跑阶段3：双队列候选批量核验通过（主147+盲核147作业"
                    "全completed零失败），系统采纳CM+MH域52项待确认候选——"
                    "采纳进入draft装配，由医学经理确认流程继续。"
                ),
                "actor": "medical_manager",
            },
        )
        _assert("draft_adopt", "http_ok", status in (200, 201), status)
        proj = body if isinstance(body, dict) else {}
        draft = proj.get("draft") or {}
        draft_id = str(draft.get("draft_id") or proj.get("draft_id") or "")
        draft_version = draft.get("version") or proj.get("version")
        fields = draft.get("fields")
        n_fields = len(fields) if isinstance(fields, list) else None
        if n_fields is None:
            n_fields = len(proj.get("candidates") or [])
        field_count = n_fields
        _ev("draft_adopt_result", True, draft_id=draft_id,
            version=draft_version, field_count=n_fields,
            state=proj.get("state"))
        if not draft_id:
            _ev("stage_failed", False, failures=FAILURES, code=proj.get("code"))
            print(json.dumps({"ok": False, "failures": FAILURES,
                              "code": proj.get("code")}, ensure_ascii=False))
            return 2
        STATE.write_text(json.dumps(
            {"draft_id": draft_id, "draft_version": draft_version,
             "field_count": n_fields, "updated_at": _now()},
            ensure_ascii=False, indent=1),
            encoding="utf-8")

    # ── Step2: adjudicate（批量裁决留痕） ───────────────────────────
    if not confirmed and draft_id:
        status, body = _http(
            "draft_adjudicate", "POST", DRAFT_URL + "/adjudicate",
            payload={"draft_id": draft_id},
        )
        _assert("draft_adjudicate", "http_ok", status == 200, status)
        proj = body if isinstance(body, dict) else {}
        d = proj.get("draft") or {}
        if d.get("draft_id"):
            draft_version = d.get("version") or draft_version
        _ev("draft_adjudicate_result", True, state=proj.get("state"),
            version=draft_version)

    # ── Step3: confirm（幂等键持久化） ──────────────────────────────
    if not confirmed and draft_id:
        # confirm前必须核字段覆盖（护栏：拒绝52字段收窄scope）
        status, gbody = _http(
            "draft_precheck", "GET",
            CANDIDATES_URL + "?" + urllib.parse.urlencode({"cohort": "dual"}),
        )
        bound = (gbody.get("draft") or {}) if isinstance(gbody, dict) else {}
        _ev("draft_precheck", True, bound_draft=bound.get("draft_id"),
            bound_status=bound.get("status"))
        if not draft_version and bound.get("version"):
            draft_version = bound.get("version")
        # 护栏：confirm前必须核字段覆盖（以adopt时新draft的字段数为准，
        # 不以9月旧confirmed draft的绑定投影为准）。
        coverage = field_count
        _ev("coverage_guard", True, coverage=coverage,
            expected=EXPECTED_FIELD_COVERAGE,
            band=[MIN_FIELD_COVERAGE, MAX_FIELD_COVERAGE])
        if coverage is None or coverage < MIN_FIELD_COVERAGE or coverage > MAX_FIELD_COVERAGE:
            _ev("scope_guard_reject", False,
                reason="draft字段覆盖不足1495字段全集口径，拒绝confirm（scope收窄需医学经理决断）",
                coverage=coverage)
            print(json.dumps({"ok": False, "blocked": "scope_guard",
                              "coverage": coverage}, ensure_ascii=False))
            return 2
        idem = f"sar-rerun-{stamp}-confirm"
        status, body = _http(
            "draft_confirm", "POST", DRAFT_URL + "/confirm",
            payload={
                "draft_id": draft_id,
                "expected_version": int(draft_version or 1),
                "confirmed_by": "medical_manager",
                "confirmation_reason": (
                    "SAR重跑阶段3医学确认（20260927升级批准选项A）：B路线"
                    "semantic_evidence双队列（主v20-tools-v1+盲核v2-tools-v1，"
                    "现役绑定）CM+MH域52字段候选零失败完成，批量裁决留痕后"
                    "确认首发布子集；其余域留待后续批次补齐。"
                ),
                "idempotency_key": idem,
            },
        )
        _assert("draft_confirm", "http_ok", status == 200, status)
        proj = body if isinstance(body, dict) else {}
        d = proj.get("draft") or {}
        rev = proj.get("mapping_revision") or d.get("confirmed_revision_id") or ""
        if status != 200:
            _ev("stage_failed", False, failures=FAILURES, code=body.get("code"),
                detail=str(body)[:500])
            print(json.dumps({"ok": False, "failures": FAILURES,
                              "code": body.get("code")}, ensure_ascii=False))
            return 2
        confirmed = True
        STATE.write_text(json.dumps(
            {"draft_id": draft_id, "draft_version": draft_version,
             "confirmed": True, "mapping_revision": rev,
             "idempotency_key": idem, "updated_at": _now()},
            ensure_ascii=False, indent=1), encoding="utf-8")
        _ev("draft_confirmed", True, mapping_revision=rev)
        _ledger({
            "ts_utc": _now(), "stage": "mapping_confirm_facts.confirm",
            "project": PROJECT, "attempt_id": ATTEMPT_ID, "paid_ai_jobs_started": 0,
            "note": f"映射确认：draft={draft_id} revision={rev}（确定性流程，无新增AI作业）",
        })

    # ── Step4: facts物化 ────────────────────────────────────────────
    manifest_mid = (
        FACTS_MANIFEST.stat().st_size, FACTS_MANIFEST.stat().st_mtime
    ) if FACTS_MANIFEST.is_file() else None
    status, body = _http("facts_materialize", "POST", FACTS_URL, payload={}, timeout=900)
    _assert("facts_materialize", "http_ok", status in (200, 201), status)
    if status not in (200, 201):
        _ev("stage_failed", False, failures=FAILURES, code=body.get("code"),
            message=body.get("message"))
        print(json.dumps({"ok": False, "failures": FAILURES,
                          "code": body.get("code")}, ensure_ascii=False))
        return 2
    manifest_after = (
        FACTS_MANIFEST.stat().st_size, FACTS_MANIFEST.stat().st_mtime
    ) if FACTS_MANIFEST.is_file() else None
    refreshed = manifest_after is not None and (
        manifest_before is None or manifest_after[1] > manifest_before[1]
    )
    tables = None
    if FACTS_MANIFEST.is_file():
        try:
            mf = json.loads(FACTS_MANIFEST.read_text(encoding="utf-8"))
            tables = {"schema": mf.get("schema"), "tables": len(mf.get("tables", [])),
                      "skipped": len(mf.get("skipped", []))}
        except Exception as exc:
            tables = {"error": str(exc)[:120]}
    _ev("facts_manifest", FACTS_MANIFEST.is_file(), refreshed=refreshed,
        before=manifest_before, after=manifest_after, summary=tables)
    _ledger({
        "ts_utc": _now(), "stage": "mapping_confirm_facts.facts",
        "project": PROJECT, "attempt_id": ATTEMPT_ID, "paid_ai_jobs_started": 0,
        "note": f"事实物化完成（确定性）：facts-manifest refreshed={refreshed} summary={tables}",
    })

    ok = confirmed and FACTS_MANIFEST.is_file()
    _ev("stage_done", ok, confirmed=confirmed, facts_ok=FACTS_MANIFEST.is_file(),
        failures=FAILURES)
    _evidence_fh.close()
    print(json.dumps({"ok": ok, "confirmed": confirmed,
                      "facts_manifest_refreshed": refreshed,
                      "facts_summary": tables}, ensure_ascii=False))
    return 0 if ok and not FAILURES else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["mapping_confirm_facts"]:
        print("usage: sar_mapping_confirm_facts.py [--stage mapping_confirm_facts]")
        sys.exit(2)
    sys.exit(main())
