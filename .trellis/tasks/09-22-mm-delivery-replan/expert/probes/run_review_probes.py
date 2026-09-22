#!/usr/bin/env python3
"""Run isolated, synthetic 0922V2 review probes. This is NOT the product test suite.

Exit 0 means the probes ran and reproduced the recorded behavior at the review
baseline; it does not mean the application is correct or ready for production.
Only temporary directories and the explicit report path are written.
"""
from __future__ import annotations
import argparse
import copy
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import selected_source_logic as src

ROUND = '0922V2'
HEAD = '07b6a09c1644c9261e6e3637f4e497bf775c33a1'
RESULTS = []


def record(pid, name, classification, desired, observed, level='selected_function_logic', notes=''):
    RESULTS.append(dict(id=pid, name=name, classification=classification,
                        desired_behavior_satisfied=desired, observed=observed,
                        evidence_level=level, limitations=notes))


def clue(text):
    return SimpleNamespace(title='', text=text, evidence_ids=['synthetic-evidence-1'],
                           structured_payload={'domains': ['AE'], 'claims': []})


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


def artifact(value):
    return {'snapshot_ref': f'synthetic-{value}', 'findings': [{'finding_id': value}]}


def binding(name, value, project='synthetic-project'):
    return {'artifact': name, 'content_sha256': src.content_hash(value),
            'project_id': project, 'snapshot_digest': 'a' * 64}


def main(output):
    digests = [src.facts_table_source_digest('AE', [{'x': x}]) for x in [False, 0, '0']]
    assert len(set(digests)) == 3
    record('P01', '源摘要区分 False / 0 / 字符串0', 'local_fix_control', True, {'distinct_digests': 3})
    cleaned = [src._clean(v) for v in [False, 0, None]]
    assert cleaned == ['false', '0', '']
    record('P02', '展示清理不再吞0/False', 'local_fix_control', True, cleaned)

    value = src._clues_agree(clue('存在异常，事件为3级。'), clue('存在异常，事件为1级。'))
    assert value is False
    record('P03', '单一3级与1级不再判一致', 'local_fix_control', True, {'agree': value})
    value = src._clues_agree(clue('两条记录涉及同一受试者编号。'), clue('两条记录涉及同一受试者编号。'))
    assert value is False
    record('P04', 'neutral不再默认判一致', 'local_fix_control', True, {'agree': value},
           notes='仅验证不再默认确认；不能由此推论neutral就是医学分歧。')

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        root = Path(folder)
        write_json(root / src._AI_FINDINGS_ARTIFACT, {'findings': []})
        reader = src.FindingsReader(root)
        assert reader._read_ai_findings()['state'] == 'completed_no_findings'
        assert reader._daily_findings({}, None) == []
        record('P05', '有效零发现不生成备用提示', 'local_fix_control', True,
               {'state': reader._read_ai_findings()['state'], 'daily': []})

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        root = Path(folder); a = artifact('A'); b = artifact('B')
        write_json(root / 'result.json', a)
        write_json(root / src.FindingsReader._FINDINGS_BINDING, binding('result.json', a))
        reader = src.FindingsReader(root, 'synthetic-project')
        write_json(root / 'result.json', b)
        read = reader._read_ai_findings()
        assert read['state'] == 'read_failed' and read['error'] == 'binding_digest_mismatch'
        record('P06', '指针不变时替换同名工件被拒绝', 'local_fix_control', True, read)
        daily = reader._daily_findings({}, None)
        assert daily == []
        record('P07', '显式read_failed不再走备用生成', 'local_fix_control', True, {'daily': daily})

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        store = src.SelectionStore(); root = Path(folder)
        selection = [{'role': 'protocol', 'candidate_id': 'candidate-A'}]
        store._effective_user_selections(project_id='synthetic-project', workspace_dir=root,
                batch_id='synthetic-batch', user_role_selections=selection)
        read = store._effective_user_selections(project_id='synthetic-project', workspace_dir=root,
                batch_id='synthetic-batch', user_role_selections=[])
        assert read[0]['candidate_id'] == 'candidate-A'
        record('P08', '合法文件用途选择可无参数重读', 'local_fix_control', True,
               {'role': read[0]['role'], 'candidate_id': read[0]['candidate_id']})

    for pid, name, left, right in [
        ('P09', 'ALT相反趋势仍判一致', '存在ALT升高异常。', '存在ALT降低异常。'),
        ('P10', '给药前后相反时序仍判一致', '事件发生在给药前，存在风险信号。', '事件发生在给药后，存在风险信号。'),
        ('P11', '本次与既往分级交换仍判一致', '存在异常，本次3级、既往1级。', '存在异常，本次1级、既往3级。'),
    ]:
        a, b = clue(left), clue(right)
        value = src._clues_agree(a, b)
        assert value is True
        record(pid, name, 'defect_reproduced', False,
               {'left': left, 'right': right, 'agree': value,
                'stances': [src._clue_stance(a), src._clue_stance(b)],
                'grade_sets': [sorted(src._grade_terms(a)), sorted(src._grade_terms(b))]})

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        root = Path(folder); a = artifact('A'); b = artifact('B')
        write_json(root / 'A.json', a); write_json(root / 'B.json', b)
        pointer = root / src.FindingsReader._FINDINGS_BINDING
        write_json(pointer, binding('A.json', a))
        reader = src.FindingsReader(root, 'synthetic-project')
        first = reader._read_ai_findings()['findings'][0]['finding_id']
        write_json(pointer, binding('B.json', b))
        second = reader._read_ai_findings()['findings'][0]['finding_id']
        assert (first, second) == ('A', 'B')
        record('P12', '同一reader随active指针切换到新结果', 'defect_reproduced', False,
               {'first_read': first, 'after_active_update': second},
               notes='reader无result/run绑定参数。历史结果串新风险的API结论另依据publication_routes静态调用链；本探针未运行真实HTTP端点。')

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        root = Path(folder)
        write_json(root / src._AI_FINDINGS_ARTIFACT, artifact('legacy-B'))
        (root / src.FindingsReader._FINDINGS_BINDING).write_text('{broken', encoding='utf-8')
        read = src.FindingsReader(root)._read_ai_findings()
        assert read['state'] == 'completed_with_findings'
        assert read['findings'][0]['finding_id'] == 'legacy-B'
        record('P13', '已存在binding损坏后静默走legacy', 'defect_reproduced', False, read)

    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        root = Path(folder)
        write_json(root / src.FindingsReader._FINDINGS_BINDING, binding('missing.json', artifact('missing')))
        reader = src.FindingsReader(root)
        read = reader._read_ai_findings(); daily = reader._daily_findings({}, None)
        assert read['state'] == 'missing'
        assert daily == [{'kind':'DETERMINISTIC_FALLBACK_FIXTURE'}]
        record('P14', 'binding目标丢失被当无AI lane并进入备用分支', 'defect_reproduced', False,
               {'read': read, 'daily': daily},
               notes='备用生成函数为哨兵桩，证明该控制流被调用；未模拟实际临床风险。')

    unresolved = {'state':'needs_user_input', 'resolved_roles':[], 'unresolved_roles':['protocol']}
    batch = {'candidates':[{'candidate_id':'candidate-A'}, {'candidate_id':'candidate-B'}]}
    with tempfile.TemporaryDirectory(prefix='kz_0922V2_') as folder:
        store = src.SelectionStore(); root=Path(folder); errors=[]
        for selections in [[{'role':'protocol','candidate_id':'BAD-CANDIDATE'}], []]:
            effective=store._effective_user_selections(project_id='synthetic-project',workspace_dir=root,
                       batch_id='synthetic-batch',user_role_selections=selections)
            try:
                src._apply_user_role_selections(copy.deepcopy(unresolved), effective, batch)
            except src.DocumentAuthorityError as e:
                errors.append(str(e))
        assert len(errors)==2
        record('P15', '非法候选先落盘，下一次空参数仍被同值阻断', 'defect_reproduced', False,
               {'error_first_submit':errors[0], 'error_next_poll':errors[1],
                'persisted_candidate':store._load_user_selections(root,'synthetic-batch')[0]['candidate_id']},
               'composed_selected_function_logic',
               '组合遵循advance先effective/save后resolve/apply次序；未运行真实workflow和API。合法同角色新选择可修复，不能称不可恢复。')

    already={'state':'resolved','resolved_roles':[{'role':'protocol','status':'selected','candidate_id':'candidate-A'}],
             'unresolved_roles':[]}
    merged=src._apply_user_role_selections(already,[{'role':'protocol','candidate_id':'candidate-B'}],batch)
    assert merged['resolved_roles'][0]['candidate_id']=='candidate-A' and merged['user_adjudicated_roles']==[]
    record('P16', '自动已收敛角色的不同合法用户选择被静默忽略', 'behavioral_risk_reproduced', False,
           {'requested_by_user':'candidate-B','effective':'candidate-A','user_adjudicated_roles':[]},
           notes='不是规定用户必须覆盖模型；问题是不同选择没有冲突或过期状态反馈。')

    promoted=src._apply_user_role_selections(copy.deepcopy(unresolved),[{'role':'protocol','candidate_id':'candidate-A'}],batch)
    replayed=src._apply_user_role_selections(copy.deepcopy(unresolved),(),batch)
    assert promoted['state']=='resolved' and replayed['state']=='needs_user_input'
    record('P17', '人工决策未参与重放时无法再现原resolution', 'dependency_gap_demonstrated', False,
           {'with_manual_decision':promoted['state'],'without_manual_decision':replayed['state']},
           'composed_dependency_probe',
           '此探针仅证明人工决策为必要输入。真实promotion receipt未包含选择、verify函数未传选择，依据源码静态核对；未运行完整回执验签。')

    # Extracted branch from promote: blocked primary continues before map entry;
    # allowed supplementary immediately indexes that missing primary claim.
    entry_id_by_claim={}; blocked_entries=[]; observed_error=None
    for role, kind, candidate, blocked in [('protocol','primary','candidate-A',True),
                                          ('protocol','supplementary','candidate-B',False)]:
        if blocked:
            blocked_entries.append(candidate)
            continue
        claim=(role,kind,candidate)
        try:
            if kind=='supplementary':
                supplementary_of=entry_id_by_claim[(role,'primary','candidate-A')]
            entry_id_by_claim[claim]='synthetic-entry'
        except KeyError as e:
            observed_error=repr(e)
            break
    assert observed_error is not None
    record('P18', '主文档待确认时补充文档引用缺失键', 'defect_branch_reproduced', False,
           {'blocked_primary':blocked_entries,'exception':observed_error},
           'selected_branch_logic',
           '提取promotion的continue与supplementary_of索引逻辑；不模拟完整registry事务。源码transaction遇异常回滚另有静态证据。')

    report={'review_round':ROUND,'head':HEAD,'executed_at_utc':datetime.now(timezone.utc).isoformat(),
            'test_scope':'isolated transcribed source logic with synthetic scaffolding; no full repository import, API/browser or live model execution',
            'total':len(RESULTS),
            'local_fix_controls':sum(r['classification']=='local_fix_control' for r in RESULTS),
            'remaining_problem_demonstrations':sum(r['classification']!='local_fix_control' for r in RESULTS),
            'production_acceptance_passed':False,'probes':RESULTS}
    output.parent.mkdir(parents=True,exist_ok=True)
    write_json(output,report)
    print(json.dumps({k:report[k] for k in ['review_round','total','local_fix_controls','remaining_problem_demonstrations','production_acceptance_passed']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'evidence'/'probe_results.json')
    args=parser.parse_args()
    main(args.output)
