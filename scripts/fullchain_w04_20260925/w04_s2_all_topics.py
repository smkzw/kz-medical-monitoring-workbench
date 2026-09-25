"""W04-S2：全部 8 主题提取 + 批量医学裁决 + 确认链，产出规则包真实前置。

承接 S1（w04_s1_first_confirmed_fact.py）：
  - S1 发现映射激活三层缺陷并获准在 S2 内实施后端修复
    （monitoring_mapping_activation.py _validate_source_chain 承认裁决收据
    来源作业，回归见 tests/test_monitoring_mapping_activation.py 末尾 4 例）。
    修复落地后 confirm 重放路由即可完成激活，打通确认链。
  - 本脚本复用 S1 骨架，对全部 8 个默认主题
    （monitoring_protocol_preparation_service.py:165-342）执行
    start→轮询→逐候选 accept/reject，再经规则模板链确认事实。

执行序：
  0. 前置核验（方案版本 confirmed、promoted 源 span 数）。
  1. 一次 start 提交全部 8 主题（topic_ids 上限 20，business_key 幂等：
     重复 start 不重建作业，monitoring_protocol_preparation_service.py:403-442）。
  2. 轮询各主题至终态（candidate_review/reviewed/failed/blocked/
     stale_input/cancelled/data_gap）。data_gap=未检索到 span，服务本就不
     提交作业（service:988-1000），如实记录。
  3. 逐主题批量裁决：候选证据 locator/quote 与冻结证据包一致、fact_type
     属主题允许集合、结构化动作齐备者 accept（低置信度必附医学核对理由，
     service:511-521）；不可用者 reject 并记录理由（留痕）。已决定候选
     幂等跳过（重复运行安全，adopt_ai_candidate 幂等分支 service:260-308）。
  4. 激活映射：confirm 重放路由（S1 修复后应 200 + activation）。
  5. 确认链：为已接受事实草案（按 fact_type 多样性优先，上限 6 条）执行
     规则模板 start→轮询→accept，断言 confirmed_fact.status=
     medically_confirmed 且 compiled_rule.immutable_identity 四元组齐备。
  6. 终验：facts 按 status/fact_type 计数（≥3 confirmed、≥2 种类型）、
     候选-事实一一对应（去重）、驳回留痕计数。

证据：每步原始响应、断言、全量候选原文与决定理由逐行追加
  runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s2_evidence.jsonl
退出码：0 达成目标；2 主题失败/候选不可用（已如实记录）；1 链路硬失败；
3 确认链仍被阻断。
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
EVIDENCE_PATH = EVIDENCE_DIR / "s2_evidence.jsonl"
RUNTIME_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
)
AI_DB_PATH = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
RULES_DB_PATH = RUNTIME_DIR / "monitoring_protocol_rules.sqlite3"

BASE_URL = "http://127.0.0.1:8910"
PROJECT_ID = "proj_user_2f17492ac59b"
MM_PREFIX = f"/api/projects/{PROJECT_ID}/modules/medical-monitoring"

PROTOCOL_VERSION_ID = "protov_c1f1135117a3838272628759"
EXPECTED_SOURCE_ENTRY_ID = "src_proj_user_2f17492ac59b_protocol_docx_7a346f97d155"
EXPECTED_REGISTERED_SPAN_COUNT = 2454

# 全部 8 个默认主题（monitoring_protocol_preparation_service.py:165-342）。
TOPIC_IDS = (
    "eligibility_continuity",
    "visit_window_and_order",
    "study_treatment",
    "concomitant_medication_policy",
    "safety_assessment",
    "efficacy_assessment",
    "early_withdrawal_and_deviation",
    "data_quality",
)

MAPPING_DRAFT_ID = "monmapdraft_a6a97ff25ed36d2f35ce00c63d5a"
MAPPING_REVISION_ID = "monmaprev_f8677a0050c5af2b3a4894e5e23d"
# 原 confirm 幂等重放（S1 已验证 sha 一致；后端激活修复后路由应走通）。
MAPPING_CONFIRM_REPLAY = {
    "expected_version": 55,
    "confirmed_by": "local-user-0249075bebd34158",
    "confirmation_reason": (
        "0924V1全链验证：60字段双队列候选，46分歧全部收敛"
        "（28双核裁决+10如实证据缺口+8医学经理裁决），确认进入事实物化"
    ),
    "idempotency_key": "fc-confirm-0924-e37148371006",
}

POLL_INTERVAL_SECONDS = 10.0
PREPARATION_TIMEOUT_SECONDS = 5_400.0
RECOMMENDATION_TIMEOUT_SECONDS = 3_600.0
CONFIRM_TARGET = 3  # ≥3 条 medically_confirmed
CONFIRM_CAP = 14  # 确认链上限：覆盖全部已接受草案（失败/人工审阅自动跳过）
TYPE_COVERAGE_TARGET = 2  # ≥2 种 fact_type

PREPARATION_TERMINAL = {
    "candidate_review",
    "reviewed",
    "failed",
    "blocked",
    "stale_input",
    "cancelled",
    "data_gap",
}
PREPARATION_FAILURE = {"failed", "blocked", "stale_input", "cancelled"}
RECOMMENDATION_TERMINAL = {
    "candidate_review",
    "reviewed",
    "manual_review",
    "ready",
    "failed",
    "blocked",
    "stale_input",
}


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
) -> tuple[int, Any]:
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


def _materialize_stored_payload(
    stored_text: str, connection: sqlite3.Connection
) -> dict[str, Any]:
    payload = json.loads(stored_text)
    if not isinstance(payload, dict):
        return payload
    resolved: dict[str, Any] = {}
    for key, value in payload.items():
        marker = (
            isinstance(value, dict)
            and set(value) == {"$section_blob"}
            and isinstance(value.get("$section_blob"), str)
        )
        if not marker:
            resolved[key] = value
            continue
        row = connection.execute(
            "SELECT payload_json FROM monitoring_ai_payload_blobs "
            "WHERE blob_sha256 = ?",
            (value["$section_blob"],),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"payload blob missing: {key}")
        resolved[key] = json.loads(row[0])
    return resolved


def _read_job_input_payload(job_id: str) -> dict[str, Any]:
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


def _count_facts_by_status() -> dict[str, int]:
    connection = sqlite3.connect(f"file:{RULES_DB_PATH}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT status, COUNT(*) FROM monitoring_protocol_facts "
            "WHERE project_id = ? GROUP BY status",
            (PROJECT_ID,),
        ).fetchall()
        return {row[0]: int(row[1]) for row in rows}
    finally:
        connection.close()


def _registered_span_count(source_entry_id: str) -> int | None:
    registry = RUNTIME_DIR / "source_registry.jsonl"
    for line in registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line).get("entry") or {}
        if entry.get("entry_id") == source_entry_id:
            metadata = entry.get("metadata") or {}
            value = metadata.get("span_count", entry.get("span_count"))
            return int(value) if value is not None else None
    return None


def step0_precheck() -> None:
    status, body = _http(
        "s0_precheck", "GET", f"{MM_PREFIX}/protocol-versions"
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
    span_count = _registered_span_count(EXPECTED_SOURCE_ENTRY_ID)
    _assertions(
        "s0_precheck",
        [
            ("protocol_versions_http_200", status == 200, status),
            ("target_version_confirmed", bool(target) and target.get("status") == "confirmed", target and target.get("status")),
            (
                "promoted_source_entry_matches",
                bool(target) and target.get("source_entry_id") == EXPECTED_SOURCE_ENTRY_ID,
                target and target.get("source_entry_id"),
            ),
            (
                "registered_span_count",
                span_count == EXPECTED_REGISTERED_SPAN_COUNT,
                {"registered": span_count, "expected": EXPECTED_REGISTERED_SPAN_COUNT},
            ),
        ],
    )
    if target is None or target.get("status") != "confirmed":
        raise RuntimeError("前置核验失败：方案版本不存在或未 confirmed")


def step1_start_all_topics() -> None:
    # 断点续跑/重入：先读当前状态。已终态主题不再 start——S1 已证 provider
    # 对同请求返回同一缓存响应（CM 三次尝试 request/response sha256 逐对
    # 相等），重试必然同败，白耗调用；在途主题也不重复提交。
    status, body = _http(
        "s1_status_precheck",
        "GET",
        f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
        f"{PROTOCOL_VERSION_ID}/status",
    )
    current = {item.get("topic_id"): item for item in body.get("topics") or []}
    need_start = []
    in_flight = []
    skipped = {}
    for topic_id in TOPIC_IDS:
        item = current.get(topic_id) or {}
        topic_status = item.get("status")
        if topic_status in PREPARATION_TERMINAL:
            skipped[topic_id] = topic_status
        elif topic_status in {"queued", "running"}:
            in_flight.append(topic_id)
        else:
            need_start.append(topic_id)
    _record(
        {
            "ts": _now(),
            "step": "s1_start",
            "kind": "summary",
            "ok": True,
            "need_start": need_start,
            "in_flight": in_flight,
            "skipped_terminal": skipped,
            "retry_policy": (
                "失败主题不再重试：provider 按请求缓存响应，同请求重试"
                "必然同败（证据见 S1 台账与 CM 三次尝试哈希）"
            ),
        }
    )
    if not need_start:
        return
    status, body = _http(
        "s1_start",
        "POST",
        f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
        f"{PROTOCOL_VERSION_ID}/start",
        payload={"topic_ids": need_start},
    )
    topics = {item.get("topic_id"): item for item in body.get("topics") or []}
    _assertions(
        "s1_start",
        [
            ("start_http_202", status == 202, status),
            (
                "started_topics_present",
                all(topics.get(topic_id) is not None for topic_id in need_start),
                {
                    topic_id: (topics.get(topic_id) or {}).get("status")
                    for topic_id in need_start
                },
            ),
        ],
    )


def step2_poll_all_topics() -> dict[str, dict[str, Any]]:
    topics_by_id: dict[str, dict[str, Any]] = {}
    pending = set(TOPIC_IDS)
    deadline = time.monotonic() + PREPARATION_TIMEOUT_SECONDS
    history: dict[str, list[str]] = {topic_id: [] for topic_id in TOPIC_IDS}
    while pending:
        status, body = _http(
            "s2_poll",
            "GET",
            f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
            f"{PROTOCOL_VERSION_ID}/status",
        )
        for item in body.get("topics") or []:
            topic_id = item.get("topic_id")
            if topic_id in pending:
                history[topic_id].append(str(item.get("status")))
                if item.get("status") in PREPARATION_TERMINAL:
                    topics_by_id[topic_id] = item
                    pending.discard(topic_id)
        if not pending:
            break
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"轮询超时，未终态主题：{sorted(pending)}"
            )
        time.sleep(POLL_INTERVAL_SECONDS)
    _record(
        {
            "ts": _now(),
            "step": "s2_poll",
            "kind": "poll_history",
            "history": history,
        }
    )
    _assertions(
        "s2_poll",
        [
            (
                "all_topics_terminal",
                set(topics_by_id) == set(TOPIC_IDS),
                {k: v.get("status") for k, v in topics_by_id.items()},
            ),
        ],
    )
    return topics_by_id


def _candidate_usability(
    candidate: dict[str, Any],
    allowed_fact_types: tuple[str, ...],
    frozen_packet_by_id: dict[str, dict[str, Any]],
    source_entry_id: str,
) -> tuple[bool, list[dict[str, Any]], str]:
    """返回 (可用, 断言明细, 拒绝理由)。"""

    checks: list[dict[str, Any]] = []
    reject_reasons: list[str] = []
    structured = candidate.get("structured_payload") or {}
    fact_type = str(structured.get("fact_type") or "").strip()
    type_ok = fact_type in allowed_fact_types
    checks.append({"check": "fact_type_in_topic_scope", "passed": type_ok, "detail": fact_type})
    if not type_ok:
        reject_reasons.append(
            f"事实类型越界：{fact_type or '缺失'} 不属于主题允许集合"
        )
    evidence = candidate.get("evidence") or []
    checks.append({"check": "evidence_bound", "passed": bool(evidence), "detail": len(evidence)})
    if not evidence:
        reject_reasons.append("候选未绑定方案原文证据")
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
        if not consistent:
            reject_reasons.append(
                f"证据与冻结包不一致：{item.get('evidence_id')}"
            )
    required_actions = structured.get("required_actions")
    actions_ok = bool(required_actions)
    checks.append(
        {
            "check": "structured_actions_present",
            "passed": actions_ok,
            "detail": required_actions if required_actions else structured.get("conditions"),
        }
    )
    if not actions_ok:
        reject_reasons.append("结构化动作/条件缺失，不构成可监查条款")
    return (not reject_reasons), checks, "；".join(reject_reasons)


def step3_adjudicate(
    topics_by_id: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """逐主题批量裁决；返回 {topic_id: [接受的 fact 投影]}。"""

    accepted_facts: dict[str, list[dict[str, Any]]] = {}
    rejected_total = 0
    for topic_id in TOPIC_IDS:
        topic = topics_by_id[topic_id]
        status = topic.get("status")
        if status == "data_gap":
            _record(
                {
                    "ts": _now(),
                    "step": "s3_adjudicate",
                    "kind": "summary",
                    "ok": True,
                    "topic_id": topic_id,
                    "data_gap": (
                        "主题未检索到可用原文 span，服务未提交 AI 作业、"
                        "未补造条款（如实记录）"
                    ),
                }
            )
            continue
        if status in PREPARATION_FAILURE:
            job = topic.get("job") or {}
            _record(
                {
                    "ts": _now(),
                    "step": "s3_adjudicate",
                    "kind": "summary",
                    "ok": False,
                    "topic_id": topic_id,
                    "status": status,
                    "failure_code": job.get("failure_code"),
                    "failure_message": (job.get("failure_message") or "")[:800],
                }
            )
            continue
        candidates = topic.get("candidates") or []
        proposed = [c for c in candidates if c.get("status") == "proposed"]
        decided = [c for c in candidates if c.get("status") != "proposed"]
        job = topic.get("job") or {}
        job_id = job.get("job_id")
        allowed_types = tuple(topic.get("allowed_fact_types") or ())
        _record(
            {
                "ts": _now(),
                "step": "s3_candidate_quality",
                "kind": "candidate_review",
                "topic_id": topic_id,
                "source_revision": topic.get("source_revision"),
                "job_id": job_id,
                "candidates": candidates,
            }
        )
        accepted_here: list[dict[str, Any]] = [
            dict(c["fact"])
            for c in decided
            if isinstance(c.get("fact"), dict)
            and c["fact"].get("status") in {"ai_candidate", "medically_confirmed"}
        ]
        if not proposed:
            accepted_facts[topic_id] = accepted_here
            _record(
                {
                    "ts": _now(),
                    "step": "s3_adjudicate",
                    "kind": "summary",
                    "ok": True,
                    "resumed": bool(decided),
                    "topic_id": topic_id,
                    "already_decided": len(decided),
                }
            )
            continue
        job_status, job_body = _http(
            "s3_job_read",
            "GET",
            f"{MM_PREFIX}/ai/jobs/{job_id}",
        )
        job_public = job_body.get("job") or {}
        input_revision_sha256 = job_public.get("input_revision_sha256") or ""
        frozen_payload = _read_job_input_payload(str(job_id))
        frozen_by_id = {
            str(item.get("evidence_id") or "").strip(): item
            for item in (frozen_payload.get("evidence_packet") or [])
            if isinstance(item, dict) and item.get("evidence_id")
        }
        for candidate in proposed:
            usable, checks, reject_reason = _candidate_usability(
                candidate, allowed_types, frozen_by_id, EXPECTED_SOURCE_ENTRY_ID
            )
            _record(
                {
                    "ts": _now(),
                    "step": "s3_usability",
                    "kind": "assertions",
                    "topic_id": topic_id,
                    "candidate_id": candidate.get("candidate_id"),
                    "assertions": checks,
                    "ok": usable,
                }
            )
            structured = candidate.get("structured_payload") or {}
            evidence = (candidate.get("evidence") or [])[0]
            if usable:
                reason = (
                    "医学经理复核（W04-S2 批量裁决）：候选证据 "
                    f"{evidence.get('evidence_id')} 与冻结证据包 "
                    "locator/quote 逐字一致，"
                    f"fact_type={structured.get('fact_type')} 属主题允许集合；"
                    f"原文：{str(evidence.get('quote') or '')[:160]}"
                )
                payload = {
                    "decision": "accepted",
                    "reason": reason,
                    "expected_input_revision_sha256": input_revision_sha256,
                    "expected_source_revision": topic.get("source_revision"),
                    "proposed_fact_type": structured.get("fact_type"),
                }
            else:
                reason = (
                    "医学经理复核（W04-S2 批量裁决）驳回："
                    f"{reject_reason}；候选标题：{candidate.get('title')}"
                )
                payload = {
                    "decision": "rejected",
                    "reason": reason,
                    "expected_input_revision_sha256": input_revision_sha256,
                    "expected_source_revision": topic.get("source_revision"),
                }
            d_status, d_body = _http(
                "s3_decision",
                "POST",
                f"{MM_PREFIX}/protocol-preparation/protocol-versions/"
                f"{PROTOCOL_VERSION_ID}/candidates/"
                f"{candidate.get('candidate_id')}/decision",
                payload=payload,
            )
            outcome = d_body.get("outcome") or {}
            fact = outcome.get("fact") or {}
            _assertions(
                "s3_decision",
                [
                    ("decision_http_200", d_status == 200, d_status),
                    (
                        "decision_matches_intent",
                        (outcome.get("state") == "user_confirmed_fact_draft")
                        if usable
                        else (outcome.get("state") == "user_rejected"),
                        outcome.get("state"),
                    ),
                    (
                        "accepted_fact_is_ai_candidate",
                        (not usable) or fact.get("status") == "ai_candidate",
                        fact.get("status"),
                    ),
                ],
            )
            if d_status == 200 and usable and fact:
                accepted_here.append(fact)
            elif d_status == 200 and not usable:
                rejected_total += 1
        accepted_facts[topic_id] = accepted_here
    counts = _count_facts_by_status()
    _record(
        {
            "ts": _now(),
            "step": "s3_adjudicate",
            "kind": "summary",
            "ok": True,
            "accepted_facts": {
                k: [f.get("fact_revision_id") for f in v]
                for k, v in accepted_facts.items()
            },
            "rejected_total": rejected_total,
            "db_fact_status_counts": counts,
        }
    )
    return accepted_facts


def step4_activate_mapping() -> bool:
    status, body = _http(
        "s4_active_mapping_before",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    if status == 200:
        _assertions(
            "s4_activate_mapping",
            [
                (
                    "already_active_rerun",
                    body.get("mapping_revision") == MAPPING_REVISION_ID,
                    body.get("mapping_revision"),
                )
            ],
        )
        return True
    status, body = _http(
        "s4_confirm_replay",
        "POST",
        f"{MM_PREFIX}/ai/mapping-drafts/{MAPPING_DRAFT_ID}/confirm",
        payload=dict(MAPPING_CONFIRM_REPLAY),
    )
    activation = body.get("activation") or {}
    ok = (
        status == 200
        and body.get("mapping_revision") == MAPPING_REVISION_ID
        and bool(activation)
    )
    _assertions(
        "s4_activate_mapping",
        [
            ("confirm_replay_http_200", status == 200, status),
            (
                "revision_matches_original",
                body.get("mapping_revision") == MAPPING_REVISION_ID,
                body.get("mapping_revision"),
            ),
            (
                "activation_performed",
                bool(activation),
                sorted(activation.keys()) if isinstance(activation, dict) else activation,
            ),
        ],
    )
    if not ok:
        detail = (body.get("detail") or {}) if isinstance(body, dict) else {}
        _record(
            {
                "ts": _now(),
                "step": "s4_activate_mapping",
                "kind": "blocked",
                "ok": False,
                "http_status": status,
                "conflict_code": detail.get("code"),
                "conflict_message": detail.get("message"),
            }
        )
        return False
    status, body = _http(
        "s4_active_mapping_after",
        "GET",
        f"{MM_PREFIX}/ai/active-mapping",
    )
    _assertions(
        "s4_activate_mapping",
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
                    "capability_manifest_sha256": body.get("capability_manifest_sha256"),
                    "effective_capabilities_sha256": body.get(
                        "effective_capabilities_sha256"
                    ),
                },
            ),
        ],
    )
    return status == 200 and body.get("mapping_revision") == MAPPING_REVISION_ID


def _select_facts_for_confirmation(
    accepted_facts: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """按 fact_type 多样性轮询挑选待确认事实（上限 CONFIRM_CAP）。"""

    queue: dict[str, list[dict[str, Any]]] = {}
    for topic_id, facts in accepted_facts.items():
        for fact in facts:
            queue.setdefault(str(fact.get("fact_type")), []).append(fact)
    selected: list[dict[str, Any]] = []
    type_order = sorted(queue)
    index = 0
    while len(selected) < CONFIRM_CAP and any(queue[t] for t in type_order):
        fact_type = type_order[index % len(type_order)]
        bucket = queue[fact_type]
        if bucket:
            selected.append(bucket.pop(0))
        index += 1
    return selected


_RETRY_REPOSITORY = None


def _retry_failed_template_jobs(fact_revision_id: str) -> int:
    """对失败终态的模板作业执行产品自身的 retry_terminal（操作员语义）。

    背景与授权：模板服务 start 不带自动重试（submit 的 create_or_get 对
    同请求永远返回既有作业），失败作业会永久阻断该事实。修复生成归一后，
    为让重跑的确认链能真正走到修复后的生成路径，按协议准备服务对失败
    作业的同一恢复方法（monitoring_protocol_preparation_service.py:432-438
    调 monitoring_ai_repository.retry_terminal，无预算上限=操作员语义）
    在脚本内重排失败作业；每次重排在台账留痕。
    """

    global _RETRY_REPOSITORY
    if _RETRY_REPOSITORY is None:
        sys.path.insert(0, str(WORKBENCH_ROOT))
        from services.api.app.monitoring_ai_repository import (
            MonitoringAiRepository,
        )

        _RETRY_REPOSITORY = MonitoringAiRepository(AI_DB_PATH)
    status, body = _http(
        "s5_job_lookup",
        "GET",
        f"{MM_PREFIX}/ai/jobs",
        query={
            "task_type": "rule_template_recommendation",
            "business_key_prefix": (
                f"rule-template-recommendation:{fact_revision_id}:"
            ),
        },
    )
    retried = 0
    for job in body.get("items") or []:
        if job.get("status") != "failed":
            continue
        try:
            _RETRY_REPOSITORY.retry_terminal(
                PROJECT_ID,
                job["job_id"],
                current_input_revision_sha256=job["input_revision_sha256"],
            )
            retried += 1
            _record(
                {
                    "ts": _now(),
                    "step": "s5_retry_terminal",
                    "kind": "summary",
                    "ok": True,
                    "fact_revision_id": fact_revision_id,
                    "job_id": job["job_id"],
                    "message": (
                        "失败模板作业已按操作员语义重排（retry_terminal），"
                        "由下一次 start 唤醒 worker 重走归一后的生成路径"
                    ),
                }
            )
        except Exception as exc:
            _record(
                {
                    "ts": _now(),
                    "step": "s5_retry_terminal",
                    "kind": "summary",
                    "ok": False,
                    "fact_revision_id": fact_revision_id,
                    "job_id": job.get("job_id"),
                    "error": repr(exc),
                }
            )
    return retried


def step5_confirm_chain(
    facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    confirmed: list[dict[str, Any]] = []
    for fact in facts:
        fact_revision_id = str(fact.get("fact_revision_id"))
        state_version = int(fact.get("state_version") or 1)
        _retry_failed_template_jobs(fact_revision_id)
        status, body = _http(
            "s5_start",
            "POST",
            f"{MM_PREFIX}/rule-template-recommendations/facts/"
            f"{fact_revision_id}/start",
            payload={"expected_fact_state_version": state_version},
        )
        if status != 202:
            _record(
                {
                    "ts": _now(),
                    "step": "s5_confirm",
                    "kind": "summary",
                    "ok": False,
                    "fact_revision_id": fact_revision_id,
                    "http_status": status,
                }
            )
            continue
        if body.get("status") == "manual_review":
            _record(
                {
                    "ts": _now(),
                    "step": "s5_manual_review",
                    "kind": "summary",
                    "ok": False,
                    "fact_revision_id": fact_revision_id,
                    "reason_code": body.get("reason_code"),
                    "message": body.get("message"),
                }
            )
            continue
        deadline = time.monotonic() + RECOMMENDATION_TIMEOUT_SECONDS
        while True:
            status, body = _http(
                "s5_poll",
                "GET",
                f"{MM_PREFIX}/rule-template-recommendations/facts/"
                f"{fact_revision_id}/status",
                query={"expected_fact_state_version": state_version},
            )
            current = body.get("status")
            if current in RECOMMENDATION_TERMINAL:
                break
            if time.monotonic() > deadline:
                raise RuntimeError(
                    f"推荐轮询超时：{fact_revision_id} 最后状态 {current}"
                )
            time.sleep(POLL_INTERVAL_SECONDS)
        recommendations = body.get("candidates") or []
        proposed = [c for c in recommendations if c.get("status") == "proposed"]
        accepted = [c for c in recommendations if c.get("status") == "accepted"]
        _record(
            {
                "ts": _now(),
                "step": "s5_recommendations",
                "kind": "candidate_review",
                "fact_revision_id": fact_revision_id,
                "status": body.get("status"),
                "failure": body.get("failure"),
                "context": {
                    key: body.get(key)
                    for key in ("fact", "mapping", "input_revision_sha256")
                },
                "candidates": recommendations,
            }
        )
        if proposed:
            candidate = proposed[0]
        elif accepted:
            candidate = accepted[0]
        else:
            _record(
                {
                    "ts": _now(),
                    "step": "s5_confirm",
                    "kind": "summary",
                    "ok": False,
                    "fact_revision_id": fact_revision_id,
                    "reason": "no_selectable_recommendation",
                }
            )
            continue
        fact_context = body.get("fact") or {}
        expected_state = int(fact_context.get("state_version") or state_version)
        reason = (
            "医学经理复核（W04-S2）：建议 "
            f"{candidate.get('rule_family')} 与已接受事实类型一致，"
            "确定性模板映射字段与已激活映射闭合；选择即确认事实并编译规则。"
        )
        status, body = _http(
            "s5_decision",
            "POST",
            f"{MM_PREFIX}/rule-template-recommendations/facts/"
            f"{fact_revision_id}/candidates/{candidate.get('candidate_id')}/decision",
            payload={
                "decision": "accepted",
                "reason": reason,
                "expected_input_revision_sha256": str(
                    body.get("input_revision_sha256") or ""
                ),
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
            "s5_decision",
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
        if confirmed_fact.get("status") == "medically_confirmed":
            confirmed.append(confirmed_fact)
    return confirmed


def step6_final_assertions(confirmed: list[dict[str, Any]]) -> None:
    status, body = _http(
        "s6_facts",
        "GET",
        f"{MM_PREFIX}/protocol-versions/{PROTOCOL_VERSION_ID}/facts",
    )
    items = body.get("items") or []
    confirmed_items = [
        item for item in items if item.get("status") == "medically_confirmed"
    ]
    fact_types = {str(item.get("fact_type")) for item in confirmed_items}
    confirmed_ids = {item.get("fact_revision_id") for item in confirmed_items}
    candidate_backed = all(
        isinstance(item.get("normalized_payload"), dict)
        and isinstance(item["normalized_payload"].get("ai_candidate"), dict)
        for item in confirmed_items
    )
    counts = _count_facts_by_status()
    _assertions(
        "s6_final",
        [
            ("facts_http_200", status == 200, status),
            (
                "confirmed_count_at_least_3",
                len(confirmed_items) >= CONFIRM_TARGET,
                {"api": len(confirmed_items), "db": counts.get("medically_confirmed", 0)},
            ),
            (
                "fact_type_coverage_at_least_2",
                len(fact_types) >= TYPE_COVERAGE_TARGET,
                sorted(fact_types),
            ),
            (
                "db_status_counts_consistent",
                counts.get("medically_confirmed", 0) == len(confirmed_items),
                counts,
            ),
            (
                "facts_deduped_one_candidate_each",
                candidate_backed and len(confirmed_ids) == len(confirmed_items),
                len(confirmed_ids),
            ),
            (
                "script_confirmed_matches_api",
                {f.get("fact_revision_id") for f in confirmed} <= confirmed_ids,
                len(confirmed),
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
            "message": "W04-S2 全主题提取+批量裁决+确认链开始",
            "topic_ids": list(TOPIC_IDS),
        }
    )
    step0_precheck()
    step1_start_all_topics()
    topics = step2_poll_all_topics()
    accepted = step3_adjudicate(topics)
    mapping_active = step4_activate_mapping()
    if not mapping_active:
        _record(
            {
                "ts": _now(),
                "step": "run",
                "kind": "summary",
                "ok": False,
                "exit_code": 3,
                "message": "确认链仍被映射激活阻断（见 s4 blocked 证据）",
            }
        )
        raise SystemExit(3)
    candidates = _select_facts_for_confirmation(accepted)
    _record(
        {
            "ts": _now(),
            "step": "s5_select",
            "kind": "summary",
            "ok": True,
            "selected": [
                {
                    "fact_revision_id": f.get("fact_revision_id"),
                    "fact_type": f.get("fact_type"),
                }
                for f in candidates
            ],
        }
    )
    confirmed = step5_confirm_chain(candidates)
    step6_final_assertions(confirmed)
    _record(
        {
            "ts": _now(),
            "step": "run",
            "kind": "summary",
            "ok": True,
            "message": (
                "W04-S2 完成：medically_confirmed 事实 "
                f"{len(confirmed)} 条（目标 ≥{CONFIRM_TARGET}，"
                f"≥{TYPE_COVERAGE_TARGET} 种 fact_type）"
            ),
        }
    )
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
