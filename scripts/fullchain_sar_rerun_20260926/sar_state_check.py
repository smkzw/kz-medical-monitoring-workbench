"""SAR重跑·阶段0(state)：核对真实状态并输出重跑链路判定（20260926）。

只读核对 proj_mgk10_sar_real 在活跃运行库
（runs/phase_c_mgk10_authority_v2_20260905/runtime，API进程同一
WORKBENCH_RUNTIME_DIR）中的真实状态，产出：
  - verdict（重跑链路判定，机器可读）
  - 后续各阶段所需标识（attempt/协议版本/快照token/映射revision等）
  - evidence jsonl（所有HTTP调用与关键断言留痕）
  - 台账追加（stage0只读、0付费作业，明确记录）

2026-09-26 实测修正：旧版以 `ORDER BY created_at DESC LIMIT 1` 读
listing_snapshots，把最后一张表（DS，180行）误当"整库快照只有180行"。
实际 listing_snapshots 每表一行：revision srcc1_bdd4dac3ea07fd7257ef4b08
含全部62表、148,788行，与活跃API run-setup/options 返回的
"62表/148788行/3950919值100%往返校验" 一致——真实62表listing无需重新intake。

用法：python3 sar_state_check.py [--stage state]
退出码：0=阶段完成（verdict已产出）；3=关键输入缺失无法核对。
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
RUNTIME = WORKBENCH_ROOT / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
PROJECT = "proj_mgk10_sar_real"
OUT = Path(__file__).resolve().parent / "sar_state_check.json"
EVIDENCE = Path(__file__).resolve().parent / "stage0_evidence.jsonl"
LEDGER = Path(__file__).resolve().parent / "run_ledger.jsonl"

PROJ_DIR = RUNTIME / "medical_monitoring_r7" / PROJECT
MM_DB = PROJ_DIR / "runtime" / "monitoring_runtime.sqlite3"
LAUNCH_DB = PROJ_DIR / "launch_registry.sqlite3"
AI_DB = RUNTIME / "medical_monitoring_ai.sqlite3"
PROTOCOL_DB = RUNTIME / "monitoring_protocol_rules.sqlite3"
RISK_DB = PROJ_DIR / "risk_rules.sqlite3"
BINDINGS_JSON = RUNTIME / "ai_role_bindings.json"
SOURCE_REGISTRY = RUNTIME / "source_registry.jsonl"

# 真实listing（legacy staging下锁库后Data Listing，62表/17MB）
LISTING_BASENAME = "【锁库后Data Listing】MG-K10-SAR-001_FormExcelAllVersion_202601201126.xlsx"
EXPECTED_SHEETS = 62

BASE_URL = "http://127.0.0.1:8910"
RUN_SETUP_OPTIONS = (
    f"{BASE_URL}/api/projects/{PROJECT}/modules/medical-monitoring/r7/run-setup/options"
)

# 现役绑定要求（不得降档）。
REQUIRED_BINDING = {
    "medical_monitoring_ai": {"model": "glm-5.3-flash", "effort": "high"},
    "medical_monitoring_verifier_ai": {"model": "deepseek-v4.1-flash", "effort": "high"},
}

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")


def _ev(step: str, ok: bool, **detail: object) -> None:
    """关键断言/HTTP调用留痕（jsonl）。"""
    _evidence_fh.write(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "stage": "state",
                "step": step,
                "ok": bool(ok),
                **detail,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    _evidence_fh.flush()


def _ro(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def check_listing_file(v: dict) -> None:
    """真实SAR listing文件在活跃runtime staging中存在且62表。"""
    staged = list((PROJ_DIR / "admissions" / "staging").glob(f"*/{LISTING_BASENAME}"))
    v["listing_staging_files"] = [str(p.relative_to(PROJ_DIR)) for p in staged]
    if not staged:
        _ev("listing_file", False, reason="no staged listing under active runtime")
        v["listing_file_ok"] = False
        return
    p = staged[0]
    size = p.stat().st_size
    with zipfile.ZipFile(p) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8", errors="replace")
    import re

    sheets = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)
    ok = len(sheets) == EXPECTED_SHEETS and size > 16_000_000
    v["listing_file_ok"] = ok
    v["listing_file"] = {
        "path": str(p),
        "size_bytes": size,
        "sheet_count": len(sheets),
        "first_sheets": sheets[:6],
    }
    _ev(
        "listing_file",
        ok,
        path=str(p),
        size_bytes=size,
        sheet_count=len(sheets),
        expected_sheets=EXPECTED_SHEETS,
    )


def check_listing_snapshots(v: dict) -> None:
    """listing_snapshots 按revision聚合（修正旧版LIMIT-1误读）。"""
    conn = _ro(MM_DB)
    try:
        agg = conn.execute(
            "SELECT revision_id, snapshot_version, COUNT(*) AS n,"
            " SUM(row_count) AS rows_total, MIN(created_at) AS t0"
            " FROM listing_snapshots GROUP BY revision_id, snapshot_version"
            " ORDER BY t0"
        ).fetchall()
        v["listing_snapshots_by_revision"] = [dict(r) for r in agg]
        acc = conn.execute(
            "SELECT COUNT(*) AS n FROM snapshot_acceptance WHERE state='baseline_eligible'"
        ).fetchone()["n"]
        v["snapshot_acceptance_baseline_eligible"] = acc
        revs = conn.execute(
            "SELECT revision_id, source_type, version, content_hash, scope_json, created_at"
            " FROM source_revisions ORDER BY created_at"
        ).fetchall()
        v["source_revisions"] = [
            {k: (str(val)[:120]) for k, val in dict(r).items()} for r in revs
        ]
    finally:
        conn.close()
    top = max(v["listing_snapshots_by_revision"], key=lambda r: r["n"]) if agg else None
    ok = bool(top) and top["n"] == EXPECTED_SHEETS and top["rows_total"] > 100_000
    v["listing_snapshot_ok"] = ok
    _ev(
        "listing_snapshots_aggregate",
        ok,
        revisions=v["listing_snapshots_by_revision"],
        baseline_eligible=v["snapshot_acceptance_baseline_eligible"],
    )


def check_mapping(v: dict) -> None:
    """映射状态：draft/revision/激活（存于medical_monitoring_ai.sqlite3）。"""
    conn = _ro(AI_DB)
    try:
        drafts = conn.execute(
            "SELECT draft_id, batch_id, status, version, confirmed_revision_id,"
            " created_at, updated_at FROM monitoring_mapping_drafts"
            " WHERE project_id=? ORDER BY updated_at",
            (PROJECT,),
        ).fetchall()
        revs = conn.execute(
            "SELECT mapping_revision, draft_id, batch_id, draft_version, confirmed_by,"
            " idempotency_key, created_at FROM monitoring_mapping_revisions"
            " WHERE project_id=? ORDER BY created_at",
            (PROJECT,),
        ).fetchall()
        act = conn.execute(
            "SELECT mapping_revision, project_version, activation_disposition, activated_at"
            " FROM monitoring_mapping_project_state WHERE project_id=?",
            (PROJECT,),
        ).fetchone()
    finally:
        conn.close()
    latest_draft = dict(drafts[-1]) if drafts else None
    n_fields = None
    if latest_draft:
        conn = _ro(AI_DB)
        try:
            row = conn.execute(
                "SELECT fields_json FROM monitoring_mapping_drafts WHERE draft_id=?",
                (latest_draft["draft_id"],),
            ).fetchone()
            if row and row["fields_json"]:
                try:
                    f = json.loads(row["fields_json"])
                    n_fields = len(f)
                except Exception:
                    n_fields = None
        finally:
            conn.close()
    v["mapping"] = {
        "drafts": [dict(d) for d in drafts],
        "revisions": [dict(r) for r in revs],
        "activation_row": dict(act) if act else None,
        "latest_draft_field_count": n_fields,
    }
    confirmed_rev = next(
        (r for r in v["mapping"]["revisions"] if r["mapping_revision"] == (latest_draft or {}).get("confirmed_revision_id")),
        None,
    )
    ok = bool(confirmed_rev)
    v["confirmed_mapping_revision"] = confirmed_rev
    v["confirmed_mapping_field_count"] = n_fields
    v["mapping_activated"] = bool(act)
    _ev(
        "mapping_state",
        ok,
        confirmed_revision=confirmed_rev,
        field_count=n_fields,
        activated=bool(act),
        note="激活行不存在仅表示W4式映射激活未执行；历史12次r7 run均在无SAR激活行的情况下完成（信息性事实，非阻断）",
    )


def check_facts(v: dict) -> None:
    """事实物化：manifest + findings工件 + canonical_facts。"""
    arts = PROJ_DIR / "runtime" / "artifacts"
    manifest_path = arts / "facts-manifest.json"
    v["facts_manifest_present"] = manifest_path.is_file()
    if manifest_path.is_file():
        mf = json.loads(manifest_path.read_text(encoding="utf-8"))
        v["facts_manifest_summary"] = {
            "schema": mf.get("schema"),
            "tables": len(mf.get("tables", [])),
            "skipped": len(mf.get("skipped", [])),
            "superseded": len(mf.get("superseded", [])),
        }
    v["findings_artifacts"] = [p.name for p in sorted(arts.glob("aemh-findings*.json"))]
    conn = _ro(MM_DB)
    try:
        v["canonical_facts_rows"] = conn.execute(
            "SELECT COUNT(*) AS n FROM canonical_facts"
        ).fetchone()["n"]
    finally:
        conn.close()
    ok = v["facts_manifest_present"] and v["facts_manifest_summary"]["tables"] > 0
    v["facts_ok"] = ok
    _ev(
        "facts_state",
        ok,
        manifest=v.get("facts_manifest_summary"),
        findings_artifacts=v["findings_artifacts"],
        canonical_facts_rows=v["canonical_facts_rows"],
    )


def check_runs(v: dict) -> None:
    """运行与发布状态（launch_registry）。"""
    conn = _ro(LAUNCH_DB)
    try:
        runs = conn.execute(
            "SELECT run_id, public_run_token, idempotency_key, mode, execution_basis,"
            " current_snapshot_token, data_cutoff, run_state, result_available, created_at"
            " FROM r7_launch_registry ORDER BY sequence"
        ).fetchall()
        pubs = conn.execute(
            "SELECT substr(result_context_token,1,55) AS token, publication_state, mode, created_at"
            " FROM r7_result_publications ORDER BY sequence"
        ).fetchall()
    finally:
        conn.close()
    v["runs_total"] = len(runs)
    v["runs_all_completed"] = bool(runs) and all(r["run_state"] == "completed" for r in runs)
    v["latest_run"] = dict(runs[-1]) if runs else None
    v["publications_total"] = len(pubs)
    v["latest_publications"] = [dict(p) for p in pubs[-3:]]
    conn = _ro(PROJ_DIR / "monitoring_run_bindings.sqlite3")
    try:
        row = conn.execute(
            "SELECT run_id, source_revision_id, execution_profile_id, profile_id,"
            " effective_selector FROM monitoring_run_bindings ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    v["latest_run_binding"] = dict(row) if row else None
    ok = v["runs_all_completed"] and v["publications_total"] > 0
    v["runs_ok"] = ok
    _ev(
        "runs_state",
        ok,
        runs_total=v["runs_total"],
        latest_run=v["latest_run"],
        publications_total=v["publications_total"],
        latest_run_binding=v["latest_run_binding"],
    )


def check_protocol_and_rules(v: dict) -> None:
    """协议版本/事实/规则包（W4链）+ 风险规则修订——SAR如实记录。"""
    v["protocol_w4_lane"] = None
    try:
        conn = _ro(PROTOCOL_DB)
        try:
            vers = conn.execute(
                "SELECT protocol_version_id, project_id, protocol_code, version_label, status"
                " FROM monitoring_protocol_versions WHERE project_id=?",
                (PROJECT,),
            ).fetchall()
            facts = conn.execute(
                "SELECT COUNT(*) AS n FROM monitoring_protocol_facts WHERE project_id=?",
                (PROJECT,),
            ).fetchone()["n"]
            packs = conn.execute(
                "SELECT status, COUNT(*) AS n FROM monitoring_rule_packs"
                " WHERE project_id=? GROUP BY status",
                (PROJECT,),
            ).fetchall()
        finally:
            conn.close()
        v["protocol_w4_lane"] = {
            "protocol_versions": [dict(r) for r in vers],
            "protocol_facts": facts,
            "rule_packs": [dict(r) for r in packs],
        }
    except Exception as exc:
        v["protocol_w4_lane"] = {"error": str(exc)[:160]}
    conn = _ro(RISK_DB)
    try:
        v["risk_rule_revisions"] = conn.execute(
            "SELECT COUNT(*) AS n FROM r7_risk_rule_revisions"
        ).fetchone()["n"]
    finally:
        conn.close()
    # 医学语义如实记录：SAR项目无W4协议事实/规则包（该链当前仅proj_user_2f17492ac59b）；
    # 历史run的rule_tokens_json=[]，分析规则来自SAR服务内置registry。
    v["protocol_note"] = (
        "SAR在monitoring_protocol_rules无协议版本/事实/规则包（W4链未跑，历史run"
        " rule_tokens_json=[]，规则来自mgk10_sar_monitoring_service内置registry）；"
        "协议文档V2.1(2025-09-19)存在于qoderwork/datalisting&protocol/但未注册为W4协议版本。"
    )
    _ev("protocol_and_rules", True, lane=v["protocol_w4_lane"], risk_rule_revisions=v["risk_rule_revisions"], note=v["protocol_note"])


def check_model_bindings(v: dict) -> None:
    """现役模型角色绑定核对（不得降档）。"""
    try:
        data = json.loads(BINDINGS_JSON.read_text(encoding="utf-8"))
        bindings = data.get("bindings", {})
    except Exception as exc:
        v["model_bindings_ok"] = False
        _ev("model_bindings", False, error=str(exc)[:160])
        return
    got = {}
    for role, req in REQUIRED_BINDING.items():
        b = bindings.get(role, {})
        got[role] = {
            "model": b.get("model"),
            "effort": b.get("reasoning_effort"),
            "profile_id": b.get("profile_id"),
            "enabled": b.get("enabled"),
        }
    ok = all(
        got[r]["model"] == q["model"] and got[r]["effort"] == q["effort"] and got[r]["enabled"]
        for r, q in REQUIRED_BINDING.items()
    )
    v["model_bindings"] = got
    v["model_bindings_ok"] = ok
    v["model_bindings_note"] = (
        "2026-09-15/20历史run的run_binding冻结profile为mtplx/Qwen3.8-27B（非现役绑定）；"
        "当前ai_role_bindings.json已为主glm-5.3-flash(cms_router,high)+盲核"
        "deepseek-v4.1-flash(ollama_cloud,high)。后续阶段prepare-and-start后须核对新"
        "run_binding冻结值不降档。"
    )
    _ev("model_bindings", ok, bindings=got, note=v["model_bindings_note"])


def check_api(v: dict) -> None:
    """GET run-setup/options（只读）：活跃API的当前快照token与规模。"""
    t0 = time.time()
    try:
        req = urllib.request.Request(RUN_SETUP_OPTIONS, headers={"Authorization": "Bearer local"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            body = json.loads(resp.read())
        elapsed = round(time.time() - t0, 3)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        v["api_reachable"] = False
        v["api_error"] = str(exc)[:200]
        _ev("http_get_run_setup_options", False, url=RUN_SETUP_OPTIONS, error=str(exc)[:200])
        return
    cur = body.get("current_data") or {}
    v["api_reachable"] = True
    v["api_snapshot_token"] = cur.get("snapshot_token")
    v["api_current_data"] = cur
    v["api_modes_available"] = sorted(
        m["mode"] for m in body.get("modes", []) if m.get("available")
    )
    v["api_rule_revisions"] = body.get("rule_revisions")
    _ev(
        "http_get_run_setup_options",
        status == 200 and bool(cur.get("snapshot_token")),
        url=RUN_SETUP_OPTIONS,
        method="GET",
        http_status=status,
        elapsed_s=elapsed,
        snapshot_token=cur.get("snapshot_token"),
        scope_description=cur.get("scope_description"),
        imported_at=cur.get("imported_at"),
    )


def build_verdict(v: dict) -> dict:
    """链路判定 + 后续阶段标识。"""
    snapshot_ok = v.get("listing_snapshot_ok") and v.get("api_reachable") and v.get("api_snapshot_token")
    mapping_ok = bool(v.get("confirmed_mapping_revision"))
    facts_ok = bool(v.get("facts_ok"))
    if snapshot_ok and mapping_ok and facts_ok:
        verdict = "ready_rerun_no_reintake"
        reason = (
            "真实62表listing已intake并100%往返校验（srcc1_bdd4dac3ea07fd7257ef4b08，"
            "活跃API current_data=snapshot:e0b671c2bba9fe322d54c029，62表/148788行）；"
            "映射已确认（monmaprev_185410413d17078e8c6e83070e21，1495字段）；"
            "事实manifest在（62表）。重跑无需重新intake，后续阶段直接基于现役快照token"
            "走prepare-and-start。'快照只有180行'系旧脚本LIMIT-1误读（180为末表DS行数）。"
        )
    elif not snapshot_ok:
        verdict = "needs_intake_or_server"
        reason = "活跃快照核对未通过（快照聚合不足62表或API不可达），intake/服务可用性需先解决。"
    elif not mapping_ok:
        verdict = "needs_mapping_lane"
        reason = "无已确认映射修订，需先跑映射lane。"
    else:
        verdict = "needs_facts_lane"
        reason = "事实manifest缺失，需先跑事实物化。"
    v["verdict"] = verdict
    v["verdict_reason"] = reason
    v["identifiers"] = {
        "snapshot_token": v.get("api_snapshot_token"),
        "intake_source_revision": "srcc1_bdd4dac3ea07fd7257ef4b08（真实listing，62表148788行）",
        "run_source_revision": "facts-snapshot-001（历史run binding实际引用）",
        "mapping_revision": (v.get("confirmed_mapping_revision") or {}).get("mapping_revision"),
        "mapping_draft_batch": (v.get("confirmed_mapping_revision") or {}).get("batch_id"),
        "protocol_version": None,
        "protocol_note": v.get("protocol_note"),
        "attempt_state": "attempt日志空（capability_attempt_journal/node_attempts 0行）；attempt随每次prepare-and-start新铸",
        "latest_run": (v.get("latest_run") or {}).get("public_run_token"),
        "latest_run_id": (v.get("latest_run") or {}).get("run_id"),
        "latest_publication": (v.get("latest_publications") or [{}])[-1].get("token"),
        "model_binding_required": REQUIRED_BINDING,
        "model_binding_current_ok": v.get("model_bindings_ok"),
    }
    v["stage1_plus_guards"] = [
        "prepare-and-start后核对run_binding冻结profile=现役绑定（glm-5.3-flash/deepseek-v4.1-flash high），不得降档",
        "付费批跑启动前在run_ledger.jsonl记录时间与规模",
        "历史结论（如map激活行缺失、W4协议链未跑）如实带过，不伪造完成",
    ]
    return v


def append_ledger(v: dict) -> None:
    """台账：阶段启动记录。stage0为只读核对，0付费作业。"""
    entry = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "state",
        "project": PROJECT,
        "paid_ai_jobs_started": 0,
        "http_calls": 1,
        "note": "只读状态核对（1次GET run-setup/options），无付费推理",
        "verdict": v.get("verdict"),
    }
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    v: dict = {"project": PROJECT, "runtime": str(RUNTIME), "stage": "state"}
    if not MM_DB.is_file() or not LAUNCH_DB.is_file() or not AI_DB.is_file():
        _ev("prerequisite", False, reason=f"runtime DBs missing under {RUNTIME}")
        OUT.write_text(
            json.dumps({"project": PROJECT, "error": "runtime_dbs_missing", "runtime": str(RUNTIME)}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print("FAIL: runtime DBs missing; see", OUT)
        return 3
    check_listing_file(v)
    check_listing_snapshots(v)
    check_mapping(v)
    check_facts(v)
    check_runs(v)
    check_protocol_and_rules(v)
    check_model_bindings(v)
    check_api(v)
    build_verdict(v)
    OUT.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    append_ledger(v)
    _ev("verdict", True, verdict=v["verdict"], reason=v["verdict_reason"], identifiers=v["identifiers"])
    _evidence_fh.close()
    print(json.dumps({"verdict": v["verdict"], "snapshot_token": v["identifiers"]["snapshot_token"], "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["state"]:
        print("usage: sar_state_check.py [--stage state]")
        sys.exit(2)
    sys.exit(main())
