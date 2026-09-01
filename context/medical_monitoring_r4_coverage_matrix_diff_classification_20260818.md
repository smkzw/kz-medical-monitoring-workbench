# Coverage Matrix 差异分类与冻结动作备忘录（W2）

日期：2026-08-18
状态：`CLASSIFICATION_READY_FOR_CODEX_DECISION`
范围：仅分类与建议；本备忘录不修改矩阵、不冻结、不构成 R4 接受。

## 1. 两个字节集的来源与 SHA

### 1.1 已接受字节集（FROZEN_R4_CONTRACT_V1）

- SHA-256：`6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`
- 冻结：2026-08-10，Codex 主会场在 Pi `ACCEPT` / Grok 反证复核 `ACCEPT` 后应用最终 P4 文字收口并冻结。
- 当前文件系统上已无该版本的独立副本（git 不存在；`archives/`、`records/`、`backups/`、hermes_sessions 均为 07 月或更早内容，无 R4 矩阵快照；无任何日志内嵌完整矩阵正文副本）。
- **恢复方式**：从接受期内（矩阵仍为已接受字节时）runner 日志中 `read` 工具结果重建。
  - 主来源：`logs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_01_stdout.txt`
    - `toolCallId call_b92928c6e9ad4f54864cbcbe`：`read reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`（行 1–300 全量，行号前缀 `N:`）
    - `toolCallId call_b363a07d74d54efc967ad328`：`read ...:301-389`（行 301–389 全量）
  - 交叉验证来源：`logs/conference/medical_monitoring_r4_d02_cm_contract_20260811/general_pi_qwen38_stdout.txt`（同法重建，结果一致）。
  - 重建（去除 `[anchor]` 首行与 `N:` 行号前缀，`\n` 连接，389 行含末行空行）后重算：
    - `sha256(reconstructed) = 6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705` ✅ 精确匹配
  - 两个独立日志重建结果均为 389 行、无缺行、SHA 精确一致 → 不是手工拼凑，是字节精确恢复并经验证。

### 1.2 当前字节集

- SHA-256：`8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`
- 来源：`reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`（当前文件系统，磁盘实读重算确认）。
- mtime：2026-08-12 22:06:37 +0800（D06 合同会话期间）。
- 时间线证据：
  - 2026-08-10 冻结 `6bb9f73a`；D01（AEMH slice/acceptance）、D02（contract/acceptance/slice）各接受记录均钉 `6bb9f73a`。
  - 2026-08-12 21:19 D05 final acceptance（矩阵仍未变）。
  - 2026-08-12 22:06:37 矩阵被改写 → `8ad9d6`。
  - 2026-08-12 22:08:55 `prompts/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup2.md` 显式写：“the revised `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` at SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`” → 编辑发生在 D06 合同会话内，且该会话把修订后矩阵当权威使用。[编辑者身份为推演：mtime 落在 D06 会话窗口内且 followup2 立即引用新 SHA，无独立编辑记录]
  - 2026-08-13 07:26 D06 合同冻结（`FROZEN_R4_D06_CONTRACT_V1_18`）；08-13 D06 实现会话读取的矩阵已是新句；08-13 D07 contract followup2 钉 `8ad9d6`。
  - 2026-08-14 D08、08-16 D10 合同冻结。此后矩阵未再变化（与 08-13 D06 实现日志读到的输出行一致）。

## 2. 差异 hunk 分类

两个字节集 unified diff 仅 **1 个 hunk**（`@@ -265,7 +265,7 @@`，第 268 行，R4-D06 输出行）：

| 版本 | 第 268 行内容 |
|---|---|
| 已接受 `6bb9f73a` | `| 输出 | 疗效数据一致性/趋势待核实风险、指标趋势图、时间轴联动和项目级分母明确的趋势摘要 |` |
| 当前 `8ad9d6` | `| 输出 | 疗效数据一致性/趋势待核实风险、受试者级指标趋势图、时间轴联动，以及供 D10 聚合使用的稳定个体结果与 coverage；中心/项目/治疗组分母和聚合趋势仅由 D10 生成 |` |

### 分类：**C**（合同变更）

- 非 A：不是空白/换行/非语义编辑，是实质性措辞与义务变更。
- 非 B：不是“不改变合同语义的澄清”。变更内容：
  1. D06 输出从“指标趋势图”收窄为“受试者级指标趋势图”；
  2. 删除 D06 输出中的“项目级分母明确的趋势摘要”（项目级聚合输出义务从 D06 移走）；
  3. 新增 D06→D10 交接义务：“供 D10 聚合使用的稳定个体结果与 coverage”；
  4. 显式把中心/项目/治疗组分母与聚合趋势的生成权**唯一**授予 D10。
- 归类 C 的理由：改变 D06 域输出合同与 D06/D10 聚合归属边界（共享服务合同 §5.2 之外的域间所有权边界），属于“changes … ensemble/聚合边界/风险门”一类的合同面变更；即使按最严枚举（L0/L1/L2/L3、Query、lifecycle、ensemble/baseline、visibility、risk gate）判断，第 4 项直接落在“聚合/ensemble 归属”合同面上，且改变了 D06 输出可交付物。

## 3. 后续 D01–D10 已接受实现对该 hunk 的语义依赖

### 3.1 依赖新句（C 变更）的已接受记录

| 记录 | 时间 | 依赖证据 |
|---|---|---|
| D06 合同 `medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`（FROZEN_R4_D06_CONTRACT_V1_18） | 冻结 2026-08-13 | §1 第 18 行：“D06 输出严格停在受试者级稳定结果、个体趋势和供 D10 消费的 typed inputs；不得形成中心、项目、治疗组或总体分母、聚合趋势、比较或推断。所有中心/项目/治疗组聚合唯一由 D10 生成。”——与新句逐条同义。 |
| D06 合同挑战矩阵 | 冻结 2026-08-13 | 第 184 行：“D06 尝试输出中心/项目/治疗组聚合趋势 → owner/QC fail，必须路由 D10”。可执行验收依赖新句。 |
| D06 实现 `efficacy_evaluator.py` | 接受 2026-08-13 | 第 2766 行：`raise OwnerScopeContractError("D06 must not form project-level aggregates", "owner_scope_validation")`——实现强制新句边界。 |
| D07 contract followup2 `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup2.md` | 2026-08-13 | 第 18 行把 R4 matrix 钉为 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03` 作为其核验基线。 |
| D10 合同 `medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`（v0.6） | 冻结 2026-08-16 | 第 82 行：D06 site efficacy rate/estimand 不得作为 D09 成员；只有 D10-owned、已授权的 efficacy context 可消费 D06 typed measure 作为 source measure——消费 D06 个体结果并独占聚合，依赖新句边界。 |
| D10 实现 `d10_evaluator.py` | 接受 2026-08-17 | `member_producer_d06`、`efficacy_present` 等字段消费 D06 typed 个体 measure；D10 独占项目级聚合。 |

### 3.2 无任何已接受记录依赖旧句

- 全库检索旧句“项目级分母明确的趋势摘要”：仅出现在读取旧字节的日志（作为 read 工具输出），**无任何**已接受合同、review、acceptance、context、plan、metrics 或测试引用旧句。
- D01–D05 合同/接受记录（均在编辑前）钉的是 `6bb9f73a` SHA 本身，未引用该句正文；编辑发生在 D05 接受（21:19）之后，D05 无矩阵正文依赖。

### 3.3 结论

- C 类变更，且后续已接受域合同（D06 V1_18、D07 followup2、D10 v0.6）把新句当权威；D06 实现与 D10 实现已按新边界落地并通过（全 R4 `4268 passed`）。
- 恢复旧句会让矩阵与已接受的 D06 合同（§1 第 18 行、挑战 184）、D06 实现、D10 合同 §2/§3、D10 实现产生**直接矛盾**（矩阵将宣称 D06 输出“项目级分母明确的趋势摘要”，与“不得形成项目级聚合”冲突）。

## 4. 建议：正式重冻当前字节（不静默恢复）

按 grok 方案决策表：**C，且后续已接受域合同把新句子当权威 → 不得静默恢复；写 errata：逐项差异、传播影响、重冻 SHA、阶段证据重跑。**

- 恢复 `6bb9f73a` 会推翻已接受的 D06/D07/D10 运行时语义，且新句已有多个已接受下游依赖 → 恢复路径不成立，除非先架构/过程分叉（本备忘录不建议）。
- 推荐动作：以当前字节 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03` 正式重冻 `FROZEN_R4_CONTRACT_V1`，并写冻结记录（含本备忘录引用）。

## 5. 传播与所需测试（重冻路径）

1. **冻结记录**：在 `context/` 或 `runs/execution/medical_monitoring_r4_stage_closure_20260818/` 下写重冻记录：差异逐项表、传播表（D06 合同/挑战 184/实现、D07 followup2、D10 合同/实现）、新 SHA、编辑时间线、本备忘录引用。矩阵文件本身不改（当前字节即冻结字节）。
2. **SHA 复核**：`shasum -a 256 reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` == `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`。
3. **测试**：
   - `poc/medical_monitoring_ai_native_r4/tests/test_coverage_contract.py`（当前 55 passed；矩阵正文不被测试字节引用，只引用 §6 语义——重冻不改变该结果）。
   - D06 focused：D06 合同 219 行挑战全绿（已知通过）。
   - D10 focused：`tests/test_d10_runtime_contract.py`、`tests/test_d10_runtime_closure.py`。
   - 全 R4 回归（`4268 passed` 基线）与 Ruff 门（W1/W5 负责；本 W2 不重复执行）。
4. **接受记录更新**：钉 `6bb9f73a` 的历史记录（D01/D02 时代）标注“该 SHA 已被 2026-08-18 errata 重冻取代”，不改写历史字节；D06/D07 followup2/D10 记录保持 `8ad9d6` 不变。
5. **8911 保持停止**；不启动服务、不改 POC/artifact/test 字节。

## 6. 不确定性

- 接受字节恢复：无不确定性——两个独立日志重建 SHA 均精确等于 `6bb9f73a…2705`。
- 编辑者与动机：mtime 落在 D06 合同会话窗口且 followup2 立即引用新 SHA，判定编辑发生在该会话内，动机为对齐 D06/D10 边界；但无独立编辑记录/提交，[INFERENCE]，非证据。
- 分类边界：该 hunk 是否落在“C 枚举面”存在解释空间（域输出/聚合归属 vs L0/L1/L2/L3 等显式枚举）；无论按 B+C 依赖或直接 C 处理，决策表结论一致（下游已接受依赖 → 重冻），本备忘录取 C。
- 未执行：矩阵未改、未重冻、未跑全 R4（属 W5 同一 verifier 复验包范围）；本备忘录不构成 R4 接受。

## 7. 停止条件

- 若 Codex 决定恢复 `6bb9f73a`：必须先解决与已接受 D06/D07/D10 合同的矛盾（架构/过程分叉），本备忘录标记为“不推荐、需停止升级”。
- 若发现任何已接受 Dxx artifact 或测试字节级依赖矩阵正文（当前检索未发现）：停止并升级。
- 若后续发现第二个差异 hunk（当前 diff 仅 1 hunk）：停止并升级，勿在缺漏分类下重冻。

## 8. 结论

- 已接受字节已恢复并验证：SHA-256 精确等于 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`。
- 当前字节 SHA-256 = `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`。
- 唯一差异：1 个 hunk（R4-D06 输出行），分类 **C**，且 D06/D07/D10 已接受合同与实现语义依赖新句。
- 建议：**正式重冻当前字节**并写 errata/冻结记录；不得静默恢复 `6bb9f73a`。
- 本备忘录不冻结矩阵、不代表 R4 接受；`CLASSIFICATION_READY_FOR_CODEX_DECISION`。
