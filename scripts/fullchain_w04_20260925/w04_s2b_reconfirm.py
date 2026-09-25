"""W04-S2b：修复后重跑确认链（20260926）。

第三类形态（表达式字符串→符号算子）归一修复已落地并通过回归
（11/11）。本驱动器只重跑确认段：对S2已accept的14条事实重排失败
模板作业（操作员语义retry_terminal）、start、轮询生成、逐条裁决
确认，目标 ≥3 条 medically_confirmed（≥2 种 fact_type）。
证据追加写入 s2b_evidence.jsonl；不重复提取/裁决（零新增提取成本）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKBENCH_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import w04_s2_all_topics as m  # noqa: E402

EVIDENCE = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s2b_evidence.jsonl"
)


def _record(row: dict) -> None:
    with open(EVIDENCE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False)[:240], flush=True)


def main() -> int:
    evidence = (
        WORKBENCH_ROOT
        / "runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/s2_evidence.jsonl"
    )
    rows = [
        json.loads(line)
        for line in evidence.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selects = [r for r in rows if r.get("step") == "s5_select" and r.get("ok")]
    if not selects:
        _record({"step": "s2b", "kind": "summary", "ok": False, "reason": "no s5_select row"})
        return 2
    selected = selects[-1]["selected"]
    _record(
        {
            "ts": m._now(),
            "step": "s2b",
            "kind": "summary",
            "ok": True,
            "message": f"重跑确认链：{len(selected)} 条已accept事实",
        }
    )
    candidates: list[dict] = []
    for fact in selected:
        fact_revision_id = str(fact.get("fact_revision_id"))
        status, body = m._http(
            "s2b_status",
            "GET",
            f"{m.MM_PREFIX}/rule-template-recommendations/facts/{fact_revision_id}/status",
            payload=None,
        )
        state_version = 1
        if status == 200 and isinstance(body, dict):
            state_version = int(
                body.get("fact_state_version")
                or body.get("state_version")
                or 1
            )
        candidates.append(
            {
                "fact_revision_id": fact_revision_id,
                "fact_type": str(fact.get("fact_type")),
                "state_version": state_version,
            }
        )
    confirmed = m.step5_confirm_chain(candidates)
    types = {str(c.get("fact_type")) for c in confirmed}
    ok = len(confirmed) >= m.CONFIRM_TARGET and len(types) >= m.TYPE_COVERAGE_TARGET
    _record(
        {
            "ts": m._now(),
            "step": "s2b",
            "kind": "summary",
            "ok": ok,
            "confirmed": len(confirmed),
            "fact_types": sorted(types),
            "message": (
                f"medically_confirmed {len(confirmed)} 条 / "
                f"{len(types)} 种 fact_type（目标 ≥{m.CONFIRM_TARGET} / ≥{m.TYPE_COVERAGE_TARGET}）"
            ),
        }
    )
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
