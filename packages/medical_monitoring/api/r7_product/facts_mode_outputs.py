"""Real facts-backed R6 mode outputs for the materialized-facts product lane.

Mirrors the synthetic mode-output provider protocol but derives every row
from the typed facts authority packet: severity/type aggregation for the
full-risk output and adverse-event (medium-or-higher) query findings with
their source locators for the affected-query draft. No invented findings.
"""

from __future__ import annotations

import glob
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Optional

from ...reports import mode_output as mo

_SEVERITY_ZH = {"critical": "重度", "medium": "中度", "low": "轻度"}
_DOMAIN_ZH = {
    "ae": "不良事件",
    "mh": "既往病史",
    "cm": "合并用药",
    "ip": "试验药使用",
    "lab_exam": "检验检查",
    "hospital_procedure": "住院/操作",
    "symptom_efficacy": "症状/疗效",
    "protocol_compliance": "方案符合性",
}
_MAX_FINDINGS = 200


class FactsModeOutputProvider:
    """Build the four mode outputs from the real facts authority packet."""

    def __init__(self, artifacts_dir: Optional[Path] = None) -> None:
        self._artifacts_dir = artifacts_dir

    @staticmethod
    def _binding(run_binding: Mapping[str, Any]) -> dict[str, Any]:
        binding = dict(run_binding)
        binding.setdefault("carry_forward_run_ids", [])
        binding.setdefault("mode_transition", "explicit_new_run")
        binding.setdefault("actor", "system_facts")
        if not binding.get("created_at"):
            binding["created_at"] = "2026-08-28T00:00:00Z"
        if not binding.get("knowledge_pack_version"):
            binding["knowledge_pack_version"] = "facts-kp-v1"
        if not binding.get("rule_activation_version"):
            binding["rule_activation_version"] = "facts-rules-v1"
        if not binding.get("mapping_version"):
            binding["mapping_version"] = "facts-mapping-v1"
        if not binding.get("identity_algorithm_version"):
            binding["identity_algorithm_version"] = "facts-identity-v1"
        if not binding.get("identity_algorithm_digest"):
            binding["identity_algorithm_digest"] = "facts-identity-digest-v1"
        return binding

    def get_mode_outputs(
        self,
        run_binding: Mapping[str, Any],
        r5_packet: Any,
        **_: Any,
    ) -> tuple[dict[str, Any], ...]:
        binding = self._binding(run_binding)
        mode = str(binding["mode"])
        if mode == "post_lock_pre_cfdi":
            binding.setdefault("fixed_total", True)
            binding.setdefault("locked_snapshot_hash", r5_packet.packet_digest)
            binding.setdefault("output_cutoff_ref", binding.get("data_cutoff"))
            binding.setdefault("output_revision_ref", binding.get("source_revision_id"))
            binding.setdefault("local_os_user", "local-os-user")
            binding.setdefault("acceptance_evidence_hash", "facts-acceptance-v1")
        contract = mo.build_mode_contract(mode)
        context = mo.default_entry_context_for_mode(mode, run_binding=binding)
        if mode == "post_lock_pre_cfdi":
            # 锁定版本选择必须与本次运行声明的锁字段逐字一致（默认
            # context 硬编码合成值，会与 facts 锁字段冲突）。
            context["locked_version_selection"] = {
                "local_os_user": str(binding.get("local_os_user") or "local-os-user"),
                "snapshot_hash": str(
                    binding.get("locked_snapshot_hash") or r5_packet.packet_digest
                ),
                "acceptance_evidence_hash": str(
                    binding.get("acceptance_evidence_hash") or "facts-acceptance-v1"
                ),
            }
        digest = r5_packet.packet_digest
        refs = {
            "project_id": binding["project_id"],
            "run_id": binding["run_id"],
            "data_cutoff": binding["data_cutoff"],
            "source_revision_id": binding["source_revision_id"],
            "authority_digest": digest,
            "coverage_digest": digest,
            "qc_digest": digest,
            "digest": digest,
        }
        severity_counts = Counter(risk.severity for risk in r5_packet.risks)
        # The R6 risk payload carries the actionable set (medium-or-higher)
        # with real risk ids bound to the authority closure; the full-anchor
        # picture is served by the aggregated overview projection.
        risk_rows = [
            {
                "risk_id": risk.risk_ref,
                "severity": risk.severity,
                "risk_type": risk.risk_type_zh,
                "domain": risk.domain,
            }
            for risk in r5_packet.risks
            if risk.severity in ("medium", "critical")
        ]
        if mode == "daily":
            findings = self._daily_findings(binding, r5_packet)
            return mo.build_daily_mode_outputs(
                binding,
                contract,
                authority_refs=refs,
                coverage_refs=refs,
                qc_refs=refs,
                findings=findings,
                risks=risk_rows,
                entry_context=context,
            )
        if mode == "pre_lock":
            # 发布包自身不带源修订对；比对基准取自其产品包（事实准入源）。
            product_packet = getattr(r5_packet, "product_packet", None) or r5_packet
            source_pairs = getattr(product_packet, "source_revision_content_pairs", ())
            register = [
                risk for risk in r5_packet.risks
                if risk.severity in ("critical", "high", "medium")
            ]
            risk_ids_by_site: dict[str, list[str]] = {site.site_ref: [] for site in r5_packet.sites}
            risk_ids_by_subject: dict[str, list[str]] = {}
            for risk in register:
                risk_ids_by_site.setdefault(risk.site_ref, []).append(risk.risk_ref)
                risk_ids_by_subject.setdefault(risk.subject_ref, []).append(risk.risk_ref)
            evidence_refs = [
                locator_ref
                for risk in register[:50]
                for locator_ref in risk.source_locator_refs
            ]
            return mo.build_pre_lock_mode_outputs(
                binding,
                contract,
                authority_refs=refs,
                coverage_refs=refs,
                qc_refs=refs,
                risks=risk_rows,
                population_scope={
                    "scope_kind": "project",
                    "population_id": binding["project_id"],
                    "label": "全部已核验事实受试者",
                    "site_count": len(r5_packet.sites),
                    "subject_count": len(r5_packet.subjects),
                    "risk_count": sum(severity_counts.values()),
                },
                from_source_revision_id=(
                    source_pairs[0].revision_id
                    if source_pairs
                    else f"{binding['source_revision_id']}-prior"
                ),
                revision_reason="锁库前全量风险核对（首次事实快照）",
                check_items=[
                    {
                        "level": "project",
                        "check_kind": "pre_lock_total_review",
                        "scope_id": binding["project_id"],
                        "status": "ready",
                        "risk_ids": [risk.risk_ref for risk in register[:20]],
                        "evidence_refs": evidence_refs[:5],
                        "locator": {"path": "facts.project", "record_id": binding["project_id"]},
                    },
                ] + [
                    {
                        "level": "site",
                        "check_kind": "pre_lock_site_review",
                        "scope_id": site.site_ref,
                        "site_id": site.site_ref,
                        "status": "ready",
                        "risk_ids": risk_ids_by_site.get(site.site_ref, [])[:20],
                        "evidence_refs": evidence_refs[:3],
                        "locator": {"path": "facts.site", "record_id": site.site_ref},
                    }
                    for site in r5_packet.sites
                ] + [
                    {
                        "level": "subject",
                        "check_kind": "pre_lock_subject_review",
                        "scope_id": subject.subject_ref,
                        "site_id": subject.site_ref,
                        "subject_id": subject.subject_ref,
                        "status": "ready",
                        "risk_ids": risk_ids_by_subject.get(subject.subject_ref, [])[:20],
                        "evidence_refs": evidence_refs[:3],
                        "locator": {"path": "facts.subject", "record_id": subject.subject_ref},
                    }
                    for subject in r5_packet.subjects
                ],
                entry_context=context,
            )
        if mode == "post_lock_pre_cfdi":
            return self._post_lock_outputs(binding, contract, refs, context, r5_packet)
        raise mo.ModeOutputError(
            mo.OUTPUT_NOT_ELIGIBLE,
            "facts mode outputs are not yet defined for this mode",
        )

    def _post_lock_outputs(
        self,
        binding: Mapping[str, Any],
        contract: Mapping[str, Any],
        refs: Mapping[str, Any],
        context: Mapping[str, Any],
        r5_packet: Any,
    ) -> tuple[dict[str, Any], ...]:
        # 锁库后固定总量：材料与清单围绕风险登记册（中高及以上，与日常
        # 监查的行动集一致）；全量锚点计数在 project_summary 中如实声明。
        register = [
            risk for risk in r5_packet.risks
            if risk.severity in ("critical", "high", "medium")
        ]
        subject_ids_by_site: dict[str, list[str]] = {}
        for subject in r5_packet.subjects:
            subject_ids_by_site.setdefault(subject.site_ref, []).append(subject.subject_ref)
        risk_ids_by_site: dict[str, list[str]] = {site.site_ref: [] for site in r5_packet.sites}
        risk_ids_by_subject: dict[str, list[str]] = {}
        for risk in register:
            risk_ids_by_site.setdefault(risk.site_ref, []).append(risk.risk_ref)
            risk_ids_by_subject.setdefault(risk.subject_ref, []).append(risk.risk_ref)
        evidence_refs = [
            locator_ref
            for risk in register[:50]
            for locator_ref in risk.source_locator_refs
        ]
        severity_counts = Counter(risk.severity for risk in r5_packet.risks)
        return mo.build_post_lock_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            population_totals={
                "site_count": len(r5_packet.sites),
                "subject_count": len(r5_packet.subjects),
                "risk_count": len(register),
            },
            report_version="facts-post-lock-v1",
            project_summary={
                "project_id": binding["project_id"],
                "status": "locked",
                "project_label": getattr(r5_packet, "project_label", binding["project_id"]),
                "anchor_event_count": len(r5_packet.events),
                "anchor_risk_total": sum(severity_counts.values()),
            },
            risk_summary={
                "high_count": sum(risk.severity in {"critical", "high"} for risk in register),
                "medium_count": sum(risk.severity == "medium" for risk in register),
                "low_count": 0,
                "risk_ids": [risk.risk_ref for risk in register],
            },
            evidence_refs=evidence_refs,
            site_materials=[
                {
                    "site_id": site.site_ref,
                    "subject_ids": subject_ids_by_site.get(site.site_ref, []),
                    "risk_ids": risk_ids_by_site.get(site.site_ref, []),
                    "evidence_refs": evidence_refs[:5],
                    "locator": {"path": "facts.site", "record_id": site.site_ref},
                }
                for site in r5_packet.sites
            ],
            subject_materials=[
                {
                    "subject_id": subject.subject_ref,
                    "site_id": subject.site_ref,
                    "profile_ref": {"profile_id": f"profile-{subject.subject_ref}"},
                    "timeline_ref": {"timeline_id": f"timeline-{subject.spine_ref}"},
                    "risk_ids": risk_ids_by_subject.get(subject.subject_ref, []),
                    "evidence_refs": evidence_refs[:3],
                    "locator": {"path": "facts.subject", "record_id": subject.subject_ref},
                }
                for subject in r5_packet.subjects
            ],
            check_items=[
                {
                    "level": "project",
                    "check_kind": "project_lock_review",
                    "scope_id": binding["project_id"],
                    "status": "ready",
                    "risk_ids": [risk.risk_ref for risk in register[:20]],
                    "evidence_refs": evidence_refs[:5],
                    "locator": {"path": "facts.project", "record_id": binding["project_id"]},
                },
            ] + [
                {
                    "level": "site",
                    "check_kind": "site_materials_review",
                    "scope_id": site.site_ref,
                    "status": "ready",
                    "risk_ids": risk_ids_by_site.get(site.site_ref, [])[:20],
                    "evidence_refs": evidence_refs[:3],
                    "locator": {"path": "facts.site", "record_id": site.site_ref},
                }
                for site in r5_packet.sites
            ] + [
                {
                    "level": "subject",
                    "check_kind": "subject_profile_review",
                    "scope_id": subject.subject_ref,
                    "status": "ready",
                    "risk_ids": risk_ids_by_subject.get(subject.subject_ref, [])[:20],
                    "evidence_refs": evidence_refs[:3],
                    "locator": {"path": "facts.subject", "record_id": subject.subject_ref},
                }
                for subject in r5_packet.subjects
            ],
            entry_context=context,
        )

    def _daily_findings(
        self, binding: Mapping[str, Any], r5_packet: Any
    ) -> list[dict[str, Any]]:
        ai_findings = self._load_ai_findings()
        if ai_findings:
            return self._findings_from_artifact(ai_findings, r5_packet)
        events_by_ref = {event.event_ref: event for event in r5_packet.events}
        subjects_by_ref = {
            subject.subject_ref: subject for subject in r5_packet.subjects
        }
        findings: list[dict[str, Any]] = []
        for risk in r5_packet.risks:
            if len(findings) >= _MAX_FINDINGS:
                break
            if risk.severity not in ("medium", "critical"):
                continue
            event = events_by_ref.get(risk.risk_anchor_ref or "")
            if event is None:
                continue
            subject = subjects_by_ref.get(event.subject_ref)
            subject_label = subject.subject_label if subject else event.subject_ref
            domain_zh = _DOMAIN_ZH.get(event.domain, event.domain)
            severity_zh = _SEVERITY_ZH.get(risk.severity, risk.severity)
            date_text = str(event.start_date or "日期缺失")
            basis = (
                f"已核验事实：受试者{subject_label}于{date_text}记录一条"
                f"{domain_zh}（{event.label_zh}），严重程度{severity_zh}。"
            )
            finding_text = (
                f"「{event.label_zh}」为{severity_zh}{domain_zh}信号，"
                "需要医学监察员人工核对。"
            )
            action = "请下钻受试者旅程与来源记录核对临床语境后确认处置。"
            findings.append(
                {
                    "finding_id": f"facts-finding-{event.event_ref}",
                    "risk_id": risk.risk_ref,
                    "issue_id": f"facts-issue-{event.domain}",
                    "subject_id": event.subject_ref,
                    "site_id": event.site_ref,
                    "scope_kind": "subject",
                    "basis": basis,
                    "finding": finding_text,
                    "action": action,
                    "evidence_refs": list(risk.source_locator_refs)
                    or list(event.source_locator_refs),
                    "locator": {
                        "path": f"facts.{event.domain}",
                        "record_id": event.event_ref,
                    },
                }
            )
        return findings

    def public_findings(self) -> list[dict[str, Any]]:
        """Audience-facing projection of the dual-cohort AE/MH findings."""

        ai_findings = self._load_ai_findings()
        if not ai_findings:
            return []
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(ai_findings):
            cohort = (item.get("primary") or item.get("verifier")) or {}
            rows.append(
                {
                    "finding_id": f"aemh-{index:04d}",
                    "subject_label": str(item.get("subject_label", "")),
                    "state": str(item.get("state", "escalated")),
                    "state_reason_zh": str(item.get("reason_zh", "")),
                    "title": str(cohort.get("title", ""))[:200],
                    "text": str(cohort.get("text", ""))[:2000],
                }
            )
        return rows

    def _load_ai_findings(self) -> list[dict[str, Any]] | None:
        """Load the newest dual-cohort AE/MH findings artifact, if any."""

        if self._artifacts_dir is None:
            return None
        candidates = [
            path
            for path in glob.glob(
                os.path.join(
                    str(self._artifacts_dir),
                    "aemh-findings-facts-snapshot-001*.json",
                )
            )
        ]
        if not candidates:
            return None
        # 最新裁决覆盖：按修改时间取最新工件（字典序会把 .r5 样例排在
        # .full1 全量之后）。
        latest = max(candidates, key=os.path.getmtime)
        try:
            with open(latest, encoding="utf-8") as handle:
                artifact = json.load(handle)
        except (OSError, ValueError):
            return None
        findings = artifact.get("findings")
        if isinstance(findings, list) and findings:
            return findings
        return None

    def _findings_from_artifact(
        self, ai_findings: list[dict[str, Any]], r5_packet: Any
    ) -> list[dict[str, Any]]:
        """Project dual-cohort findings into query-draft findings.

        Accepted pairs carry both cohorts' wording; escalated items stay
        visible with the disagreement marker; gaps stay visible as
        unverifiable. Risk binding uses the subject's first AE risk anchor so
        evidence drill-down keeps working.
        """

        subjects_by_label = {
            subject.subject_label: subject for subject in r5_packet.subjects
        }
        risk_by_subject: dict[str, Any] = {}
        for risk in r5_packet.risks:
            if risk.domain == "ae" and risk.subject_ref not in risk_by_subject:
                risk_by_subject[risk.subject_ref] = risk
        findings: list[dict[str, Any]] = []
        for index, item in enumerate(ai_findings):
            if len(findings) >= _MAX_FINDINGS:
                break
            subject_label = str(item.get("subject_label", "")).strip()
            subject = subjects_by_label.get(subject_label)
            if subject is None:
                continue
            risk = risk_by_subject.get(subject.subject_ref)
            cohort = (item.get("primary") or item.get("verifier")) or {}
            title = str(cohort.get("title", "")).strip() or "跨表线索待复核"
            state = str(item.get("state", "escalated"))
            state_note = {
                "accepted": "主分析与独立盲核（双模型）均引用相同原始记录，线索成立，待医学复核。",
                "escalated": str(item.get("reason_zh", "双cohort存在分歧，不得强行接受，请医学监察员裁决。")),
                "unverifiable_gap": "本轮双cohort未能完成核实，覆盖不足可见，待下轮补核。",
            }.get(state, "待医学复核。")
            basis = (
                f"双cohort分析（{state_note}）受试者{subject_label}的"
                "AE/MH/合并用药/试验用药原始记录。"
            )
            finding_text = f"「{title}」"
            action = "请下钻受试者旅程与来源记录核对临床语境后确认处置。"
            findings.append(
                {
                    "finding_id": f"aemh-finding-{index:04d}",
                    "risk_id": risk.risk_ref if risk else f"aemh-subject-{subject.subject_ref}",
                    "issue_id": f"aemh-issue-{state}",
                    "subject_id": subject.subject_ref,
                    "site_id": subject.site_ref,
                    "scope_kind": "subject",
                    "basis": basis,
                    "finding": finding_text,
                    "action": action,
                    "evidence_refs": list(risk.source_locator_refs) if risk else [],
                    "locator": {
                        "path": "facts.aemh_cross_analysis",
                        "record_id": f"aemh-{subject_label}",
                    },
                }
            )
        return findings


__all__ = ["FactsModeOutputProvider"]
