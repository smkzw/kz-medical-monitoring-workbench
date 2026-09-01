# medical_monitoring_ai_native_r3

R3 Study Intelligence 与异构 listing 合成数据基座 — medical monitoring
AI-native POC。**仅合成/离线 fixtures**；无真实项目路径、凭据或网络。

## 范围 (R3-A / worker_01)

worker_01 拥有 R3 包脚手架与资料权威合同：

| 模块 | 职责 |
|---|---|
| `src/mm_r3/__init__.py` | R3 schema registry（R3-A 声明的 schema 版本）与公共导出 |
| `src/mm_r3/knowledge.py` | 资料分类、来源版本/有效时间/范围、Knowledge Pack、claim authority matrix、source conflict/resolution 合同 |
| `src/mm_r3/fixtures.py` | 合成异构 listing、Knowledge Pack、source conflict fixtures（worker_02/03 可复用） |
| `tests/conftest.py` | R3 专用 pytest fixtures（sys.path、合成来源、知识包） |
| `tests/test_r3_a_knowledge.py` | 资料权威/冲突/版本/范围/claim 优先级确定性测试 |

后续 worker（R3-B、R3-C）在各自文件中追加，仅可向 `__init__.py`/本 README 追加一致的导出与文档。

## 关键合同 (R3-A)

1. **来源版本不可变**。`SourceRevision` 携带 `revision_id`/`project_id`/`source_type`/`version`/`valid_from`/`scope`/内容摘要；不同字节产生不同身份；摘要不可由外部任意声明（authority token 封封）。
2. **有效时间与范围**。来源声明有效时间窗口与覆盖范围（域/文件/section/页码）；范围缺失时为 `scope_unspecified`，不静默视为全量。
3. **Knowledge Pack 版本化且可追溯**。四层知识（通用医学、药物/机制、项目资料、激活规则）绑定来源修订与内容哈希；项目资料在其 claim scope 内优先。
4. **claim authority matrix**。同一主张可由多层来源支持；`ClaimAuthority` 记录每个支持来源的层级、强度与冲突关系；冲突永不静默覆盖。
5. **source conflict/resolution 可审计**。`SourceConflict` 记录冲突主张、冲突类型与定位；`ConflictResolution` 显式记录裁决依据、胜出来源与未解决不确定性；裁决不可隐式发生。
6. **公共规则无项目硬编码**。所有 fixture、claim、冲突、分类不含项目绝对路径、项目名或 RUX/MGK10/MY009 特例。

## 运行

```bash
cd poc/medical_monitoring_ai_native_r3
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -q -p no:cacheprovider
```

## 范围 (R3-B / worker_02)

worker_02 拥有 listing 结构画像、语义 mapping、稳定 record identity 与规范化语义合同：

| 模块 | 职责 |
|---|---|
| `src/mm_r3/normalization.py` | 日期/部分日期/单位/编码/重复/缺失值规范化；保留原始值、规范化值与显式不确定性 |
| `src/mm_r3/identity.py` | 稳定 record identity（行/列/显示变化稳定）、identity algorithm、歧义暴露、重复检测 |
| `src/mm_r3/listing.py` | workbook/table/field 结构画像；field role 推断；内容寻址 |
| `src/mm_r3/mapping.py` | 语义 mapping 候选/置信度/依赖/显式决策（accepted/rejected/needs_confirmation/not_evaluable）|
| `tests/test_r3_b_*.py` | normalization/identity/listing/mapping 确定性测试（173 tests）|

## 关键合同 (R3-B)

1. **结构画像内容寻址**。`WorkbookProfile`/`TableProfile`/`FieldProfile` 不可变；内容哈希排除随机代理 id，相同结构产生相同哈希；绑定真实 source revision id。
2. **稳定 record identity**。`IdentityAlgorithm` 冻结；digest 在行顺序、列顺序、显示格式（空白/大小写）变化下稳定；真正内容/键变化产生新身份或歧义，不误合并。
3. **歧义暴露不静默**。全部 key 缺失或部分 key 缺失（默认）产生 `AmbiguousIdentity`（`none` kind），阻断 baseline eligibility；重复键暴露但不合并。
4. **mapping 候选可解释**。每个候选携带分数、证据（name/role/value/domain/position match）和显式决策；低置信度永不静默接受。
5. **identifier 永需确认**。identifier role 的 mapping 即使高分也标记 `needs_confirmation`；`requires_confirmation` target 同理。
6. **显式决策四态**。`accepted`/`rejected`/`needs_confirmation`/`not_evaluable`；accepted 必须命名 chosen candidate；非 accepted 阻断 baseline。
7. **规范化保留原始值**。`NormalizedValue` 保留 raw_value + normalized + quality + uncertainty；exact quality 不带不确定性；partial/ambiguous/imputed 必须携带不确定性说明。
8. **公共规则无项目硬编码**。三种异构 listing 形态（wide AE / long labs / multi-table workbook）测试不含项目绝对路径或项目名。

## 范围 (R3-C / worker_03)

worker_03 拥有 snapshot diff/临床影响传播与自然语言规则生命周期合同：

| 模块 | 职责 |
|---|---|
| `src/mm_r3/snapshot_diff.py` | 全量快照 diff（added/removed/disappeared/unchanged/modified）、scope coverage、临床影响传播 |
| `src/mm_r3/rules.py` | 自然语言规则结构化草稿、模拟、版本化激活、evaluation scope |
| `tests/test_r3_c_*.py` | snapshot diff/impact propagation/rule lifecycle 确定性测试与隐藏反过拟合挑战 |

## 关键合同 (R3-C)

1. **输入始终是全量快照**。`SnapshotFacts` 不可变、内容寻址，绑定 source revision 与冻结 identity algorithm；diff 在两个全量快照之间计算。
2. **消失记录不静默解除**。基线有而当前无的记录默认为 `disappeared`（coverage 未确认），不得直接解除风险；仅在显式 `ScopeCoverageNote(covered=True)` 时才记为 `removed`。
3. **diff 确定性可复现**。`SnapshotDiff` 按 `record_id` 排序；摘要计数由变更记录派生，不接受外部声明；相同两个快照产生相同 diff。
4. **影响传播显式分类**。`ImpactPropagation` 将 added→`new_finding`、modified→`data_correction`、disappeared→`potential_loss`、removed→`confirmed_removal`；`potential_loss` 永远 `requires_review`。
5. **规则只能先草稿后模拟**。`RuleDraft` 携带自然语言原文 + 结构化条件 + 来源绑定；`simulate_rule` 在激活前强制执行模拟。
6. **激活需显式版本与 scope**。`RuleActivation` 强制 `version` + `EvaluationScope`；模拟 content_hash 必须匹配草稿；machine 激活不能 `user_confirmed`。
7. **三类 evaluation scope**。`full_history`/`current_snapshot`/`future_only`；scope 在激活时冻结，后续变更需新版本化激活。
8. **公共规则无项目硬编码**。隐藏反过拟合挑战使用重命名/重排的异构结构，证明 diff 与规则评估不依赖项目名或路径。
