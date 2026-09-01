# 医学监查 R4-D10 runtime 最终验收与无损暂停记录

日期：2026-08-18  
状态：`ACCEPT_D10_SYNTHETIC_OFFLINE_RUNTIME_PAUSED`  
暂停边界：D10 synthetic/offline runtime 已接受；未进入 R4 阶段总体验收、
R5/UI、8911/服务、真实项目/模型、产品或医学写作。

## 已完成与接受

1. **Authority/artifact + Worker01**：312-case authority 污染已声明重开并完成
   generator-first 修订；typed contracts、test-only adapter、deterministic evaluator
   与五门 fail-closed 已独立接受。记录：
   `context/medical_monitoring_r4_d10_authority_correction_worker01_acceptance_20260818.md`。
2. **Worker02**：renderer-neutral 投影、中文受众面、分层计数、risk/hotspot、
   Query、visibility/deep-link 与 R2 handoff 已独立接受。两次被拒绝的
   hidden-site、wrong-scope exact pair 和虚假重签证据均已闭环。记录：
   `context/medical_monitoring_r4_d10_runtime_worker02_acceptance_20260818.md`。
3. **Worker03**：D10 公共导出、replay/order/anti-overfit、mutation、verifier
   probes、fresh import/static closure 与全量回归已完成。独立 reviewer 首次
   拒绝 projection 仅半重签；修复后对完整 projection core content hash 与
   projection ID 重签的篡改，validator 唯一以
   `project_projection_not_exact_authoritative_rebuild` 拒绝。最终 reviewer 返回
   `ACCEPT_WORKER03`，并明确在 Worker01/02 及 artifact 前置下可接受整个
   synthetic/offline D10 runtime。

## 最终稳定 SHA-256

- `src/mm_r4/__init__.py`  
  `f6e714aee9515b501b6679fa5f1f27416353e78c9e4b44d393b2ca15c79ecfc0`
- `src/mm_r4/d10_contracts.py`  
  `19a3b278e3d2e587be0dab5411827eaa32611e2ff95a1424cbc83c27194bdd78`
- `src/mm_r4/d10_adapter.py`  
  `d4e81606e660089166f89a4c87584e8d2d728679897f93c4b0eac60e8d1c3db7`
- `src/mm_r4/d10_evaluator.py`  
  `204fe88f3b4a5aeeaa8205e57e841f594974767785612eeeff655e7482af96af`
- `src/mm_r4/d10_projection.py`  
  `14af6237f2052ff323cc12cb9760aad8ab91c93b594d89d04e1b88fd5e43e017`
- `tests/test_d10_adapter.py`  
  `cde15796351db460d92098447498b6c52118024ce6b2a2a7db1cac43b7e8604f`
- `tests/test_d10_runtime_contract.py`  
  `21808659a85bbda82a4219ec33ed83dc420a5e201d494857c0e438e69cc74a2f`
- `tests/test_d10_projection.py`  
  `f79b71210ffc9c7c4250570b91c7d22dce4b01738cb455980f66c446505369a1`
- `tests/test_d10_mutation_suite.py`  
  `8dca7749fc0ea66be12f30c41c39f01ca92454f75931f0a504dbec71dd0f5091`
- `tests/test_d10_replay.py`  
  `525db941d7312564887fec2bfff97fd08ee36080235f6d8457fa8d51e0091908`
- `tests/test_d10_runtime_closure.py`  
  `a0423b3351d586b43123d3de5e5fbe1dd873dd5569d81ec8e71822d18da2fa24`
- `tests/test_d10_verifier_probes.py`  
  `66b00287b7eaf6e857f259cf9170c1b7507b49049014bde40d458c48ad462a2a`

## 最终决定性证据

- D10 完整测试：`182 passed, 11225 subtests passed`。
- D10 artifact：`107 passed, 10 subtests passed`。
- D09 全量相邻：`243 passed, 33 subtests passed`。
- R4 完整测试：`4268 passed, 11258 subtests passed`。
- 五个 Worker03 变更文件 Ruff `All checks passed`；12 文件 compile 通过。
- 外部 immutable anchor checksum 通过，anchor 为只读 `uchg`。
- 最终独立 reviewer 对 12 文件首尾 SHA 确认零漂移，返回
  `ACCEPT_WORKER03`。
- 8911 无监听；未启动服务、未运行五个真实项目、未调用真实
  模型、未触及医学写作。

## 明确未完成

- 本记录不等于 R4 阶段总体独立验收；R4 D01-D10 的整体需求—实现
  覆盖、跨域一致性、ensemble 1/N、高风险不隐藏和 Query 边界仍需单独
  总体关闭评审。
- R5 风险驾驶舱/中心图谱/Subject Workspace、Patient Journey UI、8911 服务、
  真实项目/模型、产品和医学写作均未验收。

## 下一恢复动作

1. 完整重读最新全局/工作台 `AGENTS.md`、System Design v1.1、R0-R8
   实施计划与本暂停记录。
2. 只读复核上述 12 个 SHA、immutable artifact anchor、8911 停止与医学写作
   隔离边界。
3. 先执行 **R4 阶段总体关闭评审**：按 R4 完成证据审计 D01-D10 覆盖、
   跨域合同、多模型/ensemble、Query、风险分级、反证、生命周期与独立 QC；
   不直接跳入 R5。
4. 仅在 R4 总体独立接受后，再解锁 R5 风险驾驶舱、中心图谱与
   Subject Workspace 的用户面设计/实施。

## 执行材料归档

- 本轮 prompts、runner reports 与 logs 已通过任务级 cleanup guard 可恢复归档至
  `archives/execution/medical_monitoring_r4_d10_runtime_20260817/`；原
  `prompts/execution`、`runs/execution`、`logs/execution` 下对应任务目录已清空。
- 该操作仅移动本轮过程材料，未删除源码、测试、验收记录或医学写作文件。

当前为无损暂停点；8911 必须保持停止。
