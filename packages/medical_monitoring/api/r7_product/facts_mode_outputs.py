"""Real facts-backed R6 mode outputs for the materialized-facts product lane.

Mirrors the synthetic mode-output provider protocol but derives every row
from the typed facts authority packet: severity/type aggregation for the
full-risk output and adverse-event (medium-or-higher) query findings with
their source locators for the affected-query draft. No invented findings.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ...intelligence.primitives import content_hash
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
_AI_FINDINGS_ARTIFACT = "aemh-findings-facts-snapshot-001.dualvlm-full1.json"
# 分析层证据ID推导所用表清单与 ae_mh_cross_analysis._ANALYSIS_TABLES 一致
_EVIDENCE_TABLES = ("AE", "MH", "CM", "EX2", "EX4", "EX5", "EX7")


class FactsModeOutputProvider:
    """Build the four mode outputs from the real facts authority packet."""

    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        domains_loader: Optional[Callable[[], Mapping[str, list]]] = None,
    ) -> None:
        self._artifacts_dir = artifacts_dir
        # 数据接入的domains快照读取器：用于把分析层evidence_id解析回
        # （表，行）→事件/来源锚点。缺省None=锚点解析降级为unbound。
        self._domains_loader = domains_loader

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
            if risk.severity in ("high", "medium", "critical")
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

    def public_findings(
        self,
        projection: Optional[Mapping[str, Any]] = None,
        project_ref: str = "",
    ) -> list[dict[str, Any]]:
        """Audience-facing projection of the dual-cohort findings.

        N1阅读模型：稳定finding_id贯穿（不按index重编号，显示序号另存
        display_seq）；保留claims真实证据引用与服务端可解析的事件/来源
        锚点；无标题的覆盖缺口以kind=coverage_gap可见（不依赖标题存活）；
        state与artifact身份经 public_findings_meta 暴露。
        """

        read = self._read_ai_findings()
        if read["state"] not in ("completed_with_findings", "completed_no_findings"):
            return []
        subjects_by_label: dict[str, Mapping[str, Any]] = {}
        for subject in (projection or {}).get("subjects", []) or []:
            label = str(
                subject.get("subject_label")
                or subject.get("label")
                or ""
            ).strip()
            if label:
                subjects_by_label.setdefault(label, subject)
        anchor_index_cache: dict[str, dict[str, tuple[str, int]]] = {}
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(read["findings"]):
            cohort = (item.get("primary") or item.get("verifier")) or {}
            state = str(item.get("state", "escalated"))
            title = str(cohort.get("title", "")).strip()
            kind = "finding"
            if state == "unverifiable_gap" and not title:
                kind = "coverage_gap"
                title = "覆盖缺口（本轮未能完成该受试者的双cohort核实）"
            subject_label = str(item.get("subject_label", ""))
            # 服务端解析subject身份（不猜ID）：projection.subjects由包授权
            # 投影给出subject_ref/site_ref/spine_ref。
            subject_row = subjects_by_label.get(subject_label) or {}
            evidence_ids = self._finding_evidence_ids(item)
            claims = self._finding_claims(item)
            rows.append(
                {
                    "finding_id": str(item.get("finding_id", "")) or f"aemh-unid-{index:04d}",
                    "display_seq": index + 1,
                    "kind": kind,
                    "subject_label": subject_label,
                    "subject_ref": str(subject_row.get("subject_ref") or subject_row.get("subject_id") or ""),
                    "site_ref": str(subject_row.get("site_ref") or subject_row.get("site_id") or ""),
                    "spine_ref": str(subject_row.get("spine_ref") or ""),
                    "state": state,
                    "state_reason_zh": str(item.get("reason_zh", "")),
                    "title": title[:200],
                    "text": str(cohort.get("text", ""))[:2000],
                    "evidence_ids": evidence_ids,
                    "claims": claims,
                }
            )
        return rows

    def _finding_claims(self, item: Mapping[str, Any]) -> list[dict[str, Any]]:
        """双cohort claims语义分点（文本+各自证据引用，供前端ul/li渲染）。"""

        claims_out: list[dict[str, Any]] = []
        seen_texts: set[str] = set()
        for side in ("primary", "verifier"):
            cohort = item.get(side) or {}
            payload = cohort.get("payload") or {}
            for claim in (payload.get("claims") or []):
                text = str(claim.get("text", "")).strip()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)
                claims_out.append(
                    {
                        "text": text[:400],
                        "kind": str(claim.get("kind", "")),
                        "evidence_ids": [str(e) for e in (claim.get("evidence_ids") or [])],
                        "side": side,
                    }
                )
        return claims_out

    def public_findings_meta(
        self,
        projection: Optional[Mapping[str, Any]] = None,
        project_ref: str = "",
    ) -> dict[str, Any]:
        """读取状态与工件身份（missing/read_failed/完成态分离，V4-05/06）。"""

        read = self._read_ai_findings()
        findings = read.get("findings") or []
        gaps = sum(
            1
            for item in findings
            if str(item.get("state", "")) == "unverifiable_gap"
        )
        return {
            "state": read["state"],
            "artifact": read.get("artifact"),
            "content_sha256": read.get("content_sha256"),
            "total": len(findings),
            "gaps": gaps,
            "error": read.get("error"),
        }

    def _read_ai_findings(self) -> dict[str, Any]:
        """按冻结名读取AI findings工件，返回带状态与身份的读取结果。

        - missing：工件不存在（项目无双cohort lane）
        - read_failed：存在但JSON损坏或内容hash不符
        - completed_no_findings / completed_with_findings：完成态分离
          （有效空数组≠缺失，不得触发备用分析）
        读取目标为固定冻结名（不glob+mtime取最新——旧run不得读到新工件）。
        """

        if self._artifacts_dir is None:
            return {"state": "missing", "findings": None, "artifact": None,
                    "error": "artifacts_dir未配置"}
        artifact_path = Path(self._artifacts_dir) / _AI_FINDINGS_ARTIFACT
        if not artifact_path.is_file():
            return {"state": "missing", "findings": None,
                    "artifact": _AI_FINDINGS_ARTIFACT, "error": None}
        try:
            with open(artifact_path, encoding="utf-8") as handle:
                artifact = json.load(handle)
        except (OSError, ValueError) as exc:
            return {"state": "read_failed", "findings": None,
                    "artifact": _AI_FINDINGS_ARTIFACT,
                    "error": f"json_decode: {exc}"}
        if not isinstance(artifact, dict):
            return {"state": "read_failed", "findings": None,
                    "artifact": _AI_FINDINGS_ARTIFACT, "error": "not_object"}
        declared = str(artifact.get("content_sha256", "")).strip()
        if declared:
            verify = {k: v for k, v in artifact.items() if k != "content_sha256"}
            if content_hash(verify) != declared:
                return {"state": "read_failed", "findings": None,
                        "artifact": _AI_FINDINGS_ARTIFACT,
                        "error": "content_sha256_mismatch"}
        findings = artifact.get("findings")
        if not isinstance(findings, list):
            return {"state": "read_failed", "findings": None,
                    "artifact": _AI_FINDINGS_ARTIFACT,
                    "error": "findings_not_list"}
        state = (
            "completed_with_findings" if findings else "completed_no_findings"
        )
        return {
            "state": state,
            "findings": findings,
            "artifact": _AI_FINDINGS_ARTIFACT,
            "content_sha256": declared,
            "error": None,
        }

    def _finding_evidence_ids(self, item: Mapping[str, Any]) -> list[str]:
        """双cohort claims的evidence_ids并集（保序去重）。"""

        ids: list[str] = []
        for side in ("primary", "verifier"):
            cohort = item.get(side) or {}
            payload = cohort.get("payload") or {}
            for claim in (payload.get("claims") or []):
                for eid in (claim.get("evidence_ids") or []):
                    eid = str(eid)
                    if eid and eid not in ids:
                        ids.append(eid)
        return ids

    def _subject_evidence_index(
        self, subject_label: str, cache: dict[str, dict[str, tuple[str, int]]]
    ) -> dict[str, tuple[str, int]]:
        """evidence_id → (表, 行) 索引（与build_subject_evidence同推导）。"""

        cached = cache.get(subject_label)
        if cached is not None:
            return cached
        index: dict[str, tuple[str, int]] = {}
        if self._domains_loader is not None:
            try:
                domains = self._domains_loader()
            except Exception:
                domains = None
            if domains:
                for table in _EVIDENCE_TABLES:
                    for idx, row in enumerate(domains.get(table, []) or []):
                        if str(row.get("SUBJID", "")).strip() != subject_label:
                            continue
                        eid = "aemh_{}".format(
                            content_hash(
                                {"table": table, "row": idx,
                                 "subject": subject_label}
                            )[:28]
                        )
                        index.setdefault(eid, (table, idx))
        cache[subject_label] = index
        return index

    def _claim_anchors(
        self,
        item: Mapping[str, Any],
        r5_packet: Any,
        evidence_index: dict[str, tuple[str, int]],
        events_by_ref: Mapping[str, Any],
    ) -> dict[str, Any]:
        """claims真实证据→事件/来源锚点解析。

        返回 anchor_event_refs / anchor_locator_refs（去重保序）与
        anchor_state（bound=至少一锚点在包内可验证；unbound=全部不可解析，
        显式标注，不借用其他事件）。
        """

        event_refs: list[str] = []
        locator_refs: list[str] = []
        for eid in self._finding_evidence_ids(item):
            hit = evidence_index.get(eid)
            if hit is None:
                continue
            table, idx = hit
            event_ref = f"event-{table}-{idx:06d}"
            loc_ref = f"loc-{table}-{idx:06d}"
            if event_ref not in event_refs:
                event_refs.append(event_ref)
            if loc_ref not in locator_refs:
                locator_refs.append(loc_ref)
        verified: list[str] = [
            ref for ref in event_refs
            if not events_by_ref or ref in events_by_ref
        ]
        anchor_state = "bound" if verified else "unbound"
        return {
            "anchor_event_refs": event_refs,
            "anchor_locator_refs": locator_refs,
            "verified_event_refs": verified,
            "anchor_state": anchor_state,
        }

    def _daily_findings(
        self, binding: Mapping[str, Any], r5_packet: Any
    ) -> list[dict[str, Any]]:
        read = self._read_ai_findings()
        if read["state"] == "completed_with_findings":
            return self._findings_from_artifact(read["findings"], r5_packet)
        if read["state"] == "completed_no_findings":
            # 有效零发现：如实返回空，不触发备用通用提示（V4-05）。
            return []
        return self._deterministic_fallback_findings(binding, r5_packet)

    def _deterministic_fallback_findings(
        self, binding: Mapping[str, Any], r5_packet: Any
    ) -> list[dict[str, Any]]:
        """无AI工件lane的确定性事实提示（原daily兜底路径，明确来源）。"""

        events_by_ref = {event.event_ref: event for event in r5_packet.events}
        subjects_by_ref = {
            subject.subject_ref: subject for subject in r5_packet.subjects
        }
        findings: list[dict[str, Any]] = []
        for risk in r5_packet.risks:
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

    def _findings_from_artifact(
        self, ai_findings: list[dict[str, Any]], r5_packet: Any
    ) -> list[dict[str, Any]]:
        """Project dual-cohort findings into query-draft findings.

        N1：锚点来自claims真实证据引用（evidence_id→表/行→event/loc），
        并经包内事件核验后绑定该事件真实关联的risk（risk_anchor_ref匹配）；
        不可解析=unbound显式标注，不借用受试者第一条AE。无截断，total另记。
        """

        subjects_by_label = {
            subject.subject_label: subject for subject in r5_packet.subjects
        }
        events_by_ref = {
            event.event_ref: event for event in getattr(r5_packet, "events", ()) or ()
        }
        risk_by_anchor: dict[str, Any] = {}
        for risk in r5_packet.risks:
            anchor = getattr(risk, "risk_anchor_ref", "") or ""
            if anchor and anchor not in risk_by_anchor:
                risk_by_anchor[anchor] = risk
        evidence_cache: dict[str, dict[str, tuple[str, int]]] = {}
        findings: list[dict[str, Any]] = []
        for item in ai_findings:
            subject_label = str(item.get("subject_label", "")).strip()
            subject = subjects_by_label.get(subject_label)
            if subject is None:
                continue
            cohort = (item.get("primary") or item.get("verifier")) or {}
            state = str(item.get("state", "escalated"))
            title = str(cohort.get("title", "")).strip() or "跨表线索待复核"
            kind = "finding"
            if state == "unverifiable_gap" and not str(
                (item.get("primary") or {}).get("title", "")
            ) and not str((item.get("verifier") or {}).get("title", "")):
                kind = "coverage_gap"
            anchors = self._claim_anchors(
                item, r5_packet,
                self._subject_evidence_index(subject_label, evidence_cache),
                events_by_ref,
            )
            verified_event = (
                anchors["verified_event_refs"][0]
                if anchors["verified_event_refs"]
                else ""
            )
            bound_risk = risk_by_anchor.get(verified_event)
            state_note = {
                "accepted": "主分析与独立盲核（双模型）均引用相同原始记录，线索成立，待医学复核。",
                "escalated": str(item.get("reason_zh", "双cohort存在分歧，不得强行接受，请医学监察员裁决。")),
                "unverifiable_gap": "本轮双cohort未能完成核实，覆盖不足可见，待下轮补核。",
            }.get(state, "待医学复核。")
            basis = (
                f"双cohort分析（{state_note}）受试者{subject_label}的"
                "AE/MH/合并用药/试验用药原始记录。"
            )
            findings.append(
                {
                    "finding_id": str(item.get("finding_id", "")),
                    "kind": kind,
                    "display_seq": len(findings) + 1,
                    "risk_id": bound_risk.risk_ref if bound_risk is not None else None,
                    "issue_id": f"aemh-issue-{state}",
                    "subject_id": subject.subject_ref,
                    "site_id": subject.site_ref,
                    "scope_kind": "subject",
                    "anchor_event_refs": anchors["anchor_event_refs"],
                    "anchor_locator_refs": anchors["anchor_locator_refs"],
                    "anchor_state": anchors["anchor_state"],
                    "evidence_ids": self._finding_evidence_ids(item),
                    "basis": basis,
                    "finding": f"「{title}」",
                    "action": "请下钻受试者旅程与来源记录核对临床语境后确认处置。",
                    "locator": {
                        "path": "facts.aemh_cross_analysis",
                        "record_id": str(item.get("finding_id", "")),
                    },
                }
            )
        return findings


__all__ = ["FactsModeOutputProvider"]
