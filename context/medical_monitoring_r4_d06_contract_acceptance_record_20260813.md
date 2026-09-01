# R4-D06 合成/离线纵切合同接受记录

Date: 2026-08-13  
Status: `ACCEPTED_FROZEN_R4_D06_CONTRACT_V1_18`

## 接受对象

- 合同：`reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- 独立接受的 v1.18 草稿完整文件 SHA-256：`663ca94a3166fea08080a0611e3831a21396fe3a8783c646a434e2e537b8bef7`
- 独立接受且冻结后保持不变的 §1–§14 语义 SHA-256：`247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`
- Codex 写入顶部状态与 §15 冻结记录后的最终文件 SHA-256：`460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`
- 固定 typed fixture catalog 版本/hash/文件 SHA-256：`8.0.3` / `44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774` / `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9`
- 固定 independent expected-outcome oracle hash/文件 SHA-256：`16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a` / `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b`
- 固定 219-case registry hash/文件 SHA-256：`f7a7733b00c1367d95e66d7f8b5e1a12793d51ab0f7585367dcad664922be1b4` / `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba`
- 冻结生成器 SHA-256：`fea1ad5692d81aabb19419709fbd3f5b9c4b9a7efdef9f4280db9668383fc3f2`

## v1.16–v1.17 被取代原因

v1.16 实现因 expected/manifest 循环注入、106/191 同输入异 trace、硬编码与失败吞没等问题被独立拒绝。v1.17 修复了 106/191 的 validation-artifact 冲突，既有实现会话随后移除了主要注入路径，但暴露出用例 17/173 仍拥有相同实质 typed input、不同 `clinical_outcome_contract`，测试又对 173 做了特例跳过。该 v1.17 实现同样从未被接受。

v1.18 将 17/173 的结果统一为 `definition boundary gate`，补齐完整 definition scope、精确 instrument/endpoint schema 与 endpoint version，并冻结实质重复组不变量：移除 `fixture.challenge_number` 后，相同输入必须具有相同 entrypoint、trace 和全部非用例绑定结果；只允许 assertion code、evaluated fixture hash 与 fixture hash 随用例变化。独立 `DefinitionBoundaryClinicalOutcomeResolver` 只依据 typed definition-boundary 输入求值，不得读取 expected/oracle/manifest 或用例身份。

## 独立反证链

同一 Codex Luna session：`019ff62a-6f59-75f2-b80f-95f917d53a4b`。

- Pass 27 复算 v1.18 全部锚点，验证 219 条关系、实质重复组不变量、精确 definition scope/schema/version、独立 resolver 及负变异；结论 `VERDICT: ACCEPT`，无 P0–P4。
- Codex 仅改动顶部冻结元数据和 §15，并更新完整文件/前导 pin；§1–§14、catalog、oracle、registry 未改变。
- Pass 28 对冻结转移做只读 metadata 复核，重算全部 SHA、运行生成器 `--check`，验证 preamble 与 §15/suffix 变异在 manifest 生成前失败；结论 `VERDICT: ACCEPT`，无 P0–P4。

决定性报告：

- `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup24.md`，SHA-256 `1d975757a9f0bea48b46dbbba39793cba2264fcf5cf140f6515914f85d64bf7b`
- `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup25.md`，SHA-256 `22bcb23bef37f59d12472c6bca44b6aee41ae09df74c5e5077617013e50cac98`
- 拒绝初始实现的独立报告：`runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813.md`，SHA-256 `26e55fd5abcc43dca16508a51ebf4abf2f6aedd77dcf61a3489a1b9a102f4136`

## 接受范围与下一动作

接受仅限 synthetic/offline R4-D06 v1.18 合同语义、219 个挑战用例及固定验证工件。下一步只能让既有 implementation worker session 适配 v1.18，删除 17/173 特例跳过，令全部 219 个 raw runtime outcome 无例外匹配 oracle/DSL；随后由原 fresh-context implementation verifier 复核。

它不接受或证明 D06 代码、R4 总体、R5 Patient Journey UI、真实项目、真实数据/模型、总体疗效统计分析、产品、医学写作或生产。继续保持：8911 停止；不运行真实项目；不修改医学写作子系统；不新增或测试系统安全功能。
