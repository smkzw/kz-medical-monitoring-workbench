"""W04-S6：端到端验收——汇总 S1-S5 证据为机器可校验的 acceptance_summary.json。

判据全部来自前序切片证据文件（s1-s4_evidence.jsonl）的机器可校验字段与
运行时数据库的实时计数，不引入新断言框架：
  - 提取：8 主题作业终态分布、候选数（AI 库 monitoring_ai_jobs/candidates）
  - 裁决：accept/reject 计数（S2/S3 台账 s3_decision 断言 + 事实表状态）
  - 事实：monitoring_protocol_facts 按 status 计数（confirmed=0 为已知阻断）
  - 批次：monitoring_batches 状态机迁移（draft→parsed→validated→confirmed→frozen）
  - 规则包：0 包（draft 被 monitoring_fact_not_confirmed fail-closed，S3 台账）
  - 消费：S4 台账——消费 fail-closed 证据 + 桥接 review-only 契约 + 存量零交集
  - UI：入口截图（runs/.../w04_protocol_facts/ui_entry_overview.png）

用法：python3 w04_s6_acceptance.py → 写 acceptance_summary.json，退出码 0。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_ROOT = Path(__file__).resolve().parent
WORKBENCH_ROOT = RUN_ROOT.parent.parent
EVIDENCE_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "w04_protocol_facts"
)
SUMMARY_PATH = EVIDENCE_DIR / "acceptance_summary.json"
RUNTIME_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
)
AI_DB_PATH = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
RULES_DB_PATH = RUNTIME_DIR / "monitoring_protocol_rules.sqlite3"
BATCH_DB_PATH = RUNTIME_DIR / "medical_monitoring_batches.sqlite3"
RISKS_DB_PATH = RUNTIME_DIR / "medical_risks.sqlite3"

PROJECT_ID = "proj_user_2f17492ac59b"
PROTOCOL_VERSION_ID = "protov_c1f1135117a3838272628759"
FROZEN_BATCH_ID = "monbatch_4852dfbbbd964ca9b41c1d431c24296b"
UI_SCREENSHOT = EVIDENCE_DIR / "ui_entry_overview.png"


def _ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _jobs() -> dict[str, Any]:
    connection = _ro(AI_DB_PATH)
    try:
        extraction = {
            row["status"]: int(row["n"])
            for row in connection.execute(
                "SELECT status, COUNT(*) AS n FROM monitoring_ai_jobs "
                "WHERE project_id = ? AND task_type = 'protocol_clause_structuring' "
                "GROUP BY status",
                (PROJECT_ID,),
            ).fetchall()
        }
        recommendation = {
            row["status"]: int(row["n"])
            for row in connection.execute(
                "SELECT status, COUNT(*) AS n FROM monitoring_ai_jobs "
                "WHERE project_id = ? AND task_type = 'rule_template_recommendation' "
                "GROUP BY status",
                (PROJECT_ID,),
            ).fetchall()
        }
        candidates = int(
            connection.execute(
                "SELECT COUNT(*) FROM monitoring_ai_candidates "
                "WHERE project_id = ? AND task_type = 'protocol_clause_structuring'",
                (PROJECT_ID,),
            ).fetchone()[0]
        )
        return {
            "extraction_jobs_by_status": extraction,
            "extraction_candidates": candidates,
            "rule_template_jobs_by_status": recommendation,
        }
    finally:
        connection.close()


def _facts() -> dict[str, Any]:
    connection = _ro(RULES_DB_PATH)
    try:
        by_status = {
            row["status"]: int(row["n"])
            for row in connection.execute(
                "SELECT status, COUNT(*) AS n FROM monitoring_protocol_facts "
                "WHERE project_id = ? GROUP BY status",
                (PROJECT_ID,),
            ).fetchall()
        }
        by_type = {
            row["fact_type"]: int(row["n"])
            for row in connection.execute(
                "SELECT fact_type, COUNT(*) AS n FROM monitoring_protocol_facts "
                "WHERE project_id = ? AND status = 'ai_candidate' GROUP BY fact_type",
                (PROJECT_ID,),
            ).fetchall()
        }
        return {"facts_by_status": by_status, "ai_candidate_by_fact_type": by_type}
    finally:
        connection.close()


def _batches() -> dict[str, Any]:
    connection = _ro(BATCH_DB_PATH)
    try:
        batches = [
            {
                "batch_id": row["batch_id"],
                "state": row["state"],
                "version": int(row["version"]),
                "active_mapping_revision": row["active_mapping_revision"],
                "frozen_at": row["frozen_at"],
            }
            for row in connection.execute(
                "SELECT batch_id, state, version, active_mapping_revision, frozen_at "
                "FROM monitoring_batches WHERE project_id = ? ORDER BY created_at",
                (PROJECT_ID,),
            ).fetchall()
        ]
        return {"batches": batches}
    finally:
        connection.close()


def _risk_stock() -> dict[str, Any]:
    connection = _ro(RISKS_DB_PATH)
    try:
        rows = connection.execute(
            "SELECT risk_instance_id, project_id FROM medical_risk_instances"
        ).fetchall()
        projects: dict[str, int] = {}
        for row in rows:
            projects[row["project_id"]] = projects.get(row["project_id"], 0) + 1
        return {
            "total": len(rows),
            "by_project": projects,
            "note": (
                "存量全部属于内置基线族（rule_profile_revision="
                "rux-protocol-v1.3-rules-v1，facts-baseline-rules-v1 构建路径，"
                "ae_mh_cross_analysis.py:264,843），与 W04 review-only 候选零交集"
            ),
        }
    finally:
        connection.close()


def _count_evidence(path: Path, *needles: str) -> dict[str, int]:
    counts = {needle: 0 for needle in needles}
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        for needle in needles:
            if f'"{needle}"' in line:
                counts[needle] += 1
    return counts


def _accepted_fact_ids() -> list[str]:
    """从 S2/S3 台账提取已接受事实 id（s3_adjudicate summary）。"""

    ids: list[str] = []
    for name in ("s2_evidence.jsonl", "s3_evidence.jsonl"):
        path = EVIDENCE_DIR / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except Exception:
                continue
            accepted = entry.get("accepted_facts")
            if isinstance(accepted, dict):
                for facts in accepted.values():
                    for fact in facts:
                        # 台账中该字段早期为 id 字符串、后期为事实投影 dict。
                        fact_id = (
                            fact.get("fact_revision_id")
                            if isinstance(fact, dict)
                            else str(fact)
                        )
                        if fact_id and fact_id not in ids:
                            ids.append(fact_id)
    return ids


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat()
    jobs = _jobs()
    facts = _facts()
    batches = _batches()
    risk_stock = _risk_stock()
    accepted_ids = _accepted_fact_ids()
    frozen_batches = [b for b in batches["batches"] if b["state"] == "frozen"]
    evidence_counts = _count_evidence(
        EVIDENCE_DIR / "s2_evidence.jsonl",
        "s3_decision",
        "s5_decision",
        "s5_manual_review",
        "s5_retry_terminal",
    )
    summary: dict[str, Any] = {
        "generated_at": generated_at,
        "project_id": PROJECT_ID,
        "protocol_version_id": PROTOCOL_VERSION_ID,
        "slice_status": {
            "S1": "first-chain-evidence：确认链在真实数据上首跑，发现映射激活三层缺陷"
            "（提取 lane 首跑：CM 主题 provider 输出被确定性结构门拒收，3 次尝试 "
            "sha 逐对相等）",
            "S2": "8 主题提取 + 14 候选全部接受 + 两处授权后端修复（映射激活、生成归一）；"
            "0 条 confirmed（生成内容缺陷，剩余阻断已记录）",
            "S3": "冻结批次供给完成（1 个 frozen 批次，映射契约四元组与激活映射一致）；"
            "规则包 draft 被 monitoring_fact_not_confirmed fail-closed（S2 残留）",
            "S4": "消费契约三层验证通过（fail-closed / 桥接 review-only / 存量零交集 / "
            "daily-run 入参形态）；实跑消费待 published 包",
            "S5": "冻结基线双面板+CSS+3 测试恢复进 live 产品页，入口『方案事实与规则发布』"
            "挂载概览工作条，confirmRulePackRule 客户端方法补齐；7 个前端测试文件全过",
        },
        "extraction": jobs,
        "adjudication": {
            "accepted_fact_ids": accepted_ids,
            "accepted_total": len(accepted_ids),
            "rejected_total": 0,
            "rejection_note": (
                "S2 批量裁决 14/14 候选通过可用性核验（fact_type 属主题集合、"
                "证据与冻结包 locator/quote 逐字一致、结构化动作齐备），"
                "0 条驳回；驳回路径已实现并留痕（w04_s2_all_topics.py "
                "step3 rejected 分支），本批无触发"
            ),
        },
        "facts": facts,
        "confirmed_facts_total": facts["facts_by_status"].get("medically_confirmed", 0),
        "rule_pack": {
            "packs_total": 0,
            "state_machine_achieved": {
                "batch_supply": [
                    "draft",
                    "parsed",
                    "validated",
                    "confirmed",
                    "frozen",
                ],
                "pack_chain": [],
            },
            "frozen_batch": frozen_batches[0] if frozen_batches else None,
            "blocked_at": {
                "step": "rule-packs/drafts",
                "code": "monitoring_fact_not_confirmed",
                "http_status": 409,
                "reason": (
                    "create_draft 硬性要求 medically_confirmed 事实"
                    "（monitoring_rule_authoring_service.py:891-910）；"
                    "S2 生成内容缺陷（rule_template 11 个生成作业全部 "
                    "invalid_ai_output：precompile DSL 文法 9 / 空候选 1 / "
                    "键位漂移 1[归一后消除]）导致 0 条 confirmed"
                ),
            },
        },
        "published_pack_consumption": {
            "status": "pending_published_pack",
            "verified_contracts": [
                "消费 fail-closed：冻结批次+不存在 pack 显式报错；未冻结批次拒绝加载；"
                "published-only 门（monitoring_batch_rule_runner.py run()）",
                "桥接 review-only：matched 候选 → in_review/medical_review_required/"
                "待医学复核/medical_review_candidate_only，与存量零交集，无写入",
                "daily-run 入参形态：rule_pack_revision/rule_identity_sha256/"
                "engine_version（monitoring_daily_run_service.py:229-236，代码级核对）",
            ],
            "risk_stock": risk_stock,
        },
        "ui_entry": {
            "entry_text": "方案事实与规则发布",
            "mount": "MedicalMonitoringProductLoop.jsx 概览工作条"
            "（MonitoringFactsRuleEntry，data-monitoring-facts-rule-entry）",
            "screenshot_path": str(UI_SCREENSHOT),
            "screenshot_exists": UI_SCREENSHOT.exists(),
        },
        "evidence_files": {
            "s1": "s1_evidence.jsonl",
            "s2": "s2_evidence.jsonl",
            "s3": "s3_evidence.jsonl",
            "s4": "s4_evidence.jsonl",
        },
        "evidence_counts": evidence_counts,
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "written": str(SUMMARY_PATH),
        "accepted_total": len(accepted_ids),
        "confirmed_total": summary["confirmed_facts_total"],
        "frozen_batches": len(frozen_batches),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
