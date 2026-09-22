"""Read-only production-module probes; all writes confined to temporary fixtures."""
import hashlib
import json
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from packages.medical_monitoring.analysis.protocol_profile import build_protocol_profile
from packages.medical_monitoring.analysis.ae_mh_cross_analysis import _clues_agree, adjudicate
from packages.medical_monitoring.api.r7_product.facts_mode_outputs import FactsModeOutputProvider
from packages.medical_monitoring.projections.facts_publication import FactsPublicationAuthorityProvider
from services.api.app.monitoring_document_authority_workflow import MonitoringDocumentAuthorityWorkflow
from services.api.app.monitoring_document_authority_jobs import _apply_user_role_selections

cases = []
def record(id, reproduced, observed):
    cases.append(dict(id=id, defect_reproduced=bool(reproduced), observed=observed))

with tempfile.TemporaryDirectory(prefix='mm-review-0922-') as temp:
    root = Path(temp)
    docs = root/'docs'; docs.mkdir()
    (docs/'candidate.txt').write_text('本研究适应症为过敏性鼻炎。', encoding='utf-8')
    profile = build_protocol_profile(docs).to_payload()
    record('R10-keyword-risk', bool(profile['risk_direction_zh']), profile)
    (docs/'candidate.txt').write_text('方案采用CTCAE 4.0。', encoding='utf-8')
    (docs/'background.txt').write_text('CTCAE 5.0 CTCAE 5.0', encoding='utf-8')
    record('R10-version-vote', build_protocol_profile(docs).ctcae_version == '5.0', build_protocol_profile(docs).to_payload())
    helpers = runpy.run_path(str(ROOT/'tests/test_aemh_dualvlm_contracts.py'))
    candidate = helpers['_candidate']
    primary = candidate('p', '存在ALT升高异常，需关注', '存在ALT升高异常，提示风险信号')
    verifier = candidate('v', '存在ALT降低异常，需关注', '存在ALT降低异常，提示风险信号')
    repo = helpers['FakeRepository'](jobs={'p':helpers['_completed_job']('p'), 'v':helpers['_completed_job']('v')}, candidates_by_job={'p':[primary], 'v':[verifier]})
    result = adjudicate(ai_repository=repo, project_id='synthetic', subject_labels=['001'], facts_snapshot_ref='frozen-test', primary_job_by_subject={'001':'p'}, verifier_job_by_subject={'001':'v'}, artifacts_dir=None)
    record('R04-opposite-predicate', _clues_agree(primary, verifier) and result['counts']['accepted'] > 0, result['counts'])
    artifacts=root/'findings'; artifacts.mkdir()
    legacy=artifacts/'aemh-findings-facts-snapshot-001.dualvlm-full1.json'
    legacy.write_text(json.dumps({'findings':[{'finding_id':'legacy','subject_label':'001','state':'accepted','primary':{'title':'synthetic','text':'x'}}]}))
    (artifacts/'aemh-findings.active.json').write_text('{broken')
    provider=FactsModeOutputProvider(artifacts, project_ref='synthetic')
    state=provider._read_ai_findings()
    record('R03-bad-binding', state['state']=='completed_with_findings', {'state':state['state'],'artifact':state['artifact']})
    rows=provider.public_findings(projection={},project_ref='synthetic')
    record('R05-public-dto', bool(rows) and 'verified_event_refs' not in rows[0], sorted(rows[0]))
    (artifacts/'aemh-findings.active.json').write_text(json.dumps({'artifact':'missing.json','content_sha256':'0'*64,'project_id':'synthetic'}))
    state=provider._read_ai_findings()
    record('R03-bound-missing', state['state']=='missing', state)
    helpers2=runpy.run_path(str(ROOT/'tests/test_facts_publication_manifest.py'))
    workspace=helpers2['_make_workspace'](root)
    fp=FactsPublicationAuthorityProvider(workspace)
    fp._load_domains()
    manifest=workspace/'runtime/artifacts/facts-manifest.json'
    helpers2['_write_table_artifact'](manifest.parent,'LB',[{'SUBJID':'01001','LBTEST':'ALT','LBORRES':'42'}])
    manifest.write_text('{broken')
    domains=FactsPublicationAuthorityProvider(workspace)._load_domains()
    record('R11-corrupt-manifest', 'LB' in domains, {'tables_after_corrupt_manifest':sorted(domains)})
    packet=FactsPublicationAuthorityProvider(workspace).get_packet('synthetic',run_ref='requested-run',snapshot_ref='nonexistent-history',cutoff_ref='requested-cutoff')
    record('R11-unbound-snapshot', packet.snapshot_ref=='nonexistent-history', {'snapshot_ref':packet.snapshot_ref,'run_ref':packet.run_ref})
    obj=object.__new__(MonitoringDocumentAuthorityWorkflow)
    selections=obj._effective_user_selections(project_id='synthetic',workspace_dir=root/'decisions',batch_id='batch',user_role_selections=[{'role':'protocol','candidate_id':'invalid'}])
    rejected=False
    try:
        _apply_user_role_selections({'unresolved_roles':['protocol'],'resolved_roles':[]},selections,{'candidates':[{'candidate_id':'valid'}]})
    except Exception:
        rejected=True
    persisted=obj._load_user_selections(root/'decisions','batch')
    record('R06-invalid-persisted', rejected and bool(persisted), {'rejected':rejected,'persisted':persisted})

print(json.dumps({'scope':'actual modules with synthetic temporary fixtures; no API/browser/provider calls', 'cases':cases},ensure_ascii=False,indent=2))
