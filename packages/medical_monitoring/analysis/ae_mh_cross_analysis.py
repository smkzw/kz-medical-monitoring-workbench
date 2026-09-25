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
# R24V2-B04：本清单是**本lane的合同范围**，不是全研究分析覆盖。未列入
# 的域（如本例标准EX、实验室LB_*、疗效量表、PK/PD/ADA）为 not-assessed，
# 在分析覆盖口径中如实单列——不以"已分析7表"冒充全域覆盖；扩展域分析
# 属独立工作包。
_NOT_ASSESSED_DOMAIN_NOTE = (
    "本lane仅覆盖AE/MH/CM/EX（试验用药子表）跨表线索；实验室、疗效量表、"
    "PK/PD、ADA等域尚未纳入本分析，覆盖口径中如实标记为未评估。"
)
# N5：去除截断限制——全部行/全部字段/完整值纳入证据包。
# 管理列仍排除（不承载临床语义）。
_ADMIN_COLUMNS = frozenset({"Block顺序号", "RECREP", "PAGELMDT", "FORMOID", "FORMNM", "FORMNM__2"})
# 分析版本：N5证据扩容（完整行/字段/值+真实内容hash）
ANALYSIS_GENERATION_V2 = "aemh-evidence-v2"
# V5-01统一源摘要合同：facts:<table>源摘要=全表冻结内容的版本化摘要。
# build_subject_evidence（盖章）与main._current_facts_analysis_revision
# （fresh校验）必须共用本函数，禁止各自再实现行数式或子集式摘要。
FACTS_SOURCE_DIGEST_VERSION = "facts-source-digest-v2"


def facts_table_source_digest(table: str, rows: Sequence[Mapping[str, Any]]) -> str:
    """`facts:<table>`源的统一版本化内容摘要（V5-01合同）。

    覆盖范围=该表全部冻结行（不是受试者切片，也不是行数）；行值保留
    原始类型（不做str化——0/False/数值与字符串可区分）。历史作业使用
    旧算法（行数式）盖章，fresh校验按新算法重算不等即判stale：策略
    变化不伪造数据变化，旧代际作业已全部终态不再重查。
    """
    return content_hash({
        "digest_version": FACTS_SOURCE_DIGEST_VERSION,
        "table": table,
        "rows": [content_hash(dict(row)) for row in rows],
    })


@dataclass(frozen=True)
class AeMhSubmission:
    project_id: str
    primary_job_ids: tuple[str, ...]
    verifier_job_ids: tuple[str, ...]
    subject_ids: tuple[str, ...]


def _clean(value: Any) -> str:
    """V5-08 R5-02：0/False不再被`value or ""`吞掉。

    None→空串；字符串规范化空白；bool→true/false；其余数值str化。
    展示仍是字符串，但0与空、False与0可区分。
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, bool):
        return "true" if value else "false"
    return " ".join(str(value).split())


def _compact_fields(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    """N5：全部非管理字段完整纳入（去24字段/120字符截断）。

    管理列（Block顺序号等）仍排除——不承载临床语义。
    值保留完整长度（不再截断到120字符）。
    """
    fields = []
    for key, value in row.items():
        text = _clean(value)
        if not text or key in _ADMIN_COLUMNS:
            continue
        fields.append({"field": str(key), "value": text})
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
        # V5-01：源摘要=全表冻结内容的统一版本化摘要（与fresh校验共用
        # facts_table_source_digest）；受试者切片归属由行级locator/fingerprint
        # 表达，不再混入源身份。
        table_hash = facts_table_source_digest(table, rows)
        source_hashes[table] = table_hash
        domain = _TABLE_DOMAIN[table]
        # N5：全部受试者行纳入证据包（不再截断到前6行）
        for index, row in subject_rows:
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


# 命题方向标记（N5命题核验）：正/负方向词组用于检测"同一证据、
# 相反结论"的危险误配——共享evidence_id不等于命题方向一致。
_POSITIVE_DIRECTION_RE = re.compile(
    r"存在|有|记录了|提示|不一致|矛盾|漏报|缺如|异常|升高|降低|超出|"
    "超出正常|需核查|需关注|值得关注|风险信号"
)
_NEGATIVE_DIRECTION_RE = re.compile(
    r"未见|未记录|未提及|无异常|正常|一致|相符|不存在|无明显|"
    "未见明显|未见异常|无特殊|排除"
)


def _clue_direction_text(candidate: Any) -> str:
    """Concatenate all directional text from a clue for direction analysis."""
    payload = getattr(candidate, "structured_payload", {}) or {}
    parts = [
        str(getattr(candidate, "title", "") or ""),
        str(getattr(candidate, "text", "") or ""),
    ]
    for claim in payload.get("claims", []) or []:
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    return " ".join(parts)


def _clue_stance(candidate: Any) -> str:
    """Extract the dominant proposition stance of a clue.

    Returns "positive" (存在问题/需关注), "negative" (未见异常/无问题),
    or "neutral" (无法判定方向).
    """
    text = _clue_direction_text(candidate)
    if not text:
        return "neutral"
    pos_hits = len(_POSITIVE_DIRECTION_RE.findall(text))
    neg_hits = len(_NEGATIVE_DIRECTION_RE.findall(text))
    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


def _clues_agree(primary: Any, verifier: Any) -> bool:
    """Pairing: shared evidence rows AND compatible proposition direction.

    Two independent models often cite different rows of the same subject while
    describing the same finding (e.g. both discuss the hypertension history,
    one citing MH rows and the other CM rows). Evidence overlap alone would
    mis-file those as disagreements.

    N5命题核验：evidence_id重叠是必要条件而非充分条件——两条线索引用
    同一证据但命题方向相反（"存在AE"vs"未见AE"）不得判为一致。
    方向通过正/负标记词频比较，neutral方向不做方向否决。
    """
    shared_evidence = _clue_fingerprint(primary) & _clue_fingerprint(verifier)
    domains = _clue_domain_pair(primary) & _clue_domain_pair(verifier)
    shared_entities = _clue_entities(primary) & _clue_entities(verifier)

    has_evidence_overlap = bool(shared_evidence)
    has_entity_match = bool(domains) and len(shared_entities) >= 2

    if not has_evidence_overlap and not has_entity_match:
        return False

    # V5-06命题核验降级：词频方向仅是候选配对信号，不是确认依据。
    # 确认（accepted）只允许双方立场都明确为positive且无数值/分级冲突；
    # 任一方neutral（无法判定方向）、同负向词频、或有分级差异，一律
    # 不判一致（保守升级为可见分歧，交人工/定向核实裁决）。
    primary_stance = _clue_stance(primary)
    verifier_stance = _clue_stance(verifier)
    if primary_stance != "positive" or verifier_stance != "positive":
        return False
    primary_grades = _grade_terms(primary)
    verifier_grades = _grade_terms(verifier)
    if primary_grades and verifier_grades and not (
        primary_grades & verifier_grades
    ):
        # "3级"vs"1级"类分级矛盾：词频同向也不能判一致
        return False
    return True


_GRADE_RE = re.compile(r"(?:^|[^0-9])([1-5])\s*级|grade\s*([1-5])", re.IGNORECASE)


def _grade_terms(candidate: Any) -> set[str]:
    """Extract explicit severity-grade mentions ("3级"/"grade 2") from a clue."""

    text = _clue_direction_text(candidate)
    if not text:
        return set()
    grades = set()
    for first, second in _GRADE_RE.findall(text):
        grades.add(first or second)
    return grades


def _finding_text(candidate: Any) -> dict[str, Any]:
    payload = getattr(candidate, "structured_payload", {}) or {}
    return {
        "title": str(getattr(candidate, "title", "") or "")[:200],
        "text": str(getattr(candidate, "text", "") or "")[:2000],
        "domains": list(payload.get("domains", []) or []),
        "payload": payload,
    }


def _stable_finding_id(subject_label: str, side: str, clue: Mapping[str, Any]) -> str:
    """Deterministic finding identity: subject + proposing side + clue text.

    稳定finding_id：同一线索在重跑/重合并/JSON往返后身份不变，取代
    位置索引（zip/index）作为定向核实的关联键。
    """
    title = str(clue.get("title", "") or "")
    text = str(clue.get("text", "") or "")
    domains = ",".join(sorted(str(d) for d in (clue.get("domains", []) or [])))
    digest = content_hash(
        {"subject": subject_label, "side": side, "title": title, "text": text, "domains": domains}
    )
    return f"aemh-{subject_label}-{side}-{digest[:12]}"


def adjudicate(
    *,
    ai_repository: Any,
    project_id: str,
    subject_labels: Sequence[str],
    facts_snapshot_ref: str,
    primary_job_by_subject: Mapping[str, str],
    verifier_job_by_subject: Mapping[str, str],
    artifacts_dir: Path | None,
) -> dict[str, Any]:
    """Pair the two cohorts per subject into visible findings.

    Conservative structural matching only: a primary clue and a verifier clue
    agree when they cite at least one shared original evidence row. Unpaired
    clues from either cohort stay ``escalated`` (never force-accepted); a
    subject whose cohort job did not complete stays ``unverifiable_gap``.
    Each finding carries a stable ``finding_id`` used by the focused
    verification round; pass ``artifacts_dir=None`` for in-memory evaluation
    with no artifact side effects (dry-run/只读探查).
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
                    "finding_id": f"aemh-{subject_label}-subjectgap",
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
                        "finding_id": _stable_finding_id(subject_label, "primary", primary_text),
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
                        "finding_id": _stable_finding_id(subject_label, "primary", primary_text),
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
                        "finding_id": _stable_finding_id(subject_label, "primary", primary_text),
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
                        "finding_id": _stable_finding_id(subject_label, "verifier", verifier_text),
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
                        "finding_id": _stable_finding_id(subject_label, "verifier", verifier_text),
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
    if artifacts_dir is not None:
        # dry-run/只读评估传None：不写正式工件，无落盘副作用。
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / f"aemh-findings-{facts_snapshot_ref}.json").write_text(
            json.dumps(artifact, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    return artifact


class FocusedSubmission:
    """Focused-verification submission ledger.

    ``job_by_finding_id``把作业与稳定线索身份关联（无zip/位置索引）；每个
    跳项都必须带可见原因，不得无声消失。
    """

    def __init__(
        self,
        job_by_finding_id: dict[str, str],
        skipped: list[dict[str, str]],
    ) -> None:
        self.job_by_finding_id = job_by_finding_id
        self.skipped = skipped


FOCUSED_CONTRACT_VERSION = "aemh-focused-v1"


def submit_focused_verifications(
    *,
    verifier_service: Any,
    project_id: str,
    domains: Mapping[str, list[dict[str, Any]]],
    escalated: Sequence[Mapping[str, Any]],
    facts_snapshot_ref: str,
    max_attempts: int = 2,
    primary_service: Any = None,
) -> FocusedSubmission:
    """Focused second-round verification for one-sided findings.

    For each escalated clue (proposed by only one cohort), the OPPOSITE
    model receives the same subject evidence packet plus a focused
    instruction: confirm the observation against the rows, or refute it with
    a data_gap candidate. The harness then re-pairs; only genuine refusals
    remain escalated for the human reviewer. Clues proposed by the primary
    cohort go to the verifier service; clues proposed by the verifier cohort
    go to the primary service when one is supplied (真对侧盲核), otherwise
    they fall back to the verifier service.

    Jobs are associated with the stable ``finding_id`` (never positional
    index) and carry the versioned focused contract
    (``FOCUSED_CONTRACT_VERSION``：恰好一个核实候选），使服务端校验与
    提示词合同显式绑定，而不是靠隐式约定。
    """

    from services.api.app.monitoring_ai_contracts import (  # noqa: PLC0415
        MonitoringAiInputRevision,
        MonitoringAiSourceBinding,
        MonitoringAiTaskType,
    )

    job_by_finding_id: dict[str, str] = {}
    skipped: list[dict[str, str]] = []
    for item in escalated:
        subject_label = str(item.get("subject_label", "")).strip()
        finding_id = str(item.get("finding_id", "")).strip()
        clue = (item.get("primary") or item.get("verifier")) or {}
        title = str(clue.get("title", "")).strip()
        text = str(clue.get("text", "")).strip()
        if not finding_id:
            skipped.append(
                {
                    "subject_label": subject_label,
                    "finding_id": "",
                    "reason": "missing_finding_id",
                }
            )
            continue
        if not subject_label or (not title and not text):
            skipped.append(
                {
                    "subject_label": subject_label,
                    "finding_id": finding_id,
                    "reason": "empty_subject_or_clue",
                }
            )
            continue
        try:
            evidence, source_hashes = build_subject_evidence(domains, subject_label)
        except ValueError as exc:
            skipped.append(
                {
                    "subject_label": subject_label,
                    "finding_id": finding_id,
                    "reason": f"evidence_unavailable: {exc}",
                }
            )
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
                "focused_contract": {
                    "version": FOCUSED_CONTRACT_VERSION,
                    "expected_candidates": 1,
                },
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
                    "finding_id": finding_id,
                    "title": title[:200],
                    "text": text[:2000],
                    "proposer": "primary" if item.get("primary") else "verifier",
                },
            },
            "evidence_packet": evidence,
        }
        # 对侧定向核实：主侧提出的线索由盲核模型核实；盲核侧提出的线索由
        # 主模型核实（真对侧盲核），未提供主服务时回退盲核服务。
        if not item.get("primary") and primary_service is not None:
            service = primary_service
            prompt_version = PRIMARY_PROMPT_VERSION
            side_tag = "focus-p"
        else:
            service = verifier_service
            prompt_version = VERIFIER_PROMPT_VERSION
            side_tag = "focus"
        job = service.submit_task(
            project_id=project_id,
            task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
            input_revision=input_revision,
            input_payload=payload,
            business_key=(
                f"aemh:{facts_snapshot_ref}:{side_tag}:{subject_label}:{finding_id}"
            ),
            prompt_version=prompt_version,
            max_attempts=max_attempts,
        )
        job_by_finding_id[finding_id] = job.job_id
    return FocusedSubmission(job_by_finding_id=job_by_finding_id, skipped=skipped)


def merge_focused_verifications(
    *,
    ai_repository: Any,
    project_id: str,
    findings: Sequence[Mapping[str, Any]],
    focused_job_by_finding_id: Mapping[str, str],
    wait_timed_out_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Merge focused verification results into the findings list.

    四态区分（D-03）——核实结论与执行状态严格分开：
    - ``confirmed``：对侧给出一致候选 → accepted；
    - ``refuted``：对侧给出data_gap反证 → escalated（真分歧，请用户裁决）；
    - ``insufficient_evidence``：有候选但既未确认也未反证 → escalated；
    - 执行状态（作业缺失/失败/等待超时/零候选）→ escalated但标注
      ``verification_execution``技术原因，明确"非医学反证"，不写
      "请医学监察员裁决"式措辞把技术缺口伪装成医学分歧。

    Jobs are looked up by stable ``finding_id``; positional/zip identity is
    not used.  ``wait_timed_out_ids`` marks findings whose focused job was
    still unfinished when the wait deadline expired.
    """

    merged: list[dict[str, Any]] = []

    class _ClueView:
        """Minimal duck-typed view over a stored finding for _clues_agree."""

        def __init__(self, title: str, text: str, evidence_ids: frozenset[str], domains: set[str]) -> None:
            self.title = title
            self.text = text
            self.evidence = tuple(
                type("E", (), {"evidence_id": eid})() for eid in evidence_ids
            )
            self.structured_payload = {"domains": sorted(domains), "claims": [{"text": text}]}

    for item in findings:
        if item.get("state") != "escalated":
            merged.append(dict(item))
            continue
        finding_id = str(item.get("finding_id", "")).strip()
        new_item = dict(item)
        if not finding_id or finding_id not in focused_job_by_finding_id:
            new_item["verification_execution"] = "verification_missing"
            new_item["reason_zh"] = (
                "该单侧线索未进入定向核实（作业缺失），非医学反证；结果以单侧线索呈现。"
            )
            merged.append(new_item)
            continue
        job_id = focused_job_by_finding_id[finding_id]
        try:
            job = ai_repository.get(project_id, job_id)
            raw_status = getattr(job, "status", "missing")
            # 仓库返回pydantic模型时status是枚举：取.value归一为字符串，
            # 否则str(enum)永远不等于"completed"，全部误判为失败。
            job_status = str(getattr(raw_status, "value", raw_status))
        except Exception:
            job_status = "query_error"
        if finding_id in (wait_timed_out_ids or set()) or job_status in (
            "queued",
            "running",
        ):
            new_item["verification_execution"] = "verification_timed_out"
            new_item["verification_job_id"] = job_id
            new_item["reason_zh"] = (
                f"定向核实作业未在等待期限内完成（作业状态={job_status}），"
                "非医学反证；结果以单侧线索呈现。"
            )
            merged.append(new_item)
            continue
        if job_status != "completed":
            new_item["verification_execution"] = "verification_failed"
            new_item["verification_job_id"] = job_id
            new_item["reason_zh"] = (
                f"定向核实作业未成功（作业状态={job_status}），"
                "非医学反证；结果以单侧线索呈现。"
            )
            merged.append(new_item)
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
        has_gap = False
        confirmed = False
        for candidate in candidates:
            payload = getattr(candidate, "structured_payload", {}) or {}
            is_gap = any(
                str(claim.get("kind", "")) == "data_gap"
                for claim in payload.get("claims", []) or []
                if isinstance(claim, Mapping)
            )
            verification_texts.append(str(getattr(candidate, "title", "")))
            if is_gap:
                has_gap = True
                continue
            if _clues_agree(original_view, candidate):
                confirmed = True
                break
        new_item["verification_job_id"] = job_id
        new_item["focused_verification"] = verification_texts[:2]
        if confirmed:
            new_item["verification_execution"] = "confirmed"
            new_item["state"] = "accepted"
            new_item["reason_zh"] = (
                "单侧线索经对侧模型定向核实确认（第二轮聚焦核对通过），待医学复核。"
            )
        elif has_gap:
            new_item["verification_execution"] = "refuted"
            new_item["reason_zh"] = (
                "定向核实给出反证（对侧模型认为该观察与原始记录不一致或证据不足），"
                "请医学监察员裁决。"
            )
        elif verification_texts:
            new_item["verification_execution"] = "insufficient_evidence"
            new_item["reason_zh"] = (
                "定向核实返回的候选既未确认也未反驳该线索（证据不足），"
                "请医学监察员裁决。"
            )
        else:
            new_item["verification_execution"] = "verification_no_candidates"
            new_item["reason_zh"] = (
                "定向核实作业完成但未产出任何候选（执行状态异常），"
                "非医学反证；结果以单侧线索呈现。"
            )
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
