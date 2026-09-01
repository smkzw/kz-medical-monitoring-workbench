# Codex Execution Plan: mm_r7_slice07c1_setup_diff_rules_implementation_20260829

Objective: 实施已冻结 R7 Slice-07C-1：仅用 synthetic 数据建立三模式 run options、同模式已发布基线、canonical keyed diff、项目级版本化特殊风险规则和模板到 work-unit 的同源数据合同；不实现 prepare-and-start、结果发布或前端。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 领域模块：在 R7 POC 内新增 stdlib-only run-setup 数据合同，定义三模式 options、同模式已发布基线、canonical keyed diff、项目级规则 preview/registry revision、模式模板到 work-unit 的确定性生成；只改 poc/medical_monitoring_ai_native_r7/src/mm_r7 下新模块与必要导出，不改产品 router/前端。 | `runs/execution/mm_r7_slice07c1_setup_diff_rules_implementation_20260829/worker_01.md` |
| `worker_02` | 产品 API：在现有 medical_monitoring_r7_product_router 中接入 GET run-setup/options、POST risk-rules/preview、POST/GET risk-rules，复用 canonical project/workspace/authorization/error 约定；只改该 router 及产品路由聚焦测试，不实现 prepare-and-start/结果发布/前端。 | `runs/execution/mm_r7_slice07c1_setup_diff_rules_implementation_20260829/worker_02.md` |
| `worker_03` | 验证与证据：补充 R7 synthetic fixture 和 07C-1 端到端确定性测试，覆盖三模式、全量载体增量语义、跨 hash seed、混合模式/未发布/跨项目基线、规则歧义/版本/历史不变、模板分母；只改 R7 tests/evidence/README，不改生产源码或前端。 | `runs/execution/mm_r7_slice07c1_setup_diff_rules_implementation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Accepted after Codex integration and corrective review. The initial CodeBuddy route ended with a
quota error, the MTPLX fallback was filtered by its declared >50 GB available-memory gate, and the
declared Luna fallback completed all three bounded work items. Codex reduced the domain module by
570 lines, fixed the empty-project edge, then closed independent-review findings for public rule-token
resolution, expired previews, timestamp-stable idempotency and empty snapshot selectors. Final gates:
R7 `170 passed`, product router `37 passed`, compilation and JSON receipt checks passed, protected
medical-writing aggregate and stopped-port checks passed inside the R7 suite.
