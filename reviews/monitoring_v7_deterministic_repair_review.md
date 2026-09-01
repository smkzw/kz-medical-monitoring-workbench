# 旧 v7 确定性技术元数据修复验收

日期：2026-07-29  
结论：实现验收通过；真实运行库尚未执行修复。

## 验收范围

仅审核旧 `monitoring-listing-field-mapping-v7` 任务中，已终止为
`failed + invalid_ai_output` 且分片内全部字段均属于封闭确定性技术元数据白名单的
修复路径。

## 关键结论

- 语义字段、混合分片及 `VISIT`、`VISITNUM`、`PAGE`、`FORM`、`LINE`、`AEOID`
  等模糊字段均关闭失败，不能借该入口绕过独立 AI。
- 修复前的 job id、business key、输入 revision、输入 payload、prompt version、
  provider、requested model 和 attempts 均保持不变。
- 原失败状态、失败码、失败信息、尝试次数、原始修复输出、provenance、actor、reason
  和幂等身份写入不可更新、不可删除的独立审计记录。
- 候选写入、job 状态迁移和修复审计为同一事务，并使用精确状态 CAS。
- 修复候选仍须按既有人工候选决策流程接受，接受后可被旧 v7 mapping draft assemble
  正常消费；修复不自动确认、发布或激活字段映射。
- 路由在进入修复服务前重新计算当前冻结批次和完整 field profile 身份，批次或 profile
  漂移时拒绝。

## Codex 复核证据

- 定向组合回归：`181 passed`。
- 未调用真实修复入口，未写真实运行库，未重启 v7 API。
- 当前两个 MY009 DD 失败只有在旧队列排空、全输出 QC、数据库备份后才可执行；
  执行后仍需候选接受、草稿组装和人工字段映射复核。

## 文件身份

- `monitoring_ai_repository.py`
  `b2773eb9c31a4b8eff074f4a93f1adc0b51169dba1d4e2f919f65df9f7eff0b0`
- `monitoring_ai_service.py`
  `cd87b405122e801b624ed000090fb942f277b46f529c6b7c7bb6cfdecc6060f1`
- `monitoring_ai_router.py`
  `4eae2fa33b388ef743310515c652d7270ef2061677be3f204941fb09258ad87e`
- `test_monitoring_ai_v7_deterministic_repair.py`
  `6f5dc2d3da77dbeee8b656e6cd0322f4b41c29eba8b1cb79b4139476a5017149`

