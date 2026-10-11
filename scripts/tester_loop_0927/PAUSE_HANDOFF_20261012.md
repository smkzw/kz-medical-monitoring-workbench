# 无损暂停交接（2026-10-12 用户指令：立刻无损暂停）

## 暂停精确状态
- **被暂停的run**：dwfrun-91c93297-298b-44a7-870f-717606b9500d（监查质量循环·第35轮·单轮制，stop_reason=model无损可续）。
- **暂停点**：R35四测试位已交卷（**1/4通过——D位连续第5轮通过**）+分诊完成（新7条/P0P1×2、未决P0/P1累计16），**修复员在途被停**（约50分钟时被用户指令打断；其未提交的修复工作恢复时会重做）。恢复时修复员重派→回归门→复盘→轮末落盘照常走完。
- **台账基线**：STATE_V2.json=round34（registry138）；R35的7条新发现已分诊在册但round=35落盘未写——由恢复后的轮末落盘完成。
- **修复员手头清单首位**：R35-01 critical（字段识别停滞80+分钟不推进不失败、承诺的"采用已识别字段继续"降级入口永不出现）。

## 恢复方式（就一步，不重跑已沉淀工作）
让ZCode执行：**ResumeWorkflowRun(dwfrun-91c93297-298b-44a7-870f-717606b9500d)**
- 已沉淀171步零token回放；被中断的修复员ask会重新执行（其约50分钟未提交工作需重做——本次"立刻停"的已知代价，用户知情）。
- 不要用CreateWorkflow开新轮（会跳过R35的修复/复盘/落盘）。

## 暂停期间铁律（轮中暂停标准三件）
1. **8911/5178保持运行**（恢复时环境门探针为日志回放不重查；环境死=修复员/复测撞死站）。
2. 在途现场不清。
3. STATE_V2.json保持round34现状，由R35轮末落盘覆盖。

## 万一环境挂掉（恢复前救活再Resume）
```
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a; WORKBENCH_RUNTIME_DIR="$PWD/runs/tester_loop_iso_20260928/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &
cd frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &
```

## 关键背景
- 模型：GLM-5.3-Flash$max（用户拍板）；用户已全授权。
- zhipu已摘除；independent_ai=ollama活凭据（冷启动验证过）。
- 战役：单轮制R24~R34完成+R35大半；P0/P1走势15-21带内；主攻=字段映射确认死锁族+医学产出+误报族。
