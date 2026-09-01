# 医学监查 R5-S4 合同冻结无损暂停点（2026-08-19，已被接受记录取代）

> 本文档保留第四轮修订时的历史暂停状态，不再是当前恢复权威。
> 同一 reviewer 后续完成至第八轮的复验并返回 `ACCEPT_R5_S4_CONTRACT`。
> 当前权威请读
> `context/medical_monitoring_r5_s4_contract_acceptance_record_20260819.md`。

## 暂停状态与边界

- 用户于第四轮独立复核进行中明确要求“进行无损暂停”。
- 已立即中断同一个 fresh isolated reviewer：`/root/r5_s4_contract_fresh_reviewer`；当前状态为 `interrupted`，没有仍在运行的子 Agent。
- 本暂停点仍只属于 R5-S4 synthetic/offline、renderer-neutral 精确合同冻结；**尚未取得 `ACCEPT_R5_S4_CONTRACT`**。
- 因此 S4 runtime、UI、浏览器、产品接入、真实项目、真实模型和生产均继续锁定。
- 医学写作子系统、R4、R5 S0-S3、根 `__init__.py`、frontend/services 均不得改动。
- 8911 已核查无监听；恢复前及 S7 明确解锁前必须继续保持停止。

## 当前事实状态

1. 原 W3 执行会话仍可续接，必须优先复用：
   - session：`01a01726-9bc8-7000-a962-baac806dfbf9`
   - 当前路由：`Pi/cms-smk/deepseek-v4-flash:max`
   - 已在同一会话完成第三、第四轮定向修订，没有因日夜路由或慢响应新开会话。
2. 第四轮修订已关闭上一轮审阅者明确复现的以下缺口：
   - ReferenceBaselineItem 全叶外部权威绑定与 baseline row 精确重建；
   - Journey event/visit 身份与可定位状态绑定；
   - QueryDraft 全量身份/内容绑定；
   - audit worker、packet fingerprint、worker refs、audience baseline/验证中文投影重建；
   - 真正的 zero/single/N fixture，single 不再别名到 multi；
   - declared-leaf coverage gate 与 97 行 registry 单一变异/单一错误码收敛。
3. 外部临床权威 fixture：
   - `artifacts/medical_monitoring_r5_s4_contract_v0_1/accepted_authority_anchor.json`
   - generator 不创建、不重写、不列入 manifest、不签署该文件；verifier 必须由调用方显式传入 `--anchor`，缺失时非零 fail closed。
   - 该 fixture 与其 test pin 同属当前 S4 合同写集的信任边界，是否足以构成最终独立权威，仍须同一 fresh reviewer 给出结论；不得由主会话自行接受。
4. `critical_severity_authority` 继续是 named deferred：`critical-severity-authority-public-v1`。当前范围内所有 critical packet 必须拒绝，不存在 verifier 自造的可通过 critical 路径。
5. 另两个 named deferred 保持不变：
   - `aemh_match_history` → `aemh-match-history-public-v1`
   - `subject_temporal_spine_full` → `subject-workspace-temporal-spine-v1`

## 主会话第四轮后实际验证

主会话在当前文件系统上实际运行并观察到：

- generator write 成功，且只写：`exact_overlay.json`、`packet_schema.json`、`source_pins.json`、`manifest.json`；
- generator `--check`：`mismatches=[]`；
- verifier 以 caller-supplied anchor 运行成功；normal 与 `PYTHONOPTIMIZE=2` 输出逐字节一致；
- verifier 缺少 `--anchor` 时非零退出，并输出 `external accepted-authority anchor required`；
- Ruff `--select F` 通过；`py_compile` 通过；
- 完整 `poc/medical_monitoring_ai_native_r5/tests`：`989 passed in 24.20s`；
- verifier 报告：8 个 generator-owned artifacts、0 planned、97/97 registry rows、13 tamper probes、299 source-matrix rows、27 schema objects，状态为 `R5_S4_CONTRACT_READY_FOR_REVIEW`；
- 8911 无监听。

上述只证明当前门禁通过，不等于独立接受。

## 当前稳定 SHA（raw file）

- human contract：`334c7983863b00c7dae84f118b814cd96743e5d8e6cb77c35ce5c160d40e1792`
- generator：`034faf86f10258aac1049d59442844e04da7e833610aae0d52bb700f77e41a75`
- verifier：`5298bdaae7d8bc75a81eeb8fbbd44c3be007e21cb382c49a4e6c499f20f365c0`
- external accepted-authority fixture：`be19b4058ee9d60cf91a900dea482e81b91a0c953019db16d52e001b3067ca38`
- challenge registry：`6614394d6e370d298e9b7179b09e651af42f0aaf716f8fefc6c03a2c74951961`
- exact overlay：`7b65ffbf8c061b1848a7b56ef97e1721909e6feed73e209993019964982848c5`
- manifest raw file：`271eef939bba62a0f22578bf7247e784cc5ca17bd001256702760c61db0790db`
- packet schema：`8306e3fe1ab80c451b852800ab73f7f47c175cbfca497845cfddb2571e9c2d16`
- source pins：`7267776ef395cea3fd7a3a069a23c1cc7575ebecae62a4c4de8a4de30e47081c`
- S4 tests：`ec02b020ddc559fcd9c9f801e3ed240fd6237846c2a6bb4944362bea566e16ce`
- accepted R5 exact-contract JSON raw file：`3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`

verifier 输出的 manifest canonical content/self hash 为：
`f5ca1b40d5c5c25de1ad060658fe8d8d27a6d7d39f59b5bd24c05ce27fc4ce3b`。
它与 manifest raw-file SHA 使用不同 recipe，恢复时必须分开陈述。

## 独立审阅 lineage 与当前停止点

同一 reviewer 已连续进行多轮复核。最近一个**有效**结论是针对第三轮快照的 `REVISE_R5_S4_CONTRACT`，指出 baseline、Journey、Query、投影叶与 single fixture 缺口；这些缺口触发了当前第四轮修订。

针对第四轮快照：

1. 第一次复核请求被平台误判为 cybersecurity 内容，Agent errored；这不是 ACCEPT 或 REVISE。
2. 已在同一 reviewer 会话中以“临床数据合同一致性复核”重新发送等价检查任务。
3. 用户随后要求暂停，主会话立即中断 reviewer；因此第四轮快照**尚无独立 verdict**。

恢复时必须复用 `/root/r5_s4_contract_fresh_reviewer`，不得因为被中断或误判而新建另一审阅者，除非该会话被运行时明确判定不可恢复并留下证据。

## 证据文件与注意事项

- 第三轮执行提示：`prompts/execution/medical_monitoring_r5_s4_contract_20260819/worker_03_followup6_revise_01a01726.md`
- 第四轮执行提示：`prompts/execution/medical_monitoring_r5_s4_contract_20260819/worker_03_followup7_revise_01a01726.md`
- 第三轮 runner stdout：`runs/pi_medical_monitoring_r5_s4_contract_20260819_worker03_followup6.stdout.log`
- 第四轮 runner stdout：`runs/pi_medical_monitoring_r5_s4_contract_20260819_worker03_followup7.stdout.log`
- execution report：`runs/execution/medical_monitoring_r5_s4_contract_20260819/worker_03.md`

重要：runner 在 followup6/7 的 stdout 中保存了最新完整输出，但 `worker_03.md` 仍显示较早一轮报告内容，不能把该旧文本当作当前快照事实。恢复后应以当前文件、上述 raw SHA、主会话门禁和 followup7 stdout 为准，并在最终接受前修复/补齐 durable execution report 的这一记录偏差。

阶段尚未接受，因此没有运行 `cleanup-execution`，也没有清理 W3/reviewer 证据；这些记录当前仍是恢复必需材料，不得删除。

## 恢复后的唯一安全动作

1. 完整重读最新全局与工作台 `AGENTS.md`，再读本暂停点、S4 execution context/plan、human contract 与 followup7 stdout。
2. 只读核对上述 raw SHA、accepted R5 exact JSON SHA、8911 无监听及是否存在暂停后的迟到写入。
3. 若 SHA 稳定，不要先重跑全部测试；直接复用同一 `/root/r5_s4_contract_fresh_reviewer`，继续已中断的“临床数据合同一致性复核”，要求唯一 `ACCEPT_R5_S4_CONTRACT` / `REVISE_R5_S4_CONTRACT`。
4. reviewer 必须重点复核：baseline 全叶外部绑定、Journey event/visit+availability、QueryDraft 权威绑定、所有 audit/worker/audience declared-leaf 重建、真实 single fixture，以及 anchor/test pin 信任边界。
5. 若 `REVISE`：把精确复现项发回同一个 W3 session `01a01726-...`，修订后由主会话跑相称门禁，再回到同一 reviewer。
6. 若 `ACCEPT`：写 S4 合同接受记录，修复 durable execution report 偏差，更新 plan/metrics/context，运行 guard 允许的 execution cleanup，然后读取 R5 计划决定 S4 runtime 的下一份精确片合同；仍不得直接进入 UI 或启动 8911。

## 恢复提示

> 继续医学监查 R5-S4 合同冻结。先完整读取最新全局/工作台 AGENTS.md 与 `context/medical_monitoring_r5_s4_contract_pause_20260819.md`，核对暂停点 raw SHA、accepted R5 exact JSON SHA、8911 必须停止和是否有迟到写入。当前第四轮快照已由主会话跑通 989 项 R5 测试及全部机械门禁，但尚无独立 verdict。复用同一 `/root/r5_s4_contract_fresh_reviewer` 继续被中断的临床数据合同一致性复核；不得新建 reviewer，不得实现 S4 runtime/UI，不得触碰医学写作、R4、R5 S0-S3、真实项目/模型/生产。只有 `ACCEPT_R5_S4_CONTRACT` 才可关闭合同阶段并规划下一片。
