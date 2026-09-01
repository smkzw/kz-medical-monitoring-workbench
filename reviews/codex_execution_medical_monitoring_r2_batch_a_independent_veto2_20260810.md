# R2 Batch A 第二轮独立验收：VETO

日期：2026-08-10

范围：仅 `poc/medical_monitoring_ai_native_r2/` Batch A；独立 reviewer 对首尾 SHA 稳定的候选快照做只读复核，不代表 R2 总体。

## 结论

当前快照 VETO。既有 `221 passed`、语法编译、R1 冻结摘要和 8911 停止状态均通过，上一轮记录的攻击路径也已关闭；但独立复核仍复现 4 个 P1 和 2 个 P2 合同缺口。Batch B/C 继续冻结。

## 必须修复

1. P1：`ImmutableDict._m` 可被普通属性赋值整体替换；冻结后的 `SchemaRegistry._by_name` / `_frozen` 也可整体重绑，默认 registry 可因此接受 rogue schema。
2. P1：非零快照可绑定 `record_count=0` 的 mapping result 和空 `IdentityResolution`，仍到达 `baseline_eligible`；绑定未证明逐行映射与身份解析覆盖。
3. P1：`mm_r2.domain._VERIFIED` 是可直接取得的模块属性，可用于直接构造看似权威的摘要对象。
4. P1：`payload_role="facts"` 可封装任意候选字典；facts 角色未强制绑定 `CanonicalFact` 权威对象。
5. P2：`CanonicalFact.from_bundle` 只接收 `MappingResult`，未绑定 `MappingDefinition` 的语义；例如 AE 事实可错误绑定到无关 DM 字段映射。
6. P2：README 同时声称存在和不存在 `_rehydrate_verified`，与当前 fail-closed 实现矛盾。

## 已通过但不足以接受的证据

- 全套 Batch A：`221 passed`；
- in-memory syntax compile 通过；
- 目标文件首尾 SHA 稳定；
- R1 tree digest 保持 `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；
- 无 8911 listener，无 R1 import、网络、subprocess 或凭据访问；
- 上一轮 mutable backing、缺 mapping/identity、可变 identity 集合、语义指纹碰撞、digest-only rehydration、重复 result ID、跨项目 resolution 和 ambiguity 排序缺陷均已关闭。

## 处置

Codex 只在隔离 R2 namespace 内做同根、最小修复并补负向回归；修复后运行聚焦、全量、语法、缓存、R1 摘要和 8911 停止检查，再把稳定 SHA 交给独立 reviewer 复验。Batch B/C 在独立 ACCEPT 前保持冻结。
