# R2 Batch A 第三轮独立验收：VETO

日期：2026-08-10

范围：仅稳定 SHA 的 synthetic/offline R2 Batch A；只读独立复核。

## 结论

VETO，仅剩 1 个 P1：`mm_r2.acceptance._EVIDENCE_OK` 仍是可直接读取的模块属性，且 `AcceptanceEvidence` 构造签名暴露 `_issued`。普通调用者可读取真实 token，伪造绑定当前 fingerprint/派生属性的 evidence，不经 `AcceptanceService.evidence()` 走完整条链并到达 `baseline_eligible`。

## 已通过

- 前一轮六项否决全部关闭；
- 全量 `235 passed`、in-memory compile 12；
- R2 tree 首尾 SHA 稳定为 `35d47e83413060aaa9f1861e3eaabfdba68a811e12a3e8d579017b5c8ebf809b`；
- R1 tree 保持 `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；
- 无缓存、无 8911 listener。

## 处置

只修复 Evidence 签发边界：删除模块可达 token，公开构造入口无 `_issued` 且始终拒绝，service 通过闭包保留的内部构造能力签发；补真实 token 攻击回归后重新冻结独立复验。Batch B/C 继续冻结。
