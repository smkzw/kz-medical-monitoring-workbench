from __future__ import annotations

import copy
import hashlib
import json

import pytest

from packages.medical_monitoring.admission.document_authority import (
    AdjudicationDecision,
    DOCUMENT_AUTHORITY_SCHEMA_VERSION,
    LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION,
    LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION,
    REPLAY_ADJUDICATION_PROMPT_PAIRS,
    CandidateAssessment,
    ConflictDecision,
    DocumentAuthorityAnalysis,
    DocumentAuthorityAdjudicationReview,
    DocumentAuthorityConflictRunEnvelope,
    DocumentAuthorityConflictReview,
    DocumentAuthorityError,
    DocumentAuthorityRunEnvelope,
    EvidenceReference,
    FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS,
    PRIMARY_ADJUDICATION_PROMPT_VERSION,
    PRIMARY_PROMPT_VERSION,
    PRIMARY_REVIEW_PROMPT_VERSION,
    ResolvedRole,
    RoleSelection,
    RoleSupplementaryBinding,
    VERIFIER_PROMPT_VERSION,
    VERIFIER_ADJUDICATION_PROMPT_VERSION,
    VERIFIER_REVIEW_PROMPT_VERSION,
    build_anonymous_conflict_packet,
    build_anonymous_adjudication_context,
    document_authority_batch_sha256,
    reconcile_document_authority,
    resolve_document_authority_conflicts,
    resolve_document_authority_adjudication,
    validate_document_authority_analysis,
    validate_document_authority_adjudication_context,
    validate_document_authority_adjudication_review,
    validate_document_authority_conflict_packet,
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


def test_batch_rejects_locator_content_when_locator_count_is_zero() -> None:
    batch = _batch()
    batch["candidates"][0]["locator_count"] = 0

    with pytest.raises(
        DocumentAuthorityError,
        match="document_authority_candidate_locator_count_invalid",
    ):
        document_authority_batch_sha256(batch)


def test_legacy_batch_allows_historical_full_locator_count_above_excerpts() -> None:
    batch = _batch()
    batch["candidates"][0]["locator_count"] = 13

    assert document_authority_batch_sha256(batch) == _digest(batch)


def _ocr_batch() -> dict:
    candidate_id = "candidate_scan"
    locator = f"candidate:{candidate_id}:p1:ocr"
    text = "REAL TEXT"
    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    candidate = {
        "candidate_id": candidate_id,
        "filename": "scan.pdf",
        "role_hypotheses": ["protocol"],
        "technical_status": "ready",
        "extraction_status": "parsed",
        "page_count": 1,
        "locator_count": 1,
        "locator_index_sha256": _digest([locator]),
        "excerpts": [{
            "locator": locator,
            "text": text,
            "text_sha256": text_sha256,
        }],
        "sheets": [],
        "zero_text_page_count": 1,
        "zero_text_page_samples": [1],
        "ocr_recovery_pages": [{
            "page_number": 1,
            "dpi": 200,
            "image_sha256": "a" * 64,
            "locator": locator,
            "requested_model": "ocr-model",
            "actual_model": "ocr-model",
            "provider": "test",
            "fell_back": False,
            "status": "recovered",
            "failure_code": "",
            "text_sha256": text_sha256,
            "character_count": len(text),
        }],
    }
    candidate["evidence_revision_sha256"] = _digest(candidate)
    return {
        "manifest_version": "monitoring-document-candidate-v1",
        "batch_id": "mmbatch_ocr",
        "authority_status": "not_adjudicated",
        "candidates": [candidate],
    }


@pytest.mark.parametrize("tamper", ("text_hash", "locator_index", "page_locator"))
def test_revised_ocr_candidate_recomputes_hash_and_locator_closure(
    tamper: str,
) -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    if tamper == "text_hash":
        candidate["excerpts"][0]["text_sha256"] = "1" * 64
        candidate["ocr_recovery_pages"][0]["text_sha256"] = "1" * 64
    elif tamper == "locator_index":
        candidate["locator_index_sha256"] = "0" * 64
    else:
        wrong = "candidate:candidate_scan:p2:ocr"
        candidate["excerpts"][0]["locator"] = wrong
        candidate["ocr_recovery_pages"][0]["locator"] = wrong
        candidate["locator_index_sha256"] = _digest([wrong])
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError):
        document_authority_batch_sha256(batch)


def test_revised_candidate_cannot_claim_parsed_when_ocr_failed() -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    evidence = candidate["ocr_recovery_pages"][0]
    candidate["excerpts"] = []
    candidate["locator_count"] = 0
    candidate["locator_index_sha256"] = _digest([])
    evidence.update({
        "locator": "",
        "actual_model": "",
        "status": "failed",
        "failure_code": "ocr_runtime_unavailable",
        "text_sha256": hashlib.sha256(b"").hexdigest(),
        "character_count": 0,
    })
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError, match="ocr_status_invalid"):
        document_authority_batch_sha256(batch)


def test_revised_candidate_rejects_wrong_recovered_page_with_matching_count() -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    candidate["zero_text_page_count"] = 2
    candidate["zero_text_page_samples"] = [1, 2]
    wrong = copy.deepcopy(candidate["ocr_recovery_pages"][0])
    wrong_locator = "candidate:candidate_scan:p3:ocr"
    wrong["page_number"] = 3
    wrong["locator"] = wrong_locator
    candidate["ocr_recovery_pages"].append(wrong)
    candidate["excerpts"].append({
        **candidate["excerpts"][0],
        "locator": wrong_locator,
    })
    candidate["locator_count"] = 2
    candidate["locator_index_sha256"] = _digest([
        candidate["excerpts"][0]["locator"],
        wrong_locator,
    ])
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError, match="ocr_evidence_invalid"):
        document_authority_batch_sha256(batch)


def test_revised_candidate_rejects_ocr_page_outside_pdf_page_count() -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    candidate["page_count"] = 1
    candidate["zero_text_page_samples"] = [2]
    evidence = candidate["ocr_recovery_pages"][0]
    wrong_locator = "candidate:candidate_scan:p2:ocr"
    evidence["page_number"] = 2
    evidence["locator"] = wrong_locator
    candidate["excerpts"][0]["locator"] = wrong_locator
    candidate["locator_index_sha256"] = _digest([wrong_locator])
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError, match="ocr_evidence_invalid"):
        document_authority_batch_sha256(batch)


def test_revised_candidate_rejects_missing_requested_ocr_model() -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    candidate["ocr_recovery_pages"][0]["requested_model"] = ""
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError, match="ocr_evidence_invalid"):
        document_authority_batch_sha256(batch)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_model", "invented-model"),
        ("fell_back", True),
        ("requested_model", ""),
    ),
)
def test_revised_candidate_rejects_failed_ocr_provenance_tampering(
    field: str, value: object,
) -> None:
    batch = _ocr_batch()
    candidate = batch["candidates"][0]
    evidence = candidate["ocr_recovery_pages"][0]
    candidate["extraction_status"] = "needs_ocr"
    candidate["excerpts"] = []
    candidate["locator_count"] = 0
    candidate["locator_index_sha256"] = _digest([])
    evidence.update({
        "locator": "",
        "actual_model": "",
        "fell_back": False,
        "status": "failed",
        "failure_code": "ocr_runtime_unavailable",
        "text_sha256": hashlib.sha256(b"").hexdigest(),
        "character_count": 0,
        field: value,
    })
    candidate["evidence_revision_sha256"] = _digest({
        key: value
        for key, value in candidate.items()
        if key != "evidence_revision_sha256"
    })

    with pytest.raises(DocumentAuthorityError, match="ocr_evidence_invalid"):
        document_authority_batch_sha256(batch)


def test_batch_rejects_more_than_review_schema_can_cover() -> None:
    template = _batch()["candidates"][0]
    batch = _batch()
    batch["candidates"] = [
        {**template, "candidate_id": f"candidate_{index:03d}"}
        for index in range(101)
    ]

    with pytest.raises(
        DocumentAuthorityError,
        match="document_authority_candidate_coverage_invalid",
    ):
        document_authority_batch_sha256(batch)


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
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="investigator_brochure",
                decision="missing",
                confidence=0.95,
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="ecrf",
                decision="selected" if ecrf else "unresolved",
                selected_candidate_id=ecrf,
                confidence=0.98 if ecrf else 0.5,
                evidence_locators=("xlsx:sheet:1",) if ecrf else (),
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="sap",
                decision="missing",
                confidence=0.95,
                supplementary_bindings=(),
            ),
        ),
    )


def test_analysis_rejects_usable_candidate_with_incomplete_extraction() -> None:
    batch = _batch()
    batch["candidates"][0]["extraction_status"] = "needs_ocr"

    with pytest.raises(DocumentAuthorityError, match="candidate_not_usable"):
        validate_document_authority_analysis(batch, _analysis(batch))


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
        job_input_revision_sha256="f" * 64,
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


def test_legacy_v6_analysis_pair_replays_but_mixed_generation_fails() -> None:
    batch = _batch()
    analysis = _analysis(batch)
    primary = _run(analysis, "primary").model_copy(
        update={"prompt_version": "monitoring-document-authority-primary-v6"}
    )
    verifier = _run(analysis, "verifier").model_copy(
        update={"prompt_version": "monitoring-document-authority-verifier-v6"}
    )

    assert reconcile_document_authority(batch, primary, verifier)["state"] == "resolved"
    with pytest.raises(DocumentAuthorityError, match="run_identity_invalid"):
        reconcile_document_authority(batch, _run(analysis, "primary"), verifier)


def _review_run(
    review: DocumentAuthorityConflictReview,
    role: str,
    *,
    adjudication: bool = False,
) -> DocumentAuthorityConflictRunEnvelope:
    primary = role == "primary"
    return DocumentAuthorityConflictRunEnvelope(
        run_id=f"{role}-{'adjudication' if adjudication else 'review'}-run",
        job_id=f"{role}-{'adjudication' if adjudication else 'review'}-job",
        role=role,
        provider=(
            MONITORING_C3_MAPPING_PROVIDER
            if primary else MONITORING_C3_VERIFIER_PROVIDER
        ),
        model=MONITORING_C3_MAPPING_MODEL if primary else MONITORING_C3_VERIFIER_MODEL,
        prompt_version=(
            PRIMARY_ADJUDICATION_PROMPT_VERSION
            if primary and adjudication
            else VERIFIER_ADJUDICATION_PROMPT_VERSION
            if adjudication
            else PRIMARY_REVIEW_PROMPT_VERSION
            if primary
            else VERIFIER_REVIEW_PROMPT_VERSION
        ),
        conflict_packet_sha256=review.conflict_packet_sha256,
        job_input_revision_sha256="f" * 64,
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


def test_dual_analysis_requires_one_job_input_revision() -> None:
    batch = _batch()
    primary = _run(_analysis(batch), "primary")
    verifier = _run(_analysis(batch), "verifier").model_copy(
        update={"job_input_revision_sha256": "e" * 64}
    )

    with pytest.raises(DocumentAuthorityError, match="input_revision_mismatch"):
        reconcile_document_authority(batch, primary, verifier)


@pytest.mark.parametrize(
    "field_update",
    (
        {"uncertainty": "该受试者事件确定为CTCAE 3级，应立即生成Query。"},
        {"document_version": "V2.0 高风险信号"},
        {"uncertainty": "风险判定为高。"},
        {"uncertainty": "该患者不良反应判定为3级，应向研究中心发出质疑。"},
        {"uncertainty": "该病例存在严重毒性，需要立即干预。"},
    ),
)
def test_document_authority_text_rejects_uncontrolled_free_text(
    field_update: dict,
) -> None:
    with pytest.raises(ValueError):
        CandidateAssessment(
            candidate_id="candidate_protocol",
            inferred_role="protocol",
            usable=True,
            confidence=0.98,
            evidence_locators=("doc:p1",),
            **field_update,
        )
    with pytest.raises(ValueError):
        ConflictDecision(
            role="protocol",
            decision="unresolved",
            confidence=0.4,
            supplementary_candidate_ids=(),
            uncertainty="发现安全性信号，应生成Query。",
        )


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
        update={"evidence_locators": ("doc:p2",), "uncertainty": "version_unclear"}
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


def test_conflict_packet_rejects_zero_count_locator_and_excess_candidates() -> None:
    batch = _batch()
    primary = _run(_analysis(batch), "primary")
    verifier = _run(_analysis(batch, ecrf=""), "verifier")
    packet = build_anonymous_conflict_packet(batch, primary, verifier)

    zero_count = json.loads(json.dumps(packet))
    zero_count["candidates"][0]["locator_count"] = 0
    zero_count["conflict_packet_sha256"] = _digest({
        key: value
        for key, value in zero_count.items()
        if key != "conflict_packet_sha256"
    })
    with pytest.raises(DocumentAuthorityError, match="conflict_packet_invalid"):
        validate_document_authority_conflict_packet(zero_count)

    excess = json.loads(json.dumps(packet))
    template = excess["candidates"][0]
    excess["candidates"] = [
        {**template, "candidate_id": f"candidate_{index:03d}"}
        for index in range(101)
    ]
    candidate_ids = sorted(
        item["candidate_id"] for item in excess["candidates"]
    )
    excess["candidate_coverage"] = candidate_ids
    excess["allowed_candidate_ids_by_role"] = {
        role: candidate_ids for role in excess["conflict_roles"]
    }
    excess["conflict_packet_sha256"] = _digest({
        key: value
        for key, value in excess.items()
        if key != "conflict_packet_sha256"
    })
    with pytest.raises(DocumentAuthorityError, match="conflict_packet_invalid"):
        validate_document_authority_conflict_packet(excess)

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
                supplementary_candidate_ids=(),
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

    mismatched_review = _review_run(accepted, "verifier").model_copy(
        update={"job_input_revision_sha256": "e" * 64}
    )
    with pytest.raises(DocumentAuthorityError, match="input_revision_mismatch"):
        resolve_document_authority_conflicts(
            batch,
            analysis_primary,
            analysis_verifier,
            packet,
            _review_run(accepted, "primary"),
            mismatched_review,
        )

    unresolved = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="unresolved",
                confidence=0.4,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                supplementary_candidate_ids=(),
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


def test_conflict_review_accepts_equivalent_metadata_and_independent_evidence() -> None:
    batch = _batch()
    batch["candidates"][0]["locator_count"] = 2
    batch["candidates"][0]["excerpts"].append(
        {"locator": "doc:p2", "text": "研究方案版本与日期"}
    )
    batch["candidates"][1]["locator_count"] = 2
    batch["candidates"][1]["sheets"].append(
        {"locator": "xlsx:sheet:2", "sheet_name": "访视数据"}
    )
    _reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(
        batch
    )
    primary = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                document_date="2024年4月17日",
                confidence=0.88,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                supplementary_candidate_ids=(),
                evidence_references=_refs(
                    ("candidate_protocol", "doc:p1"),
                    ("candidate_ecrf", "xlsx:sheet:1"),
                ),
            ),
        ),
    )
    verifier = primary.model_copy(
        update={
            "decisions": (
                primary.decisions[0].model_copy(
                    update={
                        "document_version": "1.0",
                        "document_date": "2024-04-17",
                        "confidence": 0.75,
                        "evidence_references": _refs(
                            ("candidate_protocol", "doc:p2"),
                            ("candidate_ecrf", "xlsx:sheet:2"),
                        ),
                    }
                ),
            )
        }
    )

    result = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        packet,
        _review_run(primary, "primary"),
        _review_run(verifier, "verifier"),
    )

    assert result["state"] == "resolved"
    assert result["user_question"] == ""


def test_conflict_review_keeps_low_consensus_confidence_unresolved() -> None:
    batch = _batch()
    _reconciliation, packet, analysis_primary, analysis_verifier = _conflict_context(
        batch
    )
    review = DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.74,
                considered_candidate_ids=("candidate_protocol", "candidate_ecrf"),
                supplementary_candidate_ids=(),
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
        _review_run(review, "primary"),
        _review_run(review, "verifier"),
    )

    assert result["state"] == "needs_user_input"
    assert result["unresolved_roles"] == ["ecrf"]


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
                supplementary_candidate_ids=(),
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
                supplementary_candidate_ids=(),
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
                    supplementary_candidate_ids=(),
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
                supplementary_candidate_ids=(),
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
        uncertainty="content_unreadable",
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
                supplementary_bindings=(),
                uncertainty="content_unreadable",
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
                supplementary_candidate_ids=(),
                uncertainty="evidence_insufficient",
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


def _composite_batch() -> dict:
    batch = _batch()
    batch["candidates"].extend([
        {
            "candidate_id": "candidate_protocol_erratum",
            "filename": "protocol_erratum.docx",
            "role_hypotheses": ["protocol"],
            "technical_status": "ready",
            "extraction_status": "parsed",
            "locator_count": 1,
            "excerpts": [{"locator": "erratum:p1", "text": "方案 V2.0 勘误说明"}],
            "sheets": [],
        },
        {
            "candidate_id": "candidate_ecrf_addendum",
            "filename": "ecrf_addendum.xlsx",
            "role_hypotheses": ["ecrf"],
            "technical_status": "ready",
            "extraction_status": "parsed",
            "locator_count": 1,
            "excerpts": [],
            "sheets": [{"locator": "xlsx:sheet:2", "sheet_name": "AE_Addendum"}],
        },
    ])
    return batch


def _composite_analysis(
    batch: dict,
    *,
    ecrf: str = "candidate_ecrf",
    bind_erratum: bool = False,
) -> DocumentAuthorityAnalysis:
    assessments = (
        CandidateAssessment(
            candidate_id="candidate_protocol",
            inferred_role="protocol",
            usable=True,
            confidence=0.98,
            evidence_locators=("doc:p1",),
        ),
        CandidateAssessment(
            candidate_id="candidate_protocol_erratum",
            inferred_role="protocol",
            usable=True,
            confidence=0.97,
            document_version="V1.1",
            evidence_locators=("erratum:p1",),
        ),
        CandidateAssessment(
            candidate_id="candidate_ecrf",
            inferred_role="ecrf",
            usable=True,
            confidence=0.98,
            evidence_locators=("xlsx:sheet:1",),
        ),
        CandidateAssessment(
            candidate_id="candidate_ecrf_addendum",
            inferred_role="ecrf",
            usable=True,
            confidence=0.96,
            evidence_locators=("xlsx:sheet:2",),
        ),
    )
    erratum_binding = (
        RoleSupplementaryBinding(
            candidate_id="candidate_protocol_erratum",
            evidence_locators=("erratum:p1",),
        ),
    ) if bind_erratum else ()
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
                supplementary_bindings=erratum_binding,
            ),
            RoleSelection(
                role="investigator_brochure",
                decision="missing",
                confidence=0.95,
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="ecrf",
                decision="selected" if ecrf else "unresolved",
                selected_candidate_id=ecrf,
                confidence=0.98 if ecrf else 0.5,
                evidence_locators=("xlsx:sheet:1",) if ecrf else (),
                supplementary_bindings=(),
            ),
            RoleSelection(
                role="sap",
                decision="missing",
                confidence=0.95,
                supplementary_bindings=(),
            ),
        ),
    )


def _composite_references() -> tuple[EvidenceReference, ...]:
    return _refs(
        ("candidate_protocol", "doc:p1"),
        ("candidate_protocol_erratum", "erratum:p1"),
        ("candidate_ecrf", "xlsx:sheet:1"),
        ("candidate_ecrf_addendum", "xlsx:sheet:2"),
    )


def _composite_conflict_context(
    batch: dict,
) -> tuple[DocumentAuthorityRunEnvelope, DocumentAuthorityRunEnvelope, dict]:
    primary = _run(_composite_analysis(batch, ecrf=""), "primary")
    verifier = _run(_composite_analysis(batch), "verifier")
    packet = build_anonymous_conflict_packet(batch, primary, verifier)
    return primary, verifier, packet


def _ecrf_composite_review(
    packet: dict,
    *,
    supplements: tuple[str, ...] = ("candidate_ecrf_addendum",),
    references: tuple[EvidenceReference, ...] | None = None,
) -> DocumentAuthorityConflictReview:
    considered = (
        "candidate_protocol",
        "candidate_protocol_erratum",
        "candidate_ecrf",
        "candidate_ecrf_addendum",
    )
    return DocumentAuthorityConflictReview(
        schema_version=DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        conflict_packet_sha256=packet["conflict_packet_sha256"],
        decisions=(
            ConflictDecision(
                role="ecrf",
                decision="selected",
                selected_candidate_id="candidate_ecrf",
                document_version="V1.0",
                confidence=0.97,
                considered_candidate_ids=considered,
                supplementary_candidate_ids=supplements,
                evidence_references=(
                    _composite_references() if references is None else references
                ),
            ),
        ),
    )


def _ecrf_adjudication_review(
    packet: dict,
    *,
    supplements: tuple[str, ...] = ("candidate_ecrf_addendum",),
) -> DocumentAuthorityAdjudicationReview:
    base = _ecrf_composite_review(packet, supplements=supplements)
    decision = base.decisions[0]
    considered = set(decision.considered_candidate_ids)
    bound = {decision.selected_candidate_id, *decision.supplementary_candidate_ids}
    return DocumentAuthorityAdjudicationReview(
        schema_version=base.schema_version,
        conflict_packet_sha256=base.conflict_packet_sha256,
        decisions=(
            AdjudicationDecision(
                **decision.model_dump(mode="python"),
                excluded_candidate_ids=tuple(sorted(considered - bound)),
            ),
        ),
    )


def test_primary_with_agreed_supplement_resolves_as_composite_authority() -> None:
    batch = _composite_batch()

    result = _reconcile(
        batch,
        _composite_analysis(batch, bind_erratum=True),
        _composite_analysis(batch, bind_erratum=True),
    )

    assert result["state"] == "resolved"
    protocol_row = next(
        item for item in result["resolved_roles"] if item["role"] == "protocol"
    )
    assert protocol_row["candidate_id"] == "candidate_protocol"
    assert protocol_row["supplementary_candidate_ids"] == [
        "candidate_protocol_erratum"
    ]


def test_supplement_disagreement_between_models_blocks_auto_resolution() -> None:
    batch = _composite_batch()

    result = _reconcile(
        batch,
        _composite_analysis(batch, bind_erratum=True),
        _composite_analysis(batch),
    )

    assert result["state"] == "needs_dual_review"
    protocol_conflict = next(
        item for item in result["conflicts"] if item["role"] == "protocol"
    )
    assert protocol_conflict["candidate_options"] == [
        "candidate_protocol",
        "candidate_protocol_erratum",
    ]


def test_supplement_assessment_disagreement_blocks_auto_resolution() -> None:
    batch = _composite_batch()
    primary = _composite_analysis(batch, bind_erratum=True)
    shifted = primary.candidate_assessments[1].model_copy(
        update={"document_version": "V1.2"}
    )
    verifier = primary.model_copy(update={
        "candidate_assessments": (
            primary.candidate_assessments[0],
            shifted,
            *primary.candidate_assessments[2:],
        )
    })

    result = _reconcile(batch, primary, verifier)

    assert result["state"] == "needs_dual_review"
    assert any(item["role"] == "protocol" for item in result["conflicts"])


def test_supplementary_binding_requires_locator_closure() -> None:
    batch = _composite_batch()
    analysis = _composite_analysis(batch, bind_erratum=True)
    unclosed_binding = RoleSupplementaryBinding(
        candidate_id="candidate_protocol_erratum",
        evidence_locators=("invented",),
    )
    bad_selection = analysis.role_selections[0].model_copy(
        update={"supplementary_bindings": (unclosed_binding,)}
    )
    unclosed = analysis.model_copy(
        update={"role_selections": (bad_selection, *analysis.role_selections[1:])}
    )

    with pytest.raises(DocumentAuthorityError, match="evidence_not_closed"):
        _reconcile(batch, unclosed, unclosed)


def test_supplementary_candidate_must_be_usable_same_role() -> None:
    batch = _composite_batch()
    analysis = _composite_analysis(batch, bind_erratum=True)
    unusable = analysis.candidate_assessments[1].model_copy(update={"usable": False})
    unusable_analysis = analysis.model_copy(update={
        "candidate_assessments": (
            analysis.candidate_assessments[0],
            unusable,
            *analysis.candidate_assessments[2:],
        )
    })
    with pytest.raises(DocumentAuthorityError, match="selection_inconsistent"):
        _reconcile(batch, unusable_analysis, unusable_analysis)

    role_shift = analysis.candidate_assessments[1].model_copy(
        update={"inferred_role": "sap"}
    )
    shifted_analysis = analysis.model_copy(update={
        "candidate_assessments": (
            analysis.candidate_assessments[0],
            role_shift,
            *analysis.candidate_assessments[2:],
        )
    })
    with pytest.raises(DocumentAuthorityError, match="selection_inconsistent"):
        _reconcile(batch, shifted_analysis, shifted_analysis)


def test_supplementary_binding_model_guards() -> None:
    analysis_payload = _analysis(_batch()).model_dump(mode="json")
    analysis_payload["role_selections"][0].pop("supplementary_bindings")
    with pytest.raises(ValueError):
        DocumentAuthorityAnalysis.model_validate(analysis_payload)

    with pytest.raises(ValueError):
        RoleSelection(
            role="protocol",
            decision="missing",
            confidence=0.95,
            supplementary_bindings=(
                RoleSupplementaryBinding(
                    candidate_id="candidate_protocol_erratum",
                    evidence_locators=("erratum:p1",),
                ),
            ),
        )


def test_conflict_review_requires_explicit_supplement_accounting() -> None:
    batch = _composite_batch()
    _primary, _verifier, packet = _composite_conflict_context(batch)
    payload = _ecrf_composite_review(packet).model_dump(mode="json")
    payload["decisions"][0].pop("supplementary_candidate_ids")

    with pytest.raises(ValueError):
        DocumentAuthorityConflictReview.model_validate(payload)
    with pytest.raises(ValueError):
        RoleSupplementaryBinding(
            candidate_id="candidate_protocol_erratum",
            evidence_locators=(),
        )
    with pytest.raises(ValueError):
        RoleSelection(
            role="protocol",
            decision="selected",
            selected_candidate_id="candidate_protocol",
            confidence=0.98,
            evidence_locators=("doc:p1",),
            supplementary_bindings=(
                RoleSupplementaryBinding(
                    candidate_id="candidate_protocol_erratum",
                    evidence_locators=("erratum:p1",),
                ),
                RoleSupplementaryBinding(
                    candidate_id="candidate_protocol_erratum",
                    evidence_locators=("erratum:p1",),
                ),
            ),
        )
    with pytest.raises(ValueError):
        RoleSelection(
            role="protocol",
            decision="selected",
            selected_candidate_id="candidate_protocol",
            confidence=0.98,
            evidence_locators=("doc:p1",),
            supplementary_bindings=(
                RoleSupplementaryBinding(
                    candidate_id="candidate_protocol",
                    evidence_locators=("doc:p1",),
                ),
            ),
        )
    with pytest.raises(ValueError):
        ResolvedRole(
            role="sap",
            status="missing",
            supplementary_candidate_ids=("candidate_sap_note",),
        )
    with pytest.raises(ValueError):
        ResolvedRole(
            role="protocol",
            status="selected",
            candidate_id="candidate_protocol",
            supplementary_candidate_ids=("candidate_protocol",),
        )


def test_conflict_review_resolves_composite_selection_with_supplements() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    review = _ecrf_composite_review(packet)

    result = resolve_document_authority_conflicts(
        batch,
        primary,
        verifier,
        packet,
        _review_run(review, "primary"),
        _review_run(review, "verifier"),
    )

    assert result["state"] == "resolved"
    ecrf_row = next(item for item in result["resolved_roles"] if item["role"] == "ecrf")
    assert ecrf_row["candidate_id"] == "candidate_ecrf"
    assert ecrf_row["supplementary_candidate_ids"] == ["candidate_ecrf_addendum"]


def test_conflict_review_supplement_disagreement_requires_user() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    accepted = _ecrf_composite_review(packet)
    without_supplement = _ecrf_composite_review(packet, supplements=())

    result = resolve_document_authority_conflicts(
        batch,
        primary,
        verifier,
        packet,
        _review_run(accepted, "primary"),
        _review_run(without_supplement, "verifier"),
    )

    assert result["state"] == "needs_user_input"


def test_internal_adjudication_resolves_material_supplement_disagreement() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    with_supplement = _ecrf_composite_review(packet)
    without_supplement = _ecrf_composite_review(packet, supplements=())
    primary_review = _review_run(with_supplement, "primary")
    verifier_review = _review_run(without_supplement, "verifier")
    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
    )

    assert context["unresolved_roles"] == ["ecrf"]
    assert len(context["options_by_role"]["ecrf"]) == 2
    assert context["disputed_candidate_ids_by_role"] == {
        "ecrf": ["candidate_ecrf_addendum"]
    }
    validate_document_authority_adjudication_context(packet, context)

    result = resolve_document_authority_adjudication(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
        context,
        _review_run(_ecrf_adjudication_review(packet), "primary", adjudication=True),
        _review_run(_ecrf_adjudication_review(packet), "verifier", adjudication=True),
    )

    assert result["state"] == "resolved"
    ecrf = next(item for item in result["resolved_roles"] if item["role"] == "ecrf")
    assert ecrf["supplementary_candidate_ids"] == ["candidate_ecrf_addendum"]
    assert result["adjudication_run_ids"] == [
        "primary-adjudication-run",
        "verifier-adjudication-run",
    ]


def test_adjudication_context_allows_metadata_only_dispute() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    first = _ecrf_composite_review(packet)
    second = first.model_copy(
        update={
            "decisions": (
                first.decisions[0].model_copy(
                    update={"document_version": "V2.0"}
                ),
            )
        }
    )

    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        _review_run(first, "primary"),
        _review_run(second, "verifier"),
    )

    assert context["unresolved_roles"] == ["ecrf"]
    assert context["disputed_candidate_ids_by_role"] == {"ecrf": []}
    validate_document_authority_adjudication_context(packet, context)


def test_legacy_v1_adjudication_context_remains_replayable() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    with_supplement = _ecrf_composite_review(packet)
    without_supplement = _ecrf_composite_review(packet, supplements=())
    primary_review = _review_run(with_supplement, "primary")
    verifier_review = _review_run(without_supplement, "verifier")
    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
        legacy_v1=True,
    )
    primary_adjudication = _review_run(with_supplement, "primary", adjudication=True)
    verifier_adjudication = _review_run(with_supplement, "verifier", adjudication=True)
    primary_adjudication = primary_adjudication.model_copy(
        update={"prompt_version": LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION}
    )
    verifier_adjudication = verifier_adjudication.model_copy(
        update={"prompt_version": LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION}
    )

    result = resolve_document_authority_adjudication(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
        context,
        primary_adjudication,
        verifier_adjudication,
    )

    assert context["schema_version"] == "monitoring-document-authority-adjudication-v1"
    assert "disputed_candidate_ids_by_role" not in context
    assert result["state"] == "resolved"


@pytest.mark.parametrize(
    ("primary_prompt", "verifier_prompt"),
    tuple(sorted(REPLAY_ADJUDICATION_PROMPT_PAIRS)),
)
def test_previous_adjudication_prompts_remain_replayable(
    primary_prompt: str,
    verifier_prompt: str,
) -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    with_supplement = _ecrf_composite_review(packet)
    without_supplement = _ecrf_composite_review(packet, supplements=())
    primary_review = _review_run(with_supplement, "primary")
    verifier_review = _review_run(without_supplement, "verifier")
    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
    )
    adjudication = _ecrf_adjudication_review(packet)
    primary_adjudication = _review_run(
        adjudication, "primary", adjudication=True
    ).model_copy(
        update={"prompt_version": primary_prompt}
    )
    verifier_adjudication = _review_run(
        adjudication, "verifier", adjudication=True
    ).model_copy(
        update={"prompt_version": verifier_prompt}
    )

    result = resolve_document_authority_adjudication(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
        context,
        primary_adjudication,
        verifier_adjudication,
    )

    assert context["schema_version"] == "monitoring-document-authority-adjudication-v2"
    assert result["state"] == "resolved"

    with pytest.raises(DocumentAuthorityError, match="run_identity_invalid"):
        resolve_document_authority_adjudication(
            batch,
            primary,
            verifier,
            packet,
            primary_review,
            verifier_review,
            context,
            primary_adjudication,
            _review_run(adjudication, "verifier", adjudication=True),
        )

    replay_pairs = sorted(REPLAY_ADJUDICATION_PROMPT_PAIRS)
    mixed_primary = primary_adjudication.model_copy(
        update={"prompt_version": replay_pairs[0][0]}
    )
    mixed_verifier = verifier_adjudication.model_copy(
        update={"prompt_version": replay_pairs[1][1]}
    )
    with pytest.raises(DocumentAuthorityError, match="run_identity_invalid"):
        resolve_document_authority_adjudication(
            batch,
            primary,
            verifier,
            packet,
            primary_review,
            verifier_review,
            context,
            mixed_primary,
            mixed_verifier,
        )
    with pytest.raises(DocumentAuthorityError, match="run_identity_invalid"):
        resolve_document_authority_adjudication(
            batch,
            primary,
            verifier,
            packet,
            primary_review,
            verifier_review,
            context,
            primary_adjudication.model_copy(
                update={"prompt_version": replay_pairs[1][0]}
            ),
            verifier_adjudication.model_copy(
                update={"prompt_version": replay_pairs[0][1]}
            ),
        )


def test_v2_adjudication_review_covers_only_unresolved_roles() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    primary_review = _review_run(_ecrf_composite_review(packet), "primary")
    verifier_review = _review_run(
        _ecrf_composite_review(packet, supplements=()), "verifier"
    )
    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
    )
    packet_body = {
        key: value for key, value in packet.items() if key != "conflict_packet_sha256"
    }
    packet_body["conflict_roles"] = ["protocol", "ecrf"]
    packet_body["allowed_candidate_ids_by_role"] = {
        role: sorted(packet["candidate_coverage"])
        for role in packet_body["conflict_roles"]
    }
    expanded_packet = {
        **packet_body,
        "conflict_packet_sha256": _digest(packet_body),
    }
    context_body = {
        key: value
        for key, value in context.items()
        if key != "adjudication_context_sha256"
    }
    context_body["conflict_packet_sha256"] = expanded_packet[
        "conflict_packet_sha256"
    ]
    expanded_context = {
        **context_body,
        "adjudication_context_sha256": _digest(context_body),
    }
    review = _ecrf_adjudication_review(expanded_packet)

    validate_document_authority_adjudication_review(
        expanded_packet, expanded_context, review
    )

    extra_role = review.decisions[0].model_copy(
        update={"role": "protocol", "excluded_candidate_ids": ()}
    )
    with pytest.raises(DocumentAuthorityError, match="review_coverage_invalid"):
        validate_document_authority_adjudication_review(
            expanded_packet,
            expanded_context,
            review.model_copy(update={"decisions": (*review.decisions, extra_role)}),
        )
    validate_document_authority_adjudication_review(
        expanded_packet,
        expanded_context,
        review.model_copy(update={"decisions": (*review.decisions, extra_role)}),
        prompt_version=sorted(FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS)[-1][0],
    )
    with pytest.raises(DocumentAuthorityError, match="review_coverage_invalid"):
        validate_document_authority_adjudication_review(
            expanded_packet,
            expanded_context,
            review.model_copy(update={"decisions": (*review.decisions, extra_role)}),
            prompt_version="monitoring-document-authority-adjudication-primary-v5",
        )


def test_internal_adjudication_remains_fail_closed_and_context_bound() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    with_supplement = _ecrf_composite_review(packet)
    without_supplement = _ecrf_composite_review(packet, supplements=())
    primary_review = _review_run(with_supplement, "primary")
    verifier_review = _review_run(without_supplement, "verifier")
    context = build_anonymous_adjudication_context(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
    )

    result = resolve_document_authority_adjudication(
        batch,
        primary,
        verifier,
        packet,
        primary_review,
        verifier_review,
        context,
        _review_run(_ecrf_adjudication_review(packet), "primary", adjudication=True),
        _review_run(
            _ecrf_adjudication_review(packet, supplements=()),
            "verifier",
            adjudication=True,
        ),
    )
    assert result["state"] == "needs_user_input"
    assert result["unresolved_roles"] == ["ecrf"]

    with pytest.raises(ValueError):
        DocumentAuthorityAdjudicationReview.model_validate(
            with_supplement.model_dump(mode="json")
        )

    tampered = json.loads(json.dumps(context))
    tampered["options_by_role"]["ecrf"][0]["confidence"] = 0.99
    with pytest.raises(DocumentAuthorityError, match="context_tampered"):
        resolve_document_authority_adjudication(
            batch,
            primary,
            verifier,
            packet,
            primary_review,
            verifier_review,
            tampered,
            _review_run(_ecrf_adjudication_review(packet), "primary", adjudication=True),
            _review_run(_ecrf_adjudication_review(packet), "verifier", adjudication=True),
        )


def test_conflict_review_supplement_must_be_allowed_and_evidence_bound() -> None:
    batch = _composite_batch()
    primary, verifier, packet = _composite_conflict_context(batch)
    unknown_supplement = _ecrf_composite_review(
        packet, supplements=("unknown_candidate",)
    )

    with pytest.raises(DocumentAuthorityError, match="candidate_unknown"):
        resolve_document_authority_conflicts(
            batch,
            primary,
            verifier,
            packet,
            _review_run(unknown_supplement, "primary"),
            _review_run(unknown_supplement, "verifier"),
        )


def test_conflict_review_supplement_requires_direct_evidence() -> None:
    batch = _composite_batch()
    batch["candidates"][3]["locator_count"] = 0
    batch["candidates"][3]["sheets"] = []

    def zero_locator_analysis(ecrf: str) -> DocumentAuthorityAnalysis:
        analysis = _composite_analysis(batch, ecrf=ecrf)
        fixed = analysis.candidate_assessments[3].model_copy(
            update={"evidence_locators": ()}
        )
        return analysis.model_copy(update={
            "candidate_assessments": (
                *analysis.candidate_assessments[:3],
                fixed,
            )
        })

    primary = _run(zero_locator_analysis(ecrf=""), "primary")
    verifier = _run(zero_locator_analysis(ecrf="candidate_ecrf"), "verifier")
    packet = build_anonymous_conflict_packet(batch, primary, verifier)
    review = _ecrf_composite_review(
        packet,
        references=_refs(
            ("candidate_protocol", "doc:p1"),
            ("candidate_protocol_erratum", "erratum:p1"),
            ("candidate_ecrf", "xlsx:sheet:1"),
        ),
    )

    with pytest.raises(DocumentAuthorityError, match="evidence_not_closed"):
        resolve_document_authority_conflicts(
            batch,
            primary,
            verifier,
            packet,
            _review_run(review, "primary"),
            _review_run(review, "verifier"),
        )
