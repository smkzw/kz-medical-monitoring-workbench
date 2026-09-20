"""WP1回归：事实快照不可变清单与语义域边界（审阅V3 WP1第一切片）。

- 未知表/无法按列签名判定的表一律"未分类"，不得默认"方案偏离"
  （PD采样≠方案偏离、FW花粉天气≠偏离、PK采样≠偏离）。
- 事实加载走持久化不可变清单（facts-manifest.json）：碰巧同目录的
  findings/布局/方案画像等非事实文件不得混入；清单校验文件字节hash，
  篡改即fail-closed。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.projections.facts_publication import (  # noqa: E402
    FactsPublicationAuthorityProvider,
    _domain_for,
    _infer_domain_by_columns,
)


def test_unknown_table_falls_back_to_unclassified() -> None:
    assert _domain_for("TOTALLY_UNKNOWN") == ("uncategorized", "unclassified")
    assert _infer_domain_by_columns("WEIRD", set()) == (
        "uncategorized",
        "unclassified",
    )


def test_pk_sampling_table_is_not_protocol_deviation() -> None:
    columns = {"SUBJID", "PKDOSE", "PKDAT", "PKCONC", "PKUNIT"}
    assert _infer_domain_by_columns("PKSAMP", columns) == (
        "uncategorized",
        "unclassified",
    )


def test_fw_table_is_not_deviation() -> None:
    # 花粉/天气等环境背景表按名字旧映射为"方案偏离"——语义错误。
    assert _domain_for("FW") == ("uncategorized", "unclassified")


def test_true_deviation_signature_kept() -> None:
    columns = {"SUBJID", "PDTERM", "PDDAT", "PDCAT"}
    assert _infer_domain_by_columns("PDLOG", columns) == (
        "protocol_compliance",
        "protocol_deviation",
    )


def _write_table_artifact(
    artifacts: Path, table: str, rows: list[dict]
) -> Path:
    payload = {table: rows}
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    path = artifacts / f"{digest}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "proj"
    artifacts = workspace / "runtime" / "artifacts"
    artifacts.mkdir(parents=True)
    _write_table_artifact(
        artifacts,
        "AE",
        [{"SUBJID": "01001", "AETERM": "头痛", "AESEV": "1", "AESTDAT": "2026-01-05"}],
    )
    _write_table_artifact(
        artifacts,
        "MH",
        [{"SUBJID": "01001", "MHTERM": "高血压", "MHSTDAT": "2025-06-01"}],
    )
    # 同目录的非事实文件：碰巧含list-of-dict值的键名（旧实现会混入）
    (artifacts / "aemh-findings-facts-snapshot-001.json").write_text(
        json.dumps(
            {
                "kind": "aemh_cross_findings",
                "findings": [
                    {"subject_label": "01001", "state": "accepted", "title": "x"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (artifacts / "listing-layout.json").write_text(
        json.dumps({"forms": [{"form": "AE", "layout": "wide"}]}),
        encoding="utf-8",
    )
    (artifacts / "protocol-profile.json").write_text(
        json.dumps({"protocol": {"ctcae_version": "5.0"}}),
        encoding="utf-8",
    )
    return workspace


def test_loader_uses_immutable_manifest_and_excludes_non_facts(
    tmp_path: Path,
) -> None:
    workspace = _make_workspace(tmp_path)
    provider = FactsPublicationAuthorityProvider(workspace)
    domains = provider._load_domains()
    assert set(domains) == {"AE", "MH"}
    assert domains["AE"][0]["AETERM"] == "头痛"

    # 清单已持久化，且不含非事实文件
    manifest = json.loads(
        (workspace / "runtime" / "artifacts" / "facts-manifest.json").read_text()
    )
    tables = {entry["table"] for entry in manifest["tables"]}
    assert tables == {"AE", "MH"}
    names = {entry["file"] for entry in manifest["tables"]}
    assert all(name.count(".") == 1 for name in names)

    # 不可变：之后新增的同形文件不会被自动吸入
    _write_table_artifact(
        workspace / "runtime" / "artifacts",
        "LB",
        [{"SUBJID": "01001", "LBTEST": "ALT", "LBORRES": "42"}],
    )
    domains2 = FactsPublicationAuthorityProvider(workspace)._load_domains()
    assert set(domains2) == {"AE", "MH"}


def test_loader_fails_closed_on_tampered_artifact(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    FactsPublicationAuthorityProvider(workspace)._load_domains()
    artifacts = workspace / "runtime" / "artifacts"
    manifest = json.loads((artifacts / "facts-manifest.json").read_text())
    target = next(e for e in manifest["tables"] if e["table"] == "AE")
    path = artifacts / target["file"]
    payload = json.loads(path.read_text())
    payload["AE"][0]["AETERM"] = "被篡改的术语"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    import pytest

    with pytest.raises(Exception, match="digest|mismatch|篡改"):
        FactsPublicationAuthorityProvider(workspace)._load_domains()
