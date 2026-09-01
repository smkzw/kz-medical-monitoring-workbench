# Codex Conference Review: medical_writing_sites_feasibility_20260714

Date: 2026-07-14

## Verdict

`PASS WITH DECLARED FALLBACK AND CODEX CORRECTIONS`。两名参与者完成同会话三轮并与本地Sites合同审计一致；DeepSeek后两轮发生buddy代理数据库字段截断；GLM主持未建立可续会的三轮会话，因此按用户既定fallback由OpenCode Go `qwen3.7-plus`完成同会话三轮替补主持。现有证据足以收口，不为获取形式上的全员成功而重复消耗同题会商。

## Routing And Failure Record

- MiniMax-M3：完成三轮，支持“可演示/可试点/可生产/可合规”四层边界；部分最终文件只保留末段，Codex结合逐轮stdout核验。
- deepseek-v4-pro：首轮完成；第2/3轮在3次受控重试后返回HTTP 502及MySQL `text`字段截断，按规则记为终端基础设施失败，不把缺失输出解释为模型意见。
- MiMo-v2.5：完成三轮，明确撤回未验证的远程访问替代方案，最终支持本地/内网主线与条件式混合部署研究。
- GLM-5.2 chair：首轮产生了实质分析，但runner记录`no usable Hermes session was established`，未满足同会话三轮主持门禁。
- Qwen3.7 Plus fallback chair：在声明替补后完成同会话三轮，复核参与者分歧、失败证据和本地Sites合同，给出可执行终裁。

## Accepted Findings

1. 当前Vite前端可以适配Sites构建，但Python FastAPI、SQLite、本地文件系统、本地OCR/文档处理和私有AI网关不能原样迁移到Worker兼容ESM运行时。
2. Sites当前适合独立Gap决策页、无真实临床数据演示、合成/经批准脱敏数据的前端试点；“能部署页面”不等于“能承载生产医学写作”。
3. 医学写作P0继续走本地单机和未来公司内网/个人私有化主线。Sites不得进入P0生产后端重写，也不得形成第二套业务逻辑。
4. “Sites前端 + 私有后端”只能作为后续条件式试点，前提是公司供应商治理、身份/RBAC、审计、数据驻留、网络可达性和长任务拓扑逐项通过。
5. 全Worker/D1/R2迁移是远期架构研究，不是当前实施任务。

## Codex Corrections

- 不采纳“演示页面必须隐藏ICH M11公开章节名”等过度脱敏建议；公开标准结构本身不是公司机密。演示边界按真实临床数据、未公开项目设计、项目语料和内部实现细节分级治理。
- 不把Sites private deployment解释为公司合规结论；平台访问策略不能替代供应商准入、公司SSO、项目级权限或临床审计。
- 不把决策工具部署到Sites作为当前交付条件。本轮用户仅要求调研可行性，未授权创建或发布站点。

## Independent Verification

- 读取本地`sites-building`、`sites-hosting`、持久化与身份合同。
- 核对当前项目无`.openai/hosting.json`，后端为FastAPI/SQLite，本地文档与AI/OCR链路依赖明确。
- 核对当前会话可调用Sites建站、版本、私有/共享部署、访问策略、环境变量和自定义域工具，但没有执行创建或部署。
- 形成独立可行性文档`records/active_slices/medical_writing_full_gap_review_20260714/SITES_DEPLOYMENT_FEASIBILITY.md`。

## Final Decision

会商通过并关闭。Sites作为独立演示/评审发布候选保留；医学写作生产架构不迁移，待公司治理和网络身份条件成熟后再评估混合方案。
