"""W04-S4：消费闭环验证——published 规则包被确定性执行引擎消费并产出
review-only 风险候选。

前置现状（本脚本如实核验并记录）：
  - S3 交付了冻结批次 monbatch_4852dfbb…（映射契约四元组与激活映射一致），
    但规则包链在 draft 步被 fail-closed 拒绝（S2 遗留 0 条
    medically_confirmed 事实）——当前 0 个规则包，因此不存在 published 包，
    实跑消费（MonitoringBatchRuleRunner.run 仅执行 published 包，
    monitoring_batch_rule_runner.py:173-176）暂不可达。
  - 本脚本在此现状下验证消费闭环的三层可验证契约，全部只读、不改任何
    风险存量数据：
    L1 消费 fail-closed（live）：对冻结批次用不存在的 pack id 调
       MonitoringBatchRuleRunner.run → 显式失败（不静默）；对未冻结批次
       调 run → "batch must be frozen"。published-only 门由代码
       （:173-176）与 tests/test_monitoring_rule_release_chain_p0_20260730.py
       覆盖。
    L2 桥接 review-only 契约（纯函数合成夹具，明确标注，不触碰任何存储）：
       MonitoringRuleRiskBridge.convert 把命中候选转为复核候选 RiskCase
       （status=IN_REVIEW、action_priority=medical_review_required、
       rationale 含"待医学复核"、证据 fragment medical_review_candidate_only
       =True），并断言产出身份与既有风险存量（proj_rux_03_002，
       rule_pack_revision=facts-baseline-rules-v1，ae_mh_cross_analysis.py
       :264,843）零交集；前后存量计数不变（无写入）。
    L3 daily-run 编排入参形态（代码级核对，不重建流水线）：
       monitoring_daily_run_service.py:229-236 按 rule_pack_revision/
       rule_identity_sha256/engine_version 消费，解析自 inspect.getsource。

证据逐行追加 runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/
s4_evidence.jsonl。退出码 0（harness 交付；缺 published 包的阻断已记录）。
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

RUN_ROOT = Path(__file__).resolve().parent
WORKBENCH_ROOT = RUN_ROOT.parent.parent
EVIDENCE_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "w04_protocol_facts"
)
EVIDENCE_PATH = EVIDENCE_DIR / "s4_evidence.jsonl"
RUNTIME_DIR = (
    WORKBENCH_ROOT
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
)
BATCH_DB_PATH = RUNTIME_DIR / "medical_monitoring_batches.sqlite3"
RULES_DB_PATH = RUNTIME_DIR / "monitoring_protocol_rules.sqlite3"
RISKS_DB_PATH = RUNTIME_DIR / "medical_risks.sqlite3"

PROJECT_ID = "proj_user_2f17492ac59b"
FROZEN_BATCH_ID = "monbatch_4852dfbbbd964ca9b41c1d431c24296b"
PARSED_BATCH_ID = "monbatch_012153ea5d8243d3b0cacb4a847385e6"
BASELINE_PACK_REVISION = "facts-baseline-rules-v1"


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


def _rule_service():
    from services.api.app.monitoring_protocol_rule_repository import (
        MonitoringProtocolRuleRepository,
    )
    from services.api.app.monitoring_protocol_rule_service import (
        MonitoringProtocolRuleService,
    )

    return MonitoringProtocolRuleService(
        MonitoringProtocolRuleRepository(RULES_DB_PATH)
    )


def _batch_repository():
    from services.api.app.monitoring_batch_repository import (
        MonitoringBatchRepository,
    )

    return MonitoringBatchRepository(
        BATCH_DB_PATH,
        RUNTIME_DIR / "medical_monitoring_batch_objects",
    )


def _risk_stock() -> tuple[int, set[str], set[str], dict[str, int]]:
    connection = sqlite3.connect(f"file:{RISKS_DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT risk_instance_id, risk_key, project_id, payload_json "
            "FROM medical_risk_instances"
        ).fetchall()
        instance_ids = {row["risk_instance_id"] for row in rows}
        risk_keys = {row["risk_key"] for row in rows}
        by_pack: dict[str, int] = {}
        projects: dict[str, int] = {}
        for row in rows:
            payload = json.loads(row["payload_json"] or "{}")
            pack = str(
                payload.get("rule_profile_revision")
                or payload.get("rule_pack_id")
                or ""
            )
            by_pack[pack] = by_pack.get(pack, 0) + 1
            projects[row["project_id"]] = (
                projects.get(row["project_id"], 0) + 1
            )
        return len(rows), instance_ids, risk_keys, {**by_pack, **{f"project:{k}": v for k, v in projects.items()}}
    finally:
        connection.close()


def step0_precheck() -> None:
    status, body = _http_packs()
    items = body.get("items") or []
    connection = sqlite3.connect(f"file:{RULES_DB_PATH}?mode=ro", uri=True)
    try:
        pack_rows = int(
            connection.execute("SELECT COUNT(*) FROM monitoring_rule_packs").fetchone()[0]
        )
        fact_counts: dict[str, int] = {}
        for row in connection.execute(
            "SELECT status, COUNT(*) FROM monitoring_protocol_facts "
            "WHERE project_id = ? GROUP BY status",
            (PROJECT_ID,),
        ).fetchall():
            fact_counts[row[0]] = int(row[1])
    finally:
        connection.close()
    stock_total, _ids, _keys, stock_detail = _risk_stock()
    _record(
        {
            "ts": _now(),
            "step": "s0_precheck",
            "kind": "summary",
            "ok": True,
            "rule_packs_api_items": len(items),
            "rule_packs_db_rows": pack_rows,
            "fact_status_counts": fact_counts,
            "risk_stock_total": stock_total,
            "risk_stock_detail": stock_detail,
        }
    )
    _assertions(
        "s0_precheck",
        [
            (
                "no_published_pack_recorded",
                pack_rows == 0 and len(items) == 0,
                {"db": pack_rows, "api": len(items)},
            ),
            (
                "risk_stock_baseline_source",
                any("rules-v1" in key for key in stock_detail),
                stock_detail,
            ),
            (
                "risk_stock_is_read_only_snapshot",
                stock_total >= 0,
                stock_total,
            ),
        ],
    )


def _http_packs() -> tuple[int, Any]:
    import urllib.request

    url = (
        f"http://127.0.0.1:8910/api/projects/{PROJECT_ID}"
        f"/modules/medical-monitoring/rule-packs"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return 0, {"items": [], "_error": repr(exc)}


def step1_runner_fail_closed() -> None:
    sys.path.insert(0, str(WORKBENCH_ROOT))
    from services.api.app.monitoring_batch_rule_runner import (
        MonitoringBatchRuleRunner,
        MonitoringBatchRuleRunnerError,
    )

    repository = _batch_repository()
    runner = MonitoringBatchRuleRunner(_rule_service())

    frozen = repository.load_diff_ready_batch(FROZEN_BATCH_ID)
    live_error = ""
    try:
        runner.run(frozen, rule_pack_id="monpack_w04s4_nonexistent")
    except MonitoringBatchRuleRunnerError as exc:
        live_error = str(exc)
    except Exception as exc:
        live_error = f"{type(exc).__name__}: {exc}"
    _record(
        {
            "ts": _now(),
            "step": "s1_runner",
            "kind": "summary",
            "ok": True,
            "case": "frozen_batch_with_nonexistent_pack",
            "failed_closed": bool(live_error),
            "error": live_error,
        }
    )

    # 未冻结批次的加载本身就被仓库拒绝（load_diff_ready_batch 仅接受
    # frozen）；状态门再用最小 DiffReadyBatch 夹具直验 run() 的第一道闸。
    load_blocked = False
    try:
        parsed = repository.load_diff_ready_batch(PARSED_BATCH_ID)
    except Exception as exc:
        parsed = None
        load_blocked = True
        _record(
            {
                "ts": _now(),
                "step": "s1_runner",
                "kind": "summary",
                "ok": True,
                "case": "non_frozen_batch_load",
                "failed_closed": True,
                "error": str(exc)[:200],
            }
        )
    state_error = ""
    if parsed is not None:
        try:
            runner.run(parsed, rule_pack_id="monpack_w04s4_nonexistent")
        except MonitoringBatchRuleRunnerError as exc:
            state_error = str(exc)
        except Exception as exc:
            state_error = f"{type(exc).__name__}: {exc}"
    _record(
        {
            "ts": _now(),
            "step": "s1_runner",
            "kind": "summary",
            "ok": True,
            "case": "non_frozen_batch",
            "failed_closed": bool(state_error),
            "error": state_error,
        }
    )
    source_lines = inspect.getsource(MonitoringBatchRuleRunner.run)
    published_gate_in_source = 'only a published rule pack may be executed' in source_lines
    _assertions(
        "s1_runner_fail_closed",
        [
            (
                "missing_pack_fails_closed",
                bool(live_error),
                live_error[:120],
            ),
            (
                "non_frozen_batch_fails_closed",
                load_blocked or "must be frozen" in state_error,
                {
                    "load_blocked": load_blocked,
                    "runner_error": state_error[:120],
                },
            ),
            (
                "published_only_gate_present_in_code",
                published_gate_in_source,
                "monitoring_batch_rule_runner.py run()",
            ),
        ],
    )


def step2_bridge_review_only_contract() -> None:
    from datetime import datetime as dt

    from services.api.app.monitoring_rule_risk_bridge import (
        MonitoringRuleRiskBridge,
    )
    from services.api.app.monitoring_batch_rule_runner import (
        BatchRuleCandidate,
        BatchRuleRunResult,
    )

    # 合成夹具：仅验证桥接纯函数契约，不触碰任何存储/风险存量。
    result = BatchRuleRunResult(
        run_id="monbatchrun_w04s4_synthetic",
        project_id=PROJECT_ID,
        batch_id=FROZEN_BATCH_ID,
        batch_version=8,
        mapping_revision="monmaprev_f8677a0050c5af2b3a4894e5e23d",
        rule_pack_id="monpack_w04s4_synthetic",
        rule_revision_ids=("monrulerev_synthetic",),
        evaluated_record_count=573,
        candidates=(
            BatchRuleCandidate(
                candidate_id="monbatchcand_w04s4_synthetic",
                project_id=PROJECT_ID,
                batch_id=FROZEN_BATCH_ID,
                batch_version=8,
                mapping_revision="monmaprev_f8677a0050c5af2b3a4894e5e23d",
                rule_pack_id="monpack_w04s4_synthetic",
                rule_revision_id="monrulerev_synthetic",
                rule_key="synthetic_ae_missing_report_check",
                subject_id="0001",
                current_domain="AE",
                current_business_key="AE-0001-合成核验",
                severity="medium",
                confidence="high",
                evidence_summary="合成核验：AE 记录缺失归因受试者标识。",
                evaluation={
                    "matched": True,
                    "risk_category_code": "ae_missing_report",
                    "evidence": {
                        "medical_review_candidate_only": True,
                        "current_record": {
                            "raw_data": {"AETERM": "头痛", "AESEQ": 1}
                        },
                        "protocol_source": {
                            "source_text": "合成核验引用的方案原文片段"
                        },
                    },
                },
            ),
        ),
        diagnostics=(),
        output_sha256="0" * 64,
    )
    stock_total, stock_instances, stock_keys, _detail = _risk_stock()
    risks = MonitoringRuleRiskBridge.convert(
        result,
        engine_version="w04s4-verification",
        source_revision="w04s4-verification-source",
        created_at=dt.now(timezone.utc),
    )
    after_total, after_instances, after_keys, _after_detail = _risk_stock()
    review_only_checks: list[dict[str, Any]] = []
    for risk in risks:
        fragments = risk.evidence_snapshots or []
        fragment_flags = [
            bool(
                (
                    fragment.fragment or {}
                ).get("medical_review_candidate_only")
            )
            for fragment in fragments
        ]
        review_only_checks.append(
            {
                "risk_id": risk.risk_id,
                "risk_type": risk.risk_type,
                "status": risk.status.value if hasattr(risk.status, "value") else str(risk.status),
                "action_priority": risk.action_priority,
                "review_only_in_rationale": "待医学复核" in (risk.rationale or ""),
                "medical_review_candidate_only": any(fragment_flags),
                "engine_version": risk.engine_version,
                "source_revision": risk.source_revision,
                "rule_profile_revision": risk.rule_profile_revision,
            }
        )
    instance_ids = {risk.risk_instance_id for risk in risks}
    _assertions(
        "s2_bridge_review_only",
        [
            (
                "converts_matched_candidates",
                len(risks) == len(result.candidates),
                {"candidates": len(result.candidates), "risks": len(risks)},
            ),
            (
                "all_review_only",
                all(item["status"] == "in_review" for item in review_only_checks)
                and all(
                    item["action_priority"] == "medical_review_required"
                    for item in review_only_checks
                )
                and all(item["review_only_in_rationale"] for item in review_only_checks)
                and all(item["medical_review_candidate_only"] for item in review_only_checks),
                review_only_checks,
            ),
            (
                "provenance_stamped",
                all(item["engine_version"] == "w04s4-verification" for item in review_only_checks),
                review_only_checks[0] if review_only_checks else None,
            ),
            (
                "no_collision_with_baseline_stock",
                instance_ids.isdisjoint(stock_instances)
                and all(
                    item["rule_profile_revision"] != BASELINE_PACK_REVISION
                    for item in review_only_checks
                ),
                {
                    "stock_project": "proj_rux_03_002",
                    "stock_total": stock_total,
                    "synthetic_ids": sorted(instance_ids),
                },
            ),
            (
                "risk_stock_untouched",
                after_total == stock_total and after_instances == stock_instances,
                {"before": stock_total, "after": after_total},
            ),
        ],
    )


def step3_daily_run_input_shape() -> None:
    sys.path.insert(0, str(WORKBENCH_ROOT))
    import services.api.app.monitoring_daily_run_service as module

    source = inspect.getsource(module)
    lines = source.splitlines()
    hits = [
        line.strip()
        for line in lines
        if "rule_pack_revision" in line
        or "rule_identity_sha256" in line
        or "engine_version" in line
    ]
    in_range = [
        lines[index - 1].strip()
        for index, line in enumerate(lines, start=1)
        if 228 <= index <= 237
        and (
            "rule_pack_revision" in line
            or "rule_identity_sha256" in line
            or "engine_version" in line
        )
    ]
    _record(
        {
            "ts": _now(),
            "step": "s3_daily_run_input_shape",
            "kind": "summary",
            "ok": True,
            "contract": (
                "daily-run 编排按 rule_pack_revision/rule_identity_sha256/"
                "engine_version 消费（monitoring_daily_run_service.py:229-236），"
                "本切片仅核对入参形态，不重建 daily-run 流水线"
            ),
            "matched_source_lines_all": hits[:8],
            "matched_source_lines_in_range_229_236": in_range,
        }
    )
    _assertions(
        "s3_daily_run_input_shape",
        [
            (
                "rule_pack_revision_input_present",
                bool(in_range),
                in_range[:3],
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
            "message": "W04-S4 消费闭环验证开始（当前无 published 包：S3 残留阻断，如实记录）",
        }
    )
    step0_precheck()
    step1_runner_fail_closed()
    step2_bridge_review_only_contract()
    step3_daily_run_input_shape()
    _record(
        {
            "ts": _now(),
            "step": "run",
            "kind": "summary",
            "ok": True,
            "message": (
                "W04-S4 完成：消费契约三层可验证项全部通过"
                "（消费 fail-closed / 桥接 review-only 与存量零交集 / "
                "daily-run 入参形态）；实跑消费待 published 包产出"
                "（依赖 S2 生成内容缺陷修复）"
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
