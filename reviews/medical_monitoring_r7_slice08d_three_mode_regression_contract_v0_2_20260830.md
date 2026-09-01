# R7 Slice-08D 三模式综合回归合同 v0.2 纠偏附录

日期：2026-08-30  
状态：`FROZEN_ACCEPTED_R7_SLICE_08D_CONTRACT_V0_2`

本附录与 v0.1 合并构成完整 08D 合同；冲突时本附录优先。它只增强可执行验收，不改变冻结 Slice-08 v0.2 的业务语义。

## 11. 二十格场景闭包

每格均必须有唯一 case key、独立输入 fixture、预期公开结果或稳定错误码；禁止只跑四个 happy path。

| Case key | 场景 | 条件 | 最小断言 |
|---|---|---|---|
| DF-N | 日常 full | 正常完整快照 | 无比较基线；全量生成；publication available |
| DF-B | 日常 full | 高危关联行缺失 | 不因缺行关闭；需重新判断/既有高危沿用 |
| DF-M | 日常 full | 快照/映射/覆盖不合格 | baseline 不可提升；结果失败关闭 |
| DF-R | 日常 full | 同值重放 | 返回原运行/发布身份与相同摘要 |
| DF-C | 日常 full | 同 key 不同快照/规则/决定版本 | 稳定冲突；不覆盖旧结果 |
| DI-N | 日常 incremental | 推荐最近兼容已发布基线 | 逐对象沿用/重评；七类变化正确 |
| DI-B | 日常 incremental | 用户改选另一兼容基线 | 比较来源与摘要切换到所选基线 |
| DI-M | 日常 incremental | 无基线、跨项目/模式、未发布或摘要漂移 | 失败关闭；不伪装增量 |
| DI-R | 日常 incremental | 同值重放 | plan/publication/item 字节与顺序一致 |
| DI-C | 日常 incremental | 同 key 不同基线或未确认规则 | 稳定冲突/阻断；不回退旧规则 |
| PL-N | 锁库前 full | 一般完整修订 | 归因为“本轮数据修订变化” |
| PL-B | 锁库前 full | Query 关联证据完整 | 仅相关对象显示“Query 后修订影响” |
| PL-M | 锁库前 full | Query 证据不完整或仅时间相邻 | 不显示 Query 归因；缺口可追溯 |
| PL-R | 锁库前 full | 同一轮同值重放 | 返回原发布；历史条目不增加 |
| PL-C | 锁库前 | incremental 或同 key 不同完整 listing | 明确 4xx/冲突；旧历史不覆盖 |
| PC-N | 核查前 full | fixed-total 完整固定范围 | 发布绑定 snapshot/cutoff/rules/decision/centers |
| PC-B | 核查前 full | 同值固定范围重放 | 返回原运行/发布；旧结果字节不变 |
| PC-M | 核查前 | `fixed_total=false` 或 incremental | 明确 4xx；不创建运行 |
| PC-R | 核查前 full | 关闭重开/迟到 callback 后同值恢复 | 只完成原事务；无半发布/重复发布 |
| PC-C | 核查前 full | snapshot/cutoff/rules/decision/center 任一变化 | 创建新运行；旧 publication/plan 不变 |

模式×basis 反向断言必须独立覆盖：`daily/full`、`daily/incremental` 可用；`pre_lock/incremental` 与 `post_lock_pre_cfdi/incremental` 返回稳定中文 4xx；`post_lock_pre_cfdi/full` 若未固定总量同样失败。预期码以现有产品合同为权威，测试不得为了迁就实现新增同义错误码。

## 12. 独立 oracle 与反过拟合

1. expected 只能由输入侧冻结事实重建：R2 前后状态/严重度、R5 authority packet、R6 ModeOutput/receipt、R1 ArtifactEnvelope 实际成员字节、规则作用域和当前/比较快照。不得从被测公开 DTO、产品 payload、FINDINGS、自报 digest 或数据库结果反算 expected。
2. `artifact_verified`、`artifact_member_verified`、identity/coverage complete 等门值必须由实际 verifier 路径得出；测试不得直接置 `True` 后把它当权威。负例必须篡改底层事实或字节，而不是只改布尔值。
3. fixture 名、case key、case id、mutation class、case 描述、预期 digest 不得进入产品或 oracle 决策分支。它们只可用于 pytest 参数 id 与失败定位。
4. oracle 必须独立重建 canonical payload、排序、计数、member-set digest 与 SHA-256；产品输出仅作为 actual。
5. 08D 使用 08B 已冻结的真实 R5/R6/artifact closure，不得退回 08A 早期代理 digest 作为 authority。

## 13. 确定性固定网格

固定运行 `PYTHONHASHSEED ∈ {0,1,17,42,31415926}` × 解释器参数 `normal/-O/-OO` 共 15 格。每格在独立 subprocess 中使用同一输入侧 fixture，比较公开 JSON 字节、plan/item/publication digest、排序、计数与稳定错误码。优先扩展并复用 `test_determinism_adjacent.py` 现有探针，不新建生产模块。

SQLite 关闭重开后必须通过 `PRAGMA busy_timeout` 直接断言 10000 ms，不读取私有属性代替真实连接状态。

## 14. 原子状态与故障恢复

- 至少覆盖当前实现已有的 plan insert、逐 item、status update、publication update、version advance、before commit 故障点；测试从源码枚举当前钩子并逐一命中，未命中即失败。
- CAS 冲突时 plan 不得进入 `published`。可重试冲突保持 `verified`；真实摘要/成员/身份漂移进入 `blocked` 或保持可解释失败状态，绝不推进 publication available。
- 同 `plan_digest` 修复瞬时冲突后可完成一次；不同 digest、迟到 callback 与重复 finalize 不能覆盖或新增第二 publication。

## 15. 08C 边界与中文公开面

08D 不重启 ego(lite)、不截图、不重建 08C-4 FINDINGS 算法，也不以 mtime 代替回归。只复跑已有 08C 前端/DTO/中文合同测试，证明综合后端回归没有改变已接受的字段、九项计数、五项摘要、七类变化与身份路由。

内部术语验证按公开 schema 字段与实际 UI 文本节点执行，不对医学来源正文做全字符串 scrub，也不依赖英语 `\b` 词边界。允许的医学正文词语不会因包含“模型”“运行”等自然语言被删除；内部 `run_id/run_ref/digest/CAS/artifact/provider/model/sqlite/S4/R5/R6/R7` 字段不得进入公开对象或 UI 节点。

## 16. 相邻回归固定门

至少复跑：

- `poc/medical_monitoring_ai_native_r7/tests/test_continuity.py`
- `test_continuity_registry.py`
- `test_continuity_bridge.py`
- `test_determinism_adjacent.py`
- `tests/test_medical_monitoring_r7_product_router.py` 中 Slice-08A/B/C 与三模式/basis 路径
- 直接共享的 R2 lifecycle、R5 authority、R6 ModeOutput/receipt/artifact-envelope 最小决定性套件
- 现有 08C 前端 contract test files；不运行新浏览器视觉验收

compileall、项目/路径中性、医学写作保护面和 8911/5174 停止证据必须随同记录。任何通过集不得用 deselection 隐藏 08D 影响路径。

## 17. 完成门

20 格、15 格确定性、全故障钩子、反向 mode/basis、公开中文、相邻回归全部通过；独立实现审阅列出 P0-P4 且全部为 0；Codex 复核当前源码、actual/expected 独立性、测试日志、端口和医学写作边界后，方可接受 08D。

本合同通过只解锁 Slice-08 总体复盘，不直接解锁 Slice-09、R7 总体或 R8。

## 18. 冻结依据

- 同会话独立复核：`runs/conference/mm_r7_slice08d_contract_20260830/general_single_object_round2.md`
- 复核结论：`ACCEPT_CONTRACT_V0_2`
- 严重度：P0/P1/P2/P3/P4 = `0/0/0/0/0`
- Codex 最终判断：v0.1 与本附录合并后的合同可进入 08D governed execution；实施期仍须由输入侧事实证明 oracle 独立性，不得将会商接受误写为实现完成。
