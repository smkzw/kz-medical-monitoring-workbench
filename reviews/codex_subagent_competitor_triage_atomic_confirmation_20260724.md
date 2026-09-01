# 竞品分诊最终分类原子确认定向返修审阅

- 日期：2026-07-24
- 工作区：`implementation/workbench`
- 结论：通过
- 范围：竞品 Protocol/SAP AI 分诊确认、最终分类、幂等、全排除及 corpus 投影

## 1. 修复目标

消除旧链路中的非原子窗口：

1. service 先按 AI 分类写确认和 relevance decision；
2. service 随后投影 authoring journey；
3. HTTP 层最后逐条写医学经理覆盖分类。

如果第 3 步中途失败，确认记录、旅程 basket 与最终 relevance decision 可能不一致。

## 2. 最终实现

### 2.1 正式请求契约

`CompetitorTriageBasketConfirmationRequest` 新增：

- `final_classifications`：以 NCT ID 为键，值仅允许
  `direct_competitor`、`indirect_reference`、`excluded`；
- `no_suitable_competitor_reason`：全部候选均排除时必填，去除标点和空白后至少 10 个实质字符。

`retained_nct_ids` 允许为空，但 service 仍强制：

- retained/excluded 内部无重复；
- retained/excluded 无交集；
- retained + excluded 精确覆盖当前不可变快照；
- `final_classifications` 精确覆盖同一候选集；
- final classification 与 retained/excluded 分区完全一致；
- REVIEW_READY run 的 AI 结果本身覆盖全部候选；
- stale、partial_failed、failed run 不能首次确认。

确认记录同时保存最终分类和无合适竞品理由，二者均进入 confirmation hash。

### 2.2 单事务写入

`CompetitorTriageService._atomic_confirm_and_decisions` 在同一
`BEGIN IMMEDIATE` 事务中完成：

1. 幂等键 replay/conflict 校验；
2. 写入 confirmation；
3. 按医学经理最终分类写入所有 relevance decision；
4. 将 triage run 更新为 `confirmed`；
5. 写入幂等记录；
6. 一次提交。

事务任一点异常均回滚上述全部写入。HTTP 层不再读取当前 decision，也不再执行逐条后置覆盖。

authoring journey 使用独立数据库，继续采用既有可重试投影边界：

- confirmation、最终 decision 和 run 状态先成为权威状态；
- journey 投影失败时记录 `projection_pending/failed`；
- 用户无需二次批准，可通过 projection retry 恢复。

该状态是显式、可恢复状态，不再存在“旅程已按 AI 分类投影、decision 又被 HTTP 改成另一分类”的不一致。

### 2.3 幂等语义

- 同一 key、同一完整请求：返回同一 confirmation，不增加 decision revision，不重复投影 journey。
- 同一 key、不同最终分类：409 conflict。
- 不同 key、相同 confirmation material：返回同一 material confirmation，并为新 key 建立幂等别名。
- 最终分类、retained/excluded、理由、journey revision 和 run canonical hash 均参与请求/确认身份。

### 2.4 全部排除

前端允许将所有候选设为 excluded，并显示：

- 全排除后的工作流影响；
- 必填“无合适竞品理由”；
- 确认后可继续手工上传方案或使用通用语料库。

确认按钮只有在理由不少于 10 个字时可用。后端再次执行实质字符校验，不能依赖前端。

`MedicalWritingCorpusTriageFinalizeRequest.retained_candidate_ids` 同步允许空列表，但：

- snapshot 仍必填；
- finalize reason 仍至少 10 个字符；
- 全排除 service 路径使用已确认的 `no_suitable_competitor_reason`；
- 未放宽候选集合、分类或快照一致性。

## 3. 变更文件

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_medical_writing_competitor_triage.py`
- `tests/test_medical_writing_triage_recovery_api.py`
- `tests/test_frontend_medical_writing_contract.py`

未修改已冻结的动态设计 typed 对象或动态设计投影实现。

## 4. 关键回归覆盖

服务与 API/前端合同测试覆盖：

1. 医学经理将 AI `indirect_reference` 改为 `direct_competitor` 后，confirmation、decision 和 journey retained basket 一致。
2. 在事务最后阶段注入异常后，confirmation、全部 decision、run 状态和 journey revision 均不半写。
3. 完全相同请求幂等，decision revision 和 journey revision 不增加。
4. 相同 key 配不同最终分类发生冲突。
5. retained/excluded 缺候选、重复、交集被拒绝。
6. final classifications 缺候选、非法枚举、与集合矛盾被拒绝。
7. 全部 excluded 且提供实质理由成功，corpus triage 以空 retained 列表完成。
8. 全部 excluded 但理由不足被契约拒绝。
9. HTTP confirm 只调用一次 service，不再调用 repository 后置覆盖。
10. 前端发送 `final_classifications` 和
    `no_suitable_competitor_reason`，并提供全排除交互。

## 5. 验证结果

### 聚焦回归

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_medical_writing_competitor_triage \
  tests.test_medical_writing_triage_recovery_api \
  tests.test_frontend_medical_writing_contract

Ran 176 tests in 1.808s
OK
```

### 相邻 corpus/authoring 回归

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_medical_writing_corpus_readiness \
  tests.test_medical_writing_authoring_journey

Ran 29 tests in 0.939s
OK
```

### 前端生产构建

```text
npm run build

1885 modules transformed
build completed in 1.60s
```

Vite 仍报告既有的大 chunk 提示（主 JS 约 1.53 MB，gzip 约 450 kB），不影响本次构建通过，也不属于本次竞品分诊事务返修范围。

## 6. 残余边界

writing-reference 数据库与 authoring-journey 数据库不是同一 SQLite
事务。当前采用权威确认先落盘、投影失败显式标记、同一 confirmation
无二次批准重试的既有恢复设计。此次修复保证旅程投影消费的 retained/excluded
来自同一份已原子确认的最终分类，不再由 HTTP 后置覆盖改变。

工作区没有 Git 元数据，无法提供 `git diff/status` 证据；本次按实际编辑文件和测试结果完成边界核对。
