# Conference Context: mw_company_protocol_template_authority_20260719

Created: 2026-07-19 17:49:29
Objective: 基于用户指定的公司方案摘要与I/II/III期完整方案，复核并形成公司优先、分期与设计可插拔、M11仅作条件性覆盖核对的医学写作模板治理与落地方案
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- 用户最新裁决和结构证据：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`
- 当前错误主模板实现：
  `services/api/app/medical_writing_protocol_template.py`
- 当前摘要组装逻辑：
  `services/api/app/medical_writing_authoring_journey.py`
- 当前绿地摘要/首页测试：
  `tests/test_medical_writing_greenfield_runtime.py`
- 当前Word导出实现：
  `services/api/app/medical_writing_document_exporter.py`
- 只读权威原文件已由用户明确授权：
  - `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D005-减重II期临床试验方案概要-V0.3-KZYY0525-clean-DIP0526-KZYY0526 (2).docx`
  - `/Users/smkzw/Documents/朗来项目资料/MY004/RA/MY004-RA-2b 研究方案摘要_V0.3-with Comments to ABBV.docx`
  - `/Users/smkzw/Documents/朗来项目资料/MY004/AD-CSU-PN三合一整合/MY004567片-炎症性皮肤病-方案摘要-V0.4-clean.docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMD-D001-AD II期临床方案-V1.0-tracked-20251212(1).docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/MG-K10-青少年AD-3期方案V1.0-20251105-clean.docx`

## Scope

- In scope:
  - 复核权威层级、摘要槽位、完整方案稳定核心和条件模块；
  - 设计不与某项目强绑定的模板数据合同和组装算法；
  - 识别当前M11主树实现的迁移风险、兼容策略和最小可验证落地顺序；
  - 给出能由真实I/II/III项目验证的验收矩阵。
- Out of scope:
  - 不修改源代码或用户原始DOCX；
  - 不撰写项目特异临床事实；
  - 不把模型意见作为最终临床/监管裁决；
  - 不重新设计整个写作工作台前端。

## Success Criteria

- 明确公司摘要/全文、竞品和M11三层权威如何裁决；
- 摘要与全文模板分离，且语义节点与最终显示标题分离；
- 能表达I/II/III期、设计、药物类型、给药途径、适应症特异模块；
- 能从当前160节点M11实现迁移且不破坏来源、候选和编辑器定位；
- 提供具体代码边界、数据合同、黄金测试和负向测试；
- 任何建议均标注直接证据、推断和待Codex验证项。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- 权威原DOCX只读，不复制全文到模型输出，不修改原件。
- 允许读取上述外部权威路径，仅用于本次模板结构复核。
- 允许输出仅限初始化的runner报告路径；不得写产品源码。

## Loop Log

- 2026-07-19 17:49:29: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-19: Codex完成四份摘要和I/II/III期完整方案的结构抽取，并将
  用户裁决、共性/差异、当前缺陷和候选数据合同写入权威矩阵。
