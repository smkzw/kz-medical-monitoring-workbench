# R4-D09 合同冻结接受记录

日期：2026-08-14  
范围：中心重复模式与系统性风险 typed 合同；不含 artifact/runtime、R5 UI、真实项目或医学写作。

## 最终接受对象

- 合同：`reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- SHA-256：`9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- 状态：`FROZEN_R4_D09_CONTRACT_V0_5`

## 审阅链

- Pi/CMS-SMK session `01a00037-520f-7000-b401-88129ac0f56f`：v0.1/v0.2 revise，v0.3 `ACCEPT_D09_V0_3_FOR_INDEPENDENT_FREEZE_REVIEW`。
- Grok Build session `0a5b4e90-10cc-4d96-823c-356e2375c56f`：首轮 terminal cancelled 后同会话恢复；v0.1 revise，v0.3 `ACCEPT_D09_V0_3_FOR_INDEPENDENT_FREEZE_REVIEW`。
- 独立 Codex Luna/max CLI compatibility session `01a0004e-3fb6-7b30-a552-95edd8d9932a`：v0.3、v0.4 均 `REVISE_D09_CONTRACT`；v0.5 对不可变 SHA 快照返回 `ACCEPT_D09_CONTRACT`。
- 原生 Luna spawn 被当前 App 后端明确拒绝；按全局规则使用 provider=`codex` 的 CLI compatibility 路线，未替换模型。

## 已冻结关键决策

- D09 只评价单中心重复/系统性模式及同中心历时变化；项目、跨中心、治疗组推断归 D10。
- expected-set 以 pattern definition 为唯一模式轴，禁止 kind × domain × definition 笛卡尔生成。
- negative 必须闭合 required-domain L0 与中心域 L1 医学完整性、分母、机会、cutoff、窗口和方法；零风险不等于中心无问题。
- 单个高风险个例不升格为系统性模式，但 hotspot 始终保留。
- gap/change/window-pair、stable/window/evaluation/public/R2 identity、机会量、visibility、deep-link、Query proof 均为 typed 合同。
- D09 center-pattern RiskInstance 与成员风险分层计数，跨 run 相同内容使用稳定 idempotency key。
- 179-case 挑战下限以 primary partition、quota manifest、无交集并集和 canonical SHA-256 机器证明。

## 门禁与边界

- 独立 verifier 起止合同 SHA 一致。
- 8911 起止均 STOPPED。
- 未构建 catalog/oracle/registry/generator/runtime；未运行真实项目/模型/患者数据；未触碰产品 UI 或医学写作。
- 下一安全动作：按冻结 v0.5 合同构建 179-case 以上 synthetic/offline artifacts，并在独立 artifact verifier 接受后才解锁 D09 runtime。
