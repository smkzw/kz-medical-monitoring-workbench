You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current workspace root (`.`).
- Do not read or modify production paths.
- Do not edit files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/hermes_tfl_pv_source_labels_20260713.md`.

Read these files only:
- `context/tfl_pv_source_labels_20260713_context.md`

Task:
逐条审查context中列出的中文标签和提示。按`原文 | 结论（保留/替换） | 建议文本 | 理由`输出；仅在确有临床试验医学经理语境、TFL或PV边界问题时替换。不要改文件。

Output schema:
1. `# Hermes Chinese Label Review: tfl_pv_source_labels_20260713`
2. `## Boundary Check`
3. `## Label Review`
4. `## Boundary And Terminology Findings`
5. `## Recommended Final Copy`
6. `## Uncertainty`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Keep the plan scoped to Hermes execution, not Codex final review.
