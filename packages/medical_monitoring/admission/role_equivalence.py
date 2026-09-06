"""Field-local, source-bound declarations authored by two product models.

This module verifies structure and agreement; it never infers clinical synonymy.
A certificate is not a guarantee against a shared model error.
"""
from copy import deepcopy
from ..intelligence.primitives import content_hash

ROLE_EQUIVALENCE_POLICY = 'mm-mapping-role-equivalence-v1'
DIMENSIONS = ('object', 'measurement_concept', 'action_target', 'value_representation', 'standard_granularity')
RELATIONS = frozenset({'equivalent', 'distinct', 'insufficient'})
UNRESOLVED_ROLES = frozenset({'', 'unmapped', 'unresolved', 'unknown'})


def option_identity(domain, source_field, option):
    return content_hash({'domain': domain, 'source_field': source_field, 'option': option})


def bind_role_declaration(declaration, *, domain, source_field, options, evidence_ids, source_scope_sha256):
    """Validate model-authored proof and attach the exact anonymous options.

    Caller must subsequently validate citation/source closure, as for all mapping
    evidence. Provider-supplied binding fields are forbidden by the exact shape.
    """
    if declaration is None:
        return None
    if not isinstance(source_scope_sha256, str) or len(source_scope_sha256) != 64:
        raise ValueError('role_equivalence_source_scope_required')
    if not isinstance(declaration, dict) or set(declaration) != {
        'judgment', 'option_ids', 'dimensions', 'counterevidence_summary',
    }:
        raise ValueError('role_equivalence_shape_invalid')
    if declaration['judgment'] not in RELATIONS:
        raise ValueError('role_equivalence_judgment_invalid')
    bound = []
    for option in options:
        raw = {key: value for key, value in option.items() if key != 'option_id'}
        oid = option_identity(domain, source_field, raw)
        if option.get('option_id') != oid:
            raise ValueError('role_equivalence_option_binding_invalid')
        bound.append({'option_id': oid, 'role': raw.get('semantic_verdict', {}).get('recommended_role', ''),
                      'semantic_verdict_sha256': content_hash(raw.get('semantic_verdict', {}))})
    ids = declaration['option_ids']
    if (len(bound) != 2 or len({item['option_id'] for item in bound}) != 2
            or not isinstance(ids, list) or len(ids) != 2
            or any(not isinstance(item, str) for item in ids)
            or set(ids) != {item['option_id'] for item in bound}):
        raise ValueError('role_equivalence_option_set_mismatch')
    dimensions = declaration['dimensions']
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ValueError('role_equivalence_dimensions_incomplete')
    allowed = set(evidence_ids)
    for axis_name, axis in dimensions.items():
        if (not isinstance(axis, dict) or set(axis) != {'relation', 'evidence_ids', 'rationale'}
                or axis['relation'] not in RELATIONS
                or not isinstance(axis['rationale'], str) or not axis['rationale'].strip()
                or not isinstance(axis['evidence_ids'], list)
                or any(not isinstance(item, str) or item not in allowed for item in axis['evidence_ids'])
                or (axis['relation'] == 'equivalent' and not axis['evidence_ids'])):
            raise ValueError('role_equivalence_axis_invalid:' + axis_name)
    if (not isinstance(declaration['counterevidence_summary'], str)
            or not declaration['counterevidence_summary'].strip()):
        raise ValueError('role_equivalence_counterevidence_missing')
    if declaration['judgment'] == 'equivalent':
        if any(axis['relation'] != 'equivalent' for axis in dimensions.values()):
            raise ValueError('role_equivalence_axis_disagreement')
        if any(str(item['role']).strip().casefold() in UNRESOLVED_ROLES for item in bound):
            raise ValueError('role_equivalence_cannot_promote_unknown')
    result = deepcopy(declaration)
    result['option_ids'] = sorted(ids)
    result['bound_options'] = sorted(bound, key=lambda item: item['option_id'])
    result['source_scope_sha256'] = source_scope_sha256
    result['binding_sha256'] = content_hash({'domain': domain, 'source_field': source_field,
                                           'source_scope_sha256': source_scope_sha256,
                                           'options': result['bound_options']})
    result['domain'], result['source_field'] = domain, source_field
    return result


def agreed_role_representation(left, right, *, left_role, right_role):
    """Return a representation only for two validated, matching declarations.

    The enclosing comparator must still compare every non-role hard attribute.
    """
    for declaration in (left, right):
        if not isinstance(declaration, dict) or declaration.get('judgment') != 'equivalent':
            return None
        axes = declaration.get('dimensions', {})
        if set(axes) != set(DIMENSIONS) or any(
            not isinstance(axis, dict) or axis.get('relation') != 'equivalent'
            or not axis.get('evidence_ids') or not axis.get('rationale') for axis in axes.values()
        ):
            return None
        bound = declaration.get('bound_options', [])
        if len(bound) != 2 or len({item.get('option_id') for item in bound}) != 2:
            return None
        if declaration.get('binding_sha256') != content_hash({
            'domain': declaration.get('domain'), 'source_field': declaration.get('source_field'), 'options': bound,
            'source_scope_sha256': declaration.get('source_scope_sha256'),
        }):
            return None
        if set(declaration.get('option_ids', [])) != {item.get('option_id') for item in bound}:
            return None
    if left['binding_sha256'] != right['binding_sha256'] or left['bound_options'] != right['bound_options']:
        return None
    roles = {item['role'] for item in left['bound_options']}
    if left_role not in roles or right_role not in roles or any(
        str(role).strip().casefold() in UNRESOLVED_ROLES for role in roles
    ):
        return None
    return {'policy_version': ROLE_EQUIVALENCE_POLICY, 'canonical_role': min(roles),
            'left_declaration': deepcopy(left), 'right_declaration': deepcopy(right),
            'clinical_acceptance': False}


def compare_role_equivalence(left, right, *, domain, source_field):
    from .mapping_comparison import compare_mapping_dependencies
    a,b=deepcopy(dict(left)),deepcopy(dict(right))
    ca,cb=a.pop('role_equivalence',None),b.pop('role_equivalence',None)
    proof=agreed_role_representation(ca,cb,left_role=a.get('recommended_role'),right_role=b.get('recommended_role'))
    if proof is not None and any(c.get('domain') != domain or c.get('source_field') != source_field for c in (ca, cb)):
        proof = None
    if proof is not None:
        a['recommended_role']=b['recommended_role']=proof['canonical_role']
    result=compare_mapping_dependencies(a,b)
    result['policy_version']=ROLE_EQUIVALENCE_POLICY
    if (ca is not None or cb is not None) and proof is None:
        result['dependencies_agreed']=False
        result['dependency_differences']=sorted(set(result['dependency_differences'])|{'role_equivalence'})
    result['role_equivalence_certificate']=proof
    if proof is not None and result['dependencies_agreed']:
        result['canonical_role']=proof['canonical_role']
    result['left_annotations']['role_equivalence']=deepcopy(ca)
    result['right_annotations']['role_equivalence']=deepcopy(cb)
    return result
