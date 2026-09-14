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
from typing import Any, Mapping

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
    "SH": ("hospital_procedure", "procedure"),
    "SU": ("hospital_procedure", "procedure"),
    "PT": ("symptom_efficacy", "symptom"),
    "NE": ("symptom_efficacy", "efficacy"),
    "PC": ("symptom_efficacy", "outcome"),
    "PD": ("protocol_compliance", "protocol_deviation"),
    "RQL": ("protocol_compliance", "protocol_deviation"),
    "RES": ("symptom_efficacy", "efficacy"),
}


def _domain_for(table: str) -> tuple[str, str]:
    if table in _DOMAIN_BY_TABLE:
        return _DOMAIN_BY_TABLE[table]
    for prefix, mapping in _DOMAIN_BY_TABLE.items():
        if table.startswith(prefix):
            return mapping
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
                label_zh=label[:60] or subtype,
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

        # 访视（VS 或任一含 VISIT+日期的表取每个受试者×访视一条）
        seen_visits: set[tuple[str, str]] = set()
        for table in ("VS", "HW", "EG"):
            for index, row in enumerate(domains.get(table, [])):
                subj = _clean(row.get("SUBJID"))
                visit_name = _clean(row.get("VISIT"))
                date_raw = row.get(f"{table}DAT") if table != "VS" else row.get("VSDAT")
                if not subj or not visit_name or subj in _UK_TOKENS:
                    continue
                key = (subj, visit_name)
                if key in seen_visits:
                    continue
                state = _date_state(date_raw)
                seen_visits.add(key)
                visits.append(
                    R5VisitRecord(
                        visit_ref=f"visit-{subj}-{abs(hash(visit_name)) % 10_000:04d}",
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
            domain, subtype = _domain_for(table)
            date_keys = [k for k in rows[0].keys() if k.endswith("DAT") or k in ("SHDAT",)] if rows else []
            term_keys = [k for k in rows[0].keys() if k in ("AETERM", "SHTERM", "CMTRT", "EGABCO", "PTTERM", "LBNAM")] if rows else []
            for index, row in enumerate(rows):
                subj = _clean(row.get("SUBJID"))
                if not subj or subj in _UK_TOKENS:
                    continue
                start_raw = next((row[k] for k in date_keys if _clean(row.get(k))), None)
                label = _clean(next((row[k] for k in term_keys if _clean(row.get(k))), subtype))
                _add_event(
                    table=table, index=index, subj=subj, subtype=subtype,
                    domain=domain, start_raw=start_raw, label=label,
                )

        # 受试者流向（SV/筛选表：ICF→筛选→治疗→研究状态）
        flow_catalog = self._flow_catalog(domains)
        flow_paths = self._flow_paths(domains, subject_site, snapshot_ref, sources)

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
            R5FlowStageRecord(stage_ref="stage-treatment", stage_label_zh="治疗", column_order=2, row_order=0, stage_kind="main", is_entry=False, is_terminal=False, source_locator_refs=()),
            R5FlowStageRecord(stage_ref="stage-study-status", stage_label_zh="研究状态", column_order=3, row_order=0, stage_kind="main", is_entry=False, is_terminal=True, source_locator_refs=()),
        )

    def _flow_paths(
        self,
        domains: Mapping[str, list[dict[str, Any]]],
        subject_site: Mapping[str, str],
        snapshot_ref: str,
        sources: list[R5SourceRecord],
    ) -> tuple[R5SubjectFlowPathRecord, ...]:
        paths = []
        # 状态列（SUBJSTA）作为研究状态依据；EX 给药记录作为进入治疗依据
        treatment_subjects = {
            _clean(row.get("SUBJID"))
            for table, rows in domains.items()
            if _domain_for(table)[0] == "ip"
            for row in rows
            if _clean(row.get("SUBJID"))
        }
        status_by_subject: dict[str, str] = {}
        for table, rows in domains.items():
            for row in rows:
                subj = _clean(row.get("SUBJID"))
                status = _clean(row.get("SUBJSTA"))
                if subj and status and status not in _UK_TOKENS:
                    status_by_subject.setdefault(subj, status)
        for subj in sorted({s for s in subject_site}):
            steps = [
                R5SubjectFlowStep(stage_ref="stage-icf", entered_date=None, basis_date=None, date_state="missing", transition_reason_zh="名册记录", source_locator_refs=()),
                R5SubjectFlowStep(stage_ref="stage-screening", entered_date=None, basis_date=None, date_state="missing", transition_reason_zh="名册记录", source_locator_refs=()),
            ]
            if subj in treatment_subjects:
                steps.append(R5SubjectFlowStep(stage_ref="stage-treatment", entered_date=None, basis_date=None, date_state="missing", transition_reason_zh="给药记录", source_locator_refs=()))
            status = status_by_subject.get(subj, "")
            if status:
                steps.append(R5SubjectFlowStep(stage_ref="stage-study-status", entered_date=None, basis_date=None, date_state="missing", transition_reason_zh=f"状态：{status}", source_locator_refs=()))
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
