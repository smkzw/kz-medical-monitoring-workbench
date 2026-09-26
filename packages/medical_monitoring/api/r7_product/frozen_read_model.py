"""Frozen read model for published R7 results（W01-R26，20260926）.

发布时把当次构建出的R5 publication packet快照为冻结read model：经Store
artifact+CAS落库，发布行以``frozen_read_model_artifact_id``/
``frozen_read_model_sha256``两个引用列绑定。读取时优先反序列化该快照并
按冻结sha256校验，digest校验对象从"当下重算"换成"发布时快照"，因此投影
代码升级后旧result token仍能打开发布时的正确历史，而不会因当前代码重算
digest不一致被拒绝。无引用的存量发布行走既有重建比对路径。

文档结构（read_model_version=r7-frozen-read-model-v1）：
- ``projection_version``：发布manifest digest，随发布记录，不从当前默认
  配置推断（W01动作2）；
- ``authority_anchor``：发布packet的identity/digest/site_refs，读取侧
  与发布行同名锚点比对（校验强度不降）；
- ``member_refs``：发布packet六个authority集合的稳定引用，冻结后用于
  桥接引用与product引用的一致性比对；
- ``product_packet``：完整product packet的类型化序列化，读取侧还原后
  供R5ProductAdapter按发布时内容服务公开视图。
"""

from __future__ import annotations

import dataclasses
import datetime as _datetime
from hashlib import sha256
import importlib
import json
from typing import Any, Mapping, Optional, Tuple

from ...domain.execution import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    NodeType,
)
from .contracts import ProductPublicationError

READ_MODEL_VERSION = "r7-frozen-read-model-v1"
FROZEN_READ_MODEL_ARTIFACT_TYPE = "r7_frozen_read_model"

# 与读取侧(result_context_service)的桥接/产品引用比对表保持同一键序。
_MEMBER_REF_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("sites", "site_ref"),
    ("subjects", "subject_ref"),
    ("events", "event_ref"),
    ("visits", "visit_ref"),
    ("risks", "risk_ref"),
    ("sources", "locator_ref"),
)

# 还原时的类型来源白名单：冻结read model是服务端读取通道，product
# packet的类型必须来自本代码库的投影契约模块；其余一律拒绝。
_ALLOWED_TYPE_MODULE_PREFIXES = (
    "packages.medical_monitoring.",
    "medical_monitoring.",
)


def _canonical_document_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def read_model_sha256(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_document_bytes(document)).hexdigest()


def _encode(value: Any) -> Any:
    if isinstance(value, _datetime.date):
        return {"__date__": value.isoformat()}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            "__dc__": f"{type(value).__module__}:{type(value).__qualname__}",
            "f": {
                field.name: _encode(getattr(value, field.name))
                for field in dataclasses.fields(value)
            },
        }
    if isinstance(value, Mapping):
        return {str(key): _encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        # 本文档约定：序列仅在dataclass的Tuple[...]字段中出现，JSON数组
        # 统一还原为tuple；若未来出现真正的list/dict字段，__post_init__
        # 的类型校验会拒绝并转化为result_context_unavailable。
        return [_encode(item) for item in value]
    return value


def _decode(value: Any) -> Any:
    if isinstance(value, Mapping):
        tag = value.get("__dc__")
        if isinstance(tag, str):
            module_name, _, qualname = tag.partition(":")
            if not module_name.startswith(_ALLOWED_TYPE_MODULE_PREFIXES):
                raise ProductPublicationError("result_context_unavailable")
            module = importlib.import_module(module_name)
            target: Any = module
            for part in qualname.split("."):
                target = getattr(target, part)
            if (
                not dataclasses.is_dataclass(target)
                or isinstance(target, type) is False
                or not getattr(
                    getattr(target, "__dataclass_params__", None),
                    "frozen",
                    False,
                )
            ):
                raise ProductPublicationError("result_context_unavailable")
            fields = value.get("f")
            if not isinstance(fields, Mapping):
                raise ProductPublicationError("result_context_unavailable")
            return target(
                **{str(key): _decode(item) for key, item in fields.items()}
            )
        if isinstance(value.get("__date__"), str):
            return _datetime.date.fromisoformat(str(value["__date__"]))
        raise ProductPublicationError("result_context_unavailable")
    if isinstance(value, list):
        return tuple(_decode(item) for item in value)
    return value


@dataclasses.dataclass(frozen=True)
class FrozenAuthorityMember:
    """发布packet成员的引用视图：读取侧只按引用属性比对集合一致性。"""

    site_ref: str = ""
    subject_ref: str = ""
    event_ref: str = ""
    visit_ref: str = ""
    risk_ref: str = ""
    locator_ref: str = ""


@dataclasses.dataclass(frozen=True)
class FrozenR5PublicationPacket:
    """冻结read model的读取视图，暴露与实时packet相同的属性面。"""

    packet_identity: str
    packet_digest: str
    site_refs: Tuple[str, ...]
    product_packet: Any
    sites: Tuple[FrozenAuthorityMember, ...]
    subjects: Tuple[FrozenAuthorityMember, ...]
    events: Tuple[FrozenAuthorityMember, ...]
    visits: Tuple[FrozenAuthorityMember, ...]
    risks: Tuple[FrozenAuthorityMember, ...]
    sources: Tuple[FrozenAuthorityMember, ...]


def freeze_read_model_document(
    packet: Any,
    *,
    projection_version: str,
) -> dict[str, Any]:
    """把发布时构建的R5 publication packet快照为冻结read model文档。"""

    return {
        "read_model_version": READ_MODEL_VERSION,
        "projection_version": str(projection_version or ""),
        "authority_anchor": {
            "packet_identity": str(packet.packet_identity),
            "packet_digest": str(packet.packet_digest),
            "site_refs": sorted(str(item) for item in packet.site_refs),
        },
        "member_refs": {
            name: sorted(
                str(getattr(item, ref))
                for item in tuple(getattr(packet, name))
            )
            for name, ref in _MEMBER_REF_COLUMNS
        },
        "product_packet": _encode(packet.product_packet),
    }


def store_frozen_read_model(
    store: Any,
    *,
    run_id: str,
    document: Mapping[str, Any],
) -> Tuple[str, str]:
    """经Store artifact+CAS落库；返回(artifact_id, 文档sha256)。"""

    envelope = ArtifactEnvelope(
        artifact_type=FROZEN_READ_MODEL_ARTIFACT_TYPE,
        version=READ_MODEL_VERSION,
        run_id=str(run_id),
        node_id="r7-result-publication",
        node_type=NodeType.PROJECTION,
        payload=dict(document),
        completeness=ArtifactCompleteness.COMPLETE,
    )
    staged = store.stage_artifact(envelope)
    committed = store.commit_artifact(staged, envelope)
    return committed.artifact_id, read_model_sha256(document)


def load_frozen_read_model_document(
    store: Any,
    publication: Any,
) -> Optional[dict[str, Any]]:
    """按发布行引用读取冻结read model；无引用返回None。

    任何损坏（CAS校验失败、sha256不符、版本不符）都fail-closed为
    result_context_unavailable，绝不回退live或重建顶替。
    """

    artifact_id = publication.frozen_read_model_artifact_id
    expected_sha256 = publication.frozen_read_model_sha256
    if not artifact_id or not expected_sha256:
        return None
    try:
        if not store.verify_artifact(str(artifact_id)):
            raise ProductPublicationError("result_context_unavailable")
        envelope = store.get_artifact(str(artifact_id))
    except ProductPublicationError:
        raise
    except Exception as exc:
        raise ProductPublicationError("result_context_unavailable") from exc
    document = envelope.payload
    if not isinstance(document, Mapping):
        raise ProductPublicationError("result_context_unavailable")
    if read_model_sha256(document) != str(expected_sha256):
        raise ProductPublicationError("result_context_unavailable")
    if document.get("read_model_version") != READ_MODEL_VERSION:
        raise ProductPublicationError("result_context_unavailable")
    return dict(document)


def restore_frozen_packet(document: Mapping[str, Any]) -> FrozenR5PublicationPacket:
    """还原冻结read model为读取视图；损坏一律result_context_unavailable。"""

    try:
        anchor = document["authority_anchor"]
        product_packet = _decode(document["product_packet"])
        members = {
            name: tuple(
                FrozenAuthorityMember(**{ref: str(item)})
                for item in document["member_refs"][name]
            )
            for name, ref in _MEMBER_REF_COLUMNS
        }
        return FrozenR5PublicationPacket(
            packet_identity=str(anchor["packet_identity"]),
            packet_digest=str(anchor["packet_digest"]),
            site_refs=tuple(str(item) for item in anchor["site_refs"]),
            product_packet=product_packet,
            **members,
        )
    except ProductPublicationError:
        raise
    except Exception as exc:
        raise ProductPublicationError("result_context_unavailable") from exc


__all__ = [
    "FROZEN_READ_MODEL_ARTIFACT_TYPE",
    "FrozenAuthorityMember",
    "FrozenR5PublicationPacket",
    "READ_MODEL_VERSION",
    "freeze_read_model_document",
    "load_frozen_read_model_document",
    "read_model_sha256",
    "restore_frozen_packet",
    "store_frozen_read_model",
]
