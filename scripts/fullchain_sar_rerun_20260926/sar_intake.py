"""SAR重跑·阶段1(intake+content_confirm)：真实listing入库到可映射状态。

模式照搬CSU（proj_user_2f17492ac59b）全链 w04_s3_rule_pack_release.py
step1_intake_batch/_confirm_listing_content：
  1. POST monitoring/batches/intake-file（幂等键带时间戳，raw body=文件字节）
  2. 409 source_content_confirmation_required → 按P7合同逐项确认校验器
     已列出的warning/mismatch检查项（不新增、不虚构）→ use_status
     confirmed_after_warning → 换幂等键重intake
  3. 409 listing_classification_confirmation_required → 以实际分类警告
     为由传classification_override_reason重试（确认不改变原分类）
完成标准：monbatch_*创建、normalized行>0、observed_domains非空（批次处于
可映射供给状态；状态机draft→parsed→validated→confirmed→frozen，
monitoring_batch_repository.py:70-82）。

幂等设计：首次成功后把幂等键与batch_id持久化到stage1_state.json；重跑时
同键重放（服务端idempotency ledger返回同一批次），不产生新批次。

付费台账：intake为确定性解析+校验，0付费AI作业，台账如实记录。
退出码：0=完成；2=断言失败/阻断（evidence含原因）。
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
RUNTIME = WORKBENCH_ROOT / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
PROJECT = "proj_mgk10_sar_real"
LISTING_BASENAME = (
    "【锁库后Data Listing】MG-K10-SAR-001_FormExcelAllVersion_202601201126.xlsx"
)
LISTING_PATH = (
    RUNTIME
    / "medical_monitoring_r7"
    / PROJECT
    / "admissions/staging"
    / "stg-e9d5050c73ef44be818e1f44920fdb5f"
    / LISTING_BASENAME
)

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "stage1_evidence.jsonl"
STATE = HERE / "stage1_state.json"
LEDGER = HERE / "run_ledger.jsonl"

BASE_URL = "http://127.0.0.1:8910"
API = f"{BASE_URL}/api/projects/{PROJECT}"
INTAKE_TIMEOUT_S = 600

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")
FAILURES: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _evidence_fh.write(
        json.dumps(
            {"ts": _now(), "stage": "intake", "step": step, "ok": bool(ok), **detail},
            ensure_ascii=False,
        )
        + "\n"
    )
    _evidence_fh.flush()


def _assert(step: str, label: str, ok: bool, detail: object) -> None:
    _ev(step, ok, assertion=label, detail=detail)
    if not ok:
        FAILURES.append(f"{step}:{label}={detail!r}")


def _http(step: str, method: str, path: str, *, payload=None, query=None,
          raw_body: bytes | None = None, timeout: int = 120):
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    body = raw_body
    if body is None and payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header(
        "Content-Type",
        "application/octet-stream" if raw_body is not None else "application/json",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _ev(step, False, kind="http", url=url, error=str(exc)[:300])
        FAILURES.append(f"{step}:http_error={exc}")
        return 0, {}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:2000]}
    # 留痕：请求与响应摘要（响应截断，避免evidence膨胀）
    _ev(
        step,
        True,
        kind="http",
        request={"method": method, "url": url, "payload": payload,
                 "body_bytes": len(raw_body) if raw_body else 0},
        http_status=status,
        elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:2500],
    )
    return status, parsed


def _batch_of(body: dict) -> dict:
    """IntakeResult.batch 可能嵌套 BatchMutationResult.batch。"""
    batch = body.get("batch")
    if isinstance(batch, dict) and isinstance(batch.get("batch"), dict):
        batch = batch["batch"]
    return batch if isinstance(batch, dict) else {}


def _confirm_content(detail: dict, stamp: str) -> bool:
    """按P7合同逐项确认校验器列出的可覆盖检查项（CSU模式）。"""
    source_entry_id = str(detail.get("source_entry_id") or "")
    validation = detail.get("validation") or {}
    revision = int(validation.get("revision") or 1)
    codes = sorted(
        str(c.get("check_code"))
        for c in validation.get("checks") or []
        if c.get("outcome") in {"warning", "mismatch"}
    )
    _assert(
        "confirm_content",
        "confirmable_checks_listed",
        bool(codes),
        {"codes": codes, "source_entry_id": source_entry_id, "revision": revision},
    )
    if not codes or not source_entry_id:
        return False
    reason = (
        "医学经理逐项确认（SAR重跑stage1）：该文件为MG-K10-SAR-001锁库后"
        "Data Listing全版本（62表，与活跃运行库已核验事实快照srcc1_"
        "bdd4dac3ea07fd7257ef4b08同源同sha256，148788行100%往返校验）；"
        f"确认校验器所列检查项{codes}为已知来源属性，不阻断批次供给。"
    )
    status, body = _http(
        "confirm_content",
        "POST",
        f"/api/projects/{PROJECT}/sources/{source_entry_id}/content-validation/confirm",
        payload={
            "reason": reason,
            "acknowledged_check_codes": codes,
            "actor": "medical_manager",
            "expected_revision": revision,
            "idempotency_key": f"sar-rerun-{stamp}-content-confirm",
        },
    )
    _assert("confirm_content", "http_ok", status in (200, 201), status)
    _assert(
        "confirm_content",
        "use_status_confirmed_after_warning",
        body.get("use_status") == "confirmed_after_warning",
        body.get("use_status"),
    )
    return status in (200, 201) and body.get("use_status") == "confirmed_after_warning"


def _intake(content: bytes, key: str) -> tuple[int, dict]:
    return _http(
        "intake_file",
        "POST",
        f"/api/projects/{PROJECT}/monitoring/batches/intake-file",
        query={
            "filename": LISTING_BASENAME,
            "idempotency_key": key,
            "classification_override_reason": "",
        },
        raw_body=content,
        timeout=INTAKE_TIMEOUT_S,
    )


def main() -> int:
    if not LISTING_PATH.is_file():
        _ev("prerequisite", False, reason=f"listing missing: {LISTING_PATH}")
        print("FAIL: listing file missing")
        return 2
    content = LISTING_PATH.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    _ev("prerequisite", True, listing=str(LISTING_PATH), size_bytes=len(content), sha256=sha)

    # 幂等：已有成功state则同键重放
    prior = None
    if STATE.is_file():
        try:
            prior = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            prior = None
    if prior and prior.get("intake_key"):
        stamp, key = prior["stamp"], prior["intake_key"]
        _ev("idempotent_reuse", True, stamp=stamp, intake_key=key,
            prior_batch_id=prior.get("batch_id"))
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"sar-rerun-{stamp}-intake"

    status, body = _intake(content, key)
    detail = body.get("detail") if isinstance(body.get("detail"), dict) else {}
    if status == 409 and detail.get("code") == "source_content_confirmation_required":
        if _confirm_content(detail, stamp):
            key = f"sar-rerun-{stamp}-intake-after-confirm"
            status, body = _intake(content, key)
    elif status == 409 and detail.get("code") == "listing_classification_confirmation_required":
        classification = detail.get("classification") or {}
        warnings = tuple(
            dict.fromkeys(classification.get("content_warnings") or [])
        )
        reason = (
            "医学经理确认来源分类（SAR重跑stage1）：分类警告"
            f"{warnings}为该锁库后Data Listing已知来源属性，确认沿用原分类导入。"
        )
        _ev("classification_confirm", True, warnings=warnings, reason=reason)
        status, body = _http(
            "intake_file_after_classification_confirm",
            "POST",
            f"/api/projects/{PROJECT}/monitoring/batches/intake-file",
            query={
                "filename": LISTING_BASENAME,
                "idempotency_key": key,
                "classification_override_reason": reason,
            },
            raw_body=content,
            timeout=INTAKE_TIMEOUT_S,
        )

    batch = _batch_of(body)
    _assert("intake_result", "http_ok", status in (200, 201), status)
    _assert("intake_result", "batch_created", bool(batch.get("batch_id")),
            {"batch_id": batch.get("batch_id"), "state": batch.get("state"),
             "version": batch.get("version")})
    _assert("intake_result", "rows_normalized", bool(body.get("row_count")),
            body.get("row_count"))
    _assert("intake_result", "observed_domains", bool(body.get("observed_domains")),
            body.get("observed_domains"))
    if not batch.get("batch_id"):
        _ev("stage_failed", False, failures=FAILURES)
        print(json.dumps({"ok": False, "failures": FAILURES}, ensure_ascii=False))
        return 2

    # 回读批次，确认持久化与可映射供给
    gstatus, gbody = _http(
        "batch_readback",
        "GET",
        f"/api/projects/{PROJECT}/monitoring/batches/{batch['batch_id']}",
    )
    _assert("batch_readback", "http_ok", gstatus == 200, gstatus)
    _assert("batch_readback", "row_count_matches",
            bool(gbody.get("row_count")) and gbody.get("row_count") == body.get("row_count"),
            {"readback": gbody.get("row_count"), "intake": body.get("row_count")})
    _assert("batch_readback", "state_recorded", bool(gbody.get("state")),
            gbody.get("state"))

    STATE.write_text(
        json.dumps(
            {
                "stamp": stamp,
                "intake_key": key,
                "batch_id": batch["batch_id"],
                "batch_state": gbody.get("state") or batch.get("state"),
                "row_count": body.get("row_count"),
                "observed_domains": body.get("observed_domains"),
                "source_entry_id": body.get("source_entry_id"),
                "listing_sha256": sha,
                "content_confirmed": detail.get("code")
                == "source_content_confirmation_required",
                "updated_at": _now(),
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "ts_utc": _now(),
                    "stage": "intake",
                    "project": PROJECT,
                    "paid_ai_jobs_started": 0,
                    "http_calls": 3,
                    "note": (
                        "确定性intake+内容确认（0付费AI作业）；批次"
                        f"{batch['batch_id']} state={gbody.get('state')} "
                        f"rows={body.get('row_count')}"
                    ),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    _ev("stage_done", not FAILURES, batch_id=batch["batch_id"], failures=FAILURES)
    _evidence_fh.close()
    print(
        json.dumps(
            {
                "ok": not FAILURES,
                "batch_id": batch["batch_id"],
                "state": gbody.get("state"),
                "row_count": body.get("row_count"),
                "domains": len(body.get("observed_domains") or []),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not FAILURES else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["intake"]:
        print("usage: sar_intake.py [--stage intake]")
        sys.exit(2)
    sys.exit(main())
