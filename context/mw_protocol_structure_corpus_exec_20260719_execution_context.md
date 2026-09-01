# Execution Context: mw_protocol_structure_corpus_exec_20260719

Created: 2026-07-19 20:00:30
Objective: 为医学写作动态章节证据库建立可复核的三适应症、II/III期、不同申办方公开原始Protocol样本清单与结构语义分析执行计划
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_qoder` -> live `qodercli` PID `39908` /
  `qwen3.8-max-preview`
- Execution-manager fallback: Grok Build / `grok-4.5`, followed by the
  previously declared fallbacks in their existing order
- Qoder budget: no artificial tool-turn or token restriction; process liveness
  and actual progress determine availability

## Source Of Truth

- `context/mw_protocol_structure_corpus_20260719_context.md`
- ClinicalTrials.gov官方study API和ProvidedDocs。
- 每个工作项只报告可核验的原始Protocol；SAP、统计计划、结果论文、
  publication和注册摘要分别标注，不得替代Protocol。

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- 工作者不得修改生产源代码、模板或语料库。
- 工作者只在最终响应中返回候选清单、官方URL和方法建议；runner写入
  `runs/execution/mw_protocol_structure_corpus_exec_20260719/`。
- 不足5家时不得用同一申办方多个研究或同一Protocol多个版本凑数。
- 模型输出只是候选，Codex需重查API和实际PDF首页/目录。

## Work Items

1. 特应性皮炎：分别寻找II期和III期各至少5家不同申办方的公开原始Protocol，记录NCT、阶段、申办方、官方ProvidedDocs URL、版本日期、文档角色和下载可用性，提出章节医学功能编码初稿
2. 类风湿关节炎：分别寻找II期和III期各至少5家不同申办方的公开原始Protocol，记录NCT、阶段、申办方、官方ProvidedDocs URL、版本日期、文档角色和下载可用性，提出章节医学功能编码初稿
3. 肥胖或超重：分别寻找II期和III期各至少5家不同申办方的公开原始Protocol，记录NCT、阶段、申办方、官方ProvidedDocs URL、版本日期、文档角色和下载可用性；若不足，提供检索证据及适应症替换建议

## Acceptance Criteria

1. 每个“适应症×分期”至少列出5家不同申办方的候选Protocol；若无法
   达到，列出已检索研究、缺失原因和可替换适应症。
2. 每个候选至少含NCT、官方题目、分期、申办方、干预、ProvidedDocs
   文档名/日期/URL和Protocol角色判断。
3. 区分最终Protocol、Protocol amendment、Protocol+SAP合并文件和非
   Protocol文档；同一研究多个版本只保留一个主分析版本并保留版本链。
4. 给出适应症内最可能的章节功能差异和必须由Codex复核的边缘点。

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Route Override Log

- 2026-07-19 22:18: User explicitly replaced every Grok Build conference role
  and the current complex execution-manager role with QoderCLI PID `39908`,
  model `qwen3.8-max-preview`, as first priority. The original Grok route is
  retained only as the first fallback.
