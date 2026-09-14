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
                        "evidence_kind": "original_data",
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
                "analysis_contract": (
                    "每个线索候选的claims.evidence_ids必须合计引用至少两个"
                    "不同domain（如AE+MH、CM+EX、AE+CM）的evidence_id；"
                    "只引用单一domain证据的候选会被系统直接拒绝。"
                    "evidence_packet每条证据的raw_fields.domain标明了所属域。"
                    "AE强度、严重性、预期性、因果性与监查优先级必须分开表述，"
                    "不得合并；证据不足时输出data_gap主张，不得补造。"
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


def _clue_fingerprint(candidate: Any) -> frozenset[str]:
    """Structural fingerprint: the original-evidence ids one clue cites."""
    return frozenset(
        item.evidence_id for item in getattr(candidate, "evidence", ())
    )


def _finding_text(candidate: Any) -> dict[str, Any]:
    payload = getattr(candidate, "structured_payload", {}) or {}
    return {
        "title": str(getattr(candidate, "title", "") or "")[:200],
        "text": str(getattr(candidate, "text", "") or "")[:2000],
        "domains": list(payload.get("domains", []) or []),
        "payload": payload,
    }


def adjudicate(
    *,
    ai_repository: Any,
    project_id: str,
    subject_labels: Sequence[str],
    facts_snapshot_ref: str,
    primary_job_by_subject: Mapping[str, str],
    verifier_job_by_subject: Mapping[str, str],
    artifacts_dir: Path,
) -> dict[str, Any]:
    """Pair the two cohorts per subject into visible findings.

    Conservative structural matching only: a primary clue and a verifier clue
    agree when they cite at least one shared original evidence row. Unpaired
    clues from either cohort stay ``escalated`` (never force-accepted); a
    subject whose cohort job did not complete stays ``unverifiable_gap``.
    """

    findings: list[dict[str, Any]] = []
    cohort_status: dict[str, dict[str, str]] = {}
    for subject_label in subject_labels:
        primary_id = primary_job_by_subject.get(subject_label, "")
        verifier_id = verifier_job_by_subject.get(subject_label, "")
        primary_candidates = (
            ai_repository.candidates(project_id, primary_id)
            if primary_id
            else ()
        )
        verifier_candidates = (
            ai_repository.candidates(project_id, verifier_id)
            if verifier_id
            else ()
        )
        primary_job = (
            ai_repository.get(project_id, primary_id) if primary_id else None
        )
        verifier_job = (
            ai_repository.get(project_id, verifier_id) if verifier_id else None
        )
        cohort_status[subject_label] = {
            "primary_job": primary_id,
            "primary_state": str(getattr(primary_job, "status", "missing")),
            "verifier_job": verifier_id,
            "verifier_state": str(getattr(verifier_job, "status", "missing")),
        }
        if not primary_candidates and not verifier_candidates:
            findings.append(
                {
                    "subject_label": subject_label,
                    "state": "unverifiable_gap",
                    "reason_zh": "双cohort均无可用候选（未完成或输出无效），本轮不可核实。",
                    "primary": None,
                    "verifier": None,
                }
            )
            continue
        used_verifier: set[str] = set()
        for primary_clue in primary_candidates:
            primary_text = _finding_text(primary_clue)
            primary_evidence = _clue_fingerprint(primary_clue)
            matched_verifier = None
            for verifier_clue in verifier_candidates:
                if verifier_clue.candidate_id in used_verifier:
                    continue
                if primary_evidence & _clue_fingerprint(verifier_clue):
                    matched_verifier = verifier_clue
                    break
            if matched_verifier is not None:
                used_verifier.add(matched_verifier.candidate_id)
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "accepted",
                        "reason_zh": "主分析与独立盲核均引用相同原始记录，线索成立，待医学复核。",
                        "primary": primary_text,
                        "verifier": _finding_text(matched_verifier),
                    }
                )
            else:
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "escalated",
                        "reason_zh": "仅主分析提出该线索，独立盲核未引用相同原始记录；不得强行接受，请医学监察员裁决。",
                        "primary": primary_text,
                        "verifier": None,
                    }
                )
        for verifier_clue in verifier_candidates:
            if verifier_clue.candidate_id in used_verifier:
                continue
            findings.append(
                {
                    "subject_label": subject_label,
                    "state": "escalated",
                    "reason_zh": "仅独立盲核提出该线索（主分析遗漏）；不得强行接受，请医学监察员裁决。",
                    "primary": None,
                    "verifier": _finding_text(verifier_clue),
                }
            )
    accepted = sum(1 for item in findings if item["state"] == "accepted")
    escalated = sum(1 for item in findings if item["state"] == "escalated")
    gaps = sum(1 for item in findings if item["state"] == "unverifiable_gap")
    artifact = {
        "kind": "aemh_cross_findings",
        "snapshot_ref": facts_snapshot_ref,
        "project_id": project_id,
        "prompt_versions": {
            "primary": PRIMARY_PROMPT_VERSION,
            "verifier": VERIFIER_PROMPT_VERSION,
        },
        "counts": {
            "accepted": accepted,
            "escalated": escalated,
            "unverifiable_gap": gaps,
        },
        "cohort_status": cohort_status,
        "findings": findings,
    }
    digest = content_hash(artifact)
    artifact["content_sha256"] = digest
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / f"aemh-findings-{facts_snapshot_ref}.json").write_text(
        json.dumps(artifact, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return artifact


__all__ = [
    "AeMhSubmission",
    "PRIMARY_PROMPT_VERSION",
    "VERIFIER_PROMPT_VERSION",
    "adjudicate",
    "build_subject_evidence",
    "submit_cohorts",
]
