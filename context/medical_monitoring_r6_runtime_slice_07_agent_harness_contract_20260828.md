# R6 runtime slice-07：Agent Harness adapter 合同（冻结稿）

日期：2026-08-28  
状态：实现前冻结  
范围：synthetic/offline 合同与隔离 Harness smoke；不改产品服务、前端、医学写作或真实项目。

## 1. 目标与边界

本纵切只建立医学监查独立 AI 的 `ExecutionProfile -> Harness adapter -> invocation receipt`
公共边界。模型身份、调用参数、完整性、覆盖度、原始输出和恢复语义不得进入
`ModeOutput`、风险、Profile、Timeline、Query 或报告等医学业务对象。

允许新增：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_agent_harness.py`
- 既有 `test_challenge_matrix.py`、`test_report_review.py`、`test_report_bundle.py`、
  `test_mode_output.py` 仅允许新增上述 3 个 slice-07 路径到 create-only allowlist；
- `poc/medical_monitoring_ai_native_r6/evidence/r6_agent_harness_runtime_receipt.json`
- 本合同、执行/复核记录，以及 POC `README.md` / `__init__.py` 的必要邻接更新。

禁止：产品 `services/`、`frontend/`、医学写作文件、真实项目、8911/5174、浏览器、OCR、
医学结论、自动 fallback、凭据值落盘。

## 2. 模型身份与别名

用户配置名称与当前 OMP 18.0.7 运行选择器分开保存，冻结后不得静默改写：

| profile | 用户配置名称 | OMP effective selector | effort | 角色 |
|---|---|---|---|---|
| `monitoring_harness_default_mtplx_qwen38_medium` | `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality` | `mtplx/Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality` | `medium` | 默认 |
| `monitoring_harness_deepseek_v4_flash_max` | `deepseek/DeepSeek V4 flash` | `deepseek/deepseek-v4-flash` | `max` | 用户明确选择的替代能力 |

别名映射属于 adapter registry，不属于医学对象。未知别名、provider/model/effort 不一致、
或目录不支持所需 effort 时失败关闭。DeepSeek 是可选 profile，不是 MTPLX 的自动 fallback。

## 3. ExecutionProfile 冻结顺序

有效配置按以下优先级合并：全局默认 -> capability/Agent override -> project override ->
Run 冻结副本。只允许已登记字段覆盖；`None` 表示继承，空字符串不是删除指令。

冻结副本至少包含：

- `profile_id`、`profile_revision`、`capability_id`；
- requested provider/model 与 effective selector；
- `reasoning_effort`、`timeout_seconds`、`allowed_tools`；
- `context_isolation`、`credential_ref`、`adapter_id/version`；
- `fallback_profile_ids`（默认空；本纵切禁止 adapter 自动执行）；
- canonical `execution_profile_id` 和 `execution_profile_digest`。

任何 Run 内变更都必须新建冻结副本；旧 Run 不随活动配置漂移。

## 4. AdapterContract

`omp_print_v1` 必须提供：

1. `catalog_snapshot`：仅返回模型公开目录字段，不返回环境值或密钥；
2. `preflight`：检查 executable、selector、effort、工具白名单和超时；
3. `build_start_command`：参数数组，不经 shell；显式 `--model`、`--thinking`、`--mode json`、
   `--print`、`--no-session`、`--no-skills`、`--no-rules`、`--tools`、`--max-time`；
4. `invoke`：stdin 传 prompt，stdout/stderr 分离，按超时终止并形成 receipt；
5. 本 slice 的 print invocation 不声称 session resume。若上层请求 `continue/resume/cancel`
   而当前 invocation 不具备相应句柄，必须返回 `unsupported`，不得伪造成功；
6. 不调用 shell，不插入 API key，不从响应文本推断模型身份。

## 5. Invocation receipt

receipt 必须包含：

- invocation/profile/adapter/input 的稳定身份与 SHA-256；
- requested/effective selector、effort、allowed tools、开始/结束时间和耗时；
- `state`: `complete | partial | truncated | failed | timed_out | not_evaluable`；
- `parse_state`: `parsed | unparsed | invalid`；
- `expected_units`、`produced_units`、`missing_units`；
- stdout 原始字节的保存路径和 SHA-256，stderr 仅保存净化后的摘要；
- exit code、failure reason、fallback 使用情况（本 slice 恒为 false）；
- `analysis_complete`。

只有 `state=complete`、`parse_state=parsed`、零 missing units、profile/adapter/input 身份一致时，
`analysis_complete=true`。partial/truncated/failed/timed_out/not_evaluable 均失败关闭。

## 6. 用户进度投影

面向医学监察员的投影只包含中文业务节点、已完成/总节点、当前工作和结果可用性。
不得显示 provider、model、selector、effort、adapter、attempt、stdout/stderr、hash、路径、
内部错误码或日志标签。本纵切只提供纯函数投影，不进入前端。

## 7. 验收矩阵

### 离线确定性

- 默认 profile 精确映射到 MTPLX canonical selector + medium；
- DeepSeek profile 精确映射到 canonical selector + max；
- 合并/冻结/ID 在 hash seed 0/1/42 与 `-O/-OO` 下稳定；
- 未知别名、非法 effort、空 capability、非法 timeout、工具越权失败关闭；
- command 为 argv，无 shell，prompt 不出现在 argv；
- complete/partial/truncated/failed/timed_out/invalid JSON/coverage gap 门禁正确；
- 无自动 fallback；无 secret value 序列化；用户投影无内部术语。

### 受控真实调用

- 使用 synthetic non-medical prompt，各真实运行一次 MTPLX medium 与 DeepSeek max；
- 固定 `--no-session --no-skills --no-rules`，只允许 `read` 工具且 prompt 不要求工具；
- 保存最小 raw output receipt，不保存凭据；
- 真实调用成功只能证明 adapter 接入，不证明医学质量、产品集成、R6/R7 或真实项目验收。

### 相邻保护

- R6 全量 POC 测试继续通过；
- 医学写作文件数/aggregate 不变；
- 8911/5174 无 listener；
- `services/`、`frontend/` 和真实项目无修改。

## 8. 完成判定

只有代码、离线测试、两条真实模型 smoke、相邻保护、独立复核和 Codex 验收全部通过，
方可记录 `ACCEPT_R6_RUNTIME_SLICE_07_AGENT_HARNESS_ADAPTER_LIMITED`。该判定仍不代表产品接入、
医学结论或真实项目可用。
