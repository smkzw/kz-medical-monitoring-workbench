# R2 Batch B 独立 follow-up 02 VETO 纠偏门

日期：2026-08-10

状态：`REMEDIATED / PENDING_FRESH_INDEPENDENT_REVIEW`

来源：`runs/medical_monitoring_r2_batch_b_independent_followup_02_20260810.md` 的 1 个 P1、2 个 P2。全部历史 VETO、纠偏与 Batch A ACCEPT 保留，不覆盖。

## 纠偏

1. **大小写/连接标签/中文名称漏识别**：缩写识别增加受控的 compact marker 规则，覆盖 `AeSi`、`sAe`、全大写或全小写连接标签；常用中文术语同时识别有无“的”的表达。
2. **merge identity 输入顺序漂移**：merge 首先按稳定 risk identity/instance key 规范化 targets，结果 scope 使用所有来源 scope 的排序并集，不再读取调用方列表的第一个元素。
3. **否定标签过度匹配**：英文 token/sequence/compact marker 与中文短语均增加显式否定判断；compact marker 只接受受控前后缀，避免复数和普通单词子串误报。

## 新增决定性回归

- 12 类 mixed-case/connected/中英文 SAE/AESI 标签进入真实 RiskInstance，后续机器关闭均 fail closed。
- 13 类普通、复数、相似词及显式否定标签保持 unflagged；低风险后续机器关闭可完成。
- `not_protocol_aesi_signal`、`without_protocol_sae_signal` 和 `未发生严重不良事件` 均不误标。
- 两个不同 scope 风险以正序/逆序合并，结果 scope 均为 `("left", "right")`，RiskIdentity 相同。
- split child classifier=`AeSi` 形成 AESI flag，后续机器关闭 fail closed。

## 决定性检查

- 风险聚焦：`111 passed in 0.11s`。
- Batch B：`220 passed in 0.19s`。
- R2 全量：`456 passed in 0.30s`。
- 内存语法编译：10 个 `src/**/*.py` 文件通过。
- R2 cache：无；TCP 8911 listener：无。

## 冻结锚点

- R2 tree：`28858c7d47c05207fa8d2e2659464038000ccd46986bc44ba503dc477ff038e5`
- README：`8ef40e759ed9bc7718d987e2109e855e5a21d64d6d135626e683d456a39d7185`
- `src/mm_r2/__init__.py`：`67907ffd3640d5757cf9edacb27e0e9fff4a9455f3f949a2822fb8776734980a`
- `src/mm_r2/baselines.py`：`6a489e7e40004382c5684e7e005e6715e263da25611500cfd2e4f7d3f7b089fd`
- `src/mm_r2/modes.py`：`05a032b7fd42b0c0a8aaa150048d1531a685171eba5787efe14175100582d6ea`
- `src/mm_r2/diff.py`：`a4991ec9c17b7283e8978e7b5ebe6abf99be62ed8523d595ee448a208a17f91e`
- `src/mm_r2/risk.py`：`d7d5de88d040fde7fde8f3d9b5a2742da25076f35964be9d8945bb3613ea4166`
- `tests/test_r2_b_baselines.py`：`c0b1047e143f432f0f388508a2aba5f47bcdeef87553b959ebb7dda3a6ca2354`
- `tests/test_r2_b_modes.py`：`6fb164f98951720fa4688b3695e2d45a4a61f39ff0074effe980bfafbe2eef73`
- `tests/test_r2_b_diff.py`：`84b7d40a275c7580b6e58e211dde2de65b9b7b26c7bd2cc15f13164b4fcce572`
- `tests/test_r2_b_risk.py`：`ee651e0688e948333b5deb08615e72d92da38e2d1e02cc689e5ae214c859be72`

Batch C 继续冻结，等待 fresh-context 独立审阅明确 ACCEPT。

## 独立审阅路由

- 原生 fresh `gpt-5.6-luna/max` 子会话探测返回 `Unknown model`，当前 spawn 运行时仅列出 Sol/Terra。
- 按全局合同使用 `cli_compatibility_fallback`：`/Applications/ChatGPT.app/Contents/Resources/codex exec -m gpt-5.6-luna`，保留 `max` effort、fresh context、workspace-write 和长硬等待；不替换为 Sol/Terra，不经 Hermes。
