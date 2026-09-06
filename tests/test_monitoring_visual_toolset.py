import json
from dataclasses import replace
from types import SimpleNamespace

from services.api.app.monitoring_evidence_toolset import MonitoringEvidenceToolset
from tests.test_mm_c3_document_evidence import _packet
from tests.test_monitoring_document_visual_regions import freeze, header_and_two_image_pages_pdf


def toolkit(tmp_path, enabled=True):
    content, _, _, _ = header_and_two_image_pages_pdf()
    visual, binding, _, _ = freeze(tmp_path, content, '.pdf', 'application/pdf')
    packet = _packet()
    roles = tuple(replace(role, binding=replace(role.binding, content_sha256=binding.content_sha256))
                  if role.role == 'protocol' else role for role in packet.roles)
    packet = replace(packet, roles=roles)
    visual.project_id = packet.project_id
    reader = SimpleNamespace(project_id=packet.project_id, input_revision='a' * 64,
                             profile={'document_evidence': packet.to_dict()})
    return MonitoringEvidenceToolset(reader, document_resolver=visual.resolver,
                                    visual_reader=visual if enabled else None), roles[0].binding.source_entry_id


def test_visual_tools_are_opt_in_and_do_not_change_text_only_tools(tmp_path):
    tools, _ = toolkit(tmp_path, enabled=False)
    assert 'render_pdf_region' not in tools.schemas
    assert 'extract_word_embedded_image' not in tools.schemas
    assert tools.visual_inputs == {}


def test_visual_tool_receipt_binds_actual_pixels_without_serializing_them(tmp_path):
    tools, source = toolkit(tmp_path)
    result = tools.execute('render_pdf_region', {'source_entry_id': source, 'page_index': 1, 'dpi': 72})
    assert result['locator'] == 'pdf:page:2'
    assert result['absence_claim_supported'] is False
    assert result['coverage'] == 'partial'
    assert result['source_entry_id'] == source
    image = tools.visual_inputs[result['visual_ref']]
    assert image.image.image_sha256 == result['image_sha256']
    assert image.image.image_bytes.startswith(b'\x89PNG')
    assert 'image_bytes' not in json.dumps(result)


def test_visual_tool_unknown_source_and_wrong_page_are_explicit_failures(tmp_path):
    tools, source = toolkit(tmp_path)
    for arguments in ({'source_entry_id': 'not-bound', 'page_index': 0},
                      {'source_entry_id': source, 'page_index': 999}):
        result = tools.execute('render_pdf_region', arguments)
        assert result['status'] == 'unavailable'
        assert result['coverage'] == 'none'
        assert result['absence_claim_supported'] is False
    assert tools.visual_inputs == {}
