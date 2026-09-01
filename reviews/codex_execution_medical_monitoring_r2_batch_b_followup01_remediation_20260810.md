# R2 Batch B 独立 follow-up 01 VETO 纠偏门

日期：2026-08-10

状态：`REMEDIATED / PENDING_INDEPENDENT_FOLLOWUP_02`

来源：`runs/medical_monitoring_r2_batch_b_independent_followup_01_20260810.md` 的 2 个 P1。此前首次 VETO、follow-up 01 VETO 与 Batch A ACCEPT 均保留为不可覆盖历史。

## 根因与纠偏

1. **merge/split 丢失 high lineage**：增加保守 severity 次序；merge 默认继承所有来源风险中的最高严重程度，merge/split 均拒绝低于来源最高严重程度的结果。merge 裁决现在必须绑定标准化后的精确 `severity` 与 `classifier` action payload；使用时重算并比较哈希。新 classifier 中的 SAE/AESI 语义同样进入继承 flags。
2. **合法 SAE/AESI 字符串绕过**：术语规范化在转小写前保留 camel-case 边界，并识别 `SAE`/`AESI` token、`serious adverse event`、`adverse event of special interest` 以及常用中文名称；相近无关词不得误标。

## 新增决定性攻击回归

- `potentialAESI`、`potentialSAE`、`serious_adverse_event`、`adverse_event_of_special_interest`、`严重不良事件`、`特别关注不良事件`：medium risk 均形成正确 flag，机器关闭被拒绝。
- `disease_management`、`unsafe_data`：不产生 SAE/AESI flag。
- merge 无结果 payload：裁决签发拒绝；payload classifier 不匹配：合并拒绝且状态原子。
- high+medium merge 显式降为 low：拒绝且状态原子；未指定时结果为 high，后续机器关闭拒绝。
- high split 为 low children：拒绝且状态原子；未指定时 children 保留 high，后续机器关闭拒绝。

## 决定性检查

- 风险聚焦：`89 passed in 0.10s`。
- Batch B：`198 passed in 0.20s`。
- R2 全量：`434 passed in 0.33s`。
- 内存语法编译：10 个 `src/**/*.py` 文件通过。
- R2 `__pycache__` / `.pytest_cache`：无。
- TCP 8911 listener：无。

## 冻结锚点

- R2 tree：`ee9e32032c61c7895d3c6040d7e1322dc76c71d4d60b75f503b7fae860d3ce72`
- README：`cfcf9e376a212ac6039059596b2909e49e8e5ba7de113cf272303dfd8a75ee54`
- `src/mm_r2/__init__.py`：`67907ffd3640d5757cf9edacb27e0e9fff4a9455f3f949a2822fb8776734980a`
- `src/mm_r2/baselines.py`：`6a489e7e40004382c5684e7e005e6715e263da25611500cfd2e4f7d3f7b089fd`
- `src/mm_r2/modes.py`：`05a032b7fd42b0c0a8aaa150048d1531a685171eba5787efe14175100582d6ea`
- `src/mm_r2/diff.py`：`a4991ec9c17b7283e8978e7b5ebe6abf99be62ed8523d595ee448a208a17f91e`
- `src/mm_r2/risk.py`：`1bb82f26b01cbbb56658bdc146501bfdefa5e3741cb18baa950f7392d3637ef4`
- `tests/test_r2_b_baselines.py`：`c0b1047e143f432f0f388508a2aba5f47bcdeef87553b959ebb7dda3a6ca2354`
- `tests/test_r2_b_modes.py`：`6fb164f98951720fa4688b3695e2d45a4a61f39ff0074effe980bfafbe2eef73`
- `tests/test_r2_b_diff.py`：`84b7d40a275c7580b6e58e211dde2de65b9b7b26c7bd2cc15f13164b4fcce572`
- `tests/test_r2_b_risk.py`：`dc3552afaeacac0ee6491432b96d2e9c7e9253a40c3d52a35430a1a1aaca9ed2`

Batch C 继续冻结，直至原独立审阅会话 follow-up 02 明确 ACCEPT。
