# R7 Slice-09C 实现接受记录

日期：2026-08-30  
状态：`ACCEPT_R7_SLICE_09C_SYNTHETIC_OFFLINE`

## 接受对象

按冻结合同 v0.2（SHA-256 `834da09de169dba4cf6a00d9c369a479fcdbe28537389870e59921443f8af6de`）完成根级项目审计链、operation 同事务投影、只读项目核验、09A/09B 三入口恢复接线、最小中文结果 DTO 与有界技术日志。

## 决定性证据

- 聚焦 09C：`37 passed, 2 warnings`；15 格 hash/优化级别/TZ/locale：`15 passed`。
- 全 R7：`526 passed, 19 warnings`；R1：`327 passed`；compileall/py_compile 通过。
- 8911、5174、8984 均无监听。
- 独立会商首轮发现并驱动修复；同一 session 第二轮逐项复核后返回 `P0=P1=P2=P3=P4=0`，无 fallback。

## 明确解释

1. 根审计链已被证明损坏时，核验器直接返回“发现异常”且不追加新的验证事件；在失真链上继续追加会制造误导性连续性。所有从有效根链开始的调用仍追加成对验证事件。
2. 8 KiB 上限针对完整序列化 JSONL 行，包含 `segment_bytes` 与换行；超限整行丢弃，不产生截断记录。

## 已知非阻断边界

- startup scan 为 best-effort：09A 只报告公开恢复态，不重放文件系统切换；09B 仅通过已接受 migration runner 恢复；triage、failed/retry-only 不自动执行。
- SQLite 指纹按逻辑 schema/row 内容计算，排除生成型 `meta.store_id` 与 `-wal/-shm`；这是 synthetic/offline 确定性边界，不是长期数据库性能结论。
- FastAPI startup API 存在弃用警告，当前不影响功能验收。

## 范围边界与下一动作

本接受不覆盖真实项目、真实模型、浏览器视觉、09D 性能、Slice-09/R7/R8 总体、生产或医学写作。下一动作先冻结 09D 容量/性能/长运行恢复合同，并将跨研究、跨药物、跨疾病和跨 listing 结构的反过拟合门写入合同；真实资料只作为只读泛化挑战，不得形成硬编码。
