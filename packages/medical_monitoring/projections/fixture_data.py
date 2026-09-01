"""Validated loader for the external medical-monitoring synthetic fixtures.

B5 contract: synthetic *data* lives in ``tests/fixtures/medical_monitoring/``
as JSON; this module is the only reader. Structural validation is a whitelist
(unknown keys, missing keys and wrong types fail closed with a Chinese
error); semantic validation stays with the existing dataclass constructors.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Tuple

FIXTURE_SCHEMA_ID = "mm-medical-monitoring-synthetic-fixture-v1"
FIXTURE_SCHEMA_VERSION = "1"
ENV_FIXTURES_DIR = "MM_SYNTHETIC_FIXTURES_DIR"
FIXTURES_DIRNAME = Path("tests") / "fixtures" / "medical_monitoring"

_R5_FIXTURE_KEYS = ("sources", "sites", "subjects", "events", "visits", "risks", "histories", "flow_stages", "flow_paths")
_R7_SETUP_KEYS = ("snapshots", "baselines")
_SYNTHETIC_RUN_KEYS = ("run_id", "mode", "execution_basis", "data_cutoff", "source_revision_id", "work_units")
_RUN_STRING_KEYS = ("run_id", "mode", "execution_basis", "data_cutoff", "source_revision_id")


class FixtureDataError(ValueError):
    """Raised when the synthetic fixture directory or file is missing or invalid."""


def fixtures_dir() -> Path:
    """Resolve the fixture directory without depending on the CWD.

    ``MM_SYNTHETIC_FIXTURES_DIR`` overrides the default (reserved for future
    packaged runs; tests are the only legitimate user in this phase).
    """

    override = os.environ.get(ENV_FIXTURES_DIR, "").strip()
    if override:
        return Path(override)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / FIXTURES_DIRNAME
        if candidate.is_dir():
            return candidate
    raise FixtureDataError(
        "未找到医学监查合成 fixture 目录："
        f"期望存在 {FIXTURES_DIRNAME}（可通过环境变量 {ENV_FIXTURES_DIR} 指定）"
    )


@lru_cache(maxsize=None)
def _load_cached(
    filename: str,
    directory: str,
    expected_keys: Tuple[str, ...],
    string_keys: Tuple[str, ...],
) -> Mapping[str, Any]:
    path = Path(directory) / filename
    if not path.is_file():
        raise FixtureDataError(f"合成 fixture 文件缺失：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FixtureDataError(f"合成 fixture 文件不可读或 JSON 非法：{path}") from exc
    if not isinstance(data, dict):
        raise FixtureDataError(f"合成 fixture 顶层必须是 JSON 对象：{path}")
    _validate_whitelist(path, data, expected_keys, string_keys)
    return data


def _validate_whitelist(
    path: Path,
    data: Mapping[str, Any],
    expected_keys: Tuple[str, ...],
    string_keys: Tuple[str, ...],
) -> None:
    schema_id = data.get("fixture_schema")
    if schema_id != FIXTURE_SCHEMA_ID:
        raise FixtureDataError(
            f"合成 fixture 标识不合法：期望 {FIXTURE_SCHEMA_ID!r}，实际 {schema_id!r}（{path}）"
        )
    version = data.get("fixture_version")
    if version != FIXTURE_SCHEMA_VERSION:
        raise FixtureDataError(
            f"合成 fixture 版本不合法：期望 {FIXTURE_SCHEMA_VERSION!r}，实际 {version!r}（{path}）"
        )
    expected = set(expected_keys) | {"fixture_schema", "fixture_version"}
    unknown = sorted(set(data) - expected)
    if unknown:
        raise FixtureDataError(f"合成 fixture 存在未知字段：{unknown}（{path}）")
    missing = sorted(expected - set(data))
    if missing:
        raise FixtureDataError(f"合成 fixture 缺少必填字段：{missing}（{path}）")
    for key in expected_keys:
        value = data[key]
        if key in string_keys:
            if not isinstance(value, str) or not value.strip():
                raise FixtureDataError(f"合成 fixture 字段 {key} 必须是非空字符串（{path}）")
        elif not isinstance(value, list):
            raise FixtureDataError(f"合成 fixture 字段 {key} 必须是数组（{path}）")


def load_r5_fixture() -> Mapping[str, Any]:
    """Load the R5 S7 authority source records (structure only)."""

    return _load_cached(
        "r5_authority_fixture.json",
        str(fixtures_dir()),
        _R5_FIXTURE_KEYS,
        (),
    )


def load_r7_setup_fixture() -> Mapping[str, Any]:
    """Load the R7 deterministic snapshots and published baselines."""

    return _load_cached(
        "r7_setup_fixture.json",
        str(fixtures_dir()),
        _R7_SETUP_KEYS,
        (),
    )


def load_synthetic_run_fixture() -> Mapping[str, Any]:
    """Load the deterministic ``--synthetic`` run seed for the progress page."""

    return _load_cached(
        "synthetic_run_fixture.json",
        str(fixtures_dir()),
        _SYNTHETIC_RUN_KEYS,
        _RUN_STRING_KEYS,
    )


__all__ = [
    "ENV_FIXTURES_DIR",
    "FIXTURE_SCHEMA_ID",
    "FIXTURE_SCHEMA_VERSION",
    "FixtureDataError",
    "fixtures_dir",
    "load_r5_fixture",
    "load_r7_setup_fixture",
    "load_synthetic_run_fixture",
]
