"""Continuity result reconstruction for the public R7 product view."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from ...graph.store import Store
from ...projections.product_adapter import R5ProductAdapter
from ...runtime import launch_registry as lr
from ...runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .contracts import ProductPublicationError
from .continuity_contracts import (
    _CONTINUITY_ATTENTION_TEXTS,
    _CONTINUITY_DATA_CHANGE_KINDS_ZH,
    _CONTINUITY_DISPOSITIONS_ZH,
    _CONTINUITY_RISK_CHANGE_KINDS_ZH,
    _SEVERITY_RANK,
    _continuity_row_sort_key,
    _normalize_severity_zh,
    _validate_continuity_risk_semantics,
    ProductContinuityChangeCounts,
    ProductContinuityComparison,
    ProductContinuityIdentity,
    ProductContinuityResponse,
    ProductContinuityRow,
)
from .public_text import _SECRET_VALUE, _public_continuity_text
from .route_utils import _workspace_dir


def build_public_continuity_envelope(
    root: Path,
    *,
    registry: lr.LaunchRegistry,
    launch: lr.LaunchRecord,
    publication: lr.ResultPublication,
    adapter: R5ProductAdapter,
    result_context_token: str,
    site_ref: Optional[str] = None,
) -> dict[str, Any]:
    try:
        plan = registry.get_continuity_plan(
            project_id=launch.project_id, target_run_id=launch.run_id
        )
    except Exception as exc:
        raise ProductPublicationError("continuity_unavailable") from exc

    if (
        plan.status != lr.CONTINUITY_PLAN_STATE_PUBLISHED
        or plan.project_id != launch.project_id
        or plan.target_run_id != launch.run_id
        or plan.mode != launch.mode
        or plan.target_snapshot_id != publication.snapshot_token
        or plan.target_data_cutoff != publication.data_cutoff
        or plan.r5_authority_digest != publication.r5_authority_packet_digest
        or plan.r6_publication_digest != publication.publication_fingerprint
        or plan.r6_receipt_digest != publication.receipt_set_digest
    ):
        raise ProductPublicationError("continuity_unavailable")
    if plan.r6_output_set_digest != publication.r6_output_set_digest:
        raise ProductPublicationError("continuity_unavailable")

    try:
        packet = adapter.get_authority_packet(
            project_ref=launch.project_id,
            run_ref=launch.run_id,
            snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
            cutoff_ref=publication.data_cutoff,
        )
    except Exception as exc:
        raise ProductPublicationError("continuity_unavailable") from exc
    def unique_map(values: Sequence[Any], key_name: str) -> dict[str, Any]:
        mapped: dict[str, Any] = {}
        for value in values:
            key = str(getattr(value, key_name, "") or "").strip()
            if not key or key in mapped:
                raise ProductPublicationError("continuity_unavailable")
            mapped[key] = value
        return mapped

    site_map = unique_map(packet.sites, "site_ref")
    site_audience_map = unique_map(packet.site_audience, "site_ref")
    if set(site_audience_map) != set(site_map):
        raise ProductPublicationError("continuity_unavailable")
    subject_map = unique_map(packet.subjects, "subject_ref")
    event_map = unique_map(packet.events, "event_ref")
    source_map = unique_map(packet.sources, "locator_ref")
    risk_by_ref = unique_map(packet.risks, "risk_ref")
    risk_by_instance = unique_map(packet.risks, "risk_instance_ref")

    runtime_dir = _workspace_dir(root, launch.project_id) / RUNTIME_DIR_NAME
    artifact_envelopes: dict[str, Any] = {}
    artifact_atoms: dict[tuple[str, str, str], Any] = {}
    r1_store = Store(
        runtime_dir / RUNTIME_DB_NAME,
        runtime_dir / ARTIFACT_DIR_NAME,
    )
    try:
        for member_id in publication.artifact_member_ids:
            envelope = r1_store.get_artifact(member_id)
            if not r1_store.verify_artifact(member_id):
                raise ProductPublicationError("continuity_unavailable")
            artifact_envelopes[member_id] = envelope
            from packages.medical_monitoring.runtime.continuity_bridge import (
                extract_atomic_items,
            )

            for atom in extract_atomic_items(
                [envelope.payload],
                mode=launch.mode,
                output_artifact_map={envelope.node_id: envelope.artifact_id},
            ):
                atom_key = (member_id, atom.object_type, atom.object_id)
                if atom_key in artifact_atoms:
                    raise ProductPublicationError("continuity_unavailable")
                artifact_atoms[atom_key] = atom
    except Exception as exc:
        raise ProductPublicationError("continuity_unavailable") from exc
    finally:
        r1_store.close()

    basis_raw = (
        str(plan.execution_basis or launch.execution_basis or "")
        .strip()
        .lower()
    )
    if basis_raw in {"incremental", "增量分析"}:
        basis_text = "增量分析"
    elif basis_raw in {"full", "全量分析", ""}:
        basis_text = "全量分析"
    else:
        raise ProductPublicationError("continuity_unavailable")

    if plan.baseline is None:
        source_run_text = ""
        comparison_text = "本轮为首次全面分析，无比较基线"
    else:
        baseline_cutoff = str(
            plan.baseline.source_data_cutoff or ""
        ).strip()
        if not baseline_cutoff:
            source_run_text = ""
            comparison_text = "本轮为首次全面分析，无比较基线"
        else:
            try:
                date.fromisoformat(baseline_cutoff)
            except ValueError as exc:
                raise ProductPublicationError("continuity_unavailable") from exc
            source_run_text = f"{baseline_cutoff} 监查批次"
            comparison_text = "已与上次监查结果比较"

    rows: list[dict[str, Any]] = []
    all_risk_rows: list[dict[str, Any]] = []
    seen_risk_instances: set[str] = set()

    for item in plan.items:
        if item.object_type == "evidence_binding":
            continue
        if item.object_type not in {
            "risk_instance",
            "query_draft",
            "mode_output_item",
        }:
            raise ProductPublicationError("continuity_unavailable")

        if (
            item.artifact_verified is False
            or item.artifact_member_verified is False
            or not item.source_artifact_id
            or item.source_artifact_id not in publication.artifact_member_ids
        ):
            raise ProductPublicationError("continuity_unavailable")
        source_artifact = artifact_envelopes[item.source_artifact_id]
        if (
            not item.source_artifact_sha256
            or item.source_artifact_sha256 != source_artifact.content_hash
            or item.source_run_id
            and item.source_run_id != source_artifact.run_id
            or not item.source_object_id
            or not item.source_identity
            or not item.target_object_id
            or item.target_object_id != item.object_ref
        ):
            raise ProductPublicationError("continuity_unavailable")
        source_atom = artifact_atoms.get(
            (
                item.source_artifact_id,
                item.object_type,
                item.source_object_id,
            )
        )
        if source_atom is None or source_atom.item_digest != item.source_identity:
            raise ProductPublicationError("continuity_unavailable")
        if item.object_type == "risk_instance":
            obj_type = "risk"
            obj_type_text = "风险"
        elif item.object_type == "query_draft":
            obj_type = "query_draft"
            obj_type_text = "Query 草稿"
        else:
            obj_type = "monitoring_output"
            obj_type_text = "监查结果项"

        change_kind = str(getattr(item, "risk_change_kind", None) or getattr(item, "change_kind", None) or "").strip().lower()
        if change_kind not in _CONTINUITY_RISK_CHANGE_KINDS_ZH:
            raise ProductPublicationError("continuity_unavailable")
        if obj_type == "risk":
            _validate_continuity_risk_semantics(item, change_kind)
        change_text = _CONTINUITY_RISK_CHANGE_KINDS_ZH[change_kind]

        disposition = str(item.disposition or "").strip().lower()
        if disposition not in _CONTINUITY_DISPOSITIONS_ZH:
            raise ProductPublicationError("continuity_unavailable")
        disposition_text = _CONTINUITY_DISPOSITIONS_ZH[disposition]

        data_change_kind = str(item.data_change_kind or "").strip().lower()
        if data_change_kind not in _CONTINUITY_DATA_CHANGE_KINDS_ZH:
            raise ProductPublicationError("continuity_unavailable")
        data_change_text = _CONTINUITY_DATA_CHANGE_KINDS_ZH[data_change_kind]

        sev_before_raw = getattr(item, "prior_severity", None)
        sev_after_raw = getattr(item, "current_severity", None)
        sev_before_zh = _normalize_severity_zh(sev_before_raw)
        sev_after_zh = _normalize_severity_zh(sev_after_raw)

        need_severity_attention = False
        if obj_type == "risk" and change_kind == "new":
            if sev_before_zh != "" or sev_after_zh not in {"高", "中", "低"}:
                need_severity_attention = True
            sev_before_zh = ""
        elif change_kind == "closed":
            if sev_before_zh not in {"高", "中", "低"} or sev_after_zh != "":
                need_severity_attention = True
            sev_after_zh = ""
        elif change_kind in {"upgraded", "downgraded", "continued"}:
            if (
                sev_before_zh not in {"高", "中", "低"}
                or sev_after_zh not in {"高", "中", "低"}
            ):
                raise ProductPublicationError("continuity_unavailable")
            rank_before = _SEVERITY_RANK[sev_before_zh]
            rank_after = _SEVERITY_RANK[sev_after_zh]
            if change_kind == "upgraded" and not (rank_after > rank_before):
                raise ProductPublicationError("continuity_unavailable")
            if change_kind == "downgraded" and not (rank_after < rank_before):
                raise ProductPublicationError("continuity_unavailable")
            if change_kind == "continued" and not (rank_after == rank_before):
                raise ProductPublicationError("continuity_unavailable")
        elif obj_type == "risk" and change_kind == "reopened":
            if sev_after_zh not in {"高", "中", "低"}:
                need_severity_attention = True
        elif obj_type == "risk" and change_kind == "needs_rejudgment":
            if sev_after_zh not in {"高", "中", "低"}:
                need_severity_attention = True

        ev_summary = (
            item.evidence_summary
            if isinstance(item.evidence_summary, Mapping)
            else {}
        )
        risk_ref_hint = str(ev_summary.get("risk_ref") or "").strip()
        risk_instance_hint = str(
            ev_summary.get("risk_instance_ref") or ""
        ).strip()
        matching_risk = (
            risk_by_instance.get(risk_instance_hint)
            or risk_by_ref.get(risk_ref_hint)
            or risk_by_instance.get(item.object_ref)
            or risk_by_ref.get(item.object_ref)
        )
        if obj_type == "risk":
            if matching_risk is None:
                raise ProductPublicationError("continuity_unavailable")
            if (
                risk_ref_hint and risk_ref_hint != matching_risk.risk_ref
                or risk_instance_hint
                and risk_instance_hint != matching_risk.risk_instance_ref
            ):
                raise ProductPublicationError("continuity_unavailable")
            event_ref = matching_risk.event_ref or ""
            event = event_map.get(event_ref) if event_ref else None
            if event_ref and event is None:
                raise ProductPublicationError("continuity_unavailable")
            row_site_ref = matching_risk.site_ref
            row_subject_ref = matching_risk.subject_ref
            row_risk_ref = matching_risk.risk_ref
            row_risk_instance_ref = matching_risk.risk_instance_ref
            row_risk_anchor_ref = matching_risk.risk_anchor_ref
            authoritative_locators = tuple(matching_risk.source_locator_refs)
            if event is not None and (
                matching_risk.risk_anchor_ref not in event.risk_anchor_refs
            ):
                raise ProductPublicationError("continuity_unavailable")
            authority_severity_zh = _normalize_severity_zh(matching_risk.severity)
            if not need_severity_attention and (
                (change_kind == "closed" and sev_before_zh != authority_severity_zh)
                or (change_kind != "closed" and sev_after_zh != authority_severity_zh)
            ):
                raise ProductPublicationError("continuity_unavailable")
        else:
            risk_ref_match = risk_by_ref.get(risk_ref_hint) if risk_ref_hint else None
            risk_instance_match = (
                risk_by_instance.get(risk_instance_hint)
                if risk_instance_hint
                else None
            )
            if (
                risk_ref_hint
                and risk_ref_match is None
                or risk_instance_hint
                and risk_instance_match is None
                or risk_ref_match is not None
                and risk_instance_match is not None
                and risk_ref_match is not risk_instance_match
            ):
                raise ProductPublicationError("continuity_unavailable")
            event_ref = str(ev_summary.get("event_ref") or "").strip()
            event = event_map.get(event_ref)
            if event is None:
                raise ProductPublicationError("continuity_unavailable")
            row_site_ref = event.site_ref
            row_subject_ref = event.subject_ref
            row_risk_ref = matching_risk.risk_ref if matching_risk is not None else ""
            row_risk_instance_ref = (
                matching_risk.risk_instance_ref if matching_risk is not None else ""
            )
            row_risk_anchor_ref = (
                matching_risk.risk_anchor_ref if matching_risk is not None else ""
            )
            authoritative_locators = tuple(event.source_locator_refs)
            if (
                matching_risk is not None
                and (matching_risk.event_ref or "") != event_ref
            ):
                raise ProductPublicationError("continuity_unavailable")

        subject = subject_map.get(row_subject_ref)
        if (
            subject is None
            or row_site_ref not in site_map
            or subject.site_ref != row_site_ref
            or event is not None
            and (event.subject_ref != row_subject_ref or event.site_ref != row_site_ref)
        ):
            raise ProductPublicationError("continuity_unavailable")
        for hint, expected in (
            (ev_summary.get("site_ref"), row_site_ref),
            (ev_summary.get("subject_ref"), row_subject_ref),
            (ev_summary.get("risk_anchor_ref"), row_risk_anchor_ref),
            (ev_summary.get("event_ref"), event_ref),
        ):
            if hint not in (None, "") and str(hint).strip() != expected:
                raise ProductPublicationError("continuity_unavailable")

        row_site_label = _public_continuity_text(
            site_audience_map[row_site_ref].site_label
        )
        row_subject_label = _public_continuity_text(subject.subject_label)
        row_title = _public_continuity_text(
            event.label_zh
            if event is not None
            else matching_risk.risk_type_zh
        )
        row_reason_text = _public_continuity_text(item.reason)
        row_date_label = (
            event.start_date.isoformat()
            if event is not None and event.start_date is not None
            else ""
        )
        row_window_start = str(ev_summary.get("window_start") or "").strip()
        row_window_end = str(ev_summary.get("window_end") or "").strip()
        try:
            parsed_window_start = date.fromisoformat(row_window_start)
            parsed_window_end = date.fromisoformat(row_window_end)
        except ValueError as exc:
            raise ProductPublicationError("continuity_unavailable") from exc
        if parsed_window_start > parsed_window_end:
            raise ProductPublicationError("continuity_unavailable")

        row_event_ref = event_ref

        if any(locator not in source_map for locator in authoritative_locators):
            raise ProductPublicationError("continuity_unavailable")
        requested_locator = str(
            ev_summary.get("source_locator_ref") or ""
        ).strip()
        if requested_locator and requested_locator not in authoritative_locators:
            raise ProductPublicationError("continuity_unavailable")
        loc_ref = requested_locator or (
            authoritative_locators[0] if len(authoritative_locators) == 1 else ""
        )
        src_count = len(authoritative_locators) if loc_ref else 0
        raw_source_count = ev_summary.get("source_count")
        if raw_source_count is not None and (
            type(raw_source_count) is not int
            or raw_source_count < 0
            or raw_source_count != src_count
        ):
            raise ProductPublicationError("continuity_unavailable")

        if data_change_kind == "missing":
            attention_text = "未见记录不代表风险已解除"
        elif (
            change_kind == "needs_rejudgment"
            or disposition == "blocked_incompatible"
            or data_change_kind == "cannot_compare"
            or not getattr(item, "identity_compatible", True)
            or not getattr(item, "source_compatible", True)
            or not getattr(item, "output_contract_compatible", True)
            or getattr(item, "identity_ambiguous", False)
            or getattr(item, "lineage_changed", False)
            or getattr(item, "data_missing", False)
        ):
            attention_text = "身份或数据不完整，需重新判断"
        elif need_severity_attention:
            attention_text = "等级变化待确认"
        elif not loc_ref or src_count == 0:
            attention_text = "原始记录位置待确认"
        else:
            attention_text = ""

        if attention_text not in _CONTINUITY_ATTENTION_TEXTS:
            raise ProductPublicationError("continuity_unavailable")

        ordinal = int(item.ordinal)
        if ordinal < 0:
            raise ProductPublicationError("continuity_unavailable")
        row_ref = f"continuity-row-{ordinal}"

        row_dict = {
            "row_ref": row_ref,
            "object_type": obj_type,
            "object_type_text": obj_type_text,
            "ordinal": ordinal,
            "change_kind": change_kind,
            "change_text": change_text,
            "disposition": disposition,
            "disposition_text": disposition_text,
            "data_change_kind": data_change_kind,
            "data_change_text": data_change_text,
            "severity_before_text": sev_before_zh,
            "severity_after_text": sev_after_zh,
            "title": row_title,
            "reason_text": row_reason_text,
            "attention_text": attention_text,
            "site_ref": row_site_ref,
            "site_label": row_site_label,
            "subject_ref": row_subject_ref,
            "subject_label": row_subject_label,
            "date_label": row_date_label,
            "window_start": row_window_start,
            "window_end": row_window_end,
            "risk_ref": row_risk_ref,
            "risk_instance_ref": row_risk_instance_ref,
            "risk_anchor_ref": row_risk_anchor_ref,
            "event_ref": row_event_ref,
            "source_locator_ref": loc_ref,
            "source_count": src_count,
        }
        validated_row = ProductContinuityRow(**row_dict).model_dump()

        if site_ref is not None and row_site_ref != site_ref:
            continue

        if obj_type == "risk":
            if (
                not row_risk_instance_ref
                or row_risk_instance_ref in seen_risk_instances
            ):
                raise ProductPublicationError("continuity_unavailable")
            seen_risk_instances.add(row_risk_instance_ref)
            all_risk_rows.append(validated_row)

        rows.append(validated_row)

    counts = {
        "new": 0,
        "upgraded": 0,
        "continued": 0,
        "downgraded": 0,
        "closed": 0,
        "reopened": 0,
        "needs_rejudgment": 0,
        "mid_high_total": 0,
        "changed_subject_count": 0,
    }
    changed_subjects: set[str] = set()
    for r in all_risk_rows:
        k = r["change_kind"]
        if k in counts:
            counts[k] += 1
        else:
            raise ProductPublicationError("continuity_unavailable")
        if r["severity_after_text"] in {"高", "中"}:
            counts["mid_high_total"] += 1
        if k in {
            "new",
            "upgraded",
            "downgraded",
            "closed",
            "reopened",
            "needs_rejudgment",
        }:
            s = r["subject_ref"]
            if s:
                changed_subjects.add(s)

    counts["changed_subject_count"] = len(changed_subjects)

    if (
        counts["new"]
        + counts["upgraded"]
        + counts["continued"]
        + counts["downgraded"]
        + counts["closed"]
        + counts["reopened"]
        + counts["needs_rejudgment"]
        != len(all_risk_rows)
    ):
        raise ProductPublicationError("continuity_unavailable")

    validated_counts = ProductContinuityChangeCounts(**counts).model_dump()
    sorted_rows = sorted(rows, key=_continuity_row_sort_key)
    total_count = len(sorted_rows)
    truncated = total_count > 200
    shown_rows = sorted_rows[:200]
    shown_count = len(shown_rows)

    comparison_dict = {
        "available": True,
        "basis_text": basis_text,
        "comparison_text": comparison_text,
        "source_run_text": source_run_text,
        "change_counts": validated_counts,
        "rows": shown_rows,
        "shown_count": shown_count,
        "total_count": total_count,
        "truncated": truncated,
    }
    validated_comparison = ProductContinuityComparison(
        **comparison_dict
    ).model_dump()

    identity_dict: dict[str, Any] = {
        "project_ref": launch.project_id,
        "public_run_token": launch.public_run_token,
        "snapshot_token": publication.snapshot_token,
        "data_cutoff_text": publication.data_cutoff,
        "mode_text": launch.mode_text,
        "site_scope_text": "、".join(
            _public_continuity_text(site_audience_map[s].site_label)
            for s in publication.site_coverage
        ),
    }
    if site_ref is not None:
        identity_dict["site_ref"] = site_ref

    validated_identity = ProductContinuityIdentity(**identity_dict).model_dump(
        exclude_none=True
    )

    public_blob = json.dumps(
        {"identity": validated_identity, "comparison": validated_comparison},
        ensure_ascii=False,
    ).casefold()
    if _SECRET_VALUE.search(public_blob) or any(
        marker in public_blob
        for marker in (
            '"run_id"',
            '"run_ref"',
            '"snapshot_ref"',
            '"cutoff_ref"',
            '"authority_hash"',
            '"authority_receipt',
            '"packet_digest"',
            '"packet_identity"',
            '"s4_',
            '"r5_',
        )
    ):
        raise ProductPublicationError("continuity_unavailable")

    response_digest = lr.content_digest(
        {"identity": validated_identity, "comparison": validated_comparison}
    )

    response_dict = {
        "result_context_token": result_context_token,
        "identity": validated_identity,
        "comparison": validated_comparison,
        "response_digest": response_digest,
    }
    return ProductContinuityResponse(**response_dict).model_dump(
        exclude_none=True
    )

__all__ = ["build_public_continuity_envelope"]
