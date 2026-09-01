# R2 Batch A 独立验收：VETO

日期：2026-08-10

范围：仅 `poc/medical_monitoring_ai_native_r2/` Batch A；只读独立复核，不代表 R2 总体。

## 结论

当前快照 VETO。R2 全套 `146 passed`，目标文件首尾 SHA 稳定，R1 全树摘要首尾均为 `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`，但测试未覆盖下列 fail-open 合同。

## 必须修复

1. P1：`default_registry()._by_name` 仍是可变字典，可绕过 `register()` 和 `_frozen` 直接插入 schema。
2. P1：dataclass 只浅冻结；scope/structure/payload/coverage 等嵌套 dict/list 可在构造后修改，使公开 hash/ID 与重新计算结果失配。
3. P1：source/snapshot 只校验调用方提供的 64 位字符串；没有接收/核验实际 bytes/canonical full rows 的权威构造入口。RecordIdentity 的 algorithm digest、CanonicalFact 的 source/snapshot/mapping/identity 引用同样仅做字符串形态检查。
4. P1：AcceptanceEvidence 未绑定 project/snapshot/source/mapping/algorithm/actor/confidence；任意 actor 可用自报布尔值走到 baseline eligible，低置信度 critical mapping 没有进入 gate。
5. P2：非法 skip 在 `_check_forward()` 抛出前未追加 blocked/rejected decision record。

## 已通过但不足以接受的证据

- fresh envelope 同逻辑内容同 hash；
- record/risk 跨项目 ID 分离；
- 普通缺证据 transition blocked 会保持状态并追加记录；
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests`：`146 passed in 0.07s`。

## 处置

原 worker 初始实现后已完成两次同会话修复，仍未通过独立 gate。依据执行路由，在失败验收后切换到声明 fallback 做 fresh-context 修复；B/C 继续冻结。
