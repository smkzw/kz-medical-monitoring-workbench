"""Versioned evidence-tool identity rules, shared by submit and revalidation."""
# 注：本文件在Python 3.9运行时求值函数注解——`frozenset[str] | None`这类
# PEP 604联合必须延迟求值（future import），否则模块导入即TypeError。
from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from typing import Any

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
    # --- 20260927 R27-01首轮/遗留执行身份：如实登记为无工具（空集）---
    # 这些是当前仍可派发或仍被服务识别的首轮/遗留mapping版本，其真实
    # 执行路径是单次provider调用（_run_with_evidence_tools对无
    # evidence_tool功能者直接单次调用；submit也不做冻结文档源绑定）。
    # 版本名中的tools-vN只是命名沿袭（推进版本以打开全新重试预算时
    # 保留旧名），不构成能力声称——能力唯一以本表为准，不因后缀声称。
    # 历史SAR 302作业（主侧v19×151+盲核v8-tools-v6×151）全部属于此类，
    # 其evidence_reads回执为0（见scripts/monitoring_mapping_tool_usage_audit.py
    # 的只读分类导出），不得描述为已做自主取证。若未来要给首轮接上
    # 取证工具，必须登记新的tool-enabled版本形成新执行身份，不得就地
    # 改写这些历史行的语义。
    f"{_MAP}-v19": frozenset(),  # 主侧默认首轮（PROMPT_VERSION_BY_TASK）
    f"{_MAP_V}-v1": frozenset(),  # 首轮盲核遗留合同（服务提示块仍识别）
    f"{_MAP_V}-v5-tools-v4": frozenset(),
    f"{_MAP_V}-v6-tools-v5": frozenset(),
    f"{_MAP_V}-v7-tools-v6": frozenset(),
    f"{_MAP_V}-v8-tools-v6": frozenset(),  # mapping_gate现行盲核首轮
    f"{_ADJ}-v5": frozenset(),  # 裁决lane无工具读开关时的遗留派发身份
    f"{_ADJ_V}-v3": frozenset(),
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

# 功能键全集：登记行引用未知功能键（如拼写漂移）会被启动闭包拒绝——
# 否则该版本会从所有派生集合静默消失。
KNOWN_PROMPT_VERSION_FEATURES = frozenset({
    "strict", "patch_repair", "role_eq_evidence", "role_eq",
    "visual", "dependency", "evidence_tool",
})

# 层叠规则（自低向高）：右侧功能登记时必须已含其全部左侧功能。
_FEATURE_LAYER_REQUIREMENTS: dict[str, frozenset[str]] = {
    "dependency": frozenset({"evidence_tool"}),
    "visual": frozenset({"dependency", "evidence_tool"}),
    "role_eq": frozenset({"visual", "dependency", "evidence_tool"}),
    "role_eq_evidence": frozenset({"role_eq", "visual", "dependency", "evidence_tool"}),
    "strict": frozenset({"role_eq_evidence", "role_eq", "visual", "dependency", "evidence_tool"}),
    "patch_repair": frozenset({"strict"}),
}


def prompt_version_features(prompt_version: str) -> frozenset[str] | None:
    """登记处唯一查询入口：返回版本登记的功能集。

    空集 = 明确登记为无工具（单次调用）；None = 未登记。能力以本表
    为准，不按版本名（含tools-vN后缀）推断。
    """
    features = _PROMPT_VERSION_FEATURES.get(str(prompt_version or "").strip())
    return None if features is None else features


def assert_prompt_version_reachable(prompt_version: str, *, evidence_tool_factory: Any) -> None:
    """R27-01提交前可达性预检：在作业进入队列前核对能力合同可兑现。

    - 未登记的mapping版本拒收（新版本必须先在此登记，杜绝绕过登记处）；
    - 登记为取证工具循环而本部署未配置冻结证据工具集时显式失败，
      不允许带工具合同的作业入队后静默降级为单次调用或运行期崩溃。
    无工具合同总是可达（单次调用不需要额外设施），预检直接放行。
    """
    features = prompt_version_features(prompt_version)
    if features is None:
        raise ValueError(
            "mapping prompt version is not registered in evidence_tool_contract: "
            f"{str(prompt_version or '').strip()}"
        )
    if "evidence_tool" in features and evidence_tool_factory is None:
        raise ValueError(
            "prompt version contract claims evidence tools but the frozen "
            f"evidence toolset is not configured: {str(prompt_version or '').strip()}"
        )


def check_prompt_version_tool_closure(dispatch_versions: Iterable[str] = ()) -> None:
    """R27-01启动闭包：派发集与登记表必须互相闭合，违约即失败。

    - 派发集（服务默认/门常量/裁决现行）中每个版本都已显式登记；
    - 每个登记行的功能键已知（防拼写漂移导致功能静默消失）；
    - 层叠规则成立（低层功能是高层功能的真子集前提）。
    "声称的工具能解析"在登记层面的含义：声称evidence_tool的版本必然
    出现在EVIDENCE_TOOL_PROMPT_VERSIONS且被工具循环消费；运行期工具
    名解析由回归测试对真实MonitoringEvidenceToolset验证。
    """
    problems: list[str] = []
    for version in dispatch_versions:
        if str(version or "").strip() not in _PROMPT_VERSION_FEATURES:
            problems.append(f"dispatchable version not registered: {version}")
    for version, features in _PROMPT_VERSION_FEATURES.items():
        unknown = features - KNOWN_PROMPT_VERSION_FEATURES
        if unknown:
            problems.append(f"{version}: unknown feature keys {sorted(unknown)}")
        missing = set()
        for feature in features:
            missing |= _FEATURE_LAYER_REQUIREMENTS.get(feature, frozenset()) - features
        if missing:
            problems.append(f"{version}: layered features missing {sorted(missing)}")
    if problems:
        raise ValueError(
            "evidence_tool_contract closure violated: " + "; ".join(problems)
        )


def classify_tool_usage(prompt_version: str, evidence_read_count: int) -> str:
    """按登记合同×实际回执数做事后诚实分类（R27-01历史作业口径）。

    分类依据是实际evidence_reads回执数，不是版本名：只有
    "tool_loop_executed" 表示该作业确实做了工具取证；"tool_loop_idle"
    表示登记有工具合同但本次执行未发生任何工具读取，同样不得描述为
    已做自主取证。
    """
    features = prompt_version_features(prompt_version)
    if features is None:
        return "unregistered"
    if "evidence_tool" in features:
        return "tool_loop_executed" if evidence_read_count > 0 else "tool_loop_idle"
    return "single_call" if evidence_read_count <= 0 else "receipts_without_tool_contract"


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
