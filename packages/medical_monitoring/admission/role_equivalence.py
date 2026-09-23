"""Field-local, source-bound declarations authored by two product models.

This module verifies structure and agreement; it never infers clinical synonymy.
A certificate is not a guarantee against a shared model error.
"""
from copy import deepcopy
from ..intelligence.primitives import content_hash

LEGACY_ROLE_EQUIVALENCE_POLICY = 'mm-mapping-role-equivalence-v1'
ROLE_EQUIVALENCE_POLICY = 'mm-mapping-role-equivalence-v2'
ROLE_EQUIVALENCE_POLICIES = frozenset({LEGACY_ROLE_EQUIVALENCE_POLICY, ROLE_EQUIVALENCE_POLICY})
DIMENSIONS = ('object', 'measurement_concept', 'action_target', 'value_representation', 'standard_granularity')
RELATIONS = frozenset({'equivalent', 'distinct', 'insufficient'})
UNRESOLVED_ROLES = frozenset({'', 'unmapped', 'unresolved', 'unknown'})


def option_identity(domain, source_field, option):
    return content_hash({'domain': domain, 'source_field': source_field, 'option': option})


def _normalize_dimensions(dimensions, allowed_evidence_ids):
    """R23轮6：良性结构变异归一——模型在五维轴上产出不规范对象时，
    做确定性修正而非直接拒收。

    - axis非dict（如纯字符串"insufficient"）→ 构造insufficient轴
    - relation缺失或不在RELATIONS → 降为insufficient
    - evidence_ids为字符串 → 包装为单元素列表
    - evidence_ids含非allowed项 → 过滤保留allowed子集
    - rationale缺失/空白 → 填入确定性占位说明
    归一后仍不合规（dimension键缺失等）由后续严格校验统一拒收。
    """
    if not isinstance(dimensions, dict):
        return
    for axis_name, axis in dimensions.items():
        if isinstance(axis, str) and axis.strip():
            dimensions[axis_name] = {
                'relation': axis if axis in RELATIONS else 'insufficient',
                'evidence_ids': [],
                'rationale': f'模型以文本形式返回该维度判断：{axis.strip()}',
            }
            axis = dimensions[axis_name]
        if not isinstance(axis, dict):
            dimensions[axis_name] = {
                'relation': 'insufficient', 'evidence_ids': [],
                'rationale': '模型未能产出该维度的结构化判断',
            }
            continue
        relation = axis.get('relation')
        if relation not in RELATIONS:
            axis['relation'] = 'insufficient'
            if not axis.get('rationale'):
                axis['rationale'] = '模型返回的relation值不在合法集合内，保守降级'
        eids = axis.get('evidence_ids')
        if isinstance(eids, str):
            axis['evidence_ids'] = [eids] if eids.strip() else []
        elif not isinstance(eids, list):
            axis['evidence_ids'] = []
        else:
            axis['evidence_ids'] = [str(x) for x in eids if isinstance(x, str)]
        rationale = axis.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip():
            axis['rationale'] = '该维度判断依据未在payload中完整表述，保守归入insufficient'


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
    _normalize_dimensions(declaration['dimensions'], evidence_ids)
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


def compare_role_equivalence(left, right, *, domain, source_field, policy_version=ROLE_EQUIVALENCE_POLICY):
    from .mapping_comparison import compare_mapping_dependencies
    if policy_version not in ROLE_EQUIVALENCE_POLICIES:
        raise ValueError("unsupported_role_equivalence_policy")
    a,b=deepcopy(dict(left)),deepcopy(dict(right))
    ca,cb=a.pop('role_equivalence',None),b.pop('role_equivalence',None)
    proof=agreed_role_representation(ca,cb,left_role=a.get('recommended_role'),right_role=b.get('recommended_role'))
    if proof is not None and any(c.get('domain') != domain or c.get('source_field') != source_field for c in (ca, cb)):
        proof = None
    if proof is not None:
        a['recommended_role']=b['recommended_role']=proof['canonical_role']
    result=compare_mapping_dependencies(a,b)
    result['policy_version']=policy_version
    optional_agreement = False
    if (policy_version == ROLE_EQUIVALENCE_POLICY and (ca is None) != (cb is None)
            and a.get('recommended_role') == b.get('recommended_role')):
        declaration = ca if ca is not None else cb
        # A self-check validates the optional claim's binding only. It never
        # constitutes a second model opinion or authorizes canonicalization.
        optional_agreement = (
            isinstance(declaration, dict)
            and declaration.get('domain') == domain and declaration.get('source_field') == source_field
            and agreed_role_representation(declaration, declaration,
                left_role=a.get('recommended_role'), right_role=b.get('recommended_role')) is not None
        )
    if (ca is not None or cb is not None) and proof is None and not optional_agreement:
        result['dependencies_agreed']=False
        result['dependency_differences']=sorted(set(result['dependency_differences'])|{'role_equivalence'})
    if proof is not None:
        proof['policy_version'] = policy_version
    result['role_equivalence_certificate']=proof
    if proof is not None and result['dependencies_agreed']:
        result['canonical_role']=proof['canonical_role']
    result['left_annotations']['role_equivalence']=deepcopy(ca)
    result['right_annotations']['role_equivalence']=deepcopy(cb)
    return result
