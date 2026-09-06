"""Versioned evidence-tool identity rules, shared by submit and revalidation."""
from copy import deepcopy

from .document_evidence import MonitoringDocumentEvidencePacket
from ..intelligence.primitives import content_hash

EVIDENCE_TOOL_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v20-tools-v1",
    "monitoring-listing-field-mapping-verifier-v2-tools-v1",
    "monitoring-listing-field-mapping-adjudication-v6-tools-v1",
    "monitoring-listing-field-mapping-adjudication-verifier-v4-tools-v1",
})


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
