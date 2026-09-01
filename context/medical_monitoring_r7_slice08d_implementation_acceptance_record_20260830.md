# R7 Slice-08D 三模式综合回归实现接受记录

日期：2026-08-30  
决定：`ACCEPT_R7_SLICE_08D`

## 接受结果

- 日常 full、日常 incremental、锁库前 full、核查前 fixed-total 已按 DF/DI/PL/PC × N/B/M/R/C 形成 20 格 synthetic 闭包。
- expected 由 `CellFacts` 和实际成员字节使用 stdlib-only oracle 独立重建；产品 digest、处置、变化函数被运行时 poison 后 oracle 仍可完成 20 格 expected。
- 可沿用项的 `artifact_verified`、`artifact_member_verified` 和 `reuse_reviewed` 只由 R1/R5/R6 verifier 提升；负例通过成员字节/身份/闭包篡改触发，不以布尔值自证。
- 两个确定性探针均覆盖 5 个 `PYTHONHASHSEED` × `normal/-O/-OO`，共 30 个独立 subprocess 格。
- 当前源码枚举 31 个 failure hook，全部证明事务回滚、恢复后只发布一次；SQLite 关闭重开后实际 `PRAGMA busy_timeout=10000`。
- CAS、同值重放、真实摘要漂移、可恢复重试、迟到 callback、plan blocked 和无半发布均通过。
- 08C 已接受的中文公开面和桌面视觉未被重开或改变。

## 决定性证据

- 20 格与独立 oracle：`poc/medical_monitoring_ai_native_r7/tests/test_slice08d_three_mode_matrix.py`
- 确定性与相邻保护：`poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
- 故障/恢复：`poc/medical_monitoring_ai_native_r7/tests/test_continuity_registry.py`
- 机器可读汇总：`artifacts/mm_r7_slice08d_regression_20260830/codex_combined_verification.json`
- Codex 复跑：R7 183、产品路由 86、R6 351、R5 143、R2 148，共 911 个 Python 测试，0 失败；12 个 Node 文件通过，包含 1991 项前端检查和 92 文件路径中性扫描；compileall 通过。
- 独立会商：`runs/conference/mm_r7_slice08d_implementation_acceptance_20260830/general_single_object.md`，结论 `ACCEPT_R7_SLICE_08D`，P0/P1/P2/P3/P4=`0/0/0/0/0`。
- execution audit 本体、conference validate、execution/conference review gate 均通过。带 `--require-conference` 的 execution audit 因独立 conference 使用关联但不同 task id 而报告 `conference_status=not_initialized`；未将该工具限制伪造为通过。

## 医学写作与端口边界

- 任务时段内医学写作文件新增 mtime 为 0。
- R6 旧保护基线从历史 542 文件纠正为当前文件系统 445 文件、聚合 SHA-256 `59dd4628eeedd376ab60e54806d0b9eeb3486ba444b5316fcfef8f9829863299`；只修改 R6 测试常量，未修改医学写作文件。
- 8911/5174 `connect_ex=61`，保持停止；未运行真实项目、真实模型、产品服务或浏览器。

## 接受边界

本记录只接受 Slice-08D synthetic/offline 综合回归。它不等于五个真实项目/模型医学质量、Slice-09、R7 总体、R8、生产、监管或商业化接受。

## 下一安全动作

完成 Slice-08 总体复盘，然后冻结 Slice-09A 项目级备份/恢复/导出导入合同；继续保持真实项目/模型、8911/5174、医学写作和 08C 视觉不变。
