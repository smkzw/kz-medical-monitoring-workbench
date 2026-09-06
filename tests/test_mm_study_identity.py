"""Study identity must not accept neighbouring trials by prefix."""

import pytest

from packages.medical_monitoring.admission.pipeline import (
    _project_identifiers,
    _project_identity_assessment,
)


@pytest.mark.parametrize("observed", ["TRIAL-010", "TRIAL-0", "T", "TRIAL-01B", "TRIAL-01[OTHER]"])
def test_distinct_or_partial_study_ids_are_not_matches(observed):
    assert _project_identity_assessment(["TRIAL-01"], [observed])["status"] == "conflict"


@pytest.mark.parametrize("observed", ["TRIAL-01", "trial_01", "TRIAL-01[PROD]", "TRIAL-01 [UAT]"])
def test_complete_id_with_explicit_export_annotation_matches(observed):
    # Exercise extraction as well as comparison: the extracted identifier
    # must not lose the suffix boundary before normalization handles it.
    values = _project_identifiers(["STUDYID"], [{"STUDYID": observed}])
    result = _project_identity_assessment(["TRIAL-01"], values)
    assert result["status"] == "matched"
    assert result["schema_version"] == "mm-admission-project-identity-v2"


def test_any_foreign_study_in_a_mixed_export_blocks_match():
    assert _project_identity_assessment(
        ["TRIAL-01"], ["TRIAL-01", "TRIAL-010"]
    )["status"] == "conflict"


def test_absent_identity_is_unknown_not_matching():
    assert _project_identity_assessment(["TRIAL-01"], [])["status"] == "not_observed"
    assert _project_identity_assessment([], ["TRIAL-01"])["status"] == "not_configured"
