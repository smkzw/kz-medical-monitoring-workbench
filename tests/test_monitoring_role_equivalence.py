from copy import deepcopy
import pytest
from packages.medical_monitoring.admission.role_equivalence import (
    DIMENSIONS, option_identity, bind_role_declaration, agreed_role_representation,
)


def inputs(roles=('reading.code', 'reading.category')):
    options=[]
    for role in roles:
        value={'semantic_verdict':{'recommended_role':role,'field_kind':'source_collected'}}
        options.append({**value,'option_id':option_identity('X','VALUE',value)})
    declaration={'judgment':'equivalent','option_ids':[o['option_id'] for o in options],
        'dimensions':{axis:{'relation':'equivalent','evidence_ids':['ev-a'],'rationale':'Synthetic source comparison.'} for axis in DIMENSIONS},
        'counterevidence_summary':'Synthetic alternatives were examined; no distinction supported in this fixture.'}
    return options,declaration


def bind(declaration, options):
    return bind_role_declaration(declaration,domain='X',source_field='VALUE',options=options,evidence_ids=['ev-a'],source_scope_sha256='a'*64)


def test_declarations_are_symmetric_scoped_and_do_not_rewrite_models():
    options,declaration=inputs();before=deepcopy(declaration)
    a=bind(declaration,options)
    b=bind(declaration,list(reversed(options)))
    b['dimensions']['object']['rationale']='A separately authored explanation.'
    result=agreed_role_representation(a,b,left_role='reading.code',right_role='reading.category')
    reverse=agreed_role_representation(b,a,left_role='reading.category',right_role='reading.code')
    assert result['canonical_role']==reverse['canonical_role']=='reading.category'
    assert result['left_declaration'] != result['right_declaration']
    assert declaration==before
    assert result['clinical_acceptance'] is False


@pytest.mark.parametrize('mutate',[
    lambda d:d.update(option_ids=['wrong','wrong']),
    lambda d:d.update(bound_options=[]),
    lambda d:d['dimensions'].pop('object'),
    lambda d:d['dimensions']['object'].update(relation='insufficient'),
    lambda d:d['dimensions']['object'].update(evidence_ids=[]),
    lambda d:d['dimensions']['object'].update(evidence_ids=['not-cited']),
    lambda d:d.update(counterevidence_summary=''),
])
def test_invalid_or_unsupported_model_certificate_is_rejected(mutate):
    options,declaration=inputs();mutate(declaration)
    with pytest.raises(ValueError):bind(declaration,options)


def test_unknown_role_cannot_be_promoted_by_dual_equivalence():
    options,declaration=inputs(('unmapped','reading.code'))
    with pytest.raises(ValueError,match='cannot_promote'):bind(declaration,options)


def test_a_distinct_or_incomplete_view_does_not_become_equivalence():
    options,declaration=inputs();a=bind(declaration,options)
    for status in ('distinct','insufficient'):
        other=deepcopy(declaration);other['judgment']=status
        other['dimensions']['object']['relation']=status
        b=bind(other,options)
        assert agreed_role_representation(a,b,left_role='reading.code',right_role='reading.category') is None
    b=deepcopy(a);b['source_field']='OTHER'
    assert agreed_role_representation(a,b,left_role='reading.code',right_role='reading.category') is None
    assert agreed_role_representation(a,a,left_role='invented-role',right_role='reading.category') is None


def test_certificate_cannot_hide_non_role_hard_differences():
    from packages.medical_monitoring.admission.role_equivalence import compare_role_equivalence
    options,declaration=inputs();certificate=bind(declaration,options)
    a={'recommended_role':'reading.code','dependency_fields':[],'field_kind':'source_collected','role_equivalence':certificate}
    b={**deepcopy(a),'recommended_role':'reading.category'}
    result=compare_role_equivalence(a,b,domain='X',source_field='VALUE')
    assert result['dependencies_agreed'] and result['canonical_role']=='reading.category'
    for key,value in [('dependency_fields',[{'domain':'X','source_field':'UNIT'}]),
                      ('object_identity','other_object'),('standards_reference',{'version':'changed'}),
                      ('value_constraints',{'unit':'different'}),('dose_semantics','changed'),
                      ('unknown_future_contract',True)]:
        changed={**deepcopy(b),key:value}
        result=compare_role_equivalence(a,changed,domain='X',source_field='VALUE')
        assert not result['dependencies_agreed']
        assert 'canonical_role' not in result
    no_proof=deepcopy(b);del no_proof['role_equivalence']
    assert not compare_role_equivalence(a,no_proof,domain='X',source_field='VALUE')['dependencies_agreed']


def test_role_certificate_namespace_is_isolated_from_visual_only_adjudication():
    from packages.medical_monitoring.admission.mapping_pipeline import AdmissionMappingPipeline, _anonymous_review_rows
    old=AdmissionMappingPipeline(adjudication_tool_reads=True,explicit_mapping_dependencies=True,visual_tool_reads=True)
    new=AdmissionMappingPipeline(adjudication_tool_reads=True,explicit_mapping_dependencies=True,visual_tool_reads=True,role_equivalence=True)
    assert old.adjudication_prompt_versions.isdisjoint(new.adjudication_prompt_versions)
    assert old.adjudication_comparison_policy!=new.adjudication_comparison_policy
    row={'domain':'X','source_field':'VALUE','primary':{'semantic_verdict':{'recommended_role':'one'}},
         'verifier':{'semantic_verdict':{'recommended_role':'two'}}}
    before=deepcopy(row)
    plain=_anonymous_review_rows([row])
    current=_anonymous_review_rows([row],include_option_ids=True)
    assert row==before
    assert all('option_id' not in o for o in plain[0]['candidate_options'])
    for option in current[0]['candidate_options']:
        assert option['option_id']==option_identity('X','VALUE',{k:v for k,v in option.items() if k!='option_id'})
    reverse=_anonymous_review_rows([{**row,'primary':row['verifier'],'verifier':row['primary']}],include_option_ids=True)
    assert reverse==current


def test_reconciliation_requires_coverage_and_keeps_both_original_roles():
    from packages.medical_monitoring.admission.mapping_reconciliation import reconcile_mapping_cohorts
    from packages.medical_monitoring.admission.role_equivalence import ROLE_EQUIVALENCE_POLICY
    options,declaration=inputs();certificate=bind(declaration,options)
    base={'domain':'X','source_field':'VALUE','field_kind':'source_collected','dependency_fields':[],
          'evidence_ids':['ev-a'],'role_equivalence':certificate}
    a={**deepcopy(base),'recommended_role':'reading.code'}
    b={**deepcopy(base),'recommended_role':'reading.category'}
    kwargs=dict(profile_fields=[{'domain':'X','field':'VALUE'}],primary_mappings=[a],verifier_mappings=[b],
                primary_evidence_ids={'ev-a'},verifier_evidence_ids={'ev-a'},comparison_policy_version=ROLE_EQUIVALENCE_POLICY)
    report=reconcile_mapping_cohorts(**kwargs)
    assert report['auto_pass'] is True
    row=report['fields'][0]
    assert row['primary']['recommended_role']=='reading.code'
    assert row['verifier']['recommended_role']=='reading.category'
    assert row['dependency_comparison']['canonical_role']=='reading.category'
    assert report['facts_generated'] is False
    kwargs['verifier_evidence_ids']=set()
    assert reconcile_mapping_cohorts(**kwargs)['auto_pass'] is False
    kwargs['verifier_evidence_ids']={'ev-a'}
    kwargs['verifier_mappings']=[]
    assert reconcile_mapping_cohorts(**kwargs)['auto_pass'] is False


@pytest.mark.parametrize('reverse', [False, True])
def test_same_literal_role_optional_equivalence_is_not_a_new_disagreement(reverse):
    from packages.medical_monitoring.admission.role_equivalence import compare_role_equivalence
    options, declaration = inputs()
    certificate = bind(declaration, options)
    left = {'recommended_role': 'reading.code', 'dependency_fields': [],
            'field_kind': 'source_collected', 'role_equivalence': certificate}
    right = {key: deepcopy(value) for key, value in left.items() if key != 'role_equivalence'}
    if reverse:
        left, right = right, left
    result = compare_role_equivalence(left, right, domain='X', source_field='VALUE')
    assert result['dependencies_agreed']
    assert 'canonical_role' not in result
    assert result['role_equivalence_certificate'] is None
    assert result['left_annotations']['role_equivalence'] == left.get('role_equivalence')
    assert result['right_annotations']['role_equivalence'] == right.get('role_equivalence')
    legacy = compare_role_equivalence(left, right, domain='X', source_field='VALUE',
                                     policy_version='mm-mapping-role-equivalence-v1')
    assert not legacy['dependencies_agreed']


@pytest.mark.parametrize('defect', ['different_role', 'case_changed', 'distinct', 'insufficient',
                                   'wrong_scope', 'wrong_hash', 'hard_difference'])
def test_optional_certificate_never_hides_a_material_or_invalid_claim(defect):
    from packages.medical_monitoring.admission.role_equivalence import compare_role_equivalence
    options, declaration = inputs()
    certificate = bind(declaration, options)
    left = {'recommended_role': 'reading.code', 'dependency_fields': [],
            'field_kind': 'source_collected', 'role_equivalence': certificate}
    right = {key: deepcopy(value) for key, value in left.items() if key != 'role_equivalence'}
    if defect == 'different_role': right['recommended_role'] = 'reading.category'
    elif defect == 'case_changed': right['recommended_role'] = 'Reading.code'
    elif defect in ('distinct', 'insufficient'): certificate['judgment'] = defect
    elif defect == 'wrong_scope': certificate['source_field'] = 'OTHER'
    elif defect == 'wrong_hash': certificate['binding_sha256'] = '0' * 64
    elif defect == 'hard_difference': right['field_kind'] = 'derived'
    result = compare_role_equivalence(left, right, domain='X', source_field='VALUE')
    assert not result['dependencies_agreed']
    assert 'canonical_role' not in result
