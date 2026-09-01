"""Shared pytest fixtures for the R3 POC test suite (worker_01-owned, R3-A).

All tests run only inside the R3 POC root; runtime artifacts go to pytest
tmp dirs.  No real-project paths, credentials, or network are permitted.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from mm_r3.fixtures import (  # noqa: E402
    make_classification,
    make_ib_revision,
    make_knowledge_pack,
    make_listing_revision,
    make_protocol_revision,
    make_report_revision,
    make_three_heterogeneous_listing_sources,
)
from mm_r3.knowledge import (  # noqa: E402
    ClaimStatus,
    SourceClassification,
    SourceRevision,
    StudyKnowledgePack,
)

LOCAL_TEST_USER = "local_test_user"


@pytest.fixture
def protocol_source() -> SourceRevision:
    return make_protocol_revision()


@pytest.fixture
def ib_source() -> SourceRevision:
    return make_ib_revision()


@pytest.fixture
def listing_source() -> SourceRevision:
    return make_listing_revision()


@pytest.fixture
def report_source() -> SourceRevision:
    return make_report_revision()


@pytest.fixture
def protocol_classification(protocol_source) -> SourceClassification:
    return make_classification(protocol_source)


@pytest.fixture
def three_heterogeneous_sources():
    """Three listing sources with deliberately different shapes."""
    return make_three_heterogeneous_listing_sources()


@pytest.fixture
def knowledge_pack(protocol_source, ib_source) -> StudyKnowledgePack:
    return make_knowledge_pack(
        source_revisions=[protocol_source, ib_source],
        general_layer={"population": "adult patients"},
        drug_layer={"mechanism": "JAK inhibitor (synthetic)"},
        project_layer={"primary_endpoint": "response rate"},
        rules_layer={"activated_rule_count": 0},
        claim_scope=("ae", "dosing", "endpoint"),
    )
