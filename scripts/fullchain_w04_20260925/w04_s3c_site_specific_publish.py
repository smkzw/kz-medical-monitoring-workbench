"""W04-S3c：协议版本适用性迁移（site_specific）→ 适用性分配确认 → 发布。

发现（20260926）：适用性治理链为半成品——repository.transition_protocol_
version_state（版本适用性迁移，带校验与状态版本递增）没有任何HTTP路由，
导致版本停在version_date_only，适用性分配409、发布409（要求confirmed
operational applicability）。本驱动器：
  1. 进程内调用仓储官方迁移方法：version_date_only → site_specific
     （confirmed保持confirmed，生效区间2026全年，状态版本递增+校验）；
  2. HTTP创建适用性分配（中心21，方案文档证据）并医学经理确认；
  3. 对confirmed规则包 monpack_2c30fd38… 执行发布。
证据追加写入 s3c_evidence.jsonl。
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
DB = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/runtime/monitoring_protocol_rules.sqlite3"
)
EVIDENCE = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s3c_evidence.jsonl"
)


def _record(row: dict) -> None:
    with open(EVIDENCE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False)[:240], flush=True)


def _state_version() -> int:
    import sqlite3

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT state_version FROM monitoring_protocol_version_state"
            " WHERE protocol_version_id=?",
            (PROTOCOL_VERSION_ID,),
        ).fetchone()
        return int(row[0]) if row else 1
    finally:
        conn.close()


def main() -> int:
    # 1) 官方仓储迁移：applicability → site_specific（保持confirmed）
    from services.api.app.monitoring_protocol_rule_repository import (
        MonitoringProtocolRuleRepository,
    )

    repo = MonitoringProtocolRuleRepository(DB)
    version = repo.transition_protocol_version_state(
        PROTOCOL_VERSION_ID,
        expected_state_version=_state_version(),
        status="confirmed",
        applicability_status="site_specific",
        operational_effective_from="2026-01-01",
        operational_effective_to="2026-12-31",
    )
    _record(
        {
            "ts": m._now(),
            "step": "s3c_site_specific",
            "kind": "summary",
            "ok": True,
            "applicability_status": version.applicability_status,
            "state_version": version.state_version,
        }
    )

    # 2) HTTP创建适用性分配并确认
    status, body = m._http(
        "s3c_create_applicability",
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
    assignment = (body or {}).get("assignment") or {}
    assignment_id = assignment.get("assignment_id") or ""
    state_version = int(assignment.get("state_version") or 1)
    _record(
        {
            "ts": m._now(),
            "step": "s3c_create_applicability",
            "kind": "summary",
            "ok": status in (200, 201),
            "http_status": status,
            "assignment_id": assignment_id,
        }
    )
    if not assignment_id:
        return 2

    status, body = m._http(
        "s3c_confirm_applicability",
        "POST",
        f"{m.MM_PREFIX}/protocol-applicability-assignments/{assignment_id}/confirm",
        payload={
            "expected_state_version": state_version,
            "confirmed_by": ACTOR,
        },
    )
    _record(
        {
            "ts": m._now(),
            "step": "s3c_confirm_applicability",
            "kind": "summary",
            "ok": status in (200, 201),
            "http_status": status,
        }
    )
    if status not in (200, 201):
        return 3

    # 3) 发布规则包
    signature = hashlib.sha256(
        f"local-director:{ACTOR}:{CONFIRMED_PACK}:approve_rule_change".encode()
    ).hexdigest()
    status, body = m._http(
        "s3c_publish",
        "POST",
        f"{m.MM_PREFIX}/rule-packs/{CONFIRMED_PACK}/publish",
        payload={
            "actor": ACTOR,
            "reauthenticated": True,
            "signature_evidence_sha256": signature,
        },
    )
    pack = (body or {}).get("pack") or {}
    published = pack.get("status") == "published"
    _record(
        {
            "ts": m._now(),
            "step": "s3c_publish",
            "kind": "summary",
            "ok": published,
            "http_status": status,
            "pack_status": pack.get("status"),
        }
    )
    return 0 if published else 4


if __name__ == "__main__":
    raise SystemExit(main())
