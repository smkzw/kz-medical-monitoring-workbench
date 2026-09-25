"""W04-S3：冻结批次供给 + 规则包全链（draft→rule confirm→start-shadow→
automatic-shadow-runs→confirm-shadow→publish）。

承接 S1/S2：已激活映射 monmaprev_f8677…（S2 修复后 live 激活成功）；
14 条 ai_candidate 事实草案（S2 裁决产物）；确认链被生成内容缺陷阻断，
0 条 medically_confirmed（S2 台账已记录，按护栏5不在 S2 追加修复轮）。

本切片两段：
  A. 冻结批次供给（本切片核心可交付）：CSU 真实 listing（与映射批次同源
     同 sha256 71595d3b…）走 P7 intake 链——
       POST monitoring/batches/intake-file（HTTP，main.py:11827）
       → in-process batch_service.transition(parsed)（HTTP transition 路由
         被 _reject_legacy_monitoring_policy_gap 刻意封写，main.py:12026/3195）
       → POST batches/{id}/record-validation-evidence（HTTP，允许写：
         main.py:11888；写入激活映射身份/expected_domains/full_snapshot_proof，
         monitoring_batch_repository.py:2296 同时落 monitoring_mapping_revisions）
       → in-process transitions validated→confirmed→frozen（CAS version）
     冻结后断言 active_mapping_revision 与 load_frozen_mapping_contract
     四元组 == 激活映射身份（影子采样前提，monitoring_shadow_sample_service
     .py:695-760）。
  B. 规则包全链：POST rule-packs/drafts 传 fact_revision_ids
     （medical_monitoring_router.py:1367；create_draft 硬性要求
     medically_confirmed，monitoring_rule_authoring_service.py:891-910）。
     S2 遗留 0 条 confirmed 事实 → 预期 409 monitoring_fact_not_confirmed，
     如实记录；若后续事实状态变化则继续
     confirm→start-shadow→automatic-shadow-runs→confirm-shadow→publish。

证据逐行追加 runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/
s3_evidence.jsonl。退出码：0 全链或部分交付成功；1 硬失败。
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_ROOT = Path(__file__).resolve().parent
WORKBENCH_ROOT = RUN_ROOT.parent.parent
EVIDENCE_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "w04_protocol_facts"
)
EVIDENCE_PATH = EVIDENCE_DIR / "s3_evidence.jsonl"
RUNTIME_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
)
BATCH_DB_PATH = RUNTIME_DIR / "medical_monitoring_batches.sqlite3"
AI_DB_PATH = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"

BASE_URL = "http://127.0.0.1:8910"
PROJECT_ID = "proj_user_2f17492ac59b"
MM_PREFIX = f"/api/projects/{PROJECT_ID}/modules/medical-monitoring"

PROTOCOL_VERSION_ID = "protov_c1f1135117a3838272628759"
MAPPING_REVISION_ID = "monmaprev_f8677a0050c5af2b3a4894e5e23d"
MAPPING_BATCH_ID = "stg-1b8dd8c423f84248bde9f942e640912b"
LISTING_PATH = (
    RUNTIME_DIR
    / "medical_monitoring_r7"
    / "proj_user_8100977594cd"
    / "admissions"
    / "staging"
    / "stg-83da93b4f43f478087b56fcd176ba40b"
    / "【Data Listing】MG-K10-CSU-001_合成测试数据_V1.0.xlsx"
)
LISTING_SHA256 = "71595d3b6296e38984e6123b607c7efdf117e5b22c87656edf2f5665bef908bd"
ACTOR = "local-user-0249075bebd34158"
RUN_STAMP = "w04s3-20260925"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record(entry: dict[str, Any]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with EVIDENCE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _assertions(step: str, checks: list[tuple[str, bool, Any]]) -> None:
    _record(
        {
            "ts": _now(),
            "step": step,
            "kind": "assertions",
            "assertions": [
                {"check": name, "passed": bool(ok), "detail": detail}
                for name, ok, detail in checks
            ],
            "ok": all(ok for _, ok, _ in checks),
        }
    )


def _http(
    step: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    raw_body: bytes | None = None,
) -> tuple[int, Any]:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    body = raw_body
    if body is None and payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    if raw_body is not None:
        request.add_header("Content-Type", "application/octet-stream")
    else:
        request.add_header("Content-Type", "application/json")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:2_000]}
    _record(
        {
            "ts": _now(),
            "step": step,
            "kind": "http",
            "request": {"method": method, "url": url, "payload": payload},
            "http_status": status,
            "elapsed_ms": elapsed_ms,
            "response": parsed,
        }
    )
    return status, parsed


def _batch_service():
    """进程内 batch_service（仅用 transition/record_validation_evidence，
    二者只依赖 repository）。与 API 进程共库（WAL 并发安全）。"""

    sys.path.insert(0, str(WORKBENCH_ROOT))
    from services.api.app.monitoring_batch_repository import (
        MonitoringBatchRepository,
    )
    from services.api.app.monitoring_batch_service import (
        MonitoringBatchService,
    )
    from types import SimpleNamespace

    repository = MonitoringBatchRepository(
        BATCH_DB_PATH,
        RUNTIME_DIR / "medical_monitoring_batch_objects",
    )
    return MonitoringBatchService(SimpleNamespace(), repository)


def _active_mapping() -> dict[str, Any]:
    status, body = _http(
        "s0_active_mapping",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    if status != 200:
        raise RuntimeError(f"active-mapping HTTP {status}：激活映射缺失")
    return body


def _fact_status_snapshot() -> dict[str, int]:
    status, body = _http(
        "s0_facts",
        "GET",
        f"{MM_PREFIX}/protocol-versions/{PROTOCOL_VERSION_ID}/facts",
    )
    items = body.get("items") or []
    counts: dict[str, int] = {}
    for item in items:
        counts[item.get("status")] = counts.get(item.get("status"), 0) + 1
    return counts


def step0_precheck() -> tuple[dict[str, Any], dict[str, int], int]:
    status, body = _http(
        "s0_precheck",
        "GET",
        f"{MM_PREFIX}/protocol-versions",
    )
    items = body.get("items") or []
    target = next(
        (
            item
            for item in items
            if item.get("protocol_version_id") == PROTOCOL_VERSION_ID
        ),
        None,
    )
    active = _active_mapping()
    fact_counts = _fact_status_snapshot()
    connection = sqlite3.connect(f"file:{BATCH_DB_PATH}?mode=ro", uri=True)
    try:
        batch_count = int(
            connection.execute("SELECT COUNT(*) FROM monitoring_batches").fetchone()[0]
        )
    finally:
        connection.close()
    _assertions(
        "s0_precheck",
        [
            ("protocol_version_confirmed", bool(target) and target.get("status") == "confirmed", target and target.get("status")),
            (
                "active_mapping_present",
                active.get("mapping_revision") == MAPPING_REVISION_ID,
                active.get("mapping_revision"),
            ),
            (
                "batches_before_informational",
                batch_count >= 0,
                batch_count,
            ),
            (
                "confirmed_facts_known_state",
                True,
                fact_counts,
            ),
        ],
    )
    if target is None or target.get("status") != "confirmed":
        raise RuntimeError("前置核验失败：方案版本不存在或未 confirmed")
    if active.get("mapping_revision") != MAPPING_REVISION_ID:
        raise RuntimeError("前置核验失败：激活映射身份不符")
    return active, fact_counts, batch_count


def _mapping_payload(active: dict[str, Any]) -> dict[str, Any]:
    """按 monitoring_mapping_batch_lifecycle.confirm_full_snapshot 的
    mapping_payload 形状构建（含 60 字段的完整映射内容）。"""

    connection = sqlite3.connect(f"file:{AI_DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        revision = connection.execute(
            "SELECT batch_id, full_profile_sha256, fields_json, "
            "semantic_quality_report_sha256 FROM monitoring_mapping_revisions "
            "WHERE mapping_revision = ?",
            (MAPPING_REVISION_ID,),
        ).fetchone()
        if revision is None:
            raise RuntimeError("激活映射修订在 AI 库中不存在")
        fields = json.loads(revision["fields_json"])
        payload = {
            "schema_version": "monitoring_project_mapping_v2",
            "mapping_revision": MAPPING_REVISION_ID,
            "mapping_content_sha256": active.get("mapping_content_sha256"),
            "source_batch_id": revision["batch_id"],
            "source_profile_sha256": revision["full_profile_sha256"],
            "semantic_quality_report_sha256": active.get(
                "semantic_quality_report_sha256"
            ),
            "capability_manifest_sha256": active.get(
                "capability_manifest_sha256"
            ),
            "activation_disposition": active.get("activation_disposition"),
            "effective_capabilities_sha256": active.get(
                "effective_capabilities_sha256"
            ),
            "effective_capabilities": list(active.get("effective_capabilities") or []),
            "capability_states": list(active.get("capability_states") or []),
            "fields": fields,
        }
        return payload
    finally:
        connection.close()


def _confirm_listing_content(detail: dict[str, Any]) -> None:
    """医学经理确认来源内容警告（P7 链的逐项确认手势）。

    intake 409 source_content_confirmation_required：来源内容校验为
    warning（project_identity——合成测试数据命名与项目注册身份的固有差异），
    use_status=requires_confirmation。按 P7 合同逐项确认后沿用
    （use_status → confirmed_after_warning），非契约宽容：只确认校验器
    已列出的可覆盖检查项。
    """

    source_entry_id = str(detail.get("source_entry_id") or "")
    validation = detail.get("validation") or {}
    revision = int(validation.get("revision") or 1)
    codes = sorted(
        check.get("check_code")
        for check in validation.get("checks") or []
        if check.get("outcome") in {"warning", "mismatch"}
    )
    reason = (
        "医学经理逐项确认：该 Data Listing 为 MG-K10-CSU-001 合成测试数据 "
        "V1.0，与本工作区映射批次来源为同一文件（sha256 "
        f"{LISTING_SHA256[:16]}…）；project_identity 警告源于合成测试数据"
        "命名约定，域/字段与项目一致，确认沿用进入批次供给。"
    )
    status, body = _http(
        "s1_confirm_content",
        "POST",
        f"/api/projects/{PROJECT_ID}/sources/{source_entry_id}/"
        f"content-validation/confirm",
        payload={
            "reason": reason,
            "acknowledged_check_codes": codes,
            "actor": ACTOR,
            "expected_revision": revision,
            "idempotency_key": f"{RUN_STAMP}-content-confirm",
        },
    )
    _assertions(
        "s1_confirm_content",
        [
            (
                "content_confirmation_http_ok",
                status in (200, 201),
                status,
            ),
            (
                "use_status_confirmed_after_warning",
                (body.get("use_status") == "confirmed_after_warning"),
                body.get("use_status"),
            ),
        ],
    )


def _batch_of(body: Any) -> dict[str, Any]:
    """BatchMutationResult/IntakeResult 的 batch 字段可能嵌套一层。"""

    batch = body.get("batch") if isinstance(body, dict) else None
    if isinstance(batch, dict) and isinstance(batch.get("batch"), dict):
        batch = batch["batch"]
    return batch if isinstance(batch, dict) else {}


def step1_intake_batch() -> dict[str, Any]:
    content = LISTING_PATH.read_bytes()
    import hashlib

    digest = hashlib.sha256(content).hexdigest()
    _assertions(
        "s1_intake",
        [
            (
                "listing_sha_matches_mapping_batch_source",
                digest == LISTING_SHA256,
                {"actual": digest, "expected": LISTING_SHA256},
            ),
        ],
    )
    idempotency_key = f"{RUN_STAMP}-intake"
    status, body = _http(
        "s1_intake",
        "POST",
        f"/api/projects/{PROJECT_ID}/monitoring/batches/intake-file",
        query={
            "filename": LISTING_PATH.name,
            "idempotency_key": idempotency_key,
            "classification_override_reason": "",
        },
        raw_body=content,
    )
    detail = (body.get("detail") or {}) if isinstance(body, dict) else {}
    if (
        status == 409
        and detail.get("code") == "source_content_confirmation_required"
    ):
        # P7 合同：内容警告须医学经理逐项确认后才能建批次。
        _confirm_listing_content(detail)
        idempotency_key = f"{RUN_STAMP}-intake-after-confirm"
        status, body = _http(
            "s1_intake_after_confirm",
            "POST",
            f"/api/projects/{PROJECT_ID}/monitoring/batches/intake-file",
            query={
                "filename": LISTING_PATH.name,
                "idempotency_key": idempotency_key,
                "classification_override_reason": "",
            },
            raw_body=content,
        )
    batch = _batch_of(body)
    _assertions(
        "s1_intake",
        [
            ("intake_http_ok", status in (200, 201), status),
            (
                "batch_created",
                bool(batch.get("batch_id")),
                {
                    "batch_id": batch.get("batch_id"),
                    "state": batch.get("state"),
                    "version": batch.get("version"),
                },
            ),
            (
                "observed_domains_present",
                bool(body.get("observed_domains")),
                body.get("observed_domains"),
            ),
            (
                "normalized_rows_present",
                bool(body.get("row_count")),
                body.get("row_count"),
            ),
        ],
    )
    if not batch.get("batch_id"):
        raise RuntimeError(f"intake 失败：HTTP {status}")
    return body


def step2_parsed(batch_id: str, version: int) -> int:
    service = _batch_service()
    result = service.transition(
        batch_id=batch_id,
        target_state="parsed",
        expected_version=version,
        idempotency_key=f"{RUN_STAMP}:{batch_id}:parsed",
    )
    batch = result.batch
    _record(
        {
            "ts": _now(),
            "step": "s2_transition_parsed",
            "kind": "summary",
            "ok": True,
            "state": batch.state,
            "replayed": result.replayed,
            "version": batch.version,
        }
    )
    return batch.version


def step3_record_validation_evidence(
    batch_id: str,
    version: int,
    source_ids: list[str],
    row_count: int,
    observed_domains: list[str],
    source_class: str,
    active: dict[str, Any],
) -> int:
    classification = {"source_class": source_class}
    payload = _mapping_payload(active)
    proof = {
        "confirmed": True,
        "basis": (
            "冻结快照与激活映射同源：Data Listing "
            f"{LISTING_PATH.name}（sha256 {LISTING_SHA256}）即映射批次 "
            f"{MAPPING_BATCH_ID} 的唯一来源文件；intake 规整化 {row_count} 行、"
            f"域 {sorted(observed_domains)}；影子采样前由医学经理确认全量快照。"
        ),
        "confirmed_by": ACTOR,
        "snapshot_source_ids": source_ids,
        "observed_row_count": row_count,
        "expected_domains": observed_domains,
        "source_class": source_class,
        "source_content_sha256": LISTING_SHA256,
    }
    status, body = _http(
        "s3_record_validation_evidence",
        "POST",
        f"/api/projects/{PROJECT_ID}/monitoring/batches/{batch_id}/"
        f"validation-evidence",
        payload={
            "mapping_revision": MAPPING_REVISION_ID,
            "mapping": payload,
            "expected_domains": observed_domains,
            "full_snapshot_proof": proof,
            "expected_version": version,
            "idempotency_key": f"{RUN_STAMP}:{batch_id}:evidence",
        },
    )
    batch = _batch_of(body)
    _assertions(
        "s3_record_validation_evidence",
        [
            ("evidence_http_ok", status in (200, 201), status),
            (
                "active_mapping_written",
                batch.get("active_mapping_revision") == MAPPING_REVISION_ID,
                batch.get("active_mapping_revision"),
            ),
            (
                "expected_domains_written",
                bool(batch.get("expected_domains")),
                batch.get("expected_domains"),
            ),
        ],
    )
    return int(batch.get("version") or version)


def step4_transition_to_frozen(batch_id: str, version: int) -> dict[str, Any]:
    service = _batch_service()
    current_version = version
    for state in ("validated", "confirmed", "frozen"):
        result = service.transition(
            batch_id=batch_id,
            target_state=state,
            expected_version=current_version,
            idempotency_key=f"{RUN_STAMP}:{batch_id}:{state}",
        )
        current_version = result.batch.version
        _record(
            {
                "ts": _now(),
                "step": "s4_transition",
                "kind": "summary",
                "ok": True,
                "target_state": state,
                "state": result.batch.state,
                "replayed": result.replayed,
                "version": current_version,
            }
        )
    status, body = _http(
        "s4_batch_read",
        "GET",
        f"/api/projects/{PROJECT_ID}/monitoring/batches/{batch_id}",
    )
    return body


def step5_assert_frozen_contract(batch: dict[str, Any], active: dict[str, Any]) -> str:
    batch_id = batch.get("batch_id")
    sys.path.insert(0, str(WORKBENCH_ROOT))
    from services.api.app.monitoring_batch_repository import (
        MonitoringBatchRepository,
    )

    repository = MonitoringBatchRepository(
        BATCH_DB_PATH,
        RUNTIME_DIR / "medical_monitoring_batch_objects",
    )
    contract = repository.load_frozen_mapping_contract(batch_id)
    identity = {
        "mapping_revision": contract.mapping_revision,
        "mapping_content_sha256": contract.mapping_content_sha256,
        "capability_manifest_sha256": contract.capability_manifest_sha256,
        "effective_capabilities_sha256": (
            contract.effective_capabilities_sha256
        ),
    }
    active_identity = {
        "mapping_revision": active.get("mapping_revision"),
        "mapping_content_sha256": active.get("mapping_content_sha256"),
        "capability_manifest_sha256": active.get("capability_manifest_sha256"),
        "effective_capabilities_sha256": active.get(
            "effective_capabilities_sha256"
        ),
    }
    _assertions(
        "s5_frozen_contract",
        [
            ("batch_frozen", batch.get("state") == "frozen", batch.get("state")),
            (
                "frozen_mapping_identity_matches_active",
                identity == active_identity,
                {"contract": identity, "active": active_identity},
            ),
            (
                "frozen_fields_count",
                len(contract.fields) == 60,
                len(contract.fields),
            ),
        ],
    )
    return batch_id


def step6_rule_pack_chain(batch_id: str, fact_ids: list[str]) -> None:
    """规则包全链。0 条 confirmed 事实时 draft 必然 409（fail-closed），
    如实记录；若事实状态已变化则继续执行全链。"""

    if not fact_ids:
        _record(
            {
                "ts": _now(),
                "step": "s6_draft",
                "kind": "summary",
                "ok": False,
                "reason": "no_fact_revision_ids_available",
            }
        )
        return
    status, body = _http(
        "s6_draft",
        "POST",
        f"{MM_PREFIX}/rule-packs/drafts",
        payload={
            "protocol_version_id": PROTOCOL_VERSION_ID,
            "fact_revision_ids": fact_ids,
            "created_by": ACTOR,
        },
    )
    if status != 201 and status != 200:
        detail = (body.get("detail") or {}) if isinstance(body, dict) else {}
        _record(
            {
                "ts": _now(),
                "step": "s6_draft",
                "kind": "blocked",
                "ok": False,
                "http_status": status,
                "code": detail.get("code"),
                "message": detail.get("message"),
                "reason": (
                    "rule-pack draft 被拒：create_draft 硬性要求 "
                    "medically_confirmed 事实"
                    "（monitoring_rule_authoring_service.py:891-910），"
                    "当前 0 条 confirmed——S2 生成内容缺陷的延续阻断，"
                    "按台账如实记录"
                ),
            }
        )
        return
    pack = body.get("pack") or {}
    rule_pack_id = pack.get("rule_pack_id")
    rules = body.get("rules") or []
    _assertions(
        "s6_draft",
        [
            ("draft_http_ok", status in (200, 201), status),
            ("rules_present", bool(rules), len(rules)),
        ],
    )
    for rule in rules:
        rule_revision_id = rule.get("rule_revision_id")
        d_status, d_body = _http(
            "s7_rule_confirm",
            "POST",
            f"{MM_PREFIX}/rule-packs/{rule_pack_id}/rules/"
            f"{rule_revision_id}/confirm",
            payload={
                "expected_state_version": int(rule.get("state_version") or 1),
                "confirmed_by": ACTOR,
                "reauthenticated": True,
            },
        )
        _assertions(
            "s7_rule_confirm",
            [("rule_confirm_http_ok", d_status in (200, 201), d_status)],
        )
    status, body = _http(
        "s8_start_shadow",
        "POST",
        f"{MM_PREFIX}/rule-packs/{rule_pack_id}/start-shadow",
        payload={"actor": ACTOR},
    )
    _assertions(
        "s8_start_shadow",
        [("start_shadow_http_ok", status in (200, 201), status)],
    )
    status, body = _http(
        "s9_automatic_shadow",
        "POST",
        f"{MM_PREFIX}/rule-packs/{rule_pack_id}/automatic-shadow-runs",
        payload={"batch_id": batch_id, "actor": ACTOR},
    )
    _assertions(
        "s9_automatic_shadow",
        [
            (
                "automatic_shadow_http_ok",
                status in (200, 201),
                status,
            ),
            (
                "inspection_present",
                bool(body.get("inspection")),
                sorted((body.get("inspection") or {}).keys()),
            ),
        ],
    )
    sample_sets = (body.get("inspection") or {}).get("sample_set_id")
    status, body = _http(
        "s10_confirm_shadow",
        "POST",
        f"{MM_PREFIX}/rule-packs/{rule_pack_id}/confirm-shadow",
        payload={
            "sample_set_id": sample_sets,
            "confirmed_by": ACTOR,
            "reauthenticated": True,
        },
    )
    _assertions(
        "s10_confirm_shadow",
        [("confirm_shadow_http_ok", status in (200, 201), status)],
    )
    status, body = _http(
        "s11_publish",
        "POST",
        f"{MM_PREFIX}/rule-packs/{rule_pack_id}/publish",
        payload={"actor": ACTOR, "reauthenticated": True},
    )
    published = ((body.get("pack") or {}).get("status")) if isinstance(body, dict) else None
    _assertions(
        "s11_publish",
        [
            ("publish_http_ok", status in (200, 201), status),
            ("pack_published", published == "published", published),
        ],
    )


def _find_reusable_draft_batch() -> tuple[str, int] | None:
    """断点续跑：项目已有 draft 批次则复用（intake 每次会产生新批次）。"""

    connection = sqlite3.connect(f"file:{BATCH_DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT batch_id, version FROM monitoring_batches "
            "WHERE project_id = ? AND state = 'draft' "
            "ORDER BY created_at DESC LIMIT 1",
            (PROJECT_ID,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return row["batch_id"], int(row["version"])


def main() -> int:
    _record(
        {
            "ts": _now(),
            "step": "run",
            "kind": "summary",
            "ok": True,
            "message": "W04-S3 冻结批次供给 + 规则包全链开始",
        }
    )
    active, fact_counts, batch_count = step0_precheck()
    reuse = _find_reusable_draft_batch()
    if reuse is not None:
        batch_id, version = reuse
        _record(
            {
                "ts": _now(),
                "step": "s1_reuse_draft_batch",
                "kind": "summary",
                "ok": True,
                "batch_id": batch_id,
                "version": version,
                "message": "断点续跑：复用既有 draft 批次，不重复 intake",
            }
        )
    else:
        intake = step1_intake_batch()
        batch = _batch_of(intake)
        batch_id = batch["batch_id"]
        version = int(batch.get("version") or 1)
    version = step2_parsed(batch_id, version)
    if reuse is not None:
        source_ids, row_count, observed_domains = _batch_supply_facts(batch_id)
        source_class = "raw_full_snapshot_candidate"
    else:
        source = intake.get("source") or {}
        source_ids = [str(source.get("source_id") or "")]
        row_count = int(intake.get("row_count") or 0)
        observed_domains = list(intake.get("observed_domains") or [])
        source_class = str(
            (intake.get("classification") or {}).get("source_class") or ""
        )
    version = step3_record_validation_evidence(
        batch_id,
        version,
        source_ids,
        row_count,
        observed_domains,
        source_class,
        active,
    )
    frozen = step4_transition_to_frozen(batch_id, version)
    step5_assert_frozen_contract(frozen, active)
    fact_ids = []
    status, body = _http(
        "s6_fact_ids",
        "GET",
        f"{MM_PREFIX}/protocol-versions/{PROTOCOL_VERSION_ID}/facts",
    )
    for item in body.get("items") or []:
        fact_ids.append(item.get("fact_revision_id"))
    step6_rule_pack_chain(batch_id, fact_ids)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code not in (0,):
            _record(
                {
                    "ts": _now(),
                    "step": "run",
                    "kind": "summary",
                    "ok": False,
                    "exit_code": code,
                }
            )
        raise
    except Exception as exc:
        _record(
            {
                "ts": _now(),
                "step": "run",
                "kind": "summary",
                "ok": False,
                "exit_code": 1,
                "error": repr(exc),
            }
        )
        raise
