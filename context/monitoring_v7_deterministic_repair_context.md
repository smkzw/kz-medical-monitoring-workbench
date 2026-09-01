# 旧版字段映射纯技术元数据失败的受控确定性修复合同

## 目标

为已存在的 `monitoring-listing-field-mapping-v7` 运行提供一次受控、可审计、产品侧修复能力，
仅修复经验证全部属于确定性 EDC 技术元数据、且因模型未按 `source_metadata` 返回而终止的
字段块。禁止手工修改 SQLite，禁止把一般语义字段绕过独立 AI。

当前真实阻塞：

- MY009 `DD:0001-of-0003`：`DD.__FORMOID`
- MY009 `DD:0002-of-0003`：`DD.DOMAIN`

两者均为旧 v7 `invalid_ai_output`，新 v9 已从根因上加入确定性技术字段映射，但当前 v7
队列必须保留原提示词、输入修订和候选身份，完成后才能由仍运行的旧 API 正常 assemble/adopt。

## 允许条件

修复操作必须同时验证：

1. `task_type == listing_field_mapping`；
2. `prompt_version == monitoring-listing-field-mapping-v7`；
3. 当前状态严格为终态 `failed`；
4. `failure_code == invalid_ai_output`；
5. 输入修订仍为当前批次与 field profile 的精确修订；
6. 该 chunk 的全部字段均由
   `monitoring_deterministic_metadata_mapping.v1` 封闭白名单判定为确定性技术字段；
7. 不存在一般语义字段、模糊字段或需要 AI 推断的字段；
8. 当前 job 尚无候选，且未被接受、驳回或标记 stale。

任一条件不满足均关闭失败，不允许部分修复。

## 输出与审计

- 复用原 `job_id`、`project_id`、`business_key`、`input_revision_sha256`、`prompt_version`、
  requested model 和输入 payload。
- 服务端按 v7 可接受的 `listing_field_mapping_set` 候选合同确定性构造字段结果。
- 每字段使用 `source_metadata`、确定性 role、无推断 lineage，并记录：
  - `schema_version = monitoring_field_mapping_provenance_v1`
  - `provenance = deterministic_rule`
  - `deterministic_rule_version = monitoring_deterministic_metadata_mapping.v1`
  - `ai_inference_used = false`
  - `migration_reason = v7_invalid_ai_output_repair`
- 候选、原始输出、输出 SHA、状态迁移和操作 actor/reason 均写入现有审计表或新增不可变迁移
  记录；不得覆盖或删除旧失败 attempts。
- 幂等重放返回同一 completed job/candidate；相同 idempotency key 不同请求关闭失败。
- 修复后的 job 对旧 v7 assemble/adopt 路径透明，不把 job 改成 v9，也不重跑 AI。

## 实现范围

允许：

- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_deterministic_metadata_mapping.py`
- 对应医学监查 AI 测试
- 本切片 handoff / metrics / review

禁止：

- 医学写作；
- 共享 AI 配置；
- 当前运行 API 的重启；
- 真实数据库写入（实现与测试阶段）；
- 普通语义字段的确定性映射；
- P7B/P7C 规则文件和前端。

## 测试

- 精确 v7 纯技术块修复成功，旧失败 attempts 保留；
- v9、其他 prompt、其他 task、非 invalid_ai_output、queued/running/completed/stale 均拒绝；
- 混合技术/语义字段、模糊 `VISIT/VISITNUM/PAGE/FORM/LINE/AEOID` 均拒绝；
- 候选已存在、输入修订漂移、批次/profile 不匹配均拒绝；
- 幂等重放与 idempotency 冲突；
- 修复结果能被现有 v7 mapping draft assemble 接受；
- SQLite 迁移幂等；
- 组合回归不影响 v9 正常确定性映射和独立 AI 路径。

## 运行边界

只有在两个项目旧 v7 队列全部排空、Codex 完成输出 QC、测试通过并记录备份后，才允许对
真实 MY009 两个失败 job 调用该产品修复入口。调用后仍须由旧 v7 API 正常完成
assemble、人工字段 QC、确认与激活，不自动医学确认。
