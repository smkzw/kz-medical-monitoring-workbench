import json
from copy import deepcopy
from unittest.mock import patch
from services.api.app.ai_gateway import AiPromptEnvelope, AiTaskType, OpenAICompatibleAiProvider
from services.api.app.monitoring_visual_tool_bridge import attach_visual_inputs, visual_provider
from services.api.app.monitoring_visual_transport import MonitoringVisualOpenAIProvider, MonitoringVisualPromptEnvelope
from services.api.app.monitoring_evidence_tool_loop import run_evidence_tool_loop, TOOL_REQUEST_SCHEMA
from services.api.app.monitoring_tool_evidence import verified_tool_evidence
from tests.test_monitoring_visual_toolset import toolkit
import pytest


def test_real_tool_image_is_attached_to_next_model_http_call(tmp_path):
    tools, source = toolkit(tmp_path)
    env = AiPromptEnvelope(task_id='visual-job', task_type=list(AiTaskType)[0],
                           prompt_version='synthetic-v3', system_prompt='read the source', payload={})
    original = deepcopy(env)
    seen = []
    class Response:
        status = 200
        headers = {'Content-Type': 'application/json'}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps({'model': 'synthetic-model', 'choices': [{'message': {'content': '{"candidates":[]}'}}]}).encode()
    def send(request, **kwargs):
        seen.append(json.loads(request.data));return Response()
    provider = MonitoringVisualOpenAIProvider(base_url='https://synthetic.invalid/v1', api_key='synthetic',
                                              model_name='synthetic-model', expected_response_model='synthetic-model')
    def call(current):
        if not tools.visual_inputs:
            return {'schema_version': TOOL_REQUEST_SCHEMA, 'task_id': env.task_id,
                    'input_revision_sha256': 'a'*64, 'tool_requests': [{'request_id':'image-1', 'name':'render_pdf_region',
                    'arguments': {'source_entry_id':source,'page_index':0,'dpi':72}}]}
        attached = attach_visual_inputs(current, tools.visual_inputs)
        assert isinstance(attached, MonitoringVisualPromptEnvelope)
        return provider.run(attached)
    with patch('services.api.app.monitoring_visual_transport.urlopen', side_effect=send):
        result=run_evidence_tool_loop(env,input_revision='a'*64,call_model=call,
            validate_current=lambda:None,validate_model=lambda:None,tool_schemas=tools.schemas,execute_tool=tools.execute)
    assert env == original
    assert result.model_turns == 2
    content=seen[0]['messages'][1]['content']
    assert content[1]['type']=='image_url'
    metadata=json.loads(content[0]['text'])['visual_image_inputs'][0]
    receipt=result.receipts[0]['result']
    assert metadata['visual_ref']==receipt['visual_ref']
    assert metadata['source_entry_id']==source
    assert 'image_bytes' not in json.dumps(result.receipts)
    citation={'evidence_id':'visual-evidence','source_entry_id':source,
              'source_content_sha256':receipt['source_content_sha256'], 'locator':receipt['locator'],
              'quote':'','raw_fields':{'tool_visual_ref':receipt['visual_ref']}}
    verified=verified_tool_evidence([citation],[{'receipt':result.receipts[0]}],{(source,receipt['source_content_sha256'])})
    assert verified['visual-evidence']['quote']==''
    assert verified['visual-evidence']['raw_fields']['native_text_quote_verified'] is False
    for bad in ({**citation,'quote':'invented native quote'},
                {**citation,'raw_fields':{'tool_visual_ref':'wrong-image'}},
                {**citation,'locator':'pdf:page:999'}):
        with pytest.raises(ValueError):
            verified_tool_evidence([bad],[{'receipt':result.receipts[0]}],{(source,receipt['source_content_sha256'])})


def test_provider_adaptation_preserves_exact_configuration():
    base=OpenAICompatibleAiProvider(base_url='https://synthetic.invalid/v1',api_key='synthetic',
         model_name='m',provider_name='p',timeout_seconds=300,max_attempts=1,
         expected_response_model='observed',default_thinking='enabled',default_reasoning_effort='high')
    adapted=visual_provider(base)
    assert type(adapted) is MonitoringVisualOpenAIProvider
    for key in ('base_url','api_key','model_name','provider_name','timeout_seconds','max_attempts',
                'expected_response_model','default_thinking','default_reasoning_effort'):
        assert getattr(adapted,key)==getattr(base,key)
    assert visual_provider(adapted) is adapted
