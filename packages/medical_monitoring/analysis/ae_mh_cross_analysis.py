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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

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


_PROFILE_CACHE: dict[str, Any] = {"signature": None, "profile": None}


def _protocol_profile_payload(workspace: Path | None) -> dict[str, Any] | None:
    """Load the project's protocol/IB profile (cached per process).

    Injected into every analysis job so models know the CTCAE grading
    version, MedDRA version and the drug-background risk direction —
    derived from documents, never hard-coded per project.
    """
    from .protocol_profile import load_or_build_profile  # noqa: PLC0415

    if workspace is None or not workspace.is_dir():
        return None
    try:
        signature = str(workspace)
        if _PROFILE_CACHE["signature"] == signature and _PROFILE_CACHE["profile"] is not None:
            profile = _PROFILE_CACHE["profile"]
        else:
            profile = load_or_build_profile(workspace)
            _PROFILE_CACHE.update(signature=signature, profile=profile)
    except Exception:
        return None
    if profile is None:
        return None
    payload = profile.to_payload()
    if payload.get("unknown_visible"):
        # 覆盖不足可见：没有方案证据时显式告知模型不要假设分级标准。
        return {
            "note_zh": "方案/IB尚未注册或未识别到分级标准版本；不要假设CTCAE版本，严重程度按原始记录表述。",
            "unknown_visible": True,
        }
    return payload


def _layout_payload(workspace: Path | None) -> dict[str, Any] | None:
    """Load the listing layout profile and project the contract summary."""

    from .listing_layout import layout_artifact_path, layout_summary_for_contract  # noqa: PLC0415

    if workspace is None or not workspace.is_dir():
        return None
    artifact = layout_artifact_path(workspace)
    if not artifact.is_file():
        return None
    try:
        import json as _json

        profile = _json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return layout_summary_for_contract(profile)


def submit_cohorts(
    *,
    primary_service: Any,
    verifier_service: Any,
    project_id: str,
    domains: Mapping[str, list[dict[str, Any]]],
    subject_labels: Sequence[str],
    facts_snapshot_ref: str,
    max_attempts: int = 2,
    protocol_workspace: Optional[Path] = None,
) -> AeMhSubmission:
    """Submit primary + blind verifier jobs for each subject."""

    from services.api.app.monitoring_ai_contracts import (  # noqa: PLC0415
        MonitoringAiTaskType,
    )

    primary_ids: list[str] = []
    verifier_ids: list[str] = []
    used: list[str] = []
    profile_payload = _protocol_profile_payload(protocol_workspace)
    layout_payload = _layout_payload(protocol_workspace)
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
                "protocol_profile": profile_payload,
                "listing_layout": layout_payload,
                "analysis_contract": (
                    "每个线索候选的claims.evidence_ids必须合计引用至少两个"
                    "不同domain（如AE+MH、CM+EX、AE+CM）的evidence_id；"
                    "只引用单一domain证据的候选会被系统直接拒绝。"
                    "evidence_packet每条证据的raw_fields.domain标明了所属域。"
                    "AE强度、严重性、预期性、因果性与监查优先级必须分开表述，"
                    "不得合并；严重程度表述必须遵循subject_context."
                    "protocol_profile.ctcae_version对应的分级标准（若"
                    "unknown_visible为true则按原始记录表述并标注口径未知）；"
                    "证据不足时输出data_gap候选，不得补造。"
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


_ENTITY_RE = re.compile(r"[\u4e00-\u9fa5]{2,8}|[A-Za-z][A-Za-z0-9-]{2,14}")


def _clue_entities(candidate: Any) -> frozenset[str]:
    """Medical-entity words cited in a clue's title/text/claims."""
    payload = getattr(candidate, "structured_payload", {}) or {}
    parts = [
        str(getattr(candidate, "title", "") or ""),
        str(getattr(candidate, "text", "") or ""),
    ]
    for claim in payload.get("claims", []) or []:
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    words: set[str] = set()
    for part in parts:
        words.update(_ENTITY_RE.findall(part[:1200]))
    return frozenset(words)


def _clue_domain_pair(candidate: Any) -> frozenset[str]:
    payload = getattr(candidate, "structured_payload", {}) or {}
    return frozenset(str(d).upper() for d in payload.get("domains", []) or [])


def _clues_agree(primary: Any, verifier: Any) -> bool:
    """Pairing: shared evidence rows, or same domain-pair with shared entities.

    Two independent models often cite different rows of the same subject while
    describing the same finding (e.g. both discuss the hypertension history,
    one citing MH rows and the other CM rows). Evidence overlap alone would
    mis-file those as disagreements.
    """
    if _clue_fingerprint(primary) & _clue_fingerprint(verifier):
        return True
    domains = _clue_domain_pair(primary) & _clue_domain_pair(verifier)
    if not domains:
        return False
    shared = _clue_entities(primary) & _clue_entities(verifier)
    # 共享≥2个医学实体词（如"高血压"+"剂量"）视为同一发现的不同表述；
    # 单个常见词（"受试者""记录"等）不足以配对。
    return len(shared) >= 2


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
        # 单侧cohort未完成 = 覆盖缺口而非分歧：对侧没有表达任何不同意见，
        # 不应按"待用户裁决"推给医学用户；标记为待补核（重试/定向核实轮兜底）。
        primary_failed = bool(primary_id) and not primary_candidates
        verifier_failed = bool(verifier_id) and not verifier_candidates
        used_verifier: set[str] = set()
        for primary_clue in primary_candidates:
            primary_text = _finding_text(primary_clue)
            matched_verifier = None
            for verifier_clue in verifier_candidates:
                if verifier_clue.candidate_id in used_verifier:
                    continue
                if _clues_agree(primary_clue, verifier_clue):
                    matched_verifier = verifier_clue
                    break
            if matched_verifier is not None:
                used_verifier.add(matched_verifier.candidate_id)
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "accepted",
                        "reason_zh": "主分析与独立盲核均确认该线索（相同原始记录或同一发现的两种表述），待医学复核。",
                        "primary": primary_text,
                        "verifier": _finding_text(matched_verifier),
                    }
                )
            elif verifier_failed:
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "coverage_gap",
                        "reason_zh": "盲核cohort本轮未完成，该线索尚缺独立核对（非分歧），待补核后自动定级。",
                        "primary": primary_text,
                        "verifier": None,
                    }
                )
            else:
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "escalated",
                        "reason_zh": "仅主分析提出该线索，独立盲核未确认同一发现；请医学监察员核对。",
                        "primary": primary_text,
                        "verifier": None,
                    }
                )
        for verifier_clue in verifier_candidates:
            if verifier_clue.candidate_id in used_verifier:
                continue
            verifier_text = _finding_text(verifier_clue)
            if primary_failed:
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "coverage_gap",
                        "reason_zh": "主分析cohort本轮未完成，该线索尚缺独立核对（非分歧），待补核后自动定级。",
                        "primary": None,
                        "verifier": verifier_text,
                    }
                )
            else:
                findings.append(
                    {
                        "subject_label": subject_label,
                        "state": "escalated",
                        "reason_zh": "仅独立盲核提出该线索（主分析未覆盖），请医学监察员核对。",
                        "primary": None,
                        "verifier": verifier_text,
                    }
                )
    accepted = sum(1 for item in findings if item["state"] == "accepted")
    escalated = sum(1 for item in findings if item["state"] == "escalated")
    gaps = sum(1 for item in findings if item["state"] in ("unverifiable_gap", "coverage_gap"))
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
            "coverage_gap": sum(1 for item in findings if item["state"] == "coverage_gap"),
            "unverifiable_gap": sum(1 for item in findings if item["state"] == "unverifiable_gap"),
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


def submit_focused_verifications(
    *,
    verifier_service: Any,
    project_id: str,
    domains: Mapping[str, list[dict[str, Any]]],
    escalated: Sequence[Mapping[str, Any]],
    facts_snapshot_ref: str,
    max_attempts: int = 2,
) -> tuple[str, ...]:
    """Focused second-round verification for one-sided findings.

    For each escalated clue (proposed by only one cohort), the OPPOSITE
    model receives the same subject evidence packet plus a focused
    instruction: confirm the observation against the rows, or refute it with
    a data_gap candidate. The harness then re-pairs; only genuine refusals
    remain escalated for the human reviewer.
    """

    from services.api.app.monitoring_ai_contracts import (  # noqa: PLC0415
        MonitoringAiInputRevision,
        MonitoringAiSourceBinding,
        MonitoringAiTaskType,
    )

    job_ids: list[str] = []
    for index, item in enumerate(escalated):
        subject_label = str(item.get("subject_label", "")).strip()
        clue = (item.get("primary") or item.get("verifier")) or {}
        title = str(clue.get("title", "")).strip()
        text = str(clue.get("text", "")).strip()
        if not subject_label or (not title and not text):
            continue
        try:
            evidence, source_hashes = build_subject_evidence(domains, subject_label)
        except ValueError:
            continue
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
                "selection_reasons": ["aemh_focused_verification"],
                "domains": sorted({item2["raw_fields"]["domain"] for item2 in evidence}),
                "domain_semantics": dict(_DOMAIN_ROLE),
                "medical_boundary": (
                    "仅对待核实观察给出独立判断；不得自动判定AE/MH漏报、"
                    "方案违背或生成Query。"
                ),
                "analysis_contract": (
                    "本轮是定向核实：请针对下方focus_clue描述的观察，逐条"
                    "比对evidence_packet中的原始字段值。若观察与证据一致，"
                    "输出恰好一个确认该观察的候选（引用支持它的证据行，"
                    "域对≥2）；若观察与证据不一致或证据不足，输出恰好一个"
                    "data_gap候选并说明反证或缺口。不要输出其他候选。"
                    "候选对象只允许输出schema定义的字段（candidate_type/"
                    "title/text/claims/evidence等），严禁添加"
                    "system_generated_evidence等任何额外字段；证据引用只能"
                    "使用evidence_packet中已有的evidence_id。"
                ),
                "focus_clue": {
                    "finding_id": f"aemh-fv-{index:04d}",
                    "title": title[:200],
                    "text": text[:2000],
                    "proposer": "primary" if item.get("primary") else "verifier",
                },
            },
            "evidence_packet": evidence,
        }
        job_ids.append(
            verifier_service.submit_task(
                project_id=project_id,
                task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
                input_revision=input_revision,
                input_payload=payload,
                business_key=(
                    f"aemh:{facts_snapshot_ref}:focus:{subject_label}:{index:04d}"
                ),
                prompt_version=VERIFIER_PROMPT_VERSION,
                max_attempts=max_attempts,
            ).job_id
        )
    return tuple(job_ids)


def merge_focused_verifications(
    *,
    ai_repository: Any,
    project_id: str,
    findings: Sequence[Mapping[str, Any]],
    focused_job_by_index: Mapping[int, str],
) -> list[dict[str, Any]]:
    """Merge focused verification results into the findings list.

    An escalated clue whose focused-verification candidate agrees with it
    (``_clues_agree`` against the ORIGINAL clue's fingerprint/entities) is
    reclassified ``accepted`` with both wordings; a data_gap/other candidate
    keeps it ``escalated`` (genuine refusal) with the verification text
    attached.
    """

    merged: list[dict[str, Any]] = []
    original_clue_fingerprints: dict[int, frozenset[str]] = {}

    class _ClueView:
        """Minimal duck-typed view over a stored finding for _clues_agree."""

        def __init__(self, title: str, text: str, evidence_ids: frozenset[str], domains: set[str]) -> None:
            self.title = title
            self.text = text
            self.evidence = tuple(
                type("E", (), {"evidence_id": eid})() for eid in evidence_ids
            )
            self.structured_payload = {"domains": sorted(domains), "claims": [{"text": text}]}

    for index, item in enumerate(findings):
        if item.get("state") != "escalated":
            merged.append(dict(item))
            continue
        job_id = focused_job_by_index.get(index)
        if not job_id:
            merged.append(dict(item))
            continue
        candidates = ai_repository.candidates(project_id, job_id)
        clue = (item.get("primary") or item.get("verifier")) or {}
        original_view = _ClueView(
            title=str(clue.get("title", "")),
            text=str(clue.get("text", "")),
            evidence_ids=frozenset(
                str(eid)
                for claim in (clue.get("payload", {}).get("claims", []) or [])
                if isinstance(claim, Mapping)
                for eid in (claim.get("evidence_ids", []) or [])
            ),
            domains=set(clue.get("domains", []) or []),
        )
        verification_texts: list[str] = []
        confirmed = False
        for candidate in candidates:
            payload = getattr(candidate, "structured_payload", {}) or {}
            is_gap = any(
                str(claim.get("kind", "")) == "data_gap"
                for claim in payload.get("claims", []) or []
                if isinstance(claim, Mapping)
            )
            verification_texts.append(str(getattr(candidate, "title", "")))
            if not is_gap and _clues_agree(original_view, candidate):
                confirmed = True
                break
        new_item = dict(item)
        if confirmed:
            new_item["state"] = "accepted"
            new_item["reason_zh"] = (
                "单侧线索经对侧模型定向核实确认（第二轮聚焦核对通过），待医学复核。"
            )
            new_item["focused_verification"] = verification_texts[:2]
        else:
            new_item["reason_zh"] = (
                "定向核实未确认该线索（反证或证据不足），请医学监察员裁决。"
            )
            new_item["focused_verification"] = verification_texts[:2]
        merged.append(new_item)
    return merged


__all__ = [
    "AeMhSubmission",
    "PRIMARY_PROMPT_VERSION",
    "VERIFIER_PROMPT_VERSION",
    "adjudicate",
    "build_subject_evidence",
    "merge_focused_verifications",
    "submit_cohorts",
    "submit_focused_verifications",
]
