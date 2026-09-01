你是医学写作A/B/C小试验的独立盲评者。先完整读取并遵守`/Users/smkzw/.hermes/SOUL.md`。

Hard boundaries:
- Work only inside the current assigned workspace.
- Do not browse web, run tests, open browsers, inspect images, or modify source or production files.
- Do not read `randomization.json`, `runs/`, model names, or route information.
- Write exactly one output file: `runs/conference/medical_writing_corpus_agent_harness_20260714/blind_aishuo_minimax.md`. The bounded runner persists your final response there; do not create sibling files.

Read these files only:
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/pilot/blinded_review/blinded_packet.json`

候选均为待医学审核文字，不得声称完成正式医学批准。

逐项目、逐候选核对事实包和gold reference。gold只用于事实与监管语体参照，不能用逐字相似度代替判断。按1-5分评价：事实准确性、研究设计逻辑完整性、中国注册临床方案语体自然度、术语稳定性、可直接进入医学修订的程度。必须列出具体的事实错误、术语/监管措辞问题、AI化或不必要表达，并给出项目内首选。

本轮独立分析。输出Markdown，最后附一个完整JSON对象，schema如下：
```json
{"reviewer_id":"aishuo_minimax_blind","round":1,"projects":[{"project_id":"...","candidate_reviews":[{"candidate_id":"...","scores":{"事实准确性":1,"研究设计逻辑完整性":1,"中国注册临床方案语体自然度":1,"术语稳定性":1,"可直接进入医学修订的程度":1},"fact_errors":[],"terminology_or_regulatory_issues":[],"ai_like_or_unnecessary_phrasing":[],"required_edits":[]}],"preferred_candidate_id":"...","preference_reason":"..."}]}
```
