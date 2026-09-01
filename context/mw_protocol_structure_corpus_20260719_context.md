# Task Context: mw_protocol_structure_corpus_20260719

Created: 2026-07-19 19:59:55
Objective: 从公开原始Protocol出发，按三个适应症的II期和III期、每层至少5家不同申办方，建立章节医学功能层面的必选/条件可选/不适用证据矩阵，并把结果回写医学写作模板、语料标签、AI候选路由和跨项目测试
Task type: `competitive_intelligence`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 用户要求：不能由单一期中分析示例外推；需比较章节承担的真实医学/监管
  功能，而非只比较标题文字。
- 用户抽样要求：3个不同适应症；每个适应症的II期、III期各至少5份、
  来自不同申办方的公开原始Protocol（以确实可获得为前提）。
- 官方外部来源：ClinicalTrials.gov study API、Study Documents/
  ProvidedDocs及其最终下载URL；注册页面、publication和新闻仅用于定位，
  不进入Protocol结构频率分母。
- 公司模板权威：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`
- 当前动态章节合同：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/DYNAMIC_CHAPTER_DECISION_MATRIX.md`
- 当前实现：
  `services/api/app/medical_writing_protocol_template.py`、
  `services/api/app/medical_writing_greenfield.py`、
  `frontend/src/features/medical-writing/ProtocolModuleResolutionPanel.jsx`。
- 现有三适应症新下载探针仅可复用其原始文件，不可把旧拆解结论当作新
  结构分析：
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/`。

## Scope

- In scope:
  - 首选特应性皮炎、类风湿关节炎、肥胖/超重；若某一“适应症×分期”
    无法找到5家不同申办方的公开Protocol，保留完整检索证据并替换为
    公开资料更充足且对产品有代表性的适应症。
  - 建立样本登记：NCT、适应症、分期、研究设计、申办方、药物/机制、
    文档角色、版本日期、官方URL、字节数和SHA-256。
  - 从原始Protocol提取TOC、标题层级和章节文本，建立跨标题同义归并的
    “医学功能编码词典”。
  - 分别计算适应症内/分期内、跨适应症同分期和跨分期的出现率；记录
    功能被其他章节承载、明确不适用、未决定、文件版本不足等原因。
  - 把结论转为模板节点适用性、语料标签、证据选择条件、AI候选路由和
    跨项目测试建议；只有经Codex核验的结论才可进入生产代码。
- Out of scope:
  - 不使用publication、结果论文、SAP或注册摘要冒充Protocol。
  - 不因标题缺失就断言医学功能缺失；必须检索全文中的替代承载位置。
  - 不用30份样本直接宣称监管普遍性；结论限定为公开样本中的产品证据。
  - 本轮模型输出不得直接修改生产模板、语料准入状态或临床内容。

## Success Criteria

1. 每个纳入层均达到至少5家不同申办方；不足时有可复核的检索记录和
   替换决定。
2. 每份样本均为官方可下载原始Protocol并具备版本、URL、字节数、
   SHA-256和文档角色校验。
3. 功能编码至少覆盖文档控制、摘要、背景/获益风险、目的/终点、设计、
   人群、干预、流程、疗效、安全、PK/PD/免疫原性、统计、伦理/管理、
   参考文献/附录及设计特异模块。
4. 每项“稳定核心/分期核心/设计可选/适应症可选/明确不适用/证据不足”
   结论均可回溯到Protocol定位和分母。
5. 形成机器可读manifest、章节功能矩阵、方法说明、差异报告和产品回写
   建议；至少一轮独立会商和Codex复核完成。
6. 生产变更前先增加失败用例，再以最小补丁更新模板/标签/路由并完成
   I/II/III和跨适应症回归、浏览器和Word验收。

## Risk Boundaries

- 原始公开Protocol写入专用语料研究目录；公司本地文件和稳定运行库只读。
- 不上传公司内部文件或受试者数据到第三方。
- 外部Agent只输出候选清单、编码建议和审阅意见；Codex核验官方URL、
  文档角色、哈希、结构和最终产品写入。
- 统计阈值是产品工程规则，不冒充监管法规；少量或偏倚样本必须显式标注。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-19 19:59:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-19 20:00: 用户要求从单点示例扩展为章节医学功能级证据工程；
  确定先按特应性皮炎、类风湿关节炎、肥胖/超重做II/III期分层取样。
- 2026-07-19 20:00: 已建立三路执行和独立会商；生产代码保持冻结，待
  样本、方法和编码词典经Codex复核后再进入实现。
- 2026-07-19 22:18: 用户覆盖本任务会商路由：所有原 Grok Build 角色
  第一顺位改由现有 `qodercli` PID `39908`、模型
  `qwen3.8-max-preview` 承担，工具轮次和 token 不做人为限制；
  Grok Build / grok-4.5 顺延为第一 fallback，其余 fallback 依次后移。
  此覆盖同时适用于本轮复杂执行管理者和会商主席；已运行的非 Grok
  参与者继续执行，不重启、不重复消耗。
- 2026-07-19 22:52: ClinicalTrials.gov 初筛显示肥胖/超重 III 期虽有
  9家名义申办方公开Protocol，但不同申办方样本大量以 PWS、NASH、
  T2D 或其他特殊人群/共病为主要适应症，不能代表常规体重管理方案，
  不得用于凑足分母。按预设替换规则，保留失败检索证据，将第三适应症
  替换为斑块状银屑病并从官方Protocol重新抽样。
