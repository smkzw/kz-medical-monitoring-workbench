# Task Context: mw_m11_template_upgrade_20260717

Created: 2026-07-17 04:42:08
Objective: 为旧绿地医学写作工作副本建立显式M11模板升级预检、内容映射、用户确认和可回滚版本事务，保留原文、审批与审计历史，不做静默迁移
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`：当前全局路由、LOOP、记录和验证规则。
- `services/api/app/medical_writing_greenfield.py`：旧绿地基线、事件和决策事实源。
- `services/api/app/medical_writing_protocol_template.py`：当前中文M11模板ID、版本、哈希和160节点定义。
- `services/api/app/medical_writing_repository.py`与`sqlite_runtime_store.py`：工作副本、审批快照和审计事实源。
- `records/active_slices/medical_writing_authoring_journey_20260714/TASK_RECORD.md`：旧14节CRSwNP运行态、不得静默覆盖的既定边界。
- 只读核对的稳定数据：`runtime/medical_writing_greenfield.sqlite3`和`runtime/workbench_runtime.sqlite3`。用户已长期授权只读及备份后读写；本切片在review gate前不修改稳定数据。

## Scope

- In scope: 仅旧绿地文档；模板升级预检、确定性映射、未映射/合并/审批失效提示、显式确认、幂等和陈旧写拒绝、升级后新文档身份、立即回滚门、API、桌面交互、隔离双项目验证。
- Out of scope: 原始DOCX项目结构迁移、自动改写正文、AI决定映射、静默升级、删除旧工作副本/快照、在稳定项目上自动执行升级、改变当前M11模板结构或公司样式/语料定义。

## Success Criteria

- 旧14节CRSwNP与RA均可看到14→160节点预检；所有14个源章节都有明确目标或明确阻断，不丢内容块、表格或来源定位。
- 预检哈希绑定当前基线、目标模板和有效工作副本；任一变化后旧确认请求失败。
- 用户确认后生成新的document_id和160节点基线；旧工作副本、快照和事件不删除，内容复制到新基线且所有新章节为待医学审阅。
- 未保存的新升级文档可立即回滚到原document_id；升级后出现新工作副本时回滚默认阻断。
- 非绿地/已是当前模板/未知模板/未映射内容/陈旧修订/幂等键复用均fail closed。
- API、前端、DOCX草稿预览、重载、浏览器桌面QC和相关回归通过；稳定5174/8911持续可用且稳定数据未被测试修改。

## Risk Boundaries

- 不在稳定项目上自动执行模板升级；浏览器写操作只使用隔离复制或临时运行时。
- 不把旧审批状态或批准快照迁入新document_id；升级后的正文必须重新医学审阅。
- 不删除旧document_id关联的工作副本、快照、修订线程和审计；回滚恢复旧基线后应重新可见。
- 不使用AI推断章节映射；仅使用版本化、测试覆盖的确定性映射表，未知源章节阻断。
- Codex直接执行并负责最终验证；当前没有超过两个独立工作包，不创建Codex SubAgent或会商任务。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-17 04:42:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-17: 只读核对稳定绿地库：CRSwNP与RA均为无template_id的14节`greenfield_protocol_v0_1`；CRSwNP有1个revision=2工作副本和2个save快照，RA无工作副本。当前模板为`ich_m11_zh_cn_step4_cde_consultation_2026_06_12_v1`、160节点。
- 2026-07-17: 路由评估为Codex连续主线直接执行；不新建SubAgent。升级设计采用新document_id并将当前有效内容复制进新基线，旧运行态记录原样保留；立即回滚仅在新document_id尚无工作副本时允许。
