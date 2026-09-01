# ClinicalTrials.gov 候选事实补全审阅记录

## 范围与结论

本切片仅扩展未来新建 ClinicalTrials.gov 搜索快照中的竞品候选事实，并将这些事实传给现有产品独立 AI 分诊链路。未修改前端、`main.py`、数据库结构、运行记录、AI-first prefill 文件，也未确认任何 D017 分诊运行。

实现符合以下边界：

- 继续使用产品既有 `deepseek/deepseek-v4-pro` 路由，未替换模型或传输层。
- 旧 JSON 快照缺少新增字段时仍可加载，新增字段采用空字符串、空列表或 `None` 默认值。
- 旧快照和正在运行的 D017 v2 未被重写；新字段只会在后续新搜索快照中出现。
- 未增加本地医学枚举映射，保留 ClinicalTrials.gov v2 返回的原始字符串值。

## 官方字段核对

依据 ClinicalTrials.gov v2 官方数据结构和实时 API 响应，采用以下映射：

| 搜索字段 | v2 JSON 路径 | 合同字段 |
| --- | --- | --- |
| `BriefSummary` | `protocolSection.descriptionModule.briefSummary` | `brief_summary` |
| `InterventionName` / `InterventionType` | `protocolSection.armsInterventionsModule.interventions[].name/type` | `interventions[].name/intervention_type` |
| `DesignAllocation` | `protocolSection.designModule.designInfo.allocation` | `design_allocation` |
| `DesignInterventionModel` | `protocolSection.designModule.designInfo.interventionModel` | `design_intervention_model` |
| `DesignMasking` | `protocolSection.designModule.designInfo.maskingInfo.masking` | `design_masking` |
| `EnrollmentCount` | `protocolSection.designModule.enrollmentInfo.count` | `enrollment_count` |

官方来源：

- https://clinicaltrials.gov/data-api/about-api/study-data-structure
- https://clinicaltrials.gov/api/v2/studies?query.cond=Atopic%20Dermatitis&pageSize=1&format=json&fields=NCTId,BriefSummary,InterventionName,InterventionType,DesignAllocation,DesignInterventionModel,DesignMasking,EnrollmentCount

实时无落库烟测解析 `NCT03562377`，得到 4 个显式干预项、`RANDOMIZED`、`PARALLEL`、`DOUBLE` 和入组人数 `215`。

## 代码变更

1. 新增 `WritingReferenceTrialIntervention` typed model，并向 `WritingReferenceTrialCandidate` 增加向后兼容字段。
2. 扩展 `CTGOV_DISCOVERY_FIELDS`，从官方 v2 路径解析新增事实。
3. 将全部新增事实纳入 `_snapshot_hash()`；任何一类医学事实变化都会使快照哈希变化。
4. 将新增事实原样加入 `_build_chunk_input()`，确保产品独立 AI 实际收到候选摘要、干预、设计和入组信息。
5. 对分诊 system prompt 作限定性微调：优先使用显式候选事实；缺失信息写入 `evidence_gaps`，不得推断靶点、给药途径或模态。

## 验证

聚焦测试：

```text
pytest -q tests/test_ctgov_candidate_enrichment.py
5 passed, 6 subtests passed
```

受影响回归：

```text
PYTHONPATH=/tmp/mw_ctgov_pydeps /opt/homebrew/bin/python3.12 -m pytest -q \
  tests/test_writing_reference.py \
  tests/test_writing_reference_repository.py \
  tests/test_medical_writing_competitor_triage.py \
  tests/test_medical_writing_triage_durable.py \
  tests/test_ctgov_candidate_enrichment.py
169 passed, 22 subtests passed
```

语法检查：

```text
/opt/homebrew/bin/python3.12 -m py_compile <本切片全部 Python 文件>
通过
```

`ruff` 和 `black` 未安装，因此未作为验收证据。测试仅出现既有 FastAPI、Starlette 和 SWIG 弃用警告，无功能失败。

## 旧快照与数据库未修改证据

- 实现和烟测未调用本地产品 API、未调用生产数据库写入方法。
- 持久化回归使用测试内 `TemporaryDirectory` 创建隔离 SQLite 文件。
- 实时 ClinicalTrials.gov 烟测只在内存中调用 `candidate_from_study()`。
- 本切片没有修改数据库文件、数据库迁移、`main.py` 或任何 D017 运行记录。
- 当前 D017 v2 仍基于原不可变快照；要让产品 AI 获得新增事实，必须重新执行 ClinicalTrials.gov 搜索并生成新快照。

## 修改文件

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/writing_reference.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_ctgov_candidate_enrichment.py`
- `reviews/codex_subagent_ctgov_candidate_enrichment_20260724.md`
- `runs/execution/mw_ctgov_candidate_enrichment_20260724/codex_worker.done`

