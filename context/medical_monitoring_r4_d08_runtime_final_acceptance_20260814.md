# R4-D08 synthetic/offline runtime 最终接受记录

日期：2026-08-14  
状态：`ACCEPT_D08_RUNTIME`

## 接受范围

接受 `poc/medical_monitoring_ai_native_r4` 内 D08 多表医学逻辑与数据质量 synthetic/offline 纵切：typed 合同校验、按合同顺序 fail-closed 的完整性门、跨表关系/时序/身份/基数/传播评价、renderer-neutral 风险/中文三分句 Query/Patient Journey 投影，以及冻结 233-case oracle 的测试适配。

本接受不等于 R4 总体、D09/D10、R5/UI、产品集成、真实项目/患者数据、真实模型端点、生产或医学写作子系统接受。

## 最终不可变快照

- `d08_contracts.py`：`8d8fb6727a878642b361b444edb110b7283ef11b41adc1cb3c561152699225ad`
- `d08_evaluator.py`：`0d584064143263409a3e282a087c4931a4cfb4a1d832556836bc9a71ad23e43b`
- `d08_projection.py`：`2764c737e906ad1f947b8785d66c03c2989c0c455eb6bd37bfb3a9f502098c9b`
- `mm_r4/__init__.py`：`70a7f42c1e8fd268a346d396d86f6f10cb07810852864d2848a42b96413afd3b`
- `test_d08_adapter.py`：`b8e3b63290bcf4a4ce7ab8d8ca978f9e237fac8deb462966feb3ba48e6d66347`
- `test_d08_challenge_matrix.py`：`bd61e7ad3a67d83509930c58988480f46d0176f3116af5c55de99f18483dfc78`
- `test_d08_runtime_contract.py`：`21683deeb4c00eb81a16ab8c9d6189347b647baa025682e1074bbb48e3e2771d`
- `test_d08_verifier_probes.py`：`5d4ed184fe561a54702cc9e165a39fa6342bff6d5d910836314614de33313a25`

冻结合同与制品保持原接受哈希：contract `ff3d3a1b…d64`、catalog `d3cd694b…82c`、oracle `a40cbb50…ac9`、registry `bf0142b3…a9a`、generator `63d610e8…100`、generator test `0b4e7c1d…906`。

## 决定性证据

- D08 聚焦：`186 passed`；冻结 233-case exact oracle：`1 passed, 9 deselected`。
- 全 R4：`3843 passed`；R1-R3 相邻回归：`1264 passed`。
- 冻结 generator：`54 passed`；Ruff 与 Python compile 通过。
- TCP 8911：`STOPPED`；未启动服务、未运行真实项目或患者数据、未触碰医学写作子系统。
- 独立 Luna 原会话 `019fff98-9f85-7ec2-ba80-63be3ef6ab1e` 最终报告：`runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup4_20260814.md`，SHA-256 `7b0ec9d75a7c1cd3d9d612f7325133b35478ced7a72c19a7b61a0bc3cb5630ab`，结论 `ACCEPT_D08_RUNTIME`，当前范围无剩余 P0-P4。

## 审阅纠偏轨迹

独立审阅连续四次保留 `REVISE_D08_RUNTIME`，累计发现并复现：全局完整性门遗漏、传播/时序/反向基数错误、可见性泄漏、coverage/authority/hash/n-ary/RMB 边界、上限策略、stage 顺序、handoff 重复、规则身份合成、投影非确定性、传播交集未闭合、未解析 raw link 假阴性等。所有缺口均在当前快照中修复并由原会话重新验证；历史 REVISE 报告作为不可覆盖证据保留。

## 下一安全动作

按 R4 顺序先冻结 D09“中心重复模式与系统性风险”的独立合同、typed 输入/输出、分母/coverage/cutoff/分层/owner 边界和挑战矩阵，再决定 synthetic/offline 实施。D09 合同接受前不进入 D09 runtime、D10 或 R5/UI；8911 继续停止，不运行真实项目，不扩大安全设计/测试。
