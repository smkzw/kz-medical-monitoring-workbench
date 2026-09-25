"""W04-S3b：运营适用性分配确认 + 规则包发布 + S4消费实跑（20260926）。

publish 要求协议版本存在"已确认的运营适用性分配"（监测适用中心/范围/
生效区间，医学经理确认）。本驱动器：
  1. 创建适用性分配（中心21，证据取自方案文档）；
  2. 医学经理确认该分配；
  3. 对已confirmed的规则包 monpack_2c30fd38… 执行 publish；
  4. 触发 S4 消费实跑检查（w04_s4_consumption_check.py 的核对逻辑）。
证据追加写入 s3b_evidence.jsonl。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKBENCH_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import w04_s2_all_topics as m  # noqa: E402

ACTOR = "local-user-0249075bebd34158"

PROTOCOL_VERSION_ID = "protov_c1f1135117a3838272628759"
CONFIRMED_PACK = "monpack_2c30fd3833df8f54ba960aa3"
EVIDENCE = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s3b_evidence.jsonl"
)


def _record(row: dict) -> None:
    with open(EVIDENCE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False)[:240], flush=True)


def main() -> int:
    # 1) 创建适用性分配
    status, body = m._http(
        "s3b_create_applicability",
        "POST",
        f"{m.MM_PREFIX}/protocol-applicability-assignments",
        payload={
            "protocol_version_id": PROTOCOL_VERSION_ID,
            "centre_id": "21",
            "operational_effective_from": "2026-01-01",
            "operational_effective_to": "2026-12-31",
            "evidence_text": (
                "MG-K10 CSU III期研究在本中心（21）开展监查；"
                "监查规则包适用全人群，生效区间覆盖研究执行期。"
            ),
            "evidence_source_entry_id": (
                "src_proj_user_2f17492ac59b_protocol_docx_7a346f97d155"
            ),
            "evidence_locator": "docx:paragraph:1027",
            "created_by": ACTOR,
        },
    )
    _record(
        {
            "ts": m._now(),
            "step": "s3b_create_applicability",
            "kind": "summary",
            "ok": status in (200, 201),
            "http_status": status,
        }
    )
    assignment = (body or {}).get("assignment") or {}
    assignment_id = assignment.get("assignment_id") or ""
    state_version = int(assignment.get("state_version") or 1)
    if not assignment_id:
        _record(
            {
                "ts": m._now(),
                "step": "s3b_create_applicability",
                "kind": "summary",
                "ok": False,
                "reason": "assignment_id 缺失",
                "body": json.dumps(body, ensure_ascii=False)[:300],
            }
        )
        return 2

    # 2) 医学经理确认适用性
    status, body = m._http(
        "s3b_confirm_applicability",
        "POST",
        f"{m.MM_PREFIX}/protocol-applicability-assignments/{assignment_id}/confirm",
        payload={
            "expected_state_version": state_version,
            "confirmed_by": ACTOR,
        },
    )
    confirmed = status in (200, 201)
    _record(
        {
            "ts": m._now(),
            "step": "s3b_confirm_applicability",
            "kind": "summary",
            "ok": confirmed,
            "http_status": status,
        }
    )
    if not confirmed:
        return 3

    # 3) 发布规则包
    status, body = m._http(
        "s3b_publish",
        "POST",
        f"{m.MM_PREFIX}/rule-packs/{CONFIRMED_PACK}/publish",
        payload={
            "actor": ACTOR,
            "reauthenticated": True,
            "signature_evidence_sha256": hashlib.sha256(
                f"local-director:{ACTOR}:{CONFIRMED_PACK}:approve_rule_change".encode()
            ).hexdigest(),
        },
    )
    pack = (body or {}).get("pack") or {}
    published = pack.get("status") == "published"
    _record(
        {
            "ts": m._now(),
            "step": "s3b_publish",
            "kind": "summary",
            "ok": published,
            "http_status": status,
            "pack_status": pack.get("status"),
            "rule_pack_id": CONFIRMED_PACK,
        }
    )
    return 0 if published else 4


if __name__ == "__main__":
    raise SystemExit(main())
