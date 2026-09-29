"""R5D 预置·映射问题卡片作答（设计内医学手势，经 PATCH mapping-draft/field）。

背景：confirm 门 422 mapping_questions_unresolved——EX/EXTRT 问题卡片待答；
semantic G-ROLE-002 全局阻断——MH/MHNUM 角色 record_number(source_metadata)
未入闭合目录，阻断指引为「选择目录角色或保持未映射」。

作答依据（合成数据实测，见 r5d_seed_evidence 与本脚本输出）：
  - DM.试验分组：试验组8/安慰剂组8；EX.给药药物128行全为'MG-K10 300mg
    Q4W'（含安慰剂组64行）→ 该列不区分IMP/安慰剂，实际治疗身份在
    DM.试验分组；EXTRT按中性给药角色保留来源值（G-CMIP-005指引：
    证据不足时来源值保留在中性给药角色下）。
  - MH.MHNUM 为病史记录号 → 闭合目录角色 metadata.record_id
    （别名 record.id / source.record.identifier）。
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

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "r5d_seed_evidence.jsonl"

EXTRT_ANSWER = (
    "用户已确认：经核对合成数据MG-K10-CSU-001_合成测试数据_V1.0.xlsx，"
    "EX域'给药药物'128行唯一值'MG-K10 300mg Q4W'，其中安慰剂组8名受试者"
    "64行同样记录该值——该列不代表所有受试者实际接受的试验药物，为方案"
    "标签式给药记录；实际治疗身份以DM域'试验分组'（试验组8/安慰剂组8）"
    "为准，受试者级随机治疗分配经DM.试验分组与EX.受试者编号显式绑定解析。"
    "EXTRT按中性给药角色保留来源值，IMP身份不由此列声明；暴露与变更能力"
    "在独立IMP身份锚点建立前保持停用（按G-CMIP-005指引）。"
)
MHNUM_ANSWER = (
    "用户已核对：MH域'病史记录号'为域内记录标识，选择闭合目录角色"
    "metadata.record_id（G-ROLE-002指引：选择目录角色）。"
)


def _ev(step: str, ok: bool, **detail: object) -> None:
    with EVIDENCE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run": "r5d_seed", "step": step, "ok": bool(ok), **detail,
        }, ensure_ascii=False) + "\n")


def _http(step: str, method: str, url: str, payload=None, timeout=300):
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
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:1500]}
    _ev(step, status in (200, 201), kind="http", request={"method": method, "url": url},
        http_status=status, elapsed_ms=int((time.monotonic() - started) * 1000),
        response=json.dumps(parsed, ensure_ascii=False)[:2000])
    return status, parsed


def _draft_version() -> int:
    _, body = _http("draft_version_read", "GET",
                    f"{MM}/ai/mapping-drafts/{DRAFT}")
    draft = (body or {}).get("draft") or body or {}
    return int(draft.get("version") or 1)


def patch_field(label: str, domain: str, source_field: str, patch: dict) -> int:
    for _ in range(3):
        version = _draft_version()
        status, body = _http(
            f"field_patch_{label}", "PATCH",
            f"{ATT}/mapping-draft/field",
            payload={
                "draft_id": DRAFT,
                "domain": domain,
                "source_field": source_field,
                "patch": patch,
                "expected_version": version,
                "actor": "r5d_seeder",
                "idempotency_key": f"r5d-patch-{label}-{uuid.uuid4().hex[:8]}",
            },
        )
        if status in (200, 201):
            return 0
        if status == 409:  # version conflict → re-read and retry
            continue
        return 1
    return 1


def main() -> int:
    rc = patch_field("extrt_answer", "EX", "EXTRT", {"user_action": EXTRT_ANSWER})
    rc += patch_field("mhnum_role", "MH", "MHNUM", {
        "recommended_role": "metadata.record_id",
        "user_action": MHNUM_ANSWER,
    })
    # 复核语义质量与剩余问题
    _, body = _http("post_patch_semantic_check", "GET",
                    f"{ATT}/mapping-candidates?focus=all")
    draft = (body or {}).get("draft") or {}
    sq = draft.get("semantic_quality") or {}
    uq = draft.get("user_questions") or []
    _ev("post_patch_state", True,
        semantic_status=sq.get("status"),
        global_blockers=sq.get("global_blocker_count"),
        remaining_user_questions=len(uq))
    print(json.dumps({
        "ok": rc == 0,
        "semantic_status": sq.get("status"),
        "global_blockers": sq.get("global_blocker_count"),
        "remaining_user_questions": len(uq),
    }, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
