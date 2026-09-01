# Route D0 中文监管语体单模型门禁

你是独立中文药物注册临床试验方案文字审阅者。本任务是单模型中文门禁，不是会商，不构成医学批准。

先完整阅读`/Users/smkzw/.hermes/SOUL.md`。

Read these files only:

- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/expression_template_candidate_library.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/sources/proj_rux_03_002/project_fact_pack_v2.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/sources/proj_my008_pnh_3_01/project_fact_pack_v2.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/sources/proj_d001/project_fact_pack_v2.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/runs/proj_rux_03_002/D0/output.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/runs/proj_my008_pnh_3_01/D0/output.json`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot_v2/runs/proj_d001/D0/run_manifest.json`

Hard boundaries:

- 只读上述七个项目文件及`/Users/smkzw/.hermes/SOUL.md`。
- 不得修改源文件、事实包、运行结果或生产代码。
- 不得访问网络、其他项目目录或未列出的工作区文件。
- 该输出只作中文监管语体问题发现，不构成医学批准或最终生产验收。
- Write exactly one output file: `runs/conference/medical_writing_corpus_agent_harness_20260714/route_d_deepseek_chinese_gate.md`. The bounded runner persists your final response there; do not create sibling output files.

任务：

- 逐句核对RUX和PNH输出是否忠实于各自v2事实包，特别检查设计要素、数值、比较符、条件、否定、术语和伦理/知情同意语义。
- 从中国注册临床试验方案语体判断是否存在机械拼接、重复、歧义、AI式空话或不自然措辞。
- 判断D001因2周/4周随访源内冲突而阻断是否合理；不得替用户选择冲突值。
- 明确当前只是无模型缺口生成的D0确定性可行性单元，不得把它评价成完整Route D或通用生产renderer。
- 明确区分事实错误、高风险监管措辞、一般文风问题和无须修改项。
- 不得因为句子“更流畅”而新增事实，不要重写整段；只给最小修改建议。

输出中文Markdown，包含：来源已读、RUX逐项发现、PNH逐项发现、D001阻断判断、是否适合进入资深医学盲评、仍存不确定性。最后给出紧凑loop trace：观察、证据、建议下一步。
