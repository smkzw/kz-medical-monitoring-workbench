"""Chinese structured prompt contract for rule-candidate extraction.

Discovery review §4.3 + context §Scope: the model only receives the user's
original Chinese rule text, the current project's available field catalog, and
necessary business context.  It never receives simulation records.

This module builds the deterministic prompt payload that an executor sends to
a user-configured model/harness, and binds the schema revision + catalog
fingerprint so the same input always yields a stable, reproducible request.

The prompt is **vendor/model neutral**: it contains no provider name, model
selector, API route, or project path.  Business logic carries no project names
or listing-specific table/field names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .catalog import FieldCatalog
from .schema import schema_content_hash, schema_json

__all__ = [
    "SYSTEM_PROMPT_ZH",
    "RULE_EXTRACTION_PROMPT_TEMPLATE_ZH",
    "PromptPayload",
    "build_prompt",
    "prompt_payload_hash",
]

#: Chinese system prompt.  Vendor-neutral; instructs the model to emit exactly
#: one JSON object conforming to the schema, never to invent fields, and to
#: surface ambiguities as open questions rather than guessing.
SYSTEM_PROMPT_ZH = (
    "你是一名服务于资深医学监察员的医学风险规则结构化助手。\n"
    "你的唯一任务是把用户用中文描述的风险规则，严格按照给定的 JSON Schema "
    "拆解为结构化候选条件。\n"
    "\n"
    "铁律（违反任意一条即判定失败，不会被自动修复）：\n"
    "1. 只能输出恰好一个 JSON 对象，不得输出 Markdown 代码围栏、散文说明、"
    "注释或多个 JSON 值。\n"
    "2. 不得新增 Schema 之外的任何键；每个层级的额外属性都会被拒绝。\n"
    "3. 每个条件的 field 必须命中下方提供的「可用字段目录」中的一个字段；"
    "目录之外的字段一律视为未知，禁止凭常识发明（例如不得自行编造字段）。\n"
    "4. 每个条件的 operator 必须取自字段目录为该字段声明的允许操作符；"
    "threshold 的值类型必须与字段目录和操作符兼容。\n"
    "5. 每个条件必须填写非空的 extracted_from，引用用户原文中对应的中文字句，"
    "用于人工审核追溯。\n"
    "6. logical_combination 只能是 all 或 any；severity_hint、domain_hint "
    "只能取 Schema 允许的枚举值（可为空字符串）。\n"
    "7. 若存在无法消解的歧义、缺失信息或需要用户确认的假设，必须放入 "
    "open_questions；任何非空 open_questions 都会阻断结构化草稿的生成，"
    "等待用户澄清，不得自行猜测后隐藏。\n"
    "8. 你不能直接创建、激活或修改任何规则；你只输出候选解释。"
)

#: User-turn template.  The model sees: schema, field catalog, business
#: context (optional), and the original Chinese rule text.  It never sees
#: simulation records.
RULE_EXTRACTION_PROMPT_TEMPLATE_ZH = (
    "请将下面的中文风险规则拆解为一个符合 JSON Schema 的结构化候选对象。\n"
    "\n"
    "== JSON Schema（唯一权威合同，$id 与 $schema 标明版本）==\n"
    "{schema_json}\n"
    "\n"
    "== 可用字段目录（fingerprint={catalog_fingerprint}）==\n"
    "条件 field 只能取自下列字段；每个字段标注了允许的 operator 与 threshold "
    "值类型：\n"
    "{catalog_block}\n"
    "\n"
    "== 业务上下文（可选）==\n"
    "{business_context}\n"
    "\n"
    "== 用户原始中文规则 ==\n"
    "{rule_text}\n"
    "\n"
    "== 输出要求 ==\n"
    "只输出一个 JSON 对象，键与值严格符合上面的 JSON Schema 与字段目录。"
    "不要输出任何额外文字。"
)


@dataclass(frozen=True)
class PromptPayload:
    """The fully-built, deterministic prompt payload for one extraction call.

    Everything needed to reproduce the exact request: system prompt, user
    prompt, bound schema hash, catalog fingerprint, original rule text, and
    optional business context.  No vendor/model/credentials.
    """
    system_prompt: str
    user_prompt: str
    schema_hash: str
    catalog_fingerprint: str
    rule_text: str
    business_context: str
    schema_json: str

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "schema_hash": self.schema_hash,
            "catalog_fingerprint": self.catalog_fingerprint,
            "rule_text": self.rule_text,
            "business_context": self.business_context,
            "schema_json": self.schema_json,
        }


def _catalog_block(catalog: FieldCatalog) -> str:
    lines: List[str] = []
    for spec in catalog:
        ops = ", ".join(spec.allowed_operators)
        lines.append(
            f"- {spec.name}（{spec.label_zh}，域 {spec.domain}）："
            f"值类型={spec.value_type}；允许操作符={ops}。"
            f"说明：{spec.description_zh}"
        )
    return "\n".join(lines)


def build_prompt(
    rule_text: str,
    catalog: FieldCatalog,
    *,
    business_context: str = "",
) -> PromptPayload:
    """Build the deterministic Chinese prompt payload for one rule.

    ``rule_text`` is the user's original Chinese rule; ``catalog`` is the
    explicit field catalog the model may reference (there is no built-in
    default); ``business_context`` is optional, must be vendor/project-path
    free (the caller is responsible).  No simulation records are ever
    included.
    """
    if not isinstance(rule_text, str) or not rule_text.strip():
        raise ValueError("rule_text must be a non-empty string")
    if not isinstance(catalog, FieldCatalog):
        raise ValueError("catalog must be a FieldCatalog")
    if business_context is None:
        business_context = ""
    if not isinstance(business_context, str):
        raise ValueError("business_context must be a string")

    sch_json = schema_json(indent=2)
    sch_hash = schema_content_hash()
    cat_block = _catalog_block(catalog)

    user_prompt = RULE_EXTRACTION_PROMPT_TEMPLATE_ZH.format(
        schema_json=sch_json,
        catalog_fingerprint=catalog.fingerprint,
        catalog_block=cat_block,
        business_context=business_context if business_context.strip() else "（无）",
        rule_text=rule_text,
    )

    return PromptPayload(
        system_prompt=SYSTEM_PROMPT_ZH,
        user_prompt=user_prompt,
        schema_hash=sch_hash,
        catalog_fingerprint=catalog.fingerprint,
        rule_text=rule_text,
        business_context=business_context,
        schema_json=sch_json,
    )


def prompt_payload_hash(payload: PromptPayload) -> str:
    """Stable SHA-256 of the canonical prompt payload."""
    import hashlib
    import json

    canon = json.dumps(
        payload.to_public_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
