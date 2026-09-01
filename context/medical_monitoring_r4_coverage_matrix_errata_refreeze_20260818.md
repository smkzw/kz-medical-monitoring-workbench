# R4 公共风险覆盖矩阵 Errata 与重新冻结记录

日期：2026-08-18  
决定：`REFREEZE_CURRENT_MATRIX`  
范围：synthetic/offline R4 阶段合同；不代表 R4 阶段接受或 R5 解锁。

## 1. 决定

将当前 `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` 的字节显式重新冻结为 R4 当前公共风险覆盖合同：

- 新冻结 SHA-256：`8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`
- 被替代的初始冻结 SHA-256：`6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`
- 矩阵文件本轮不改写；本记录把 2026-08-12 尚未形成独立 errata 的变更补齐为可审计的显式重新冻结。
- 历史接受记录保持原样，不回写或抹除旧 SHA；涉及当前阶段关闭时，以本 errata 的新冻结 SHA 为准。

## 2. 决定依据

逐字节分类证据见 `context/medical_monitoring_r4_coverage_matrix_diff_classification_20260818.md`：

1. 已从两个接受期 runner 日志独立恢复 389 行旧矩阵；两次重建均精确得到旧 SHA `6bb9f73a…2705`。
2. 旧字节与当前字节只有 1 个 unified-diff hunk，位于 R4-D06 输出边界。
3. 该 hunk 是 C 类合同变更：D06 从项目级聚合输出收窄为受试者级稳定结果与 coverage，中心/项目/治疗组分母及聚合趋势唯一由 D10 生成。
4. 后续已接受的 D06 合同、挑战 184、D06 evaluator、D07 contract follow-up、D10 合同及 evaluator 已按当前句子实现并接受；没有已接受实现依赖旧句“项目级分母明确的趋势摘要”。
5. 恢复旧字节会使公共矩阵与已接受 D06/D10 owner 边界直接冲突，因此不采用静默恢复。

## 3. 传播影响

| 传播面 | 当前影响 | 重新冻结要求 |
|---|---|---|
| D01–D05 | 历史接受时钉旧 SHA，但未依赖差异句正文 | 保留历史记录；阶段关闭引用本 errata |
| D06 | 合同与 runtime 已禁止中心/项目/治疗组聚合 | 重跑 D06 focused、challenge、mutation 与 owner boundary |
| D07 | 合同 follow-up 已钉当前 SHA | 重跑 D07 artifact/runtime 相邻回归 |
| D08–D09 | 消费受试者/中心级稳定输入，不获得 D06 项目聚合权 | 重跑相邻 runtime/artifact |
| D10 | 唯一拥有中心/项目/治疗组疗效聚合 | 重跑 D10 runtime、projection、artifact 与高风险可见性 |
| Query/PD | 无变化 | 仍为“依据＋发现＋行动项”草稿；PD 只作待核实线索 |
| R5/UI | 不在本次范围 | 继续锁定，等待 `ACCEPT_R4_STAGE` |

## 4. 重新冻结接受门

本记录只有在以下证据全部通过后，才能用于 R4 阶段关闭：

- 矩阵实读 SHA 仍为 `8ad9d6…fc03`；
- coverage contract、D06 focused/挑战/变异、D07–D10 adjacent/artifact、全 R4 回归通过；
- Ruff 与 compile 通过；
- shared ensemble/reference-baseline 闭环及 D06 去 sentinel 修复通过决定性测试；
- 8911 无监听；
- 同一 fresh-context stage verifier 返回 `ACCEPT_R4_STAGE`。

在独立 verifier 接受前，当前阶段结论仍为 `REVISE_R4_STAGE`。

## 5. 边界

本 errata 不修改任何 POC 源码或冻结 artifact，不启动服务、浏览器、真实项目或真实医学模型，不触碰医学写作子系统，也不构成产品、R5、UI 或商业化验收。
