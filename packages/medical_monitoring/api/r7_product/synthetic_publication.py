"""Explicit publication providers for the product-native synthetic profile."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from ...projections.product_fixtures import build_synthetic_r5_authority_packet
from ...projections.publication.r5_publication_authority import (
    R5AuthorityPacket,
    _aggregate_digest,
)
from ...reports import mode_output as mo


class SyntheticPublicationAuthorityProvider:
    """Adapt the accepted R5 fixture packet to one synthetic R7 run identity."""

    fixture_mode = True

    def get_authority(self, identity: Any, **_: Any) -> R5AuthorityPacket:
        product = build_synthetic_r5_authority_packet(
            project_ref=identity.project_ref,
            snapshot_ref=identity.snapshot_ref,
            cutoff_ref=identity.cutoff_ref,
        )
        product = replace(
            product,
            run_ref=identity.run_ref,
            sites=tuple(
                site for site in product.sites if site.site_ref in identity.site_refs
            ),
            authority_hash="",
            source_snapshot_sha256="",
        )
        members = {
            "project_ref": identity.project_ref,
            "run_ref": identity.run_ref,
            "public_run_token": identity.public_run_token,
            "snapshot_ref": identity.snapshot_ref,
            "cutoff_ref": identity.cutoff_ref,
            "site_refs": identity.site_refs,
            "s4_packets": (),
            "risks": product.risks,
            "subjects": product.subjects,
            "sites": product.sites,
            "events": product.events,
            "visits": product.visits,
            "sources": product.sources,
            "product_packet_authority_hash": product.authority_hash,
        }
        digest = _aggregate_digest(members)
        members.pop("product_packet_authority_hash")
        return R5AuthorityPacket(
            **members,
            packet_identity=f"r5-publication-authority:{digest}",
            packet_digest=digest,
            authority_hash=digest,
            product_packet=product,
        )


class SyntheticModeOutputProvider:
    """Build the four existing mode outputs from accepted synthetic members."""

    @staticmethod
    def _binding(run_binding: Mapping[str, Any]) -> dict[str, Any]:
        binding = dict(run_binding)
        binding.setdefault("carry_forward_run_ids", [])
        binding.setdefault("mode_transition", "explicit_new_run")
        binding.setdefault("actor", "system_synthetic")
        binding.setdefault("created_at", "2026-08-28T00:00:00Z")
        binding.setdefault("knowledge_pack_version", "synthetic-kp-v1")
        binding.setdefault("rule_activation_version", "synthetic-rules-v1")
        binding.setdefault("mapping_version", "synthetic-mapping-v1")
        binding.setdefault("identity_algorithm_version", "synthetic-identity-v1")
        binding.setdefault("identity_algorithm_digest", "synthetic-identity-digest-v1")
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
            binding.setdefault("locked_snapshot_hash", "synthetic-locked-snapshot-v1")
            binding.setdefault("output_cutoff_ref", binding["data_cutoff"])
            binding.setdefault("output_revision_ref", binding["source_revision_id"])
            binding.setdefault("local_os_user", "local-user-synthetic")
            binding.setdefault("acceptance_evidence_hash", "accept-hash-fixed-001")
        contract = mo.build_mode_contract(mode)
        context = mo.default_entry_context_for_mode(mode, run_binding=binding)
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
        risk = r5_packet.risks[0]
        subject = r5_packet.subjects[0]
        site = r5_packet.sites[0]
        if mode == "daily":
            finding = {
                "finding_id": "synthetic-finding-001",
                "risk_id": risk.risk_ref,
                "issue_id": "synthetic-issue-001",
                "subject_id": risk.subject_ref,
                "site_id": risk.site_ref,
                "scope_kind": "subject",
                "basis": "合成事实包中的已接受风险",
                "finding": "存在需要医学监察员核对的风险",
                "action": "请结合来源记录确认",
                "evidence_refs": list(risk.source_locator_refs),
                "locator": {
                    "path": "synthetic.accepted-risk",
                    "record_id": risk.risk_ref,
                },
            }
            return mo.build_daily_mode_outputs(
                binding,
                contract,
                authority_refs=refs,
                coverage_refs=refs,
                qc_refs=refs,
                findings=[finding],
                risks=[
                    {
                        "risk_id": risk.risk_ref,
                        "severity": risk.severity,
                        "risk_type": risk.risk_type_zh,
                    }
                ],
                entry_context=context,
            )
        if mode == "pre_lock":
            source_refs = list(risk.source_locator_refs)
            return mo.build_pre_lock_mode_outputs(
                binding,
                contract,
                authority_refs=refs,
                coverage_refs=refs,
                qc_refs=refs,
                risks=[{"risk_id": risk.risk_ref, "severity": risk.severity}],
                population_scope={
                    "scope_kind": "project",
                    "population_id": "synthetic-population",
                    "label": "全部合成受试者",
                    "site_count": len(r5_packet.sites),
                    "subject_count": len(r5_packet.subjects),
                    "risk_count": len(r5_packet.risks),
                },
                from_source_revision_id="synthetic-source-prior",
                revision_reason="锁库前合成数据例行比对",
                check_items=[
                    {
                        "level": "project",
                        "check_kind": "lock_prep",
                        "status": "ready",
                        "evidence_refs": source_refs,
                        "locator": {
                            "path": "synthetic.project",
                            "record_id": binding["project_id"],
                        },
                    },
                    {
                        "level": "site",
                        "check_kind": "site_cutoff",
                        "status": "ready",
                        "site_id": site.site_ref,
                        "evidence_refs": source_refs,
                        "locator": {
                            "path": "synthetic.site",
                            "record_id": site.site_ref,
                        },
                    },
                    {
                        "level": "subject",
                        "check_kind": "subject_listing",
                        "status": "ready",
                        "site_id": subject.site_ref,
                        "subject_id": subject.subject_ref,
                        "evidence_refs": source_refs,
                        "locator": {
                            "path": "synthetic.subject",
                            "record_id": subject.subject_ref,
                        },
                    },
                ],
                entry_context=context,
            )
        risk_ids_by_site = {
            item.site_ref: [risk_item.risk_ref for risk_item in r5_packet.risks if risk_item.site_ref == item.site_ref]
            for item in r5_packet.sites
        }
        risk_ids_by_subject = {
            item.subject_ref: [risk_item.risk_ref for risk_item in r5_packet.risks if risk_item.subject_ref == item.subject_ref]
            for item in r5_packet.subjects
        }
        subject_ids_by_site = {
            item.site_ref: [subject_item.subject_ref for subject_item in r5_packet.subjects if subject_item.site_ref == item.site_ref]
            for item in r5_packet.sites
        }
        source_refs = list(risk.source_locator_refs)
        return mo.build_post_lock_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            population_totals={
                "site_count": len(r5_packet.sites),
                "subject_count": len(r5_packet.subjects),
                "risk_count": len(r5_packet.risks),
            },
            report_version="synthetic-v1",
            project_summary={"project_id": binding["project_id"], "status": "completed"},
            risk_summary={
                "high_count": sum(item.severity in {"critical", "high"} for item in r5_packet.risks),
                "medium_count": sum(item.severity == "medium" for item in r5_packet.risks),
                "low_count": sum(item.severity == "low" for item in r5_packet.risks),
                "risk_ids": [item.risk_ref for item in r5_packet.risks],
            },
            evidence_refs=source_refs,
            site_materials=[
                {
                    "site_id": item.site_ref,
                    "subject_ids": subject_ids_by_site[item.site_ref],
                    "risk_ids": risk_ids_by_site[item.site_ref],
                    "evidence_refs": source_refs,
                    "locator": {"path": "synthetic.site", "record_id": item.site_ref},
                }
                for item in r5_packet.sites
            ],
            subject_materials=[
                {
                    "subject_id": item.subject_ref,
                    "site_id": item.site_ref,
                    "profile_ref": {"profile_id": f"profile-{item.subject_ref}"},
                    "timeline_ref": {"timeline_id": f"timeline-{item.subject_ref}"},
                    "risk_ids": risk_ids_by_subject[item.subject_ref],
                    "evidence_refs": source_refs,
                    "locator": {"path": "synthetic.subject", "record_id": item.subject_ref},
                }
                for item in r5_packet.subjects
            ],
            check_items=[
                {
                    "level": "project",
                    "check_kind": "project_lock",
                    "scope_id": binding["project_id"],
                    "status": "ready",
                    "risk_ids": [item.risk_ref for item in r5_packet.risks],
                    "evidence_refs": source_refs,
                    "locator": {"path": "synthetic.project", "record_id": binding["project_id"]},
                },
                {
                    "level": "site",
                    "check_kind": "site_coverage",
                    "scope_id": site.site_ref,
                    "status": "ready",
                    "risk_ids": risk_ids_by_site[site.site_ref],
                    "evidence_refs": source_refs,
                    "locator": {"path": "synthetic.site", "record_id": site.site_ref},
                },
                {
                    "level": "subject",
                    "check_kind": "subject_profile",
                    "scope_id": subject.subject_ref,
                    "status": "ready",
                    "risk_ids": risk_ids_by_subject[subject.subject_ref],
                    "evidence_refs": source_refs,
                    "locator": {"path": "synthetic.subject", "record_id": subject.subject_ref},
                },
            ],
            entry_context=context,
        )


__all__ = [
    "SyntheticModeOutputProvider",
    "SyntheticPublicationAuthorityProvider",
]
