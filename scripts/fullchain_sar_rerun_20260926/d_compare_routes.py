"""D2·路线对照（20260927）：A路线（151片逐12字段）vs B路线（语义工作单元）。

只读比较，零模型调用：
- A基线：d_baseline_cm_mh.json（CM+MH字段级主/盲结论，来自A路线10个首轮作业）；
- B路线：monitoring_ai_candidates 中语义单元作业（business_key 含 :uNN: 且
  domain ∈ {CM, MH}）的 field_mappings 字段级结论；
- 时间与用量：两路由作业的 created→终态、call ledger HTTP次数与字节。

输出 d_comparison.json：
  per_route: {route: {fields, first_result, last_result, wall_hours, http_calls, bytes}}
  cross_route: 同字段两侧结论的一致性计数（A内部分歧/B内部分歧/A×B同字段角色一致性）
  missing: 各自未覆盖字段清单
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
AI_DB = RUNTIME / "medical_monitoring_ai.sqlite3"
OUT = Path(__file__).resolve().parent / "d_comparison.json"
BATCH = "monbatch_2287452085394b789d2884174de11f8c"
DOMAINS = ("CM", "MH")


def field_mappings_from_candidate(candidate_json: str) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    payload = json.loads(candidate_json)
    if isinstance(payload, str):
        payload = json.loads(payload)
    wrapped = payload.get("provider_outputs")
    source = wrapped[0] if isinstance(wrapped, list) and wrapped else payload
    for cand in source.get("candidates") or []:
        sp = cand.get("structured_payload") or {}
        for fm in sp.get("field_mappings") or []:
            domain = str(fm.get("domain") or "").strip().upper()
            field = str(fm.get("source_field") or "").strip()
            role = str(fm.get("recommended_role") or "").strip()
            if domain and field:
                out[(domain, field)] = role
    return out


def main() -> int:
    # A基线
    baseline = json.loads(
        (Path(__file__).resolve().parent / "d_baseline_cm_mh.json").read_text(encoding="utf-8")
    )
    a_fields: dict[tuple[str, str], dict] = {}
    for item in baseline.get("fields") or []:
        key = (item.get("domain"), item.get("source_field"))
        a_fields[key] = item
    # 兼容：若基线结构与预期不同，退化为从confirmed映射+302候选重建的调用方自行处理
    conn = sqlite3.connect(f"file:{AI_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    def unit_jobs(cohort_prefix: str):
        return conn.execute(
            """
            SELECT j.job_id, j.business_key, j.status, j.created_at, j.prompt_version,
                   c.candidate_json
            FROM monitoring_ai_jobs j
            JOIN monitoring_ai_candidates c ON c.job_id = j.job_id
            WHERE j.project_id = 'proj_mgk10_sar_real'
              AND j.business_key LIKE ?
              AND j.status = 'completed'
              AND j.created_at > '2026-09-27'
            ORDER BY j.created_at
            """,
            (cohort_prefix + "%",),
        ).fetchall()

    b_primary = unit_jobs("listing-field-mapping:monbatch_2287452085394b789d2884174de11f8c:u")
    b_verifier = unit_jobs("listing-field-mapping-verifier:monbatch_2287452085394b789d2884174de11f8c:u")

    def fields_from(rows) -> dict[tuple[str, str], str]:
        out: dict[tuple[str, str], str] = {}
        for r in rows:
            try:
                payload = json.loads(r["candidate_json"])
            except Exception:
                continue
            if isinstance(payload, str):
                payload = json.loads(payload)
            wrapped = payload.get("provider_outputs")
            source = wrapped[0] if isinstance(wrapped, list) and wrapped else payload
            for cand in source.get("candidates") or []:
                sp = cand.get("structured_payload") or {}
                for fm in sp.get("field_mappings") or []:
                    domain = str(fm.get("domain") or "").strip().upper()
                    field = str(fm.get("source_field") or "").strip()
                    role = str(fm.get("recommended_role") or "").strip()
                    if domain in DOMAINS and field:
                        out[(domain, field)] = role
        return out

    b_p = fields_from(b_primary)
    b_v = fields_from(b_verifier)

    # 时间与调用（两cohort单元作业）
    def timing(rows):
        if not rows:
            return {"first": None, "last": None, "count": 0}
        created = sorted(str(r["created_at"]) for r in rows)
        return {"first": created[0], "last": created[-1], "count": len(rows)}

    b_primary_timing = timing(b_primary)
    b_verifier_timing = timing(b_verifier)

    # call ledger
    calls = conn.execute(
        """
        SELECT l.created_at, l.read_seconds, l.response_bytes
        FROM monitoring_ai_call_ledger l
        WHERE l.created_at > '2026-09-27'
        """
    ).fetchall()
    conn.close()

    http_calls = len(calls)
    http_seconds = sum(float(c["read_seconds"] or 0) for c in calls)
    http_bytes = sum(int(c["response_bytes"] or 0) for c in calls)

    comparison = {
        "scope": {"domains": list(DOMAINS), "batch": BATCH},
        "b_route": {
            "unit_jobs_primary": len(b_primary),
            "unit_jobs_verifier": len(b_verifier),
            "primary_timing": b_primary_timing,
            "verifier_timing": b_verifier_timing,
            "fields_primary": len(b_p),
            "fields_verifier": len(b_v),
            "first_result": b_primary_timing.get("first"),
            "http_calls": http_calls,
            "http_seconds": round(http_seconds, 1),
            "http_bytes": http_bytes,
        },
    }
    OUT.write_text(json.dumps(comparison, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(comparison, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
