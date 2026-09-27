"""B路线执行策略：语义工作单元 + 工具版本身份（默认off）。

开关解析走 ``service.runtime_resolver().env``，与
``AdmissionMappingPipeline._listing_mapping_chunk_size`` 同一访问模式：

- ``WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY``：空值或未知值一律=off
  （解析为 ``None``，提交路径保持原样）；``semantic_evidence``=on。
- ``WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS``：on 时的可选域白名单
  （逗号/空白分隔）；缺省（空）=全域。

on 的语义：接缝处的整次提交改走B路线——

1. 每个覆盖域先 ``partition_metadata_fields`` 分离技术元数据字段；
2. 业务字段按 ``field_profile`` 自带 ``relationships``（冻结的同表配对
   证据）做确定性连通分量分组，无任何硬编码字段名词表；超过单元上限的
   分量按确定性顺序切分；
3. 每个单元经同一个 ``submit_listing_field_mapping_chunks`` 提交：单元
   字段 ≤12 ⇒ 每单元恰一片（``0001-of-0001``），满足该函数 1..12 硬合同；
   单元业务键前缀 ``{cohort前缀}:{batch_id}:u{seq:02d}``，最终键形
   ``listing-field-mapping:{batch_id}:u01:{batch_id}:{domain}:0001-of-0001``
   （batch_id 两现：单元前缀已含、chunks 拼装段序再拼一次），仍以
   ``{cohort前缀}:{attempt_id}:`` 为锚点、全前缀唯一；
4. 每个含技术元数据的域另发恰好一个元数据-only确定性作业
   （workbench-system 快路径）：显式传本cohort的B版 ``prompt_version``
   （N5，留空会默认v19并跌出 ``_latest_job_cohort`` 的同版本投影），并
   显式补 ``full_profile_sha256``（N2，单发不自动补键，缺键会使
   ``identity(required=True)`` 对整个前缀的候选投影抛 mapping_bridge_failed）。

B版 prompt_version 是本策略的工具执行身份：主=
``monitoring-listing-field-mapping-v20-tools-v1``，盲核=
``monitoring-listing-field-mapping-verifier-v2-tools-v1``，两者均登记于
evidence_tool_contract 的 evidence_tool 功能集；单元与确定性作业同版本。

域白名单是显式的范围声明：范围外的域不会被本策略提交（对照运行以此
界定规模）；需要对全批运行必须留空（缺省全域）。
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from .mapping_bridge import MappingHarnessInput
from .mapping_gate import (
    MONITORING_MAPPING_COHORT_PRIMARY,
    MONITORING_MAPPING_COHORT_VERIFIER,
    MonitoringMappingCohortContract,
)

STRATEGY_EXECUTION_ENV = "WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY"
STRATEGY_DOMAINS_ENV = "WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS"
SEMANTIC_EVIDENCE_STRATEGY = "semantic_evidence"
# B路线的工具版本身份：两个版本都必须保持登记在
# evidence_tool_contract 的 evidence_tool 功能集；改身份=新登记行，
# 不得复用无工具的现行默认（主v19/盲核v8-tools-v6）。
SEMANTIC_EVIDENCE_PROMPT_VERSIONS = {
    MONITORING_MAPPING_COHORT_PRIMARY: (
        "monitoring-listing-field-mapping-v20-tools-v1"
    ),
    MONITORING_MAPPING_COHORT_VERIFIER: (
        "monitoring-listing-field-mapping-verifier-v2-tools-v1"
    ),
}
# submit_listing_field_mapping_chunks 的 1..12 硬合同上限。单元按此切分，
# 每单元恰为一片（chunk_total=1），与 DEFAULT/MAX_LISTING_MAPPING_CHUNK_SIZE
# 的既有边界一致。
SEMANTIC_UNIT_FIELD_LIMIT = 12


class MappingExecutionStrategyError(ValueError):
    """B路线执行策略合同违约（fail-closed）。"""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class MappingExecutionStrategy:
    """已解析的B路线开关状态；``None`` 语义由解析函数返回值表达。"""

    name: str
    # 空集=全域（缺省）；非空=显式白名单，范围外的域不提交。
    domains: frozenset

    def covers_domain(self, domain: str) -> bool:
        return not self.domains or str(domain).strip() in self.domains


@dataclass(frozen=True)
class SemanticWorkUnit:
    """一个语义提交单元：同域、同连通分量的 ≤12 个业务字段。"""

    seq: int
    domain: str
    fields: Tuple[Mapping[str, Any], ...]


def _strategy_env(service: Any, name: str) -> str:
    try:
        runtime = service.runtime_resolver()
        return str(
            (getattr(runtime, "env", {}) or {}).get(name, "")
        ).strip()
    except Exception:
        # 环境不可读=开关关闭；绝不因解析层异常打开B路线。
        return ""


def resolve_mapping_execution_strategy(
    service: Any,
) -> Optional[MappingExecutionStrategy]:
    """解析执行策略开关；空/未知=off（``None``），semantic_evidence=on。"""

    raw = _strategy_env(service, STRATEGY_EXECUTION_ENV)
    if raw.casefold() != SEMANTIC_EVIDENCE_STRATEGY:
        return None
    raw_domains = _strategy_env(service, STRATEGY_DOMAINS_ENV)
    normalized = (
        raw_domains.replace("；", ",").replace(";", ",").replace(",", " ")
    )
    domains = frozenset(
        token for token in normalized.split() if token
    )
    return MappingExecutionStrategy(
        name=SEMANTIC_EVIDENCE_STRATEGY,
        domains=domains,
    )


def _field_name(field: Mapping[str, Any]) -> str:
    return str(field.get("field", "")).strip()


def _field_sort_key(field: Mapping[str, Any]) -> tuple:
    name = _field_name(field)
    return (name.casefold(), name)


def _strategy_fields_by_domain(
    field_profile: Mapping[str, Any],
    strategy: MappingExecutionStrategy,
) -> Dict[str, list]:
    """按域收集白名单覆盖内的字段，域内按 (casefold, 原名) 确定性排序。"""

    grouped: Dict[str, list] = {}
    for field in field_profile.get("fields") or []:
        domain = str(field.get("domain", "")).strip()
        if domain and strategy.covers_domain(domain):
            grouped.setdefault(domain, []).append(field)
    return {
        domain: sorted(fields, key=_field_sort_key)
        for domain, fields in grouped.items()
    }


def _component_blocks(
    sorted_fields: list,
    relationships,
    domain: str,
    limit: int,
) -> list:
    """同一域内按 relationships 做连通分量，再按确定性顺序切 ≤limit 块。

    分量划分与关系遍历顺序无关；分量按其最小成员在排序列表中的先后
    排序，块保持分量内排序——同一输入永远得到同一单元序列。
    """

    parent = {_field_name(field): _field_name(field) for field in sorted_fields}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for relationship in relationships or []:
        if str(relationship.get("domain", "")).strip() != domain:
            continue
        left = str(relationship.get("left_field", "")).strip()
        right = str(relationship.get("right_field", "")).strip()
        if left != right and left in parent and right in parent:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root
    groups: Dict[str, list] = {}
    for field in sorted_fields:
        groups.setdefault(find(_field_name(field)), []).append(field)
    blocks: list = []
    for members in groups.values():
        for start in range(0, len(members), limit):
            blocks.append(tuple(members[start : start + limit]))
    return blocks


def semantic_work_units(
    field_profile: Mapping[str, Any],
    *,
    strategy: MappingExecutionStrategy,
) -> Tuple[Tuple[SemanticWorkUnit, ...], Dict[str, Tuple[Mapping[str, Any], ...]]]:
    """把白名单覆盖域的字段确定性切分为语义单元 + 每域元数据组。

    覆盖盖性由构造保证：单元字段 ∪ 该域元数据字段 = 该域全部字段，
    每个字段恰出现一次；单元字段数 ≤ SEMANTIC_UNIT_FIELD_LIMIT。
    """

    from services.api.app.monitoring_deterministic_metadata_mapping import (
        partition_metadata_fields,
    )

    fields_by_domain = _strategy_fields_by_domain(field_profile, strategy)
    relationships = field_profile.get("relationships") or []
    units: list = []
    deterministic: Dict[str, Tuple[Mapping[str, Any], ...]] = {}
    seq = 0
    for domain in sorted(fields_by_domain, key=lambda value: (value.casefold(), value)):
        domain_fields = fields_by_domain[domain]
        metadata, business = partition_metadata_fields(domain_fields)
        deterministic[domain] = tuple(
            deepcopy(field) for field, _decision in metadata
        )
        for block in _component_blocks(
            list(business),
            relationships,
            domain,
            SEMANTIC_UNIT_FIELD_LIMIT,
        ):
            seq += 1
            units.append(
                SemanticWorkUnit(
                    seq=seq,
                    domain=domain,
                    fields=tuple(deepcopy(field) for field in block),
                )
            )
    return tuple(units), deterministic


# 与 chunks 的顶层排除集一致（monitoring_ai_service chunk_profile 拷贝）；
# table_bindings 必须保留：字段的 table_binding_id 依赖它过稳定身份校验，
# chunks 会在片内再按域过滤。
_PROFILE_DROP_KEYS = frozenset({
    "fields",
    "relationships",
    "treatment_identity_bindings",
    "table_field_order",
})


def _restricted_profile_copy(
    field_profile: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in field_profile.items()
        if key not in _PROFILE_DROP_KEYS
    }


def _domain_identity_bindings(
    field_profile: Mapping[str, Any],
    domain: str,
) -> list:
    return [
        deepcopy(binding)
        for binding in field_profile.get("treatment_identity_bindings") or []
        if str(binding.get("target_domain", "")).strip() == domain
    ]


def _unit_profile(
    field_profile: Mapping[str, Any],
    unit: SemanticWorkUnit,
) -> Dict[str, Any]:
    profile = _restricted_profile_copy(field_profile)
    unit_names = {_field_name(field) for field in unit.fields}
    profile["fields"] = [deepcopy(field) for field in unit.fields]
    # 只保留两端都在本单元内的同域关系：chunks 会按片再过滤，而提交
    # 校验要求关系字段必须落在当前 profile 的字段对内。
    profile["relationships"] = [
        deepcopy(relationship)
        for relationship in field_profile.get("relationships") or []
        if (
            str(relationship.get("domain", "")).strip() == unit.domain
            and {
                str(relationship.get("left_field", "")).strip(),
                str(relationship.get("right_field", "")).strip(),
            }
            <= unit_names
        )
    ]
    # 原始列序按单元过滤后保留（保持相对顺序），chunks 会将其作为
    # 只读结构上下文带进片内。
    for entry in field_profile.get("table_field_order") or []:
        if str(entry.get("domain", "")).strip() != unit.domain:
            continue
        order = [
            str(name).strip()
            for name in entry.get("field_order") or []
            if str(name).strip() in unit_names
        ]
        if order:
            profile["table_field_order"] = [
                {"domain": unit.domain, "field_order": order}
            ]
        break
    # 治疗身份绑定：仅保留本域绑定，并按 chunks 口径预声明来源对，
    # 使来源字段在单元外时提交校验仍可通过。
    bindings = _domain_identity_bindings(field_profile, unit.domain)
    if bindings:
        profile["treatment_identity_bindings"] = bindings
        profile["treatment_identity_binding_source_pairs"] = [
            {
                "domain": str(binding.get("source_domain", "")).strip(),
                "field": str(binding.get("source_field", "")).strip(),
            }
            for binding in bindings
        ]
    return profile


def _deterministic_profile(
    field_profile: Mapping[str, Any],
    domain: str,
    metadata_fields: Tuple[Mapping[str, Any], ...],
) -> Dict[str, Any]:
    profile = _restricted_profile_copy(field_profile)
    profile["fields"] = [deepcopy(field) for field in metadata_fields]
    profile["domain"] = domain
    # N2：单发不经 chunks，无 full_* 自动补键。identity(required=True)
    # 读取该键把本作业收进cohort投影；缺键会让整个前缀的候选投影抛
    # mapping_bridge_failed。取完整profile的profile_sha256，与单元作业
    # 的片内 full_profile_sha256 同源。
    profile["full_profile_sha256"] = str(field_profile["profile_sha256"])
    return profile


def _cohort_prompt_version(cohort: str) -> str:
    version = SEMANTIC_EVIDENCE_PROMPT_VERSIONS.get(str(cohort or "").strip())
    if not version:
        raise MappingExecutionStrategyError(
            "mapping_strategy_cohort_unsupported"
        )
    return version


def submit_semantic_evidence_units(
    *,
    service: Any,
    contract: MonitoringMappingCohortContract,
    harness_input: MappingHarnessInput,
    strategy: MappingExecutionStrategy,
    project_id: str,
    revision_factory,
) -> tuple:
    """B路线整次提交：语义单元逐个走 chunks + 每域一个确定性作业。

    单元与确定性作业共用同一份冻结 input_revision 和同一cohort B版
    prompt_version；返回作业元组，交回既有恢复/投影路径处理。
    """

    field_profile = harness_input.field_profile
    prompt_version = _cohort_prompt_version(contract.cohort)
    batch_id = str(field_profile["batch_id"]).strip()
    revision = revision_factory(harness_input.input_revision)
    units, deterministic = semantic_work_units(field_profile, strategy=strategy)
    jobs: list = []
    for unit in units:
        jobs.extend(
            service.submit_listing_field_mapping_chunks(
                project_id=project_id,
                input_revision=revision,
                field_profile=_unit_profile(field_profile, unit),
                chunk_size=SEMANTIC_UNIT_FIELD_LIMIT,
                prompt_version=prompt_version,
                business_key_prefix=(
                    f"{contract.business_key_prefix}:{batch_id}:"
                    f"u{unit.seq:02d}"
                ),
            )
        )
    for domain in sorted(deterministic, key=lambda value: (value.casefold(), value)):
        metadata_fields = deterministic[domain]
        if not metadata_fields:
            continue
        jobs.append(
            service.submit_listing_field_mapping(
                project_id=project_id,
                input_revision=revision,
                field_profile=_deterministic_profile(
                    field_profile,
                    domain,
                    metadata_fields,
                ),
                business_key=(
                    f"{contract.business_key_prefix}:{batch_id}:"
                    f"deterministic:{domain}"
                ),
                prompt_version=prompt_version,
            )
        )
    return tuple(jobs)


__all__ = [
    "MappingExecutionStrategy",
    "MappingExecutionStrategyError",
    "SEMANTIC_EVIDENCE_PROMPT_VERSIONS",
    "SEMANTIC_EVIDENCE_STRATEGY",
    "SEMANTIC_UNIT_FIELD_LIMIT",
    "STRATEGY_DOMAINS_ENV",
    "STRATEGY_EXECUTION_ENV",
    "SemanticWorkUnit",
    "resolve_mapping_execution_strategy",
    "semantic_work_units",
    "submit_semantic_evidence_units",
]
