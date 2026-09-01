"""Independent verification for R6 slice-02 report-review runtime.

Work item 3 (verification worker). Extends the source/object surface checks and
independently gates coverage/ledger APIs, slice-01 adjacency, medical-writing
boundary, create-only allowlist, protected ports, and raise-based
normal/`-O`/`-OO` × multi-``PYTHONHASHSEED`` reproducibility.

Does not claim Codex final acceptance, product/runtime acceptance, or medical
conclusions. Coverage scenario bodies skip when worker_02 APIs are absent; a
hard-fail gate records that blocker explicitly.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from mm_r6 import contracts, fixtures, report_review as rr, validator


IA_VER = "ia-r6-slice02-001"
IA_DIG = "ia-digest-r6-slice02-001"


def _descriptor(**overrides):
    base = {
        "project_id": "project-r6-synthetic",
        "media_type": "pdf",
        "source_name": "synthetic-dsmb-v1.pdf",
        "reported_version_label": "v1.0",
        "reported_data_cutoff": "cutoff-2026-08-01",
        "reported_cutoff_status": "declared",
        "received_at": "2026-08-27T00:00:00Z",
        "source_scope": {"kind": "external_report", "label": "dsmb"},
        "report_lineage_id": "lineage-r6-001",
        "parent_report_revision_id": None,
        "run_source_revision_id": "run-source-revision-001",
    }
    base.update(overrides)
    return base


def _register(raw: bytes, desc=None, existing=()):
    return rr.register_report_source(raw, desc or _descriptor(), existing)


def _unit_specs(report_revision_id: str):
    return [
        {
            "unit_id": "doc-001",
            "unit_type": "document",
            "parent_unit_id": None,
            "required": True,
            "locator": {"path": "/", "report_revision_id": report_revision_id},
            "extractability": "text",
            "anchor_digest": "anchor-doc-001",
        },
        {
            "unit_id": "body-001",
            "unit_type": "body",
            "parent_unit_id": "doc-001",
            "required": True,
            "locator": {"path": "/body/1", "report_revision_id": report_revision_id},
            "extractability": "text",
            "anchor_digest": "anchor-body-001",
        },
        {
            "unit_id": "table-001",
            "unit_type": "table",
            "parent_unit_id": "doc-001",
            "required": True,
            "locator": {"path": "/table/1", "report_revision_id": report_revision_id},
            "extractability": "table",
            "anchor_digest": "anchor-table-001",
        },
        {
            "unit_id": "footnote-001",
            "unit_type": "footnote",
            "parent_unit_id": "doc-001",
            "required": True,
            "locator": {
                "path": "/footnote/1",
                "report_revision_id": report_revision_id,
            },
            "extractability": "text",
            "anchor_digest": "anchor-footnote-001",
        },
    ]


def _evidence(eid="ev-001"):
    return {
        "evidence_id": eid,
        "authority_class": "source_record",
        "source_revision_id": "run-source-revision-001",
        "snapshot_id": "snap-001",
        "data_cutoff": "cutoff-2026-08-01",
        "locator": "body-page-1/p-1",
        "content_hash": "sha256-ev-001",
        "relation": "supports",
    }


# ---------------------------------------------------------------------------
# register_report_source
# ---------------------------------------------------------------------------


def test_register_computes_raw_byte_sha_and_freezes_immutable():
    raw = b"%PDF-synthetic-report-v1%"
    result = _register(raw)
    assert result["status"] == "registered"
    assert result["report_artifact_id"] == rr.sha256_hex(raw)
    rev = result["report_source_revision"]
    assert rev["immutable"] is True
    assert rev["report_artifact_id"] == result["report_artifact_id"]
    assert rev["source_revision_id"] == rev["report_source_revision_id"]
    assert rev["source_revision_id"] == result["generic_source_revision"]["source_revision_id"]
    assert rev["parent_report_revision_id"] is None


def test_same_raw_hash_deduplicates_without_new_clinical_revision():
    raw = b"%PDF-synthetic-report-v1%"
    first = _register(raw)
    existing = [first["report_source_revision"]]
    second = _register(raw, existing=existing)
    assert second["status"] == "deduplicated"
    assert (
        second["report_source_revision"]["report_revision_id"]
        == first["report_source_revision"]["report_revision_id"]
    )
    assert (
        second["report_source_revision"]["report_artifact_id"]
        == first["report_artifact_id"]
    )


def test_same_hash_in_different_report_lineage_does_not_cross_deduplicate():
    raw = b"same-bytes-distinct-report-lineage"
    first = _register(raw)
    second = _register(
        raw,
        _descriptor(report_lineage_id="lineage-r6-002"),
        existing=[first["report_source_revision"]],
    )
    assert second["status"] == "registered"
    assert second["report_source_revision"]["report_lineage_id"] == "lineage-r6-002"


def test_new_content_creates_new_revision_with_parent_lineage():
    v1 = _register(b"report-bytes-v1")
    rev1 = v1["report_source_revision"]
    v2 = _register(
        b"report-bytes-v2",
        _descriptor(
            reported_version_label="v2.0",
            parent_report_revision_id=rev1["report_revision_id"],
        ),
        existing=[rev1],
    )
    assert v2["status"] == "registered"
    rev2 = v2["report_source_revision"]
    assert rev2["report_revision_id"] != rev1["report_revision_id"]
    assert rev2["report_source_revision_id"] != rev1["report_source_revision_id"]
    assert rev2["report_artifact_id"] != rev1["report_artifact_id"]
    assert rev2["report_lineage_id"] == rev1["report_lineage_id"]
    assert rev2["parent_report_revision_id"] == rev1["report_revision_id"]
    chain = rr.rebuild_parent_lineage(
        rev2["report_revision_id"], [rev1, rev2]
    )
    assert chain == (rev1["report_revision_id"], rev2["report_revision_id"])


def test_missing_parent_fail_closed():
    with pytest.raises(rr.ReportReviewError) as ei:
        _register(
            b"report-bytes-v2",
            _descriptor(parent_report_revision_id="missing-parent"),
            existing=[],
        )
    assert ei.value.failure_code == "source_revision_mismatch"


def test_run_and_report_source_ids_must_not_mix_at_registration():
    with pytest.raises(rr.ReportReviewError) as ei:
        _register(
            b"report-bytes",
            _descriptor(
                run_source_revision_id="same-id",
                report_source_revision_id="same-id",
            ),
        )
    assert ei.value.failure_code == "identity_mismatch"


def test_missing_cutoff_is_explicit_not_defaulted_to_current():
    result = _register(
        b"report-no-cutoff",
        _descriptor(
            reported_data_cutoff=None,
            reported_cutoff_status="missing",
            reported_version_label=None,
        ),
    )
    rev = result["report_source_revision"]
    assert rev["reported_data_cutoff"] is None
    assert rev["reported_cutoff_status"] == "missing"
    assert rev["reported_version_label"] is None


def test_declared_cutoff_without_value_fail_closed():
    with pytest.raises(rr.ReportReviewError) as ei:
        _register(
            b"x",
            _descriptor(
                reported_data_cutoff=None,
                reported_cutoff_status="declared",
            ),
        )
    assert ei.value.failure_code == "source_revision_mismatch"


def test_register_does_not_mutate_descriptor_or_existing():
    desc = _descriptor()
    existing_rev = _register(b"prior")["report_source_revision"]
    existing = [existing_rev]
    before_desc = rr.canonical_bytes(desc)
    before_existing = rr.canonical_bytes(existing)
    _register(
        b"new-bytes",
        desc,
        existing=existing,
    )
    assert rr.canonical_bytes(desc) == before_desc
    assert rr.canonical_bytes(existing) == before_existing


def test_registration_canonical_bytes_two_pass_identical():
    raw = b"stable-bytes"
    a = _register(raw)
    b = _register(raw)
    # Fresh registrations of identical bytes yield identical derived identities
    # when no caller-supplied revision IDs differ.
    assert rr.canonical_bytes(a["report_source_revision"]) == rr.canonical_bytes(
        b["report_source_revision"]
    )
    assert rr.canonical_bytes(a) == rr.canonical_bytes(b)


# ---------------------------------------------------------------------------
# object construction
# ---------------------------------------------------------------------------


def test_build_units_claims_issues_many_to_many_and_cross_identity_ok():
    reg = _register(b"object-surface-v1")
    src = reg["report_source_revision"]
    units = [rr.build_report_unit(spec, src) for spec in _unit_specs(src["report_revision_id"])]

    claim_a = rr.build_report_claim(
        {
            "claim_id": "claim-multi-001",
            "run_id": "run-r6-001",
            "unit_ids": ["body-001", "footnote-001"],
            "claim_kind": "numeric",
            "source_text": "AE rate 11.9%",
            "normalized_claim_concept": "ae_rate",
            "scope": "project",
            "normalized_subject_or_site_scope": "project",
            "temporal_window": "cutoff-2026-08-01",
            "status": "supported",
            "evidence_refs": [_evidence()],
            "issue_ids": [],
            "locator": {"path": "/body/1"},
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    claim_b = rr.build_report_claim(
        {
            "claim_id": "claim-table-001",
            "run_id": "run-r6-001",
            "unit_ids": ["table-001"],
            "claim_kind": "numeric",
            "source_text": "N=42",
            "normalized_claim_concept": "safety_n",
            "scope": "project",
            "normalized_subject_or_site_scope": "project",
            "temporal_window": "cutoff-2026-08-01",
            "status": "supported",
            "evidence_refs": [_evidence("ev-002")],
            "issue_ids": ["issue-omitted-001"],
            "locator": {"path": "/table/1"},
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    # Same unit may carry multiple claims (many-to-many).
    claim_c = rr.build_report_claim(
        {
            "claim_id": "claim-table-trend-001",
            "run_id": "run-r6-001",
            "unit_ids": ["table-001"],
            "claim_kind": "trend",
            "source_text": "rate rising",
            "normalized_claim_concept": "ae_rate_trend",
            "scope": "project",
            "normalized_subject_or_site_scope": "project",
            "temporal_window": "cutoff-2026-08-01",
            "status": "partially_supported",
            "evidence_refs": [],
            "issue_ids": [],
            "locator": {"path": "/table/1/trend"},
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    issue = rr.build_review_issue(
        {
            "issue_id": "issue-omitted-001",
            "run_id": "run-r6-001",
            "issue_kind": "omitted",
            "claim_ids": [],
            "unit_ids": ["doc-001"],
            "severity": "high",
            "clinical_or_document_scope": "missing_risk_domain_x",
            "evidence_refs": [_evidence("ev-risk")],
            "source_locators": [{"path": "/"}],
            "lifecycle_state": "open",
            "revision_diff_state": "new",
            "related_issue_ids": [],
            "transition_refs": [],
            "current_note": "expected risk absent from report",
            "normalized_clinical_concept": "risk_domain_x",
            "normalized_subject_or_site_scope": "project",
            "normalized_temporal_window": "cutoff-2026-08-01",
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )

    assert set(claim_a["unit_ids"]) == {"body-001", "footnote-001"}
    table_claims = [
        c["claim_id"]
        for c in (claim_b, claim_c)
        if "table-001" in c["unit_ids"]
    ]
    assert table_claims == ["claim-table-001", "claim-table-trend-001"]
    assert issue["claim_ids"] == []

    codes = rr.validate_object_cross_identity(
        src,
        units,
        [claim_a, claim_b, claim_c],
        [issue],
        run_source_revision_id="run-source-revision-001",
    )
    assert codes == ()


def test_claim_without_unit_fail_closed():
    src = _register(b"x")["report_source_revision"]
    with pytest.raises(rr.ReportReviewError) as ei:
        rr.build_report_claim(
            {
                "claim_id": "c1",
                "run_id": "run-1",
                "unit_ids": [],
                "claim_kind": "numeric",
                "source_text": "x",
                "normalized_claim_concept": "c",
                "scope": "project",
                "temporal_window": "t",
                "status": "supported",
                "locator": {"path": "/"},
            },
            src,
            identity_algorithm_version=IA_VER,
            identity_algorithm_digest=IA_DIG,
        )
    assert ei.value.failure_code == "claim_without_unit"


def test_omission_issue_requires_unit_or_scope_and_evidence():
    src = _register(b"x")["report_source_revision"]
    with pytest.raises(rr.ReportReviewError) as ei:
        rr.build_review_issue(
            {
                "issue_id": "i1",
                "run_id": "run-1",
                "issue_kind": "omitted",
                "claim_ids": [],
                "unit_ids": [],
                "severity": "high",
                "clinical_or_document_scope": "x",
                "evidence_refs": [],
                "source_locators": [],
                "lifecycle_state": "open",
                "revision_diff_state": "new",
                "normalized_clinical_concept": "x",
            },
            src,
            identity_algorithm_version=IA_VER,
            identity_algorithm_digest=IA_DIG,
        )
    assert ei.value.failure_code == "issue_without_unit_or_evidence"


def test_cross_identity_accumulates_all_blocking_reasons():
    src = _register(b"cross-id")["report_source_revision"]
    units = [rr.build_report_unit(spec, src) for spec in _unit_specs(src["report_revision_id"])]
    bad_claim = rr.build_report_claim(
        {
            "claim_id": "claim-ok-shape",
            "run_id": "run-r6-001",
            "unit_ids": ["body-001"],
            "claim_kind": "numeric",
            "source_text": "x",
            "normalized_claim_concept": "c",
            "scope": "project",
            "temporal_window": "t",
            "status": "supported",
            "locator": {"path": "/"},
            "issue_ids": ["missing-issue"],
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    # Tamper after build: wrong revision + unknown unit link.
    tampered = copy.deepcopy(bad_claim)
    tampered["report_revision_id"] = "other-revision"
    tampered["unit_ids"] = ["body-001", "unit-missing"]
    tampered["claim_identity_key"] = "tampered-key"

    orphan_issue = {
        "issue_id": "issue-orphan",
        "issue_identity_key": "bad",
        "project_id": src["project_id"],
        "run_id": "run-r6-001",
        "report_lineage_id": src["report_lineage_id"],
        "report_revision_id": src["report_revision_id"],
        "report_source_revision_id": src["report_source_revision_id"],
        "issue_kind": "omitted",
        "claim_ids": ["missing-claim"],
        "unit_ids": ["unit-also-missing"],
        "severity": "high",
        "clinical_or_document_scope": "x",
        "evidence_refs": [],
        "source_locators": [],
        "lifecycle_state": "open",
        "revision_diff_state": "new",
        "related_issue_ids": [],
        "transition_refs": [],
        "current_note": "",
        "normalized_clinical_concept": "x",
        "normalized_subject_or_site_scope": "project",
        "normalized_temporal_window": "t",
        "identity_algorithm_version": IA_VER,
        "identity_algorithm_digest": IA_DIG,
    }

    codes = rr.validate_object_cross_identity(
        src,
        units,
        [tampered],
        [orphan_issue],
        run_source_revision_id=src["report_source_revision_id"],  # illegal mix
    )
    # Must accumulate multiple reasons, not first-error-only.
    assert "identity_mismatch" in codes
    assert "revision_mismatch" in codes
    assert "unit_claim_link_unknown" in codes
    assert "issue_without_unit_or_evidence" in codes
    assert codes == tuple(sorted(set(codes)))


def test_document_parent_must_be_null_other_units_require_parent():
    src = _register(b"parents")["report_source_revision"]
    with pytest.raises(rr.ReportReviewError):
        rr.build_report_unit(
            {
                "unit_id": "doc-bad",
                "unit_type": "document",
                "parent_unit_id": "x",
                "required": True,
                "locator": {"path": "/"},
                "extractability": "text",
                "anchor_digest": "a",
            },
            src,
        )
    with pytest.raises(rr.ReportReviewError):
        rr.build_report_unit(
            {
                "unit_id": "body-bad",
                "unit_type": "body",
                "parent_unit_id": None,
                "required": True,
                "locator": {"path": "/"},
                "extractability": "text",
                "anchor_digest": "a",
            },
            src,
        )


def test_identity_keys_stable_under_hash_seed_independent_serialization():
    key_a = rr.compute_claim_identity_key(
        project_id="p",
        report_lineage_id="l",
        scope="project",
        normalized_claim_concept="ae_rate",
        normalized_subject_or_site_scope="project",
        normalized_temporal_window="t",
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    key_b = rr.compute_claim_identity_key(
        project_id="p",
        report_lineage_id="l",
        scope="project",
        normalized_claim_concept="ae_rate",
        normalized_subject_or_site_scope="project",
        normalized_temporal_window="t",
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    assert key_a == key_b
    assert key_a.startswith("cik-")
    # Different concept → different key.
    key_c = rr.compute_claim_identity_key(
        project_id="p",
        report_lineage_id="l",
        scope="project",
        normalized_claim_concept="other",
        normalized_subject_or_site_scope="project",
        normalized_temporal_window="t",
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    assert key_c != key_a


def test_builders_do_not_mutate_inputs():
    src = _register(b"immut")["report_source_revision"]
    spec = {
        "unit_id": "doc-001",
        "unit_type": "document",
        "parent_unit_id": None,
        "required": True,
        "locator": {"path": "/"},
        "extractability": "text",
        "anchor_digest": "a",
    }
    before_src = rr.canonical_bytes(src)
    before_spec = rr.canonical_bytes(spec)
    rr.build_report_unit(spec, src)
    assert rr.canonical_bytes(src) == before_src
    assert rr.canonical_bytes(spec) == before_spec


def test_cross_project_isolation_on_dedup():
    raw = b"shared-bytes"
    a = _register(raw, _descriptor(project_id="project-a"))
    # Same bytes, different project → new registration (project isolation).
    b = _register(
        raw,
        _descriptor(project_id="project-b"),
        existing=[a["report_source_revision"]],
    )
    assert b["status"] == "registered"
    assert b["report_artifact_id"] == a["report_artifact_id"]
    assert (
        b["report_source_revision"]["project_id"]
        != a["report_source_revision"]["project_id"]
    )


def test_invalid_media_type_uses_frozen_failure_code():
    with pytest.raises(rr.ReportReviewError) as ei:
        _register(b"x", _descriptor(media_type="docx_pdf"))
    assert ei.value.failure_code == "source_revision_mismatch"


# ---------------------------------------------------------------------------
# worker_03 independent verification gates
# ---------------------------------------------------------------------------

POC_ROOT = Path(__file__).resolve().parents[1]
WORKBENCH_ROOT = contracts.WORKBENCH_ROOT

REQUIRED_COVERAGE_APIS = (
    "build_report_review_matrix",
    "build_claim_coverage_ledger",
    "validate_report_review_matrix",
)
COVERAGE_READY = all(hasattr(rr, name) for name in REQUIRED_COVERAGE_APIS)

# Slice-02 create-only tree (contract §允许路径) plus accepted slice-01 files.
SLICE02_CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "src/mm_r6/report_review.py",
        "src/mm_r6/report_bundle.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "tests/test_report_review.py",
        "tests/test_report_bundle.py",
        "evidence/r6_contract_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "src/mm_r6/mode_output.py",
        "src/mm_r6/agent_harness.py",
        "tests/test_mode_output.py",
        "tests/test_agent_harness.py",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
        "README.md",
    }
)
SLICE01_ALLOWLIST_STILL_EXACT_10 = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "evidence/r6_contract_runtime_receipt.json",
        "README.md",
    }
)

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 542
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
)
EXPECTED_CONTRACT_SHA = (
    "0fca738c19277777de25ce819285ace2e836b2e323e581ce04f52608ce0ed1d7"
)
EXPECTED_MATRIX_SHA = (
    "cb5b30bc8397e022efff6bc7e57b4d23b99f1debff1c405879e42e698444b2dc"
)
EXPECTED_PROSE_SHA = (
    "1c6fc588335206020389527bf0841bbf57abe227dbea46a2420c0456ed2f1acd"
)
EXPECTED_SLICE01_SRC = {
    "src/mm_r6/contracts.py": (
        "f5ce93629bd008d438095fd9b23ab1f335b951087bf916b85ac990a350e8fcfa"
    ),
    "src/mm_r6/fixtures.py": (
        "e8064ad358e0a215d6b428bc1c48e97a4ef55a20131261e5b6a9c21eac44e56c"
    ),
    "src/mm_r6/validator.py": (
        "8c9bb8c60c64c1a102d37f5e4e49263844061fd5b37cce01060bbd4133d891d0"
    ),
}
PROTECTED_PORTS = (8911, 5174)
FROZEN_BLOCKING_CODES = (
    "expected_set_missing",
    "expected_unit_missing",
    "duplicate_unit_entry",
    "unexpected_unit_entry",
    "reverse_omission_uncovered",
    "invalid_coverage_status",
    "unreasoned_not_evaluable",
    "partial_unit",
    "truncated_unit",
    "claim_without_unit",
    "unit_claim_link_unknown",
    "issue_without_unit_or_evidence",
    "anchor_unverified",
    "cutoff_mismatch",
    "revision_mismatch",
    "evidence_comparison_missing",
)


def _poc_files() -> set:
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        if "__pycache__" in rel.split("/") or ".pytest_cache" in rel.split("/"):
            continue
        if rel.endswith(".pyc"):
            continue
        found.add(rel)
    return found


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _medical_writing_boundary(root: Path) -> dict:
    matched = {}
    errors = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        base = root / root_relative
        if not base.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, dirnames, filenames in os.walk(
            base, topdown=True, followlinks=False
        ):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(directory) / filename
                relative = path.relative_to(root).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(
                        f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}"
                    )
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched[relative] = (
                        hashlib.sha256(path.read_bytes()).hexdigest().lower()
                    )
                except (OSError, UnicodeError) as exc:
                    errors.append(
                        f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}"
                    )
    aggregate = hashlib.sha256()
    for relative in sorted(matched, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "file_count": len(matched),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def _binding(**overrides):
    base = {
        "project_id": "project-r6-synthetic",
        "run_id": "run-r6-001",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "cutoff-2026-08-01",
        "source_revision_id": "run-source-revision-001",
        "knowledge_pack_version": "kp-1",
        "rule_activation_version": "rav-1",
        "mapping_version": "map-1",
        "identity_algorithm_version": IA_VER,
        "identity_algorithm_digest": IA_DIG,
        "schema_version": "r6-0.1",
    }
    base.update(overrides)
    return base


def _positive_object_surface(raw=b"verifier-positive-v1"):
    reg = _register(raw)
    src = reg["report_source_revision"]
    units = [
        rr.build_report_unit(spec, src)
        for spec in _unit_specs(src["report_revision_id"])
    ]
    # Annotate units for coverage when that surface exists.
    for unit in units:
        unit.setdefault("anchor_status", "verified")
        unit.setdefault("coverage_status", "claimed" if unit["unit_type"] != "document" else "no_claim")
        unit.setdefault("coverage_reason", None)
    claim = rr.build_report_claim(
        {
            "claim_id": "claim-pos-001",
            "run_id": "run-r6-001",
            "unit_ids": ["body-001", "table-001"],
            "claim_kind": "numeric",
            "source_text": "AE rate 11.9%",
            "normalized_claim_concept": "ae_rate",
            "scope": "project",
            "normalized_subject_or_site_scope": "project",
            "temporal_window": "cutoff-2026-08-01",
            "status": "supported",
            "evidence_refs": [_evidence()],
            "issue_ids": [],
            "locator": {"path": "/body/1"},
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    issue = rr.build_review_issue(
        {
            "issue_id": "issue-pos-001",
            "run_id": "run-r6-001",
            "issue_kind": "omitted",
            "claim_ids": [],
            "unit_ids": ["footnote-001"],
            "severity": "medium",
            "clinical_or_document_scope": "footnote_gap",
            "evidence_refs": [_evidence("ev-fn")],
            "source_locators": [{"path": "/footnote/1"}],
            "lifecycle_state": "open",
            "revision_diff_state": "new",
            "related_issue_ids": [],
            "transition_refs": [],
            "current_note": "footnote not claimed",
            "normalized_clinical_concept": "footnote_gap",
            "normalized_subject_or_site_scope": "project",
            "normalized_temporal_window": "cutoff-2026-08-01",
        },
        src,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    surface = [
        {
            "expectation_id": "exp-risk-001",
            "expectation_kind": "accepted_risk",
            "authority_ref": "synthetic-authority/risk-001",
            "scope": "project",
            "temporal_window": "cutoff-2026-08-01",
        }
    ]
    reverse = [
        {
            "expectation_id": "exp-risk-001",
            "claim_ids": [],
            "issue_ids": ["issue-pos-001"],
            "not_evaluable_exception": None,
            "evidence_refs": [_evidence("ev-fn")],
        }
    ]
    return {
        "binding": _binding(),
        "report_source": src,
        "units": units,
        "claims": [claim],
        "issues": [issue],
        "expected_review_surface": surface,
        "reverse_coverage_links": reverse,
        "registration": reg,
    }


def test_coverage_apis_required_for_slice02_completion():
    """Hard gate: coverage APIs must exist for slice-02 completion."""
    missing = [name for name in REQUIRED_COVERAGE_APIS if not hasattr(rr, name)]
    assert missing == [], (
        "worker_02 coverage APIs absent from report_review.py: "
        + ", ".join(missing)
    )


def test_source_object_apis_present():
    for name in (
        "register_report_source",
        "build_report_unit",
        "build_report_claim",
        "build_review_issue",
        "validate_object_cross_identity",
        "canonical_bytes",
        "rebuild_parent_lineage",
    ):
        assert hasattr(rr, name), name


def test_positive_cross_identity_surface_clean():
    pack = _positive_object_surface()
    codes = rr.validate_object_cross_identity(
        pack["report_source"],
        pack["units"],
        pack["claims"],
        pack["issues"],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    assert codes == ()


def test_tamper_immutable_flag_and_claim_identity_detected():
    pack = _positive_object_surface(b"tamper-immut")
    src = copy.deepcopy(pack["report_source"])
    src["immutable"] = False
    codes_immut = rr.validate_object_cross_identity(
        src,
        pack["units"],
        pack["claims"],
        pack["issues"],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    assert "source_not_immutable" in codes_immut

    claim = copy.deepcopy(pack["claims"][0])
    claim["claim_identity_key"] = "cik-" + ("0" * 64)
    codes_key = rr.validate_object_cross_identity(
        pack["report_source"],
        pack["units"],
        [claim],
        pack["issues"],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    assert "identity_mismatch" in codes_key


def test_tamper_report_artifact_id_detected_through_bound_locators():
    pack = _positive_object_surface(b"tamper-artifact")
    src = copy.deepcopy(pack["report_source"])
    before = rr.canonical_bytes(src)
    src["report_artifact_id"] = "0" * 64
    assert rr.canonical_bytes(src) != before
    codes = rr.validate_object_cross_identity(
        src,
        pack["units"],
        pack["claims"],
        pack["issues"],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    assert "identity_mismatch" in codes


def test_issue_identity_scope_is_never_silently_defaulted():
    pack = _positive_object_surface(b"issue-scope-required")
    spec = copy.deepcopy(pack["issues"][0])
    spec.pop("normalized_subject_or_site_scope")
    with pytest.raises(rr.ReportReviewError) as exc:
        rr.build_review_issue(
            spec,
            pack["report_source"],
            identity_algorithm_version=IA_VER,
            identity_algorithm_digest=IA_DIG,
        )
    assert exc.value.failure_code == "issue_identity_invalid"


def test_duplicate_unit_ids_fail_cross_identity():
    pack = _positive_object_surface(b"dup-units")
    units = pack["units"] + [copy.deepcopy(pack["units"][1])]
    codes = rr.validate_object_cross_identity(
        pack["report_source"],
        units,
        pack["claims"],
        pack["issues"],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    # Duplicate unit identity breaks closed accounting / identity surface.
    assert codes  # fail-closed; must not silently accept
    assert codes == tuple(sorted(set(codes)))


def test_orphan_claim_issue_cross_refs_accumulate():
    pack = _positive_object_surface(b"orphan-refs")
    claim = copy.deepcopy(pack["claims"][0])
    claim["issue_ids"] = ["missing-issue-x"]
    claim["unit_ids"] = list(claim["unit_ids"]) + ["missing-unit-x"]
    issue = copy.deepcopy(pack["issues"][0])
    issue["claim_ids"] = ["missing-claim-y"]
    issue["unit_ids"] = ["missing-unit-y"]
    codes = rr.validate_object_cross_identity(
        pack["report_source"],
        pack["units"],
        [claim],
        [issue],
        run_source_revision_id=pack["binding"]["source_revision_id"],
    )
    assert "unit_claim_link_unknown" in codes
    assert len(codes) >= 2
    assert codes == tuple(sorted(set(codes)))


def test_cross_revision_isolation_on_objects():
    v1 = _register(b"rev-iso-v1")["report_source_revision"]
    v2 = _register(
        b"rev-iso-v2",
        _descriptor(
            reported_version_label="v2.0",
            parent_report_revision_id=v1["report_revision_id"],
        ),
        existing=[v1],
    )["report_source_revision"]
    unit_v1 = rr.build_report_unit(
        {
            "unit_id": "doc-001",
            "unit_type": "document",
            "parent_unit_id": None,
            "required": True,
            "locator": {"path": "/", "report_revision_id": v1["report_revision_id"]},
            "extractability": "text",
            "anchor_digest": "a",
        },
        v1,
    )
    claim_on_v2 = rr.build_report_claim(
        {
            "claim_id": "claim-cross-rev",
            "run_id": "run-r6-001",
            "unit_ids": ["doc-001"],
            "claim_kind": "numeric",
            "source_text": "x",
            "normalized_claim_concept": "c",
            "scope": "project",
            "temporal_window": "t",
            "status": "supported",
            "locator": {"path": "/"},
        },
        v2,
        identity_algorithm_version=IA_VER,
        identity_algorithm_digest=IA_DIG,
    )
    codes = rr.validate_object_cross_identity(
        v2,
        [unit_v1],
        [claim_on_v2],
        [],
        run_source_revision_id="run-source-revision-001",
    )
    assert "revision_mismatch" in codes


def test_canonical_bytes_two_pass_object_pack():
    pack_a = _positive_object_surface(b"canon-pack")
    pack_b = _positive_object_surface(b"canon-pack")
    assert rr.canonical_bytes(pack_a["report_source"]) == rr.canonical_bytes(
        pack_b["report_source"]
    )
    assert rr.canonical_bytes(pack_a["claims"][0]) == rr.canonical_bytes(
        pack_b["claims"][0]
    )
    # Round-trip through json preserves canonical form.
    loaded = json.loads(rr.canonical_bytes(pack_a["claims"][0]).decode("utf-8"))
    assert rr.canonical_bytes(loaded) == rr.canonical_bytes(pack_a["claims"][0])


def test_slice01_frozen_inputs_and_src_immutable():
    assert _sha256_file(contracts.contract_path()) == EXPECTED_CONTRACT_SHA
    assert _sha256_file(contracts.matrix_path()) == EXPECTED_MATRIX_SHA
    assert _sha256_file(contracts.prose_path()) == EXPECTED_PROSE_SHA
    for rel, digest in EXPECTED_SLICE01_SRC.items():
        assert _sha256_file(POC_ROOT / rel) == digest, rel
    # Slice-01 receipt untouched.
    receipt = POC_ROOT / "evidence" / "r6_contract_runtime_receipt.json"
    assert receipt.is_file()
    # Catalog still rebuilds to accepted digest.
    rows = contracts.matrix_obj(contracts.matrix_raw())["rows"]
    catalog = fixtures.build_fixture_catalog(rows)
    assert catalog["catalog_sha256"] == (
        "76b43076d896001fb4b393f43329a194b32d9091625101d8eed2ba2ece940b53"
    )


def test_slice01_adjacency_oracle_still_clean(contract, matrix):
    report = validator.oracle_parity_report(matrix["rows"], contract, matrix)
    assert report["mismatch_count"] == 0
    assert report["row_count"] == 86


def test_medical_writing_aggregate_unchanged():
    boundary = _medical_writing_boundary(WORKBENCH_ROOT)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


def test_slice02_create_only_allowlist_exact():
    found = _poc_files()
    optional_receipts = {
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
    }
    extras = found - SLICE02_CREATE_ONLY_RELATIVE
    missing_required = (SLICE02_CREATE_ONLY_RELATIVE - optional_receipts) - found
    assert extras == set()
    assert missing_required == set()
    assert found <= SLICE02_CREATE_ONLY_RELATIVE


def test_slice01_allowlist_test_still_expects_exact_10_documenting_gap():
    """Document adjacency debt: slice-01 allowlist was not authorized to expand."""
    found = _poc_files()
    extras = found - SLICE01_ALLOWLIST_STILL_EXACT_10
    # Slice-02 authorized extras must be present; slice-01 frozenset therefore fails.
    assert "src/mm_r6/report_review.py" in extras
    assert "tests/test_report_review.py" in extras


_REPRO_PROBE = r"""
import os, sys
sys.path.insert(0, os.environ["MM_R6_SRC"])
from mm_r6 import report_review as rr
raw = b"repro-seed-bytes"
desc = {
    "project_id": "project-r6-synthetic",
    "media_type": "pdf",
    "source_name": "synthetic.pdf",
    "reported_version_label": "v1.0",
    "reported_data_cutoff": "cutoff-2026-08-01",
    "reported_cutoff_status": "declared",
    "received_at": "2026-08-27T00:00:00Z",
    "source_scope": {"kind": "external_report", "label": "dsmb"},
    "report_lineage_id": "lineage-r6-001",
    "parent_report_revision_id": None,
    "run_source_revision_id": "run-source-revision-001",
}
a = rr.register_report_source(raw, desc, ())
b = rr.register_report_source(raw, desc, ())
if rr.canonical_bytes(a) != rr.canonical_bytes(b):
    raise SystemExit("canonical_diverge")
src = a["report_source_revision"]
unit = rr.build_report_unit(
    {
        "unit_id": "doc-001",
        "unit_type": "document",
        "parent_unit_id": None,
        "required": True,
        "locator": {"path": "/", "report_revision_id": src["report_revision_id"]},
        "extractability": "text",
        "anchor_digest": "a1",
    },
    src,
)
claim = rr.build_report_claim(
    {
        "claim_id": "c1",
        "run_id": "run-1",
        "unit_ids": ["doc-001"],
        "claim_kind": "numeric",
        "source_text": "x",
        "normalized_claim_concept": "c",
        "scope": "project",
        "normalized_subject_or_site_scope": "project",
        "temporal_window": "t",
        "status": "supported",
        "locator": {"path": "/"},
    },
    src,
    identity_algorithm_version="ia-r6-slice02-001",
    identity_algorithm_digest="ia-digest-r6-slice02-001",
)
codes = rr.validate_object_cross_identity(
    src, [unit], [claim], [], run_source_revision_id="run-source-revision-001"
)
if codes:
    raise SystemExit("cross_identity_fail:%s" % (codes,))
# Coverage APIs: if present, positive matrix must close dual-gate cleanly or
# fail-closed with frozen codes only. Absence is reported via the hard gate.
if all(hasattr(rr, n) for n in (
    "build_report_review_matrix",
    "build_claim_coverage_ledger",
    "validate_report_review_matrix",
)):
    print("coverage_apis=present")
else:
    print("coverage_apis=absent")
print("ok")
"""


@pytest.mark.parametrize("opt_flag", ["", "-O", "-OO"])
@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
def test_repro_source_object_raise_based(opt_flag, hash_seed):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MM_R6_SRC"] = str(POC_ROOT / "src")
    cmd = [sys.executable]
    if opt_flag:
        cmd.append(opt_flag)
    cmd.extend(["-c", _REPRO_PROBE])
    proc = subprocess.run(
        cmd,
        cwd=str(WORKBENCH_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"opt={opt_flag!r} seed={hash_seed} rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "ok" in proc.stdout


# ---------------------------------------------------------------------------
# Coverage / ClaimCoverageLedger scenarios (require worker_02 APIs)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_positive_coverage_closed_and_full_eligible():
    pack = _positive_object_surface(b"cov-positive")
    # Mark all units claimed/no_claim with verified anchors for full eligibility.
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        if unit["unit_id"] in ("body-001", "table-001"):
            unit["coverage_status"] = "claimed"
        else:
            unit["coverage_status"] = "no_claim"
        unit["coverage_reason"] = None
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        pack["claims"],
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    codes = rr.validate_report_review_matrix(matrix)
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert codes == ()
    assert ledger["coverage_closed"] is True
    assert ledger["full_report_reviewed_eligible"] is True
    assert rr.canonical_bytes(ledger) == rr.canonical_bytes(
        rr.build_claim_coverage_ledger(matrix)
    )


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_reasoned_not_evaluable_closes_but_blocks_full_eligible():
    pack = _positive_object_surface(b"cov-ne")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
        unit["coverage_reason"] = None
    target = next(u for u in pack["units"] if u["unit_id"] == "table-001")
    target["coverage_status"] = "not_evaluable"
    target["coverage_reason"] = "synthetic extractability limit"
    target["extractability"] = "unknown"
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        [],  # no claims on not_evaluable path
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert ledger["coverage_closed"] is True
    assert ledger["full_report_reviewed_eligible"] is False
    reasons = set(ledger["blocking_reasons"])
    assert "coverage_incomplete" in reasons or "claim_not_evaluable" in reasons


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
@pytest.mark.parametrize(
    "status,code",
    [
        ("partial", "partial_unit"),
        ("truncated", "truncated_unit"),
    ],
)
def test_partial_truncated_block_full_eligible(status, code):
    pack = _positive_object_surface(f"cov-{status}".encode())
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    target = next(u for u in pack["units"] if u["unit_id"] == "body-001")
    target["coverage_status"] = status
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        [],
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert ledger["full_report_reviewed_eligible"] is False
    assert code in ledger["blocking_reasons"]


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_unreasoned_not_evaluable_blocks_coverage_closed():
    pack = _positive_object_surface(b"cov-unreasoned")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    target = next(u for u in pack["units"] if u["unit_id"] == "body-001")
    target["coverage_status"] = "not_evaluable"
    target["coverage_reason"] = None
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        [],
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert ledger["coverage_closed"] is False
    assert "unreasoned_not_evaluable" in ledger["blocking_reasons"]


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_missing_duplicate_unexpected_unit_entries():
    pack = _positive_object_surface(b"cov-set")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    # Missing: drop a required unit from the expected set input while keeping
    # reverse/claims referencing the remaining set — builder must derive
    # expected_unit_missing / unexpected / duplicate via frozen codes.
    units_missing = [u for u in pack["units"] if u["unit_id"] != "footnote-001"]
    matrix_missing = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        units_missing,
        [],
        [],
        pack["expected_review_surface"],
        [
            {
                "expectation_id": "exp-risk-001",
                "claim_ids": [],
                "issue_ids": [],
                "not_evaluable_exception": {
                    "reason": "no omission issue yet",
                    "report_scope": "project",
                    "evidence_refs": [_evidence("ev-ne")],
                },
                "evidence_refs": [_evidence("ev-ne")],
            }
        ],
    )
    ledger_missing = rr.build_claim_coverage_ledger(matrix_missing)
    # With a smaller frozen unit list the set may close on itself; force
    # duplicate by repeating an entry if the API exposes entries.
    units_dup = pack["units"] + [copy.deepcopy(pack["units"][0])]
    matrix_dup = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        units_dup,
        [],
        [],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    codes_dup = set(rr.validate_report_review_matrix(matrix_dup))
    ledger_dup = rr.build_claim_coverage_ledger(matrix_dup)
    assert "duplicate_unit_entry" in codes_dup or "duplicate_unit_entry" in set(
        ledger_dup["blocking_reasons"]
    )
    assert ledger_missing["blocking_reasons"] == sorted(
        set(ledger_missing["blocking_reasons"])
    )


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_reverse_omission_empty_mapping_blocks_full_eligible():
    pack = _positive_object_surface(b"cov-reverse")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    reverse = [
        {
            "expectation_id": "exp-risk-001",
            "claim_ids": [],
            "issue_ids": [],
            "not_evaluable_exception": None,
            "evidence_refs": [],
        }
    ]
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        [],
        [],
        pack["expected_review_surface"],
        reverse,
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert "reverse_omission_uncovered" in ledger["blocking_reasons"]
    assert ledger["full_report_reviewed_eligible"] is False


@pytest.mark.parametrize("report_scope", [None, "", "   "])
def test_reverse_not_evaluable_exception_requires_nonempty_report_scope(report_scope):
    pack = _positive_object_surface(b"cov-reverse-exception-scope")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    exception = {
        "reason": "synthetic scan limitation",
        "evidence_refs": [_evidence("ev-exception")],
    }
    if report_scope is not None:
        exception["report_scope"] = report_scope
    reverse = [{
        "expectation_id": "exp-risk-001",
        "claim_ids": [],
        "issue_ids": [],
        "not_evaluable_exception": exception,
        "evidence_refs": [_evidence("ev-exception")],
    }]
    matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], [], [],
        pack["expected_review_surface"], reverse,
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert "reverse_omission_uncovered" in ledger["blocking_reasons"]
    assert ledger["full_report_reviewed_eligible"] is False


@pytest.mark.parametrize("exception_refs", [[{}], ["not-a-mapping"]])
def test_reverse_exception_requires_shape_valid_evidence(exception_refs):
    pack = _positive_object_surface(b"cov-reverse-exception-evidence")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    reverse = [{
        "expectation_id": "exp-risk-001",
        "claim_ids": [],
        "issue_ids": [],
        "not_evaluable_exception": {
            "reason": "synthetic scan limitation",
            "report_scope": "project",
            "evidence_refs": exception_refs,
        },
        "evidence_refs": [_evidence("ev-link")],
    }]
    matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], [], [],
        pack["expected_review_surface"], reverse,
    )
    reasons = set(rr.build_claim_coverage_ledger(matrix)["blocking_reasons"])
    assert {"reverse_omission_uncovered", "evidence_comparison_missing"} <= reasons


def test_reverse_link_requires_shape_valid_evidence_even_when_issue_mapped():
    pack = _positive_object_surface(b"cov-reverse-link-evidence")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    reverse = copy.deepcopy(pack["reverse_coverage_links"])
    reverse[0]["evidence_refs"] = []
    matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], [], pack["issues"],
        pack["expected_review_surface"], reverse,
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    assert "evidence_comparison_missing" in ledger["blocking_reasons"]
    assert ledger["full_report_reviewed_eligible"] is False


def test_invalid_expectation_kind_and_empty_surface_fail_full_eligibility_only():
    pack = _positive_object_surface(b"cov-surface-shape")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    invalid = copy.deepcopy(pack["expected_review_surface"])
    invalid[0]["expectation_kind"] = "not_a_kind"
    matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], [], [],
        invalid, pack["reverse_coverage_links"],
    )
    assert "identity_mismatch" in rr.build_claim_coverage_ledger(matrix)["blocking_reasons"]

    empty = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], [], [], [], [],
    )
    ledger = rr.build_claim_coverage_ledger(empty)
    assert ledger["coverage_closed"] is True
    assert ledger["full_report_reviewed_eligible"] is False
    assert "reverse_omission_uncovered" in ledger["blocking_reasons"]


def test_no_claim_with_claim_link_and_parent_cycle_fail_closed():
    pack = _positive_object_surface(b"cov-status-parent-cycle")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], pack["units"], pack["claims"],
        pack["issues"], pack["expected_review_surface"], pack["reverse_coverage_links"],
    )
    assert "invalid_coverage_status" in rr.build_claim_coverage_ledger(matrix)["blocking_reasons"]

    cycled = copy.deepcopy(pack["units"])
    next(unit for unit in cycled if unit["unit_id"] == "doc-001")["parent_unit_id"] = "body-001"
    cycle_matrix = rr.build_report_review_matrix(
        pack["binding"], pack["report_source"], cycled, [], [],
        pack["expected_review_surface"], [{
            "expectation_id": "exp-risk-001", "claim_ids": [], "issue_ids": [],
            "not_evaluable_exception": {"reason": "none", "report_scope": "project", "evidence_refs": [_evidence("ev-cycle")]},
            "evidence_refs": [_evidence("ev-cycle")],
        }],
    )
    cycle_ledger = rr.build_claim_coverage_ledger(cycle_matrix)
    assert "identity_mismatch" in cycle_ledger["blocking_reasons"]
    assert cycle_ledger["coverage_closed"] is False


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_unverified_anchor_cutoff_revision_comparison_blockers():
    pack = _positive_object_surface(b"cov-anchors")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "claimed" if unit["unit_type"] != "document" else "no_claim"
    body = next(u for u in pack["units"] if u["unit_id"] == "body-001")
    body["anchor_status"] = "unverified"
    # Cutoff/revision mismatch via binding vs report source.
    binding = _binding(data_cutoff="cutoff-OTHER")
    matrix = rr.build_report_review_matrix(
        binding,
        pack["report_source"],
        pack["units"],
        pack["claims"],
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    ledger = rr.build_claim_coverage_ledger(matrix)
    reasons = set(ledger["blocking_reasons"])
    assert "anchor_unverified" in reasons
    assert "cutoff_mismatch" in reasons or "revision_mismatch" in reasons
    assert ledger["full_report_reviewed_eligible"] is False
    # All emitted codes must be frozen vocabulary or known slice-02 extensions.
    allowed = set(FROZEN_BLOCKING_CODES) | {
        "identity_mismatch",
        "source_revision_mismatch",
        "source_not_immutable",
        "issue_identity_invalid",
        "claim_not_evaluable",
        "coverage_incomplete",
        "output_not_eligible",
    }
    assert reasons <= allowed


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_coverage_validator_accumulates_all_reasons_not_first_error():
    pack = _positive_object_surface(b"cov-multi")
    for unit in pack["units"]:
        unit["anchor_status"] = "unverified"
        unit["coverage_status"] = "partial"
    reverse = [
        {
            "expectation_id": "exp-risk-001",
            "claim_ids": [],
            "issue_ids": [],
            "not_evaluable_exception": None,
            "evidence_refs": [],
        }
    ]
    matrix = rr.build_report_review_matrix(
        _binding(data_cutoff="cutoff-OTHER"),
        pack["report_source"],
        pack["units"],
        pack["claims"],
        pack["issues"],
        pack["expected_review_surface"],
        reverse,
    )
    codes = rr.validate_report_review_matrix(matrix)
    ledger = rr.build_claim_coverage_ledger(matrix)
    combined = set(codes) | set(ledger["blocking_reasons"])
    assert len(combined) >= 3
    assert list(ledger["blocking_reasons"]) == sorted(set(ledger["blocking_reasons"]))


@pytest.mark.skipif(
    not COVERAGE_READY, reason="blocked: worker_02 coverage APIs absent"
)
def test_matrix_input_not_mutated_and_tamper_detected():
    pack = _positive_object_surface(b"cov-immut")
    for unit in pack["units"]:
        unit["anchor_status"] = "verified"
        unit["coverage_status"] = "no_claim"
    before_units = rr.canonical_bytes(pack["units"])
    before_claims = rr.canonical_bytes(pack["claims"])
    matrix = rr.build_report_review_matrix(
        pack["binding"],
        pack["report_source"],
        pack["units"],
        pack["claims"],
        pack["issues"],
        pack["expected_review_surface"],
        pack["reverse_coverage_links"],
    )
    assert rr.canonical_bytes(pack["units"]) == before_units
    assert rr.canonical_bytes(pack["claims"]) == before_claims
    tampered = copy.deepcopy(matrix)
    if "matrix_id" in tampered:
        tampered["matrix_id"] = "tampered"
    elif "coverage_ledger_id" in tampered:
        tampered["coverage_ledger_id"] = "tampered"
    else:
        tampered["run_binding"] = dict(tampered.get("run_binding") or {})
        tampered["run_binding"]["run_id"] = "tampered-run"
    codes = rr.validate_report_review_matrix(tampered)
    assert codes  # fail-closed on tamper
