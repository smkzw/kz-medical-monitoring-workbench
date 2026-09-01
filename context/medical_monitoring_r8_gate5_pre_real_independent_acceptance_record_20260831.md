# 医学监查 R8 G5 预真实联合独立接受记录

日期：2026-08-31  
状态：`PRE_REAL_INDEPENDENT_ACCEPTED`  
范围：当前 G2 synthetic runtime、G3 通知决策、修订后 G4 synthetic 通知与 §15.4 程序的联合证据接受

## 接受基础

- G5 合同：`context/medical_monitoring_r8_gate5_pre_real_joint_acceptance_contract_v0_1_20260831.md`。
- 已审 evidence manifest：
  `context/medical_monitoring_r8_gate5_pre_real_evidence_manifest_v0_1_20260831.json`，
  21/21 path/SHA 匹配，文件 SHA-256
  `c1e57388102a57d2860942684b1017d1a4119c886b2d8a141f9101f05072c3cd`。
- 第 1 轮纠偏意见：
  `reviews/medical_monitoring_r8_gate5_pre_real_independent_review_round1_20260831.md`。
- 同一独立会话第 2 轮接受意见：
  `reviews/medical_monitoring_r8_gate5_pre_real_independent_review_round2_20260831.md`。

## 处置

1. 第 1 轮两项 P1 均已在当前已审快照关闭：旧/乱序 terminal revision 和失效跳转目标
   fail closed；§15.4 发布 manifest 为可独立运行的 R1-R7 Python 依赖闭包。
2. G4 synthetic/offline `SYNTHETIC_15_4_PROCEDURE_READY` 接受在本记录中恢复；原 G4 文件保留
   `REVISED_CANDIDATE` 字样作为被审快照，不再原位改写，避免使已核验 G5 manifest 失效。
3. 同一独立审阅会话最终 `P0=0, P1=0, P2=0, P3=0, P4=0`，处置 `ACCEPT_G5`。
4. G5 通过只允许进入 G6 合同冻结，不等于 G6 已实施或接受。

## 决定性证据

- G4 聚焦：`73 passed`。
- 扩大 G2/R7 相邻：`210 passed, 3 non-failing warnings`；独立复核指定子集 `118 passed`。
- normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42`：9/9 digest 一致：
  `aec859cf59e4d3bac812f45293dff6175f4117df1f7b985fffc9f8e28d659475`。
- 发布 manifest：157 文件，digest
  `33fa98a46b8b0306839fd8dc7b6e86e628b002c01e4903c756a6f2db273a3263`。
- 独立 release-root 13/13 passed，107 个相关已加载模块全部来自隔离副本。
- `py_compile` 通过；8911/5174/8984 均停止；医学写作只读当前指纹
  `ba4975e20315482607bee43693d5c775c415fc2547df2f1a403348f205e5a018`。

## 禁止扩大

本接受不证明真实通知送达或用户实际看到、真实 §15.4、真实项目、真实模型或产品 harness、
产品浏览器、医学质量、G6-G15、R8 总体，也不构成生产、商业化、监管或合规声明。

## 下一安全动作

先冻结独立 G6 synthetic `ego(lite)` 受众验收合同，明确实际本地应用入口、synthetic fixture、
mock/recorded adapter、synthetic binding、视觉/交互/中文用户语言与 fail-closed 验收矩阵。
合同冻结前不启动应用或浏览器；G7 前不访问真实项目，G8 前真实项目语义不进入模型。
