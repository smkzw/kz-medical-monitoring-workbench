# 医学监查 P10：Capability-aware Mapping Activation 最小切片实施记录

## 1. 目标与边界

本切片实现字段映射的双层质量合同：

1. 正式映射真实性门：来源、身份、CM/IP 边界、标准编码声明和确定性派生必须真实、
   唯一、可复核；
2. 医学监查能力门：局部前置血缘不足只限制受影响能力，不阻断原始数据查阅及无关能力。

未修改 `monitoring_ai_worker.py`、`monitoring_ai_service.py`、
`monitoring_ai_repository.py`，未读写或迁移正在运行的 runtime DB，未增加通用
override。

## 2. 已实施合同

### 2.1 语义质量报告 v2

- 报告 schema 升级为 `monitoring_mapping_semantic_quality_v2`；
- 固定首版 10 项能力目录及 manifest SHA-256；
- finding 增加 `affected_capability_ids`；
- 报告增加 `activation_disposition`、manifest 身份和完整能力状态快照；
- `status=blocked` 只由 `global_blocker` 产生；
- 仅有 capability blocker 时结论为
  `pass_with_warnings + activate_restricted`。

### 2.2 全局阻断保持失败关闭

以下情况仍拒绝 confirm/activate：

- 来源字段覆盖、来源/profile/revision/身份链冲突；
- CM 与试验药物事实混淆或互斥试验药物动作被虚假合并；
- 声称 `standardized_coded` 却缺少明确编码体系或版本；
- 声称 `deterministic_derived` 却不可复算；
- capability finding 无法闭合映射到当前 manifest。

### 2.3 局部能力限制

- 来源编码值缺少可核验体系/版本：禁用标准编码规则，Timeline/Profile 保留来源值子集；
- 已明确为部分日期或不支持精确日：禁用精确时间规则，Timeline 以受限模式保留；
- 量表存在但无可复算血缘：禁用量表复算，Profile 保留来源条目/来源总分；
- 实验室结果、单位、参考范围或分级定义不完整：禁用自动 CTCAE/阈值规则，
  Profile 保留来源结果。

### 2.4 不可变激活快照

激活服务完全从已确认 revision 的不可变语义质量报告生成：

- `semantic_quality_report_sha256`；
- `capability_manifest_sha256`；
- `activation_disposition`；
- `effective_capabilities` 及 SHA-256；
- 每项能力的状态、finding 关联和限制代码。

快照原子写入项目活动状态，并随既有不可变 activation history 保存。活动状态每次读取
都会与不可变 revision 重新核对；直接扩大有效能力集合会失败关闭。

新增统一服务端入口：

```text
require_monitoring_capability(project_id, capability_id)
```

`ready` 和 `limited` 可返回其明确状态；`blocked_by_quality` 与
`disabled_by_design` 明确报不可用，不会返回空结果伪装成“未发现风险”。

旧活动状态迁移后采用 `reject + 空能力集合` 的安全默认值，不会被误认为完整激活。

## 3. 改动文件

- `services/api/app/monitoring_mapping_semantic_quality.py`
- `services/api/app/monitoring_mapping_activation.py`
- `tests/test_monitoring_mapping_semantic_quality.py`
- `tests/test_monitoring_mapping_activation.py`

## 4. 验证证据

- 语义质量、draft、激活聚焦回归：`93 passed`；
- 全部 mapping 生命周期及 monitoring AI API 相邻回归：`103 passed`；
- 修改文件 Ruff 检查：`All checks passed`；
- Python 编译检查通过；
- 未重启正在运行的 API，未触发真实运行库 migration。

新增验证覆盖：

- 编码、部分日期、量表、实验室局部缺口均生成 restricted activation；
- 标准编码虚假声明仍为 global blocker；
- capability-only revision 可 confirm 并受限 activate；
- 受阻能力不进入 effective capabilities；
- 原始来源查阅及受限 Timeline 仍可通过能力门；
- 直接篡改活动能力集合会在读取时被拒绝；
- 完整映射生成 10 项 ready 能力的 full activation。

## 5. 剩余风险与后续切片

1. 本切片已提供统一运行时能力门，但尚未把标准编码、精确时间、CTCAE、量表复算、
   AE/MH 和 IP/依从性等每个下游执行入口逐一接入；下一切片必须完成逐入口接线和
   “不可运行而非空结果”回归。
2. 日期能力只在来源元数据明确表明精度不足时限制；字段画像/映射流程仍需稳定产出
   日期精度元数据。
3. 量表与实验室规则当前采取保守的项目中立最小合同；应在 RUX 与另一种 EDC 结构的
   真实项目完成受限/完整激活校准，避免误把来源总分当复算值或误启用 CTCAE。
4. 旧活动映射在服务重启迁移后不会自动获得能力；需基于当前规则形成新 revision 并
   重新激活，不改写历史。
5. 前端三态摘要和轻量能力详情不在本切片范围，仍需后续实现。
