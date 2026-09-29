"""R5D 预置·复核收敛后最终裁决卡作答（8张，全部依据合成数据列标题实测）。

每张卡："系统两轮独立复核对本字段结论仍不一致，请裁决...可采纳任一方或
给出其他结论"。作答原则：采纳与来源列标题一致的角色（数据实测见
r5d_seed_evidence），user_action 使用决策前缀"用户已核对："。
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
ATT = (f"{BASE}/api/projects/{PROJECT}/modules/medical-monitoring"
       f"/r7/data-admissions/{ATTEMPT}")

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "r5d_seed_evidence.jsonl"

# (domain, source_field, 采纳角色, 依据)
DECISIONS = [
    ("ICF_TRACK", "ICFSTATE", "informed_consent_status",
     "来源列标题'知情状态'，取值已签署/待签署"),
    ("LB_HEM", "LBDAT", "lab_collection_date",
     "来源列标题'采样日期'，全列合法日期，与检验名称同行配对"),
    ("LB_HEM", "LBORRES", "lab_result_value",
     "来源列标题'结果'，CDISC LBORRES原始结果值语义，与单位/参考范围同行配对"),
    ("LB_HEM", "LBSIGNI", "lab_significance_flag",
     "来源列标题'临床意义'（正常/异常/偏低），两轮复核同判lab_clinical_significance，语义一致"),
    ("MH", "MHCAT", "medical_history_category",
     "来源列标题'病史类型'，全列唯一值'既往病史'"),
    ("MH", "MHONGO", "medical_history_ongoing_flag",
     "来源列标题'目前是否持续'，二值分布"),
    ("MH", "MHSTDAT", "medical_history_start_date",
     "来源列标题'开始日期'，与病史名称/持续标志同行"),
    ("SV", "VISDAT", "actual_visit_date",
     "来源列标题'实际访视日期'，与访视状态同行配对"),
]


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
    _ev(step, status in (200, 201), kind="http", request={"method": method, "url": url},
        http_status=status, response=json.dumps(parsed, ensure_ascii=False)[:1500])
    return status, parsed


def main() -> int:
    rc = 0
    for domain, field, role, basis in DECISIONS:
        done = False
        for _ in range(6):
            _, gb = _http("card_version_read", "GET", f"{ATT}/mapping-candidates?focus=all")
            draft = (gb or {}).get("draft") or {}
            version = draft.get("version")
            status, body = _http(
                f"card_answer_{domain}_{field}", "PATCH",
                f"{ATT}/mapping-draft/field",
                payload={
                    "draft_id": DRAFT,
                    "domain": domain,
                    "source_field": field,
                    "patch": {
                        "recommended_role": role,
                        "user_action": (
                            f"用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
                            f"{role}（{basis}）。"
                        ),
                    },
                    "expected_version": version,
                    "actor": "r5d_seeder",
                    "idempotency_key": f"r5d-card-{domain}-{field}-{uuid.uuid4().hex[:8]}",
                },
            )
            if status in (200, 201):
                done = True
                break
            if status != 409:
                rc = 1
                break
            time.sleep(3)
        print(f"{domain}.{field} -> {'OK' if done else 'FAIL'} ({role})", flush=True)
        if not done:
            rc = 1
    _, gb = _http("post_cards_check", "GET", f"{ATT}/mapping-candidates?focus=all")
    draft = (gb or {}).get("draft") or {}
    print(json.dumps({
        "remaining_user_questions": len(draft.get("user_questions") or []),
        "semantic_status": (draft.get("semantic_quality") or {}).get("status"),
    }, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
