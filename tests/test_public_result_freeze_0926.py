"""W01-R26（20260926）：冻结历史read model——旧token在投影代码升级后仍可打开。

验收锚点 R26-A10/A11/A13(坏工件)/A14 与存量库迁移要求
（review_pack_0926V1/kz_review_0926V1/04_ACCEPTANCE_0926V1.json，W01-R26
工作令动作2：版本内容从发布manifest获得，不从当前默认配置推断）：
- A10 相同facts两次发布，打开A仍是A，身份与证据冻结；
- A11 核心反例：发布后人为修改severity投影代码，旧token仍打开且内容
  逐字段等于发布时快照。新增失败反例已在修改前HEAD 872a451复现：当时
  result_context_service重建比对路径raise result_context_unavailable；
- 坏工件verify失败→明确result_context_unavailable，不回退live或重建；
- A14 两项目同subject label，不混来源；
- 存量库迁移：旧v4 schema库经守卫式ALTER原地升级后存量token行为不变。

真实入口：LaunchRegistry发布事务、Store artifact+CAS、
load_public_result_context读取链。冻结合成fixture，0模型调用。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path

import pytest

from packages.medical_monitoring.api.r7_product.frozen_read_model import (
    READ_MODEL_VERSION,
    freeze_read_model_document,
    load_frozen_read_model_document,
    read_model_sha256,
    restore_frozen_packet,
    store_frozen_read_model,
)
from packages.medical_monitoring.api.r7_product.result_context_service import (
    ResultContextDependencies,
    load_public_result_context,
)
from packages.medical_monitoring.api.r7_product.route_utils import (
    _workspace_dir,
)
from packages.medical_monitoring.domain.execution import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    NodeType,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.projections.product_fixture_records import (
    base_records_from_fixture,
)
from packages.medical_monitoring.projections.product_types import (
    SYNTHETIC_FIXTURE_MODE,
    R5AuthorityPacket as ProductPacket,
    R5SourceRevisionPair,
    canonical_sha256,
)
from packages.medical_monitoring.projections.publication.r5_publication_authority import (
    _PACKET_ID_PREFIX,
    _aggregate_digest,
    R5AuthorityPacket as PublicationPacket,
)
from packages.medical_monitoring.runtime import launch_schema
from packages.medical_monitoring.runtime import launch_registry as lr
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
)
from packages.medical_monitoring.runtime.schema_manifest import (
    SchemaClassification,
    inspect_member,
)

# 合成product packet的synthetic分支要求project_ref以s7-synthetic-开头。
PROJECT_A = "s7-synthetic-freeze-a"
PROJECT_B = "s7-synthetic-freeze-b"
RUN_A = "freeze-run-a"
RUN_B = "freeze-run-b"
SNAPSHOT = "s7-snapshot-current-001"
SNAPSHOT_TOKEN = "freeze-snapshot-token-001"
CUTOFF = "2026-03-31"
SOURCE_REVISION = "freeze-source-revision-001"
SITE_REF = "s7-site-006"
MANIFEST_DIGEST = "m" * 64
MANIFEST_REVISION = 3
SETUP_IDENTITY = {
    "setup": "freeze-fixture",
    "mandatory_denominator": 1,
    "work_units": {"freeze-unit": True},
}
RUNTIME_IDENTITY = {
    "runtime": "freeze-runtime",
    "mandatory_denominator": 1,
    "work_units": {"freeze-unit": True},
}
RECEIPT_IDS = ("freeze-receipt-001",)
RECEIPT_SET_DIGEST = "r" * 64
R6_OUTPUT_SET_DIGEST = "a" * 64
MODE_OUTPUT_KINDS = (
    "affected_query_draft",
    "overview_projection",
    "subject_journey",
    "source_evidence",
)


# ---------------------------------------------------------------------------
# 冻结合成packet
# ---------------------------------------------------------------------------


def _build_product_packet(
    project_ref: str,
    run_ref: str,
    *,
    severity: str,
) -> ProductPacket:
    """合成product packet：与product_fixtures同构，但身份可自定义。"""

    (
        sources,
        sites,
        subjects,
        events,
        visits,
        risks,
        _histories,
    ) = base_records_from_fixture(SNAPSHOT)
    risks = tuple(dataclass_replace(item, severity=severity) for item in risks)
    revision_pairs = tuple(
        R5SourceRevisionPair(
            revision_id=item.source_revision_ref,
            content_hash=item.source_revision_content_hash,
            locator_refs=(item.locator_ref,),
        )
        for item in sources
    )
    return ProductPacket(
        project_ref=project_ref,
        run_ref=run_ref,
        snapshot_ref=SNAPSHOT,
        cutoff_state="present",
        cutoff_ref=CUTOFF,
        project_label="冻结读模型合成项目",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version="2026-08-26.1",
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id=f"s7-visibility:{SNAPSHOT}",
        visibility_decision_hash=canonical_sha256(
            {
                "snapshot_ref": SNAPSHOT,
                "projectable": True,
                "source_count": len(sources),
            }
        ),
        evaluation_content_identities=(
            canonical_sha256({"snapshot_ref": SNAPSHOT, "kind": "evaluation"}),
        ),
        source_revision_content_pairs=revision_pairs,
        sources=sources,
        sites=sites,
        subjects=subjects,
        events=events,
        visits=visits,
        risks=risks,
        histories=(),
        synthetic=True,
        data_mode=SYNTHETIC_FIXTURE_MODE,
    )


def _build_publication_packet(
    project_ref: str,
    run_ref: str,
    product_packet: ProductPacket,
) -> PublicationPacket:
    """按R5PublicationAuthorityBridge.build的同一确定性流程组装packet。"""

    # 成员直接采用product packet自身的authority集合：桥接/产品引用
    # 一致性比对（读取侧三棵树之外的最后一段）由构造保证成立。
    site_refs = tuple(sorted({item.site_ref for item in product_packet.sites}))
    members = {
        "project_ref": project_ref,
        "run_ref": run_ref,
        "public_run_token": lr.derive_public_run_token(project_ref, run_ref),
        "snapshot_ref": SNAPSHOT,
        "cutoff_ref": CUTOFF,
        "site_refs": site_refs,
        "s4_packets": (),
        "risks": product_packet.risks,
        "subjects": product_packet.subjects,
        "sites": product_packet.sites,
        "events": product_packet.events,
        "visits": product_packet.visits,
        "sources": product_packet.sources,
    }
    product_hash = getattr(product_packet, "authority_hash", "")
    assert len(product_hash) == 64
    digest = _aggregate_digest(
        {**members, "product_packet_authority_hash": product_hash}
    )
    return PublicationPacket(
        **members,
        packet_identity=_PACKET_ID_PREFIX + digest,
        packet_digest=digest,
        authority_hash=digest,
        product_packet=product_packet,
    )


# ---------------------------------------------------------------------------
# 真实发布与读取入口
# ---------------------------------------------------------------------------


class _StubEntry:
    def close(self) -> None:
        return None


def _seed_runtime_run(runtime_db: Path, project_ref: str, run_ref: str) -> None:
    """Store工件表外键要求：artifacts.run_id须存在于monitoring_runs。"""

    connection = sqlite3.connect(str(runtime_db))
    try:
        connection.execute(
            "INSERT OR IGNORE INTO projects(project_id, name, is_synthetic,"
            " config_json, created_at) VALUES (?,?,?,?,?)",
            (
                project_ref,
                "冻结读模型合成项目",
                1,
                "{}",
                "2026-09-26T00:00:00+00:00",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO source_revisions(revision_id, project_id,"
            " source_type, version, content_hash, scope_json, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                SOURCE_REVISION,
                project_ref,
                "listing",
                "v1",
                "e" * 64,
                "{}",
                "2026-09-26T00:00:00+00:00",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO monitoring_runs(run_id, project_id, mode,"
            " data_cutoff, source_revision_id, execution_basis,"
            " analysis_state, evidence_state, review_state, output_state,"
            " manifest_revision, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_ref,
                project_ref,
                "daily",
                CUTOFF,
                SOURCE_REVISION,
                "full",
                "completed",
                "completed",
                "completed",
                "completed",
                MANIFEST_REVISION,
                "2026-09-26T00:00:00+00:00",
                "2026-09-26T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()


def _publish(
    root: Path,
    project_ref: str,
    run_ref: str,
    *,
    severity: str = "high",
    freeze: bool = True,
) -> tuple[lr.ResultPublication, PublicationPacket, dict, str]:
    """走真实LaunchRegistry事务与Store CAS完成一次发布（含冻结read model）。

    run_ref即registry.reserve生成的launch运行ID：读取链要求product packet
    与publication packet的run_ref都等于launch.run_id。
    """

    workspace = _workspace_dir(root, project_ref)
    registry = lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME, project_id=project_ref
    )
    try:
        reservation = registry.reserve(
            project_ref,
            idempotency_key=f"launch-{run_ref}",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=SNAPSHOT_TOKEN,
            data_cutoff=CUTOFF,
        )
        run_ref = reservation.record.run_id
        registry.mark_completed(run_ref, project_id=project_ref)
        product_packet = _build_product_packet(
            project_ref, run_ref, severity=severity
        )
        packet = _build_publication_packet(
            project_ref, run_ref, product_packet
        )
        publication = registry.reserve_publication(
            project_id=project_ref,
            run_id=run_ref,
            idempotency_key=f"publication-{run_ref}",
            fingerprint=f"fingerprint-{run_ref}",
            snapshot_token=SNAPSHOT_TOKEN,
            snapshot_ref=SNAPSHOT,
            source_revision_id=SOURCE_REVISION,
            data_cutoff=CUTOFF,
            setup_manifest_digest=MANIFEST_DIGEST,
            site_coverage=tuple(
                sorted({item.site_ref for item in product_packet.sites})
            ),
            setup_manifest_identity=SETUP_IDENTITY,
            mandatory_denominator=1,
        )
        publication = registry.bind_publication_runtime_manifest(
            project_id=project_ref,
            run_id=run_ref,
            revision=publication.publication_revision,
            expected_state=publication.publication_state,
            fingerprint=publication.publication_fingerprint,
            runtime_manifest_revision=MANIFEST_REVISION,
            runtime_manifest_digest=MANIFEST_DIGEST,
            runtime_manifest_identity=RUNTIME_IDENTITY,
            mandatory_denominator=1,
        )

        runtime_dir = workspace / RUNTIME_DIR_NAME
        store = Store(
            runtime_dir / RUNTIME_DB_NAME, runtime_dir / ARTIFACT_DIR_NAME
        )
        _seed_runtime_run(runtime_dir / RUNTIME_DB_NAME, project_ref, run_ref)
        member_ids: list[str] = []
        try:
            for kind in MODE_OUTPUT_KINDS:
                envelope = ArtifactEnvelope(
                    artifact_type="r6_mode_output",
                    version="freeze-fixture-v1",
                    run_id=run_ref,
                    node_id=f"r6-{kind}",
                    node_type=NodeType.PROJECTION,
                    payload={
                        "output_kind": kind,
                        "project_id": project_ref,
                        "run_id": run_ref,
                        "data_cutoff": CUTOFF,
                        "authority_refs": {
                            "authority_digest": packet.packet_digest,
                        },
                        "findings": [],
                    },
                    completeness=ArtifactCompleteness.COMPLETE,
                )
                staged = store.stage_artifact(envelope)
                committed = store.commit_artifact(staged, envelope)
                member_ids.append(committed.artifact_id)
            member_ids.sort()
            document = freeze_read_model_document(
                packet, projection_version=MANIFEST_DIGEST
            )
            frozen_artifact_id: str | None = None
            frozen_sha256: str | None = None
            if freeze:
                frozen_artifact_id, frozen_sha256 = store_frozen_read_model(
                    store, run_id=run_ref, document=document
                )
        finally:
            store.close()

        publication = registry.finalize_publication(
            project_id=project_ref,
            run_id=run_ref,
            revision=publication.publication_revision,
            expected_state=publication.publication_state,
            fingerprint=publication.publication_fingerprint,
            receipt_identities=RECEIPT_IDS,
            receipt_set_digest=RECEIPT_SET_DIGEST,
            r5_authority_packet_id=packet.packet_identity,
            r5_authority_packet_digest=packet.packet_digest,
            r6_output_set_digest=R6_OUTPUT_SET_DIGEST,
            artifact_member_ids=tuple(member_ids),
            artifact_member_set_digest=lr.content_digest(list(member_ids)),
            frozen_read_model_artifact_id=frozen_artifact_id,
            frozen_read_model_sha256=frozen_sha256,
        )
        return publication, packet, document, run_ref
    finally:
        registry.close()


def _publication_gate(workspace: Path, project_ref: str, run_ref: str) -> dict:
    registry = lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME, project_id=project_ref
    )
    try:
        publication = registry.get_publication(
            project_id=project_ref, run_id=run_ref
        )
        return {
            "revision": publication.manifest_revision,
            "digest": publication.manifest_digest,
            "identity": dict(publication.runtime_manifest_identity),
            "receipt_ids": tuple(publication.receipt_identities),
            "receipt_set_digest": publication.receipt_set_digest,
            "receipt_attempts": (),
        }
    finally:
        registry.close()


def _make_loader(
    root: Path,
    *,
    severity: str,
):
    """注入"当前投影代码"的builder；severity即当前投影实现会算出的值。"""

    calls = {"count": 0}

    def builder(
        _provider,
        identity,
        *,
        attempts,
        bridge,
        product_packet_factory,
    ):
        calls["count"] += 1
        return _build_publication_packet(
            identity.project_ref,
            identity.run_ref,
            _build_product_packet(
                identity.project_ref, identity.run_ref, severity=severity
            ),
        )

    def load(project_ref: str, token: str):
        workspace = _workspace_dir(root, project_ref)
        dependencies = ResultContextDependencies(
            root=root,
            open_legacy_view=lambda project: None,
            open_launch_registry=lambda project: lr.LaunchRegistry(
                _workspace_dir(root, project) / lr.LAUNCH_REGISTRY_DB_NAME,
                project_id=project,
            ),
            open_entry=lambda workspace_dir, allow_create: _StubEntry(),
            publication_setup_inputs=lambda *args, **kwargs: None,
            publication_bridge=None,
            publication_provider=None,
            r5_product_packet_factory=None,
            harness_r1_profile=None,
            build_r5_publication_packet=builder,
            read_publication_gate=lambda workspace_dir, run_id, *, entry,
            harness_r1_profile: _publication_gate(
                workspace_dir, project_ref, run_id
            ),
        )
        return load_public_result_context(dependencies, project_ref, token)

    return load, calls


# ---------------------------------------------------------------------------
# A11：投影实现升级后旧token仍打开发布时快照
# ---------------------------------------------------------------------------


def test_a11_projection_upgrade_old_token_still_opens_frozen_content(
    tmp_path: Path,
) -> None:
    root = tmp_path
    publication, packet, document, run_id = _publish(
        root, PROJECT_A, RUN_A, severity="high"
    )
    assert publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE
    assert publication.frozen_read_model_artifact_id
    assert publication.frozen_read_model_sha256 == read_model_sha256(document)
    token = publication.result_context_token
    assert token

    load, calls = _make_loader(root, severity="high")
    context = load(PROJECT_A, token)
    try:
        # 发布时内容：severity投影为high。
        assert context.publication.r5_authority_packet_digest == (
            packet.packet_digest
        )
        assert document["authority_anchor"]["packet_digest"] == (
            packet.packet_digest
        )
    finally:
        context.close()
    assert calls["count"] == 0  # 冻结路径不重建

    # 投影实现"升级"：同样的facts现在会投影出medium。
    load_after_upgrade, calls_after = _make_loader(
        root, severity="medium"
    )
    context = load_after_upgrade(PROJECT_A, token)
    try:
        # 旧token仍可读，且内容逐字段等于发布时快照（high而非medium）。
        assert context.publication.r5_authority_packet_id == (
            publication.r5_authority_packet_id
        )
        assert context.publication.r5_authority_packet_digest == (
            packet.packet_digest
        )
        view = restore_frozen_packet(document)
        assert view.product_packet == _build_product_packet(
            PROJECT_A, run_id, severity="high"
        )
        for output in context.mode_outputs.values():
            assert (
                output["authority_refs"]["authority_digest"]
                == packet.packet_digest
            )
    finally:
        context.close()
    assert calls_after["count"] == 0


def test_frozen_read_model_round_trip_matches_published_packet(
    tmp_path: Path,
) -> None:
    _publication, packet, document, _run_id = _publish(
        root=tmp_path, project_ref=PROJECT_A, run_ref=RUN_A
    )
    assert document["read_model_version"] == READ_MODEL_VERSION
    # projection_version来自发布manifest，不从当前默认配置推断。
    assert document["projection_version"] == MANIFEST_DIGEST
    view = restore_frozen_packet(document)
    assert view.packet_identity == packet.packet_identity
    assert view.packet_digest == packet.packet_digest
    assert tuple(view.site_refs) == tuple(packet.site_refs)
    assert view.product_packet == packet.product_packet
    ref_columns = {
        "sites": "site_ref",
        "subjects": "subject_ref",
        "events": "event_ref",
        "visits": "visit_ref",
        "risks": "risk_ref",
        "sources": "locator_ref",
    }
    for name, ref in ref_columns.items():
        # 冻结文档按引用排序；读取语义是集合一致性，逐元素排序后比对。
        assert sorted(
            getattr(item, ref) for item in getattr(view, name)
        ) == sorted(
            getattr(item, ref) for item in getattr(packet, name)
        )


# ---------------------------------------------------------------------------
# A10：相同facts两次发布，打开A仍是A
# ---------------------------------------------------------------------------


def test_a10_same_facts_two_publications_keep_own_frozen_identity(
    tmp_path: Path,
) -> None:
    publication_a, packet_a, document_a, run_id_a = _publish(
        tmp_path, PROJECT_A, RUN_A
    )
    publication_b, packet_b, document_b, run_id_b = _publish(
        tmp_path, PROJECT_A, RUN_B
    )
    # 同facts、同投影 → 受试者账本一致；运行身份不同 → packet身份不同。
    assert packet_a.product_packet.subjects == packet_b.product_packet.subjects
    assert packet_a.packet_digest != packet_b.packet_digest
    assert (
        publication_a.frozen_read_model_artifact_id
        != publication_b.frozen_read_model_artifact_id
    )

    load, calls = _make_loader(tmp_path, severity="high")
    context_a = load(PROJECT_A, publication_a.result_context_token)
    try:
        assert context_a.launch.run_id == run_id_a
        assert context_a.publication.frozen_read_model_artifact_id == (
            publication_a.frozen_read_model_artifact_id
        )
        view_a = restore_frozen_packet(document_a)
        assert view_a.product_packet.run_ref == run_id_a
    finally:
        context_a.close()
    context_b = load(PROJECT_A, publication_b.result_context_token)
    try:
        assert context_b.launch.run_id == run_id_b
        assert context_b.publication.frozen_read_model_artifact_id == (
            publication_b.frozen_read_model_artifact_id
        )
        view_b = restore_frozen_packet(document_b)
        assert view_b.product_packet.run_ref == run_id_b
        assert view_a.product_packet != view_b.product_packet
    finally:
        context_b.close()
    assert calls["count"] == 0


# ---------------------------------------------------------------------------
# 坏工件：verify失败→明确错误，不回退live或重建（A13坏工件分支）
# ---------------------------------------------------------------------------


def test_bad_frozen_artifact_fails_closed_without_rebuild(
    tmp_path: Path,
) -> None:
    publication, _packet, _document, _run_id = _publish(tmp_path, PROJECT_A, RUN_A)
    artifact_dir = (
        _workspace_dir(tmp_path, PROJECT_A)
        / RUNTIME_DIR_NAME
        / ARTIFACT_DIR_NAME
    )
    content_file = (
        artifact_dir / f"{publication.frozen_read_model_artifact_id}.json"
    )
    assert content_file.is_file()
    content_file.write_text(
        json.dumps(
            {
                "read_model_version": READ_MODEL_VERSION,
                "projection_version": "tampered",
                "authority_anchor": {
                    "packet_identity": "tampered",
                    "packet_digest": "tampered",
                    "site_refs": [SITE_REF],
                },
                "member_refs": {},
                "product_packet": None,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    load, calls = _make_loader(tmp_path, severity="high")
    with pytest.raises(
        Exception, match="result_context_unavailable"
    ) as excinfo:
        load(PROJECT_A, publication.result_context_token)
    assert getattr(excinfo.value, "code", "") == "result_context_unavailable"
    assert calls["count"] == 0  # 坏工件不得借重建顶替


def test_frozen_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    publication, _packet, document, run_id = _publish(
        tmp_path, PROJECT_A, RUN_A
    )
    # 直接篡改发布行sha256引用：读取必须fail-closed。
    workspace = _workspace_dir(tmp_path, PROJECT_A)
    with sqlite3.connect(
        str(workspace / lr.LAUNCH_REGISTRY_DB_NAME)
    ) as connection:
        connection.execute(
            "UPDATE r7_result_publications SET frozen_read_model_sha256 = ? "
            "WHERE run_id = ?",
            ("b" * 64, run_id),
        )
        connection.commit()
    registry = lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME, project_id=PROJECT_A
    )
    try:
        drifted = registry.get_publication(
            project_id=PROJECT_A, run_id=run_id
        )
        store = Store(
            workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
            workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME,
        )
        try:
            with pytest.raises(Exception, match="result_context_unavailable"):
                load_frozen_read_model_document(store, drifted)
        finally:
            store.close()
    finally:
        registry.close()
    assert document["read_model_version"] == READ_MODEL_VERSION


# ---------------------------------------------------------------------------
# A14：两项目同subject label不混来源
# ---------------------------------------------------------------------------


def test_a14_two_projects_same_subject_labels_do_not_cross(tmp_path: Path) -> None:
    publication_a, packet_a, document_a, _run_id_a = _publish(
        tmp_path, PROJECT_A, RUN_A
    )
    publication_b, packet_b, document_b, _run_id_b = _publish(
        tmp_path, PROJECT_B, RUN_B
    )
    # 同一fixture → subject label相同。
    assert (
        packet_a.product_packet.subjects[0].subject_ref
        == packet_b.product_packet.subjects[0].subject_ref
    )

    load, calls = _make_loader(tmp_path, severity="high")
    context_a = load(PROJECT_A, publication_a.result_context_token)
    try:
        assert context_a.publication.project_id == PROJECT_A
        view_a = restore_frozen_packet(document_a)
        assert view_a.product_packet.project_ref == PROJECT_A
    finally:
        context_a.close()
    context_b = load(PROJECT_B, publication_b.result_context_token)
    try:
        assert context_b.publication.project_id == PROJECT_B
        view_b = restore_frozen_packet(document_b)
        assert view_b.product_packet.project_ref == PROJECT_B
        assert view_a.product_packet.project_ref != (
            view_b.product_packet.project_ref
        )
    finally:
        context_b.close()
    # A的token在B项目不可解析：不混来源、不混模型回执。
    with pytest.raises(Exception, match="result_context_unavailable"):
        load(PROJECT_B, publication_a.result_context_token)
    assert calls["count"] == 0


# ---------------------------------------------------------------------------
# 存量库迁移：v4旧schema库守卫式ALTER原地升级，存量token行为不变
# ---------------------------------------------------------------------------


def _create_legacy_v4_launch_db(path: Path, project_ref: str) -> None:
    """按v4形状（无冻结引用列）与v4 marker构造存量库。"""

    publication_ddl = launch_schema.PUBLICATION_DDL.replace(
        "    frozen_read_model_artifact_id TEXT,\n", ""
    ).replace("    frozen_read_model_sha256 TEXT,\n", "")
    assert "frozen_read_model" not in publication_ddl
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        for statement in (
            launch_schema.BASE_DDL
            + publication_ddl
            + launch_schema.RESULT_CONTEXT_INDEX_DDL
            + launch_schema.CONTINUITY_DDL
            + launch_schema.CONTINUITY_INDEX_DDL
        ).split(";"):
            sql = statement.strip()
            if sql:
                connection.execute(sql)
        connection.execute(
            "INSERT INTO r7_launch_registry_meta(key, value) VALUES (?, ?)",
            ("schema_version", lr.SCHEMA_VERSION_V4),
        )
        connection.commit()
    finally:
        connection.close()


def test_legacy_v4_db_upgrades_in_place_and_keeps_existing_token(
    tmp_path: Path,
) -> None:
    workspace = _workspace_dir(tmp_path, PROJECT_A)
    workspace.mkdir(parents=True)
    db_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    _create_legacy_v4_launch_db(db_path, PROJECT_A)
    public_run_token = lr.derive_public_run_token(PROJECT_A, RUN_A)

    # 存量launch行 + 存量发布行：已available、带token、无冻结引用。
    request_fingerprint = lr.compute_request_fingerprint(
        "daily", "full", SNAPSHOT_TOKEN
    )
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute(
            """
            INSERT INTO r7_launch_registry(
                project_id, idempotency_key, run_id, public_run_token,
                request_fingerprint, mode, execution_basis,
                current_snapshot_token, data_cutoff, comparison_range_text,
                rule_tokens_json, run_state, result_available, main_action,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                PROJECT_A,
                "legacy-launch-key",
                RUN_A,
                public_run_token,
                request_fingerprint,
                "daily",
                "full",
                SNAPSHOT_TOKEN,
                CUTOFF,
                "",
                "[]",
                "completed",
                1,
                "查看本次结果",
                "2026-08-01T00:00:00+00:00",
                "2026-08-01T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO r7_result_publications(
                project_id, run_id, public_run_token, result_context_token,
                idempotency_key, publication_revision, publication_fingerprint,
                mode, execution_basis, snapshot_token, data_cutoff,
                site_coverage_json, setup_manifest_identity_json,
                runtime_manifest_identity_json, receipt_identities_json,
                r5_authority_packet_id, r5_authority_packet_digest,
                publication_state, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                PROJECT_A,
                RUN_A,
                public_run_token,
                "result-context:legacy-token",
                "legacy-key",
                1,
                "legacy-fingerprint",
                "daily",
                "full",
                SNAPSHOT_TOKEN,
                CUTOFF,
                '["%s"]' % SITE_REF,
                "{}",
                "{}",
                "[]",
                "legacy-r5-id",
                "d" * 64,
                "available",
                "2026-08-01T00:00:00+00:00",
                "2026-08-01T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    before = inspect_member(db_path, "launch_registry")
    assert before.classification is SchemaClassification.LEGACY

    # 打开即原地升级：守卫ALTER + marker推进，一行数据不改写。
    registry = lr.LaunchRegistry(db_path, project_id=PROJECT_A)
    try:
        assert registry.schema_version == lr.SCHEMA_VERSION
        with sqlite3.connect(str(db_path)) as connection:
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(r7_result_publications)"
                )
            }
            assert {
                "frozen_read_model_artifact_id",
                "frozen_read_model_sha256",
            } <= columns
        publication = registry.get_publication(
            project_id=PROJECT_A, run_id=RUN_A
        )
        # 存量token行为不变：身份/状态/锚点逐字段保留，冻结引用为空。
        assert publication.result_context_token == (
            "result-context:legacy-token"
        )
        assert publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE
        assert publication.r5_authority_packet_digest == "d" * 64
        assert publication.frozen_read_model_artifact_id is None
        assert publication.frozen_read_model_sha256 is None
    finally:
        registry.close()

    after = inspect_member(db_path, "launch_registry")
    assert after.classification is SchemaClassification.CURRENT
    assert after.schema_version == lr.SCHEMA_VERSION_V5


def test_finalize_replay_cas_binds_frozen_references(tmp_path: Path) -> None:
    publication, packet, document, run_id = _publish(
        tmp_path, PROJECT_A, RUN_A
    )
    artifact_id = publication.frozen_read_model_artifact_id
    sha256_value = publication.frozen_read_model_sha256
    assert artifact_id and sha256_value
    registry = lr.LaunchRegistry(
        _workspace_dir(tmp_path, PROJECT_A) / lr.LAUNCH_REGISTRY_DB_NAME,
        project_id=PROJECT_A,
    )
    try:
        # 相同引用重放finalize：幂等可用。
        replayed = registry.finalize_publication(
            project_id=PROJECT_A,
            run_id=run_id,
            revision=publication.publication_revision,
            expected_state=lr.PUBLICATION_STATE_AVAILABLE,
            fingerprint=publication.publication_fingerprint,
            r5_authority_packet_id=packet.packet_identity,
            r5_authority_packet_digest=packet.packet_digest,
            frozen_read_model_artifact_id=artifact_id,
            frozen_read_model_sha256=sha256_value,
        )
        assert replayed.replayed is True
        # 不同冻结sha引用同一available行：CAS冲突。
        from packages.medical_monitoring.runtime.launch_registry_contracts import (
            LaunchRegistryError,
        )

        with pytest.raises(
            LaunchRegistryError, match="publication_cas_conflict"
        ):
            registry.finalize_publication(
                project_id=PROJECT_A,
                run_id=run_id,
                revision=publication.publication_revision,
                expected_state=lr.PUBLICATION_STATE_AVAILABLE,
                fingerprint=publication.publication_fingerprint,
                r5_authority_packet_id=packet.packet_identity,
                r5_authority_packet_digest=packet.packet_digest,
                frozen_read_model_artifact_id=artifact_id,
                frozen_read_model_sha256="c" * 64,
            )
    finally:
        registry.close()
