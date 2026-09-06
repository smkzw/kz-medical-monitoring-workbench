from copy import deepcopy

import pytest

from packages.medical_monitoring.admission.mapping_comparison import compare_mapping_dependencies


def verdict():
    return {"recommended_role": "measurement.value", "field_kind": "source_collected",
            "dependency_fields": [{"domain": "M", "source_field": "UNIT"}],
            "related_fields": ["NOTE"], "object_identity_evidence_fields": ["IDENTITY"],
            "standards_reference": {"reference_only": True, "reference_name": "reference",
                                    "reference_concept": "concept", "uncertainty": "note"}}


def test_explanations_are_preserved_symmetrically_without_interpreting_them():
    a, b = verdict(), verdict()
    b['related_fields'] = ['COMMENT']
    b['standards_reference']['uncertainty'] = 'different note'
    before = deepcopy((a, b))
    report = compare_mapping_dependencies(a, b)
    reverse = compare_mapping_dependencies(b, a)
    assert report['dependencies_agreed'] and not report['facts_generated']
    assert report['left_annotations'] == reverse['right_annotations']
    assert report['right_annotations'] == reverse['left_annotations']
    assert (a, b) == before


@pytest.mark.parametrize('key,value', [
    ('dependency_fields', []), ('object_identity_evidence_fields', ['OTHER']),
    ('recommended_role', 'measurement.coded_value'), ('field_kind', 'derived'),
    ('dose_semantics', 'planned'), ('object_identity', 'placebo'),
    ('derivation_lineage', {'operation': 'sum'}), ('value_constraints', {'unit': 'mg'}),
    ('validated_treatment_identity_binding', {'join_keys': ['OTHER']}),
    ('quality_gate_actions', ['unresolved']), ('future_semantic_key', 'unknown'),
])
def test_protected_and_unknown_semantics_never_become_annotations(key, value):
    a, b = verdict(), verdict()
    b[key] = value
    assert not compare_mapping_dependencies(a, b)['dependencies_agreed']


@pytest.mark.parametrize('key', ['ctcae_version', 'grading_definition_version', 'date_precision', 'future_key'])
def test_structured_standard_constraints_still_block(key):
    a, b = verdict(), verdict()
    a['standards_reference'][key] = 'one'
    b['standards_reference'][key] = 'two'
    assert not compare_mapping_dependencies(a, b)['dependencies_agreed']


def test_legacy_or_invalid_dependencies_cannot_silently_enter_new_policy():
    for invalid in (None, 'UNIT', [{'domain': 'M'}], [{'domain': 'M', 'source_field': 'UNIT'}] * 2):
        a = verdict()
        a['dependency_fields'] = invalid
        with pytest.raises(ValueError):
            compare_mapping_dependencies(a, verdict())
    a = verdict()
    del a['dependency_fields']
    with pytest.raises(ValueError):
        compare_mapping_dependencies(a, verdict())


def test_reference_without_explicit_reference_only_marker_remains_strict():
    a, b = verdict(), verdict()
    del a['standards_reference']['reference_only']
    del b['standards_reference']['reference_only']
    b['standards_reference']['uncertainty'] = 'different'
    assert not compare_mapping_dependencies(a, b)['dependencies_agreed']
