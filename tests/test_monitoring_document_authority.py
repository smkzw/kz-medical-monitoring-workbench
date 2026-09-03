from __future__ import annotations

import hashlib
import json

import pytest

from packages.medical_monitoring.admission.document_authority import (
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    CandidateAssessment,
    ConflictDecision,
    DocumentAuthorityAnalysis,
    DocumentAuthorityConflictRunEnvelope,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    DocumentAuthorityRunEnvelope,
    EvidenceReference,
    PRIMARY_PROMPT_VERSION,
    PRIMARY_REVIEW_PROMPT_VERSION,
    RoleSelection,
    VERIFIER_PROMPT_VERSION,
    VERIFIER_REVIEW_PROMPT_VERSION,
    build_anonymous_conflict_packet,
    reconcile_document_authority,
    resolve_document_authority_conflicts,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)


def _digest(value: object) -> str:
    if isinstance(value, dict) and "candidates" in value:
        value = {
            **value,
            "candidates": sorted(
                value["candidates"], key=lambda item: item["candidate_id"]
            ),
        }
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _batch() -> dict:
    return {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_demo",
        "authority_status": "not_adjudicated",
        "candidates": [
            {
                "candidate_id": "candidate_protocol",
                "filename": "protocol.docx",
                "role_hypotheses": ["protocol", "investigator_brochure", "sap"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 2,
                "excerpts": [
                    {"locator": "doc:p1", "text": "研究方案"},
                    {"locator": "doc:p2", "text": "版本日期"},
                ],
                "sheets": [],
            },
            {
                "candidate_id": "candidate_ecrf",
                "filename": "ecrf.xlsx",
                "role_hypotheses": ["ecrf"],
                "technical_status": "ready",
                "extraction_status": "parsed",
                "locator_count": 1,
                "excerpts": [],
                "sheets": [{"locator": "xlsx:sheet:1", "sheet_name": "AE"}],
            },
        ],
    }


def _analysis(batch: dict, *, ecrf: str = "candidate_ecrf") -> DocumentAuthorityAnalysis:
    assessments = (
        CandidateAssessment(
            candidate_id="candidate_protocol",
            inferred_role="protocol",
            usable=True,
            confidence=0.98,
            evidence_locators=("doc:p1",),
        ),
        CandidateAssessment(
            candidate_id="candidate_ecrf",
            inferred_role="ecrf",
            usable=True,
            confidence=0.98,
            evidence_locators=("xlsx:sheet:1",),
        ),
    )
    return DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=batch["batch_id"],
        input_sha256=_digest(batch),
        candidate_assessments=assessments,
        role_selections=(
            RoleSelection(
                role="protocol",
                decision="selected",
                selected_candidate_id="candidate_protocol",
                confidence=0.98,
                evidence_locators=("doc:p1",),
            ),
            RoleSelection(
                role="investigator_brochure",
                decision="missing",
                confidence=0.95,
            ),
            RoleSelection(
                role="ecrf",
                decision="selected" if ecrf else "unresolved",
                selected_candidate_id=ecrf,
                confidence=0.98 if ecrf else 0.5,
                evidence_locators=("xlsx:sheet:1",) if ecrf else (),
            ),
            RoleSelection(role="sap", decision="missing", confidence=0.95),
        ),
    )


def _run(
    analysis: DocumentAuthorityAnalysis, role: str
) -> DocumentAuthorityRunEnvelope:
    primary = role == "primary"
    return DocumentAuthorityRunEnvelope(
        run_id=f"{role}-run",
        job_id=f"{role}-job",
        role=role,
        provider=(
            MONITORING_C3_MAPPING_PROVIDER
            if primary else MONITORING_C3_VERIFIER_PROVIDER
        ),
        model=MONITORING_C3_MAPPING_MODEL if primary else MONITORING_C3_VERIFIER_MODEL,
        prompt_version=PRIMARY_PROMPT_VERSION if primary else VERIFIER_PROMPT_VERSION,
        input_sha256=analysis.input_sha256,
        output_sha256=_digest(analysis.model_dump(mode="json")),
        analysis=analysis,
    )


def _reconcile(
    batch: dict,
    primary: DocumentAuthorityAnalysis,
    verifier: DocumentAuthorityAnalysis,
) -> dict:
    return reconcile_document_authority(
        batch, _run(primary, "primary"), _run(verifier, "verifier")
    )


def _review_run(
    review: DocumentAuthorityConflictReview, role: str
) -> DocumentAuthorityConflictRunEnvelope:
    primary = role == "primary"
    return DocumentAuthorityConflictRunEnvelope(
        run_id=f"{role}-review-run",
        job_id=f"{role}-review-job",
        role=role,
        provider=(
            MONITORING_C3_MAPPING_PROVIDER
            if primary else MONITORING_C3_VERIFIER_PROVIDER
        ),
        model=MONITORING_C3_MAPPING_MODEL if primary else MONITORING_C3_VERIFIER_MODEL,
        prompt_version=(
            PRIMARY_REVIEW_PROMPT_VERSION
            if primary else VERIFIER_REVIEW_PROMPT_VERSION
        ),
        conflict_packet_sha256=review.conflict_packet_sha256,
        output_sha256=_digest(review.model_dump(mode="json")),
        review=review,
    )


def _refs(*values: tuple[str, str]) -> tuple[EvidenceReference, ...]:
    return tuple(
        EvidenceReference(candidate_id=candidate_id, locator=locator)
        for candidate_id, locator in values
    )


def _conflict_context(batch: dict) -> tuple[dict, dict, DocumentAuthorityRunEnvelope, DocumentAuthorityRunEnvelope]:
    primary = _run(_analysis(batch, ecrf=""), "primary")
    verifier = _run(_analysis(batch), "verifier")
    reconciliation = reconcile_document_authority(batch, primary, verifier)
    packet = build_anonymous_conflict_packet(batch, primary, verifier)
    return reconciliation, packet, primary, verifier


def test_matching_complete_blind_analyses_resolve_without_user_work() -> None:
    batch = _batch()

    result = _reconcile(batch, _analysis(batch), _analysis(batch))

    assert result["state"] == "resolved"
    assert result["conflicts"] == []
    assert [item["role"] for item in result["resolved_roles"]] == [
        "protocol",
        "investigator_brochure",
        "ecrf",
        "sap",
    ]


def test_same_run_identity_cannot_satisfy_dual_analysis() -> None:
    batch = _batch()
    primary = _run(_analysis(batch), "primary")
    forged_verifier = primary.model_copy(
        update={
            "role": "verifier",
            "provider": MONITORING_C3_VERIFIER_PROVIDER,
            "model": MONITORING_C3_VERIFIER_MODEL,
            "prompt_version": VERIFIER_PROMPT_VERSION,
        }
    )

    with pytest.raises(DocumentAuthorityError, match="runs_not_independent"):
        reconcile_document_authority(batch, primary, forged_verifier)


def test_missing_candidate_coverage_and_unknown_evidence_fail_closed() -> None:
    batch = _batch()
    analysis = _analysis(batch)
    incomplete = analysis.model_copy(
        update={"candidate_assessments": analysis.candidate_assessments[:1]}
    )
    with pytest.raises(DocumentAuthorityError, match="candidate_coverage"):
        _reconcile(batch, incomplete, analysis)

    bad_selection = analysis.role_selections[0].model_copy(
        update={"evidence_locators": ("invented",)}
    )
    unclosed = analysis.model_copy(
        update={"role_selections": (bad_selection, *analysis.role_selections[1:])}
    )
    with pytest.raises(DocumentAuthorityError, match="evidence_not_closed"):
        _reconcile(batch, unclosed, analysis)


def test_same_file_with_disagreed_version_still_requires_blind_review() -> None:
    batch = _batch()
    primary = _analysis(batch)
    changed = primary.candidate_assessments[0].model_copy(
        update={"document_version": "V2.0"}
    )
    verifier = primary.model_copy(
        update={"candidate_assessments": (changed, *primary.candidate_assessments[1:])}
    )

    result = _reconcile(batch, primary, verifier)

    assert result["state"] == "needs_dual_review"
    assert result["conflicts"][0]["role"] == "protocol"


def test_competing_candidate_disagreement_blocks_first_pass_auto_resolution() -> None:
    batch = _batch()
    batch["candidates"].append({
        "candidate_id": "candidate_protocol_v2",
        "filename": "protocol_v2.docx",
        "role_hypotheses": ["protocol"],
        "technical_status": "ready",
        "extraction_status": "parsed",
        "locator_count": 1,
        "excerpts": [{"locator": "doc-v2:p1", "text": "研究方案 V2.0"}],
        "sheets": [],
    })
    primary = _analysis(batch)
    verifier = _analysis(batch)
    primary_extra = CandidateAssessment(
        candidate_id="candidate_protocol_v2",
        inferred_role="unrelated",
        usable=False,
        confidence=0.96,
        evidence_locators=("doc-v2:p1",),
    )
    verifier_extra = CandidateAssessment(
        candidate_id="candidate_protocol_v2",
        inferred_role="protocol",
        usable=True,
        confidence=0.97,
        document_version="V2.0",
        evidence_locators=("doc-v2:p1",),
    )
    primary = primary.model_copy(update={
        "candidate_assessments": (*primary.candidate_assessments, primary_extra)
    })
    verifier = verifier.model_copy(update={
        "candidate_assessments": (*verifier.candidate_assessments, verifier_extra)
    })

    result = _reconcile(batch, primary, verifier)

    assert result["state"] == "needs_dual_review"
    assert any(item["role"] == "protocol" for item in result["conflicts"])


def test_different_locator_or_material_uncertainty_cannot_auto_resolve() -> None:
    batch = _batch()
    primary = _analysis(batch)
    changed_selection = primary.role_selections[0].model_copy(
        update={"evidence_locators": ("doc:p2",), "uncertainty": "版本仍不明确"}
    )
    verifier = primary.model_copy(
        update={"role_selections": (changed_selection, *primary.role_selections[1:])}
    )

    result = _reconcile(batch, primary, verifier)

    assert result["state"] == "needs_dual_review"
    assert result["conflicts"][0]["role"] == "protocol"


def test_optional_missing_requires_absence_of_usable_same_role_candidate() -> None:
    batch = _batch()
    analysis = _analysis(batch)
    ib_candidate = analysis.candidate_assessments[0].model_copy(
        update={"inferred_role": "investigator_brochure"}
    )
    protocol_unresolved = analysis.role_selections[0].model_copy(
        update={
            "decision": "unresolved",
            "selected_candidate_id": "",
            "evidence_locators": (),
        }
    )
    invalid = analysis.model_copy(
        update={
            "candidate_assessments": (ib_candidate, *analysis.candidate_assessments[1:]),
            "role_selections": (protocol_unresolved, *analysis.role_selections[1:]),
        }
    )

    with pytest.raises(DocumentAuthorityError, match="missing_not_proven"):
        _reconcile(batch, invalid, invalid)


def test_optional_missing_requires_competing_assessment_agreement() -> None:
    batch = _batch()
    batch["candidates"].append({
        "candidate_id": "candidate_ib",
        "filename": "ib.pdf",
        "role_hypotheses": ["investigator_brochure"],
        "technical_status": "ready",
        "extraction_status": "parsed",
        "locator_count": 1,
        "excerpts": [{"locator": "ib:p1", "text": "研究者手册"}],
        "sheets": [],
    })
    primary = _analysis(batch)
    ib_primary = CandidateAssessment(
        candidate_id="candidate_ib",
        inferred_role="investigator_brochure",
        usable=False,
        confidence=0.96,
        document_version="V1.0",
        evidence_locators=("ib:p1",),
    )
    ib_verifier = ib_primary.model_copy(update={"document_version": "V2.0"})
    primary = primary.model_copy(update={
        "candidate_assessments": (*primary.candidate_assessments, ib_primary)
    })
    verifier = primary.model_copy(update={
        "candidate_assessments": (*primary.candidate_assessments[:-1], ib_verifier)
    })

    result = _reconcile(batch, primary, verifier)

    assert result["state"] == "needs_dual_review"
    assert any(
        item["role"] == "investigator_brochure" for item in result["conflicts"]
    )


def test_conflict_packet_is_anonymous_and_order_stable() -> None:
    batch = _batch()
    reconciliation, packet, primary, verifier = _conflict_context(batch)

    reversed_batch = {**batch, "candidates": list(reversed(batch["candidates"]))}
    reversed_packet = build_anonymous_conflict_packet(
        reversed_batch, primary, verifier
    )

    assert packet["conflict_roles"] == ["ecrf"]
    assert "provider" not in json.dumps(packet)
    assert "primary" not in json.dumps(packet)
    assert [item["candidate_id"] for item in packet["candidates"]] == [
        item["candidate_id"] for item in reversed_packet["candidates"]
    ]
    assert packet["conflict_packet_sha256"] == reversed_packet["conflict_packet_sha256"]

    leaked = json.loads(json.dumps(batch))
    leaked["candidates"][0]["excerpts"][0]["provider"] = "primary"
    with pytest.raises(DocumentAuthorityError, match="anonymous_evidence_invalid"):
        build_anonymous_conflict_packet(
            leaked,
            _run(_analysis(leaked, ecrf=""), "primary"),
            _run(_analysis(leaked), "verifier"),
        )


def test_dual_conflict_review_resolves_or_asks_one_plain_question() -> None:
    batch = _batch()
    reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(batch)
    accepted = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.97,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                evidence_references=_refs(
                    ("candidate_protocol", "doc:p1"),
                    ("candidate_ecrf", "xlsx:sheet:1"),
                ),
            ),
        ),
    )
    resolved = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        packet,
        _review_run(accepted, "primary"),
        _review_run(accepted, "verifier"),
    )
    assert resolved["state"] == "resolved"
    assert resolved["user_question"] == ""

    unresolved = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="unresolved",
                confidence=0.4,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                evidence_references=_refs(
                    ("candidate_protocol", "doc:p1"),
                    ("candidate_ecrf", "xlsx:sheet:1"),
                ),
            ),
        ),
    )
    result = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        packet,
        _review_run(accepted, "primary"),
        _review_run(unresolved, "verifier"),
    )
    assert result["state"] == "needs_user_input"
    assert result["user_question"].count("？") + result["user_question"].count("。") == 1
    assert "模型" not in result["user_question"]

    version_disagreement = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            accepted.decisions[0].model_copy(update={"document_version": "V2.0"}),
        ),
    )
    result = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        packet,
        _review_run(accepted, "primary"),
        _review_run(version_disagreement, "verifier"),
    )
    assert result["state"] == "needs_user_input"


def test_tampered_conflict_packet_is_rejected() -> None:
    batch = _batch()
    _reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(batch)
    packet["candidates"][0]["filename"] = "forged.docx"
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="unresolved",
                confidence=0.5,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                evidence_references=_refs(
                    ("candidate_protocol", "doc:p1"),
                    ("candidate_ecrf", "xlsx:sheet:1"),
                ),
            ),
        ),
    )

    with pytest.raises(DocumentAuthorityError, match="packet_tampered"):
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(review, "primary"),
            _review_run(review, "verifier"),
        )


def test_rehashed_packet_with_omitted_candidate_is_rebuilt_and_rejected() -> None:
    batch = _batch()
    _reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(batch)
    packet["candidates"] = packet["candidates"][:1]
    packet["candidate_coverage"] = [packet["candidates"][0]["candidate_id"]]
    packet["allowed_candidate_ids_by_role"] = {
        "ecrf": [packet["candidates"][0]["candidate_id"]]
    }
    packet["conflict_packet_sha256"] = _digest({
        key: value for key, value in packet.items() if key != "conflict_packet_sha256"
    })
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="unresolved",
                confidence=0.5,
                considered_candidate_ids=("candidate_protocol",),
                evidence_references=_refs(("candidate_protocol", "doc:p1")),
            ),
        ),
    )

    with pytest.raises(DocumentAuthorityError, match="packet_tampered"):
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(review, "primary"),
            _review_run(review, "verifier"),
        )


def test_review_candidate_and_evidence_must_close_to_role_options() -> None:
    batch = _batch()
    _reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(batch)

    def review(
        candidate_id: str, references: tuple[EvidenceReference, ...]
    ) -> DocumentAuthorityConflictReview:
        return DocumentAuthorityConflictReview(
            schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
            conflict_packet_sha256=packet["conflict_packet_sha256"],
            decisions=(
                ConflictDecision(
                    role="ecrf",
                    decision="selected",
                    selected_candidate_id=candidate_id,
                    document_version="V1.0",
                    confidence=0.99,
                    considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                    evidence_references=references,
                ),
            ),
        )

    complete_evidence = _refs(
        ("candidate_protocol", "doc:p1"),
        ("candidate_ecrf", "xlsx:sheet:1"),
    )
    with pytest.raises(DocumentAuthorityError, match="candidate_unknown"):
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(review("unknown_candidate", complete_evidence), "primary"),
            _review_run(review("unknown_candidate", complete_evidence), "verifier"),
        )
    with pytest.raises(DocumentAuthorityError, match="evidence_not_closed"):
        invented_evidence = (*complete_evidence, *_refs(("candidate_ecrf", "invented")))
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(review("candidate_ecrf", invented_evidence), "primary"),
            _review_run(review("candidate_ecrf", invented_evidence), "verifier"),
        )
    with pytest.raises(DocumentAuthorityError, match="coverage_invalid"):
        wrong_candidate_evidence = _refs(("candidate_protocol", "doc:p1"))
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(review("candidate_ecrf", wrong_candidate_evidence), "primary"),
            _review_run(review("candidate_ecrf", wrong_candidate_evidence), "verifier"),
        )


def test_duplicate_locator_strings_remain_candidate_bound() -> None:
    batch = _batch()
    batch["candidates"][0]["excerpts"][0]["locator"] = "shared:1"
    batch["candidates"][1]["sheets"][0]["locator"] = "shared:1"
    primary_analysis = _analysis(batch, ecrf="")
    verifier_analysis = _analysis(batch)
    primary_analysis = primary_analysis.model_copy(update={
        "candidate_assessments": tuple(
            item.model_copy(update={"evidence_locators": ("shared:1",)})
            for item in primary_analysis.candidate_assessments
        ),
        "role_selections": tuple(
            item.model_copy(update={"evidence_locators": ("shared:1",)})
            if item.decision == "selected" else item
            for item in primary_analysis.role_selections
        ),
    })
    verifier_analysis = verifier_analysis.model_copy(update={
        "candidate_assessments": tuple(
            item.model_copy(update={"evidence_locators": ("shared:1",)})
            for item in verifier_analysis.candidate_assessments
        ),
        "role_selections": tuple(
            item.model_copy(update={"evidence_locators": ("shared:1",)})
            if item.decision == "selected" else item
            for item in verifier_analysis.role_selections
        ),
    })
    primary = _run(primary_analysis, "primary")
    verifier = _run(verifier_analysis, "verifier")
    packet = build_anonymous_conflict_packet(batch, primary, verifier)
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.99,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                evidence_references=_refs(("candidate_protocol", "shared:1")),
            ),
        ),
    )

    with pytest.raises(DocumentAuthorityError, match="coverage_invalid"):
        resolve_document_authority_conflicts(
            batch,
            primary,
            verifier,
            packet,
            _review_run(review, "primary"),
            _review_run(review, "verifier"),
        )


def test_unreadable_batch_can_reach_one_user_question_without_fake_evidence() -> None:
    batch = {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_unreadable",
        "authority_status": "not_adjudicated",
        "candidates": [{
            "candidate_id": "candidate_unreadable",
            "filename": "unknown.pdf",
            "role_hypotheses": [],
            "technical_status": "unreadable",
            "extraction_status": "needs_ocr",
            "locator_count": 0,
            "excerpts": [],
            "sheets": [],
        }],
    }
    assessment = CandidateAssessment(
        candidate_id="candidate_unreadable",
        inferred_role="uncertain",
        usable=False,
        confidence=0.2,
        uncertainty="无法提取内容",
    )
    analysis = DocumentAuthorityAnalysis(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        batch_id=batch["batch_id"],
        input_sha256=_digest(batch),
        candidate_assessments=(assessment,),
        role_selections=tuple(
            RoleSelection(
                role=role,
                decision="unresolved" if role in {"protocol", "ecrf"} else "missing",
                confidence=0.2 if role in {"protocol", "ecrf"} else 0.95,
                uncertainty="无法提取内容",
            )
            for role in ("protocol", "investigator_brochure", "ecrf", "sap")
        ),
    )
    primary = _run(analysis, "primary")
    verifier = _run(analysis, "verifier")
    packet = build_anonymous_conflict_packet(batch, primary, verifier)
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=tuple(
            ConflictDecision(
                role=role,
                decision="unresolved",
                confidence=0.2,
                considered_candidate_ids=("candidate_unreadable",),
                uncertainty="没有可核对的正文",
            )
            for role in ("protocol", "ecrf")
        ),
    )

    result = resolve_document_authority_conflicts(
        batch,
        primary,
        verifier,
        packet,
        _review_run(review, "primary"),
        _review_run(review, "verifier"),
    )

    assert result["state"] == "needs_user_input"
    assert result["user_question"]
