"""Dual-cohort AE/MH cross-table analysis over materialized facts.

The primary cohort (role-marked prompt ``monitoring-cross-table-clue-
synthesis-v3``) and the independent blind verifier cohort (``...-verifier-v1``)
each receive the same subject-scoped frozen-source evidence built from the
verified fact artifacts. Adjudication pairs the two cohorts per subject:

- both cohorts propose an overlapping clue set  -> ``accepted`` finding
- cohorts disagree on a clue                    -> ``escalated`` (visible,
  never force-accepted)
- either side is missing or unverifiable        -> ``unverifiable_gap``

Findings are written as a content-addressed artifact under the facts
workspace; the facts publication mode outputs load them when present.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..intelligence.primitives import content_hash

VERIFIER_PROMPT_VERSION = "monitoring-cross-table-clue-synthesis-verifier-v1"
PRIMARY_PROMPT_VERSION = "monitoring-cross-table-clue-synthesis-v3"

# 证据域角色（与八轨一致；分析上下文以 AE/MH 为主，CM/EX 作伴随证据）
_DOMAIN_ROLE = {
    "AE": "不良事件原始记录",
    "MH": "既往病史原始记录",
    "CM": "非试验用合并用药或治疗",
    "EX": "试验药物给药与依从性",
}
_ANALYSIS_TABLES = ("AE", "MH", "CM", "EX2", "EX4", "EX5", "EX7")
_TABLE_DOMAIN = {"AE": "AE", "MH": "MH", "CM": "CM", "EX2": "EX", "EX4": "EX", "EX5": "EX", "EX7": "EX"}
_MAX_ROWS_PER_DOMAIN = 6
_MAX_FIELDS_PER_ROW = 24


@dataclass(frozen=True)
class AeMhSubmission:
    project_id: str
    primary_job_ids: tuple[str, ...]
    verifier_job_ids: tuple[str, ...]
    subject_ids: tuple[str, ...]


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def _compact_fields(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = []
    for key, value in row.items():
        text = _clean(value)
        if not text or key in {"Block顺序号", "RECREP", "PAGELMDT", "FORMOID", "FORMNM", "FORMNM__2"}:
            continue
        fields.append({"field": str(key), "value": text[:120]})
        if len(fields) >= _MAX_FIELDS_PER_ROW:
            break
    return fields


def build_subject_evidence(
    domains: Mapping[str, list[dict[str, Any]]],
    subject_label: str,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Build the frozen-source evidence packet for one subject."""

    evidence: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    for table in _ANALYSIS_TABLES:
        rows = domains.get(table, [])
        subject_rows = [
            (index, row)
            for index, row in enumerate(rows)
            if _clean(row.get("SUBJID")) == subject_label
        ]
        if not subject_rows:
            continue
        table_hash = content_hash({"table": table, "rows": len(rows)})
        source_hashes[table] = table_hash
        domain = _TABLE_DOMAIN[table]
        for index, row in subject_rows[:_MAX_ROWS_PER_DOMAIN]:
            fields = _compact_fields(row)
            locator = f"{table}!row{index + 1}"
            evidence_id = "aemh_{}".format(
                content_hash(
                    {"table": table, "row": index, "subject": subject_label}
                )[:28]
            )
            quote = "{} | {}".format(
                domain,
                "; ".join(f"{f['field']}={f['value']}" for f in fields[:16]),
            )[:8000]
            evidence.append(
                {
                    "evidence_id": evidence_id,
                    "source_entry_id": f"facts:{table}",
                    "source_content_sha256": table_hash,
                    "locator": locator,
                    "quote": quote,
                    "raw_fields": {
                        "evidence_kind": "original_listing_row",
                        "subject_id": subject_label,
                        "domain": domain,
                        "domain_role": _DOMAIN_ROLE[domain],
                        "business_key": f"{table}:{index}",
                        "row_fingerprint": content_hash(
                            {f["field"]: f["value"] for f in fields}
                        )[:40],
                        "fields": fields,
                    },
                }
            )
    present_domains = {item["raw_fields"]["domain"] for item in evidence}
    if len(present_domains) < 2:
        raise ValueError(
            f"受试者 {subject_label} 缺少至少两个分析域的证据（现有 {sorted(present_domains)}）"
        )
    return evidence, source_hashes


def submit_cohorts(
    *,
    primary_service: Any,
    verifier_service: Any,
    project_id: str,
    domains: Mapping[str, list[dict[str, Any]]],
    subject_labels: Sequence[str],
    facts_snapshot_ref: str,
    max_attempts: int = 2,
) -> AeMhSubmission:
    """Submit primary + blind verifier jobs for each subject."""

    from services.api.app.monitoring_ai_contracts import (  # noqa: PLC0415
        MonitoringAiTaskType,
    )

    primary_ids: list[str] = []
    verifier_ids: list[str] = []
    used: list[str] = []
    for subject_label in subject_labels:
        try:
            evidence, source_hashes = build_subject_evidence(domains, subject_label)
        except ValueError:
            continue
        from services.api.app.monitoring_ai_contracts import (  # noqa: PLC0415
            MonitoringAiInputRevision,
            MonitoringAiSourceBinding,
        )

        input_revision = MonitoringAiInputRevision(
            project_id=project_id,
            batch_revision=f"facts:{facts_snapshot_ref}",
            mapping_revision="facts-materialized",
            rule_pack_revision="facts-baseline-rules-v1",
            sources=tuple(
                MonitoringAiSourceBinding(
                    source_entry_id=f"facts:{table}",
                    source_content_sha256=digest,
                )
                for table, digest in sorted(source_hashes.items())
            ),
        )
        payload = {
            "subject_context": {
                "subject_id": subject_label,
                "batch_id": facts_snapshot_ref,
                "batch_version": 1,
                "mapping_revision": "facts-materialized",
                "rule_snapshot_id": "facts-baseline",
                "rule_pack_id": "facts-baseline-rules-v1",
                "rule_output_sha256": content_hash({"rules": "baseline"}),
                "selection_reasons": ["aemh_cross_analysis"],
                "domains": sorted({item["raw_fields"]["domain"] for item in evidence}),
                "domain_semantics": dict(_DOMAIN_ROLE),
                "medical_boundary": (
                    "仅生成待当前医学用户复核的跨表线索；不得自动判定"
                    "AE/MH漏报、方案违背或生成Query。"
                ),
            },
            "evidence_packet": evidence,
        }
        primary_ids.append(
            primary_service.submit_task(
                project_id=project_id,
                task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
                input_revision=input_revision,
                input_payload=payload,
                business_key=f"aemh:{facts_snapshot_ref}:primary:{subject_label}",
                prompt_version=PRIMARY_PROMPT_VERSION,
                max_attempts=max_attempts,
            ).job_id
        )
        verifier_ids.append(
            verifier_service.submit_task(
                project_id=project_id,
                task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
                input_revision=input_revision,
                input_payload=payload,
                business_key=f"aemh:{facts_snapshot_ref}:verifier:{subject_label}",
                prompt_version=VERIFIER_PROMPT_VERSION,
                max_attempts=max_attempts,
            ).job_id
        )
        used.append(subject_label)
    return AeMhSubmission(
        project_id=project_id,
        primary_job_ids=tuple(primary_ids),
        verifier_job_ids=tuple(verifier_ids),
        subject_ids=tuple(used),
    )


__all__ = [
    "AeMhSubmission",
    "PRIMARY_PROMPT_VERSION",
    "VERIFIER_PROMPT_VERSION",
    "build_subject_evidence",
    "submit_cohorts",
]
