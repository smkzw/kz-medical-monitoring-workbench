#!/usr/bin/env python3
"""D1·A路线基线提取（只读）：SAR冻结批次 CM+MH 域的字段级结论导出。

数据源（sqlite3 mode=ro 只读打开，零写操作、零模型调用、不重跑A路线）：
- runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_ai.sqlite3
    ① A基线：monitoring_ai_candidates.candidate_json 的
      structured_payload.field_mappings（作业表无structured_payload列）。
      按 business_key 定位恰10个 completed 首轮作业（同键存在更早的
      stale_input 代际行，必须过滤 status='completed'）：
        主   listing-field-mapping:{attempt}:{CM,MH}:0001-of-000N   (v19)
        盲核 listing-field-mapping-verifier:{attempt}:{CM,MH}:...   (v8-tools-v6)
    ② 确认基线：monitoring_mapping_drafts（status=confirmed, version=275）
      + monitoring_mapping_revisions.field_sources_json。
- runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_batches.sqlite3
    ③ 冻结四元组：content_sha256 / row_set_sha256 / schema_fields_sha256 /
      attempt_id，逐一在批库锚点定位（content_objects 与 batch_events.payload）。

输出（④）：d_baseline_cm_mh.json，对齐键=(domain, source_field)；每字段主/盲核
结论条数（0/1/N）、分歧标记与原因、未知field_kind单列（五类边界词表之外的
field_kind 如实单列，不混入分歧计数）；分侧字段清单如实记录（两侧字段集与
元数据计数本就不同，不做并集合并）。

本脚本不把A路线当参考答案：导出的是两侧各自结论与分歧，供D切片对照使用。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = (
    WORKBENCH_ROOT / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"
)
AI_DB = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
BATCH_DB = RUNTIME_DIR / "medical_monitoring_batches.sqlite3"
DEFAULT_OUT = Path(__file__).resolve().parent / "d_baseline_cm_mh.json"

ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"
PRIMARY_PREFIX = f"listing-field-mapping:{ATTEMPT_ID}:"
VERIFIER_PREFIX = f"listing-field-mapping-verifier:{ATTEMPT_ID}:"
DOMAINS = ("CM", "MH")
# 五类field_kind边界词表（FIELD_MAPPING_SCIENTIFIC_BOUNDARY.field_layers）；
# 之外的field_kind属未知结论，单列记录、不参与分歧归并。
KNOWN_FIELD_KINDS = frozenset({
    "source_collected",
    "source_metadata",
    "standardized_coded",
    "deterministic_derived",
    "unmapped",
})
DRAFT_ID = "monmapdraft_da52157f3ed6f42405d0de95d8be"
REVISION_ID = "monmaprev_185410413d17078e8c6e83070e21"
# 四元组锚点前缀（approach给定），全值从批库逐字取回。
CONTENT_SHA_PREFIX = "81f47614"
ROW_SET_SHA_PREFIX = "57522501"
SCHEMA_FIELDS_SHA_PREFIX = "4bdf4887"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        FAILURES.append(name)
        print(f"FAIL {name} {detail}")


def open_ro(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def count_label(count: int) -> str:
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    return "N"


def entry_view(mapping: dict) -> dict:
    return {
        "recommended_role": mapping.get("recommended_role"),
        "field_kind": mapping.get("field_kind"),
        "confidence": mapping.get("confidence"),
        "user_decision_required": bool(mapping.get("user_decision_required", False)),
    }


def main() -> int:
    print(f"AI库: {AI_DB}")
    print(f"批库: {BATCH_DB}")
    check("databases-exist", AI_DB.exists() and BATCH_DB.exists())
    ai = open_ro(AI_DB)
    batch = open_ro(BATCH_DB)

    # ---------------------------------------------------------------- ① A基线
    like = " OR ".join(
        f"business_key LIKE '{prefix}{domain}:%'"
        for prefix in (PRIMARY_PREFIX, VERIFIER_PREFIX)
        for domain in DOMAINS
    )
    generations = ai.execute(
        f"SELECT business_key, status, job_id, prompt_version "
        f"FROM monitoring_ai_jobs WHERE {like} ORDER BY business_key, created_at"
    ).fetchall()
    completed = [row for row in generations if row["status"] == "completed"]
    stale = [row for row in generations if row["status"] != "completed"]
    check("exactly-10-completed-jobs", len(completed) == 10, f"got {len(completed)}")
    check("stale-generations-present-and-filtered", len(stale) == 10, f"got {len(stale)}")
    check(
        "one-completed-row-per-business-key",
        len({row["business_key"] for row in completed}) == 10,
    )
    check(
        "cohort-prompts-match-frozen-generations",
        {row["prompt_version"] for row in completed}
        == {
            "monitoring-listing-field-mapping-v19",
            "monitoring-listing-field-mapping-verifier-v8-tools-v6",
        },
        str({row["prompt_version"] for row in completed}),
    )

    candidate_rows = ai.execute(
        f"SELECT j.business_key, j.job_id, j.prompt_version, c.candidate_id, "
        f"c.candidate_json FROM monitoring_ai_jobs j "
        f"JOIN monitoring_ai_candidates c ON c.job_id = j.job_id "
        f"WHERE j.status = 'completed' AND ({like}) ORDER BY j.business_key"
    ).fetchall()
    check("one-candidate-per-completed-job", len(candidate_rows) == 10,
          f"got {len(candidate_rows)}")

    sides: dict[str, dict[str, dict[str, list]]] = {
        "primary": {domain: {} for domain in DOMAINS},
        "verifier": {domain: {} for domain in DOMAINS},
    }
    job_records = []
    total_mappings = 0
    chunk_counts: dict[str, int] = {}
    for row in candidate_rows:
        business_key = row["business_key"]
        cohort = (
            "verifier"
            if business_key.startswith("listing-field-mapping-verifier:")
            else "primary"
        )
        payload = json.loads(row["candidate_json"])
        mappings = payload["structured_payload"]["field_mappings"]
        total_mappings += len(mappings)
        # business_key 尾段: {attempt}:{domain}:{index}-of-{total}
        tail = business_key.rsplit(":", 2)
        domain = tail[1]
        index, chunk_total = tail[2].split("-of-")
        chunk_counts[(cohort, domain, index, chunk_total)] = len(mappings)
        for mapping in mappings:
            sides[cohort][domain].setdefault(
                str(mapping["source_field"]).strip(), []
            ).append(mapping)
        job_records.append({
            "business_key": business_key,
            "job_id": row["job_id"],
            "prompt_version": row["prompt_version"],
            "candidate_id": row["candidate_id"],
            "domain": domain,
            "chunk": f"{index}-of-{chunk_total}",
            "mapping_count": len(mappings),
        })

    check("field-mappings-total-104", total_mappings == 104, f"got {total_mappings}")
    check(
        "cm-last-chunk-8-not-full-12",
        chunk_counts.get(("primary", "CM", "0003", "0003")) == 8
        and chunk_counts.get(("verifier", "CM", "0003", "0003")) == 8,
        str({k: v for k, v in chunk_counts.items() if k[1] == "CM" and k[2] == "0003"}),
    )
    for cohort in ("primary", "verifier"):
        for domain in DOMAINS:
            expected = 32 if domain == "CM" else 20
            got = len(sides[cohort][domain])
            check(
                f"field-inventory-{cohort}-{domain}=={expected}",
                got == expected,
                f"got {got}",
            )
    per_side_metadata_counts = {
        cohort: {
            domain: sum(
                1
                for entries in sides[cohort][domain].values()
                for entry in entries
                if entry.get("field_kind") == "source_metadata"
            )
            for domain in DOMAINS
        }
        for cohort in ("primary", "verifier")
    }
    check("primary-cm-metadata-14-with-SUBJSTA",
          per_side_metadata_counts["primary"]["CM"] == 14
          and "SUBJSTA" in sides["primary"]["CM"],
          str(per_side_metadata_counts))
    check("verifier-cm-metadata-13-without-SUBJSTA",
          per_side_metadata_counts["verifier"]["CM"] == 13
          and "SUBJSTA" in sides["verifier"]["CM"],
          str(per_side_metadata_counts))

    # ------------------------------------------------ ② 确认基线（AI库）
    draft = ai.execute(
        "SELECT * FROM monitoring_mapping_drafts WHERE draft_id = ?", (DRAFT_ID,)
    ).fetchone()
    check("draft-exists-confirmed-v275",
          draft is not None and draft["status"] == "confirmed"
          and int(draft["version"]) == 275,
          str(draft["status"]) if draft is not None else "missing")
    check("draft-batch-is-attempt", draft["batch_id"] == ATTEMPT_ID)
    revision = ai.execute(
        "SELECT * FROM monitoring_mapping_revisions WHERE mapping_revision = ?",
        (REVISION_ID,),
    ).fetchone()
    check("revision-exists", revision is not None)
    check("revision-bound-to-draft-v275",
          revision["draft_id"] == DRAFT_ID and int(revision["draft_version"]) == 275)
    field_sources = json.loads(revision["field_sources_json"])
    field_source_chars = len(revision["field_sources_json"])
    check("field-sources-1495-entries-660980-chars",
          len(field_sources) == 1495 and field_source_chars == 660980,
          f"entries={len(field_sources)} chars={field_source_chars}")
    draft_fields = json.loads(draft["fields_json"])
    spot = {}
    for field in draft_fields:
        if field.get("domain") in DOMAINS and field.get("source_field") in (
            "CMTRT", "MHTERM", "CMDOSFRQ",
        ):
            spot[field["source_field"]] = field.get("confidence")
    check("v275-spot-checks",
          abs(spot.get("CMTRT", 0) - 0.93) < 1e-9
          and abs(spot.get("MHTERM", 0) - 0.93) < 1e-9
          and abs(spot.get("CMDOSFRQ", 0) - 0.55) < 1e-9,
          str(spot))

    # ------------------------------------------------ ③ 冻结四元组（批库）
    content = batch.execute(
        "SELECT content_sha256, size_bytes, blob_relative_path FROM "
        "monitoring_content_objects WHERE content_sha256 LIKE ?",
        (CONTENT_SHA_PREFIX + "%",),
    ).fetchall()
    check("content-sha-anchor-unique", len(content) == 1, f"got {len(content)}")
    content_sha = content[0]["content_sha256"]
    events = batch.execute(
        "SELECT event_seq, batch_id, event_type, payload_json FROM "
        "monitoring_batch_events WHERE payload_json LIKE ? AND payload_json LIKE ?",
        (f'%"{ROW_SET_SHA_PREFIX}%', f'%"{SCHEMA_FIELDS_SHA_PREFIX}%'),
    ).fetchall()
    check("batch-event-anchor-unique", len(events) == 1, f"got {len(events)}")
    event_payload = json.loads(events[0]["payload_json"])
    row_set_sha = str(event_payload.get("row_set_sha256", ""))
    schema_fields_sha = str(event_payload.get("schema_fields_sha256", ""))
    check("row-set-sha-prefix-matches",
          row_set_sha.startswith(ROW_SET_SHA_PREFIX), row_set_sha[:16])
    check("schema-fields-sha-prefix-matches",
          schema_fields_sha.startswith(SCHEMA_FIELDS_SHA_PREFIX), schema_fields_sha[:16])
    frozen_quadruple = {
        "attempt_id": ATTEMPT_ID,
        "content_sha256": content_sha,
        "content_sha256_location": "monitoring_content_objects.content_sha256",
        "content_size_bytes": int(content[0]["size_bytes"]),
        "row_set_sha256": row_set_sha,
        "row_set_sha256_location": (
            f"monitoring_batch_events.payload_json (event_seq="
            f"{events[0]['event_seq']}, event_type={events[0]['event_type']})"
        ),
        "schema_fields_sha256": schema_fields_sha,
        "schema_fields_sha256_location": (
            f"monitoring_batch_events.payload_json (event_seq="
            f"{events[0]['event_seq']})"
        ),
        "schema_field_count": event_payload.get("schema_field_count"),
    }

    # ------------------------------------------------ ④ 分歧与未知（G5口径）
    divergence_fields = []
    unknown_entries = []
    divergent_count = 0
    for domain in DOMAINS:
        all_fields = sorted(
            set(sides["primary"][domain]) | set(sides["verifier"][domain]),
        )
        for source_field in all_fields:
            primary_entries = sides["primary"][domain].get(source_field, [])
            verifier_entries = sides["verifier"][domain].get(source_field, [])
            primary_label = count_label(len(primary_entries))
            verifier_label = count_label(len(verifier_entries))
            for cohort, entries in (
                ("primary", primary_entries), ("verifier", verifier_entries),
            ):
                for entry in entries:
                    if entry.get("field_kind") not in KNOWN_FIELD_KINDS:
                        unknown_entries.append({
                            "cohort": cohort,
                            "domain": domain,
                            "source_field": source_field,
                            "field_kind": entry.get("field_kind"),
                            "recommended_role": entry.get("recommended_role"),
                        })
            primary_key = frozenset(
                (entry.get("recommended_role"), entry.get("field_kind"))
                for entry in primary_entries
            )
            verifier_key = frozenset(
                (entry.get("recommended_role"), entry.get("field_kind"))
                for entry in verifier_entries
            )
            reasons = []
            if primary_label != verifier_label:
                reasons.append(f"count:{primary_label}-vs-{verifier_label}")
            if primary_key != verifier_key:
                reasons.append("role_or_kind_mismatch")
            divergent = bool(reasons)
            divergent_count += int(divergent)
            divergence_fields.append({
                "domain": domain,
                "source_field": source_field,
                "primary_count": primary_label,
                "verifier_count": verifier_label,
                "primary": [entry_view(entry) for entry in primary_entries],
                "verifier": [entry_view(entry) for entry in verifier_entries],
                "divergent": divergent,
                "divergence_reasons": reasons,
            })

    # ------------------------------------------------ ④ 输出
    report = {
        "schema_version": "d-baseline-cm-mh-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "route": "A",
        "mode": "read_only",
        "caveats": (
            "A路线结论是对照基线之一，不是参考答案；分侧字段清单如实记录，"
            "两侧字段集与元数据分类本就不同（如主侧CM含SUBJSTA=source_metadata、"
            "盲核侧为source_collected），不做并集归并。"
        ),
        "databases": {
            "ai": str(AI_DB.relative_to(WORKBENCH_ROOT)),
            "batches": str(BATCH_DB.relative_to(WORKBENCH_ROOT)),
            "opened_mode": "sqlite3 mode=ro",
        },
        "frozen_quadruple": frozen_quadruple,
        "totals": {
            "completed_jobs": len(completed),
            "stale_generations_filtered": len(stale),
            "field_mappings": total_mappings,
            "cm_fields_per_side": {
                cohort: len(sides[cohort]["CM"]) for cohort in sides
            },
            "mh_fields_per_side": {
                cohort: len(sides[cohort]["MH"]) for cohort in sides
            },
            "per_side_metadata_counts": per_side_metadata_counts,
        },
        "jobs": job_records,
        "sides": {
            cohort: {
                domain: {
                    source_field: [entry_view(e) for e in entries]
                    for source_field, entries in sorted(sides[cohort][domain].items())
                }
                for domain in DOMAINS
            }
            for cohort in ("primary", "verifier")
        },
        "divergence": {
            "alignment_key": "(domain, source_field)",
            "criteria": (
                "count 0/1/N per side；divergent=两侧条数不同 或 (role,field_kind)"
                "集合不同；未知field_kind（五类边界词表外）单列不计入分歧"
            ),
            "divergent_count": divergent_count,
            "unknown_entries": unknown_entries,
            "fields": divergence_fields,
        },
        "confirmed_baseline": {
            "draft_id": DRAFT_ID,
            "status": draft["status"],
            "version": int(draft["version"]),
            "confirmed_revision_id": REVISION_ID,
            "batch_id": draft["batch_id"],
            "full_profile_sha256": draft["full_profile_sha256"],
            "full_input_sha256": draft["full_input_sha256"],
            "fields_json_chars": len(draft["fields_json"]),
            "fields_json_entries": len(draft_fields),
            "field_sources_json_chars": field_source_chars,
            "field_sources_entries": len(field_sources),
            "confidence_spot_checks": spot,
        },
        "self_check": {
            "cm_fields_both_sides": 32,
            "mh_fields_both_sides": 20,
            "completed_jobs": len(completed),
            "field_mappings_total": total_mappings,
            "cm_last_chunk_mappings": 8,
            "v275_spot_checks": spot,
            "per_side_metadata_counts": per_side_metadata_counts,
            "failures": FAILURES,
        },
    }
    ai.close()
    batch.close()

    if FAILURES:
        print(f"SELF-CHECK FAILED: {FAILURES}")
        return 1
    report["self_check"]["status"] = "pass"
    output_path = DEFAULT_OUT
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8",
    )
    print(f"输出: {output_path}")
    print("D1 SELF-CHECK: ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
