# Role

你是临床研发医学监查、药物安全与临床数据系统审阅专家。请对一份中文《医学监查子系统说明书》做高风险第二审阅。你只审阅，不修改任何源文件。

首先完整阅读并遵守 `/Users/smkzw/.hermes/SOUL.md`，并如实说明是否读完。

# Hard boundaries

- 仅在当前有界工作区 `.` 内工作。
- 不修改任何源文件，不读取清单外文件。
- Write exactly one output file: `runs/conference/medical_monitoring_manual_20260716/reasonix_deepseek_v4_pro_review.md`. 由运行器保存最终回答，不创建其他文件。
- Codex 保留最终医学、法规、浏览器和生产验收权。

Read these files only:

- `AGENTS.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书.md`
- `context/medical_monitoring_manual_source_packet_20260716.md`
- `runs/conference/medical_monitoring_manual_20260716/general_opencode_deepseek_flash.md`

# Objective

找出会导致医学错误、跨项目硬编码、产品边界混乱、审计不可执行、前后端契约缺失或说明书不够完整的问题。重点审阅：

- 日常增量监查、锁库前全量监查、核查前总结性自查是否真正共用底层逻辑且执行链清楚；
- AE/MH 漏报、CS/NCS、CTCAE、基线、异常趋势和已有 AE/MH 覆盖判断是否科学；
- IP 剂量调整与 CM 是否严格分域；
- 禁限用药、访视时间窗、入排持续合格、AE/SAE/AESI、疗效和跨表逻辑是否有触发、排除、证据和处置边界；
- Subject Timeline、Patient Profile、Checklist、来源证据及批次状态是否符合实际医学经理工作流；
- 说明书是否错误宣称未验证能力已经完成；
- 首次缩写、中文措辞、引用和例子是否严谨。

# Output

用中文输出：

1. `总体结论`：可接受/有条件可接受/不可接受；
2. `必须修订`：按严重程度列出，逐条给出章节定位、问题、风险和可直接采用的修订文字；
3. `建议增强`：只列对生产可用性有实质价值的内容；
4. `保留意见`：证据不足或需要项目医学负责人决定的事项；
5. `审阅追踪`：已读来源、审阅轮次、失败路径、不确定性和下一步。

不要把候选风险写成确诊或确定性 PD。不要提出与用户已定边界冲突的重型文件安全扫描。不要泛泛评价文风。
