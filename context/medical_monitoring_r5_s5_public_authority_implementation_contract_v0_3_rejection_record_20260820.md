# R5-S5 公开权威实现合同 v0.3 拒绝记录

- 日期：2026-08-20
- 拒绝标记：`REJECT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3_PARENT_CLOSURE_AND_TRACE_IDENTITY`
- manifest raw SHA-256：`c3c9e9d2ba6cb25bf9f73d4a4f685b2e8f8cb8bf4ba5707803d1a356061a4f35`

## 拒绝依据

1. 诚实的完整输入身份重算得到 `236 specs / 236 traces / 0 aliases`。原 `231/236/5` 声明把不同 base、mutation、outcome 或 reseal 行为误合并；即使两组表面 mutation 相同，不同 reseal 也使最终输入字节不同。
2. 实际执行 accepted temporal authority emitters 并组装完整图后：Subject 包有 20 个 parent validation errors，AE/MH 包有 19 个，有效完整图为 `0/2`，可证的十个 positive post-graph 为 `0/10`。
3. temporal root emitter 常量与 accepted parent 冲突：其 audience/authority contract/version 值不等于父合同要求的 `contract.s4.1`、producer-specific authority ID 和 `2026-08-19.1`。v0.3 内覆盖这些值会形成第四本地权威层。
4. 十个 positive 的抽象路径不存在于声称的 typed base fixture，且缺少 inherited trace 到 concrete source path/instance/value 的已接受绑定。

## 决策

- v0.3 九文件保持不变，仅作 negative evidence。
- 对已接受 temporal-projection-authority delta 新增 append-only erratum，仅修正 parent-compatible root constants/hash/receipt/packet closure，并新增 64 inherited traces 及 positive paths 的 concrete typed-source realization binding。
- erratum 独立接受后，按 `236/236/0` 诚实计数生成 implementation contract v0.4。
- 在 v0.4 获得独立接受前，producer 11 文件与 8911 继续锁定。
