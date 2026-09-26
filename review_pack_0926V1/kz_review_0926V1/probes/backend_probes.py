#!/usr/bin/env python3
"""Read-only isolated probes. Default = transcribed source logic, not full app.
--repo PATH loads only the named AST functions/constants from a local checkout.
No network, credentials, databases or model calls are used.
"""
from __future__ import annotations
import argparse, ast, importlib.util, json, re, threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping
from copy import deepcopy

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path);args=p.parse_args()

def excerpt(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'source_excerpts'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return vars(mod)

def select_ast(path,names,class_name=None):
    tree=ast.parse(path.read_text(encoding='utf-8'));body=tree.body
    if class_name:
        body=next(n.body for n in body if isinstance(n,ast.ClassDef) and n.name==class_name)
    selected=[]
    for node in body:
        keys=[]
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):keys=[node.name]
        elif isinstance(node,ast.Assign):keys=[t.id for t in node.targets if isinstance(t,ast.Name)]
        elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):keys=[node.target.id]
        if any(k in names for k in keys):selected.append(node)
    class StripAnnotations(ast.NodeTransformer):
        def visit_FunctionDef(self,n):
            n.returns=None;n.decorator_list=[]
            for a in n.args.args+n.args.kwonlyargs+n.args.posonlyargs:a.annotation=None
            if n.args.vararg:n.args.vararg.annotation=None
            if n.args.kwarg:n.args.kwarg.annotation=None
            return self.generic_visit(n)
    selected=[StripAnnotations().visit(n) for n in selected]
    module=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
    env={'Any':Any,'Mapping':Mapping,'re':re,'threading':threading,'deepcopy':deepcopy,
         'STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS':frozenset(),
         'MonitoringAiOutputValidationError':type('MonitoringAiOutputValidationError',(ValueError,),{}),
         'MonitoringAiStateConflictError':type('MonitoringAiStateConflictError',(RuntimeError,),{})}
    exec(compile(module,str(path),'exec'),env)
    return env

if args.repo:
    policy=select_ast(args.repo/'services/api/app/monitoring_protocol_rules.py',{'expression_requires_diagnostic_coverage'})
    names={'_clue_fingerprint','_clue_entities','_clue_domain_pair','_clue_direction_text','_clue_stance','_clues_agree','_direction_set','_grade_terms','_ENTITY_RE','_POSITIVE_DIRECTION_RE','_NEGATIVE_DIRECTION_RE','_TEMPORAL_TOKEN_RE','_TEMPORAL_CANONICAL','_DIRECTION_TOKEN_RE','_DIRECTION_CANONICAL','_GRADE_RE'}
    clue=select_ast(args.repo/'packages/medical_monitoring/analysis/ae_mh_cross_analysis.py',names)
    heartbeat=select_ast(args.repo/'services/api/app/monitoring_ai_service.py',{'_run_with_heartbeat'},'MonitoringAiService')
else:
    policy=excerpt('policy_excerpt');clue=excerpt('clue_excerpt');heartbeat=excerpt('heartbeat_excerpt')
results=[]
def record(id,description,observed,healthy,scope='source_logic_excerpt'):
    results.append(dict(id=id,description=description,observed=observed,criterion_met=healthy,evidence_level=('actual_repo_ast_extraction' if args.repo else scope)))
walk=policy['expression_requires_diagnostic_coverage']
for id,expr,expect in [
    ('B01',{'missing':{'field':'cm.end_date'}},False),
    ('B02',{'changed':{'field':'visit.label'}},True),
    ('B03',{'gt':{'field':'lab.value','value':3}},True),
    ('B04',{'eq':{'field':'ae.serious','value':'yes'}},True),
    ('B05',{'date_compare':{'field':'ae.start','other_field':'ex.start','relation':'after'}},True),
    ('B06',{'regex':{'field':'cm.name','value':'drug'}},True),
]:
    actual=walk({},expr,{})
    record(id,'诊断覆盖要求须与求值器的不可判定能力相符',{'expression':expr,'requires_diagnostic':actual,'expected':expect},actual is expect)

def candidate(text,temporal=()):
    return SimpleNamespace(title=text,text='',evidence=[SimpleNamespace(evidence_id='syn-evidence-1')],structured_payload={'domains':['AE','MH'],'claims':[],'temporal_relationships':list(temporal)})
for id,a,b,expect in [
    ('B07','存在异常 ALT 升高','存在异常 ALT 降低',False),
    ('B08','存在异常 ALT 升高；AST 降低','存在异常 ALT 降低；AST 升高',False),
    ('B09','存在异常 本次事件3级；既往事件1级','存在异常 本次事件1级；既往事件3级',False),
    ('B10','存在异常 ALT 升高','存在异常 ALT 上升',True),
]:
    actual=clue['_clues_agree'](candidate(a),candidate(b))
    record(id,'配对信号不能丢失医学对象与方向/分级的归属',{'primary':a,'verifier':b,'agrees':actual,'expected':expect},actual is expect)
a=candidate('存在两个事件异常',['事件A给药前；事件B给药后']);b=candidate('存在两个事件异常',['事件A给药后；事件B给药前'])
actual=clue['_clues_agree'](a,b);record('B11','两个事件前后关系互换不能判一致',{'agrees':actual},actual is False)

class Repo:
    lease_seconds=0.3
    def __init__(self,fail=False):self.calls=[];self.n=0;self.fail=fail;self.lost=threading.Event()
    def heartbeat(self,*args):
        self.n+=1
        if self.fail and self.n>1:
            self.lost.set();raise RuntimeError('synthetic lease lost')
    def record_call(self,**kwargs):self.calls.append(kwargs)
job=SimpleNamespace(project_id='syn-project',job_id='syn-job',provider='stub',requested_model='stub',prompt_version='probe')
repo=Repo(True)
class SlowProvider:
    response_diagnostics={};response_model='stub'
    def run(self,env):
        if not repo.lost.wait(2):raise RuntimeError('fixture did not exercise heartbeat failure')
        return {'synthetic':'valid-provider-output'}
returned=False;raised=None
try:
    heartbeat['_run_with_heartbeat'](SimpleNamespace(repository=repo),job,'syn-owner',SlowProvider(),{})
    returned=True
except Exception as e:raised=type(e).__name__
record('B12','租约心跳失败后不得正常交付模型输出',{'heartbeat_failed':repo.lost.is_set(),'returned_normally':returned,'raised':raised},repo.lost.is_set() and not returned)
repo2=Repo()
class FailingProvider:
    response_diagnostics={'wire':'stub'};response_model=''
    def run(self,env):raise TimeoutError('synthetic timeout')
try:heartbeat['_run_with_heartbeat'](SimpleNamespace(repository=repo2),job,'syn-owner',FailingProvider(),{})
except TimeoutError:pass
record('B13','provider异常路径已写账（保留修复）',{'rows':len(repo2.calls),'outcome':repo2.calls[0]['outcome'] if repo2.calls else None},len(repo2.calls)==1 and repo2.calls[0]['outcome']=='provider_error')
# Exact truthiness expression from record_call; not a database persistence test.
def _int(source,key):
    raw=source.get(key)
    if raw is None or raw=='':return None
    try:return int(raw)
    except (TypeError,ValueError):return None
usage={'detail':{'reasoning_tokens':0,'cached_tokens':0}}
observed=_int(usage['detail'],'reasoning_tokens') or _int(usage,'reasoning_tokens')
record('B14','明确0用量不得在or回退中变为unknown',{'input':usage,'reasoning_tokens':observed},observed==0,'source_expression_probe')
print(json.dumps({'suite':'backend_isolated_probes','scope':'Isolated selected functions, no production DB/API/model execution. B03-B06 compare helper output to evaluator source contract, not full evaluator execution.','results':results},ensure_ascii=False,indent=2))
