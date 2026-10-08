# 无损暂停交接（2026-10-08 用户指令）

## 暂停时的状态
- **在跑**：第26轮（单轮制）run=dwfrun-4ea04740-794d-4831-8380-1a0ebfea1296，自2026-10-08约03:3xZ起跑，**用户已批准让其自然跑完**（本轮收官后不再开第27轮）。
- **战役进度**：老战役R1-R23已收官（总交付DELIVERY.md）；单轮制v2已跑R24、R25、R26（在途）。台账口径见 STATE.json 与 STATE_V2.json（见下）。
- **未决发现**：R25收官时97条（待复测61+待修复36），P0/P1=22（critical 4=R11-01/R22-01/R25-01/R25-06，其中R25-01/R25-06当轮已修复待复测）；R26的新增/关闭数以round_26/REPORT.md为准。
- **修复进度**：R24修6条（117657f6）、R25修4条含两条critical（f74c3946）+攻坚设计收口（6dff1c10）；全部过pytest回归门并已push。

## 两个状态文件（勿混淆）
- **STATE.json** = 人读台账（每轮复盘官更新，绝对路径写，历来可靠）。
- **STATE_V2.json** = 单轮制机器交接（每轮轮末脚本落盘）。R25曾因工作区根漂移落盘失败（已根治：绝对路径+字节数回显探针，5a22b00d）；**恢复前先核验**：`python3 -c "import json;d=json.load(open('STATE_V2.json'));print(d['round'],len(d['registry']),d['campaignDone'])"` 应为 round=26、条目≈R26收官数、campaignDone=false。若文件缺失或round≠26：直接删掉它即可——下一轮开局引导员会从STATE.json+round_26/REPORT.md权威重建（R24/R25两轮验证过此路径，且会诚实纠账）。坏文件备份=STATE_V2.stale_r25_handoff_broken.json。

## 恢复步骤（就一步，不重跑任何历史）
```
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台   # 必须在项目根！工作区根=提交时cwd
# 然后让ZCode执行：CreateWorkflow(path="implementation/workbench/scripts/tester_loop_0927/quality_round_v2.dwf.ts", name="监查质量循环·第27轮（单轮制）")
```
- 环境自动拉起：脚本开局门会探测8911/5178，down则自动重启（常驻项目运行时runs/tester_loop_iso_20260928完好保留，重启秒级就绪，零重复预置）。
- 每轮收官自动接续下一轮直至收敛（连续2轮清洁→自动总交付+全量清理）。收敛前恢复后循环继续。

## 暂停期间维护动作（R26收官通知到达时执行，本轮会话负责）
1. 核验STATE_V2.json落盘成功（round=26）；失败则按上文删旧重建策略记录。
2. 停隔离测试环境（只动8911/5178，写作舰队8910/5177不碰）：`lsof -ti:8911 | xargs kill; lsof -ti:5178 | xargs kill`，留痕ISO_ENV_LOG.md。
3. git递交round_26归档与暂停交接，push。
4. 向用户确认暂停完成。

## 环境与资产清单（暂停时全部保留）
- 常驻开考项目「MX循开考-CSU」（proj_user_6ef58ac151e1）+隔离运行时 runs/tester_loop_iso_20260928（~4.8G）
- 测试材料 tester_staging_0927（两处副本）；各轮报告round_01~26+台账+证据jsonl；DELIVERY.md（老战役总交付）
- 通道状态：外部通道2/3就绪（gpt-6-sol✓/gemini-3.8-flash✓/cursor-grok-4.6✗内部代打），每轮开局自动重探
