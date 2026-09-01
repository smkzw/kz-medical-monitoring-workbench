# 真实参考原文最小批次 Codex 验收

日期：2026-07-25  
状态：候选样本与技术执行边界部分接受；来源授权硬门不接受

## 接受

- CRSwNP `NCT02898454`：125 页原生文本 Protocol，作为不应触发 OCR 的对照样本。
- UC `NCT02819635`：224 页混合 Protocol，12 个整页图像页按 200 DPI、`GLM-OCR-bf16`、最多 8 路并发恢复。
- OCR 只负责图像页文字恢复；章节识别由 `deepseek-v4-flash`，正文翻译由 `Hy-MT2-30B-A3B-oQ8-MLX`，译后整合/QC 由 Flash，必要的上层任务升级才可使用 `deepseek-v4-pro`。
- Hy-MT2 译文、章节边界、数字/单位/否定/时间窗、复杂横向访视表和图表页必须保留可追溯证据。
- CRSwNP 项目已有冻结快照但分诊尚未形成 preparation 所需确认；UC 项目尚缺锁定快照与 finalized triage。这些是正式产品工作流前置条件。
- 当前 OCR 页 PNG 和 PNG hash 未持久化，且 Flash 到 Pro 的分阶段升级与 lineage 尚未实现，均属于真实发布缺口。

## 不接受

- 不把 sponsor confidentiality 或额外“来源授权确认”设置为产品批次的强制审批门。用户已明确：公司内文件和权威来源下载文件导入后直接可用，不做费时的安全性检查。
- 文件入口仅做基本信息和内容校验，包括研究标识、适应症、文件类型、版本和来源元数据。发生不匹配时给出充分提醒，并允许医学经理明确 override。
- 不增加“待医学批准”。医学经理主动选择、确认或 override 即构成当前工作流内的用户决定。

## 下一步

1. 先关闭 OCR 原图证据持久化与 Flash/Pro 上层升级 lineage。
2. 为 UC 建立真实 ClinicalTrials.gov 快照并运行独立 AI 分诊；完成 CRSwNP 当前快照分诊。
3. 通过内容校验后创建 preparation batch，再依次运行 OCR、章节规划、Hy-MT2 翻译、Flash/Pro 上层 QC 和语料库备选准入。
4. 全程使用产品独立 AI 和本地 oMLX，不得由 Codex 或执行模型代替系统能力。
