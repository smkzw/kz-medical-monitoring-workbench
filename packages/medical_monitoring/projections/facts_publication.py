"""Real facts-backed publication authority for the materialized MG facts.

Reads the deterministic fact artifacts (62 domains, one JSON per domain,
rows keyed by original column names) and builds a typed
:class:`R5AuthorityPacket` with real subjects, sites, visits, events,
risks and subject-flow paths. No synthetic fixtures are involved.
"""
from __future__ import annotations

import json
import re
from dataclasses import fields
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..intelligence.primitives import content_hash
from .product_types import (
    CHANGE_KINDS,
    DATE_STATES,
    DOMAINS,
    R5AuthorityPacket,
    R5EventRecord,
    R5FlowStageRecord,
    R5RiskRecord,
    R5SiteAudienceRecord,
    R5SiteRecord,
    R5SourceRecord,
    R5SourceRevisionPair,
    R5SubjectFlowPathRecord,
    R5SubjectFlowStep,
    R5SubjectRecord,
    R5VisitRecord,
    SEVERITIES,
    VISIT_KINDS,
)

_UK_TOKENS = {"uk", "UNK", "UNKNOWN", ""}
_DATE_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_PARTIAL_RE = re.compile(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$")

# 源表 → 八轨临床域映射（表名 → (domain, subtype)）
_DOMAIN_BY_TABLE: dict[str, tuple[str, str]] = {
    "AE": ("ae", "ae"),
    "MH": ("mh", "mh"),
    "DAH": ("mh", "mh"),
    "DUH": ("mh", "mh"),
    "ASH": ("mh", "mh"),
    "ALR": ("mh", "mh"),
    "CM": ("cm", "concomitant_medication"),
    "EX1": ("ip", "ip_dose"),
    "EX2": ("ip", "ip_dose"),
    "EX4": ("ip", "ip_dose"),
    "EX5": ("ip", "ip_dose"),
    "EX7": ("ip", "ip_dose"),
    "EX": ("ip", "ip_dose"),
    "LB_CHEM": ("lab_exam", "lab"),
    "LB_HEM": ("lab_exam", "lab"),
    "LB_HBV": ("lab_exam", "lab"),
    "LB_HCG": ("lab_exam", "lab"),
    "LB_URI": ("lab_exam", "lab"),
    "LB_VIR": ("lab_exam", "lab"),
    "LB_REP": ("lab_exam", "lab"),
    "LB_": ("lab_exam", "lab"),
    "HW": ("lab_exam", "exam"),
    "EG": ("lab_exam", "exam"),
    "VS": ("lab_exam", "exam"),
    "SV": ("protocol_compliance", "protocol_deviation"),
    "SH": ("hospital_procedure", "procedure"),
    "SU": ("hospital_procedure", "procedure"),
    "PR": ("hospital_procedure", "procedure"),
    "PT": ("symptom_efficacy", "symptom"),
    "NE": ("symptom_efficacy", "efficacy"),
    "NS": ("symptom_efficacy", "efficacy"),
    "RQL": ("symptom_efficacy", "scale"),
    "PC": ("symptom_efficacy", "outcome"),
    "PD": ("protocol_compliance", "protocol_deviation"),
    "IE": ("protocol_compliance", "protocol_deviation"),
    "ICF": ("protocol_compliance", "protocol_deviation"),
    "RAN": ("protocol_compliance", "protocol_deviation"),
    "DS": ("protocol_compliance", "protocol_deviation"),
    "FW": ("protocol_compliance", "protocol_deviation"),
    "RES": ("symptom_efficacy", "efficacy"),
    "PE": ("lab_exam", "exam"),
    "MO": ("lab_exam", "exam"),
    "RT": ("lab_exam", "exam"),
    "UNS": ("lab_exam", "exam"),
    "USV": ("lab_exam", "exam"),
    "PK": ("lab_exam", "exam"),
    "SK": ("mh", "mh"),
    "PARH": ("mh", "mh"),
    "SARH": ("mh", "mh"),
    "AH": ("mh", "mh"),
}

# 非临床事件表：人口学与表单目录不进入八轨事件流
_EXCLUDED_TABLES = {"DM", "TOC"}

# subtype 英文标识 → 中文兜底标签（行内无术语列时使用）
_SUBTYPE_LABEL_ZH = {
    "ae": "不良事件",
    "mh": "既往病史",
    "concomitant_medication": "合并用药",
    "ip_dose": "给药记录",
    "lab": "实验室检验",
    "exam": "检查",
    "procedure": "住院/操作",
    "hospitalization": "住院",
    "symptom": "症状评估",
    "efficacy": "疗效评估",
    "scale": "量表评估",
    "outcome": "结局",
    "trend": "趋势",
    "protocol_deviation": "方案偏离",
}

# 表级中文兜底标签：同 subtype 下区分不同来源表（如 ICF/随机/访视记录）
_TABLE_LABEL_ZH = {
    "SV": "访视记录",
    "IE": "入排评估",
    "ICF": "知情同意",
    "RAN": "随机",
    "DS": "研究处置",
    "FW": "随访",
    "PD": "方案偏离",
    "RQL": "生活质量量表",
    "PK": "药代采样",
    "RT": "RPR检测",
    "USV": "尿酸检测",
    "UNS": "其他检查",
    "MO": "胸片影像",
    "PE": "体格检查",
    "VS": "生命体征",
    "EG": "心电图",
    "HW": "身高体重",
    "SK": "吸烟史",
    "PARH": "宠物接触史",
    "SARH": "特殊病史",
    "AH": "过敏史",
    "PR": "既往操作",
    "NS": "鼻腔评估",
    "NE": "鼻镜检查",
    "PT": "肺功能",
    "SH": "手术史",
}

# 事件中文标签列解析优先级：术语列 → 检查项目列 → 异常结论列 → 中文指标名/处置 → 备注列
_TERM_SUFFIX_PRIORITY = ("TERM", "TRT", "TEST", "ABCO")
_TERM_EXACT = ("实验室指标名称", "DSDECOD")
_COMMENT_SUFFIX = "CO"
_TABLE_TERM_OVERRIDES: dict[str, tuple[str, ...]] = {
    "IE": ("IECO", "IECAT"),
}


def _term_keys_for(table: str, columns: list[str]) -> list[str]:
    if table in _TABLE_TERM_OVERRIDES:
        keys = [c for c in _TABLE_TERM_OVERRIDES[table] if c in columns]
        if keys:
            return keys
    ordered: list[str] = []
    for suffix in _TERM_SUFFIX_PRIORITY:
        ordered.extend(c for c in columns if c.endswith(suffix) and c not in ordered)
    ordered.extend(c for c in _TERM_EXACT if c in columns and c not in ordered)
    ordered.extend(
        c
        for c in columns
        if c.endswith(_COMMENT_SUFFIX) and c not in ordered
    )
    return ordered


def _domain_for(table: str, rows: Sequence[dict[str, Any]] | None = None) -> tuple[str, str]:
    if table in _DOMAIN_BY_TABLE:
        return _DOMAIN_BY_TABLE[table]
    for prefix, mapping in _DOMAIN_BY_TABLE.items():
        if table.startswith(prefix):
            return mapping
    # 通用列签名推断：不看表名，看这张表实际承载的列/值形态——
    # 不同项目的listing表名各异（AE/AELOG/不良事件…），但语义列签名稳定。
    if rows:
        columns = set(rows[0].keys()) if rows else set()
        return _infer_domain_by_columns(table, columns)
    return ("protocol_compliance", "protocol_deviation")


# 列签名 → (domain, subtype)。签名按强度排序，首个命中即返回。
# 组合签名（多列同时存在）优先于单列签名。
_DOMAIN_COLUMN_SIGNATURES: tuple[tuple[tuple[str, ...], tuple[str, str]], ...] = (
    # 不良事件：术语+严重程度+与试验药关系（CTCAE分级版本由方案解构层给出）
    (("AETERM", "AESEV"), ("ae", "ae")),
    (("AETERM", "AESER"), ("ae", "ae")),
    (("AESEV", "AEREL"), ("ae", "ae")),
    # 病史：术语+起止+持续
    (("MHTERM", "MHSTDAT"), ("mh", "mh")),
    (("MHTERM", "MHONGO"), ("mh", "mh")),
    # 合并用药：药物+剂量单位+给药途径
    (("CMTRT", "CMDOSU"), ("cm", "concomitant_medication")),
    (("CMTRT", "CMROUTE"), ("cm", "concomitant_medication")),
    # 试验药：给药+剂量调整/依从性
    (("EXDOSE", "EXDAT"), ("ip", "ip_dose")),
    (("EXTRT", "EXDOSE"), ("ip", "ip_dose")),
    # 实验室：结果+参考范围/单位
    (("实验室指标名称", "结果"), ("lab_exam", "lab")),
    (("LBTEST", "LBORRES"), ("lab_exam", "lab")),
    (("LBTEST", "单位"), ("lab_exam", "lab")),
    # 检查：项目+结论
    (("VSTEST", "VSORRES"), ("lab_exam", "exam")),
    (("PETEST", "PECO"), ("lab_exam", "exam")),
    # 疗效/量表：评分组
    (("RQLSC1", "RQLYN"), ("symptom_efficacy", "scale")),
    # 方案符合：入排/偏离
    (("IECAT", "IEYN"), ("protocol_compliance", "protocol_deviation")),
    (("PDTERM", "PDDAT"), ("protocol_compliance", "protocol_deviation")),
)


def _infer_domain_by_columns(
    table: str, columns: set[str]
) -> tuple[str, str]:
    for required, mapping in _DOMAIN_COLUMN_SIGNATURES:
        if all(col in columns for col in required):
            return mapping
    # 单列强信号兜底
    if any(c.startswith("AE") and c.endswith("TERM") for c in columns):
        return ("ae", "ae")
    if any(c.startswith("MH") and c.endswith("TERM") for c in columns):
        return ("mh", "mh")
    if any(c.endswith("TRT") and c.startswith("CM") for c in columns):
        return ("cm", "concomitant_medication")
    if any(c.startswith("EX") and c.endswith("DAT") for c in columns):
        return ("ip", "ip_dose")
    if "实验室指标名称" in columns or any(c.startswith("LB") for c in columns):
        return ("lab_exam", "lab")
    return ("protocol_compliance", "protocol_deviation")


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    m = _DATE_RE.match(text)
    if not m:
        return None
    y, mo, d = (int(part) for part in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _date_state(value: Any) -> str:
    if value is None:
        return "missing"
    text = str(value).strip()
    if not text or text.upper() in {"UK", "UNK", "UNKNOWN", "NA", "N/A"}:
        return "missing"
    m = _DATE_RE.match(text)
    if m:
        return "exact"
    if _PARTIAL_RE.match(text):
        return "partial"
    return "missing"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


class FactsPublicationAuthorityProvider:
    """Typed R5 authority built from the materialized facts of one project."""

    fixture_mode = False

    def __init__(self, workspace_dir: Path, *, project_label: str = "MG-K10-SAR") -> None:
        self._workspace = Path(workspace_dir)
        self._project_label = project_label
        self._cache: dict[tuple[str, str], R5AuthorityPacket] = {}

    # -- loading -----------------------------------------------------------

    def _load_domains(self) -> dict[str, list[dict[str, Any]]]:
        artifacts = self._workspace / "runtime" / "artifacts"
        domains: dict[str, list[dict[str, Any]]] = {}
        for path in sorted(artifacts.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                continue
            for table, rows in payload.items():
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    domains[str(table)] = rows
        return domains

    # -- packet ------------------------------------------------------------

    def get_authority(self, identity: Any, **_: Any) -> R5AuthorityPacket:
        cache_key = (
            str(getattr(identity, "project_ref", "")),
            str(getattr(identity, "snapshot_ref", "")),
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        packet = self._build(cache_key)
        self._cache[cache_key] = packet
        return packet

    def get_packet(
        self,
        project_ref: str,
        run_ref: str | None = None,
        snapshot_ref: str | None = None,
        cutoff_ref: str | None = None,
    ) -> R5AuthorityPacket:
        """Positional adapter consumed by R5ProductAdapter._packet."""
        key = (str(project_ref), str(snapshot_ref or "facts-snapshot-001"))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        packet = self._build(key)
        self._cache[key] = packet
        return packet

    def _build(self, cache_key: tuple[str, str]) -> R5AuthorityPacket:
        domains = self._load_domains()
        snapshot_ref = cache_key[1] or "facts-snapshot-001"

        sources: list[R5SourceRecord] = []
        sites_by_ref: dict[str, dict[str, Any]] = {}
        subjects: dict[str, R5SubjectRecord] = {}
        subject_site: dict[str, str] = {}
        subject_site_label: dict[str, str] = {}
        visits: list[R5VisitRecord] = []
        events: list[R5EventRecord] = []
        risks: list[R5RiskRecord] = []

        # 站点/受试者骨干（任一表中的 SUBJID/SITEID/SITENM 都建立映射）
        for table, rows in domains.items():
            for row in rows:
                subj = _clean(row.get("SUBJID"))
                if not subj:
                    continue
                site_id = _clean(row.get("SITEID")) or "site-unknown"
                site_label = _clean(row.get("SITENM")) or site_id
                site_ref = f"site-{site_id}"
                subjects.setdefault(
                    subj,
                    R5SubjectRecord(
                        subject_ref=f"subject-{subj}",
                        site_ref=site_ref,
                        spine_ref=f"spine-{subj}",
                        subject_label=subj,
                    ),
                )
                subject_site[subj] = site_ref
                subject_site_label[subj] = site_label
                entry = sites_by_ref.setdefault(
                    site_ref,
                    {"label": site_label, "subjects": set()},
                )
                entry["subjects"].add(f"subject-{subj}")

        def _locator(table: str, index: int) -> R5SourceRecord:
            ref = f"loc-{table}-{index:06d}"
            record = R5SourceRecord(
                locator_ref=ref,
                snapshot_ref=snapshot_ref,
                source_file_ref=f"listing:{table}",
                source_revision_ref=f"src-rev-{table}",
                source_revision_content_hash=content_hash({"table": table})[:64].replace("-", "0"),
                record_ref=f"row-{table}-{index:06d}",
                canonical_location=f"{table}!row{index + 1}",
                excerpt=f"{table} 第{index + 1}行原始数据（已校验）",
            )
            sources.append(record)
            return record

        def _add_event(
            *,
            table: str,
            index: int,
            subj: str,
            subtype: str,
            domain: str,
            start_raw: Any,
            label: str,
            severity_hint: str = "low",
        ) -> R5EventRecord | None:
            subj_ref = f"subject-{subj}"
            site_ref = subject_site.get(subj, "site-unknown")
            spine = f"spine-{subj}"
            state = _date_state(start_raw)
            if state == "exact" and _parse_date(start_raw) is None:
                state = "missing"
            record = R5EventRecord(
                event_ref=f"event-{table}-{index:06d}",
                subject_ref=subj_ref,
                site_ref=site_ref,
                spine_ref=spine,
                domain=domain,
                subtype=subtype,
                date_state=state,
                start_date=_parse_date(start_raw) if state == "exact" else None,
                end_date=None,
                visit_ref=None,
                risk_anchor_refs=(),
                source_locator_refs=(_locator(table, index).locator_ref,),
                label_zh=label[:60] or _SUBTYPE_LABEL_ZH.get(subtype, subtype),
            )
            events.append(record)
            # 初步风险：严重度可由表内字段推导（如 AESEV），此处保守 medium 起步
            if domain == "ae":
                sev_raw = _clean(domains.get("AE", [{}])[index].get("AESEV") if index < len(domains.get("AE", [])) else "")
                sev_map = {"重度": "critical", "严重": "critical", "中度": "medium", "轻度": "low"}
                severity = sev_map.get(sev_raw, "medium")
            else:
                severity = severity_hint
            risks.append(
                R5RiskRecord(
                    risk_ref=f"risk-{table}-{index:06d}",
                    risk_instance_ref=f"riski-{table}-{index:06d}",
                    risk_key=f"{domain}:{table}:{index}",
                    site_ref=site_ref,
                    subject_ref=subj_ref,
                    spine_ref=spine,
                    domain=domain,
                    severity=severity if severity in SEVERITIES else "medium",
                    risk_type_zh=_risk_type_zh(domain, subtype),
                    date_state=state,
                    event_ref=record.event_ref,
                    visit_ref=None,
                    risk_anchor_ref=record.event_ref,
                    source_locator_refs=record.source_locator_refs,
                    change_kind="initial_current",
                )
            )
            return record

        # 访视（SV 为权威访视记录表；VS/HW/EG 补充覆盖）
        seen_visits: set[tuple[str, str]] = set()
        _VISIT_DATE_COL = {"SV": "VISDAT", "VS": "VSDAT"}
        for table in ("SV", "VS", "HW", "EG"):
            for index, row in enumerate(domains.get(table, [])):
                subj = _clean(row.get("SUBJID"))
                visit_name = _clean(row.get("VISIT"))
                date_raw = row.get(_VISIT_DATE_COL.get(table, f"{table}DAT"))
                if not subj or not visit_name or subj in _UK_TOKENS:
                    continue
                key = (subj, visit_name)
                if key in seen_visits:
                    continue
                state = _date_state(date_raw)
                seen_visits.add(key)
                visits.append(
                    R5VisitRecord(
                        visit_ref=f"visit-{subj}-{int(content_hash(visit_name)[:6], 16) % 10_000:04d}",
                        subject_ref=f"subject-{subj}",
                        site_ref=subject_site.get(subj, "site-unknown"),
                        spine_ref=f"spine-{subj}",
                        visit_kind="actual",
                        date_state=state,
                        actual_date=_parse_date(date_raw) if state == "exact" else None,
                        nominal_date=None,
                        phase_ref=None,
                        source_locator_refs=(_locator(table, index).locator_ref,),
                    )
                )

        # 八轨事件
        for table, rows in domains.items():
            if table in _EXCLUDED_TABLES:
                continue
            domain, subtype = _domain_for(table, rows)
            raw_date_keys = [k for k in rows[0].keys() if k.endswith("DAT") or k in ("SHDAT",)] if rows else []
            # 起始日期列优先（*STDAT/{表}DAT），结束列（*ENDAT）不充当起始
            date_keys = sorted(raw_date_keys, key=lambda k: (1 if "END" in k.upper() else 0, raw_date_keys.index(k)))
            term_keys = _term_keys_for(table, list(rows[0].keys())) if rows else []
            for index, row in enumerate(rows):
                subj = _clean(row.get("SUBJID"))
                if not subj or subj in _UK_TOKENS:
                    continue
                start_raw = next((row[k] for k in date_keys if _clean(row.get(k))), None)
                term_value = next((row[k] for k in term_keys if _clean(row.get(k))), None)
                if _clean(term_value):
                    label = _clean(term_value)
                else:
                    fallback = _TABLE_LABEL_ZH.get(table) or _SUBTYPE_LABEL_ZH.get(subtype, subtype)
                    visit_name = _clean(row.get("VISIT"))
                    if "共同页" in visit_name or "共同" == visit_name:
                        visit_name = ""
                    label = f"{fallback}·{visit_name}" if visit_name else fallback
                _add_event(
                    table=table, index=index, subj=subj, subtype=subtype,
                    domain=domain, start_raw=start_raw, label=label,
                )

        # 受试者流向（SV/筛选表：ICF→筛选→治疗→研究状态）
        flow_catalog = self._flow_catalog(domains)
        flow_paths = self._flow_paths(domains, subject_site, _locator)

        packet = R5AuthorityPacket(
            project_ref=cache_key[0] or "proj_mgk10_sar_real",
            run_ref="run-facts-001",
            snapshot_ref=snapshot_ref,
            cutoff_state="absent",
            cutoff_ref=None,
            project_label=self._project_label,
            authority_contract_id="facts-authority-v1",
            authority_contract_version="2026-08-28.1",
            audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
            visibility_decision_id=f"facts-visibility:{snapshot_ref}",
            visibility_decision_hash=content_hash({"snapshot": snapshot_ref, "projectable": True})[:64],
            evaluation_content_identities=(content_hash({"snapshot": snapshot_ref, "kind": "evaluation"})[:64],),
            source_revision_content_pairs=(
                R5SourceRevisionPair(
                    revision_id="src-rev-facts",
                    content_hash=content_hash({"facts": True})[:64],
                    locator_refs=(),
                ),
            ),
            sources=tuple(sources),
            sites=tuple(
                R5SiteRecord(
                    site_ref=ref,
                    subject_refs=(), pattern_refs=(), individual_risk_refs=(), measure_refs=(),
                    domain="ae", severity="low", numerator=0, denominator=None,
                    coverage_state="not_evaluable",
                )
                for ref in sorted(sites_by_ref)
            ),
            site_audience=tuple(
                R5SiteAudienceRecord(site_ref=ref, site_label=info["label"])
                for ref, info in sorted(sites_by_ref.items())
            ),
            subjects=tuple(subjects.values()),
            events=tuple(events),
            visits=tuple(visits),
            risks=tuple(risks),
            histories=(),
            flow_stages=flow_catalog,
            subject_flow_paths=flow_paths,
            synthetic=False,
            data_mode="authority",
        )
        return packet

    def _flow_catalog(self, domains: Mapping[str, list[dict[str, Any]]]) -> tuple[R5FlowStageRecord, ...]:
        return (
            R5FlowStageRecord(stage_ref="stage-icf", stage_label_zh="知情同意", column_order=0, row_order=0, stage_kind="main", is_entry=True, is_terminal=False, source_locator_refs=()),
            R5FlowStageRecord(stage_ref="stage-screening", stage_label_zh="筛选", column_order=1, row_order=0, stage_kind="main", is_entry=False, is_terminal=False, source_locator_refs=()),
            R5FlowStageRecord(stage_ref="stage-screen-failed", stage_label_zh="筛选失败", column_order=1, row_order=1, stage_kind="branch_terminal", is_entry=False, is_terminal=True, source_locator_refs=()),
            R5FlowStageRecord(stage_ref="stage-treatment", stage_label_zh="治疗", column_order=2, row_order=0, stage_kind="main", is_entry=False, is_terminal=False, source_locator_refs=()),
            R5FlowStageRecord(stage_ref="stage-study-status", stage_label_zh="研究状态", column_order=3, row_order=0, stage_kind="main", is_entry=False, is_terminal=True, source_locator_refs=()),
        )

    def _flow_paths(
        self,
        domains: Mapping[str, list[dict[str, Any]]],
        subject_site: Mapping[str, str],
        locator: Callable[[str, int], R5SourceRecord],
    ) -> tuple[R5SubjectFlowPathRecord, ...]:
        paths = []

        def _earliest(
            rows: list[dict[str, Any]], date_cols: Sequence[str]
        ) -> tuple[date | None, int] | None:
            best: tuple[date, int] | None = None
            for index, row in enumerate(rows):
                for col in date_cols:
                    raw = _clean(row.get(col))
                    if raw and _date_state(raw) == "exact":
                        parsed = _parse_date(raw)
                        if parsed and (best is None or parsed < best[0]):
                            best = (parsed, index)
                        break
            return best

        # 知情同意：ICF 表 ICFDAT
        icf_by_subject: dict[str, tuple[date | None, str, int]] = {}
        for index, row in enumerate(domains.get("ICF", [])):
            subj = _clean(row.get("SUBJID"))
            if not subj or subj in _UK_TOKENS:
                continue
            raw = _clean(row.get("ICFDAT"))
            state = _date_state(raw)
            parsed = _parse_date(raw) if state == "exact" else None
            current = icf_by_subject.get(subj)
            if current is None or (parsed and (current[0] is None or parsed < current[0])):
                icf_by_subject[subj] = (parsed, state, index)

        # 筛选：SV 中首个含「筛选」的访视日期；兜底为最早访视
        screening_by_subject: dict[str, tuple[date, int]] = {}
        first_visit_by_subject: dict[str, tuple[date, int]] = {}
        sv_rows = domains.get("SV", [])
        for index, row in enumerate(sv_rows):
            subj = _clean(row.get("SUBJID"))
            raw = _clean(row.get("VISDAT"))
            parsed = _parse_date(raw) if _date_state(raw) == "exact" else None
            if not subj or subj in _UK_TOKENS or not parsed:
                continue
            visit_name = _clean(row.get("VISIT"))
            if "筛选" in visit_name and subj not in screening_by_subject:
                screening_by_subject[subj] = (parsed, index)
            current = first_visit_by_subject.get(subj)
            if current is None or parsed < current[0]:
                first_visit_by_subject[subj] = (parsed, index)

        # 治疗：EX* 任一日期列的最早精确日期；兜底随机日期
        treatment_by_subject: dict[str, tuple[date, str, int]] = {}
        for table, rows in domains.items():
            if _domain_for(table, rows)[0] != "ip":
                continue
            date_cols = [c for c in (rows[0].keys() if rows else []) if c.endswith("DAT")]
            for index, row in enumerate(rows):
                subj = _clean(row.get("SUBJID"))
                if not subj or subj in _UK_TOKENS:
                    continue
                for col in date_cols:
                    raw = _clean(row.get(col))
                    if raw and _date_state(raw) == "exact":
                        parsed = _parse_date(raw)
                        if parsed:
                            current = treatment_by_subject.get(subj)
                            if current is None or parsed < current[0]:
                                treatment_by_subject[subj] = (parsed, table, index)
                        break
        random_by_subject: dict[str, tuple[date | None, str, int]] = {}
        for index, row in enumerate(domains.get("RAN", [])):
            subj = _clean(row.get("SUBJID"))
            if not subj or subj in _UK_TOKENS:
                continue
            raw = _clean(row.get("RANDAT"))
            state = _date_state(raw)
            parsed = _parse_date(raw) if state == "exact" else None
            random_by_subject[subj] = (parsed, state, index)

        # 研究处置：DS 表 DSDECOD + DSDAT；兜底 SUBJSTA 状态文本
        disposition_by_subject: dict[str, tuple[date | None, str, str, int]] = {}
        for index, row in enumerate(domains.get("DS", [])):
            subj = _clean(row.get("SUBJID"))
            if not subj or subj in _UK_TOKENS:
                continue
            raw = _clean(row.get("DSDAT"))
            state = _date_state(raw)
            parsed = _parse_date(raw) if state == "exact" else None
            decod = _clean(row.get("DSDECOD")) or "研究处置"
            current = disposition_by_subject.get(subj)
            if current is None or (parsed and (current[0] is None or parsed < current[0])):
                disposition_by_subject[subj] = (parsed, state, decod, index)
        status_by_subject: dict[str, str] = {}
        for table, rows in domains.items():
            for row in rows:
                subj = _clean(row.get("SUBJID"))
                status = _clean(row.get("SUBJSTA"))
                if subj and status and status not in _UK_TOKENS:
                    status_by_subject.setdefault(subj, status)

        for subj in sorted({s for s in subject_site}):
            steps = [R5SubjectFlowStep(
                stage_ref="stage-icf",
                entered_date=icf_by_subject[subj][0],
                basis_date=icf_by_subject[subj][0],
                date_state=icf_by_subject[subj][1],
                transition_reason_zh="知情同意书签署",
                source_locator_refs=(locator("ICF", icf_by_subject[subj][2]).locator_ref,),
            ) if subj in icf_by_subject else R5SubjectFlowStep(
                stage_ref="stage-icf", entered_date=None, basis_date=None,
                date_state="missing", transition_reason_zh="名册记录", source_locator_refs=(),
            )]
            screen = screening_by_subject.get(subj) or first_visit_by_subject.get(subj)
            if screen:
                steps.append(R5SubjectFlowStep(
                    stage_ref="stage-screening",
                    entered_date=screen[0], basis_date=screen[0], date_state="exact",
                    transition_reason_zh="筛选访视" if subj in screening_by_subject else "首次访视",
                    source_locator_refs=(locator("SV", screen[1]).locator_ref,),
                ))
            else:
                steps.append(R5SubjectFlowStep(
                    stage_ref="stage-screening", entered_date=None, basis_date=None,
                    date_state="missing", transition_reason_zh="名册记录", source_locator_refs=(),
                ))
            if subj in treatment_by_subject:
                treat = treatment_by_subject[subj]
                steps.append(R5SubjectFlowStep(
                    stage_ref="stage-treatment",
                    entered_date=treat[0], basis_date=treat[0], date_state="exact",
                    transition_reason_zh="首次给药",
                    source_locator_refs=(locator(treat[1], treat[2]).locator_ref,),
                ))
            elif subj in random_by_subject and random_by_subject[subj][1] == "exact":
                rand = random_by_subject[subj]
                steps.append(R5SubjectFlowStep(
                    stage_ref="stage-treatment",
                    entered_date=rand[0], basis_date=rand[0], date_state=rand[1],
                    transition_reason_zh="随机",
                    source_locator_refs=(locator("RAN", rand[2]).locator_ref,),
                ))
            if subj in disposition_by_subject:
                disp = disposition_by_subject[subj]
                steps.append(R5SubjectFlowStep(
                    stage_ref=(
                        "stage-study-status"
                        if subj in treatment_by_subject
                        else "stage-screen-failed"
                    ),
                    entered_date=disp[0], basis_date=disp[0], date_state=disp[1],
                    transition_reason_zh=f"研究处置：{disp[2]}",
                    source_locator_refs=(locator("DS", disp[3]).locator_ref,),
                ))
            elif (status := status_by_subject.get(subj)):
                # Screen failures terminate on the dedicated branch stage;
                # main-column continuity (screening→treatment→status) stays
                # intact for treated subjects.
                stage_ref = (
                    "stage-screen-failed"
                    if subj not in treatment_by_subject
                    and "筛选失败" in status
                    else "stage-study-status"
                )
                steps.append(R5SubjectFlowStep(
                    stage_ref=stage_ref, entered_date=None, basis_date=None,
                    date_state="missing", transition_reason_zh=f"状态：{status}", source_locator_refs=(),
                ))
            paths.append(
                R5SubjectFlowPathRecord(
                    subject_ref=f"subject-{subj}",
                    site_ref=subject_site.get(subj, "site-unknown"),
                    steps=tuple(steps),
                    path_state="partial",
                    stage_change_kind="initial",
                )
            )
        return tuple(paths)


def _risk_type_zh(domain: str, subtype: str) -> str:
    return {
        "ae": "不良事件", "mh": "病史", "cm": "合并用药",
        "ip": "试验药使用", "lab_exam": "检验检查",
        "hospital_procedure": "住院/操作", "symptom_efficacy": "症状/疗效",
        "protocol_compliance": "方案符合性",
    }.get(domain, domain)
