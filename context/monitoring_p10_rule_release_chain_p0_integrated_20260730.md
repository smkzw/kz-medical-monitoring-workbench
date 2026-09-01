# 医学监查 P0 规则发布链整合上下文

## 1. 本切片目标

在共享主工作区完成并验证以下最小完整产品链：

已采用规则建议 -> 已确认规则 -> 规则包草稿 -> 冻结真实批次自动影子样本与 provisional inspection -> 医学经理确认冻结样本及实际判断 -> 显式发布 -> daily-run readiness。

本切片只处理医学监查，不修改医学写作业务逻辑，不启动 8911，不写真实运行数据库。

## 2. 不可变业务边界

- 采用推荐规则本身就是医学决定，不再出现第二次“医学批准”。
- 自动影子样本的首次运行只形成 provisional inspection evidence。规则自身实际输出不能复制为可信期望并自证通过。
- 医学经理通过 `sample_set_id` 确认冻结样本及其实际判断后，系统才可把该确认转为可复用回归期望。
- 影子确认与正式发布是目的不同的两个显式动作。
- 未确认 provisional inspection、未发布规则包、身份不完整、身份漂移或独立 AI 不可用时，发布与 daily run 均失败关闭。
- 前端不得要求用户填写 row fingerprint、content hash、case id、capability manifest 等工程字段。
- CM 仅表示非试验用药。试验药物给药、剂量调整、暂停、恢复、停药、发放、回收和依从性继续使用独立数据域。

## 3. 后端纠偏完成项

### 3.1 Provisional shadow 不自证

- 自动样本和首次运行只返回实际命中、实际未命中、不可判定、诊断码、来源与覆盖情况。
- 未确认阶段不生成可信 gold/diagnostic case，不生成可信 confirmation，不返回 `shadow_passed`。
- `confirm-shadow` 使用冻结的 `sample_set_id`，先在内存构建期望案例并进行零持久化预验证；验证失败时不写可信证据。
- 确认成功后再原子写入由本次医学确认形成的 gold/diagnostic cases，并运行可信回归。
- 既有独立预注册 gold/diagnostic 证据路径保持不变。

### 3.2 Record applicability 聚合身份

- 逐记录适用模式对所有纳入规则包形成可冻结、可审计的 aggregate assignment identity。
- 每条已发布规则都必须具有 mapping revision、mapping content、capability manifest、effective capabilities 的完整身份。
- prepare/readiness 锁定该聚合身份。
- execute 前重新解析；分配、规则包或任一身份变化均拒绝执行，禁止静默使用 prepare 后的新分配。
- legacy、混合身份和缺失身份均失败关闭。

### 3.3 Batch 精确复用

- `_existing_run` 只允许复用同项目、同批次、同冻结身份的运行。
- 删除无同批次运行时回退到其他批次最近运行的逻辑。

### 3.4 Fresh-load 证据连续性

- 新增规则包生命周期祖先查询和只读 `shadow-lineage-evidence` 投影。
- confirmed/published 规则包重新打开后，可沿不可变谱系取回原 shadow 阶段样本集和确认记录。
- 跨项目、断链、环路或缺失谱系均失败关闭。

## 4. 前端产品链

- 批次管理头部新增“规则发布”入口。
- 右侧桌面抽屉按五步显示：组建规则包、自动影子检查、确认影子样本、发布规则包、日常监查就绪。
- 无规则包时直接提示进入“准备方案规则”，不要求工程配置。
- 自动影子阶段只选择冻结真实批次；样本由服务端准备。
- 样本表只显示规则、样本、实际判断、诊断码和来源依据。
- 确认文案明确：确认的是冻结样本及实际判断，不是再次批准规则。
- 确认后才显示发布动作；发布后显示 readiness 与唯一下一动作。
- 项目切换强制重建状态并取消迟到请求，避免跨项目串态。
- fresh-load 通过谱系端点恢复已确认样本与确认信息，不依赖 React 内存。

## 5. 共享工作区并行边界

- `frontend/src/App.jsx` 未由本切片修改，最终 SHA-256：
  `a94e7bd795d236c7166c13b0e12fee90094975660feb0dc2594dbc0f6b1d7af1`
- `frontend/src/styles.css` 未由本切片修改；当前 SHA-256：
  `458de7c071d60e1967db0fdf300bc7eff179126a15c69d6f84b6697c3abdda09`
  与前端切片起点不同的变化属于并行医学写作会话。
- `services/api/app/main.py` 只增加医学监查 runtime identity 的
  `effective_capabilities_sha256` 装配；最终 SHA-256：
  `e9c930e756c6f42c237d6c45cc923d5bdd94069b318147cf66cdaaa38bd91e9c`
- 禁止修改的 `monitoring_ai_router.py` 与 `tests/test_monitoring_ai_api.py` 未修改。

## 6. 验证结论

- 全量医学监查后端：`1080 passed, 4251 deselected, 0 failed`。
- Codex 独立聚焦复核：`88 passed`。
- 医学监查前端：12/12 测试文件通过。
- 相邻医学写作与写作参考前端：6/6 测试通过。
- Vite 生产构建：1914 modules，成功。
- 主应用导入成功；`shadow-lineage-evidence` 路由已注册；不存在用户可注入 gold/diagnostic cases 的端点。
- 真实桌面运行态确认“规则发布”入口可达，抽屉五步布局清晰，无工程字段，无 provisional 可信措辞，浏览器 console 无 error/warn。
- 8911 始终无监听；真实 runtime SQLite mtime 均早于本切片。

## 7. 验收证据

- 执行报告：
  - `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_01_corrective_p0.md`
  - `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_02.md`
  - `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_03.md`
- 全量监查日志：
  - `logs/runtime/worker03_final_monitoring_regression_20260730.log`
- 视觉证据：
  - `records/visual_qc/monitoring_rule_release_p0_20260730/rule_release_drawer_20260730.png`
- Codex 复核：
  - `reviews/codex_monitoring_p10_rule_release_chain_p0_20260730_review.md`
- 指标：
  - `metrics/monitoring_p10_rule_release_chain_p0_20260730_metrics.md`

## 8. 已知残余风险

- 按硬边界未启动 8911，因此没有在真实运行数据库上点击执行写链。后端完整链由隔离 TestClient/service 仓储验证，前端由真实 Vite 页面与 mock/契约测试验证。
- 首次发布仍受既有“至少两个权威项目”覆盖门约束；本切片未修改该医学治理规则。
- 推荐链 AE 夹具与影子链 EX 夹具尚不是同一个单对象真实数据夹具；整链按真实合同分段验证。后续真实项目验收应补一套映射、推荐、冻结批次和影子样本完全同源的只读副本。
- 医学写作后端回归中的 4 个失败来自并行写作会话的 schema/措辞/幂等断言变化，与本切片文件无交集；医学监查不得越界修复。
