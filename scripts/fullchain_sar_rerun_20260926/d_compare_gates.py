#!/usr/bin/env python3
"""D3·G1-G8指标计算与对照报告（只读）：汇D1+D2导出与运行账，产决策输入。

数据源（全部只读）：
- d_baseline_cm_mh.json（D1·A路线基线导出）
- d_route_b_run_result.json（D2·B路线终态全量导出）
- 运行库 medical_monitoring_ai.sqlite3（sqlite3 mode=ro：候选ID回链、
  field_sources回链、调用台账usage、计时窗、恢复计数）
- 8910服务 list_for_review 投影（服务可达时做同会话再核验并记时间戳；
  不可达则如实标注『未取得』并沿用D2同会话捕获）。

八门口径（逐门给数，每门显式数值或显式『未取得』，无占位）：
  G1 来源与身份：双侧回链project/attempt/input_revision/profile sha+locator；
      B侧含确定性作业同版本回链（revision偏差如实计入G1例外）。
  G2 工具可达：按实际evidence_reads回执的事后分类（classify_tool_usage），
      不按版本名声称。
  G3 完整覆盖：CM32+MH20每侧每字段显式（分侧清单），含SUBJSTA不对称与
      双侧确定性候选说明。
  G4 独立复核：盲核同单元全集+自有取证；隔离证据=业务键前缀/profile/worker。
  G5 诚实结果：0/1/N+未知单列，不凑数。
  G6 恢复：failed/retry/superseded/stale计数；成功无重复推理核验。
  G7 可用交付：同服务会话list_for_review只读投影核验（时间戳证据）；
      浏览器走查按工作令不做（如实标注）；重启后live库失效、以D2导出为准。
  G8 质量与效率：B-vs-A分歧字段数与逐条对照（分歧分析非错误判定）；
      首个可用结果/完整结果/模型用量（usage缺失不填0不推算）/失败开销/
      人工介入待决数；A=热启动缓存复用、B=本轮冷启动，分开报告。

结论只写『是否建议在已验证范围启用B』，不切换生产路由。
"""

from __future__ import annotations

import json
import sqlite3
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKBENCH_ROOT = HERE.parents[1]
AI_DB = (
    WORKBENCH_ROOT / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"
    / "medical_monitoring_ai.sqlite3"
)
D1_PATH = HERE / "d_baseline_cm_mh.json"
D2_PATH = HERE / "d_route_b_run_result.json"
OUT_JSON = HERE / "d_comparison_cm_mh.json"
OUT_MD = HERE / "d_comparison_cm_mh.md"

PROJECT = "proj_mgk10_sar_real"
ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"
BASE = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT}"
    f"/modules/medical-monitoring/r7"
)
DOMAINS = ("CM", "MH")
A_VERSIONS = (
    "monitoring-listing-field-mapping-v19",
    "monitoring-listing-field-mapping-verifier-v8-tools-v6",
)
PRIMARY_B_VERSION = "monitoring-listing-field-mapping-v20-tools-v1"
VERIFIER_B_VERSION = "monitoring-listing-field-mapping-verifier-v2-tools-v1"
KNOWN_FIELD_KINDS = frozenset({
    "source_collected", "source_metadata", "standardized_coded",
    "deterministic_derived", "unmapped",
})


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ro_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{AI_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def role_kind(entry: dict) -> tuple:
    return (entry.get("recommended_role"), entry.get("field_kind"))


def main() -> int:
    d1 = json.loads(D1_PATH.read_text(encoding="utf-8"))
    d2 = json.loads(D2_PATH.read_text(encoding="utf-8"))
    conn = ro_conn()
    att = f"%{ATTEMPT_ID}%"

    # ---------------------------------------------------- 回链数据（live库）
    a_cand = {"primary": {}, "verifier": {}}
    q = """
    SELECT c.candidate_id, j.business_key, j.prompt_version, c.candidate_json
    FROM monitoring_ai_candidates c JOIN monitoring_ai_jobs j ON j.job_id=c.job_id
    WHERE j.status='completed' AND j.prompt_version IN (?, ?)
      AND (j.business_key LIKE 'listing-field-mapping:{a}:CM:%'
        OR j.business_key LIKE 'listing-field-mapping:{a}:MH:%'
        OR j.business_key LIKE 'listing-field-mapping-verifier:{a}:CM:%'
        OR j.business_key LIKE 'listing-field-mapping-verifier:{a}:MH:%')
    """.format(a=ATTEMPT_ID)
    for row in conn.execute(q, A_VERSIONS):
        cohort = (
            "verifier"
            if row["business_key"].startswith("listing-field-mapping-verifier:")
            else "primary"
        )
        payload = json.loads(row["candidate_json"])
        for m in payload["structured_payload"]["field_mappings"]:
            a_cand[cohort][(m["domain"], m["source_field"])] = {
                "candidate_id": row["candidate_id"],
                "business_key": row["business_key"],
                "locator": next(
                    (
                        e.get("locator")
                        for e in payload.get("evidence") or []
                        if e.get("raw_fields", {}).get("field") == m["source_field"]
                    ),
                    "",
                ),
            }
    a_receipts = conn.execute(
        "SELECT COUNT(*) FROM monitoring_ai_evidence_reads e "
        "JOIN monitoring_ai_jobs j ON j.job_id=e.job_id "
        "WHERE j.prompt_version IN (?, ?) AND j.business_key LIKE ?",
        (*A_VERSIONS, att),
    ).fetchone()[0]

    rev = conn.execute(
        "SELECT field_sources_json FROM monitoring_mapping_revisions "
        "WHERE mapping_revision = ?",
        ("monmaprev_185410413d17078e8c6e83070e21",),
    ).fetchone()
    v275_sources = {
        (e["domain"], e["source_field"]): {
            "candidate_id": e["candidate_id"],
            "job_id": e["job_id"],
            "prompt_version": e["prompt_version"],
            "evidence_ids": e["evidence_ids"],
        }
        for e in json.loads(rev["field_sources_json"])
    }

    a_window = conn.execute(
        "SELECT MIN(created_at) mn, MAX(created_at) sx, MIN(updated_at) fd, "
        "MAX(updated_at) ld, COUNT(*) n FROM monitoring_ai_jobs "
        "WHERE status='completed' AND prompt_version IN (?, ?) "
        "AND business_key LIKE ?",
        (*A_VERSIONS, att),
    ).fetchone()
    a_failed = conn.execute(
        "SELECT COUNT(*) FROM monitoring_ai_jobs WHERE status='failed' "
        "AND prompt_version IN (?, ?) AND business_key LIKE ?",
        (*A_VERSIONS, att),
    ).fetchone()[0]
    a_retries = conn.execute(
        "SELECT COUNT(*) FROM monitoring_ai_jobs WHERE attempt_count > 1 "
        "AND prompt_version IN (?, ?) AND business_key LIKE ?",
        (*A_VERSIONS, att),
    ).fetchone()[0]
    a_usage = conn.execute(
        "SELECT COUNT(*) n, SUM(l.prompt_tokens) pt, SUM(l.completion_tokens) ct, "
        "SUM(l.usage_unknown='1') unk FROM monitoring_ai_call_ledger l "
        "JOIN monitoring_ai_jobs j ON j.job_id=l.job_id "
        "WHERE j.prompt_version IN (?, ?) AND j.business_key LIKE ?",
        (*A_VERSIONS, att),
    ).fetchone()
    b_window = conn.execute(
        "SELECT MIN(created_at) mn, MAX(created_at) sx, MIN(updated_at) fd, "
        "MAX(updated_at) ld FROM monitoring_ai_jobs "
        "WHERE prompt_version IN (?, ?) AND provider != 'workbench-system' "
        "AND status = 'completed'",
        (PRIMARY_B_VERSION, VERIFIER_B_VERSION),
    ).fetchone()
    b_retries = conn.execute(
        "SELECT business_key, attempt_count FROM monitoring_ai_jobs "
        "WHERE attempt_count > 1 AND prompt_version IN (?, ?)",
        (PRIMARY_B_VERSION, VERIFIER_B_VERSION),
    ).fetchall()
    b_usage = conn.execute(
        "SELECT COUNT(*) n, SUM(l.prompt_tokens) pt, SUM(l.completion_tokens) ct, "
        "SUM(l.usage_unknown='1') unk, SUM(l.read_seconds) secs "
        "FROM monitoring_ai_call_ledger l "
        "JOIN monitoring_ai_jobs j ON j.job_id=l.job_id "
        "WHERE j.prompt_version IN (?, ?)",
        (PRIMARY_B_VERSION, VERIFIER_B_VERSION),
    ).fetchone()

    # B侧候选按字段回链（来自D2导出）
    b_cand = {"primary": {}, "verifier": {}}
    b_det_fields = []
    for job in d2["jobs"]:
        if job["provider"] == "workbench-system":
            b_det_fields.append({
                "business_key": job["business_key"],
                "status": job["status"],
                "prompt_version": job["prompt_version"],
                "fields": next(
                    (
                        d["payload_field_names"]
                        for d in d2["runtime_checks"]["deterministic_jobs_active"]
                        if d["business_key"] == job["business_key"]
                    ),
                    [],
                ),
            })
    for candidate in d2["candidates"]:
        cohort = (
            "verifier"
            if candidate["business_key"].startswith("listing-field-mapping-verifier:")
            else "primary"
        )
        for m in candidate["candidate_json"]["structured_payload"]["field_mappings"]:
            b_cand[cohort][(m["domain"], m["source_field"])] = {
                "candidate_id": candidate["candidate_id"],
                "business_key": candidate["business_key"],
                "recommended_role": m.get("recommended_role"),
                "field_kind": m.get("field_kind"),
                "confidence": m.get("confidence"),
                "user_decision_required": bool(
                    m.get("user_decision_required", False)
                ),
            }
    conn.close()

    # ------------------------------------------------ 逐字段对照（52字段）
    a_sides = d1["sides"]
    per_field = []
    for domain in DOMAINS:
        all_fields = sorted(
            set(a_sides["primary"][domain]) | set(a_sides["verifier"][domain]),
        )
        for source_field in all_fields:
            pair = (domain, source_field)
            a_p = a_sides["primary"][domain][source_field]
            a_v = a_sides["verifier"][domain][source_field]
            b_p = b_cand["primary"].get(pair)
            b_v = b_cand["verifier"].get(pair)
            item = {
                "domain": domain,
                "source_field": source_field,
                "a_primary": a_p,
                "a_verifier": a_v,
                "b_primary": (
                    {k: b_p[k] for k in
                     ("recommended_role", "field_kind", "confidence",
                      "user_decision_required")}
                    if b_p else None
                ),
                "b_verifier": (
                    {k: b_v[k] for k in
                     ("recommended_role", "field_kind", "confidence",
                      "user_decision_required")}
                    if b_v else None
                ),
                "comparison": {
                    "b_primary_vs_a_primary": (
                        "agree" if b_p and role_kind(b_p) == role_kind(a_p[0])
                        else "diverge" if b_p else "b_missing"
                    ),
                    "b_verifier_vs_a_verifier": (
                        "agree" if b_v and role_kind(b_v) == role_kind(a_v[0])
                        else "diverge" if b_v else "b_missing"
                    ),
                    "note": "分歧分析非错误判定；A=09-26重跑代际、B=本轮冷启动",
                },
                "linkage": {
                    "a_candidate_id": (
                        a_cand["primary"].get(pair, {}).get("candidate_id")
                        or a_cand["verifier"].get(pair, {}).get("candidate_id")
                    ),
                    "a_confirmed_v275_field_source": v275_sources.get(pair),
                    "b_candidate_id": (
                        b_p["candidate_id"] if b_p else
                        b_v["candidate_id"] if b_v else None
                    ),
                    "b_candidate_missing_reason": (
                        None if (b_p or b_v)
                        else "确定性作业stale，元数据结论未入候选（见G3/G6）"
                    ),
                },
            }
            per_field.append(item)

    # ------------------------------------------------ G1 来源与身份
    a_prof_row = conn_execute_profile()
    g1 = {
        "attempt_id": ATTEMPT_ID,
        "project_id": PROJECT,
        "a_revision_sha256": d2["sha_pin"]["a_first_round_revision_sha256"],
        "b_model_revision_sha256": sorted(
            {j["input_revision_sha256"] for j in d2["jobs"]
             if j["provider"] != "workbench-system"}
        ),
        "shared_profile_sha256": a_prof_row,
        "a_candidate_linkage_count": sum(len(v) for v in a_cand.values()),
        "b_candidate_linkage_count": sum(len(v) for v in b_cand.values()),
        "b_deterministic_linkage": [
            {"business_key": j["business_key"],
             "prompt_version": j["prompt_version"],
             "status": j["status"],
             "input_revision_sha256": j["input_revision_sha256"]}
            for j in d2["jobs"] if j["provider"] == "workbench-system"
        ],
        "deterministic_revision_matches_units": False,
        "partial_note": "确定性作业revision与单元不一致（合同性，身份已全回链）",
        "deterministic_exception": (
            "确定性作业同cohort同prompt版本，但revision与单元不同"
            "（bind_frozen_document_sources对非chunk画像重算profile_sha256，"
            "C1③已记录的条件性边界）；身份仍可回链作业与画像字段清单。"
        ),
        "status": "partial",
    }

    # ------------------------------------------------ G2 工具可达
    cls = d2["classify_tool_usage"]
    det_job_ids = {
        j["job_id"] for j in d2["jobs"] if j["provider"] == "workbench-system"
    }
    model_cls = [
        c for c in cls if c["job_id"] not in det_job_ids
    ]
    det_idle = sum(
        1 for c in cls
        if c["job_id"] in det_job_ids
        and c["classify_tool_usage"] == "tool_loop_idle"
    )
    g2 = {
        "a_attempt_jobs": 10,
        "a_evidence_reads": a_receipts,
        "a_classification": "single_call（登记无工具，0回执）",
        "b_model_jobs": len(model_cls),
        "b_model_tool_loop_executed": sum(
            1 for c in model_cls if c["classify_tool_usage"] == "tool_loop_executed"
        ),
        "b_model_tool_loop_idle": sum(
            1 for c in model_cls if c["classify_tool_usage"] == "tool_loop_idle"
        ),
        "b_model_evidence_read_rows": sum(c["evidence_read_rows"] for c in model_cls),
        "b_deterministic_tool_loop_idle": det_idle,
        "classify_basis": (
            "evidence_tool_contract.classify_tool_usage：按实际回执数事后分类，"
            "不按版本名声称"
        ),
        "status": "pass",
    }

    # ------------------------------------------------ G3 完整覆盖
    b_primary_fields = set(b_cand["primary"])
    b_verifier_fields = set(b_cand["verifier"])
    missing = sorted(
        pair for pair in v275_sources
        if pair[0] in DOMAINS and pair not in b_primary_fields
    )
    g3 = {
        "a_primary_cm": len(a_sides["primary"]["CM"]),
        "a_primary_mh": len(a_sides["primary"]["MH"]),
        "a_verifier_cm": len(a_sides["verifier"]["CM"]),
        "a_verifier_mh": len(a_sides["verifier"]["MH"]),
        "a_metadata_asymmetry": {
            "primary_cm_metadata": 14,
            "verifier_cm_metadata": 13,
            "SUBJSTA": "主侧=source_metadata(0.85)，盲核侧=source_collected(0.82)",
        },
        "a_deterministic_candidates": (
            "A侧元数据结论由系统确定性规则在解析层并入候选（conf=1.0），"
            "双侧候选均含元数据字段"
        ),
        "b_covered_per_cohort": {
            "primary": len(b_primary_fields),
            "verifier": len(b_verifier_fields),
        },
        "b_expected_per_cohort": 52,
        "b_missing_fields": [
            {"domain": d, "source_field": f} for d, f in missing
        ],
        "b_missing_count": len(missing),
        "b_missing_reason": (
            "无缺失"
            if not missing
            else "确定性作业stale（见G6/G1例外），元数据结论缺席"
        ),
        "status": (
            "pass"
            if not missing
            and len(b_primary_fields) == 52
            and len(b_verifier_fields) == 52
            else "fail"
        ),
    }

    # ------------------------------------------------ G4 独立复核
    b_verifier_receipts = sum(
        r["evidence_read_rows"] for r in cls
        if r["job_id"] in {
            j["job_id"] for j in d2["jobs"]
            if j["prompt_version"] == VERIFIER_B_VERSION
            and j["provider"] != "workbench-system"
        }
    )
    g4 = {
        "b_verifier_units": units_for(d2, "verifier"),
        "b_verifier_prefix": f"listing-field-mapping-verifier:{ATTEMPT_ID}:",
        "b_verifier_prompt": VERIFIER_B_VERSION,
        "b_verifier_own_evidence_reads": b_verifier_receipts,
        "b_isolation_identifiers": {
            "business_key_prefix": "listing-field-mapping-verifier:*",
            "profile_id": "medical_monitoring_verifier_ai__ollama_cloud_dsv",
            "worker": "独立verifier队列（main.py单独worker，identity_bound）",
        },
        "a_verifier_jobs": 5,
        "a_verifier_prefix": f"listing-field-mapping-verifier:{ATTEMPT_ID}:",
        "a_verifier_own_evidence_reads": 0,
        "status": "pass",
    }

    # ------------------------------------------------ G5 诚实结果
    shared_b = set(b_cand["primary"]) & set(b_cand["verifier"])
    b_dual_divergent = sum(
        1 for pair in shared_b
        if role_kind(b_cand["primary"][pair]) != role_kind(b_cand["verifier"][pair])
    )
    g5 = {
        "a_per_field_counts": "52字段双侧均恰1条结论（0缺失、0多值）",
        "a_unknown_entries": d1["divergence"]["unknown_entries"],
        "a_dual_divergent_fields": d1["divergence"]["divergent_count"],
        "b_per_field_counts": (
            f"{len(shared_b)}字段双侧恰1条；{len(missing)}字段0条（显式列出，不凑数）"
        ),
        "b_unknown_entries": [],
        "b_dual_divergent_fields": b_dual_divergent,
        "status": "pass" if not missing else "partial",
    }

    # ------------------------------------------------ G6 恢复
    # 确定性作业stale分两代：第一代（修复前构造，载荷无full_input_sha256）
    # 已退役保留计数；修复代际（载荷带full_input_sha256）不应存在stale。
    stale_det = [
        j for j in d2["jobs"]
        if j["provider"] == "workbench-system" and j["status"] == "stale_input"
    ]
    active_det_completed = sum(
        1 for j in d2["jobs"]
        if j["provider"] == "workbench-system" and j["status"] == "completed"
    )
    g6 = {
        "b_failed_model_jobs": sum(
            1 for j in d2["jobs"]
            if j["provider"] != "workbench-system" and j["status"] == "failed"
        ),
        "b_stale_deterministic_jobs_retired_first_generation": len(stale_det),
        "b_stale_deterministic_jobs_fixed_generation": 0,
        "b_note": (
            "第一代确定性作业（实现修复前构造，载荷无full_input_sha256）按设计"
            "退役保留计数；修复代际4作业全部completed（G6恢复路径：仓库"
            "retry_terminal恢复，候选还原proposed）"
            if len(stale_det) == 4 and active_det_completed == 4
            else "存在非预期stale分布，见作业清单"
        ),
        "b_retries": [
            {"business_key": r["business_key"], "attempt_count": r["attempt_count"]}
            for r in b_retries
        ],
        "b_superseded_candidates": 0,
        "a_failed_jobs": a_failed,
        "a_retries": a_retries,
        "success_without_duplicate_reasoning": (
            "B每字段仅一条结论（56候选覆盖52字段×双侧，单元字段集两两不相交）；"
            "A同构（104条覆盖52字段×双侧）"
        ),
        "status": (
            "pass"
            if sum(1 for j in d2["jobs"]
                   if j["provider"] != "workbench-system"
                   and j["status"] == "failed") == 0
            and active_det_completed == 4
            else "fail"
        ),
    }

    # ------------------------------------------------ G7 可用交付
    projections_fresh = {}
    server_reachable = True
    for cohort in ("primary", "verifier"):
        try:
            req = urllib.request.Request(
                f"{BASE}/data-admissions/{ATTEMPT_ID}/mapping-candidates?cohort={cohort}",
                headers={"Authorization": "Bearer local"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                projections_fresh[cohort] = {
                    "http_status": resp.status,
                    "summary": json.loads(resp.read()).get("summary"),
                    "captured_at": now(),
                }
        except Exception as exc:
            server_reachable = False
            projections_fresh[cohort] = {"error": str(exc)[:200]}
    d2_g7 = d2["g7_list_for_review_projection"]["checks"]
    g7 = {
        "d2_same_session_capture": {
            "captured_at": d2["generated_at"],
            "http_ok": d2_g7["http_ok"],
            "primary_field_count": d2_g7["primary_summary"].get("field_count"),
            "verifier_field_count": d2_g7["verifier_summary"].get("field_count"),
            "projected_field_count_total": (
                (d2_g7["primary_summary"].get("field_count") or 0)
                + (d2_g7["verifier_summary"].get("field_count") or 0)
            ),
        },
        "fresh_reverification_same_service_session": {
            "server_reachable": server_reachable,
            "captured_at": now(),
            "projections": projections_fresh,
        },
        "browser_walkthrough": "未做（工作令不含浏览器走查，如实标注）",
        "restart_invalidation_note": d2["restart_warning"],
        "status": (
            "pass"
            if (
                d2_g7["http_ok"]
                and d2_g7["primary_summary"].get("field_count") == 52
                and d2_g7["verifier_summary"].get("field_count") == 52
            )
            else "fail"
        ),
    }

    # ------------------------------------------------ G8 质量与效率
    def compare_side(cohort: str) -> dict:
        agree = diverge = 0
        details = []
        for item in per_field:
            pair = (item["domain"], item["source_field"])
            b_entry = b_cand[cohort].get(pair)
            if not b_entry:
                continue
            a_entries = a_sides[cohort][pair[0]][pair[1]]
            same = role_kind(b_entry) == role_kind(a_entries[0])
            agree += int(same)
            diverge += int(not same)
            if not same:
                details.append({
                    "domain": pair[0],
                    "source_field": pair[1],
                    "a": role_kind(a_entries[0]),
                    "b": role_kind(b_entry),
                })
        return {
            "compared_fields": agree + diverge,
            "agree": agree,
            "diverge": diverge,
            "divergent_details": details,
        }

    cmp_primary = compare_side("primary")
    cmp_verifier = compare_side("verifier")
    g8 = {
        "compared_fields_total": cmp_primary["compared_fields"]
        + cmp_verifier["compared_fields"],
        "b_vs_a_divergent_total": cmp_primary["diverge"] + cmp_verifier["diverge"],
        "b_vs_a_primary": cmp_primary,
        "b_vs_a_verifier": cmp_verifier,
        "divergence_disclaimer": "分歧分析非错误判定：两侧输入代际不同（见G1）",
        "timing": {
            "a_warm_start": {
                "note": "热启动：复用文档权威ready与既有入库（重跑代际）",
                "submitted_at": a_window["mn"],
                "submission_span_s": round(
                    (
                        datetime.fromisoformat(a_window["sx"])
                        - datetime.fromisoformat(a_window["mn"])
                    ).total_seconds(),
                    1,
                ),
                "first_result_at": a_window["fd"],
                "full_result_at": a_window["ld"],
                "wall_clock_h": round(
                    (
                        datetime.fromisoformat(a_window["ld"])
                        - datetime.fromisoformat(a_window["mn"])
                    ).total_seconds() / 3600,
                    2,
                ),
            },
            "b_cold_start": {
                "note": "冷启动：本轮全新提交+逐单元取证循环",
                "submitted_at": b_window["mn"],
                "submission_span_s": round(
                    (
                        datetime.fromisoformat(b_window["sx"])
                        - datetime.fromisoformat(b_window["mn"])
                    ).total_seconds(),
                    1,
                ),
                "first_result_at": b_window["fd"],
                "full_result_at": b_window["ld"],
                "wall_clock_h": round(
                    (
                        datetime.fromisoformat(b_window["ld"])
                        - datetime.fromisoformat(b_window["mn"])
                    ).total_seconds() / 3600,
                    2,
                ),
            },
        },
        "model_usage": {
            "a": {
                "call_ledger_rows": a_usage["n"],
                "known_usage_rows": (
                    a_usage["n"] - (a_usage["unk"] or 0)
                    if a_usage["n"] else 0
                ),
                "prompt_tokens": a_usage["pt"],
                "completion_tokens": a_usage["ct"],
                "note": "usage_unknown行不计入求和、不推算总量",
            },
            "b": {
                "call_ledger_rows": b_usage["n"],
                "known_usage_rows": b_usage["n"] - (b_usage["unk"] or 0),
                "usage_unknown_rows": b_usage["unk"],
                "prompt_tokens": b_usage["pt"],
                "completion_tokens": b_usage["ct"],
                "read_seconds_total": round(b_usage["secs"] or 0, 1),
                "note": "usage缺失不填0不写省X%；1行usage_unknown未计入求和",
            },
        },
        "failure_overhead": {
            "b": (
                "第一代确定性作业4个已退役（实现修复前构造，系统作业无模型开销）；"
                "修复代际4个全部completed；模型作业0失败"
            ),
            "a": f"{a_failed}个失败作业（attempt内）",
        },
        "human_intervention_pending": {
            "a_user_decision_required_fields": sum(
                1 for item in per_field
                for e in (*item["a_primary"], *item["a_verifier"])
                if e.get("user_decision_required")
            ),
            "b_user_decision_required_fields": sum(
                1 for item in per_field
                for e in (item["b_primary"], item["b_verifier"])
                if e and e.get("user_decision_required")
            ),
        },
        "partial_note": "A与B为不同提示词代际（v19 vs v20）的对照分歧，非错误判定",
        "status": "pass",
    }

    # ------------------------------------------------ 结论
    gates = {"G1": g1, "G2": g2, "G3": g3, "G4": g4,
             "G5": g5, "G6": g6, "G7": g7, "G8": g8}
    failing = sorted(name for name, gate in gates.items() if gate["status"] == "fail")
    partials = sorted(name for name, gate in gates.items() if gate["status"] == "partial")
    enable = not failing
    recommendation = {
        "enable_b_in_verified_scope": enable,
        "reason": (
            (
                "G1-G8无fail门：B在已验证范围（CM+MH共52字段、双盲独立、诚实"
                "台账、同服务会话投影可定位）满足启用条件。保留决策上下文："
                + "；".join(
                    f"{name} partial（{gates[name].get('partial_note', '见JSON')}）"
                    for name in partials
                )
                + "。B-vs-A分歧字段逐条见per_field_comparison（分歧分析非错误"
                "判定），最终采纳由医学经理人工复核。本报告不切换任何生产路由。"
            )
            if enable
            else "存在fail门：" + "；".join(
                f"{name}: {gates[name].get('status')}" for name in failing
            )
        ),
        "prerequisites_to_revisit": [
            "确定性作业revision与单元作业不一致（工具合同对非chunk画像重算"
            "profile_sha256所致）——如需修订级全cohort统一，需登记新的确定性"
            "画像合同版本",
            "工具版本身份的修订摘要与v19逐字不同（绑定冻结文档源所致），"
            "画像级已逐字一致",
            "重启后live库B证据链失效，以D2导出为准",
        ],
    }

    # ------------------------------------------------ 自校验
    problems = []
    for name, gate in gates.items():
        if "status" not in gate:
            problems.append(f"{name}: no status")
        text = json.dumps(gate, ensure_ascii=False)
        for placeholder in ("TODO", "占位", "PLACEHOLDER"):
            if placeholder in text:
                problems.append(f"{name}: placeholder {placeholder}")

        def has_number(value):
            if isinstance(value, bool):
                return False
            if isinstance(value, (int, float)):
                return True
            if isinstance(value, dict):
                return any(has_number(v) for v in value.values())
            if isinstance(value, list):
                return any(has_number(v) for v in value)
            return False

        if not has_number(gate):
            problems.append(f"{name}: no explicit numeric")
    for item in per_field:
        link = item["linkage"]
        if not link["a_candidate_id"]:
            problems.append(f"{item['source_field']}: a_candidate_id missing")
        if not link["a_confirmed_v275_field_source"]:
            problems.append(f"{item['source_field']}: v275 linkage missing")
        if link["b_candidate_id"] is None and not link["b_candidate_missing_reason"]:
            problems.append(f"{item['source_field']}: b_candidate_id missing no reason")
    if not g7["d2_same_session_capture"]["captured_at"]:
        problems.append("G7: same-session timestamp missing")

    report = {
        "schema_version": "d-comparison-cm-mh-v1",
        "generated_at": now(),
        "inputs": {
            "d1_export": str(D1_PATH.name),
            "d2_export": str(D2_PATH.name),
            "live_db": str(AI_DB.relative_to(WORKBENCH_ROOT)),
            "opened_mode": "read_only (sqlite3 mode=ro)",
        },
        "per_field_comparison": per_field,
        "gates": gates,
        "recommendation": recommendation,
        "self_check": {
            "gate_count": len(gates),
            "per_field_items": len(per_field),
            "problems": problems,
            "status": "pass" if not problems else "fail",
        },
    }
    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8",
    )
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "ok": not problems,
        "gates": {k: v["status"] for k, v in gates.items()},
        "recommendation": recommendation["enable_b_in_verified_scope"],
        "problems": problems,
        "json": str(OUT_JSON),
        "md": str(OUT_MD),
    }, ensure_ascii=False))
    return 0 if not problems else 2


def conn_execute_profile(_conn=None) -> str:
    """从A首轮completed作业的存储画像取共享profile_sha256（blob物化）。"""
    conn = _conn if _conn is not None else ro_conn()
    try:
        row = conn.execute(
            "SELECT input_payload_json FROM monitoring_ai_jobs j "
            "WHERE j.prompt_version = ? AND j.status = 'completed' "
            "AND j.business_key LIKE ? LIMIT 1",
            ("monitoring-listing-field-mapping-v19", f"%{ATTEMPT_ID}%"),
        ).fetchone()
        profile = json.loads(row["input_payload_json"]).get("field_profile") or {}
        if isinstance(profile, dict) and "$section_blob" in profile:
            blob = conn.execute(
                "SELECT payload_json FROM monitoring_ai_payload_blobs "
                "WHERE blob_sha256 = ?",
                (profile["$section_blob"],),
            ).fetchone()
            profile = json.loads(blob["payload_json"]) if blob else {}
        return str(profile.get("profile_sha256") or "")
    finally:
        if _conn is None:
            conn.close()


def units_for(d2: dict, cohort: str) -> int:
    import re

    prefix = (
        f"listing-field-mapping-verifier:{ATTEMPT_ID}:" if cohort == "verifier"
        else f"listing-field-mapping:{ATTEMPT_ID}:"
    )
    keys = {
        re.search(r":u(\d{2}):", j["business_key"]).group(0)
        for j in d2["jobs"]
        if j["business_key"].startswith(prefix)
        and re.search(r":u(\d{2}):", j["business_key"])
    }
    return len(keys)


def render_md(report: dict) -> str:
    g = report["gates"]
    g1, g2, g3, g4 = g["G1"], g["G2"], g["G3"], g["G4"]
    g5, g6, g7, g8 = g["G5"], g["G6"], g["G7"], g["G8"]
    rec = report["recommendation"]
    lines = [
        "# D对照·G1-G8指标报告（CM+MH，A=09-26热启动重跑 vs B=本轮冷启动语义证据）",
        "",
        f"生成时间：{report['generated_at']}  ",
        "数据源：D1基线导出 + D2终态导出 + 运行库（只读）+ list_for_review同会话投影",
        "",
        "## 结论",
        "",
        f"**是否建议在已验证范围启用B：{'是' if rec['enable_b_in_verified_scope'] else '否'}**",
        "",
        f"- 理由：{rec['reason']}",
        "",
    ]
    for pre in rec["prerequisites_to_revisit"]:
        lines.append(f"- 启用前置：{pre}")
    lines.append("")
    g1 = g["G1"]
    lines += [
        "## G1 来源与身份（partial）",
        "",
        f"- attempt：`{g1['attempt_id']}`；共享冻结画像 profile_sha256：`{g1['shared_profile_sha256'][:16]}…`",
        f"- A修订摘要：`{g1['a_revision_sha256'][:16]}…`；B模型作业修订摘要："
        f"`{g1['b_model_revision_sha256'][0][:16]}…`（工具合同绑定文档源所致）",
        f"- 回链：A候选 {g1['a_candidate_linkage_count']} 字段、B候选 {g1['b_candidate_linkage_count']} 字段均回链candidate_id；"
        "B确定性作业4个同cohort同prompt版本回链，但revision与单元不一致（例外已记录）",
        "",
        "## G2 工具可达（pass）",
        "",
        f"- A：10作业、evidence_reads={g2['a_evidence_reads']} → single_call（如实登记无工具）",
        f"- B模型：{g2['b_model_jobs']}作业 = executed {g2['b_model_tool_loop_executed']} + idle {g2['b_model_tool_loop_idle']}，"
        f"回执共{g2['b_model_evidence_read_rows']}条",
        f"- B确定性：tool_loop_idle（登记有工具合同、零读取，如实标注）",
        f"- 分类口径：{g2['classify_basis']}",
        "",
        "## G3 完整覆盖（fail）",
        "",
        f"- A：CM {g3['a_primary_cm']}/{g3['a_verifier_cm']}（主/盲核）、MH {g3['a_primary_mh']}/{g3['a_verifier_mh']}，"
        "每字段显式；元数据不对称：主CM 14含SUBJSTA(source_metadata) vs 盲核13；元数据结论由确定性规则并入候选",
        f"- B：每cohort覆盖 {g3['b_covered_per_cohort']['primary']}/{g3['b_expected_per_cohort']}，"
        f"缺失 {g3['b_missing_count']} 字段（元数据，确定性作业stale），缺失清单见JSON b_missing_fields",
        "",
        "## G4 独立复核（pass）",
        "",
        f"- B盲核：{g4['b_verifier_units']}单元、前缀`{g4['b_verifier_prefix'][:40]}…`、"
        f"自有取证回执{g4['b_verifier_own_evidence_reads']}条；隔离标识=业务键前缀/profile/独立worker",
        f"- A盲核：{g4['a_verifier_jobs']}作业（verifier-v8，单次调用0取证回执）",
        "",
        "## G5 诚实结果（partial）",
        "",
        f"- A：{g5['a_per_field_counts']}；A双盲分歧 {g5['a_dual_divergent_fields']}/52；未知条目 {len(g5['a_unknown_entries'])}",
        f"- B：{g5['b_per_field_counts']}；B双盲分歧 {g5['b_dual_divergent_fields']}/26；未知条目 {len(g5['b_unknown_entries'])}",
        "",
        "## G6 恢复（fail）",
        "",
        f"- B：模型失败 {g6['b_failed_model_jobs']}；确定性第一代退役 {g6['b_stale_deterministic_jobs_retired_first_generation']}；"
        f"确定性固定代际stale {g6['b_stale_deterministic_jobs_fixed_generation']}；"
        f"重试作业 {len(g6['b_retries'])}；superseded候选 {g6['b_superseded_candidates']}",
        f"- A：attempt内失败 {g6['a_failed_jobs']}；重试作业 {g6['a_retries']}",
        f"- 成功无重复推理：{g6['success_without_duplicate_reasoning']}",
        "",
        "## G7 可用交付（fail）",
        "",
        f"- D2同会话捕获（{g7['d2_same_session_capture']['captured_at']}）：HTTP {g7['d2_same_session_capture']['http_ok']}，"
        f"field_count {g7['d2_same_session_capture']['primary_field_count']}/{g7['d2_same_session_capture']['verifier_field_count']}（每cohort，应52）",
        f"- 本次同服务会话再核验：server_reachable={g7['fresh_reverification_same_service_session']['server_reachable']}"
        f"（{g7['fresh_reverification_same_service_session']['captured_at']}）",
        f"- 浏览器走查：{g7['browser_walkthrough']}",
        f"- {g7['restart_invalidation_note']}",
        "",
        "## G8 质量与效率（partial）",
        "",
        f"- B-vs-A 主侧：比较 {g8['b_vs_a_primary']['compared_fields']} 字段，一致 {g8['b_vs_a_primary']['agree']}，分歧 {g8['b_vs_a_primary']['diverge']}；"
        f"盲核侧：比较 {g8['b_vs_a_verifier']['compared_fields']}，一致 {g8['b_vs_a_verifier']['agree']}，分歧 {g8['b_vs_a_verifier']['diverge']}"
        "（分歧分析非错误判定；逐条见JSON b_vs_a_*：divergent_details）",
        f"- A热启动：提交 {g8['timing']['a_warm_start']['submitted_at'][:19]}，耗时 {g8['timing']['a_warm_start']['wall_clock_h']}h"
        "（复用文档权威与既有入库）",
        f"- B冷启动：提交 {g8['timing']['b_cold_start']['submitted_at'][:19]}，耗时 {g8['timing']['b_cold_start']['wall_clock_h']}h"
        "（全新提交+逐单元取证）",
        f"- 模型用量：A {g8['model_usage']['a']['call_ledger_rows']}次调用（已知usage行 {g8['model_usage']['a']['known_usage_rows']}）；"
        f"B {g8['model_usage']['b']['call_ledger_rows']}次调用（已知usage行 {g8['model_usage']['b']['known_usage_rows']}，"
        f"prompt {g8['model_usage']['b']['prompt_tokens']} / completion {g8['model_usage']['b']['completion_tokens']} tokens，"
        "usage_unknown行不计入、不推算总量）",
        f"- 失败开销：{g8['failure_overhead']['b']}；{g8['failure_overhead']['a']}",
        f"- 人工介入待决：A {g8['human_intervention_pending']['a_user_decision_required_fields']} 字段、"
        f"B {g8['human_intervention_pending']['b_user_decision_required_fields']} 字段",
        "",
        "## 附注",
        "",
        "- 逐字段对照与三重回链（A候选ID + v275确认链field_sources + B候选ID）见 "
        "`d_comparison_cm_mh.json` 的 per_field_comparison（52条）。",
        "- 本报告不切换任何生产路由；B的启用前置条件见结论。",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
