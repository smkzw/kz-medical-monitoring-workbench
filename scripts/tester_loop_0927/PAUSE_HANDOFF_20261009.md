# 无损暂停交接（2026-10-09 用户指令：完成当前细节点即停——轮中暂停）

## 暂停精确状态
- **被暂停的run**：dwfrun-9077e4cd-020e-4349-921a-04921a9e7f91（监查质量循环·第29轮·单轮制，stop_reason=model无损可续）。
- **暂停点**：R29四测试位已全部交卷（收卷已录：0/4、28条原始发现），**分诊官在途**——恢复时重派分诊，随后独立复核→修复→回归门→复盘→轮末落盘照常走完。
- **R29测试者战况**（收卷行）：A停于研究文件核对（核对作业滞留）；B/C均停于**上游AI限流**（glm-5.3-flash全部凭证冷却HTTP 429，作业45分钟无收敛，伴重试按钮空跑死锁）；**D位首次旅程全程走完无卡死**（唯一硬墙=事件明细标签确定性崩溃，已立发现并绕行完成）——里程碑。
- **台账基线**：STATE_V2.json=round28（registry 104/P0P1 20）；R29的28条原始发现尚未分诊立单（在测试者报告round_29/report_*.md里，恢复后由分诊官消化）。

## 恢复方式（就一步，不重跑）
让ZCode执行：**ResumeWorkflowRun(dwfrun-9077e4cd-020e-4349-921a-04921a9e7f91)**
- 已沉淀117步零token回放，分诊重派后本轮走完并落盘STATE_V2(round=29)，之后按单轮制逐轮接续。
- 不要用CreateWorkflow开新轮（会跳过R29后半程）。

## 暂停期间铁律（同上次轮中暂停）
1. **8911/5178保持运行**（恢复时环境门探针是日志回放不重查；环境死=分诊后修复员/复测撞死站）。
2. 在途成员的工作现场（浏览器TaskSpace等）不清不删——停机保牌非终局清理。
3. STATE_V2.json保持round28现状不动，由R29轮末正常覆盖。

## 万一环境意外挂掉（恢复前先救活，再Resume）
```
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; WORKBENCH_RUNTIME_DIR="$PWD/runs/tester_loop_iso_20260928/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &
cd frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &
# 自检：8911 ready:true + 5178 200 + 指纹配对
```

## 关键背景（恢复者须知）
- **zhipu-coding-plan已彻底摘除**（用户1009指令）：independent_ai→deepseek直连+档案硬禁用（a2605357）；台账0调用实证。产品AI通道=cms-router/ollama-cloud独立账，与编码计划无关。
- **R29的B/C位卡因=上游cms-router对glm-5.3-flash限流冷却**——恢复后首轮的攻坚/修复应关注该上游可用性（若仍429，考虑换绑主侧到ollama-cloud档案，属循环所有者决策范围外的通道调整需先问用户）。
- 模型配置：subagent_model=account:bigmodel-individual-coding-plan/GLM-5.3-Flash$max（用户拍板）；用户已全授权循环不再询问。

## 资产清单（全部保留）
常驻项目「MX循开考-CSU」+隔离运行时（含zhipu摘除后配置）；测试材料双副本；round_01~29报告（R29四份测试者报告在盘）；DELIVERY.md；通道外部2/3。
