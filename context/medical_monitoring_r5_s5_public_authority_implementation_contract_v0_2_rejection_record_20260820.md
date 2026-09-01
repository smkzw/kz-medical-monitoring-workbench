# R5-S5 公开权威实现合同 v0.2 拒绝记录

- 日期：2026-08-20
- 拒绝标记：`REJECT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_2_AUTHORITY_INCOMPLETE`
- 冻结对象：`artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/manifest.json`
- manifest raw SHA-256：`cf805305e927caee07464061e95ac894a866b3a5a444d29f012e26ea92893e6f`

## 拒绝原因

去除 candidate/target/example 镜像后，现有 accepted authority surface 无法独立构造完整 272 个叶子。fresh full-leaf audit 的依赖传播结果为：

- Subject 156 叶：A 直接权威 28，B 确定性派生 18，C 已接受策略权威 4，D 不可构造 106。
- AE/MH 116 叶：A 25，B 28，C 0，D 63。
- 总计：A 53，B 46，C 4，D 169。

根缺口包括：截止日端点绑定、时间轴及日期端点权威、访视/事件/阶段/风险精确成员绑定、阶段呈现词典、待补日期成员 recipe、可见性 node 到 stable member/site 的 typed bridge、locator-revision 完整消费，以及 AE/MH append-decision/evidence/thread membership authority。其依赖的 hash、membership、projection、receipt 与 packet 也因而不可构造。

## 决策

- v0.2 九文件保持字节不变，仅作 negative evidence；不原位修补。
- 先冻结并独立接受统一 `temporal-projection-authority delta v0.1`，一次性关闭 169 叶的根权威/配方缺口。
- 随后仅从 accepted public-authority parent + accepted semantic-authority delta + accepted temporal-projection-authority delta 新生成 implementation contract v0.3。
- 在 v0.3 获得 fresh isolated acceptance 前，11 个 producer allowlist 继续锁定，8911 保持停止。

本记录不拒绝已接受的 parent 或 semantic delta，也不接受任何 producer、S5 runtime、UI、真实项目/模型、产品或生产状态。
