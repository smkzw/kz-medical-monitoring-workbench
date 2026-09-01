# ClinicalTrials.gov 候选事实补全 Codex 验收

## 结论

接受本切片进入当前源码，允许在统一重启后用于未来新建的ClinicalTrials.gov不可变搜索
快照。旧快照、D017 v1/v2 run和生产数据库均不回写。

## 接受范围

- 候选合同新增向后兼容字段：
  - Brief Summary
  - 干预名称与干预类型
  - 随机分配
  - 干预模型
  - 盲法
  - 入组人数
- 检索字段、ClinicalTrials.gov v2 JSON解析、快照hash和产品AI分诊输入同步扩展。
- 分诊提示明确要求优先使用输入中的显式事实；缺失项进入证据缺口，不得从缺失字段推断
  靶点、途径或技术类型。

## 独立验收

主线程重新执行：

```text
pytest -q \
  tests/test_ctgov_candidate_enrichment.py \
  tests/test_writing_reference.py \
  tests/test_writing_reference_repository.py \
  tests/test_medical_writing_competitor_triage.py \
  tests/test_medical_writing_triage_durable.py
```

结果：`169 passed, 22 subtests passed`，无失败。仅存在既有FastAPI、Starlette和SWIG弃用
警告。

以下文件另行通过`py_compile`：

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/writing_reference.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_ctgov_candidate_enrichment.py`

## 关键反例

- 旧JSON快照不含新增字段时仍可加载，默认值为空或`None`。
- 每一个新增医学事实变化均改变快照hash。
- 缺失候选事实时，产品AI输入保持空值，不用字符串`unknown`伪造源数据。
- 聚焦烟测只在内存解析ClinicalTrials.gov响应，没有写生产数据库。

## 后续门槛

1. 统一重启前后端，消除源码与运行build不一致。
2. 从D017现有检索条件创建全新的不可变快照。
3. 核对新快照中真实候选的新增字段和hash。
4. 通过工作台产品AI路径执行v3，不能用Codex或测试模型替代。
5. v3通过医学质量复核后才允许确认竞品篮子。
