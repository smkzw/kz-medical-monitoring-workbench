# Conference Context: mw_protocol_structure_corpus_conf_20260719

Created: 2026-07-19 20:00:03
Objective: 会商公开原始Protocol跨适应症/跨分期结构语义分析的方法、抽样充分性、必选与条件可选判定阈值、语料标签和产品回写边界
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Task-specific user override (2026-07-19 22:18): every role that would
  otherwise be assigned to Grok Build is assigned first to the existing
  QoderCLI process PID `39908`, model `qwen3.8-max-preview`. Qoder tools,
  internal turns and token use are not artificially limited. Grok Build
  `grok-4.5` becomes the first fallback; all former fallbacks shift one
  position later.
- Visual/design tasks use a Codex-led panel with no sub-venue chair: QoderCLI
  PID `39908` / `qwen3.8-max-preview` and Kimi Code (`kimi-code` /
  `kimi-code/k3` = `k3`, high reasoning). If Qoder is genuinely unavailable,
  use Grok Build `grok-4.5`, then Hermes OpenCode Go `qwen3.7-plus`, then
  `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use QoderCLI PID `39908` / `qwen3.8-max-preview` as the
  sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go
  `deepseek-v4-flash`. If Qoder is genuinely unavailable, use Grok Build
  `grok-4.5`, then the previously declared complex-task fallbacks in their
  existing order. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- 用户要求和完整执行合同：
  `context/mw_protocol_structure_corpus_20260719_context.md`。
- 公司模板权威矩阵：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`。
- 当前动态章节矩阵：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`。
- 当前模板和测试：
  `services/api/app/medical_writing_protocol_template.py`、
  `tests/test_medical_writing_protocol_template.py`。
- 外部证据只承认ClinicalTrials.gov官方ProvidedDocs中的原始Protocol；
  SAP可用于统计章节语义补充但不进入Protocol结构分母。

## Scope

- In scope:
  - 独立审阅抽样设计、适应症选择、申办方去重、Protocol角色校验、
    版本策略、章节医学功能编码、出现率阈值和缺失原因分类。
  - 评估如何把结果映射为稳定核心、分期核心、设计可选、适应症可选、
    明确不适用和证据不足，而不把统计频率机械当成监管要求。
  - 设计语料打标、候选文本检索过滤、AI生成边界、模板迁移和回归测试。
- Out of scope:
  - 不直接下载或写入生产语料库，不修改生产代码。
  - 不把标题字符串比较当作医学功能比较。
  - 不把模型共识当作临床/监管结论。

## Success Criteria

1. 给出可执行的分层抽样和样本替换规则，处理某层公开Protocol不足5家
   申办方的情况。
2. 给出章节功能本体/编码的最小可用结构、同义标题归并和人工复核点。
3. 给出定量阈值与定性裁决的组合规则，以及抽样偏倚、版本偏倚和申办方
   模板偏倚的处理。
4. 给出从证据矩阵到模板、语料标签、AI候选和测试的受控回写流程。
5. 明确边缘设计：I期Part、多队列/篮式、开放/盲法、PK/PD/免疫原性、
   AESI、委员会、期中、多重性、亚组、估计目标、背景/补救治疗等。

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
- 不访问或上传公司内部机密文件；可读取本工作区内已授权的矩阵和实现。
- 外部搜索不得把摘要、publication或SAP误计为Protocol。

## Loop Log

- 2026-07-19 20:00:03: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-19 22:18: Applied user route override: QoderCLI PID `39908` /
  `qwen3.8-max-preview` replaces all Grok Build roles as first priority;
  Grok Build is retained only as first fallback.
