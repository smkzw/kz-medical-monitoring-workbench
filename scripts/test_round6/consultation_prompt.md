# 医学监查子系统 测试轮6 会商审阅任务（独立会商角色）

你是独立会商审阅人。职责：对轮6三份测试报告进行**审阅、复盘、深挖根因、举一反三**，并审阅开发侧修复方向。只输出会商结论，不负责修复。

## 背景
- 被测系统：医学经理工作台·医学监查子系统（前端 http://localhost:5177/）
- 三份报告：/tmp/kz_test_round6/report_A_grok_CSU_F7.md（CSU·锁库前·F7回归+失败注入）、report_B_cursor_RUX_daily.md（RUX真实54表·日常·大文件+标记缺失）、report_C_glm_PSO_adversarial.md（PSO·锁库后CFDI·对抗样本+双项目交错）
- 修复账本：仓库 /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench，关键提交 3c40241（F7）/580e1c7（持久化）/08c7ccd（observed别名回放修复）/9ade37c（错误面+前端失败状态机+*NUM）/4038a0a（validation_blocked→needs_user_input内容确认流+medical_manager补VALIDATE_SOURCE_REVISION+诊断透传）
- 轮5会商结论（上一轮，供对照）：/tmp/kz_test_round5/consultation_verdict.md
- 开发自述最新进展：A项目经真实用户裁决+内容确认→**promoted历史首次达成**；此后select_document报mapping_document_selection_unusable（protocol=缺失时映射不可启动属预期）；validation_blocked已转needs_user_input内容确认流

## 你要回答的问题（逐条、引用证据）
1. **F7验收判定**：三份报告中文件角色确认UI（radio/标记缺失/提交/持久化/诊断码）的实测表现是否构成"F7闭环"？还有哪些缺口（如提交禁用逻辑、radio点击状态、裁决后推进、内容确认入口）？
2. **validation_blocked新死锁评估**：4038a0a的内容确认流（needs_user_input+content_confirmations+前端确认按钮）是否正确解法？医疗合规视角：内容mismatch由医学经理"确认沿用"是否应作为promote的合法前提？有没有更好的产品路径？
3. **反欺骗**：C报告的对抗样本（eCRF指南改名冒充方案）被系统接受为候选且无内容级警告。应如何在不阻塞正常流的前提下加入内容级反欺骗（模型已识别该文件为eCRF）？给出交互与后端方案。
4. **跨报告独立缺陷清单**：除文档核对主链外，三报告还有哪些独立P0/P1（如*NUM已修但中文列名、大文件进度、54表信息密度、映射不可改判、KPI全0误导等）？按"失败概率×下游瘫痪面"排序。
5. **下一轮测试设计**：三个互补切片（考虑：完整四件套文件集、EDC异构listing、双项目交错、分析层植入真相对照、刷新/重启恢复、增量第二批数据）。
6. **门控解耦产品决策建议**：仅凭listing先行"日常逻辑监查"（研究文档并行补齐）是否应放行？给出医学风险与产品价值权衡。

## 边界
- 只读：仓库代码、报告、sqlite只读查询；不改文件、不调模型API、不动运行中服务
- 输出：/tmp/kz_test_round6/consultation_verdict.md（中文，证据路径引用）
