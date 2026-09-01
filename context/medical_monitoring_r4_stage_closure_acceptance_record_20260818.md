# 医学监查 R4 阶段总体关闭接受记录

日期：2026-08-18  
结论：`ACCEPT_R4_STAGE`  
范围：`poc/medical_monitoring_ai_native_r4` 的 synthetic/offline D01–D10 风险 Agent 子图。

## 阶段结论

R4 已由与实施上下文隔离的独立 verifier 在当前稳定文件快照上接受，当前范围无 P0、P1、P2、P3、P4。该结论关闭 R4 阶段门并仅解锁 R5 的合同与实现工作，不表示 R5、产品界面、真实项目、真实模型、生产或商业使用已完成。

## 初审阻断及关闭

1. 共享参考基线和多模型隔离分析闭环：已新增 typed baseline/assessment/gap/attempt/verification/adjudication 合同与确定性 offline runtime；覆盖 ensemble 0/1/N、worker 与 adjudicator 分离、验证先于裁决、高风险冲突不可隐藏。
2. D06 固定合成身份分流：已删除 `SYN-WRONG-SUBJECT` 和 `CANONICAL_SYNTHETIC_SCOPE` 生产判定分支，改为每条 fixture 的 typed authority/scope binding，219 个冻结叶保持不变。
3. 公共 coverage matrix 漂移：已恢复历史差异、分类唯一 C 类修订并显式勘误重冻结；当前 SHA-256 为 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`。
4. Ruff/D07 pin：5 个 F401 已移除；D07 接受 oracle pin 更新为 `e0e244d03d06a30127daeb71769733439e8620d62722b78074eb2e2068a3f4e9`。

## 独立负向探针关闭

- N 路 worker 必须使用互异 binding/session/context；同一模型可在独立 binding/session 下合法复用。
- identity、model/source/rule version、日期、单位、来源 locator 与证据 digest 均对独立 typed authority 实值核验，缺失即 fail-closed。
- 实际 `WorkerAnalysisOutput` 重新计算 canonical digest，并同时绑定 attempt 声明与 authority digest。
- worker output mapping key 必须等于 `attempt_id`；每个 worker 对每个 baseline item 至多一条 assessment；同一 worker 内 finding/gap ID 必须唯一。

## 决定性证据

- ensemble focused：`116 passed`
- D06 focused：`920 passed`
- D08–D10 adjacent：`177 passed`
- D07–D10 artifact：`385 passed`
- full R4：`4396 passed`
- Ruff：通过
- 内存编译：94 个源文件通过
- D06/D07/D09/D10 generator、oracle、authority、verifier 检查：全部 exit 0
- 18 个冻结 D06–D10 JSON SHA：全部匹配
- 端口 8911：无监听

## 稳定实现锚点

- `ensemble.py`：`beb5c1ab8f3db5c42e780e31312e057e1fe95298ee351e28b0602fb8dffa608a`
- `ensemble_contracts.py`：`fb429ea3c854291eb2a120bd3a745eef155370bd79932c91e4fcab212ce84c40`
- `test_ensemble_runtime.py`：`ba517e231406701b18c70932db42985f2de747d0f50676cdc7cb3509effb77f5`
- `test_ensemble_contract.py`：`fbe0b96dafda1e837f62dd592420b762d6026aabb76b10318fbca08549c78eb5`
- `src/mm_r4/__init__.py`：`deeae440d6a75ce0a6c519c9ec79539b3a4225fffe9b234ecc58443beb7b3f7d`

## 边界与下一安全动作

- 未启动服务、浏览器或 8911；未运行五个真实项目或真实医学分析模型；未修改医学写作子系统。
- 不把 synthetic/offline 结果宣称为正式临床结论或商业化能力。
- 下一步按 v1.1 计划进入 R5：先冻结风险驾驶舱、中心图谱、Subject Workspace/Patient Journey 的用户任务与数据/交互/视觉验收合同；实现过程继续保护医学写作，且不扩展安全性设计或测试。
