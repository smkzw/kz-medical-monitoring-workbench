# 无损暂停交接（2026-10-08 用户指令：工作流即刻无损暂停）

## 暂停精确状态
- **被暂停的run**：dwfrun-4ea04740-794d-4831-8380-1a0ebfea1296（监查质量循环·第26轮·单轮制），stop_reason=model（TaskStop无损暂停，可原样续跑）。
- **暂停点**：R26开局链全部完成（状态重建97条与台账完全对账/环境门/常驻项目第8次复验/攻坚第1次即绿），四测试位A/C/D已交卷，**B位（系统实施工程师视角）在途**——恢复时自动重派B位，随后分诊→复核→修复→复盘→轮末落盘照常走完。
- **战役进度**：老战役R1-R23已收官（DELIVERY.md）；单轮制R24/R25已完成归档；R26暂停于测试者阶段。

## 恢复方式（就一步，不重跑）
让ZCode执行：**ResumeWorkflowRun(dwfrun-4ea04740-794d-4831-8380-1a0ebfea1296)**
- 已沉淀的114步零token回放，B位重派后本轮自动走完并落盘STATE_V2(round=26)，之后按单轮制逐轮接续直至收敛。
- 不要用CreateWorkflow开新轮——那会跳过R26后半程。

## 暂停期间的铁律（三条）
1. **8911/5178必须保持运行**——这是轮中暂停：恢复时环境门探针是日志回放不会重查，环境若死，恢复后的B位会撞上一个死站点、整轮报废。两个进程留机器上不动（写作舰队8910/5177无关不碰）。
2. **B位的浏览器任务空间（ego TaskSpace）不清不删**——它是在途测试者的工作现场。此暂停**不适用**"停run后清后台"的常规纪律（那是终局清理，这是停机保牌）。
3. **STATE_V2.json保持现状（round=25/97条）**——它是本轮开局的重建基线，恢复后由R26轮末正常覆盖为round=26，无需人工动它。

## 万一环境在暂停期间意外挂掉（恢复前先救活）
```
# API（8911）：
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; WORKBENCH_RUNTIME_DIR="$PWD/runs/tester_loop_iso_20260928/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &
# vite（5178）：
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &
# 自检：http://127.0.0.1:8911/api/runtime-readiness 返回 ready:true 且 http://localhost:5178/monitoring 返回200，且 5178/runtime-build.json 的 expectedBackendBuildId 与8911的 backend_build_id 一致
```

## 台账与资产（暂停时全部保留）
- 人读台账STATE.json=round25/97未决/P0P1=22（critical 4=R11-01/R22-01/R25-01/R25-06，后两条修复已落地待复测）；机器交接STATE_V2.json=round25重建基线。
- 常驻项目「MX循开考-CSU」+隔离运行时tester_loop_iso_20260928（~4.8G）；测试材料双副本；round_01~26报告与证据；R26的A/C/D三份测试报告已在round_26/目录。
- 通道：外部2/3（gpt-6-sol✓/gemini-3.8-flash✓/cursor-grok-4.6✗内部代打）。
- R26开局引导员特别点名三件跟踪项（已在其strategyNote/台账）：B#1确认门永久禁用（critical）、D-F3无方案版本仍可运行（high）、R23-01写锁验收未闭合。
