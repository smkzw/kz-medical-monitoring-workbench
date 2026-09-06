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


def test_boolean_and_numeric_constraints_are_not_coerced_to_agreement():
    a, b = verdict(), verdict()
    a['value_constraints'] = {'value': True}
    b['value_constraints'] = {'value': 1}
    assert not compare_mapping_dependencies(a, b)['dependencies_agreed']


def test_new_reconciliation_policy_requires_fresh_dependency_declarations():
    from packages.medical_monitoring.admission.mapping_reconciliation import reconcile_mapping_cohorts
    from packages.medical_monitoring.admission.mapping_comparison import DEPENDENCY_COMPARISON_VERSION
    a = {**verdict(), 'domain': 'M', 'source_field': 'VALUE', 'evidence_ids': ['left']}
    b = {**verdict(), 'domain': 'M', 'source_field': 'VALUE', 'evidence_ids': ['right']}
    b['related_fields'] = ['OTHER_NOTE']
    options = dict(profile_fields=[{'domain': 'M', 'field': 'VALUE'}], primary_mappings=[a], verifier_mappings=[b],
                   primary_evidence_ids=['left'], verifier_evidence_ids=['right'])
    assert reconcile_mapping_cohorts(**options)['auto_pass'] is False
    report = reconcile_mapping_cohorts(**options, comparison_policy_version=DEPENDENCY_COMPARISON_VERSION)
    assert report['auto_pass'] is True
    assert report['fields'][0]['dependency_comparison']['annotation_differences'] == ['related_fields']
    del a['dependency_fields']
    report = reconcile_mapping_cohorts(**options, comparison_policy_version=DEPENDENCY_COMPARISON_VERSION)
    assert report['state'] == 'blocked' and not report['auto_pass']


def test_new_draft_fields_preserve_both_notes_without_changing_legacy_serialization():
    from services.api.app.monitoring_mapping_draft_repository import MonitoringMappingField
    data = {'domain': 'M', 'source_field': 'VALUE', 'recommended_role': 'measurement.value',
            'field_kind': 'source_collected', 'confidence': .9, 'uncertainty': '说明',
            'user_action': '查看来源', 'evidence_ids': ['evidence-one']}
    old = MonitoringMappingField.model_validate(data).model_dump(mode='json')
    assert 'dependency_fields' not in old and 'comparison_annotations' not in old
    new = MonitoringMappingField.model_validate({**data, 'dependency_fields': [],
            'comparison_annotations': {'left_annotations': {'note': 'one'}, 'right_annotations': {'note': 'two'}}})
    assert MonitoringMappingField.model_validate(new.model_dump(mode='json')) == new
    assert new.model_dump(mode='json')['dependency_fields'] == []


def test_dependency_prompt_and_receipt_namespace_do_not_reuse_tool_v1():
    from packages.medical_monitoring.admission.mapping_pipeline import AdmissionMappingPipeline
    from packages.medical_monitoring.admission.mapping_confirmation import _adjudication_reconciliation_sha256
    old = AdmissionMappingPipeline(adjudication_tool_reads=True)
    new = AdmissionMappingPipeline(adjudication_tool_reads=True, explicit_mapping_dependencies=True)
    assert old.adjudication_prompt_versions.isdisjoint(new.adjudication_prompt_versions)
    assert old.adjudication_comparison_policy != new.adjudication_comparison_policy
    assert _adjudication_reconciliation_sha256({}, prompt_versions=old.adjudication_prompt_versions) != _adjudication_reconciliation_sha256({}, prompt_versions=new.adjudication_prompt_versions)
    with pytest.raises(ValueError):
        AdmissionMappingPipeline(explicit_mapping_dependencies=True)
