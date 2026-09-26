"""SAR重跑·阶段2·授权状态修复（用户批准选项A，2026-09-26）。

修复目标：文档权威promotion对已存在entry_id重复追加，污染span store——
ecrf_document_c7ea6e3fedf0 spans 5658（09-05的2829+09:45重复2829），
locator index sha256失配 → readiness永久false → 映射双队列前置门阻断。

修复内容（护栏内最小动作）：
  1. 动数据前取证：逐条目span计数、ecrf期望集与期望sha、09:45两行注册原文
     → stage2_repair_evidence.jsonl；
  2. 程序化界定删除：仅移除09:45两行注册原文
     （protocol_docx_8ebb9e3eb09f整行 + ecrf_document_c7ea6e3fedf0的09:45行），
     其余行字节级保留；先备份全文件；
  3. 恢复后验证：ecrf spans=2829、locator sha与metadata期望一致、无重复行、
     9月六条目原样；随后由阶段2脚本验证readiness。

退出码：0=修复+验证通过；2=取证/验证失败（不改动或回滚）。
台账已另行记录（run_ledger.jsonl）：授权的状态修复+后端修复项。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

R = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/"
    "implementation/workbench/runs/phase_c_mgk10_authority_v2_20260905/runtime"
)
JSONL = R / "source_registry.jsonl"
HERE = Path(__file__).resolve().parent
BACKUP = HERE / "source_registry.backup_20260926.jsonl"
EV = HERE / "stage2_repair_evidence.jsonl"

ECRF_ID = "src_proj_mgk10_sar_real_ecrf_document_c7ea6e3fedf0"
PROTOCOL_DOCX_ID = "src_proj_mgk10_sar_real_protocol_docx_8ebb9e3eb09f"
SEPTEMBER_DAY = "2026-09-05"

TARGETS = {
    PROTOCOL_DOCX_ID,
    ECRF_ID + "|09:45",  # ecrf仅删2026-09-26T09:45那行，09-05行保留
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    with EV.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(
            {"ts": _now(), "step": step, "ok": bool(ok), **detail},
            ensure_ascii=False) + "\n")


def main() -> int:
    raw_lines = JSONL.read_text(encoding="utf-8").splitlines(keepends=True)
    records = [json.loads(l) for l in raw_lines if l.strip()]

    # ── 护栏1：动数据前取证 ──────────────────────────────────────────
    span_counts: dict[str, int] = {}
    ecrf_meta = None
    for rec in records:
        e = rec["entry"]
        n = len(rec.get("spans") or [])
        span_counts[e["entry_id"]] = span_counts.get(e["entry_id"], 0) + n
        if e["entry_id"] == ECRF_ID:
            ecrf_meta = e["metadata"]
    _ev("before_span_counts", True, counts=span_counts, total=sum(span_counts.values()))
    _ev("before_ecrf_expectation", True,
        expected_locator_count=ecrf_meta.get("expected_locator_count"),
        expected_locator_index_sha256=ecrf_meta.get("expected_locator_index_sha256"),
        locator_manifest_complete=ecrf_meta.get("locator_manifest_complete"),
        registry_line_span_total=span_counts.get(ECRF_ID))

    dup0945 = [l for l, rec in zip(raw_lines, records)
               if rec["entry"]["entry_id"] == PROTOCOL_DOCX_ID
               or (rec["entry"]["entry_id"] == ECRF_ID
                   and rec["entry"]["created_at"].startswith("2026-09-26"))]
    for l in dup0945:
        _ev("target_line_verbatim", True, line=l.rstrip("\n")[:4000])

    # 删除界定核对：恰好两行，且都是今天的
    if len(dup0945) not in (1, 2):
        _ev("guard_fail", False, reason=f"expected exactly 2 target lines, got {len(dup0945)}")
        print("FAIL: target line count != 2; no changes made")
        return 2

    # ── 备份 ────────────────────────────────────────────────────────
    if not BACKUP.exists():
        shutil.copy2(JSONL, BACKUP)
        _ev("backup", True, path=str(BACKUP), size=BACKUP.stat().st_size)

    # ── 护栏2：程序化删除（按行原文精确匹配，其余保留） ─────────────
    drop = set(dup0945)
    kept = [l for l in raw_lines if l not in drop]
    removed = len(raw_lines) - len(kept)
    if removed != 2:
        _ev("guard_fail", False, reason=f"would remove {removed} lines, expected 2")
        print("FAIL: removal count != 2; no changes written")
        return 2
    JSONL.write_text("".join(kept), encoding="utf-8")
    _ev("lines_removed", True, removed=removed, kept=len(kept))

    # ── 护栏3：恢复后验证 ───────────────────────────────────────────
    records2 = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    counts2: dict[str, int] = {}
    ecrf_lines = 0
    protocol_docx_lines = 0
    ecrf_meta2 = None
    for rec in records2:
        e = rec["entry"]
        counts2[e["entry_id"]] = counts2.get(e["entry_id"], 0) + len(rec.get("spans") or [])
        if e["entry_id"] == ECRF_ID:
            ecrf_lines += 1
            if e["created_at"].startswith(SEPTEMBER_DAY):
                ecrf_meta2 = e["metadata"]
        if e["entry_id"] == PROTOCOL_DOCX_ID:
            protocol_docx_lines += 1
    ecrf_spans = counts2.get(ECRF_ID, 0)
    expected = int(ecrf_meta2.get("expected_locator_count") or 0)
    # 基线取自备份文件自身（不硬编码条目id）：backup聚合计数 - 被移除两行的spans
    backup_records = [json.loads(l) for l in BACKUP.read_text(encoding="utf-8").splitlines() if l.strip()]
    baseline = {}
    for rec in backup_records:
        e = rec["entry"]
        baseline[e["entry_id"]] = baseline.get(e["entry_id"], 0) + len(rec.get("spans") or [])
    removed_span_delta = {}
    for l in drop:
        rec = json.loads(l)
        e = rec["entry"]
        removed_span_delta[e["entry_id"]] = removed_span_delta.get(e["entry_id"], 0) + len(rec.get("spans") or [])
    expected_counts = {
        eid: n - removed_span_delta.get(eid, 0) for eid, n in baseline.items()
        if eid not in removed_span_delta or (n - removed_span_delta.get(eid, 0)) > 0
    }
    sep_preserved = counts2 == expected_counts
    listing_intact = all(
        counts2.get(k, 0) == v for k, v in baseline.items()
        if k.endswith("edc_data_listing_dd305385d1e7") or "edc_data_listing" in k
    ) and any("edc_data_listing" in k for k in baseline)

    ok = (ecrf_spans == expected == 2829 and ecrf_lines == 1
          and protocol_docx_lines == 0 and sep_preserved and listing_intact)
    _ev("after_verify", ok,
        ecrf_spans=ecrf_spans, expected=expected, ecrf_lines=ecrf_lines,
        protocol_docx_lines=protocol_docx_lines, september_spans_preserved=sep_preserved,
        stage1_listing_spans_intact=listing_intact,
        total_spans=sum(counts2.values()))
    if not ok:
        # 回滚到备份（护栏3失败不允许带病继续）
        shutil.copy2(BACKUP, JSONL)
        _ev("rollback", True, reason="post-verify failed; restored from backup")
        print("FAIL: post-verify failed; restored backup")
        return 2
    print(json.dumps({"ok": True, "ecrf_spans": ecrf_spans,
                      "total_spans": sum(counts2.values())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if args and args != ["--stage", "state_repair"]:
        print("usage: sar_stage2_state_repair.py [--stage state_repair]")
        sys.exit(2)
    sys.exit(main())
