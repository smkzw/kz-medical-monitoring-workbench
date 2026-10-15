"""状态机专项T6/S8（02_DESIGN §5-T6/D4）：文档权威verdict物化缓存。

- 等价性参数化（current/missing/incomplete/ambiguous四形态）：缓存命中
  与直连重放resolve输出逐字段相等（缓存只加速不改判定的验收门）；
- 命中跳过verifier重放（A8成本收口的本意）；
- registry_revision变更（A1）→失效重放；
- 被引作业行digest变更（A2）→失效重放；
- env off→零缓存路径（不读不写）。
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_document_evidence import (  # noqa: E402
    MonitoringDocumentEvidenceResolver,
)
from tests.test_mm_c3_document_evidence import (  # noqa: E402
    PROJECT_ID,
    _entry,
    _promote_entries,
    _span,
    _Registry,
)

HASH_A = "a" * 64


class CountingRegistry(_Registry):
    """带标准核验钩子的registry桩：verifier调用计数（命中跳过的观测点）。

    monitoring_authority_entry_is_verified与生产SourceRegistryService
    同构（receipt完整性先判，promoted→verifier重放）。
    """

    def __init__(self, entries, spans) -> None:
        super().__init__(entries, spans)
        self.verifier_calls = 0
        self.verdict = True

    def _verify(self, project_id, receipt) -> bool:
        self.verifier_calls += 1
        return self.verdict

    def monitoring_authority_entry_is_verified(self, entry) -> bool:
        from services.api.app.source_intake import (
            monitoring_authority_receipt_is_complete,
        )

        entries = self.list_entries(entry.project_id)
        if not monitoring_authority_receipt_is_complete(entry, entries):
            return False
        metadata = dict(entry.metadata or {})
        if metadata.get("monitoring_authority_status") != "promoted":
            return True
        verifier = self.monitoring_authority_receipt_verifier
        return bool(
            verifier is not None
            and verifier(entry.project_id, metadata["document_authority_receipt"])
        )


def _promote_single(entry, *, role: str) -> None:
    """单条目晋升（显式role）——ambiguous形态的protocol_document kind
    不在_promote_entries的kind→role表内，这里直接构造同构receipt。"""

    from packages.medical_monitoring.intelligence.primitives import content_hash

    registration = {
        "role": role,
        "candidate_id": f"candidate-{entry.entry_id}",
        "source_entry_id": entry.entry_id,
        "content_sha256": entry.content_hash,
    }
    receipt = {
        "schema_version": "monitoring-document-authority-promotion-v1",
        "batch_id": f"mmbatch_{'b' * 24}",
        "input_sha256": "a" * 64,
        "analysis_job_ids": ["primary-job", "verifier-job"],
        "review_job_ids": [],
        "analysis_run_ids": ["primary-run", "verifier-run"],
        "review_run_ids": [],
        "document_identities": [
            {
                "role": role,
                "candidate_id": registration["candidate_id"],
                "document_version": "",
                "document_date": "",
            }
        ],
        "registrations": [registration],
    }
    entry.metadata.update({
        "monitoring_authority_status": "promoted",
        "document_authority_receipt_sha256": content_hash(receipt),
        "document_authority_receipt": receipt,
    })


def _promoted_registry(*, cite_job_ids: tuple[str, ...] = ()):
    protocol = _entry("protocol", 1)
    ecrf = _entry("ecrf", 2)
    _promote_entries(protocol, ecrf)
    if cite_job_ids:
        from packages.medical_monitoring.intelligence.primitives import (
            content_hash,
        )

        receipt = protocol.metadata["document_authority_receipt"]
        receipt["analysis_job_ids"] = list(cite_job_ids)
        for entry in (protocol, ecrf):
            entry.metadata["document_authority_receipt_sha256"] = content_hash(
                receipt
            )
    registry = CountingRegistry(
        [protocol, ecrf],
        [_span(entry, index) for entry in (protocol, ecrf) for index in (1, 2)],
    )
    registry.monitoring_authority_receipt_verifier = registry._verify
    return registry


def _seed_job(repo: MonitoringAiRepository, *, job_id_hint: str, role: str = "primary"):
    revision = MonitoringAiInputRevision(
        project_id=PROJECT_ID,
        batch_revision="batch-t6",
        mapping_revision="mapping-t6",
        protocol_version="protocol-v1",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=HASH_A,
            ),
        ),
    )
    request = MonitoringAiJobCreate(
        project_id=PROJECT_ID,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
        input_revision=revision,
        input_payload={"schema_version": "monitoring_ai_v1"},
        prompt_version="document-authority-v1",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=2,
        business_key=(
            f"document-authority-analysis:{role}:g1:{job_id_hint}"
        ),
    )
    return repo.create_or_get(request)


def _dump(packet) -> str:
    return json.dumps(dataclasses.asdict(packet), sort_keys=True, default=str)


@pytest.fixture
def repo(tmp_path: Path) -> MonitoringAiRepository:
    return MonitoringAiRepository(tmp_path / "t6.sqlite3")


def test_env_off_is_zero_cache_path(repo: MonitoringAiRepository) -> None:
    """env off：不读不写缓存表，verifier照常重放（现状行为）。"""

    registry = _promoted_registry()
    resolver = MonitoringDocumentEvidenceResolver(registry, verdict_store=repo)
    packet = resolver.resolve(project_id=PROJECT_ID)
    assert registry.verifier_calls >= 2  # 两个promoted条目都重放
    with repo._connect() as connection:
        rows = connection.execute(
            "SELECT COUNT(*) FROM monitoring_document_authority_verdicts"
        ).fetchone()
    assert int(rows[0]) == 0


def test_cache_hit_skips_replay_and_packet_equivalent(
    repo: MonitoringAiRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """命中跳过重放；warm包与env off直连包逐字段相等（等价性门）。"""

    monkeypatch.setenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", "1")
    registry = _promoted_registry()
    resolver = MonitoringDocumentEvidenceResolver(registry, verdict_store=repo)
    first = resolver.resolve(project_id=PROJECT_ID)
    calls_after_first = registry.verifier_calls
    assert calls_after_first >= 2

    second = resolver.resolve(project_id=PROJECT_ID)
    assert registry.verifier_calls == calls_after_first  # 命中：零重放
    assert _dump(second) == _dump(first)

    # 等价性：直连重放（env off、独立registry同构）与缓存warm包相等。
    monkeypatch.delenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", raising=False)
    direct_registry = _promoted_registry()
    direct = MonitoringDocumentEvidenceResolver(
        direct_registry, verdict_store=repo
    ).resolve(project_id=PROJECT_ID)
    assert _dump(direct) == _dump(first)


@pytest.mark.parametrize("shape", ["current", "missing", "incomplete", "ambiguous"])
def test_packet_equivalence_across_role_shapes(
    repo: MonitoringAiRepository,
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
) -> None:
    """四形态等价性参数化：current/missing/incomplete/ambiguous。"""

    def _build():
        if shape == "current":
            registry = _promoted_registry()
            kwargs: dict = {}
        elif shape == "missing":
            registry = _promoted_registry()
            registry._entries = [
                item
                for item in registry._entries
                if item.source_kind != "statistical_analysis_plan"
            ]  # sap本就缺席→missing形态
            kwargs = {}
        elif shape == "incomplete":
            registry = _promoted_registry()
            kwargs = {"selected_entry_ids": {"protocol": "source-gone"}}
        else:  # ambiguous：同角色两个main晋升条目——各自独立receipt
            # （同receipt两同角色primary过不了completeness）+不同
            # source_kind（registry桩同kind取最新晋升，旧kind被
            # superseded；两kind同属protocol角色→双main→ambiguous）
            first = _entry("protocol", 1)
            second = _entry("protocol", 3)
            second.source_kind = "protocol_document"
            ecrf = _entry("ecrf", 2)
            _promote_entries(first)
            _promote_single(second, role="protocol")
            _promote_entries(ecrf)
            entries = [first, second, ecrf]
            registry = CountingRegistry(
                entries,
                [
                    _span(entry, index)
                    for entry in entries
                    for index in (1, 2)
                ],
            )
            registry.monitoring_authority_receipt_verifier = registry._verify
            kwargs = {}

        def _run() -> str:
            return _dump(
                MonitoringDocumentEvidenceResolver(
                    registry, verdict_store=repo
                ).resolve(project_id=PROJECT_ID, **kwargs)
            )

        return registry, _run

    monkeypatch.delenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", raising=False)
    direct_registry, direct_run = _build()
    direct = direct_run()

    monkeypatch.setenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", "1")
    warm_registry, warm_run = _build()
    warm_run()  # 首跑写缓存
    warm = warm_run()  # 次跑命中

    assert warm == direct
    if shape == "current":
        assert json.loads(warm)["roles"][0]["status"] == "current"
    elif shape == "missing":
        statuses = {item["role"]: item["status"] for item in json.loads(warm)["roles"]}
        assert statuses["sap"] == "missing"
    elif shape == "incomplete":
        statuses = {item["role"]: item["status"] for item in json.loads(warm)["roles"]}
        assert statuses["protocol"] == "incomplete"
    else:
        statuses = {item["role"]: item["status"] for item in json.loads(warm)["roles"]}
        assert statuses["protocol"] == "ambiguous"


def test_registry_revision_change_invalidates_cache(
    repo: MonitoringAiRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A1台账变化（条目document_revision变更）→键失配→失效重放。"""

    monkeypatch.setenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", "1")
    registry = _promoted_registry()
    resolver = MonitoringDocumentEvidenceResolver(registry, verdict_store=repo)
    resolver.resolve(project_id=PROJECT_ID)
    calls_after_warm = registry.verifier_calls

    registry._entries[0].metadata["document_revision"] = "protocol-revision-CHANGED"
    resolver.resolve(project_id=PROJECT_ID)
    assert registry.verifier_calls > calls_after_warm


def test_cited_job_digest_change_invalidates_cache(
    repo: MonitoringAiRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A2证据变化（被引作业行updated_at变更）→键失配→失效重放。"""

    job_primary = _seed_job(repo, job_id_hint="t6p", role="primary")
    job_verifier = _seed_job(repo, job_id_hint="t6v", role="verifier")
    monkeypatch.setenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", "1")
    registry = _promoted_registry(
        cite_job_ids=(job_primary.job_id, job_verifier.job_id)
    )
    resolver = MonitoringDocumentEvidenceResolver(registry, verdict_store=repo)
    resolver.resolve(project_id=PROJECT_ID)
    calls_after_warm = registry.verifier_calls
    assert calls_after_warm >= 2

    with repo._connect() as connection:
        connection.execute(
            "UPDATE monitoring_ai_jobs SET updated_at = '2026-10-15T09:00:00+00:00'"
            " WHERE job_id = ?",
            (job_primary.job_id,),
        )
        connection.commit()
    resolver.resolve(project_id=PROJECT_ID)
    assert registry.verifier_calls > calls_after_warm


def test_cache_write_failure_does_not_break_verification(
    repo: MonitoringAiRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """缓存写入故障→判定不变（只加速不改判定；put内部吞异常）。"""

    monkeypatch.setenv("WORKBENCH_DOCUMENT_VERDICT_CACHE", "1")
    registry = _promoted_registry()
    resolver = MonitoringDocumentEvidenceResolver(registry, verdict_store=repo)

    with repo._connect() as connection:
        connection.execute("DROP TABLE monitoring_document_authority_verdicts")
        connection.commit()
    packet = resolver.resolve(project_id=PROJECT_ID)
    statuses = {item.role: item.status for item in packet.roles}
    assert statuses["protocol"] == "current"
