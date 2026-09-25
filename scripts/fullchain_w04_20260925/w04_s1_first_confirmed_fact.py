"""W04-S1 最小纵切：真实 CSU 方案上跑通 提取→候选裁决→模板推荐→事实确认。

编排脚本：不改后端，按序调用既有 API 并逐步断言，产出首条
medically_confirmed 方案事实 + compiled rule。

链路（全部针对运行中的工作台 API，默认 127.0.0.1:8910）：
  0. 前置核验：GET  /protocol-versions 确认 protov_c1f1135117a3838272628759
     已 confirmed，promoted 源为 src_proj_user_2f17492ac59b_protocol_docx_7a346f97d155
     （注册元数据 span_count=2454）。
  1. 激活字段映射：GET /ai/active-mapping 预期 404
     （monitoring_mapping_record_not_found：草稿 monmapdraft_a6a97ff25ed36d2f35ce00c63d5a
      已 confirmed 未激活）。首选按原 idempotency_key 幂等重放 mapping confirm
     路由——repository.confirm 对已确认草稿仅接受同 key 同 payload 重放
     （confirmation_request_sha256 已本地复核一致），confirm 返回后路由内
     必然执行 activate_confirmed_revision（monitoring_ai_router confirm 分支）。
  2. POST protocol-preparation/.../start 仅选 concomitant_medication_policy
     一个主题；轮询 status 至终态（AI 作业经 monitoring_ai_worker 消费）。
  3. 以医学经理身份 POST candidates/{id}/decision accept（低置信度必附
     reason，服务层 511-521 强制），得 fact_revision_id(status=ai_candidate)。
     接受前先只读核验：候选证据 locator/quote 与冻结证据包一致。
  4. POST rule-template-recommendations/facts/{id}/start → 轮询 → candidates/
     {id}/decision accept：响应内含 medically_confirmed 事实 + compiled_rule
     （service decide 内 confirm_fact_and_compile 是唯一可走通的确认路径；
      直连 confirm 因 immutable_identity fail-closed 被拒）。

评估产物：v12 提示词在真实中文方案上的候选质量。候选不可用就如实记录并
以非零码退出上报，绝不凑数接受。

证据：每步原始响应与断言逐行追加到
  runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s1_evidence.jsonl

用法：
  python3 w04_s1_first_confirmed_fact.py            # 全链执行
退出码：0 成功；2 无可用候选（未做任何接受）；1 链路硬失败。
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
EVIDENCE_PATH = EVIDENCE_DIR / "s1_evidence.jsonl"
# 只读核验用：冻结证据包存于运行时 AI 库（与 API 进程同一 WORKBENCH_RUNTIME_DIR）。
RUNTIME_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
)
AI_DB_PATH = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
SOURCE_REGISTRY_PATH = RUNTIME_DIR / "source_registry.jsonl"

BASE_URL = "http://127.0.0.1:8910"
PROJECT_ID = "proj_user_2f17492ac59b"
MM_PREFIX = (
    f"/api/projects/{PROJECT_ID}/modules/medical-monitoring"
)

PROTOCOL_VERSION_ID = "protov_c1f1135117a3838272628759"
EXPECTED_SOURCE_ENTRY_ID = "src_proj_user_2f17492ac59b_protocol_docx_7a346f97d155"
EXPECTED_REGISTERED_SPAN_COUNT = 2454

MAPPING_DRAFT_ID = "monmapdraft_a6a97ff25ed36d2f35ce00c63d5a"
MAPPING_REVISION_ID = "monmaprev_f8677a0050c5af2b3a4894e5e23d"
# 原 confirm 幂等重放载荷：request_sha256 已与库内
# monitoring_mapping_revisions.confirmation_request_sha256 逐字一致
# （2026-09-24 会话实测）。confirmed_by 为遗留兼容字段，服务端以
# principal.server_actor 为准；本地单用户身份恒为 local-user-0249075bebd34158。
MAPPING_CONFIRM_REPLAY = {
    "expected_version": 55,
    "confirmed_by": "local-user-0249075bebd34158",
    "confirmation_reason": (
        "0924V1全链验证：60字段双队列候选，46分歧全部收敛"
        "（28双核裁决+10如实证据缺口+8医学经理裁决），确认进入事实物化"
    ),
    "idempotency_key": "fc-confirm-0924-e37148371006",
}

TOPIC_ID = "concomitant_medication_policy"
TOPIC_ALLOWED_FACT_TYPES = (
    "concomitant_medication_allowed",
    "concomitant_medication_restricted",
    "concomitant_medication_prohibited",
    "concomitant_medication_rescue",
    "concomitant_medication_washout",
)

# 轮询：作业经 monitoring_ai_worker 消费（glm-5.3-flash，高思考，最长可达
# attempt 级 900s×2），给足上限；状态机终态见各步骤集合。
POLL_INTERVAL_SECONDS = 10.0
PREPARATION_TIMEOUT_SECONDS = 3_600.0
RECOMMENDATION_TIMEOUT_SECONDS = 3_600.0

# 提取作业侧终态（topic.status，来自 _topic_status / _overall_status 契约）。
PREPARATION_TERMINAL = {
    "candidate_review",
    "reviewed",
    "failed",
    "blocked",
    "stale_input",
    "cancelled",
    "data_gap",
}
# 推荐作业侧终态（service._status_payload / _manual_review_payload）。
RECOMMENDATION_TERMINAL = {
    "candidate_review",
    "reviewed",
    "manual_review",
    "ready",
    "failed",
    "blocked",
    "stale_input",
}

_BLOB_SECTION_MARKER = "$section_blob"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record(entry: dict[str, Any]) -> None:
    """逐行追加证据（JSONL），同时落标准输出供前台跟随。"""

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
) -> tuple[int, Any]:
    """调用工作台 API 并把原始请求/响应写入证据。"""

    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    body = (
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if payload is not None
        else None
    )
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:  # 4xx/5xx 也照常留证
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


def _materialize_stored_payload(stored_text: str, connection: sqlite3.Connection) -> dict[str, Any]:
    """复刻 repository 的 $section_blob 透明物化（只读副本）。"""

    payload = json.loads(stored_text)
    if not isinstance(payload, dict):
        return payload
    resolved: dict[str, Any] = {}
    for key, value in payload.items():
        marker = (
            isinstance(value, dict)
            and set(value) == {_BLOB_SECTION_MARKER}
            and isinstance(value.get(_BLOB_SECTION_MARKER), str)
        )
        if not marker:
            resolved[key] = value
            continue
        row = connection.execute(
            "SELECT payload_json FROM monitoring_ai_payload_blobs "
            "WHERE blob_sha256 = ?",
            (value[_BLOB_SECTION_MARKER],),
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"monitoring AI payload section blob is missing: {key}"
            )
        resolved[key] = json.loads(row[0])
    return resolved


def _read_job_input_payload(job_id: str) -> dict[str, Any]:
    """只读读取作业冻结输入包（不写库、不影响 API 进程）。"""

    connection = sqlite3.connect(f"file:{AI_DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT input_payload_json FROM monitoring_ai_jobs "
            "WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"job not found in runtime DB: {job_id}")
        return _materialize_stored_payload(row["input_payload_json"], connection)
    finally:
        connection.close()


def _registered_span_count(source_entry_id: str) -> int | None:
    for line in SOURCE_REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line).get("entry") or {}
        if entry.get("entry_id") == source_entry_id:
            metadata = entry.get("metadata") or {}
            value = metadata.get("span_count", entry.get("span_count"))
            return int(value) if value is not None else None
    return None


def _topic_of(status_payload: dict[str, Any]) -> dict[str, Any]:
    for item in status_payload.get("topics") or []:
        if item.get("topic_id") == TOPIC_ID:
            return item
    raise RuntimeError(f"status payload has no topic {TOPIC_ID}")


def step0_precheck() -> None:
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
    _assertions(
        "s0_precheck",
        [
            ("protocol_versions_http_200", status == 200, status),
            (
                "target_version_present",
                target is not None,
                [item.get("protocol_version_id") for item in items],
            ),
            (
                "target_version_confirmed",
                bool(target) and target.get("status") == "confirmed",
                target and target.get("status"),
            ),
            (
                "promoted_source_entry_matches",
                bool(target)
                and target.get("source_entry_id") == EXPECTED_SOURCE_ENTRY_ID,
                target and target.get("source_entry_id"),
            ),
        ],
    )
    if target is None or target.get("status") != "confirmed":
        raise RuntimeError("前置核验失败：方案版本不存在或未 confirmed")
    span_count = _registered_span_count(EXPECTED_SOURCE_ENTRY_ID)
    _assertions(
        "s0_precheck",
        [
            (
                "registered_span_count",
                span_count == EXPECTED_REGISTERED_SPAN_COUNT,
                {"registered": span_count, "expected": EXPECTED_REGISTERED_SPAN_COUNT},
            ),
        ],
    )


def step1_activate_mapping() -> bool:
    """激活字段映射；返回是否已激活。

    2026-09-25 实测：按原 idempotency_key 幂等重放 confirm 路由在
    confirm 仓库层重放成功后，路由内 activate_confirmed_revision 的
    _validate_source_chain fail-closed（409 monitoring_mapping_state_conflict
    "mapping source job set changed after confirmation"）：
    monitoring_mapping_revisions.field_sources 含 20 个作业（primary 10 +
    裁决收据选中的 verifier 10，_effective_field_sources 合并
    adjudicated_mapping 收据所致），而 draft.expected_job_ids 只有
    primary 10 个 —— 双队列裁决收据来源不在期望作业集合内，激活必然
    fail-closed。直调 activate_confirmed_revision 走同一
    _load_valid_confirmed_revision → _validate_source_chain，同样被拒。
    这是后端缺陷（activation 期望作业集合未包含裁决收据来源），
    本切片不改后端，如实记录后放行不依赖映射的后续步骤。
    """

    status, body = _http(
        "s1_active_mapping_before",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    if status == 200:
        _assertions(
            "s1_activate_mapping",
            [
                (
                    "already_active_rerun",
                    body.get("mapping_revision") == MAPPING_REVISION_ID,
                    body.get("mapping_revision"),
                ),
            ],
        )
        return True
    detail = (body.get("detail") or {}) if isinstance(body, dict) else {}
    code = detail.get("code") if isinstance(detail, dict) else None
    _assertions(
        "s1_activate_mapping",
        [
            ("active_mapping_404_before", status == 404, status),
            (
                "not_found_code",
                code == "monitoring_mapping_record_not_found",
                code,
            ),
        ],
    )
    # 首选路径：按原 idempotency_key 幂等重放 confirm 路由；路由在 confirm
    # 返回后必然执行 activate_confirmed_revision（monitoring_ai_router）。
    status, body = _http(
        "s1_confirm_replay",
        "POST",
        f"{MM_PREFIX}/ai/mapping-drafts/{MAPPING_DRAFT_ID}/confirm",
        payload=dict(MAPPING_CONFIRM_REPLAY),
    )
    replayed_revision = body.get("mapping_revision")
    activation = body.get("activation") or {}
    replay_ok = status == 200 and replayed_revision == MAPPING_REVISION_ID
    _assertions(
        "s1_activate_mapping",
        [
            ("confirm_replay_http_200", status == 200, status),
            (
                "revision_matches_original",
                replayed_revision == MAPPING_REVISION_ID,
                replayed_revision,
            ),
            (
                "activation_performed",
                bool(activation),
                sorted(activation.keys()) if isinstance(activation, dict) else activation,
            ),
            (
                "activation_project_version",
                activation.get("project_version") == 1,
                activation.get("project_version"),
            ),
        ],
    )
    if not replay_ok:
        conflict_detail = (
            (body.get("detail") or {}).get("message")
            if isinstance(body, dict)
            else None
        )
        _record(
            {
                "ts": _now(),
                "step": "s1_activate_mapping",
                "kind": "blocked",
                "ok": False,
                "reason": (
                    "mapping_activation_fail_closed：confirm 重放到达激活时被 "
                    "_validate_source_chain 拒绝（双队列裁决收据来源作业不在 "
                    "draft.expected_job_ids 内）。后端缺陷，本切片不改后端，"
                    "如实记录后继续不依赖映射的提取与候选裁决。"
                ),
                "http_status": status,
                "conflict_message": conflict_detail,
            }
        )
        return False
    status, body = _http(
        "s1_active_mapping_after",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    identity = body.get("capability_states") if isinstance(body, dict) else None
    _assertions(
        "s1_activate_mapping",
        [
            ("active_mapping_http_200_after", status == 200, status),
            (
                "active_revision_matches",
                body.get("mapping_revision") == MAPPING_REVISION_ID,
                body.get("mapping_revision"),
            ),
            (
                "capability_manifest_present",
                bool(body.get("capability_manifest_sha256"))
                and bool(body.get("effective_capabilities_sha256")),
                {
                    "capability_manifest_sha256": body.get(
                        "capability_manifest_sha256"
                    ),
                    "effective_capabilities_sha256": body.get(
                        "effective_capabilities_sha256"
                    ),
                    "capability_states": len(identity or []),
                },
            ),
        ],
    )
    if status != 200 or body.get("mapping_revision") != MAPPING_REVISION_ID:
        raise RuntimeError("激活后 active-mapping 校验失败")
    return True


def step1b_authorized_repair() -> bool:
    """经授权的证据驱动状态修复（run owner 2026-09-25 批准，护栏如下）。

    护栏1：修复前先把 draft 的 expected_job_ids_json 原文、confirmed
           revision 的 field_sources 作业来源、待补入作业及其状态全部
           写入本台账；
    护栏2：待补集合程序化推导自 revision.field_sources 与 draft
           expected_job_ids 的差集，不手抄；
    护栏3：修复后走 confirm 重放路由让 API 进程自做激活；若仍被同一或
           新的 fail-closed 拒绝，最多带明确新原因再试一次，否则转选项(b)
           交付（ai_candidate 事实 + 缺陷证据 + blocked 记录）；
    护栏4：缺陷本体以 file:line 记入台账（高严重度后端缺陷），代码修复
           留给后端切片，本脚本不改动任何服务端代码；
    护栏5：本操作在台账如实记为「经授权的证据驱动状态修复」。
    """

    _record(
        {
            "ts": _now(),
            "step": "s1b_repair",
            "kind": "authorization",
            "ok": True,
            "message": (
                "经授权的证据驱动状态修复开始：补齐 draft.expected_job_ids"
                "缺失的裁决收据来源作业（护栏1-5见函数docstring）"
            ),
        }
    )
    # 修复前的基线拒绝原因（护栏3：同因拒绝即停，只有明确新原因才允许
    # 第二次尝试；盲目的同因重试不属于「新原因」）。
    last_rejection: dict[str, Any] = {
        "code": "monitoring_mapping_state_conflict",
        "message": "mapping source job set changed after confirmation",
    }
    for attempt in (1, 2):
        # 护栏1+2：只读取证与程序化推导。
        read = sqlite3.connect(f"file:{AI_DB_PATH}?mode=ro", uri=True)
        read.row_factory = sqlite3.Row
        try:
            draft_row = read.execute(
                "SELECT project_id, expected_job_ids_json FROM "
                "monitoring_mapping_drafts WHERE draft_id = ?",
                (MAPPING_DRAFT_ID,),
            ).fetchone()
            revision_row = read.execute(
                "SELECT input_revision_sha256, batch_id, full_profile_sha256, "
                "full_input_sha256, field_sources_json FROM "
                "monitoring_mapping_revisions WHERE mapping_revision = ?",
                (MAPPING_REVISION_ID,),
            ).fetchone()
            if draft_row is None or revision_row is None:
                raise RuntimeError("draft/revision 在运行库中不存在")
            current_expected = json.loads(draft_row["expected_job_ids_json"])
            field_sources = json.loads(revision_row["field_sources_json"])
            source_job_ids = sorted({s["job_id"] for s in field_sources})
            missing = sorted(set(source_job_ids) - set(current_expected))
            # 每个待补作业的链路证据（与 _validate_source_chain 同判据：
            # 一个作业必须恰好绑定一个候选，且为 accepted、hash 一致）。
            job_evidence = []
            prechecks_ok = True
            for job_id in missing:
                job = read.execute(
                    "SELECT status, task_type, input_revision_sha256, "
                    "prompt_version FROM monitoring_ai_jobs "
                    "WHERE project_id = ? AND job_id = ?",
                    (PROJECT_ID, job_id),
                ).fetchone()
                sources_of_job = [
                    s for s in field_sources if s["job_id"] == job_id
                ]
                candidate_ids = sorted(
                    {s["candidate_id"] for s in sources_of_job}
                )
                candidate_row = None
                candidate_checks: dict[str, bool] = {}
                if job is not None and len(candidate_ids) == 1:
                    candidate_row = read.execute(
                        "SELECT candidate_id, status, candidate_json, "
                        "input_revision_sha256 FROM monitoring_ai_candidates "
                        "WHERE project_id = ? AND job_id = ? AND candidate_id = ?",
                        (PROJECT_ID, job_id, candidate_ids[0]),
                    ).fetchone()
                if candidate_row is not None:
                    candidate_checks = {
                        "accepted": candidate_row["status"] == "accepted",
                        "input_revision_matches_revision": (
                            candidate_row["input_revision_sha256"]
                            == revision_row["input_revision_sha256"]
                        ),
                        "content_hash_matches_field_source": (
                            _canonical_candidate_sha256(
                                candidate_row["candidate_json"]
                            )
                            == sources_of_job[0]["candidate_content_sha256"]
                        ),
                        "prompt_version_matches_job": bool(job)
                        and sources_of_job[0]["prompt_version"]
                        == job["prompt_version"],
                    }
                job_ok = bool(job) and len(candidate_ids) == 1 and all(
                    candidate_checks.values()
                ) and (
                    job["status"] == "completed"
                    and job["task_type"] == "listing_field_mapping"
                    and job["input_revision_sha256"]
                    == revision_row["input_revision_sha256"]
                )
                prechecks_ok = prechecks_ok and job_ok
                job_evidence.append(
                    {
                        "job_id": job_id,
                        "status": job and job["status"],
                        "task_type": job and job["task_type"],
                        "input_revision_matches_revision": bool(job)
                        and job["input_revision_sha256"]
                        == revision_row["input_revision_sha256"],
                        "bound_candidate_ids": candidate_ids,
                        "candidate_checks": candidate_checks,
                        "field_sources_bound": len(sources_of_job),
                        "chain_precheck_passed": job_ok,
                    }
                )
        finally:
            read.close()
        _record(
            {
                "ts": _now(),
                "step": "s1b_repair",
                "kind": "pre_repair_backup",
                "attempt": attempt,
                "draft_id": MAPPING_DRAFT_ID,
                "expected_job_ids_json_verbatim": sorted(current_expected),
                "revision_field_source_jobs": source_job_ids,
                "missing_verifier_jobs": missing,
                "job_chain_evidence": job_evidence,
            }
        )
        if not missing:
            _record(
                {
                    "ts": _now(),
                    "step": "s1b_repair",
                    "kind": "summary",
                    "ok": False,
                    "reason": (
                        "missing_set_empty：无剩余可程序化推导的缺失来源"
                        "（首轮修复已写入或失败另有原因），按护栏3停止修复尝试，"
                        "转选项(b)交付"
                    ),
                    "prior_conflict_message": last_rejection.get("message"),
                    "prior_conflict_code": last_rejection.get("code"),
                }
            )
            return False
        if not prechecks_ok:
            # 镜像预校验发现的失败是激活校验的第二层缺陷证据
            # （monitoring_mapping_activation.py:1378 要求来源作业的
            # input_revision 与 revision 一致，而 verifier 分片输入包
            # 本身不同）。layer-1 修复（expected_job_ids 补齐裁决收据
            # 来源）在事实层面仍然正确——这些作业确实是裁决选中的字段
            # 来源——按授权继续写入，让 API 自身给出 layer-2 的原生拒绝
            # 证据；写入后按护栏3停止（不存在事实正确的第二层数据修复，
            # 改哈希谱系属于伪造，绝不做）。
            _record(
                {
                    "ts": _now(),
                    "step": "s1b_repair",
                    "kind": "summary",
                    "ok": True,
                    "reason": (
                        "layer2_predicted：镜像预校验发现来源作业 "
                        "input_revision 与 revision 不一致（激活校验第二层"
                        "缺陷），layer-1 数据修复仍按授权执行以取得 API "
                        "原生证据"
                    ),
                    "failed_prechecks": [
                        j for j in job_evidence if not j["chain_precheck_passed"]
                    ],
                }
            )

        # 经授权的最小写入：单行单列 CAS 更新（事务内校验原文未变）。
        repaired = sorted(set(current_expected) | set(missing))
        write = sqlite3.connect(str(AI_DB_PATH), timeout=30)
        try:
            write.execute("BEGIN IMMEDIATE")
            row = write.execute(
                "SELECT expected_job_ids_json FROM monitoring_mapping_drafts "
                "WHERE project_id = ? AND draft_id = ?",
                (PROJECT_ID, MAPPING_DRAFT_ID),
            ).fetchone()
            if row is None or json.loads(row[0]) != sorted(current_expected):
                write.rollback()
                _record(
                    {
                        "ts": _now(),
                        "step": "s1b_repair",
                        "kind": "summary",
                        "ok": False,
                        "reason": "cas_failed：draft 行在修复前已被并发修改",
                    }
                )
                return False
            write.execute(
                "UPDATE monitoring_mapping_drafts SET expected_job_ids_json = ? "
                "WHERE project_id = ? AND draft_id = ?",
                (
                    json.dumps(repaired, ensure_ascii=False),
                    PROJECT_ID,
                    MAPPING_DRAFT_ID,
                ),
            )
            write.commit()
        except sqlite3.IntegrityError as exc:
            # 第三层（Schema 层）阻断：trg_mapping_confirmed_draft_no_update
            # （monitoring_mapping_draft_repository.py:1022-1026）把已确认
            # 草稿定为不可变——产品设计的不可变性优先于任何运行时状态修复。
            # 事务已回滚，状态未变。按护栏3停止：转选项(b)交付。
            _record(
                {
                    "ts": _now(),
                    "step": "s1b_repair",
                    "kind": "summary",
                    "ok": False,
                    "reason": (
                        "schema_blocked：已确认草稿被不可变触发器保护，"
                        "数据修复在 Schema 层被拒（产品设计意图：已确认"
                        "草稿不可变）。状态未变，转选项(b)交付。"
                    ),
                    "integrity_error": str(exc),
                    "trigger": "trg_mapping_confirmed_draft_no_update",
                    "trigger_defined_at": (
                        "monitoring_mapping_draft_repository.py:1022-1026"
                    ),
                }
            )
            return False
        finally:
            write.close()
        _record(
            {
                "ts": _now(),
                "step": "s1b_repair",
                "kind": "authorized_state_repair",
                "ok": True,
                "message": (
                    "经授权的证据驱动状态修复：expected_job_ids 由 "
                    f"{len(current_expected)} 补至 {len(repaired)}，"
                    "来源为 confirmed revision 裁决收据选中的 verifier 作业"
                ),
                "repaired_expected_job_ids": repaired,
            }
        )
        # 护栏3：经 API 进程自身重放 confirm 路由执行激活。
        status, body = _http(
            "s1b_confirm_after_repair",
            "POST",
            f"{MM_PREFIX}/ai/mapping-drafts/{MAPPING_DRAFT_ID}/confirm",
            payload=dict(MAPPING_CONFIRM_REPLAY),
        )
        if status == 200 and body.get("mapping_revision") == MAPPING_REVISION_ID:
            break
        detail = (body.get("detail") or {}) if isinstance(body, dict) else {}
        last_rejection = {
            "code": detail.get("code") if isinstance(detail, dict) else None,
            "message": detail.get("message") if isinstance(detail, dict) else None,
        }
        same_as_baseline = (
            last_rejection["message"]
            == "mapping source job set changed after confirmation"
        )
        _record(
            {
                "ts": _now(),
                "step": "s1b_repair",
                "kind": "summary",
                "ok": False,
                "attempt": attempt,
                "reason": (
                    "activation_still_fail_closed_same_reason：修复未解除拒绝，"
                    "按护栏3停止，转选项(b)交付"
                    if same_as_baseline
                    else (
                        "activation_fail_closed_new_reason：出现新拒绝原因，"
                        "按护栏3允许最多一次针对新原因的尝试"
                    )
                ),
                "http_status": status,
                "conflict_code": last_rejection["code"],
                "conflict_message": last_rejection["message"],
            }
        )
        if same_as_baseline:
            return False
    status, body = _http(
        "s1_active_mapping_after",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    _assertions(
        "s1b_repair",
        [
            ("active_mapping_http_200_after_repair", status == 200, status),
            (
                "active_revision_matches",
                body.get("mapping_revision") == MAPPING_REVISION_ID,
                body.get("mapping_revision"),
            ),
            (
                "activation_project_version",
                body.get("project_version") == 1,
                body.get("project_version") if isinstance(body, dict) else None,
            ),
        ],
    )
    return status == 200 and body.get("mapping_revision") == MAPPING_REVISION_ID


def _canonical_candidate_sha256(candidate_json: str) -> str:
    """复刻服务端 content_sha256(json.loads(candidate_json)) 口径。"""

    payload = json.loads(candidate_json)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    import hashlib

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _record_topic_failure_evaluation(topic: dict[str, Any]) -> None:
    """候选不可用：如实记录 v12 候选质量评估（核心评估产物），不凑数。"""

    job = topic.get("job") or {}
    job_id = job.get("job_id")
    status, body = _http(
        "s2_failure_evaluation",
        "GET",
        f"{MM_PREFIX}/ai/jobs/{job_id}",
    )
    job_public = body.get("job") or {}
    candidates = body.get("candidates") or []
    attempt_evidence = []
    try:
        read = sqlite3.connect(f"file:{AI_DB_PATH}?mode=ro", uri=True)
        read.row_factory = sqlite3.Row
        rows = read.execute(
            "SELECT attempt_number, request_sha256, response_sha256, outcome "
            "FROM monitoring_ai_attempts WHERE job_id = ? ORDER BY attempt_number",
            (job_id,),
        ).fetchall()
        for row in rows:
            attempt_evidence.append(dict(row))
        read.close()
    except Exception:
        pass
    _record(
        {
            "ts": _now(),
            "step": "s2_failure_evaluation",
            "kind": "summary",
            "ok": False,
            "reason": (
                "v12候选不可用：provider 输出未通过确定性结构修复门"
                "（fail-closed 正确拒收），主题无可用候选，"
                "按切片要求如实记录并上报，不凑数接受"
            ),
            "topic_id": TOPIC_ID,
            "job": job_public,
            "failure_code": job_public.get("failure_code"),
            "failure_message": job_public.get("failure_message"),
            "attempts_request_response_hashes": attempt_evidence,
            "determinism_note": (
                "若各次尝试 request_sha256 与 response_sha256 逐对相等，"
                "说明 provider 侧按请求缓存响应（HANDOFF 坑3），重试无意义，"
                "需提示词版本推进（后端切片）才能改变请求内容"
            ),
            "candidate_count": len(candidates),
        }
    )


def step2_run_preparation() -> dict[str, Any]:
    # 先看当前状态：已被此前运行启动/耗尽的主题不重复 start。
    status, body = _http(
        "s2_status_precheck",
        "GET",
        f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
        f"{PROTOCOL_VERSION_ID}/status",
    )
    topic = _topic_of(body)
    if topic.get("status") in {
        "failed",
        "blocked",
        "stale_input",
        "cancelled",
    }:
        _record_topic_failure_evaluation(topic)
        raise SystemExit(4)
    if topic.get("status") in {"candidate_review", "reviewed"}:
        _record(
            {
                "ts": _now(),
                "step": "s2_status_precheck",
                "kind": "summary",
                "ok": True,
                "resumed": True,
                "message": "主题已在候选复核/已复核状态，跳过 start",
                "topic_status": topic.get("status"),
            }
        )
        return topic

    status, body = _http(
        "s2_start",
        "POST",
        f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
        f"{PROTOCOL_VERSION_ID}/start",
        payload={"topic_ids": [TOPIC_ID]},
    )
    if status != 202:
        raise RuntimeError(f"start 失败：HTTP {status}")
    topic = _topic_of(body)
    _record(
        {
            "ts": _now(),
            "step": "s2_start",
            "kind": "assertions",
            "assertions": [
                {"check": "start_accepted", "passed": True, "detail": topic.get("status")}
            ],
            "ok": True,
        }
    )

    deadline = time.monotonic() + PREPARATION_TIMEOUT_SECONDS
    polls: list[dict[str, Any]] = []
    while True:
        status, body = _http(
            "s2_poll",
            "GET",
            f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
            f"{PROTOCOL_VERSION_ID}/status",
        )
        topic = _topic_of(body)
        topic_status = topic.get("status")
        job = topic.get("job") or {}
        polls.append(
            {
                "ts": _now(),
                "topic_status": topic_status,
                "job_status": job.get("status"),
                "failure_code": job.get("failure_code"),
            }
        )
        if topic_status in PREPARATION_TERMINAL:
            break
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"提取作业轮询超时（>{PREPARATION_TIMEOUT_SECONDS:.0f}s），"
                f"最后状态 {topic_status}"
            )
        time.sleep(POLL_INTERVAL_SECONDS)

    _record(
        {
            "ts": _now(),
            "step": "s2_poll",
            "kind": "poll_history",
            "polls": polls,
        }
    )
    candidates = topic.get("candidates") or []
    _assertions(
        "s2_poll",
        [
            (
                "topic_terminal_status",
                topic_status in {"candidate_review", "reviewed"},
                topic_status,
            ),
            (
                "job_completed",
                job.get("status") == "completed",
                job.get("status"),
            ),
            (
                "candidates_present",
                bool(candidates),
                len(candidates),
            ),
        ],
    )
    if (
        topic_status not in {"candidate_review", "reviewed"}
        or job.get("status") != "completed"
    ):
        if topic_status in {"failed", "blocked", "stale_input", "cancelled"}:
            _record_topic_failure_evaluation(topic)
            raise SystemExit(4)
        raise RuntimeError(f"提取未进入候选复核：{topic_status} / {job.get('status')}")
    return topic


def _candidate_usability(
    candidate: dict[str, Any],
    frozen_packet_by_id: dict[str, dict[str, Any]],
    source_entry_id: str,
) -> tuple[bool, list[dict[str, Any]]]:
    """医学裁决前的自动化可用性核验（locator/quote 与冻结包一致等）。"""

    checks: list[dict[str, Any]] = []
    structured = candidate.get("structured_payload") or {}
    fact_type = str(structured.get("fact_type") or "").strip()
    checks.append(
        {
            "check": "fact_type_in_topic_scope",
            "passed": fact_type in TOPIC_ALLOWED_FACT_TYPES,
            "detail": fact_type,
        }
    )
    evidence = candidate.get("evidence") or []
    checks.append(
        {
            "check": "evidence_bound",
            "passed": bool(evidence),
            "detail": len(evidence),
        }
    )
    for item in evidence:
        frozen = frozen_packet_by_id.get(item.get("evidence_id"))
        consistent = bool(frozen)
        if frozen is not None:
            consistent = (
                str(frozen.get("locator") or "").strip()
                == str(item.get("locator") or "").strip()
                and str(frozen.get("quote") or "").strip()
                == str(item.get("quote") or "").strip()
                and str(frozen.get("source_entry_id") or "").strip()
                == source_entry_id
            )
        checks.append(
            {
                "check": "evidence_matches_frozen_packet",
                "passed": consistent,
                "detail": {
                    "evidence_id": item.get("evidence_id"),
                    "locator": item.get("locator"),
                },
            }
        )
    required_actions = structured.get("required_actions")
    checks.append(
        {
            "check": "structured_actions_present",
            "passed": bool(required_actions),
            "detail": required_actions if required_actions else structured.get(
                "conditions"
            ),
        }
    )
    return all(item["passed"] for item in checks), checks


def step3_decide_candidate(topic: dict[str, Any]) -> dict[str, Any]:
    candidates = topic.get("candidates") or []
    proposed = [
        item for item in candidates if item.get("status") == "proposed"
    ]
    # v12 提示词候选质量评估产物：全部候选逐个留证。
    _record(
        {
            "ts": _now(),
            "step": "s3_candidate_quality",
            "kind": "candidate_review",
            "topic_id": TOPIC_ID,
            "source_revision": topic.get("source_revision"),
            "candidates": [
                {
                    "candidate_id": item.get("candidate_id"),
                    "title": item.get("title"),
                    "text": item.get("text"),
                    "structured_payload": item.get("structured_payload"),
                    "claims": item.get("claims"),
                    "evidence": item.get("evidence"),
                    "confidence_summary": item.get("confidence_summary"),
                }
                for item in candidates
            ],
        }
    )
    if not proposed:
        # 断点续跑：候选已裁决（此前运行被映射阻断时留下 ai_candidate 事实
        # 草案或已确认事实）。从状态载荷的事实投影接续，不重复裁决。
        draft_resumes = [
            item
            for item in candidates
            if item.get("status") == "accepted"
            and (item.get("fact") or {}).get("status") == "ai_candidate"
        ]
        confirmed_resumes = [
            item
            for item in candidates
            if (item.get("fact") or {}).get("status") == "medically_confirmed"
        ]
        if draft_resumes:
            item = draft_resumes[0]
            fact = dict(item["fact"])
            _record(
                {
                    "ts": _now(),
                    "step": "s3_decide",
                    "kind": "summary",
                    "ok": True,
                    "resumed": True,
                    "message": (
                        "候选已被此前运行接受，从事实投影接续"
                        "（不重复记录决定）"
                    ),
                    "fact": fact,
                }
            )
            return {
                "fact": fact,
                "candidate": item,
                "job_public": {"job_id": topic.get("job", {}).get("job_id")},
                "resumed": True,
            }
        if confirmed_resumes:
            item = confirmed_resumes[0]
            fact = dict(item["fact"])
            _record(
                {
                    "ts": _now(),
                    "step": "s3_decide",
                    "kind": "summary",
                    "ok": True,
                    "resumed": True,
                    "already_confirmed": True,
                    "message": "该候选事实已 medically_confirmed，全链已完成",
                    "fact": fact,
                }
            )
            return {
                "fact": fact,
                "candidate": item,
                "job_public": {"job_id": topic.get("job", {}).get("job_id")},
                "resumed": True,
                "already_confirmed": True,
            }
        _record(
            {
                "ts": _now(),
                "step": "s3_decide",
                "kind": "summary",
                "ok": False,
                "reason": "no_proposed_candidate",
            }
        )
        raise RuntimeError("没有处于 proposed 状态的候选可裁决")

    job = topic.get("job") or {}
    job_id = job.get("job_id")
    status, job_body = _http(
        "s3_job_read",
        "GET",
        f"{MM_PREFIX}/ai/jobs/{job_id}",
    )
    job_public = job_body.get("job") or {}
    _assertions(
        "s3_job_read",
        [
            ("job_read_http_200", status == 200, status),
            (
                "job_provider_recorded",
                bool(job_public.get("provider"))
                and bool(job_public.get("requested_model")),
                {
                    "provider": job_public.get("provider"),
                    "requested_model": job_public.get("requested_model"),
                    "response_model": job_public.get("response_model"),
                    "prompt_version": job_public.get("prompt_version"),
                },
            ),
        ],
    )
    input_revision_sha256 = job_public.get("input_revision_sha256") or ""
    frozen_payload = _read_job_input_payload(str(job_id))
    frozen_packet = frozen_payload.get("evidence_packet") or []
    frozen_by_id = {
        str(item.get("evidence_id") or "").strip(): item
        for item in frozen_packet
        if isinstance(item, dict) and item.get("evidence_id")
    }
    _record(
        {
            "ts": _now(),
            "step": "s3_frozen_packet",
            "kind": "frozen_packet_digest",
            "job_id": job_id,
            "evidence_packet_size": len(frozen_packet),
            "context": frozen_payload.get("context"),
            "source_ids": frozen_payload.get("source_ids"),
        }
    )

    usable: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for candidate in proposed:
        ok, checks = _candidate_usability(
            candidate, frozen_by_id, EXPECTED_SOURCE_ENTRY_ID
        )
        _record(
            {
                "ts": _now(),
                "step": "s3_usability",
                "kind": "assertions",
                "candidate_id": candidate.get("candidate_id"),
                "assertions": checks,
                "ok": ok,
            }
        )
        if ok:
            usable.append((candidate, checks))
    if not usable:
        _record(
            {
                "ts": _now(),
                "step": "s3_decide",
                "kind": "summary",
                "ok": False,
                "reason": (
                    "no_usable_candidate：v12 候选未通过自动化核验"
                    "（事实类型越界/证据与冻结包不一致/缺动作），"
                    "如实上报，不凑数接受"
                ),
            }
        )
        raise SystemExit(2)

    candidate, checks = usable[0]
    structured = candidate.get("structured_payload") or {}
    evidence = (candidate.get("evidence") or [])[0]
    reason = (
        "医学经理复核（W04-S1 编排执行）：候选证据 "
        f"{evidence.get('evidence_id')} 与冻结证据包 locator/quote 逐字一致，"
        f"fact_type={structured.get('fact_type')} 属合并用药政策主题；"
        f"原文：{str(evidence.get('quote') or '')[:200]}"
    )
    status, body = _http(
        "s3_decision",
        "POST",
        f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
        f"{PROTOCOL_VERSION_ID}/candidates/{candidate.get('candidate_id')}/decision",
        payload={
            "decision": "accepted",
            "reason": reason,
            "expected_input_revision_sha256": input_revision_sha256,
            "expected_source_revision": topic.get("source_revision"),
            "proposed_fact_type": structured.get("fact_type"),
        },
    )
    outcome = body.get("outcome") or {}
    fact = outcome.get("fact") or {}
    _assertions(
        "s3_decision",
        [
            ("decision_http_200", status == 200, status),
            (
                "outcome_state",
                outcome.get("state") == "user_confirmed_fact_draft",
                outcome.get("state"),
            ),
            (
                "fact_is_ai_candidate",
                fact.get("status") == "ai_candidate",
                fact.get("status"),
            ),
            (
                "fact_revision_present",
                bool(fact.get("fact_revision_id")),
                fact.get("fact_revision_id"),
            ),
        ],
    )
    if status != 200 or fact.get("status") != "ai_candidate":
        raise RuntimeError("候选接受失败：未得到 ai_candidate 事实草案")
    return {
        "fact": fact,
        "candidate": candidate,
        "job_public": job_public,
    }


def step4_recommend_and_confirm(fact: dict[str, Any]) -> dict[str, Any]:
    fact_revision_id = fact["fact_revision_id"]
    state_version = int(fact.get("state_version") or 1)
    # 模板推荐硬依赖已激活映射（service._prepare 先取 active mapping，
    # 缺失即 409 monitoring_rule_template_mapping_unavailable）。
    status, body = _http(
        "s4_active_mapping_precheck",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    if status != 200:
        _record(
            {
                "ts": _now(),
                "step": "s4_confirm",
                "kind": "summary",
                "ok": False,
                "reason": (
                    "blocked_on_mapping_activation：模板推荐与事实确认需要"
                    "已激活字段映射；激活被后端 fail-closed 缺陷阻断"
                    "（见 s1_activate_mapping/blocked 证据）。"
                    "事实草案已产出（ai_candidate），事实确认留待缺陷修复。"
                ),
                "active_mapping_http_status": status,
                "fact_revision_id": fact_revision_id,
                "fact_status": fact.get("status"),
            }
        )
        raise SystemExit(3)
    status, body = _http(
        "s4_start",
        "POST",
        f"{MM_PREFIX}/rule-template-recommendations/facts/"
        f"{fact_revision_id}/start",
        payload={"expected_fact_state_version": state_version},
    )
    if status != 202:
        raise RuntimeError(f"推荐 start 失败：HTTP {status}")
    _record(
        {
            "ts": _now(),
            "step": "s4_start",
            "kind": "assertions",
            "assertions": [
                {
                    "check": "start_accepted",
                    "passed": body.get("status")
                    in {"ready", "queued", "running", "candidate_review", "reviewed"},
                    "detail": body.get("status"),
                }
            ],
            "ok": True,
        }
    )
    if body.get("status") == "manual_review":
        _record(
            {
                "ts": _now(),
                "step": "s4_manual_review",
                "kind": "summary",
                "ok": False,
                "reason_code": body.get("reason_code"),
                "message": body.get("message"),
            }
        )
        raise RuntimeError(
            f"模板推荐进入人工审阅（{body.get('reason_code')}），如实上报不硬凑"
        )

    deadline = time.monotonic() + RECOMMENDATION_TIMEOUT_SECONDS
    polls: list[dict[str, Any]] = []
    while True:
        status, body = _http(
            "s4_poll",
            "GET",
            f"{MM_PREFIX}/rule-template-recommendations/facts/"
            f"{fact_revision_id}/status",
            query={"expected_fact_state_version": state_version},
        )
        current = body.get("status")
        polls.append({"ts": _now(), "status": current})
        if current in RECOMMENDATION_TERMINAL:
            break
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"推荐作业轮询超时（>{RECOMMENDATION_TIMEOUT_SECONDS:.0f}s），"
                f"最后状态 {current}"
            )
        time.sleep(POLL_INTERVAL_SECONDS)
    _record(
        {
            "ts": _now(),
            "step": "s4_poll",
            "kind": "poll_history",
            "polls": polls,
        }
    )
    recommendations = body.get("candidates") or []
    _record(
        {
            "ts": _now(),
            "step": "s4_recommendations",
            "kind": "candidate_review",
            "fact_revision_id": fact_revision_id,
            "status": body.get("status"),
            "failure": body.get("failure"),
            "context": {
                key: value
                for key, value in (body.items())
                if key in {"fact", "mapping", "input_revision_sha256"}
            },
            "candidates": recommendations,
        }
    )
    proposed = [
        item for item in recommendations if item.get("status") == "proposed"
    ]
    accepted = [
        item for item in recommendations if item.get("status") == "accepted"
    ]
    replay_targets = [
        item for item in accepted if item.get("candidate_id")
    ]
    if body.get("status") == "reviewed" and not proposed and replay_targets:
        # 断点续跑：建议已被此前运行选择，decide 的 confirmed_replay 会
        # 幂等返回既定事实与规则（不产生新决定）。
        candidate = replay_targets[0]
        _record(
            {
                "ts": _now(),
                "step": "s4_confirm",
                "kind": "summary",
                "ok": True,
                "resumed": True,
                "message": "建议已被此前运行选择，走 decide 幂等重放",
            }
        )
    elif body.get("status") != "candidate_review" or not proposed:
        _record(
            {
                "ts": _now(),
                "step": "s4_confirm",
                "kind": "summary",
                "ok": False,
                "reason": "no_proposed_recommendation",
                "status": body.get("status"),
            }
        )
        raise RuntimeError("模板推荐未产出可选择项，如实上报")
    else:
        candidate = proposed[0]
    input_revision = str(body.get("input_revision_sha256") or "")
    fact_context = body.get("fact") or {}
    expected_state = int(fact_context.get("state_version") or state_version)
    reason = (
        "医学经理复核（W04-S1 编排执行）：建议 "
        f"{candidate.get('rule_family')} 与已接受事实类型一致，"
        f"确定性模板映射字段 {candidate.get('mapping_fields')}；"
        "选择即确认事实并编译规则。"
    )
    status, body = _http(
        "s4_decision",
        "POST",
        f"{MM_PREFIX}/rule-template-recommendations/facts/{fact_revision_id}"
        f"/candidates/{candidate.get('candidate_id')}/decision",
        payload={
            "decision": "accepted",
            "reason": reason,
            "expected_input_revision_sha256": input_revision,
            "expected_fact_state_version": expected_state,
        },
    )
    confirmed_fact = body.get("confirmed_fact") or {}
    compiled_rule = body.get("compiled_rule") or {}
    identity = compiled_rule.get("immutable_identity") or {}
    quadruple = {
        name: bool(str(identity.get(name) or "").strip())
        for name in (
            "mapping_revision",
            "mapping_content_sha256",
            "capability_manifest_sha256",
            "effective_capabilities_sha256",
        )
    }
    _assertions(
        "s4_decision",
        [
            ("decision_http_200", status == 200, status),
            (
                "rule_template_selected",
                body.get("status") == "rule_template_selected",
                body.get("status"),
            ),
            (
                "fact_medically_confirmed",
                confirmed_fact.get("status") == "medically_confirmed",
                confirmed_fact.get("status"),
            ),
            (
                "compiled_rule_present",
                bool(compiled_rule.get("rule_id") or compiled_rule.get("rule")),
                sorted(compiled_rule.keys()) if isinstance(compiled_rule, dict) else None,
            ),
            (
                "immutable_identity_quadruple_complete",
                all(quadruple.values()),
                {
                    **quadruple,
                    "recommendation_candidate_id": identity.get(
                        "recommendation_candidate_id"
                    ),
                },
            ),
            (
                "identity_binds_this_recommendation",
                identity.get("recommendation_candidate_id")
                == candidate.get("candidate_id"),
                identity.get("recommendation_candidate_id"),
            ),
        ],
    )
    if confirmed_fact.get("status") != "medically_confirmed":
        raise RuntimeError("事实确认失败：未得到 medically_confirmed 事实")
    return {
        "confirmed_fact": confirmed_fact,
        "compiled_rule": compiled_rule,
    }


def step5_final_state(confirmed_fact: dict[str, Any]) -> None:
    status, body = _http(
        "s5_final_facts",
        "GET",
        f"{MM_PREFIX}/protocol-versions/{PROTOCOL_VERSION_ID}/facts",
    )
    fact_revision_id = confirmed_fact.get("fact_revision_id")
    items = body.get("items") or []
    target = next(
        (
            item
            for item in items
            if item.get("fact_revision_id") == fact_revision_id
        ),
        None,
    )
    _assertions(
        "s5_final_facts",
        [
            ("facts_http_200", status == 200, status),
            (
                "confirmed_fact_persisted",
                bool(target),
                [item.get("fact_revision_id") for item in items],
            ),
            (
                "persisted_status_medically_confirmed",
                bool(target) and target.get("status") == "medically_confirmed",
                target and target.get("status"),
            ),
        ],
    )


def main() -> int:
    _record(
        {
            "ts": _now(),
            "step": "run",
            "kind": "summary",
            "ok": True,
            "message": "W04-S1 最小纵切开始",
            "base_url": BASE_URL,
            "project_id": PROJECT_ID,
            "protocol_version_id": PROTOCOL_VERSION_ID,
            "topic_id": TOPIC_ID,
        }
    )
    step0_precheck()
    mapping_active = step1_activate_mapping()
    if not mapping_active:
        mapping_active = step1b_authorized_repair()
    topic = step2_run_preparation()
    decided = step3_decide_candidate(topic)
    if decided.get("already_confirmed"):
        _record(
            {
                "ts": _now(),
                "step": "run",
                "kind": "summary",
                "ok": True,
                "message": (
                    "断点续跑检测到全链此前已完成，仅做最终状态核验"
                ),
            }
        )
        step5_final_state(decided["fact"])
        return 0
    if not mapping_active:
        _record(
            {
                "ts": _now(),
                "step": "run",
                "kind": "defect_ledger",
                "ok": False,
                "severity": "high",
                "defect_id": "monitoring_mapping_dual_queue_activation_fail_closed",
                "defect": {
                    "layer_1": (
                        "monitoring_mapping_activation.py:1344-1351 "
                        "_validate_source_chain 要求 revision.field_sources "
                        "的作业集合与 draft.expected_job_ids 完全相等；而 "
                        "confirm 侧 _effective_field_sources"
                        "（monitoring_mapping_draft_repository.py:2270-2310）"
                        "会把 adjudicated_mapping 裁决收据选中的 verifier "
                        "作业并入 field_sources——该集合必然超出 "
                        "expected_job_ids（primary 装配作业）→ 激活被拒 "
                        "'mapping source job set changed after confirmation'"
                    ),
                    "layer_2": (
                        "monitoring_mapping_activation.py:1378 每个来源作业"
                        "要求 job.input_revision_sha256 等于 "
                        "revision.input_revision_sha256；双队列 verifier "
                        "分片的输入包本身不同（实测 verifier 全部 "
                        "4369d415…，primary/revision 5578ead5…）→ 即使补齐"
                        "作业集合，verifier 来源仍被拒 "
                        "'mapping source job input hash changed'"
                    ),
                    "layer_3_schema_guard": (
                        "经授权的数据修复在 Schema 层被拒："
                        "trg_mapping_confirmed_draft_no_update"
                        "（monitoring_mapping_draft_repository.py:1022-1026）"
                        "对已确认草稿的任何 UPDATE RAISE(ABORT) "
                        "'confirmed mapping draft is immutable'——产品设计"
                        "明确已确认草稿不可变，运行时状态修复路线被产品"
                        "自身的不变量排除"
                    ),
                    "consequence": (
                        "经双队列裁决确认的字段映射 revision 永远无法激活，"
                        "规则模板推荐→事实确认链不可达；产品层面映射确认"
                        "与激活之间断链"
                    ),
                    "proper_fix": (
                        "激活校验应承认裁决收据来源为合法来源：以 "
                        "field_source 自带的 input_revision_sha256/"
                        "prompt_version（随源记录）校验对应作业，而不是要求"
                        "与 revision 主输入修订一致；留给后端修复切片"
                    ),
                },
            }
        )
        raise SystemExit(3)
    confirmed = step4_recommend_and_confirm(decided["fact"])
    step5_final_state(confirmed["confirmed_fact"])
    _record(
        {
            "ts": _now(),
            "step": "run",
            "kind": "summary",
            "ok": True,
            "message": (
                "W04-S1 最小纵切完成：首条 medically_confirmed 事实 + "
                "compiled rule 已产出"
            ),
            "fact_revision_id": confirmed["confirmed_fact"].get(
                "fact_revision_id"
            ),
            "rule": {
                key: value
                for key, value in confirmed["compiled_rule"].items()
                if key in {"rule_id", "rule", "status", "fact_key", "title"}
            },
        }
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:  # 诚实上报路径（无可接受候选等）
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
    except Exception as exc:  # 硬失败：留证后上抛
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
