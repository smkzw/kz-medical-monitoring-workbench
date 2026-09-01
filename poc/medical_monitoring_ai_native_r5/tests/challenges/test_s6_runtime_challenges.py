"""Execute every frozen S6 challenge against the real offline runtime."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

import pytest

from mm_r5.s6_contracts import (
    build_audience_encoding_registry_mapping,
    build_density_semantic_zoom_contract,
    build_performance_registry,
    build_protected_boundary,
    s6_as_mapping,
)
from mm_r5.s6_accessibility import build_keyboard_contract
from mm_r5.s6_validator import (
    validate_audience_encoding_registry,
    validate_density_semantic_zoom_contract,
    validate_deep_link_identity,
    validate_keyboard_contract,
    validate_performance_profile,
    validate_protected_boundary,
    validate_return_context,
)
from s6_runtime_fixtures import (
    build_deep_link,
    build_return_context_fixture,
    build_subject_packet,
)


_WORKSPACE = Path(__file__).resolve().parents[4]
_ARTIFACTS = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1"
)
_REGISTRY_PATH = _ARTIFACTS / "challenge_registry.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows() -> list[dict]:
    return _json(_REGISTRY_PATH)["rows"]


def _pointer(path: str) -> list[str]:
    return [
        part.replace("~1", "/").replace("~0", "~")
        for part in path.strip("/").split("/")
        if part
    ]


def _set_parts(mapping: dict, parts: list[str], value) -> None:
    target = mapping
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    leaf = parts[-1]
    if isinstance(target, list):
        target[int(leaf)] = value
    else:
        target[leaf] = value


def _apply_mutation(candidate: dict, path: str, value) -> None:
    parts = _pointer(path)
    if parts.pop(0) != "candidate":
        raise AssertionError(f"challenge path is not candidate-scoped: {path}")
    _set_parts(candidate, parts, value)


@lru_cache(maxsize=1)
def _subject():
    return build_subject_packet()


@lru_cache(maxsize=1)
def _deep_link_mapping() -> dict:
    return s6_as_mapping(build_deep_link())


@lru_cache(maxsize=1)
def _return_context_mapping() -> dict:
    return s6_as_mapping(build_return_context_fixture())


def _candidate_for(row: dict) -> tuple[dict, object]:
    category = row["category"]
    mutation_path = row["single_mutation"]["path"]
    mutation_value = row["single_mutation"]["value"]

    if category in {"deep_link_identity", "deep_link_no_nearest_fallback"}:
        candidate = {"deep_link_identity": copy.deepcopy(_deep_link_mapping())}
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_deep_link_identity

    if category == "canonical_return_context":
        candidate = {"return_context": copy.deepcopy(_return_context_mapping())}
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_return_context

    if category == "density_semantic_zoom":
        candidate = {"density_semantic_zoom": build_density_semantic_zoom_contract()}
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_density_semantic_zoom_contract

    if category == "keyboard_non_mutating":
        candidate = s6_as_mapping(build_keyboard_contract())
        parts = _pointer(mutation_path)
        if parts[:2] != ["candidate", "keyboard_contract"]:
            raise AssertionError(f"unexpected keyboard path: {mutation_path}")
        _set_parts(candidate, parts[2:], mutation_value)
        return candidate, validate_keyboard_contract

    if category == "non_colour_encoding":
        candidate = {"audience_encoding": build_audience_encoding_registry_mapping()}
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_audience_encoding_registry

    if category == "performance_corpus_identity":
        candidate = {"performance": build_performance_registry()}
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_performance_profile

    if category == "protected_boundary":
        candidate = build_protected_boundary()
        _apply_mutation(candidate, mutation_path, mutation_value)
        return candidate, validate_protected_boundary

    raise AssertionError(f"unhandled S6 challenge category: {category}")


def test_registry_has_exactly_104_frozen_metadata_rows() -> None:
    registry = _json(_REGISTRY_PATH)
    rows = registry["rows"]
    assert registry["status"] == "metadata_only"
    assert registry["row_count"] == 104
    assert len(rows) == 104
    assert len({row["challenge_id"] for row in rows}) == 104
    assert len({
        json.dumps(row["single_mutation"], ensure_ascii=False, sort_keys=True)
        for row in rows
    }) == 104
    assert registry["authority_source_forbidden"] == [
        "fixture_text", "fixture_count", "case_id", "filename", "unbound_hash",
        "nearest_record", "ui_state", "candidate_output",
    ]
    assert registry["category_counts"] == {
        "deep_link_identity": 21,
        "deep_link_no_nearest_fallback": 5,
        "canonical_return_context": 18,
        "density_semantic_zoom": 14,
        "keyboard_non_mutating": 16,
        "non_colour_encoding": 11,
        "performance_corpus_identity": 13,
        "protected_boundary": 6,
    }
    for row in rows:
        assert set(registry["row_contract"]["required_fields"]) <= set(row)
        assert row["single_mutation"]["op"] == "replace"
        assert row["test_metadata_only"] is True
        assert row["expected_outcome"] == f"reject:{row['expected_error']}"
        assert row["expected_projection"] == registry["row_contract"][
            "expected_projection_by_category"
        ][row["category"]]


@pytest.mark.parametrize("row", _rows(), ids=lambda row: row["challenge_id"])
def test_every_registry_row_reaches_the_real_validator(row: dict) -> None:
    """The registry supplies one mutation; the runtime supplies the result."""
    candidate, validator = _candidate_for(row)
    if row["category"] in {"deep_link_identity", "deep_link_no_nearest_fallback"}:
        result = validator(candidate, _subject(), expected=_deep_link_mapping())
    elif row["category"] == "canonical_return_context":
        result = validator(candidate, _subject(), expected=_return_context_mapping())
    elif row["category"] in {
        "density_semantic_zoom", "keyboard_non_mutating", "non_colour_encoding",
        "performance_corpus_identity", "protected_boundary",
    }:
        result = validator(candidate)
    else:  # pragma: no cover - _candidate_for is exhaustive
        raise AssertionError(row["category"])
    assert result.primary_code == row["expected_error"], row["challenge_id"]
    assert result.projection == row["expected_projection"], row["challenge_id"]
    assert result.ok is False, row["challenge_id"]
