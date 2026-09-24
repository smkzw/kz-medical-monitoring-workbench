"""Versioned evidence-tool identity rules, shared by submit and revalidation."""
from copy import deepcopy

from .document_evidence import MonitoringDocumentEvidencePacket
from ..intelligence.primitives import content_hash

# ---------------------------------------------------------------------------
# A18/A19单一版本→功能来源：每个mapping族提示词版本在此声明一次其功能集，
# 下面的七张frozenset全部由该表派生。新增版本只改本表（登记其features），
# 各集合自动一致——杜绝"漏注册某张集合导致schema/绑定/修复静默失灵"。
#
# features键：
#   strict          严格外层响应合同（整JSON校验+身份断言）
#   patch_repair    受控修复轮按patch模式只重发违规字段
#   role_eq_evidence role_equivalence_evidence输入侧注入
#   role_eq         角色等价证书绑定与比较（含dependency合同）
#   visual          视觉证据合同
#   dependency      显式dependency_fields合同
#   evidence_tool   证据工具循环
# 层叠规则（按tools版本自低向高）：evidence_tool ⊂ dependency ⊂ visual
#   ⊂ role_eq ⊂ role_eq_evidence ⊂ strict；patch_repair独立但v7.1起与
#   strict同登记。
# ---------------------------------------------------------------------------

_ADJ = "monitoring-listing-field-mapping-adjudication"
_ADJ_V = "monitoring-listing-field-mapping-adjudication-verifier"
_MAP = "monitoring-listing-field-mapping"
_MAP_V = "monitoring-listing-field-mapping-verifier"

_PROMPT_VERSION_FEATURES: dict[str, frozenset[str]] = {
    # --- tools-v1 base ---
    f"{_MAP}-v20-tools-v1": frozenset({"evidence_tool"}),
    f"{_MAP_V}-v2-tools-v1": frozenset({"evidence_tool"}),
    f"{_ADJ}-v6-tools-v1": frozenset({"evidence_tool"}),
    f"{_ADJ_V}-v4-tools-v1": frozenset({"evidence_tool"}),
    # --- tools-v2 dependency ---
    f"{_MAP}-v21-tools-v2": frozenset({"evidence_tool", "dependency"}),
    f"{_MAP_V}-v3-tools-v2": frozenset({"evidence_tool", "dependency"}),
    f"{_ADJ}-v7-tools-v2": frozenset({"evidence_tool", "dependency"}),
    f"{_ADJ_V}-v5-tools-v2": frozenset({"evidence_tool", "dependency"}),
    # --- tools-v3 visual + role_eq base ---
    f"{_MAP}-v22-tools-v3": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    f"{_MAP_V}-v4-tools-v3": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    f"{_ADJ}-v8-tools-v3": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    f"{_ADJ_V}-v6-tools-v3": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    f"{_ADJ}-v9-tools-v4": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    f"{_ADJ_V}-v7-tools-v4": frozenset({"evidence_tool", "dependency", "visual", "role_eq"}),
    # --- tools-v5 role_eq_evidence ---
    f"{_ADJ}-v10-tools-v5": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence"}),
    f"{_ADJ_V}-v8-tools-v5": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence"}),
    # --- tools-v6 strict ---
    f"{_ADJ}-v11-tools-v6": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict"}),
    f"{_ADJ_V}-v9-tools-v6": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict"}),
    # --- tools-v7 strict ---
    f"{_ADJ}-v12-tools-v7": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict"}),
    f"{_ADJ_V}-v10-tools-v7": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict"}),
    # --- tools-v7.1 strict + patch_repair ---
    f"{_ADJ}-v13-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v11-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ}-v14-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v12-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ}-v15-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ}-v16-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v13-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v14-tools-v7.1": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    # --- tools-v7.2 strict + patch_repair（含v17/v15后继合同与v19/v17边界结论版本）---
    f"{_ADJ}-v17-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v15-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ}-v18-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v16-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ}-v19-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
    f"{_ADJ_V}-v17-tools-v7.2": frozenset({"evidence_tool", "dependency", "visual", "role_eq", "role_eq_evidence", "strict", "patch_repair"}),
}


def _versions_with(feature: str) -> frozenset[str]:
    return frozenset(
        version
        for version, features in _PROMPT_VERSION_FEATURES.items()
        if feature in features
    )


STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS = _versions_with("strict")

# v7.1 residue contract: the controlled repair round re-emits only the
# violating field-mapping entries (patch mode) instead of the whole JSON
# document. Long single-document re-emission was the dominant v7 residue
# failure (strict parse breaks on 11-21k-char rebuilds). Older prompt
# versions keep the frozen full-rebuild repair contract.
PATCH_REPAIR_MAPPING_PROMPT_VERSIONS = _versions_with("patch_repair")

# 层叠集合 = 本层显式基线成员 ∪ 按feature派生 ∪ 下层集合（与改前手工
# 并集语义逐字节一致：RQE={v10,v8}∪STRICT等）。_versions_with只覆盖
# feature派生部分；基线成员显式列出，漂移由验证测试把关。
ROLE_EQUIVALENCE_EVIDENCE_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v10-tools-v5",
    "monitoring-listing-field-mapping-adjudication-verifier-v8-tools-v5",
}) | STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS | _versions_with("role_eq_evidence")

ROLE_EQUIVALENCE_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-adjudication-v9-tools-v4",
    "monitoring-listing-field-mapping-adjudication-verifier-v7-tools-v4",
}) | ROLE_EQUIVALENCE_EVIDENCE_PROMPT_VERSIONS | _versions_with("role_eq")

VISUAL_MAPPING_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v22-tools-v3",
    "monitoring-listing-field-mapping-verifier-v4-tools-v3",
    "monitoring-listing-field-mapping-adjudication-v8-tools-v3",
    "monitoring-listing-field-mapping-adjudication-verifier-v6-tools-v3",
}) | ROLE_EQUIVALENCE_PROMPT_VERSIONS | _versions_with("visual")

DEPENDENCY_MAPPING_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v21-tools-v2",
    "monitoring-listing-field-mapping-verifier-v3-tools-v2",
    "monitoring-listing-field-mapping-adjudication-v7-tools-v2",
    "monitoring-listing-field-mapping-adjudication-verifier-v5-tools-v2",
}) | VISUAL_MAPPING_PROMPT_VERSIONS | _versions_with("dependency")

EVIDENCE_TOOL_PROMPT_VERSIONS = frozenset({
    "monitoring-listing-field-mapping-v20-tools-v1",
    "monitoring-listing-field-mapping-verifier-v2-tools-v1",
    "monitoring-listing-field-mapping-adjudication-v6-tools-v1",
    "monitoring-listing-field-mapping-adjudication-verifier-v4-tools-v1",
}) | DEPENDENCY_MAPPING_PROMPT_VERSIONS | _versions_with("evidence_tool")


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
