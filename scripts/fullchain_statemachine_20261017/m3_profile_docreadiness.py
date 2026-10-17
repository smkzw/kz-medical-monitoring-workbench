"""M3剖析采样（02_DESIGN R4）：document_readiness热路径归因。

与8911同env导入services.api.app.main，cProfile跑
_r7_admission_mapping_pipeline.document_readiness（缓存已启用的读路径），
输出cumtime top。只读路径，不落权威写。

2026-10-17 实跑结果（本文件原在/tmp，收入证据目录）：
  import main 5.16s / warmup 14.44s / profiled 39.91s（cProfile开销放大）
  top cum：mapping_pipeline.document_readiness 39.9s
    → monitoring_document_evidence.resolve 38.9s
      → _role_evidence×4 / _current_binding×2 34.7s
        → source_intake.assert_operational_sources_usable×2 34.7s
          → source_intake.list_results×10 22.7s / _read_all×10 22.1s（tottime 9.1s，A1 JSONL全量重读）
          → main._expected_source_context×8 15.2s
            → project_source_manifest.build_manifest×24 15.1s
              → _monitoring_facts_materialized×24 → fact_materialization.latest_fact_materialization_ready×24 14.9s
                → graph.store_base.__init__×27 13.9s（反复开图库）
          → _monitoring_entry_validation_is_usable×6 11.1s（A3复查）
    pydantic model_validate×1848 7.4s
  结论：verifier重放已被S8缓存消掉（profile中不可见）；剩余成本全在S8范围外。
"""

import cProfile
import io
import os
import pstats
import sys
import time
from pathlib import Path

ROOT = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench"
)
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "WORKBENCH_RUNTIME_DIR",
    str(ROOT / "runs/tester_loop_iso_20260928/runtime"),
)
os.environ.setdefault("WORKBENCH_LOCAL_SINGLE_USER", "1")
os.environ.setdefault("WORKBENCH_AI_RUNTIME", "api")
os.environ["WORKBENCH_DOCUMENT_VERDICT_CACHE"] = "1"

t0 = time.perf_counter()
import services.api.app.main as m  # noqa: E402

t1 = time.perf_counter()
print(f"import main: {t1 - t0:.2f}s", flush=True)

resolver = m.monitoring_document_evidence_resolver
enabled = (
    resolver.verdict_store.document_verdict_cache_enabled()
    if resolver.verdict_store is not None
    and callable(
        getattr(resolver.verdict_store, "document_verdict_cache_enabled", None)
    )
    else False
)
print(f"verdict_cache_enabled={enabled}", flush=True)

PROJECT = "proj_user_6ef58ac151e1"
ATTEMPT = "stg-cd69899943ba42618f589ba07a134a59"
WORKSPACE = (
    ROOT
    / "runs/tester_loop_iso_20260928/runtime/medical_monitoring_r7"
    / PROJECT
)

t2 = time.perf_counter()
m._r7_admission_mapping_pipeline.document_readiness(
    project_id=PROJECT,
    attempt_id=ATTEMPT,
    workspace_dir=WORKSPACE,
)
t3 = time.perf_counter()
print(f"warmup call: {t3 - t2:.2f}s", flush=True)

profiler = cProfile.Profile()
t4 = time.perf_counter()
profiler.enable()
m._r7_admission_mapping_pipeline.document_readiness(
    project_id=PROJECT,
    attempt_id=ATTEMPT,
    workspace_dir=WORKSPACE,
)
profiler.disable()
t5 = time.perf_counter()
print(f"profiled call: {t5 - t4:.2f}s", flush=True)

stream = io.StringIO()
stats = pstats.Stats(profiler, stream=stream)
stats.sort_stats("cumulative").print_stats(28)
text = stream.getvalue()
print("\n".join(line.replace(str(ROOT) + "/", "") for line in text.splitlines()))
