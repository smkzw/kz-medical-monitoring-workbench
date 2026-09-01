# 最小三事实竞品检索门 Codex验收

## 结论

接受该源码分支。用户只需提供试验药物、适应症和研究分期即可保存项目草稿并启动竞品检索；ClinicalTrials.gov疾病词、研究目的、靶点、总体设计和PICOS等由系统调研/AI预填后再由用户确认，不再作为检索启动硬门。

## 主会场验证

- authoring、prefill、synopsis、greenfield后端：`154 passed`
- 前端医学写作合同：`99 passed`
- 原子composite-adopt及相邻API合同组合：`123 passed`
- Vite生产构建通过。

## 合同修订说明

旧前端测试要求恢复`LOW_RISK_BATCH_PREFILL_FIELDS`和逐字段循环调用；这与已经落地的原子`prefill-package/adopt-composite`接口冲突，并会重新引入部分成功、部分失败和重复提交风险。测试已改为验证：

- 一次原子composite请求；
- package revision并发控制；
- 409冲突后只刷新、不自动重复采用；
- 项目切换隔离；
- 三事实检索和适应症回退；
- ClinicalTrials.gov英文疾病词仅为可选优化字段。

这不是弱化测试，而是把过期实现细节替换为更强的当前业务与原子性合同。

## 未完成门

- 统一重启后必须用UC真实项目从三事实开始验证检索计划、快照、进度和失败恢复。
- 完整PICOS和方案正文生成仍执行严格确认门，不因最小检索门而放宽。
