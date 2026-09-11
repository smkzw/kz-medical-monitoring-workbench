"""Versioned evidence-tool identity rules, shared by submit and revalidation."""
from copy import deepcopy

from .document_evidence import MonitoringDocumentEvidencePacket
from ..intelligence.primitives import content_hash

STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v12-tools-v7",
    "monitoring-listing-field-mapping-adjudication-verifier-v10-tools-v7",
    "monitoring-listing-field-mapping-adjudication-v11-tools-v6",
    "monitoring-listing-field-mapping-adjudication-verifier-v9-tools-v6",
    "monitoring-listing-field-mapping-adjudication-v13-tools-v7.1",
    "monitoring-listing-field-mapping-adjudication-verifier-v11-tools-v7.1",
})

# v7.1 residue contract: the controlled repair round re-emits only the
# violating field-mapping entries (patch mode) instead of the whole JSON
# document. Long single-document re-emission was the dominant v7 residue
# failure (strict parse breaks on 11-21k-char rebuilds). Older prompt
# versions keep the frozen full-rebuild repair contract.
PATCH_REPAIR_MAPPING_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v13-tools-v7.1",
    "monitoring-listing-field-mapping-adjudication-verifier-v11-tools-v7.1",
})

ROLE_EQUIVALENCE_EVIDENCE_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v10-tools-v5",
    "monitoring-listing-field-mapping-adjudication-verifier-v8-tools-v5",
}) | STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS

ROLE_EQUIVALENCE_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v9-tools-v4",
    "monitoring-listing-field-mapping-adjudication-verifier-v7-tools-v4",
}) | ROLE_EQUIVALENCE_EVIDENCE_PROMPT_VERSIONS

VISUAL_MAPPING_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v22-tools-v3",
    "monitoring-listing-field-mapping-verifier-v4-tools-v3",
    "monitoring-listing-field-mapping-adjudication-v8-tools-v3",
    "monitoring-listing-field-mapping-adjudication-verifier-v6-tools-v3",
}) | ROLE_EQUIVALENCE_PROMPT_VERSIONS

DEPENDENCY_MAPPING_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v21-tools-v2",
    "monitoring-listing-field-mapping-verifier-v3-tools-v2",
    "monitoring-listing-field-mapping-adjudication-v7-tools-v2",
    "monitoring-listing-field-mapping-adjudication-verifier-v5-tools-v2",
}) | VISUAL_MAPPING_PROMPT_VERSIONS

EVIDENCE_TOOL_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v20-tools-v1",
    "monitoring-listing-field-mapping-verifier-v2-tools-v1",
    "monitoring-listing-field-mapping-adjudication-v6-tools-v1",
    "monitoring-listing-field-mapping-adjudication-verifier-v4-tools-v1",
}) | DEPENDENCY_MAPPING_PROMPT_VERSIONS


def bind_frozen_document_sources(profile):
    """Allow actual document citations only for explicitly frozen current files.

    The original full_profile/full_input identities stay untouched: these
    refer to the shared full-table input, while profile_sha256 binds this
    particular full profile. The job input-payload digest and explicit source
    bindings additionally freeze the tool-enabled source set.
    """
    result = deepcopy(dict(profile))
    raw = result.get("document_evidence")
    if not raw:
        return result
    packet = MonitoringDocumentEvidencePacket.from_dict(raw)
    if packet.project_id != result.get("project_id"):
        raise ValueError("tool document project mismatch")
    bindings = list(result["source_bindings"])
    known = {item["source_entry_id"]: item["source_content_sha256"] for item in bindings}
    for role in packet.roles:
        if role.status != "current" or role.binding is None:
            continue
        for source in (role.binding, *role.supplementary_bindings):
            if source.source_entry_id in known:
                if known[source.source_entry_id] != source.content_sha256:
                    raise ValueError("tool document source digest conflict")
                continue
            known[source.source_entry_id] = source.content_sha256
            bindings.append({"source_entry_id": source.source_entry_id,
                             "source_content_sha256": source.content_sha256})
    result["source_bindings"] = bindings
    result["source_sha256s"] = [item["source_content_sha256"] for item in bindings]
    if result.get("scope") != "complete_profile_chunk":
        result.pop("profile_sha256", None)
        result["profile_sha256"] = content_hash(result)
    return result


def bind_tool_revision_sources(revision, profile):
    """Extend one revision using the same frozen source set at submit/recheck."""
    sources = {item.source_entry_id: item.model_dump(mode="json") for item in revision.sources}
    for source in profile["source_bindings"]:
        source = dict(source)
        entry_id = source["source_entry_id"]
        if entry_id in sources and sources[entry_id] != source:
            raise ValueError("tool source revision conflict")
        sources[entry_id] = source
    return revision.model_validate({**revision.model_dump(mode="json"), "sources": list(sources.values())})
