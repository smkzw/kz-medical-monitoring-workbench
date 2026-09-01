# R2 Batch A 第四轮独立验收：ACCEPT

日期：2026-08-10

范围：仅 `poc/medical_monitoring_ai_native_r2/` synthetic/offline Batch A 的普通调用者合同；不代表 R2 总体、真实端点、产品或生产可用性。

## 结论

ACCEPT。稳定快照未发现本范围内剩余 P1/P2。R2-B 可按 A→B→C 既定顺序解冻；Batch C 仍须等待 B 的 Codex gate。

## 决定性证据

- 全量：`236 passed in 0.16s`；
- in-memory syntax compile：12 个 Python 文件；
- R2 tree 首尾 SHA：`f473af47b2beaed35dd451cf9bac2be5fd2f9db42ccf8c81f63036af99c9042f`；
- R1 tree：`ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；
- 无 R2 cache directory；无 8911 listener。

## 独立攻击结果

- Evidence token 不在 module namespace，公开构造签名无 `_issued`；普通字段直构和 `_issued=True` 均失败；不调用 service 时状态保持 `imported`，service 正常签发可完成四步链。
- `ImmutableDict`/registry 普通属性重绑失败。
- 非零快照拒绝零 mapping coverage 与空 identity coverage；零行显式空 resolution 通过。
- domain/identity authority token 不在 module namespace，权威 factory 签名无 `_authority_token`，`_verified=True` 失败。
- facts role 拒绝 dict、空集合、混合集合，只接受验证后的 `CanonicalFact`。
- MappingResult/CanonicalFact 绑定完整 mapping digest；fact type mismatch 与 same-ID substitution 失败。
- codec、digest-only rehydration 与 README 描述一致并 fail closed。

## 残余边界

Python 同进程反射不是安全沙箱；持久化 rehydration、R2-B/C、真实模型/端点、真实数据、产品接线和生产隔离均未在本 gate 接受。
