#!/usr/bin/env python3
"""双VLM全量批跑收尾（v3，审阅WP0B整改版）。

与v2的差异（对应增量审阅D-01/D-02/D-03/D-07/D-08/D-09）：
- p5结果进入选择链（D-01）；不再以叠加文件名为最终方案——选择按
  "当前代身份校验"进行，只认与参考代revision一致的作业（D-02）。
- 作业选择不止看status=completed：校验project/prompt版本/输入revision
  （源内容+映射+规则冻结身份），旧代completed不静默晋升为当前结果。
- 定向核实：版本化focused合同（恰好一个核实候选）、稳定finding_id关联、
  确认/反证/证据不足/执行失败四态区分（D-03）；跳项原因持久化。
- --dry-run零副作用（D-07）：不import生产main、不写任何工件/token/
  哨兵/队列，仅内存评估并打印。
- 哨兵改为 project+快照冻结身份+策略版本 作用域化原子哨兵（D-08）；
  发布幂等键绑定分析工件内容hash；发布重试轮询替代固定sleep(8)。
- 预检=精确expected作业清单对账（含project过滤），不再用p%通配
  （D-09）。

用法：
  python3 scripts/dualvlm_finalize.py            # 全流程
  python3 scripts/dualvlm_finalize.py --dry-run  # 只读评估（零副作用）
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
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
SNAPSHOT_REF = "facts-snapshot-001.dualvlm-full1"
FOCUSED_REF = "facts-snapshot-001.dualvlm-full1-fv"
BASE = f"http://127.0.0.1:8910/api/projects/{PROJECT_ID}/modules/medical-monitoring/r7"
WORKSPACE = RUNTIME_DIR / "medical_monitoring_r7" / PROJECT_ID
DB_PATH = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
BATCH_DIR = Path("/tmp")

_PRIMARY_OVERRIDE_FILES = (
    # 旧代仅在与同受试者盲核作业revision一致时才会被选中（身份校验兜底）
    "aemh_dualvlm_batch_p2_primary.json",
    "aemh_dualvlm_batch_p4_primary.json",
    "aemh_dualvlm_batch_p5_primary.json",
)


def _load_json(name: str):
    try:
        return json.load(open(BATCH_DIR / name))
    except (OSError, ValueError):
        return None


def _open_ro_db() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _job_identity(conn: sqlite3.Connection, job_id: str) -> dict | None:
    """返回作业冻结身份（只读）；缺作业返回None。

    evidence_identity = 输入冻结身份中**除代际标签（batch_revision）与
    project_id外**的全部绑定（sources源内容hash/mapping/rule/protocol/
    fact/risk_snapshot/source_binding修订）的hash——同一受试者的主/盲核
    作业基于同一证据快照时该值相同；代际命名不同不构成证据差异。
    """
    row = conn.execute(
        "SELECT status, prompt_version, input_revision_sha256, input_revision_json, "
        "business_key, response_model FROM monitoring_ai_jobs "
        "WHERE project_id=? AND job_id=?",
        (PROJECT_ID, job_id),
    ).fetchone()
    if row is None:
        return None
    evidence_identity = ""
    try:
        revision = json.loads(row["input_revision_json"] or "{}")
        stable = {
            k: v
            for k, v in revision.items()
            if k not in ("batch_revision", "project_id")
        }
        evidence_identity = hashlib.sha256(
            json.dumps(stable, sort_keys=True).encode("utf-8")
        ).hexdigest()
    except (ValueError, TypeError):
        evidence_identity = ""
    return {
        "status": row["status"],
        "prompt_version": row["prompt_version"],
        "evidence_identity": evidence_identity,
        "business_key": row["business_key"] or "",
        "response_model": row["response_model"] or "",
    }


def _select_cohort_maps(
    conn: sqlite3.Connection, batch: dict
) -> tuple[dict[str, str], dict[str, str], dict[str, int], str]:
    """按受试者配对的冻结身份选择主/盲核作业映射（D-01/D-02）。

    每受试者独立选择：主侧按 p5⊳p4⊳p2⊳MTPLX、盲核侧按 r3⊳MTPLX 找
    completed+正确prompt+正确role的作业；**配对成功要求两侧
    input_revision_sha256一致**（同一受试者同一证据快照）。旧代revision
    不一致→该受试者两侧均不入选，成为可见覆盖缺口，不静默晋升。

    返回 (prim_map, ver_map, exclusion_stats, selection_identity)。
    selection_identity=全部入选作业id的冻结hash，用于scoped哨兵。
    """
    primary_prompt = "monitoring-cross-table-clue-synthesis-v3"
    verifier_prompt = "monitoring-cross-table-clue-synthesis-verifier-v1"
    exclusion_stats: dict[str, int] = Counter()

    def _pick(
        sources: list[tuple[str, dict]], expected_prompt: str, role: str, subject: str
    ) -> tuple[str, str, str] | tuple[None, None, str]:
        for gen_name, mapping in sources:
            job_id = mapping.get(subject)
            if not job_id:
                continue
            ident = _job_identity(conn, str(job_id))
            if ident is None:
                exclusion_stats[f"{role}:{gen_name}:job_not_found"] += 1
                continue
            if ident["status"] != "completed":
                exclusion_stats[f"{role}:{gen_name}:{ident['status']}"] += 1
                continue
            if ident["prompt_version"] != expected_prompt:
                exclusion_stats[f"{role}:{gen_name}:prompt_mismatch"] += 1
                continue
            if f":{role}:" not in ident["business_key"]:
                exclusion_stats[f"{role}:{gen_name}:role_mismatch"] += 1
                continue
            return str(job_id), ident["evidence_identity"] or "", gen_name
        return None, None, "none_completed"

    prim_map: dict[str, str] = {}
    ver_map: dict[str, str] = {}
    primary_sources: list[tuple[str, dict]] = [
        ("p5", _load_json("aemh_dualvlm_batch_p5_primary.json") or {}),
        ("p4", _load_json("aemh_dualvlm_batch_p4_primary.json") or {}),
        ("p2", _load_json("aemh_dualvlm_batch_p2_primary.json") or {}),
        ("mtplx", dict(zip(batch["subjects"], batch["primary"]))),
    ]
    verifier_sources: list[tuple[str, dict]] = [
        ("r3", _load_json("aemh_dualvlm_batch_r3_verifier.json") or {}),
        ("mtplx", dict(zip(batch["subjects"], batch["verifier"]))),
    ]
    for subject in batch["subjects"]:
        p_job, p_rev, _p_gen = _pick(
            primary_sources, primary_prompt, "primary", subject
        )
        v_job, v_rev, _v_gen = _pick(
            verifier_sources, verifier_prompt, "verifier", subject
        )
        if not p_job or not v_job:
            exclusion_stats[f"subject_incomplete:{subject}"] += 1
            continue
        if p_rev != v_rev:
            # 同一受试者两侧证据身份不一致（数据/映射/规则/方案绑定在两代
            # 之间确实变化过）：不配对，可见缺口。
            exclusion_stats["pair:revision_mismatch"] += 1
            continue
        prim_map[subject] = p_job
        ver_map[subject] = v_job

    selection_identity = hashlib.sha256(
        json.dumps(
            {
                "primary": sorted(prim_map.values()),
                "verifier": sorted(ver_map.values()),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:12]
    return prim_map, ver_map, dict(exclusion_stats), selection_identity


def _preflight_expected_terminal(conn: sqlite3.Connection, batch: dict) -> None:
    """精确expected作业对账（D-09）：任一expected作业未终态→中止。

    expected = batch.primary ∪ batch.verifier ∪ r3 ∪ p2/p4/p5主作业
    （全部带project过滤；空映射/缺失映射也视为未满足，不构成"全终态"）。
    """
    expected: list[str] = list(batch["primary"]) + list(batch["verifier"])
    for name in (
        "aemh_dualvlm_batch_r3_verifier.json",
        "aemh_dualvlm_batch_p2_primary.json",
        "aemh_dualvlm_batch_p4_primary.json",
        "aemh_dualvlm_batch_p5_primary.json",
    ):
        mapping = _load_json(name)
        if isinstance(mapping, dict) and mapping:
            expected.extend(str(v) for v in mapping.values())
        elif mapping is None and name != "aemh_dualvlm_batch_p5_primary.json":
            # p5映射可以尚未产生（无失败重试波）；其余expected文件缺失=对账失败
            raise SystemExit(f"expected map missing: {name}; finalize aborted")
    if not expected:
        raise SystemExit("empty expected work manifest; finalize aborted")
    placeholders = ",".join("?" * len(expected))
    active = conn.execute(
        f"SELECT COUNT(*) FROM monitoring_ai_jobs WHERE job_id IN ({placeholders}) "
        "AND status IN ('queued','running')",
        expected,
    ).fetchone()[0]
    if active:
        print(
            f"batch still processing ({active} active expected jobs); "
            "finalize aborted"
        )
        sys.exit(2)


def _http_json(request: urllib.request.Request, timeout: int) -> dict:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    batch = _load_json("aemh_dualvlm_batch.json")
    if not batch:
        raise SystemExit("missing /tmp/aemh_dualvlm_batch.json")

    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        adjudicate,
    )

    conn = _open_ro_db()
    try:
        # 预检只约束全量收尾（发布不可逆）；dry-run零副作用，运行中也可评估。
        if not dry_run:
            _preflight_expected_terminal(conn, batch)
        prim_map, ver_map, exclusion_stats, selection_identity = (
            _select_cohort_maps(conn, batch)
        )
    finally:
        conn.close()
    print(
        f"maps: primary={len(prim_map)} verifier={len(ver_map)} "
        f"subjects={len(batch['subjects'])} "
        f"selection_identity={selection_identity} "
        f"exclusions={exclusion_stats}"
    )
    if not prim_map or not ver_map:
        raise SystemExit("empty cohort maps after identity validation; abort")

    artifacts_dir = None if dry_run else WORKSPACE / "runtime" / "artifacts"
    if dry_run:
        # D-07：dry-run不import生产main——直接构造只读仓储。
        from services.api.app.monitoring_ai_repository import (
            MonitoringAiRepository,
        )

        ai_repository = MonitoringAiRepository(DB_PATH, lease_seconds=1800)
    else:
        from services.api.app import main

        ai_repository = main.monitoring_ai_repository

    art = adjudicate(
        ai_repository=ai_repository,
        project_id=PROJECT_ID,
        subject_labels=batch["subjects"],
        facts_snapshot_ref=SNAPSHOT_REF,
        primary_job_by_subject=prim_map,
        verifier_job_by_subject=ver_map,
        artifacts_dir=artifacts_dir,
    )
    print("ADJUDICATE", art["counts"])
    if dry_run:
        return

    # ---- 定向核实轮：escalated按提出方发真对侧模型（稳定finding_id关联） ----
    from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (
        merge_focused_verifications,
        submit_focused_verifications,
    )
    from packages.medical_monitoring.intelligence.primitives import content_hash

    escalated = [
        f for f in art["findings"] if f["state"] == "escalated" and f.get("finding_id")
    ]
    wait_timed_out: set[str] = set()
    if escalated:
        domains = main._r7_facts_publication_provider._load_domains()
        submission = submit_focused_verifications(
            verifier_service=main.monitoring_ai_verifier_service,
            primary_service=main.monitoring_ai_service,
            project_id=PROJECT_ID,
            domains=domains,
            escalated=escalated,
            facts_snapshot_ref=FOCUSED_REF,
        )
        json.dump(
            submission.job_by_finding_id, open("/tmp/aemh_fv_jobs.json", "w")
        )
        json.dump(submission.skipped, open("/tmp/aemh_fv_skipped.json", "w"))
        print(
            f"FOCUSED submitted={len(submission.job_by_finding_id)} "
            f"skipped={len(submission.skipped)}"
        )
        # 唤醒worker：本进程直写仓库提交的作业，API侧worker只认wake事件
        # （D-11唤醒衔接——retry_failed已有，finalize同样必须有）。
        try:
            wake = urllib.request.Request(
                # BASE指向r7产品面；queue控制面在modules/medical-monitoring层
                f"{BASE.rsplit('/r7', 1)[0]}/ai/queue/resume",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(wake, timeout=15).read()
        except Exception as exc:
            print(f"WARN: post-submit wake failed ({exc})")
        # 等待聚焦核实轮终态（最多300分钟）；超时项以执行状态入合并，不伪装成医学反证
        deadline = time.time() + 300 * 60
        while time.time() < deadline:
            time.sleep(120)
            active = 0
            for job_id in submission.job_by_finding_id.values():
                try:
                    if (
                        main.monitoring_ai_repository.get(PROJECT_ID, job_id).status
                        in ("queued", "running")
                    ):
                        active += 1
                except Exception:
                    pass
            print(f"fv active={active}", flush=True)
            if not active:
                break
        else:
            wait_timed_out = set(submission.job_by_finding_id.keys())

    # ---- 合并定向核实结果并原子落盘 ----
    fv_map = _load_json("aemh_fv_jobs.json") or {}
    merged = merge_focused_verifications(
        ai_repository=ai_repository,
        project_id=PROJECT_ID,
        findings=art["findings"],
        focused_job_by_finding_id={str(k): str(v) for k, v in fv_map.items()},
        wait_timed_out_ids=wait_timed_out,
    )
    counts = Counter(f["state"] for f in merged)
    executions = Counter(
        f.get("verification_execution", "") for f in merged if f["state"] != "accepted" or f.get("verification_execution")
    )
    art["findings"] = merged
    art["counts"] = dict(counts)
    art.pop("content_sha256", None)
    artifact_sha = content_hash(art)
    art["content_sha256"] = artifact_sha
    artifact = (
        WORKSPACE / "runtime" / "artifacts" / f"aemh-findings-{SNAPSHOT_REF}.json"
    )
    tmp_path = artifact.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(art, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    os.replace(tmp_path, artifact)
    print("MERGED", dict(counts), "executions:", dict(executions))

    # ---- scoped原子哨兵（D-08）：project+入选作业身份+分析内容 ----
    policy8 = hashlib.sha256(
        json.dumps(
            {
                "snapshot_ref": SNAPSHOT_REF,
                "focused_ref": FOCUSED_REF,
                "selection_identity": selection_identity,
                "artifact_sha256": artifact_sha,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:8]
    sentinel = Path(f"/tmp/dualvlm_finalize_done.{PROJECT_ID}.{policy8}.flag")
    try:
        fd = os.open(sentinel, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        print(f"finalize already done for this input/policy ({sentinel.name}); skip")
        return
    try:
        _publish(artifact_sha)
    except Exception:
        sentinel.unlink(missing_ok=True)
        raise
    Path("/tmp/aemh_dualvlm_finalize_done.flag").write_text(
        "done"
    )  # 旧循环停止信号（兼容watchdog v2），非幂等凭据


def _publish(artifact_sha: str) -> None:
    """冻结run发布：幂等键绑定分析内容hash；publication轮询替代sleep(8)。"""
    with urllib.request.urlopen(f"{BASE}/run-setup/options", timeout=120) as r:
        options = json.loads(r.read())
    snapshot_token = (options.get("current_data") or {}).get("snapshot_token")
    if not snapshot_token:
        raise SystemExit("run-setup/options returned no snapshot token; abort")
    body = json.dumps(
        {
            "mode": "daily",
            "execution_basis": "full",
            "current_snapshot_token": snapshot_token,
            "risk_rule_tokens": [],
            "idempotency_key": f"dualvlm-full1-publish-{artifact_sha[:12]}",
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/runs/prepare-and-start",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
        method="POST",
    )
    prepared = _http_json(req, timeout=300)
    run_token = prepared["public_run_token"]
    print("RUN", run_token)

    pub_req = lambda: urllib.request.Request(  # noqa: E731
        f"{BASE}/runs/{run_token}/publication",
        data=json.dumps({"idempotency_key": f"dualvlm-full1-pub-{artifact_sha[:12]}"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
        method="POST",
    )
    pub = None
    last_error: Exception | None = None
    for _attempt in range(12):
        try:
            pub = _http_json(pub_req(), timeout=600)
            break
        except urllib.error.HTTPError as exc:
            last_error = exc
            # run尚未就绪：轮询替代固定sleep(8)
            time.sleep(5)
    if pub is None:
        raise SystemExit(f"publication failed after polling: {last_error}")
    print("PUB", pub.get("publication_state"))

    with urllib.request.urlopen(
        f"{BASE}/runs/{run_token}/result-entry", timeout=120
    ) as r:
        entry = json.loads(r.read())
    token = entry.get("result_context_token") or ""
    if not token:
        raise SystemExit("result-entry returned empty token; not recording success")
    Path("/tmp/result_token.txt").write_text(token)
    print("TOKEN", token)


if __name__ == "__main__":
    main()
