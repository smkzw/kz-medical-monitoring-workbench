"""Deterministic offline fixtures for the S5 runtime tests.

The base graphs are the accepted typed ``AuthorityBundleV02`` fixtures.  The
optional replay helpers decode only the accepted synthetic full-graph registry
and reseal each transformed typed bundle before it reaches a producer; no
candidate packet is ever used as authority.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from mm_r5 import public_authority_common as common
from mm_r5.s5_authority_adapter import (
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
)
from mm_r5.s5_projection import project_subject_workspace

try:
    from public_authority_runtime_fixtures import (
        build_aemh_authority_bundle,
        build_subject_authority_bundle,
    )
except ImportError:  # pragma: no cover - package import fallback
    from .public_authority_runtime_fixtures import (
        build_aemh_authority_bundle,
        build_subject_authority_bundle,
    )


def build_subject_temporal_authority_bundle() -> common.AuthorityBundleV02:
    return build_subject_authority_bundle()


def build_aemh_match_history_authority_bundle() -> common.AuthorityBundleV02:
    return build_aemh_authority_bundle()


def build_subject_packet():
    return adapt_subject_temporal_authority(build_subject_authority_bundle())


def build_aemh_packet():
    return adapt_aemh_match_history_authority(build_aemh_authority_bundle())


def build_subject_temporal_packet():
    return build_subject_packet()


def build_aemh_match_history_packet():
    return build_aemh_packet()


def build_subject_workspace():
    return project_subject_workspace(build_subject_packet(), build_aemh_packet())


def build_valid_subject_authority() -> common.AuthorityBundleV02:
    return build_subject_authority_bundle()


def build_valid_aemh_authority() -> common.AuthorityBundleV02:
    return build_aemh_authority_bundle()


def build_valid_subject_packet():
    return build_subject_packet()


def build_valid_aemh_packet():
    return build_aemh_packet()


def _decode(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Literal:
        return value
    if origin is Union:
        args = get_args(annotation)
        for item in args:
            if item is type(None) and value is None:
                return None
            if item is not type(None):
                try:
                    return _decode(item, value)
                except (KeyError, TypeError, ValueError):
                    pass
        return value
    if origin in (tuple, list):
        args = get_args(annotation)
        item_type = args[0] if args else Any
        return tuple(_decode(item_type, item) for item in value)
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        hints = get_type_hints(annotation)
        return annotation(**{
            field.name: _decode(hints[field.name], value[field.name])
            for field in dataclasses.fields(annotation)
        })
    return value


def _authority_from_mapping(value: dict[str, Any]) -> common.AuthorityBundleV02:
    return _decode(common.AuthorityBundleV02, value)


def _json_mapping(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _json_mapping(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [_json_mapping(item) for item in value]
    if isinstance(value, list):
        return [_json_mapping(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_mapping(item) for key, item in value.items()}
    return value


def _set_path(mapping: dict[str, Any], path: str, value: Any) -> None:
    parts = [item for item in path.strip("/").split("/") if item]
    target: Any = mapping
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    leaf = parts[-1]
    if isinstance(target, list):
        target[int(leaf)] = value
    else:
        target[leaf] = value


def _reseal(value: dict[str, Any]) -> common.AuthorityBundleV02:
    value = json.loads(json.dumps(value, ensure_ascii=False))
    value["bundle_content_identity"] = "0" * 64
    identity_input = {key: item for key, item in value.items() if key != "bundle_content_identity"}
    value["bundle_content_identity"] = common.canonical_sha256(identity_input)
    return _authority_from_mapping(value)


def _registry() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    path = root / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def accepted_public_graph_replay(case_id: str) -> common.AuthorityBundleV02:
    """Return one of the ten accepted synthetic public-producer replay inputs."""
    registry = _registry()
    row = next((item for item in registry["positive_paths"] if item["case_id"] == case_id), None)
    if row is None:
        raise KeyError(case_id)
    base = registry["positive_base_inputs"][row["authority_input_ref"]]
    value = json.loads(json.dumps(base, ensure_ascii=False))
    for operation in row["source_transformation"]:
        path = operation["path"]
        replacement = operation.get("post_value", operation.get("value"))
        _set_path(value, path, replacement)
    return _reseal(value)


def build_public_graph_replay(case_id: str) -> common.AuthorityBundleV02:
    return accepted_public_graph_replay(case_id)


def accepted_public_graph_replay_cases() -> tuple[str, ...]:
    return tuple(item["case_id"] for item in _registry()["positive_paths"])


def replay_packet(case_id: str):
    source = accepted_public_graph_replay(case_id)
    if source.target_contract == common.SUBJECT_CONTRACT_ID:
        return adapt_subject_temporal_authority(source)
    return adapt_aemh_match_history_authority(source)


def build_subject_replay_packet(case_id: str):
    source = accepted_public_graph_replay(case_id)
    if source.target_contract != common.SUBJECT_CONTRACT_ID:
        raise ValueError(f"{case_id} is not a subject replay")
    return adapt_subject_temporal_authority(source)


def build_aemh_replay_packet(case_id: str):
    source = accepted_public_graph_replay(case_id)
    if source.target_contract != common.AEMH_CONTRACT_ID:
        raise ValueError(f"{case_id} is not an AEMH replay")
    return adapt_aemh_match_history_authority(source)


__all__ = [
    "build_subject_authority_bundle", "build_aemh_authority_bundle",
    "build_subject_temporal_authority_bundle", "build_aemh_match_history_authority_bundle",
    "build_subject_packet", "build_aemh_packet", "build_subject_temporal_packet",
    "build_aemh_match_history_packet", "build_subject_workspace",
    "build_valid_subject_authority", "build_valid_aemh_authority",
    "build_valid_subject_packet", "build_valid_aemh_packet",
    "accepted_public_graph_replay", "build_public_graph_replay",
    "accepted_public_graph_replay_cases", "replay_packet",
    "build_subject_replay_packet", "build_aemh_replay_packet",
]
