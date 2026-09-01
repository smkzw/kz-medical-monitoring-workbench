# Conference Participant Output: mm_r7_slice08d_contract_20260830 - general_single_object

## Boundary Check

- 只读取并引用：`reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`、`reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`、`context/medical_monitoring_r7_slice08a_continuity_acceptance_record_20260829.md`、`context/medical_monitoring_r7_slice08b_authority_artifact_bridge_acceptance_record_20260829.md`、`context/medical_monitoring_r7_slice08c4_visual_acceptance_record_20260830.md`、`context/medical_monitoring_r7_phase_review_after_slice08c4_and_slice08d_plan_20260830.md`。
- 只读取代码（不修改、不调用）：`poc/medical_monitoring_ai_native_r7/src/mm_r7/{continuity.py,continuity_bridge.py,launch_registry.py,run_setup.py}`、`tests/test_medical_monitoring_r7_product_router.py` 第 498–562 行摘录，以及 `test_determinism_adjacent.py` 的 9-cell 探针骨架。
- 未启动 8911/5174、未读取真实 listing、未调用真实模型、未打开任何前端、未修改任何源码、未启动 pytest。
- 报告内容不含医学写作或临床结论；不声称 08D / Slice-08 / R7 / R8 接受；Codex 保留最终视觉、临床、监管与生产写入权。
- runner 路径 `runs/conference/mm_r7_slice08d_contract_20260830/general_single_object.md` 未由本会话创建。

## Independent Work Product

### 1. 总体判断

v0.1 合同方向正确、骨架完整，已经把 v0.2 §9–§14 的硬性语义压缩成 10 段、4 类场景矩阵、5 类对账维度、6 类确定性与恢复、5 级 P 门和最小实施形态。它可以**作为冻结起点**；但若不修以下缺陷就接受，会把 08A/08B/08C 的少量语义裂缝直接装进 Slice-08 总体复盘。结论：`ACCEPT_WITH_REQUIRED_REVISIONS_v0_2`。Codex 可决定是合并到一份 v0.2 还是另开 v0.2。

### 2. 最高风险缺陷（必须修，否则冻结后会出现跨轮漂移）

#### R1. 缺"矩阵单元格编号"和"对账维度→场景"的覆盖闭包证明

v0.1 §4 只列了 4 个场景 × 5 类必测条件，但 5 类（正常、边界、缺失/不兼容、同值重放、冲突/篡改）× 4 个场景 = 20 个矩阵格。v0.1 没有给每个格最小可执行断言指针，也没有声明矩阵闭包的"网格识别"。这意味着 08D 实施可以"通过 4 个 happy-path 测试 + 散点异常测试"就声明完成——这是 v0.1 最大的可被攻击面。  
**修法建议**：v0.2 §4 加 1 张矩阵，每格写明 (a) 涉及 `continuity.py`/`continuity_bridge.py`/`launch_registry.py`/`run_setup.py` 中哪些函数，(b) 期望的失败码（如 `invalid_baseline_digest`、`continuity_plan_cas_conflict`），(c) 至少一条 fixture-free 断言。最小覆盖示例：`daily_full/diff_ok`、`daily_full/missing_high_severity`、`daily_full/tampered_baseline_digest`、`daily_incr/recommended_baseline`、`daily_incr/user_repick_compat`、`daily_incr/cross_project_baseline`、`daily_incr/drift_run_id`、`pre_lock_full/query_driven_complete`、`pre_lock_full/query_driven_incomplete`、`pre_lock_full/data_revision`、`pre_lock_full/multi_publish_history`、`post_lock/identical_replay`、`post_lock/snapshot_change_creates_new`、`post_lock/rule_change_creates_new`、`post_lock/decision_change_creates_new`、`post_lock/center_change_creates_new`、`post_lock/late_callback_no_overwrite` 等 20 格。

#### R2. §5 oracle 独立性条款不具可执行性

v0.1 §5 写"测试 oracle 必须从输入事实重新计算，不能读取产品输出后再生成 expected"。这是反过度拟合的正确要求，但缺少**判别准则**。当前 R7 测试体里至少 3 类潜在泄漏：
- `test_continuity_bridge.py` 多处直接以 `payload["effective_profile_digest"]` 等产品输出生成期望（参见已读代码中 `_make_daily_outputs` 走 `mo.build_daily_mode_outputs`，再用同一管道产出 commit 后再断言）。这种"以产品函数做参考 oracle"在 contract §5 语义下处于灰区。
- `test_launch_registry.py` 在 08B 接受记录中已声明"调用方提供的已验证布尔值不是权威"，但 v0.1 没禁止测试用 `verified=True`、`artifact_verified=True` 等布尔直接驱动期望。
- 现有 `_repro_probe` 是把产品输出字节直接重做比对，但没有声明"若产品输出因 hash seed 改变而被篡改，测试也会盲跟"。

**修法建议**：v0.2 §5 新增三条可执行条款：(a) oracle 输入必须限定为 `R5AuthorityPacket`/`R6ModeOutput`/当前 `CarryForwardPlan` 输入字段与固定 hash 域；不得引用 `payload["..."]` 这类从产品函数返回中再取的字段。(b) `verified/...` 标志必须通过 `verify_carry_forward_item()` 真实跑出，不得在测试里直接置位。(c) fixture 名、case id、mutation class、case 描述符不得出现在 oracle 计算路径或结果比对的字符串匹配中（除命名测试函数本身）。

#### R3. §6.1 "随机固定值"是不可执行规范

v0.1 §6.1 写"`PYTHONHASHSEED=0/1/42/随机固定值` 两次独立进程输出字节一致"。"随机固定值"是矛盾的——随机与固定不兼容。当下 `test_determinism_adjacent.py` 已用 `0/1/42` 三 seed × 3 优化级别构成 9 格（参见已读 `test_effective_and_binding_digest_deterministic_matrix`），但合同没把这套已工作的探针**固化**为 08D 的执行骨架。  
**修法建议**：v0.2 §6.1 改写为"`PYTHONHASHSEED` 取固定集合 {0, 1, 42, 17, 31415926} × 优化级别 ∈ {(), -O, -OO} = 15 格，每格以 `subprocess.run([sys.executable, ...])` 在独立进程跑同一 fixture 并对公开 JSON、digest、错误码做 SHA-256 比对"；明确把 `test_determinism_adjacent.py::test_effective_and_binding_digest_deterministic_matrix` 列为 08D 必须保持通过的内置探针。

#### R4. §5 "9 项结构化计数与五项首屏摘要同源"是 08C 范畴，不是 08D

这条**逻辑上不属于"综合回归"**：09:11:5 是 08C-4 ego(lite) 视觉验收记录的产物，由 08C-4 视觉接受记录 `FINDINGS_revised.json` 保证（参见已读 08C-4 接受记录 §"决定性证据"）。若 08D 重复跑 09:11 同源校验，会和 08C-4 的 R10 视觉复核**双轨**——一旦两边算法口径不同就出现治理冲突。  
**修法建议**：v0.2 §5 把 09:11 同源条目明确标注为"复用 08C-4 视觉接受记录中 R10 `centerFoldClear=true` 与结构化 `FINDINGS_revised.json` 的回归断言，本合同不重新实现其算法"；08D 只做"重启 08C-4 synthetic fixture + ego(lite) 截图 + 结构化断言三者同时通过且 mtime 未变"的回放测试。

#### R5. §3.2 / §3.3 / §3.6 三条用户可见条款缺少反向断言

- §3.2 "锁库前只允许 full"——已读 `test_medical_monitoring_r7_product_router.py::test_replay_and_conflict_and_three_modes_and_basis_rules` 第 502–509 行确有 daily/pre_lock/post_lock 三模式回路，但合同没要求 08D 显式断言 `incremental + pre_lock`、`incremental + post_lock_pre_cfdi` 的拒绝路径。
- §3.3 "核查前强制 full+fixed_total=true"——已读 `run_setup.py:244` 有 `fixed_total: bool = False`，但合同没要求 08D 显式断言 `post_lock_pre_cfdi + execution_basis=incremental` 必须返回 4xx 且中文错误稳定。
- §3.6 "公开响应不得暴露内部术语"——v0.1 §15 闭集（已读 v0.2 §15）明确禁止 `run_id/run_ref/digest/CAS/artifact/provider/model/sqlite/S4/R5/R6/R7`，但 v0.1 没指定用哪一份 fixture 跑全闭集扫描，也没指定术语是否需要按"完整词"或"词形含子串"判别（`R5` 是否匹配 `R5X`？`run` 是否匹配 `runtime`？）。

**修法建议**：v0.2 §3 加反向断言清单：(a) 列出 `daily+full/incremental` `pre_lock+full/incremental` `post_lock+full/incremental`、`post_lock+incremental` 6 条 matrix + 期望 4xx 码 + 中文错；(b) §3.6 闭集扫描声明"按 `re.escape(token)` 做 `\b` 词边界匹配，例外词表 `runtime|runner|model_review` 等必须列入并单独经会商批准"；(c) §3.6 必须保留的合法医学文本（如"模型拟合"、"运行 12 周"、"基础研究"等）通过 schema 字段白名单而非正文 scrubber。

### 3. 中风险缺陷（建议修，但不会导致硬阻塞）

#### M1. §4 矩阵和 v0.2 §16"扩展验证矩阵"存在轻微重叠但映射不全

v0.2 §16 已列出 10 项扩展验证（已读 §16.1–10），与 v0.1 §4/§5/§6/§7 各条对账但不完全对齐。例：v0.2 §16.7 强调"日常多基线推荐与用户改选、未确认规则阻断、锁库前归因、固定总量重放/新运行"——这与 §4 矩阵第四列 `post_lock fixed-total` 部分重叠，但 v0.1 §4 没把"未确认规则阻断"显式纳入。  
**修法建议**：v0.2 §4 矩阵最后一列加"未确认规则阻断"格子；同时声明"未列入 §4 但列入 §16 的格子由对应 08A/08B 接受记录回放，08D 不重复实现"。

#### M2. §7 相邻回归列表缺"08C 中文跨轮投影"显式指针

v0.1 §7 写"Slice-08A continuity/registry、08B bridge/product route、08C frontend contract tests"。08C 的核心产物是 R10 `FINDINGS_revised.json`、`ego(lite)` 视觉证据和"五项首屏摘要 + Journey + 来源比较"的 schema 闭集（参见已读 08C-4 接受记录）。08D §7 只点"frontend contract tests"太弱。  
**修法建议**：v0.2 §7 显式列：(a) `ego(lite)` 1920/1440/1280 三档 synthetic fixture 回放；(b) `FINDINGS_revised.json` `p0_to_p4_clear=true`、`open_defects=[]`、`centerFoldClear=true` 三个布尔断言；(c) 中文闭集字符串扫描（与 R5 一并）。

#### M3. §6.3 "SQLite 关闭重开"没说明 project scope 复用

已读 `launch_registry.py:1319-1376` 显示 `LaunchRegistry` 是"project-scoped"，但 `open()` 默认绑定 `cwd` + DB 路径。v0.1 §6.3 写"`busy_timeout` 和项目作用域保持"，但没要求 08D 断言"两次 open 之间项目上下文是否被新连接继承"——`busy_timeout` 是 PRAGMA 级，不跨连接；若测试只在一个 `LaunchRegistry` 实例上 `open()`/`close()`/`open()`，`busy_timeout` 会丢失。  
**修法建议**：v0.2 §6.3 加一条：`open()` 后必须把 `busy_timeout_ms` 重设为 `BUSY_TIMEOUT_MS=10_000`；测试断言"`reg._busy_timeout_ms == 10000` after reopen"。

#### M4. §6.4 故障矩阵漏 CAS 冲突下"plan 状态机"路径

已读 `launch_registry.py:4576-4680`，`publish_continuity_plan` 走 `finalize_publication`，要求 `require_continuity_plan=True`。但 v0.1 §6.4 没说 CAS 冲突时 plan 自身状态（`staging/verified/published/blocked`）应停留在哪里——`verify_continuity_plan` 在 CAS 失败时是否回滚、是否允许重试？  
**修法建议**：v0.2 §6.4 增加"plan 状态机在 CAS 冲突时停在 `verified`/`blocked`，不前进到 `published`；再次重试同一 `plan_digest` 必须成功；摘要漂移则进入 `blocked` 不重试"。

#### M5. §7 "compileall 与项目/路径中性扫描"未指向具体已工作探针

已读 `test_determinism_adjacent.py` 有 `test_adjacent_r6_importable_product_untouched`、`test_r7_create_only_allowlist`、`test_protected_port_stopped`、`test_medical_writing_aggregate_unchanged`。这些是相邻回归的现成探针。v0.1 §7 没说要把它们**固化**为 08D 接受门。  
**修法建议**：v0.2 §7 加一句："08D 接受时以下相邻测试必须仍然 0 失败：`test_determinism_adjacent.py` 全部 8 项 + `test_medical_monitoring_r7_product_router.py` 全部测试 + 08A/08B/08C 接受记录中点名的合成 fixture 集合"。

### 4. 低风险观察（信息项，不构成阻塞）

- §4 表格用"场景/必测路径/预期"三列，但没列"对应 v0.2 §条款"——后续追溯成本会上升。建议 v0.2 §4 加列"v0.2 锚点"。
- §8 P0–P4 接受条件写"独立会商 P0-P4 全零"——但独立会商与 P0–P4 的关系没明确：是由本会议产出 P0–P4 列表再会商，还是由会商记录产出 P0–P4 后冻结？建议 v0.2 §8 加一段明确"会商产出 P0–P4 列表、Codex 复核后并入合同冻结"。
- §10 "最小实施形态"暗示"一组参数化综合测试 + 一个标准库 subprocess 确定性探针"，这与现有 `test_determinism_adjacent.py::test_effective_and_binding_digest_deterministic_matrix`（已使用 `subprocess.run` + 9 格参数化）高度匹配，但合同没把"复用而非新建"作为隐含约束。建议明示。
- §3.1 "incremental 只能选择同项目、同模式、已发布且兼容的基线"——`incremental` 兼容基线的具体定义（"compatible"含义）应回指 v0.2 §14（已读 §14.1），但 v0.1 §3.1 没写。
- §6.5 "成员丢失/篡改/跨项目/不在 publication 成员集均失败关闭"——已读 `launch_registry.py:1834` 的 `has_v4_closure` 路径支持 member-set 复核，但 v0.1 §6.5 没说"成员集摘要 = `content_digest(sorted(members))`"，应明示以免回归。

### 5. 边界复核结论

v0.1 §9 的边界（不增 UI、不启动服务、不读真实 listing、不调真实模型、不改医学写作、不扩安全）与 §17（v0.2 §17）实施顺序一致；08D 不应引入第二套 orchestration、不新建第二套发布器、不复制 R2 状态机——这些都已经在 v0.2 §10/§11/§13 中强制，v0.1 §9/§10 仅作重申。**这一段无需修改**。

## Evidence And Assumptions

### 证据（直接读取或交叉验证）

1. **v0.2 §15 中文闭集已冻结**：已读 `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md:78-88`。v0.1 §3.6 与其一致，但缺可执行的 fixture 扫描方式。
2. **9-cell determinism 探针已存在**：已读 `test_determinism_adjacent.py:201-235` `test_effective_and_binding_digest_deterministic_matrix(hash_seed, opt_flag)` 用 `subprocess.run([sys.executable, "-c", _REPRO_PROBE], env={..., "PYTHONHASHSEED": hash_seed})` 实现 3×3=9 格，且已在 08B 接受记录中报告通过。
3. **故障注入点已存在**：已读 `launch_registry.py:4178/4179/4227/4230/4232/4233/4447/4484/4543` 列出 `continuity.after_plan_insert`、`continuity.save.after_item_N`、`continuity.before_commit`、`continuity.after_status_update`、`continuity.publish.after_update` 等关键失败注入位置——v0.1 §6.4 应明示其清单。
4. **三模式 + basis 已有合成回路**：已读 `tests/test_medical_monitoring_r7_product_router.py:498-559` `test_replay_and_conflict_and_three_modes_and_basis_rules` 覆盖 daily/pre_lock/post_lock 三模式 + full/incremental 两 basis + 同值重放/冲突/合法/非法增量五种情况。但其覆盖深度未达 v0.1 §4"必测路径"中"用户改选兼容基线、迟到回调、无/错/漂移基线"等。
5. **R2 状态唯一、R7 只投影**：已读 `continuity.py:62-72/76-77` 七类 `RiskChangeKind` 与 v0.2 §10 表格一一对应；`_R2_STATES = frozenset({...})` 强约束 R2 权威——v0.1 §3.4 与之自洽。
6. **CAS 同事务门已实现**：已读 `launch_registry.py:4576-4680` `publish_continuity_plan` → `finalize_publication(require_continuity_plan=True)`，加 `save_continuity_plan` 内 `BEGIN IMMEDIATE` + `commit()/rollback()` 双轨——v0.1 §5 第 9 条已有证据基础。
7. **邻近医学写作保护探针已工作**：已读 `test_determinism_adjacent.py:38-43` 给出 `MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")` 与 `EXPECTED_MEDICAL_WRITING_AGGREGATE = "394746881c0b8b312805ee6e22047f6e32b66559d76987a7337ab151ed04a1c1"`。
8. **8911/5174 停止探针**：已读 `test_determinism_adjacent.py:252-254` `test_protected_port_stopped(port)` 用 `socket.connect_ex` 探测，`PORT != 0` 即"未监听"——v0.1 §7 末尾可固化。
9. **`r6_publication_digest` 仍为代理**（已读 08A 接受记录 §"明确保留边界"）：`r6_publication_digest` 当前仅以 `ResultPublication.publication_fingerprint` 作为 08A synthetic 代理——v0.1 §5 第 4 条不能声称"真实 R6 指纹同构已验证"，需措辞修正。

### 推断（明确标记 `[INFERENCE]`）

- `[INFERENCE]` v0.1 §4 矩阵的 20 格子可由 §4 当前描述 + §6.4 故障清单 + v0.2 §16.1–10 推导，但 v0.1 没把它们显式列出，导致独立实施时存在裁剪空间。
- `[INFERENCE]` 现有 `test_continuity_bridge.py::_make_daily_outputs` 用 `mo.build_daily_mode_outputs` 产生 reference，再以同一管道断言——这是常见的"双向 oracle"，在 §5 "oracle 独立"条款下处于灰区。
- `[INFERENCE]` 09:11 同源校验若在 08D 独立重写算法，可能与 08C-4 R10 算法口径不一致；故建议复用 08C-4 `FINDINGS_revised.json` 而非另起。

### 不确定 / 需 Codex 决策

- v0.1 §5 第 9 条 "九项结构化计数"是 08C-4 的产物；08D 是否允许直接复用 R10 `FINDINGS_revised.json` 还是必须重建？**需 Codex 决定**。
- v0.1 §3.6 的术语闭集扫描是按"完整词"还是"词形 + 词边界正则"判别？例外词表是否需要会商批准？**需 Codex 决定**。
- v0.1 §10 "最小实施形态"是否允许**复用**已有 `test_determinism_adjacent.py` 的 9-cell 探针？还是必须为 08D 新建独立测试文件？**需 Codex 决定**。
- 故障注入点清单是否需要在 v0.1 §6.4 全文照抄 `launch_registry.py` 已有的 9 个 `continuity.*` 钩子位置？**需 Codex 决定**。

## Risks, Gaps, And Verification Needs

### 待验证/待 Codex 决策的风险

1. **R1（矩阵闭包）+ R2（oracle 独立性）+ R5（反向断言）**：若不修，08D 接受会出现"通过 4 个 happy path + 散点异常"被解读为"通过"——这是治理层最大裂缝。**Codex 决策点**：是把 R1/R2/R5 三条作为 v0.2 必改项，还是由 08D 实施期再补？建议前者。
2. **R3（"随机固定值" 措辞）+ M3（busy_timeout 跨连接）**：都是细节但影响"接受条件"的可证伪性。**Codex 决策点**：v0.2 是否接受把 `test_determinism_adjacent.py` 9-cell 探针直接复用作 08D 接受门？
3. **R4（09:11 同源归属）**：影响 08C-4 与 08D 的治理边界。**Codex 决策点**：是否在 v0.2 §5 第 9 条明确"复用 08C-4 R10 结构化 FINDINGS 与 ego(lite) 视觉证据，08D 只回放不重建"？
4. **M4（CAS 冲突时 plan 状态机）**：影响 §6.4 的故障矩阵可执行性。**Codex 决策点**：v0.2 §6.4 是否补"plan 状态机在 CAS 失败时停在 verified/blocked；摘要漂移必 blocked"？

### 验证缺口（需要 08D 实施期补全）

- 矩阵 20 格的最小可执行断言列表（R1 修法建议中给出 16 格示例）。
- 反向断言矩阵（incremental+pre_lock / incremental+post_lock / post_lock+incremental 必须 4xx）的 fixture 路径。
- 闭集扫描的 fixture 选择与正则表达式。
- `open()` 后 `busy_timeout_ms` 重置的单元测试（M3）。
- CAS 冲突时 plan 状态机断言（M4）。
- `r6_publication_digest` 在 v0.1 §5 第 4 条措辞修正为"代理值，真实 R6 指纹同构属 08B 已接受范围"。

### 不属 08D 范围（明示不动）

- 09:11 算法口径、ego(lite) 视觉、移动端/窄屏、视觉风格。
- 真实项目、真实 listing、真实模型调用、医学结论。
- 医学写作保护面修改、系统安全设计/测试。
- Slice-08 / R7 / R8 总体接受、生产发布、监管与商业化结论。

## Recommended Next Step

1. **Codex 即时决策（建议在同会话内返回）**：
   - 是否合并成 `R7 Slice-08D 三模式综合回归合同 v0.2`？
   - 是否接受 R1/R2/R5 三项硬性修订与 R3/R4 措辞修正？
   - 是否允许 `test_determinism_adjacent.py` 的 9-cell 探针与 08C-4 R10 `FINDINGS_revised.json` 结构化断言作为 08D 接受门的复用探针（不再新建等价物）？
   - `r6_publication_digest` 在 §5 第 4 条是否改为"代理值，真实同构属 08B"措辞？
2. **若 Codex 同意**：把上文 R1/R2/R5/R3/R4/M1–M5 中已列出修订点直接并入 v0.2，Codex 在同会议二次复核后冻结；进入 08D 实施期——优先复用 `test_determinism_adjacent.py` 探针，新增一组三模式综合回归 fixture（按 20 格矩阵与反向断言矩阵）。
3. **若 Codex 暂缓**：保持 v0.1 不冻结，08D 实施期补 R1/R2/R5 三项，并在 v0.2 冻结时由 Codex 复核本报告列出的所有 12 个修订点。
4. **最坏情况下的安全路径**：Codex 不在本会话回复 → 本会话仅交付本报告，由 Codex 在下一会议拍板。Pi 不擅自改写 v0.1，不创建新文件，不启动任何测试。