"""E1回归：记录器形态演示探针退役 + 1000+条Finding工作列表负载。

钉住的行为与理由：
- B14（backend_probes.py）：原为记录器形态表达式探针——在探针文件内
  转录record_call旧`or`回退表达式并断言其缺陷，不触达实际实现。退役后
  必须由直接回归覆盖真实实现：本文件对真实record_call做0用量断言，
  并钉住探针文件不再含转录表达式。
- J14（timeline_probes.mjs）：同为记录器形态——转录Workspace.jsx的
  聚合展开/收起布尔表达式。退役后判定唯一实现移入真实纯模块
  medicalMonitoringJourneyTimeline.mjs::isAggregateExpanded（Workspace
  JSX实际调用它），本文件用node导入真实模块验证三种状态行为。
- 工作列表负载：合成正式Finding冻结DTO 1200条，走真实buildFindingCards
  （过滤+规范化，ProductLoop导出）与真实QueryWorkspaceView渲染
  （esbuild打包静态渲染），断言过滤只剔坏行、顺序稳定、锚点完整、
  耗时在显式预算内（不劣化天花板）。全部合成数据，0模型调用，
  布局验收不依赖真实SAR模型结果。
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
PROBES = WORKBENCH_ROOT / "review_pack_0926V1" / "kz_review_0926V1" / "probes"
TIMELINE_MODULE = (
    WORKBENCH_ROOT / "frontend" / "src" / "features" / "medical-monitoring"
    / "medicalMonitoringJourneyTimeline.mjs"
)


def _node() -> str:
    node = shutil.which("node")
    if not node:
        pytest.skip("node不可用：J14直接回归与负载测试需要node运行真实前端模块")
    return node


# ---------------------------------------------------------------------------
# B14退役：记录器表达式已移除，真实record_call由直接回归覆盖
# ---------------------------------------------------------------------------


def test_b14_recorder_expression_removed_from_probe_file() -> None:
    source = (PROBES / "backend_probes.py").read_text(encoding="utf-8")
    assert "'source_expression_probe'" not in source
    assert "or _int(usage,'reasoning_tokens')" not in source
    assert "B14已退役" in source  # 退役留痕指向直接回归


def test_b14_behavior_regression_on_real_record_call(tmp_path: Path) -> None:
    """直接回归（替代B14记录器）：真实record_call的0用量语义——
    嵌套detail里的明确0是真实观测值，不得经回退丢失为unknown。"""
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repo = MonitoringAiRepository(tmp_path / "b14-direct.sqlite3")
    repo.record_call(
        project_id="p1", job_id="job-zero", attempt_id="att", call_seq=0,
        owner="owner-a", provider="prov", requested_model="m",
        observed_model="m",
        diagnostics={
            "wire": "sse",
            "usage": {
                "detail": {
                    "reasoning_tokens": 0,
                    "cached_tokens": 0,
                    "total_tokens": 0,
                },
            },
        },
        outcome="success",
    )
    row = repo.call_ledger("p1", "job-zero")[0]
    assert row["reasoning_tokens"] == 0
    assert row["cached_tokens"] == 0
    assert row["usage_unknown"] == 0


# ---------------------------------------------------------------------------
# J14退役：判定唯一实现在真实纯模块，node直接导入验证
# ---------------------------------------------------------------------------


def test_j14_recorder_expression_removed_from_probe_file() -> None:
    source = (PROBES / "timeline_probes.mjs").read_text(encoding="utf-8")
    assert "expandedSet.has('g')" not in source
    assert "J14已退役" in source
    assert "isAggregateExpanded" in source  # 退役留痕指向真实模块函数


def test_j14_behavior_regression_on_real_module(tmp_path: Path) -> None:
    node = _node()
    script = (
        "import {pathToFileURL} from 'node:url';\n"
        "const m = await import(pathToFileURL("
        + json.dumps(str(TIMELINE_MODULE))
        + "));\n"
        "const expandedSet = new Set(['g-user-expanded']);\n"
        "const collapsedSet = new Set(['g-collapsed-selected']);\n"
        "const checks = {\n"
        "  selectedAutoExpand: m.isAggregateExpanded({"
        "expandedSet: new Set(), collapsedSet: new Set(), "
        "aggregateKey: 'g', containsSelected: true}),\n"
        "  collapsedWinsOverSelection: m.isAggregateExpanded({"
        "expandedSet: new Set(), collapsedSet: collapsedSet, "
        "aggregateKey: 'g-collapsed-selected', containsSelected: true}),\n"
        "  userExpandedPersists: m.isAggregateExpanded({"
        "expandedSet: expandedSet, collapsedSet: collapsedSet, "
        "aggregateKey: 'g-user-expanded', containsSelected: false}),\n"
        "  plainCollapsed: m.isAggregateExpanded({"
        "expandedSet: new Set(), collapsedSet: new Set(), "
        "aggregateKey: 'g', containsSelected: false}),\n"
        "};\n"
        "console.log(JSON.stringify(checks));\n"
    )
    script_path = tmp_path / "j14-direct-regression.mjs"
    script_path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(script_path)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    checks = json.loads(result.stdout)
    # 选中联动：选中事件在聚合内且未显式收起，自动展开
    assert checks["selectedAutoExpand"] is True
    # W05-J2/J14：显式收起优先于选中联动（收起后选中不再强制展开）
    assert checks["collapsedWinsOverSelection"] is False
    # 用户显式展开：无选中联动也保持展开
    assert checks["userExpandedPersists"] is True
    assert checks["plainCollapsed"] is False


def test_workspace_uses_the_real_module_function() -> None:
    """退役后判定唯一实现：JSX内联布尔不得回归（移入纯模块后应调用它）。"""
    workspace = (
        WORKBENCH_ROOT / "frontend" / "src" / "features" / "medical-monitoring"
        / "MedicalMonitoringWorkspace.jsx"
    )
    source = workspace.read_text(encoding="utf-8")
    assert "isAggregateExpanded({" in source
    assert "|| (containsSelected && !collapsedAggregates.has(" not in source


# ---------------------------------------------------------------------------
# 既有探针套件仍可执行且不再含记录器探针
# ---------------------------------------------------------------------------


def test_probe_suites_run_without_recorder_probes() -> None:
    node = _node()
    backend = subprocess.run(
        ["python3", str(PROBES / "backend_probes.py")],
        capture_output=True, text=True, timeout=60, cwd=PROBES,
    )
    assert backend.returncode == 0, backend.stderr
    backend_ids = {
        item["id"] for item in json.loads(backend.stdout)["results"]
    }
    assert "B14" not in backend_ids
    assert {"B01", "B12", "B13"} <= backend_ids

    timeline = subprocess.run(
        [node, str(PROBES / "timeline_probes.mjs")],
        capture_output=True, text=True, timeout=60, cwd=PROBES,
    )
    assert timeline.returncode == 0, timeline.stderr
    timeline_ids = {
        item["id"] for item in json.loads(timeline.stdout)["results"]
    }
    assert "J14" not in timeline_ids
    assert {"J01", "J13"} <= timeline_ids


# ---------------------------------------------------------------------------
# 1000+条Finding工作列表负载（真实投影/渲染，合成DTO，预算天花板）
# ---------------------------------------------------------------------------


def test_finding_worklist_load_1000_plus(tmp_path: Path) -> None:
    node = _node()
    esbuild = WORKBENCH_ROOT / "frontend" / "node_modules" / ".bin" / "esbuild"
    if not esbuild.exists():
        pytest.skip("esbuild不可用：负载渲染测试需要frontend依赖安装")
    result = subprocess.run(
        [node, "medicalMonitoringFindingWorklistLoad.test.mjs"],
        capture_output=True, text=True, timeout=120,
        cwd=WORKBENCH_ROOT / "frontend" / "src" / "features" / "medical-monitoring",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "findings=1200" in result.stdout
