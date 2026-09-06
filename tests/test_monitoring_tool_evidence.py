import pytest

from services.api.app.monitoring_tool_evidence import verified_tool_evidence


def evidence(**changes):
    return {"evidence_id": "ev-doc", "source_entry_id": "doc-1", "source_content_sha256": "a" * 64,
            "locator": "pdf:page:2", "quote": "exact source", "raw_fields": {}, **changes}


def read(**changes):
    return {"receipt": {"result": {"source_entry_id": "doc-1", "source_content_sha256": "a" * 64,
            "coverage": "partial", "units": [{"locator": "pdf:page:2", "text": "an exact source sentence"}], **changes}}}


@pytest.mark.parametrize("change", [{"quote": "invented"}, {"locator": "pdf:page:3"},
    {"source_entry_id": "doc-2"}, {"source_content_sha256": "b" * 64}, {"quote": ""}])
def test_document_citation_cannot_outgrow_the_actual_frozen_read(change):
    with pytest.raises(ValueError):
        verified_tool_evidence([evidence(**change)], [read()], {("doc-1", "a" * 64)})


def test_missing_or_unavailable_read_never_validates_a_document_quote():
    for reads in ([], [read(status="unavailable")]):
        with pytest.raises(ValueError):
            verified_tool_evidence([evidence()], reads, {("doc-1", "a" * 64)})
    result = verified_tool_evidence([evidence(raw_fields={"invented_interpretation": "not source"})], [read()], {("doc-1", "a" * 64)})
    assert result["ev-doc"]["source_entry_id"] == "doc-1"
    assert result["ev-doc"]["raw_fields"]["coverage"] == "partial"
    assert "invented_interpretation" not in result["ev-doc"]["raw_fields"]


def test_exact_cell_value_does_not_approve_an_unverified_quote_or_coerce_zero():
    reads = [read(units=[{"locator": "xlsx:sheet:AE:row:2", "cells": [{"coordinate": "B2", "value": 0}]}])]
    item = evidence(locator="xlsx:sheet:AE:row:2", quote="invented interpretation", raw_fields={"coordinate": "B2", "raw_value": 0})
    result = verified_tool_evidence([item], reads, {("doc-1", "a" * 64)})
    assert result["ev-doc"]["quote"] == ""
    assert result["ev-doc"]["raw_fields"]["raw_value"] == 0
    with pytest.raises(ValueError):
        verified_tool_evidence([{**item, "raw_fields": {"coordinate": "B2", "raw_value": "0"}}], reads, {("doc-1", "a" * 64)})


def test_tool_quote_reference_materializes_exact_unicode_source_without_copying():
    source = '原文：“quoted”\n保留换行。'
    receipt = read(units=[{"locator": "pdf:page:2", "text": source, "quote_ref": "quote-frozen", "text_offset": 40}])
    item = evidence(quote="", raw_fields={"tool_quote_ref": "quote-frozen"})
    result = verified_tool_evidence([item], [receipt], {("doc-1", "a" * 64)})
    assert result["ev-doc"]["quote"] == source
    assert result["ev-doc"]["raw_fields"]["text_offset"] == 40
    for change in ({"quote": "invented"}, {"locator": "pdf:page:3"}, {"raw_fields": {"tool_quote_ref": "unknown"}}):
        with pytest.raises(ValueError):
            verified_tool_evidence([{**item, **change}], [receipt], {("doc-1", "a" * 64)})
