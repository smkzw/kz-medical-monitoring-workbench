# 医学监查跨模块 action / policy-gap 盘点

日期：2026-08-04（Asia/Shanghai）  
范围：P10 关闭状态下的离线路由审查；不代表生产启用或运行态授权。

## 判定原则

只在现有 action 的业务语义、资源范围和写入风险均精确匹配时复用。
没有精确 action 的路由保持当前既有 fail-closed/策略拒绝边界，待单独的
action、角色、项目范围、再认证和审计合同明确后再实施。不得把
`READ_MONITORING`、`READ_SOURCE_EVIDENCE` 或 `INTAKE_BATCH` 当作跨模块万能
权限。

## 已完成精确保护

| 路由 | 现有 action | 结论 |
|---|---|---|
| `/risks`, `/data-batches` | `READ_MONITORING` | 已保护；旧 catalog 读面 |
| `/sources`, `/source-contents`, `/source-manifest` | `READ_SOURCE_EVIDENCE` | 已保护；来源目录、投影和 manifest |
| `/module-catalog`, `/shared-protocol-facts` | `READ_SOURCE_EVIDENCE` | 已保护；来源派生的只读 metadata/facts |
| 风险处置 POST | `CHANGE_RISK_DISPOSITION` | 已保护；服务端 actor、再认证/签名证据边界已覆盖 |
| source content validation confirm | `VALIDATE_SOURCE_REVISION` | 已保护；服务端 actor 已覆盖 |

## 保持 policy gap 的路由

| 路由族 | 实际资源/副作用 | 为什么不复用现有 action | 后续所需合同 |
|---|---|---|---|
| `/dashboard` | 汇总 dashboard、多个模块摘要和风险计数 | 不是单一医学监查资源；`READ_MONITORING` 会误授其他模块 | 组合 dashboard read action，或按模块拆分投影与 action |
| `/workbench-inbox` GET | 跨模块 handoff、通知、未读状态 | 当前 action 矩阵没有 inbox read；source/monitoring read 均不精确 | `READ_WORKBENCH_INBOX`、项目范围和 actor 显示规则 |
| `/workbench-inbox/{item}/actions` | `MARK_READ` 持久化 inbox 状态 | 不是风险处置，也不是普通监查读 | inbox mutation action、并发版本和 server actor |
| `/ai-runs` GET/`{run_id}`/artifacts | AI run 状态、结果和 artifact | `REVIEW_AI_CANDIDATE` 是候选审阅/采纳，不是 run read；source read 也不等价 | `READ_AI_RUN` 与 module/project scope、artifact disclosure 规则 |
| `/ai-runs/from-sources` POST | 触发 AI 执行并读取已登记 sources | 不是候选采纳；`RUN_DETERMINISTIC_RULES` 仅确定性规则运行 | AI execution action、provider/runtime gate、source-token/CAS |
| `/sources/*` registration/upload/local candidate | 新建或登记 protocol/listing/raw/local source | `INTAKE_BATCH` 只描述 monitoring batch intake；`VALIDATE_SOURCE_REVISION` 只确认内容核验 | source registration/import action、路径/上传审计和 CAS |
| `/eligibility/source-admission/refresh` | 用配置路径注册 protocol 与 subject bundle | 不是 batch intake，也不是 source content validation | eligibility source admission action 与路径访问审计 |
| `confirm-full-snapshot` / `transition` | 改变 batch lifecycle 状态 | 现有 intake/validation actions 不能精确表达生命周期确认/迁移 | batch lifecycle action、再认证、CAS/版本和 B6/C14 复核 |

## 安全边界

- B6 `pending_review`、C14 `blocked_pending_b6_review` 不因本盘点改变。
- 8911、5174、8910、4173 必须保持停止；不启动服务、浏览器、provider、
  API login、真实项目、运行库或外部 agent。
- 下一次用户要求解除边界时，先复核中断的 Kimi 修改，再按四项纠偏、
  聚焦/相邻回归和 Codex review 顺序推进。
