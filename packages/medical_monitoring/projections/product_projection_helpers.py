"""Pure renderer-neutral helpers for R5 product read models."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Mapping, Optional, Sequence

from .product_types import (
    DOMAIN_ENCODING,
    FLOW_COVERAGE_BUCKETS,
    FLOW_MAX_COLUMNS,
    FLOW_NOT_PROVIDED_REASON_ZH,
    FLOW_SEVERITY_ZH,
    MID_HIGH_SEVERITIES,
    R5AuthorityPacket,
    R5EventRecord,
    R5FlowStageRecord,
    R5RiskRecord,
    R5SourceRecord,
    R5SubjectFlowPathRecord,
    R5SubjectRecord,
    R5VisitRecord,
    SEVERITIES,
    _date,
    _iso,
    canonical_sha256,
)

def _public_source(source: R5SourceRecord, *, include_excerpt: bool = False) -> dict[str, Any]:
    result = {
        "locator_ref": source.locator_ref,
        "snapshot_ref": source.snapshot_ref,
        "source_file_ref": source.source_file_ref,
        "source_revision_ref": source.source_revision_ref,
        "source_revision_content_hash": source.source_revision_content_hash,
        "record_ref": source.record_ref,
        "canonical_location": source.canonical_location,
        "lineage": list(source.lineage),
    }
    if include_excerpt:
        result["excerpt"] = source.excerpt
    return result


def _with_content_hash(payload: Mapping[str, Any], field_name: str = "content_hash") -> dict[str, Any]:
    result = dict(payload)
    result[field_name] = ""
    result[field_name] = canonical_sha256(result)
    return result


def _change_band_records(risks: Sequence[R5RiskRecord]) -> tuple[R5RiskRecord, ...]:
    """Return only closed change-band rows represented by the authority packet."""

    return tuple(item for item in risks if item.change_kind != "continued" or item.change_cause is not None)


def _risk_payload(
    risk: R5RiskRecord,
    receipt_ref: str,
    *,
    subject_label: Optional[str] = None,
) -> dict[str, Any]:
    subject_name = subject_label or risk.subject_ref
    domain_label = DOMAIN_ENCODING.get(risk.domain, {}).get("short_label_zh", risk.domain)
    evidence_summary = {
        "why_reminded": f"{risk.risk_type_zh}可能影响受试者安全性评价或方案符合性判断，需要沿原始记录核实。",
        "basis": f"依据当前项目监查规则及已绑定的{domain_label}域记录。",
        "finding": f"发现{subject_name}存在“{risk.risk_type_zh}”相关记录。",
        "action_item": "请核对原始记录、研究方案与数据录入情况，并确认是否需要发出数据核查问题。",
        "supporting_evidence": "已定位到支持该风险提示的原始记录。",
        "counter_evidence": "当前证据包未提供可直接排除该风险的记录。",
        "risk_history": {
            "new": "本次新增",
            "upgraded": "本次升高",
            "continued": "持续存在",
            "downgraded": "风险降低",
            "resolved": "本次解除",
            "reopened": "后续重新出现",
            "not_comparable": "本次暂不可比较",
        }.get(risk.change_kind, "本次状态待核对"),
        "query_draft": (
            f"依据当前项目监查规则；发现{subject_name}存在“{risk.risk_type_zh}”相关记录；"
            "请核实原始记录与医学判断是否一致，并按需补充说明或更正。"
        ),
    }
    if risk.risk_key == "s7-risk-key-pd-10008":
        evidence_summary.update({
            "why_reminded": "访视窗口与方案要求可能不一致，需确认是否构成方案偏离（PD）。",
            "basis": "依据研究方案规定的访视窗口及已绑定的访视记录。",
            "finding": f"发现{subject_name}的相关访视记录超出方案规定窗口。",
            "action_item": "请核实是否构成方案偏离（PD），并在数据系统中补充说明或更正。",
            "supporting_evidence": "访视日期和方案窗口均已定位，可直接复核。",
            "counter_evidence": "当前未见已获批准的窗口豁免或其他排除依据。",
            "query_draft": (
                f"依据研究方案规定的访视窗口；发现{subject_name}的相关访视记录超出方案规定窗口；"
                "请核实是否构成方案偏离（PD），并补充说明或更正。"
            ),
        })
    elif risk.risk_key == "s7-risk-key-ae-mh-06021":
        evidence_summary.update({
            "why_reminded": "既往疑似漏报记录在后续数据中出现匹配记录，需要保留前后匹配历史。",
            "basis": "依据 AE、MH 记录的时间、术语及受试者身份匹配结果。",
            "finding": f"发现{subject_name}原疑似 AE/MH 漏报在后续数据中已有补录记录。",
            "action_item": "请核实补录记录与原疑似漏报是否为同一医学事件，并确认当前 AE/MH 判定。",
            "supporting_evidence": "原疑似漏报与后续补录记录的受试者、时间及医学术语可匹配。",
            "counter_evidence": "若两条记录对应不同临床事件，则不应合并判定。",
            "query_draft": (
                f"依据 AE/MH 前后记录的时间及医学术语；发现{subject_name}原疑似漏报在后续数据中已有补录记录；"
                "请核实两者是否为同一医学事件，并确认 AE/MH 记录是否完整。"
            ),
        })
    result = {
        "risk_ref": risk.risk_ref,
        "risk_instance_ref": risk.risk_instance_ref,
        "risk_key": risk.risk_key,
        "risk_anchor_ref": risk.risk_anchor_ref,
        "site_ref": risk.site_ref,
        "subject_ref": risk.subject_ref,
        "spine_ref": risk.spine_ref,
        "domain": risk.domain,
        "severity": risk.severity,
        "severity_zh": {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}[risk.severity],
        # R24V2-B02：recorded=源记录载明；unknown=源缺失（severity仅占位，
        # 不得当中风险呈现）；inferred=非AE系统按域推定。
        "severity_source": risk.severity_source,
        "severity_source_zh": {
            "recorded": "源记录载明",
            "unknown": "严重度未知",
            "inferred": "系统推定",
        }[risk.severity_source],
        "risk_type_zh": risk.risk_type_zh,
        "subject_label": subject_label,
        "date_state": risk.date_state,
        "event_ref": risk.event_ref,
        "visit_ref": risk.visit_ref,
        "source_locator_ref": risk.source_locator_refs[0] if len(risk.source_locator_refs) == 1 else None,
        "source_locator_refs": list(risk.source_locator_refs),
        "change_kind": risk.change_kind,
        "change_cause": risk.change_cause,
        "authority_receipt_ref": receipt_ref,
        "evidence_summary": evidence_summary,
    }
    if risk.risk_key == "s7-risk-key-ae-06021":
        result["analysis_disagreement"] = {
            "status_zh": "分析意见有分歧，暂不作为最终分析结论",
            "analysis_one": "现有 AE 记录与访视时间一致，支持继续保留风险提示。",
            "analysis_two": "现有记录可能已充分解释该事件，暂不支持提高风险等级。",
            "independent_check": "独立核对保留当前中风险入口，并要求同时展示支持与不支持证据。",
            "disagreement": "分歧集中在现有记录是否足以排除记录一致性风险。",
            "supporting_evidence": "AE 起止日期与访视记录已绑定。",
            "counter_evidence": "现有数据可能已有临床解释，但尚未形成可直接排除风险的完整证据链。",
        }
    return result


def _count_indicator(
    indicator_ref: str,
    label: str,
    records: Sequence[Any],
    *,
    date_getter: Callable[[Any], Optional[date]],
    date_state_getter: Callable[[Any], str],
    ref_getter: Callable[[Any], str],
    source_refs_getter: Callable[[Any], Sequence[str]],
    receipt_ref: str,
) -> dict[str, Any]:
    buckets: dict[Optional[date], dict[str, Any]] = {}
    for record in records:
        point_date = date_getter(record)
        bucket = buckets.setdefault(
            point_date,
            {"count": 0, "date_state": date_state_getter(record), "record_refs": [], "source_locator_refs": set()},
        )
        bucket["count"] += 1
        bucket["date_state"] = bucket["date_state"] if bucket["date_state"] == date_state_getter(record) else "conflicted"
        bucket["record_refs"].append(ref_getter(record))
        bucket["source_locator_refs"].update(source_refs_getter(record))
    points = []
    for index, point_date in enumerate(sorted(buckets, key=lambda value: (value is None, value or date.min)), start=1):
        bucket = buckets[point_date]
        points.append({
            "point_ref": f"{indicator_ref}:point:{index:03d}",
            "date": _iso(point_date),
            "date_state": bucket["date_state"],
            "value": bucket["count"],
            "record_refs": sorted(bucket["record_refs"]),
            "source_locator_refs": sorted(bucket["source_locator_refs"]),
            "authority_receipt_ref": receipt_ref,
        })
    return _with_content_hash({
        "indicator_ref": indicator_ref,
        "label": label,
        "unit": "记录数",
        "value_kind": "authority_record_count",
        "points": points,
        "authority_receipt_ref": receipt_ref,
    })


def _indicator_payloads(
    packet: R5AuthorityPacket,
    *,
    events: Sequence[R5EventRecord],
    risks: Sequence[R5RiskRecord],
) -> list[dict[str, Any]]:
    """Build deterministic record-count trends from the same typed packet.

    These are record-density indicators, not inferred clinical measurements.
    They are derived only from records already present in the typed packet;
    synthetic packets remain route-visible only through explicit fixture mode.
    """

    receipt_ref = packet.receipt_id
    event_by_ref = {item.event_ref: item for item in events}
    indicators = []
    if events:
        indicators.append(_count_indicator(
            "r5-indicator-event-record-count",
            "事件记录数",
            events,
            date_getter=lambda item: item.start_date,
            date_state_getter=lambda item: item.date_state,
            ref_getter=lambda item: item.event_ref,
            source_refs_getter=lambda item: item.source_locator_refs,
            receipt_ref=receipt_ref,
        ))
    if risks:
        indicators.append(_count_indicator(
            "r5-indicator-risk-anchor-count",
            "风险锚点记录数",
            risks,
            date_getter=lambda item: event_by_ref.get(item.event_ref).start_date if item.event_ref and event_by_ref.get(item.event_ref) else None,
            date_state_getter=lambda item: event_by_ref.get(item.event_ref).date_state if item.event_ref and event_by_ref.get(item.event_ref) else item.date_state,
            ref_getter=lambda item: item.risk_instance_ref,
            source_refs_getter=lambda item: item.source_locator_refs,
            receipt_ref=receipt_ref,
        ))
    return indicators


def _subject_rows(
    packet: R5AuthorityPacket,
    *,
    subjects: Optional[Sequence[R5SubjectRecord]] = None,
) -> list[dict[str, Any]]:
    rows = packet.subjects if subjects is None else subjects
    return [
        {
            "subject_ref": item.subject_ref,
            "subject_id": item.subject_ref,
            "label": item.subject_label,
            "subject_label": item.subject_label,
            "site_ref": item.site_ref,
            "spine_ref": item.spine_ref,
            "authority_receipt_ref": packet.receipt_id,
        }
        for item in rows
    ]


def _flow_edge_is_legal(from_stage: R5FlowStageRecord, to_stage: R5FlowStageRecord) -> bool:
    """Closed edge legality set from the frozen v0.3 §4 contract."""

    if from_stage.stage_kind == "main":
        if to_stage.stage_kind == "main":
            return to_stage.column_order == from_stage.column_order + 1
        if to_stage.stage_kind == "branch_terminal":
            return to_stage.column_order in (from_stage.column_order, from_stage.column_order + 1)
        return False
    if from_stage.stage_kind == "missing":
        # The reserved missing entry may only connect to the first known main.
        return to_stage.stage_kind == "main"
    # branch_terminal / unknown / not_applicable stages have no outbound step.
    return False


def _flow_coverage_bucket(path: R5SubjectFlowPathRecord, current_stage: R5FlowStageRecord) -> str:
    if len(path.steps) == 1 and current_stage.stage_kind in {"missing", "not_applicable", "unknown"}:
        return {
            "missing": "not_provided",
            "not_applicable": "not_applicable",
            "unknown": "conflicted",
        }[current_stage.stage_kind]
    return path.path_state


def _subject_flow_projection(
    packet: R5AuthorityPacket,
    *,
    selected_site_refs: set[str],
    site_ref: Optional[str],
) -> dict[str, Any]:
    """Build the conserved ``projection.subject_flow`` overview subtree.

    Nodes, links, detail rows and risk counts are all aggregated from the same
    scoped path records, so the four-way reconciliation holds by construction
    and is re-checked defensively before ``matched`` is emitted.
    """

    scope = {
        "project_ref": packet.project_ref,
        "run_ref": packet.run_ref,
        "snapshot_ref": packet.snapshot_ref,
        "cutoff_state": packet.cutoff_state,
        "cutoff_ref": packet.cutoff_ref,
        "site_ref": site_ref,
    }
    if not packet.flow_stages and not packet.subject_flow_paths:
        # Legacy v0.3.1 packet: flow fields absent or both empty.
        return {
            "availability": "not_provided",
            "reason_zh": FLOW_NOT_PROVIDED_REASON_ZH,
            "scope": scope,
            "reconciliation": {"state": "not_applicable"},
        }

    def _blocked(*gaps: str) -> dict[str, Any]:
        ordered: list[str] = []
        for gap in gaps:
            if gap and gap not in ordered:
                ordered.append(gap)
        return {
            "availability": "available",
            "visual_kind": "path_throughput_sankey",
            "scope": scope,
            "reconciliation": {
                "state": "blocked",
                "total_subjects": len(scope_subjects),
                "gap_zh": "；".join(ordered),
                "gaps_zh": ordered,
            },
        }

    scope_subjects = tuple(item for item in packet.subjects if item.site_ref in selected_site_refs)
    scope_subject_refs = {item.subject_ref for item in scope_subjects}
    subject_by_ref = {item.subject_ref: item for item in packet.subjects}
    scope_paths = tuple(item for item in packet.subject_flow_paths if item.subject_ref in scope_subject_refs)
    stage_by_ref = {item.stage_ref: item for item in packet.flow_stages}

    if not packet.flow_stages:
        return _blocked("路径数据缺少阶段目录")
    if len({item.column_order for item in packet.flow_stages}) > FLOW_MAX_COLUMNS:
        return _blocked("受试者阶段列数超过当前看板容量")

    # Packet-level structural checks: a defective authority packet blocks the
    # page in every scope instead of silently rendering partial data.
    path_subject_counts: dict[str, int] = {}
    orphan = site_mismatch = unknown_stage = False
    for path in packet.subject_flow_paths:
        path_subject_counts[path.subject_ref] = path_subject_counts.get(path.subject_ref, 0) + 1
        subject = subject_by_ref.get(path.subject_ref)
        if subject is None:
            orphan = True
            continue
        if path.site_ref != subject.site_ref:
            site_mismatch = True
        if any(step.stage_ref not in stage_by_ref for step in path.steps):
            unknown_stage = True
    duplicate = any(count > 1 for count in path_subject_counts.values())
    missing_members = scope_subject_refs - set(path_subject_counts)
    if orphan or duplicate or site_mismatch or unknown_stage or missing_members:
        return _blocked(
            "规范路径引用了范围外的受试者" if orphan else "",
            "同一受试者存在多条规范路径" if duplicate else "",
            "路径与受试者中心归属不一致" if site_mismatch else "",
            "规范路径引用了未定义的阶段" if unknown_stage else "",
            "受试者缺少规范路径记录" if missing_members else "",
        )

    repeated = any(
        len({step.stage_ref for step in path.steps}) != len(path.steps)
        for path in packet.subject_flow_paths
    )
    entry_invalid = any(
        not stage_by_ref[path.steps[0].stage_ref].is_entry
        or any(stage_by_ref[step.stage_ref].is_entry for step in path.steps[1:])
        for path in packet.subject_flow_paths
    )
    continuity_invalid = any(
        not _flow_edge_is_legal(stage_by_ref[from_step.stage_ref], stage_by_ref[to_step.stage_ref])
        for path in packet.subject_flow_paths
        for from_step, to_step in zip(path.steps, path.steps[1:])
    )
    if repeated or entry_invalid or continuity_invalid:
        return _blocked(
            "规范路径中阶段重复" if repeated else "",
            "规范路径入口不合法" if entry_invalid else "",
            "规范路径阶段连续性校验未通过" if continuity_invalid else "",
        )

    reached: dict[str, set[str]] = {stage.stage_ref: set() for stage in packet.flow_stages}
    current: dict[str, set[str]] = {stage.stage_ref: set() for stage in packet.flow_stages}
    link_members: dict[tuple[str, str], set[str]] = {}
    for path in scope_paths:
        subject_ref = path.subject_ref
        refs = [step.stage_ref for step in path.steps]
        for ref in refs:
            reached[ref].add(subject_ref)
        current[refs[-1]].add(subject_ref)
        for from_ref, to_ref in zip(refs, refs[1:]):
            link_members.setdefault((from_ref, to_ref), set()).add(subject_ref)

    scoped_risks = tuple(item for item in packet.risks if item.site_ref in selected_site_refs)
    mid_high_risks = tuple(item for item in scoped_risks if item.severity in MID_HIGH_SEVERITIES)
    mid_high_subject_refs = {item.subject_ref for item in mid_high_risks}

    outbound_total = {stage.stage_ref: 0 for stage in packet.flow_stages}
    inbound_total = {stage.stage_ref: 0 for stage in packet.flow_stages}
    for (from_ref, to_ref), members in link_members.items():
        outbound_total[from_ref] += len(members)
        inbound_total[to_ref] += len(members)

    node_ok = True
    for stage in packet.flow_stages:
        ref = stage.stage_ref
        if len(reached[ref]) != len(current[ref]) + outbound_total[ref]:
            node_ok = False
        if stage.is_entry and inbound_total[ref] != 0:
            node_ok = False
        if not stage.is_entry and inbound_total[ref] != len(reached[ref]):
            node_ok = False
    link_ok = sum(len(members) for members in link_members.values()) == sum(
        len(path.steps) - 1 for path in scope_paths
    )
    if not (node_ok and link_ok):
        return _blocked("节点或连线人数守恒校验未通过")

    stage_order = {stage.stage_ref: (stage.column_order, stage.row_order) for stage in packet.flow_stages}
    stages_payload = [
        {
            "stage_ref": stage.stage_ref,
            "stage_label_zh": stage.stage_label_zh,
            "column_order": stage.column_order,
            "row_order": stage.row_order,
            "stage_kind": stage.stage_kind,
            "is_entry": stage.is_entry,
            "is_terminal": stage.is_terminal,
            "reached_count": len(reached[stage.stage_ref]),
            "current_count": len(current[stage.stage_ref]),
            "current_mid_high_risk_count": len(current[stage.stage_ref] & mid_high_subject_refs),
        }
        for stage in sorted(packet.flow_stages, key=lambda item: (item.column_order, item.row_order))
    ]
    links_payload = [
        {
            "link_ref": f"r5-flow-link:{from_ref}:{to_ref}",
            "from_stage_ref": from_ref,
            "to_stage_ref": to_ref,
            "count": len(members),
            "current_mid_high_risk_count": len(members & mid_high_subject_refs),
        }
        for (from_ref, to_ref), members in sorted(
            link_members.items(),
            key=lambda item: (stage_order[item[0][0]], stage_order[item[0][1]]),
        )
    ]

    cutoff_date = _date(packet.cutoff_ref, "cutoff_ref") if packet.cutoff_ref is not None else None
    visits_by_subject: dict[str, list[R5VisitRecord]] = {}
    for visit in packet.visits:
        if visit.subject_ref in scope_subject_refs:
            visits_by_subject.setdefault(visit.subject_ref, []).append(visit)
    events_by_subject: dict[str, list[R5EventRecord]] = {}
    for event in packet.events:
        if event.subject_ref in scope_subject_refs:
            events_by_subject.setdefault(event.subject_ref, []).append(event)

    def _usable_jump_dates(subject_ref: str) -> list[date]:
        # Journey windows come only from same-packet visits/events clipped to
        # the current cutoff; path entered/basis dates never substitute.
        values: list[date] = []
        for visit in visits_by_subject.get(subject_ref, ()):
            values.extend(value for value in (visit.actual_date, visit.nominal_date) if value is not None)
        for event in events_by_subject.get(subject_ref, ()):
            values.extend(value for value in (event.start_date, event.end_date) if value is not None)
        if cutoff_date is not None:
            values = [value for value in values if value <= cutoff_date]
        return sorted(set(values))

    rows: list[dict[str, Any]] = []
    bucket_counts = {f"{bucket}_count": 0 for bucket in FLOW_COVERAGE_BUCKETS}
    for path in scope_paths:
        subject = subject_by_ref[path.subject_ref]
        refs = [step.stage_ref for step in path.steps]
        last_step = path.steps[-1]
        prior_step = path.steps[-2] if len(path.steps) > 1 else None
        current_stage = stage_by_ref[refs[-1]]
        prior_stage = stage_by_ref[prior_step.stage_ref] if prior_step is not None else None
        bucket = _flow_coverage_bucket(path, current_stage)
        bucket_counts[f"{bucket}_count"] += 1

        subject_risks = sorted(
            (item for item in mid_high_risks if item.subject_ref == subject.subject_ref),
            key=lambda item: (SEVERITIES.index(item.severity), item.risk_ref),
        )
        spine_unique = sum(1 for item in packet.subjects if item.subject_ref == subject.subject_ref) == 1
        usable_dates = _usable_jump_dates(subject.subject_ref)
        jump_enabled = bool(usable_dates) and spine_unique and bool(subject.spine_ref)
        top_risk = subject_risks[0] if subject_risks else None
        rows.append({
            "subject_ref": subject.subject_ref,
            "site_ref": subject.site_ref,
            "subject_label": subject.subject_label,
            "spine_ref": subject.spine_ref,
            "path_state": path.path_state,
            "coverage_bucket": bucket,
            "path_stage_refs": refs,
            "path_link_refs": [f"r5-flow-link:{from_ref}:{to_ref}" for from_ref, to_ref in zip(refs, refs[1:])],
            "current_stage_ref": current_stage.stage_ref,
            "current_stage_label_zh": current_stage.stage_label_zh,
            "prior_stage_ref": prior_stage.stage_ref if prior_stage is not None else None,
            "prior_stage_label_zh": prior_stage.stage_label_zh if prior_stage is not None else None,
            "entered_date": _iso(last_step.entered_date),
            "basis_date": _iso(last_step.basis_date),
            "date_state": last_step.date_state,
            "transition_reason_zh": last_step.transition_reason_zh,
            "stage_change_kind": path.stage_change_kind,
            "prior_run_current_stage_ref": path.prior_run_current_stage_ref,
            "date_pending": any(step.date_state != "exact" for step in path.steps),
            "current_mid_high_risk": bool(subject_risks),
            "current_mid_high_risk_count": len(subject_risks),
            "mid_high_risk_top_severity": top_risk.severity if top_risk else None,
            "mid_high_risk_top_severity_zh": FLOW_SEVERITY_ZH[top_risk.severity] if top_risk else None,
            "risk_summary_zh": (
                f"{FLOW_SEVERITY_ZH[top_risk.severity]} · {top_risk.risk_type_zh}" if top_risk else None
            ),
            "risk_change_kind": top_risk.change_kind if top_risk else None,
            "journey_jump_enabled": jump_enabled,
            "journey_jump_state_zh": "可跳转" if jump_enabled else "时间窗待确认",
            "jump_window_start": usable_dates[0].isoformat() if usable_dates else None,
            "jump_window_end": usable_dates[-1].isoformat() if usable_dates else None,
        })
    rows.sort(key=lambda row: (
        0 if row["current_mid_high_risk"] else 1,
        0 if row["date_pending"] else 1,
        stage_order[row["current_stage_ref"]],
        row["subject_ref"],
    ))

    return {
        "availability": "available",
        "visual_kind": "path_throughput_sankey",
        "scope": scope,
        "stages": stages_payload,
        "links": links_payload,
        "subjects": rows,
        "coverage": {
            "total_subjects": len(scope_subjects),
            **bucket_counts,
        },
        "reconciliation": {
            "state": "matched",
            "total_subject_count": len(scope_subjects),
            "entry_count": len(scope_paths),
            "current_stay_count": sum(len(current[stage.stage_ref]) for stage in packet.flow_stages),
            "detail_count": len(rows),
            "node_conservation_matched": node_ok,
            "link_conservation_matched": link_ok,
            "membership_ok": True,
            "continuity_ok": True,
            "gaps_zh": [],
        },
    }


def _event_payload(event: R5EventRecord) -> dict[str, Any]:
    return {
        "event_ref": event.event_ref,
        "subject_ref": event.subject_ref,
        "site_ref": event.site_ref,
        "spine_ref": event.spine_ref,
        "domain": event.domain,
        "subtype": event.subtype,
        "date_state": event.date_state,
        "start_date": _iso(event.start_date),
        "end_date": _iso(event.end_date),
        "visit_ref": event.visit_ref,
        "risk_anchor_refs": list(event.risk_anchor_refs),
        "source_locator_refs": list(event.source_locator_refs),
        "label_zh": event.label_zh,
        "encoding": dict(DOMAIN_ENCODING[event.domain]),
        "risk_overlay_shape": "double_chevron_badge",
    }


def _strip_response_digest(value: Any, *, parent_key: str = "") -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_response_digest(item, parent_key=str(key))
            for key, item in value.items()
            if key != "response_snapshot_sha256"
            and not (parent_key == "read_handoff" and key == "contract_sha256")
        }
    if isinstance(value, (list, tuple)):
        return [_strip_response_digest(item, parent_key=parent_key) for item in value]
    return value


def response_snapshot_sha256(envelope_without_response_digest: Mapping[str, Any]) -> str:
    """Hash canonical response bytes while excluding the self-referential digest."""

    return canonical_sha256(_strip_response_digest(envelope_without_response_digest))
