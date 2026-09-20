#!/usr/bin/env python3
"""p5重试波（审阅WP0B整改版）：为p4主lane终态失败的受试者以新命名空间重发
主cohort作业。

D-10整改：映射内容校验（损坏/空=技术状态，不是"已提交完成"证据）；
读取异常/缺证据的跳项全部落账（/tmp/aemh_p5_skipped.json），不无声消失；
提交完成后主动唤醒worker（不依赖未来外部cron tick才发现已提交任务）。
总体预算仍为每工作单元 p4两次 + p5两次；本脚本幂等——p5映射存在即跳过，
watchdog保证永不产生p6。

产出 /tmp/aemh_dualvlm_batch_p5_primary.json（subject → job_id）。
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH))

RUNTIME_DIR = Path(
    os.environ.setdefault(
        "WORKBENCH_RUNTIME_DIR",
        str(WORKBENCH / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"),
    )
)

PROJECT_ID = "proj_mgk10_sar_real"
P5_REF = "facts-snapshot-001.dualvlm-full1-p5"
WORKSPACE = RUNTIME_DIR / "medical_monitoring_r7" / PROJECT_ID
P5_MAP = Path("/tmp/aemh_dualvlm_batch_p5_primary.json")
P5_SKIPPED = Path("/tmp/aemh_p5_skipped.json")
QUEUE_RESUME_URL = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT_ID}"
    "/modules/medical-monitoring/ai/queue/resume"
)


def main() -> int:
    if P5_MAP.exists():
        try:
            existing = json.load(open(P5_MAP))
        except ValueError:
            print("existing p5 map is corrupt; visible state, not resubmitting")
            P5_SKIPPED.write_text(
                json.dumps(
                    [{"reason": "p5_map_corrupt", "detail": "see watchdog state"}],
                    ensure_ascii=False,
                )
            )
            return 2
        if not isinstance(existing, dict) or not existing:
            print("existing p5 map is empty/corrupt; visible state, not resubmitting")
            return 2
        print(f"p5 map already exists ({len(existing)} jobs); skip")
        return 0

    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        PRIMARY_PROMPT_VERSION,
        _DOMAIN_ROLE,
        _layout_payload,
        _protocol_profile_payload,
        build_subject_evidence,
    )
    from packages.medical_monitoring.intelligence.primitives import content_hash
    from services.api.app import main
    from services.api.app.monitoring_ai_contracts import (
        MonitoringAiInputRevision,
        MonitoringAiSourceBinding,
        MonitoringAiTaskType,
    )

    domains = main._r7_facts_publication_provider._load_domains()
    batch = json.load(open("/tmp/aemh_dualvlm_batch.json"))
    subjects = batch["subjects"]

    p4map = json.load(open("/tmp/aemh_dualvlm_batch_p4_primary.json"))
    if not isinstance(p4map, dict) or not p4map:
        print("p4 map missing/corrupt; cannot determine failed subjects")
        P5_SKIPPED.write_text(
            json.dumps([{"reason": "p4_map_missing_or_corrupt"}], ensure_ascii=False)
        )
        return 2

    repo = main.monitoring_ai_repository
    failed_subjects: list[str] = []
    read_errors: list[dict[str, str]] = []
    for subj in subjects:
        jid = p4map.get(subj)
        if not jid:
            read_errors.append(
                {"subject_label": subj, "reason": "p4_map_entry_missing"}
            )
            continue
        try:
            status = repo.get(PROJECT_ID, jid).status
        except Exception as exc:
            read_errors.append(
                {"subject_label": subj, "reason": f"job_query_error: {exc}"}
            )
            continue
        if status == "failed":
            failed_subjects.append(subj)
    skipped: list[dict[str, str]] = list(read_errors)
    if not failed_subjects:
        print("no failed p4 primary subjects; nothing to retry")
        P5_SKIPPED.write_text(json.dumps(skipped, ensure_ascii=False))
        return 0
    print("retry subjects:", len(failed_subjects))

    profile_payload = _protocol_profile_payload(WORKSPACE)
    layout_payload = _layout_payload(WORKSPACE)
    job_ids: dict[str, str] = {}
    for subject_label in failed_subjects:
        try:
            evidence, source_hashes = build_subject_evidence(domains, subject_label)
        except ValueError as exc:
            skipped.append(
                {
                    "subject_label": subject_label,
                    "reason": f"evidence_unavailable: {exc}",
                }
            )
            continue
        input_revision = MonitoringAiInputRevision(
            project_id=PROJECT_ID,
            batch_revision=f"facts:{P5_REF}",
            mapping_revision="facts-materialized",
            rule_pack_revision="facts-baseline-rules-v1",
            sources=tuple(
                MonitoringAiSourceBinding(
                    source_entry_id=f"facts:{table}",
                    source_content_sha256=digest,
                )
                for table, digest in sorted(source_hashes.items())
            ),
        )
        payload = {
            "subject_context": {
                "subject_id": subject_label,
                "batch_id": P5_REF,
                "batch_version": 1,
                "mapping_revision": "facts-materialized",
                "rule_snapshot_id": "facts-baseline",
                "rule_pack_id": "facts-baseline-rules-v1",
                "rule_output_sha256": content_hash({"rules": "baseline"}),
                "selection_reasons": ["aemh_cross_analysis"],
                "domains": sorted(
                    {item["raw_fields"]["domain"] for item in evidence}
                ),
                "domain_semantics": dict(_DOMAIN_ROLE),
                "medical_boundary": (
                    "仅生成待当前医学用户复核的跨表线索；不得自动判定"
                    "AE/MH漏报、方案违背或生成Query。"
                ),
                "protocol_profile": profile_payload,
                "listing_layout": layout_payload,
                "analysis_contract": (
                    "每个线索候选的claims.evidence_ids必须合计引用至少两个"
                    "不同domain（如AE+MH、CM+EX、AE+CM）的evidence_id；"
                    "只引用单一domain证据的候选会被系统直接拒绝。"
                    "evidence_packet每条证据的raw_fields.domain标明了所属域。"
                    "AE强度、严重性、预期性、因果性与监查优先级必须分开表述，"
                    "不得合并；严重程度表述必须遵循subject_context."
                    "protocol_profile.ctcae_version对应的分级标准（若"
                    "unknown_visible为true则按原始记录表述并标注口径未知）；"
                    "证据不足时输出data_gap候选，不得补造。"
                ),
            },
            "evidence_packet": evidence,
        }
        try:
            job = main.monitoring_ai_service.submit_task(
                project_id=PROJECT_ID,
                task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
                input_revision=input_revision,
                input_payload=payload,
                business_key=f"aemh:{P5_REF}:primary:{subject_label}",
                prompt_version=PRIMARY_PROMPT_VERSION,
                max_attempts=2,
            )
        except Exception as exc:
            skipped.append(
                {
                    "subject_label": subject_label,
                    "reason": f"submit_failed: {exc}",
                }
            )
            continue
        job_ids[subject_label] = job.job_id

    P5_MAP.write_text(json.dumps(job_ids))
    P5_SKIPPED.write_text(json.dumps(skipped, ensure_ascii=False))
    print(
        f"submitted p5={len(job_ids)} skipped={len(skipped)} "
        f"(ledger: {P5_SKIPPED})"
    )
    # 唤醒worker：新提交的任务立即可被发现，不依赖下一次外部cron tick。
    try:
        req = urllib.request.Request(
            QUEUE_RESUME_URL,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as exc:
        print(f"WARN: post-submit wake failed ({exc}); watchdog resume will cover")
    if not job_ids and skipped:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
