# Codex Execution Review: mw_scale_registry_discovery_20260717

## Boundary

本次 gate 只验收“量表注册能力的代码/真实方案/权利来源调查”这一执行批次，不验收完整产品能力。生产代码、最终临床判断、量表权利结论、浏览器验收和用户交付均由 Codex 负责；执行者和管理者无生产写权限。

## Verdict

有条件接受并结束本次调查执行，不重跑 worker_01/03。worker_02 的原始方案提取作为本切片的项目事实依据；worker_01 的“green-field registry”判断被拒绝；worker_03 仅保留保守默认值和来源线索，权利结论改由 Codex 读取权利人官方页面独立核验。

## Worker Outputs

- `worker_01`: 不接受其平行 `scale_registry` 建议。它未识别本轮已落盘的 `MedicalWritingAssessmentInstrumentUse`、影响映射和前端编辑器，不能作为当前代码 SSOT。
- `worker_02`: 接受其 RUX、D001、PNH 三份原始 DOCX 的量表清单和段落/表格定位。RUX 覆盖 IGA/BSA/EASI/SCORAD/DLQI/CDLQI/Itch NRS/PROMIS，D001 覆盖 PASI/PGA/BSA/DLQI，PNH 仅能从方案摘要确认 FACIT-F 且必须标记 `source_synopsis_only`。
- `worker_03`: 部分接受。接受“未知即 `metadata_only`、不得推断开放复制”的保守产品默认；拒绝把 Wikipedia 或方案内出现评分方法视作开放复制授权，也拒绝其单枚举分类，因为产品已经分离 rights、translation、full-text policy 与 medical confirmation。

## Manager Assessment

接受管理复核对现有集成面的纠偏：研究内使用对象已经位于 `picos.assessment_instruments`，后续只沿现有契约补候选提取、SoA/附录联动和导出约束。管理者要求重跑 worker_01 的目的已由 Codex 直接代码核验覆盖，重跑不会产生新的决策证据，因此不执行。

## Hermes And Grok Use

Hermes aishuo MiniMax-M3 承担三个独立调查工作包，结果按 worker 分别评审，没有把多模型意见当作事实。Grok Build `grok-4.5` 仅作为执行管理者检查遗漏与冲突，不承担最终裁决。Codex 拒绝了错误的平行 schema 与缺乏权利人证据的开放复制主张，并完成独立代码、测试和官方来源复核。

## Codex Independent Verification

- 代码：核对 `models.py` 中 source/rights/translation/project-use 四层契约、唯一 ID 和 endpoint binding 校验；核对 authoring journey 影响映射及 `AssessmentInstrumentEditor`。
- 测试：`tests/test_medical_writing_assessment_instruments.py` 与 authoring journey 测试共 22 项通过；前端生产构建通过。
- 官方来源：Cardiff DLQI 页面明确量表受版权保护、不得变更措辞/格式/设计，商业使用按许可处理；FACIT 官方条款明确量表及翻译受版权保护且翻译需许可；现阶段均按 `metadata_only` 落地。EASI/SCORAD/PASI 等未取得权利人开放复制声明前同样不自动升级。
- 未完成：真实浏览器保存重载、DOCX 附录输出门和候选提取仍在后续实施项中，因此本 review 仅关闭“调查执行”，不表示整个量表能力完成。

## Cleanup Decision

保留 worker_02 的解析脚本与 compact evidence，供真实项目 fixture 和定位复核；执行框架的 prompt/stdout 在 review gate 通过后归档。其余生产无关临时文件不进入长期工作区。
