# P10 LOOP 3.16 协议 v9 可见范围/后置触发离线纠偏无损暂停

日期：2026-08-01
状态：offline PASS；本细分项已完成并无损暂停；主 Goal 未完成

## 当前门结论

- v9 离线纠偏通过 Codex 聚焦、全监查相邻回归和 Luna 独立只读审查。
- 该结论只允许无损暂停，不代表 provider、启动恢复、runtime、canary、RUX
  协议门、MY009、发布或候选决定通过。
- v4-v8 终态 job 不得 retry/reuse/salvage；不得接受、拒绝、采用、确认或激活
  任何候选。
- 8911 和 5174 必须保持停止。

## 已完成纠偏

1. Fresh identity 为
   `monitoring-protocol-clause-structuring-v9`；v8 加入 terminal legacy。
2. Initial 与单次 repair 合同均禁止在所有用户可见字段中，为说明排除/省略/
   不结构化而重复被排除 topic/family 名称；repair 必须删除违规措辞，不得新建
   负向范围免责声明。
3. `计划访视无法在窗口内完成时的改期/补访安排` 及
   `…完成时必须改期/应重新安排` 归为 reschedule-only。
4. 情态词只有位于 schedule predicate 之前时才证明独立义务；week/day、顺序、
   量词、数值窗口定义、独立 `仍需完成` 及真实 mixed-family 继续 fail-closed。
5. Full boundary 继续覆盖 uncertainty/user action；medication、
   dispensing/PK、withdrawal、safety、collection、exactly-one-family、
   candidate-indexed 全错误、一次 repair、全响应原子性均未弱化。

## 路由与复核

- Pi/deepseek/deepseek-v4-flash/max session：
  `019fbaf4-a806-7000-95e6-a3e88e33e3e3`。
- Initial pass 后 Codex 复现一个 modal-role 缺口；仅做一次 consolidated
  same-session follow-up，无 fallback、无重复 dispatch。
- 复用 Luna reviewer `/root/rux_protocol_v4_audit`，未新建 reviewer，
  未 fallback。
- Luna 结论：无 P0/P1；一个 P2 覆盖缺口不阻断离线暂停。

## 验证

- 两项实现模块编译通过。
- 三份受控测试：`403 passed in 11.26s`。
- Codex withheld 六例语义角色矩阵：6/6。
- 标准 `pytest -q tests -k monitoring` 仍在 collection 阶段被并行医学写作
  私有符号漂移阻断：
  `test_medical_writing_dynamic_section_matrix.py` 导入已移除的
  `_REQUIRED_CORE_BODY_SEMANTIC_IDS`。
- 仅排除该单个无关收集文件后：
  `1398 passed, 4285 deselected, 27 warnings in 639.65s`。
- 医学写作相邻五份契约：`200 passed in 2.48s`。
- 本切片未修改、回退或接管医学写作实现/测试。

## 最终受控文件哈希

- `services/api/app/monitoring_ai_service.py`:
  `4d97114e1bb9a4530954bdd0282abb106cc4dc08b07c40dc3c87eafeaf1f24ee`
- `services/api/app/monitoring_protocol_preparation_service.py`:
  `08207529f0a17156c55843e2003d2c2746c9721154312dacd5783b0a7e2081ef`
- `tests/test_monitoring_ai_service.py`:
  `a907883c17a6bb61b96a83bb4a22277bcc155b962cd19dbb79c3758915a57ed3`
- `tests/test_monitoring_protocol_preparation.py`:
  `dd26a2ff10089d06f3053843fd135cb970160a26d19f69ef9a35b056877aa6f6`
- `tests/test_monitoring_ai_api.py`:
  `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`

## 冻结运行边界

- 本切片没有启动服务、调用产品/provider API、读取或写入 runtime DB，也没有
  运行 RUX/MY009/其他真实项目。
- 上一冻结锚点的计数仍是：
  - v4：8 jobs / 8 attempts / 8 candidates
  - v5：1 / 1 / 0
  - v6：1 / 1 / 0
  - v7：1 / 1 / 0
  - v8：1 / 1 / 0
  - v9：0 / 0 / 0
- 本切片未写 runtime，因此未产生计数变化；暂停终检确认 8911/5174 无 listener，
  无本任务 runner/pytest/worker 留存。
- 另有无关工作区进程监听 18911；不是 8911，本任务未触碰。

## 保留的 P2 与下一安全动作

Luna 指出直接测试尚未同时证明：

1. completed 与 failed v8 历史可见；
2. same-revision queued v8 不可 reuse/claim；
3. `RUNNING` v8 不可选择并能正确退休；
4. fresh v9 创建/选择与上述旧状态隔离。

仅在用户下一次明确继续主 Goal 后：

1. 重读最新全局/项目 AGENTS、本暂停记录、v9 review、Luna 输出与 LOOP ledger。
2. 先只读核查并行医学写作私有符号漂移；不得擅自修复或回退。
3. 核对五个受控哈希、8911/5174 为 0 listener、无遗留任务；只读核对
   v4-v9 runtime 计数及旧 active job eligibility。
4. 在任何 canary 前，先离线补齐上述四项 v8→v9 cutover 直接测试并运行聚焦/
   全监查/相邻回归；必要时复用同一 Luna 会话做 delta review。
5. 只有该 P2 关闭且 runtime preflight 通过后，才可讨论一次 fresh v9
   `visit_window_and_order` canary；不得直接启动服务、其他 topic、MY009 或
   三个真实项目。

详细 review：
`reviews/codex_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_review.md`

独立审查：
`runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna.md`

本细分项已无损暂停。8911 必须保持停止。
