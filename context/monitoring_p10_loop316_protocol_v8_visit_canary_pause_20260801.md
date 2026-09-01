# P10 LOOP 3.16 RUX v8 单主题 Canary 无损暂停

日期：2026-08-01
状态：canary FAIL CLOSED；本细分项已完成；主 Goal 未完成

## 当前门结论

- v8 运行安全门通过，功能/科学验收门 **FAIL CLOSED**。
- 唯一 v8 job、唯一 attempt、initial + 一次 controlled repair、零候选持久化、
  完整终态失败关闭均符合安全合同。
- repaired response 未满足可执行 v8 合同；不得 retry/reuse/salvage，不得对任何
  原始候选作接受、拒绝、采用、确认或激活决定。
- RUX 当前协议门仍为 NO-GO；MY009、其他 topic 与其他真实项目继续阻断。
- 8911 必须保持停止；5174 必须保持停止。

## 唯一 Canary 证据

- Job：`monai_06e9dd4e1b18677ff748ed792445`
- Attempt：`monattempt_e635a4f195ae4784b825a9be12399e8b`
- Prompt：`monitoring-protocol-clause-structuring-v8`
- Source revision：`mpr_40b82826a43e46342344841242e6`
- Terminal：`failed / invalid_ai_output`
- Provider outputs：initial + 一次 repair
- Persisted candidates：0
- Request SHA-256：
  `87bfc229bf678d11dfd8fc330f2609c9998be7c6dae596228a4c92ab6f3a9488`
- Response SHA-256：
  `aba303673d7585e9aa620b44cb70b8129e080f94bc50fd9f6f8eeed01a40e234`
- 详细摘录：
  `runs/monitoring_p10_loop316_protocol_v8_visit_canary_terminal_evidence_20260801.md`

## 失败性质

- 候选 1/2 的核心是 schedule-only，但 provider 在候选正文用
  `不包含改期/补访、计划外访视` 作为负向范围声明；可执行 family view 仍把这些
  topic 名称计为 reschedule/unscheduled。
- 候选 3 的核心是单一改期条件—动作链；`计划访视无法在窗口内完成时` 是后置触发，
  当前 classifier 误计独立 schedule family。同时 provider 在 uncertainty 与
  user guidance 中保留分发/回收及失访/退出词汇，真实违反 full-boundary 合同。
- 候选 4 的核心是 unscheduled-only，但正文以
  `不结构化安全性随访` 重复被排除 topic，触发 safety-follow-up boundary。
- 候选 5 单独 deterministic-valid，但全响应原子性正确阻止从无效响应中单独捞取。
- Repair 未关闭既有错误，还给候选 1/2 新增 `计划外访视` 词法命中；系统正确没有
  第三次 repair。

## 独立审阅

- 复用既有 Luna reviewer `/root/rux_protocol_v4_audit`，未新建 reviewer，
  未 fallback。
- Reviewer 结论：**FAIL CLOSED**。
- Reviewer 明确反对：
  - 从 full boundary 移除 uncertainty/user guidance；
  - 广义否定句豁免；
  - global reschedule precedence。
- 安全的未来方向仅限：
  - provider-visible 合同禁止在任何用户可见字段重复被排除 topic/family 名称，
    包括负向免责声明、uncertainty 与 user guidance；
  - 单独、窄范围修正后置改期触发语义角色；
  - 保留 medication、dispensing/PK、withdrawal、safety、collection、
    full-boundary 和 exactly-one-family 全部严格门。

## 备份与回归

- Pre-canary 21 库备份：
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v8_visit_canary_20260801_0859CST/`
- 21 个主库齐全；18 个非空库 immutable integrity OK，3 个空库保持 0 字节。
- Backup `medical_monitoring_ai.sqlite3` SHA-256：
  `db8d057d054b972b227c2fe281e31388effed2cbf6cacbe85d1a8bcbb5a0d350`
- 聚焦监查：`376 passed in 13.46s`
- 医学写作相邻五文件：`200 passed in 3.14s`
- 标准全监查命令在 collection 阶段被并行医学写作变更阻断：
  `medical_writing_protocol_template.py` 已删除私有
  `_REQUIRED_CORE_BODY_SEMANTIC_IDS`，既有
  `test_medical_writing_dynamic_section_matrix.py` 仍导入它。
- 本任务没有修改、回退或接管上述医学写作文件。
- 仅排除该单个无关 collection blocker 后，全监查：
  `1371 passed, 4283 deselected, 27 warnings in 731.00s`。
- 因此可以确认 monitoring selection 未回归，但不能声称标准仓库选择器全绿。

## 冻结运行状态

- v4：8 jobs / 8 attempts / 8 candidates
- v5：1 / 1 / 0
- v6：1 / 1 / 0
- v7：1 / 1 / 0
- v8：1 / 1 / 0
- v4-v7 未 retry/reuse；v8 未 retry。
- 8911：0 listener；暂停期间必须保持停止。
- 5174：0 listener；暂停期间必须保持停止。
- 无本任务 pytest、canary observer、monitoring worker 或 reviewer 留在运行中。
- 五个受控 v8 产品/测试文件未被本 canary 修改。

## 下一安全动作

仅在用户下一次明确继续本 Goal 后：

1. 重读最新全局/项目 AGENTS、本暂停记录、v8 review 与 LOOP ledger。
2. 先只读核查并行医学写作私有符号漂移是否仍存在；不得擅自修改或回退其文件。
3. 复核 8911/5174 为 0 listener、v4-v8 计数不漂移、受控文件 hash 不变、
   无遗留 runner/worker/test。
4. 初始化独立离线新切片；若 provider-visible wording 改变，必须使用 fresh prompt
   identity（不得复用 v8）。
5. 纠偏只覆盖两类已证实问题：
   - 所有用户可见字段不得重复被排除 topic/family 名称；
   - 后置 reschedule trigger 的窄范围语义角色。
6. 建立正负矩阵，证明真实禁止条款、真实 mixed-family、独立 schedule obligation
   继续失败关闭；不得弱化 full-boundary 或 exactly-one-family。
7. 完成聚焦、全监查、医学写作相邻回归和 Luna 独立只读 review 后，才允许讨论一次
   fresh single-topic canary；不得直接进入 MY009。

本细分项已无损暂停。8911 必须保持停止。
