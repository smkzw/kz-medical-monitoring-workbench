# 医学写作参考资料真实最小批次候选与执行合同

日期：2026-07-25  
性质：只读源文件盘点与下一主线执行准备  
结论状态：**候选已选定；当前不可直接启动完整生产批次，须先关闭来源授权、快照/分诊和两项证据链缺口**

## 1. 结论

下一条主线应复用现有 preparation/translation batch，以两个真实工作台项目各一份原始 Protocol 形成最小二件套：

| 工作台项目 | 真实研究 / 原始文件角色 | 源文件类型 | OCR |
|---|---|---|---|
| `proj_user_4ef4aa3da246`（CRSwNP） | `NCT02898454`，EFC14280，Protocol | 125页原生文本 PDF | 不需要；任何意外 OCR 均应阻断 |
| `proj_my009_uc`（UC） | `NCT02819635`，M14-234，Protocol | 224页混合 PDF，12页为整页图像 | 需要；12页按200 DPI、GLM-OCR、最多8并发 |

该组合比“全扫描 PDF + 原生 PDF”更适合作为第一次生产批次：它既真实覆盖 OCR、横向复杂访视表、图示和长文档，又保留足够的原生标题结构，使现有章节规划器能形成可靠 segment manifest。

**本轮未启动服务、模型或下载，未写入运行库，未运行测试。** 唯一产品工作区写入是本报告和 workflow guard 任务上下文。

## 2. 候选 A：CRSwNP 原生文本 Protocol

### 2.1 原件身份

- 工作台项目：`proj_user_4ef4aa3da246`
- NCT：`NCT02898454`
- 文件角色：`protocol`
- 原始绝对路径：
  `/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/03_Protocols/【IL-4Rα】【Dupilumab】【Sanofi_Regeneron】【Phase3】【FDA已获批】【2019】【关键III期】【SINUS-24】【NCT02898454】【FDA已获批_NMPA未获批_EMA已获批_PMDA已获批】【Protocol】.pdf`
- SHA-256：`05242e7aaa7b28f8d86a844efaca56fbeb46d1e892ae52cbc7f693d86e613bf7`
- 大小：`1,534,076` bytes
- PDF页数：125
- 原生提取字符：336,891
- 零文本页：0
- 图像对象：2；drawing对象：1,247
- 内部身份：`AMENDED CLINICAL TRIAL PROTOCOL NO. 01`，EFC14280，dupilumab，版本1，批准日期`17-May-2017`，NCT正文明确出现。

本地文件名中的 `SINUS-24` 标签不是权威身份。内部标题、NCT、EFC14280和当前快照的官方标题均指向一项52周研究；后续合同必须以 NCT + 官方标题 + 协议号 + 文件 hash 为准，不能以人工文件名标签覆盖。

### 2.2 当前快照绑定

默认生产运行库中已有：

- `project_id=proj_user_4ef4aa3da246`
- `snapshot_id=wref_search_f695ab9e5565293eb9e7`
- `document_id=ctgov_NCT02898454_000`
- CT.gov声明文件名：`Prot_000.pdf`
- CT.gov声明大小：`1,534,076` bytes，与本地原件完全一致
- CT.gov文件日期：`2017-05-17`
- `rights_status=pending_review`

当前没有该项目的 preparation batch 或 artifact。authoring journey 的 `search_plan.latest_snapshot_id` 已指向该快照，但 `corpus_triage.status=pending`，候选相关性仍未形成 preparation 所要求的当前确认。

### 2.3 OCR与章节预期

- 预期 `zero_text_pages=[]`、`ocr_recovery_pages=[]`。
- 若生产提取意外选择任何页面进入 OCR，先停止并核对本地 hash、下载 hash、PyMuPDF版本和 anomaly 检测原因。
- TOC有连续顶层 `1` 至 `16`：
  Flow Charts、TOC、Abbreviations、Introduction and Rationale、Objectives、Design、Selection、Treatments、Endpoints、Procedures、Statistics、Ethics、Monitoring、Additional Requirements、Amendments、References。
- 章节规划验收下限：连续顶层边界不得合并；正文关键映射至少覆盖 `synopsis / objectives_endpoints / eligibility / schedule / safety / statistics`。

### 2.4 内容校验预期

按 `evaluate_document_content()` 的五项检查：

1. `study_identifier`：应为 `match`，正文含 `NCT02898454`。
2. `indication`：应为 `match`，正文与快照均含 CRSwNP/nasal polyposis。
3. `document_type`：应为 `match`，标题和多类 protocol anchor 均明确。
4. `source_metadata`：正常 CT.gov ingest 时应为 `match`；若改走 manual upload，则只能是人工来源记录。
5. `document_version_date`：正常 CT.gov ingest 时应匹配 `2017-05-17`。

预期自动状态为 `confirmed`。任何 `needs_review/mismatch` 不得在批次内自动 override。

## 3. 候选 B：UC 混合文本/扫描 Protocol

### 3.1 原件身份

- 工作台项目：`proj_my009_uc`
- NCT：`NCT02819635`
- 文件角色：`protocol`
- 原始绝对路径：
  `/Users/smkzw/Documents/朗来项目资料/竞品分析/UC/JAKi Upadacitinib AbbVie/【NCT02819635 IIb-III期 诱导+维持】方案.pdf`
- SHA-256：`befe4a584e794514ead94cc796a9bb2d65539705ab8e0feba5df7ea8de53b740`
- 大小：`7,374,278` bytes
- PDF页数：224
- 原生提取字符：约405,188
- 内部身份：M14-234 Protocol Amendment 7，upadacitinib，Phase 2b/3，日期`10 May 2021`，正文第1页明确出现 `NCT02819635`。

### 3.2 OCR范围

直接 PDF 盘点确认以下12页没有原生文本，且每页含全页图像：

`143, 145, 154, 190, 191, 192, 193, 194, 198, 199, 218, 219`

直接渲染观察：

- 第143页含AE收集期正文和 Figure 5，不能按空白页忽略。
- 第190页是横向 `Study Activities` 访视表，含 Screening、Week 0-16、PD/unscheduled visit 等列，属于必须做结构连续性核对的复杂表。

执行合同：

- 模型必须精确为 `GLM-OCR-bf16`。
- 渲染固定 `200 DPI`，不得降采样。
- 12页先顺序渲染，再以 `ThreadPoolExecutor(max_workers=8)` 发起 OCR。
- 预期 `ocr_recovery_pages` 覆盖全部12页；若某页 OCR 返回空文本，必须逐页视觉确认其是否确为纯空白/全遮挡，不能静默减少。
- 每页证据至少记录：physical page、PNG SHA-256、DPI、model、profile digest、OCR text SHA-256、字符数、selection reason、span ID、视觉 QC 结论。

### 3.3 章节预期

原生 TOC 保留充足标题结构。预期顶层：

- `1.0` Title Page
- `2.0` TOC
- `3.0` Introduction
- `4.0` Study Objective
- `5.0` Investigational Plan
- `6.0` Complaints
- `7.0` Protocol Deviations
- `8.0` Statistical Methods and Determination of Sample Size
- `9.0` Ethics
- `10.0` Source Documents and CRF Completion
- `11.0` Data Quality Assurance
- `12.0` Use of Information
- `13.0` Completion of the Study
- `14.0` Investigator's Agreement
- `15.0` Reference List
- Appendices A-K，其中 C-F 为访视/活动复杂表。

章节规划必须保留 `3.0-15.0` 的连续顶层边界；第190-194页 OCR 内容应并入 Appendix C，不得成为孤立 `unmapped` 章节或跨入相邻 appendix。

### 3.4 内容校验预期

1. `study_identifier`：应为 `match`，第1页含 `NCT02819635`。
2. `indication`：应为 `match`，标题和正文明确为 ulcerative colitis。
3. `document_type`：应为 `match`，标题明确为 Clinical Study Protocol。
4. `source_metadata`：取决于后续锁定快照。若为 CT.gov公开文件，应核对 URL、document ID、大小和 hash；若为 manual upload，应保留 `user_uploaded` 来源。
5. `document_version_date`：应记录 Amendment 7 / `10 May 2021`，并与快照元数据比较。

`proj_my009_uc` 当前没有锁定 writing-reference snapshot，也没有 finalized triage/discovery confirmation，因此今天不能创建合法 preparation batch。

## 4. 未选用的全扫描原件

另有一份更纯粹的全扫描候选：

- `/Users/smkzw/Documents/朗来项目资料/竞品分析/UC/miR-124 Obefazimod Abivax/【NCT03093259 IIa期 8周诱导期】方案.pdf`
- SHA-256：`3fc705d66d074b487ce8b9a5b31a7152e1494ab882842c9fa6d3072fe4916be0`
- 52页，52/52页零原生文本，52个整页图像
- 直接页面观察确认内部为 ABX464-101 Phase IIa Protocol，TOC含13个顶层章节

它本轮不进入最小生产批次。现有 OCR recovery 对每页只生成一个
`section_heading=""`、`ich_m11_anchor="unmapped"` span；52页会被
`build_document_planner_segments()` 合并为单个 front-matter segment，Flash
无法在一个 segment 内恢复13章。应先增加可审计的 OCR 页内标题/segment
边界，再把它作为第二轮全扫描压力样本。

同目录的 `方案(OCR).pdf` 和 `方案(OCR)(1).pdf` 属于预处理版本，已明确排除，
未作为来源或内容判断依据。

## 5. 来源与使用授权门

两个 PDF 正文均带 sponsor confidentiality 限制；CRSwNP 快照还明确记录 `rights_status=pending_review`。本地可读取不自动等于可进入产品模型。

启动前必须形成一条持久授权记录，至少说明：

- 文件获得渠道和当前持有人使用权限；
- 是否允许为本项目目的发送给本地 GLM/Hy-MT2 和获批私有 DeepSeek；
- 是否允许保留译文、OCR页图和审计 hash；
- 不允许时立即更换同研究的可授权公开版本。

不得让模型或批次代码替用户解释 sponsor 条款。

## 6. 真实产品调用点

### 6.1 GLM-OCR

- `WritingReferenceExtractionService.extract()` 在原生提取后选择零文本页和 anomaly 页。
- `_recover_pages_with_ocr()` 用 PyMuPDF 顺序渲染，固定200 DPI；OCR调用最多8并发。
- `main.py::_writing_reference_ocr_runner()` 校验 PNG、模型和 DPI，再调用：
  `LocalOcrGateway.run(OcrRequest(image_bytes=..., image_suffix=".png"))`
- 网关请求：
  `${WORKBENCH_OMLX_BASE_URL:-http://127.0.0.1:8000/v1}/chat/completions`
- 模型：`GLM-OCR-bf16`。

现有缺口：200 DPI PNG 只保存在内存 `page_images`，网关只返回 text；产品未持久化 PNG 或 PNG hash。它因此不能直接满足发布优先级要求的“OCR页200 DPI原图”证据。

### 6.2 DeepSeek章节识别

- `main.py::_flash_planner_adapter()` 接收有界 segment manifest。
- `_translation_ai_env()` 强制：
  `provider=deepseek`、`model=deepseek-v4-flash`、`transport=openai_compatible`。
- planner只能返回连续 segment range，内部 span ID 不发送给模型。
- 结构错误有一次有界纠正重试；只有存在至少4个可信连续顶层标题时才允许确定性 fallback。

### 6.3 Hy-MT2正文翻译

- `main.py::_hy_mt2_translator_adapter()` 调用：
  `${WORKBENCH_OMLX_BASE_URL:-http://127.0.0.1:8000/v1}/chat/completions`
- 精确模型：
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`
- `temperature=0`，每次最多6个对齐 translation units，单次 `max_tokens=4096`，HTTP timeout 300秒。
- 章节先按约3,000字符分 chunk，长单元目标约1,200字符；输出必须保持 `[[CMS_SEG_NNNN]]` 对齐标记。
- 正文不得由 Flash/Pro 翻译、改写或补写。

### 6.4 DeepSeek译后整合/QC

- `main.py::_flash_qc_runner_adapter()` 使用 `deepseek-v4-flash`。
- Flash是非创作审核器，`integrated_text` 必须逐字回显 Hy-MT2 对齐草稿；任何改写会被确定性门拒绝或回退到有效 Hy 草稿。
- 普通章节在50,000字符输入限制内单次 QC；超限才分 integration windows。
- 数字、单位、比较符、否定、时间窗、终点层级、量表、表格和标记对齐均由确定性门复核。

### 6.5 DeepSeek Pro现状

`ai_execution_policy.py` 允许结构/翻译上层任务使用 Flash 或 Pro，但当前产品接线没有真正的 per-stage Pro 选择器：

- 允许的 Pro 精确模型名为 `deepseek-v4-pro`；
- planner常量固定 `deepseek-v4-flash`；
- QC常量固定 `deepseek-v4-flash`；
- `_translation_ai_env()` 每次强制 Flash；
- 没有批次字段、item字段、升级判据、Pro重跑入口或 Pro lineage。

因此“Flash确实不能胜任时仅将上层环节切换为 Pro”目前是**未实现的发布缺口**，不能通过手改全局环境变量绕过。

## 7. 现有 API 与 job 入口

### 7.1 准备批次

- `POST /api/projects/{project_id}/medical-writing/references/preparation-batches`
- `GET /api/projects/{project_id}/medical-writing/references/preparation-batches/latest?snapshot_id=...`
- `GET /api/projects/{project_id}/medical-writing/references/preparation-batches/{batch_id}`
- `POST /api/projects/{project_id}/medical-writing/references/preparation-batches/{batch_id}/retry`

创建体：

```json
{
  "snapshot_id": "<locked_snapshot_id>",
  "actor": "medical_manager",
  "idempotency_key": "<stable-key>"
}
```

准备批次是 FastAPI background task，不进入统一 durable-job API。它从 finalized triage 或 confirmed discovery basket 派生 NCT/文档范围，客户端不能提交任意 NCT 列表。

手动文件入口仅用于快照中的候选：

- `POST /api/projects/{project_id}/medical-writing/references/documents/upload`
- `POST /api/projects/{project_id}/medical-writing/references/documents/{artifact_id}/extract`
- `POST /api/projects/{project_id}/medical-writing/references/documents/{artifact_id}/extraction-reviews`
- 必要时人工：`POST .../{artifact_id}/content-validation/override`

### 7.2 翻译批次

- `GET /api/projects/{project_id}/medical-writing/references/translation-batches/preview`
- `POST /api/projects/{project_id}/medical-writing/references/translation-batches`
- `GET /api/projects/{project_id}/medical-writing/references/translation-batches/latest?snapshot_id=...`
- `GET /api/projects/{project_id}/medical-writing/references/translation-batches/{batch_id}`
- `POST /api/projects/{project_id}/medical-writing/references/translation-batches/{batch_id}/retry`

创建体：

```json
{
  "snapshot_id": "<locked_snapshot_id>",
  "glossary_version": "cms_regulatory_zh_v1",
  "anchor_filter": [],
  "actor": "medical_manager",
  "idempotency_key": "<stable-key>"
}
```

翻译创建返回 `durable_job_id`。统一 job API：

- `GET /api/projects/{project_id}/medical-writing/jobs/{job_id}`
- `GET /api/projects/{project_id}/medical-writing/jobs/{job_id}/result`
- `POST /api/projects/{project_id}/medical-writing/jobs/{job_id}/cancel`
- `POST /api/projects/{project_id}/medical-writing/jobs/{job_id}/retry`

翻译 preview 前必须同时满足：

- authoring journey 的 triage 已 finalized；
- snapshot 是当前锁定 snapshot；
- 最新 preparation batch 已终态且 retained IDs 一致；
- artifact 当前有效；
- validation 为 `confirmed/user_overridden` 且绑定当前文件 hash/state/extraction；
- 最新 extraction review 为 `approved`。

## 8. 当前配置与缺口

本轮只读检查的 shell 环境中，以下变量均未显式设置：

`WORKBENCH_RUNTIME_DIR`、`WORKBENCH_OMLX_BASE_URL`、`WORKBENCH_OMLX_API_KEY`、`WORKBENCH_AI_BASE_URL`、`DEEPSEEK_API_KEY`、`WORKBENCH_AI_DEPLOYMENT_PROFILE`、`WORKBENCH_AI_TIMEOUT_SECONDS`。

这不证明现有常态服务进程也未配置；本轮没有读取进程秘密或调用状态接口。

启动前必须确认：

1. `WORKBENCH_RUNTIME_DIR` 明确指向隔离验收目录或经授权的生产目录，不能误用 `implementation/workbench/runtime`。源码默认实际为：
   `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime`
2. oMLX `/v1/models` 中同时存在精确 GLM-OCR 和 Hy-MT2模型；不接受别名。
3. `DEEPSEEK_API_KEY` 已配置且不写入报告。
4. `WORKBENCH_AI_DEPLOYMENT_PROFILE` 为允许私有临床文档的批准 profile。
5. DeepSeek状态接口报告 Flash 直连路由已配置。
6. Pro上层升级缺口已实现并有独立 lineage；否则首批只能规定“Flash失败即停止”，不能假称已有 Pro fallback。
7. OCR PNG持久证据缺口已关闭；否则不能满足本批次最终验收。
8. `proj_my009_uc` 的 snapshot/triage/related decision 已建立。
9. 两份 sponsor/rights 使用授权已记录。

## 9. 失败恢复合同

| 失败点 | 当前行为 | 下一动作 |
|---|---|---|
| preparation服务重启 | running item 标为 `service_restart_interrupted`/failed | 调 preparation batch `/retry`，只领失败项 |
| 公开下载/来源漂移 | item failed；当前 artifact 不得继续 | 核对 URL、大小、hash和版本；不得用本地同名文件静默替换 |
| 内容 `needs_review/mismatch` | `review_required` | 医学经理对照原件；仅有明确依据才 override |
| OCR任一 future 异常 | 本次 extraction 整体失败，当前实现不逐页持久化 OCR中间结果 | 修复配置后重跑 extraction；预期12页会全部重做 |
| OCR返回空页 | 该页不生成 recovered span | 逐页视觉核对；关键图表页空结果必须阻断 |
| 章节 planner 输出非法 | 同一 immutable manifest 仅一次纠正重试 | 仍失败则 terminal；当前没有真实 Pro升级 |
| Hy-MT2瞬时失败 | translation item `failed_retryable` | durable job/batch retry；已完成 immutable chunk 可复用 |
| source/validation/review lineage 变旧 | item terminal stale-lineage | 新 extraction + validation + structure review；不能重用旧候选 |
| deterministic fidelity blocked | `fidelity_blocked`，不自动重试 | 单元级医学核对/修订，不走“仅重试失败项” |
| durable worker wake失败 | sweeper可恢复 queued job | 轮询统一 job；不要重复创建相同 idempotency batch |
| 取消或租约丢失 | cooperative cancel/ownership guard 阻止晚写 | 根据 job状态显式 retry；保留旧attempt证据 |

## 10. 持久证据目录

产品权威状态继续落在指定 `WORKBENCH_RUNTIME_DIR`：

- `writing_reference.sqlite3`
- `medical_writing_durable_jobs.sqlite3`
- `writing_reference_artifacts/`
- `writing_reference_translation_ai_runs.jsonl`（当前默认生产目录尚不存在，首次真实运行应创建并核验）

本批验收证据建议固定为：

`records/active_slices/medical_writing_reference_real_batch_20260725/`

目录合同：

```text
source_receipts/
  crswnp_nct02898454.json
  uc_nct02819635.json
api/
  <project_id>/journey_snapshot_triage/
  <project_id>/preparation/
  <project_id>/translation/
ocr/
  proj_my009_uc/<artifact_id>/page_0143_200dpi.png
  proj_my009_uc/<artifact_id>/page_0190_200dpi.png
  proj_my009_uc/<artifact_id>/...all_12_pages...
  proj_my009_uc/<artifact_id>/ocr_lineage.json
  proj_my009_uc/<artifact_id>/visual_qc.json
translation/
  <project_id>/<artifact_id>/plan.json
  <project_id>/<artifact_id>/chunks.json
  <project_id>/<artifact_id>/integration_qc.json
  <project_id>/<artifact_id>/fidelity.json
recovery/
  preparation_restart_retry.json
  durable_job_restart_retry.json
admission/
  medical_reviews.json
  corpus_admissions.json
final/
  batch_acceptance.json
```

不复制用户原始 PDF；`source_receipts/*.json` 记录绝对路径、SHA-256、文件大小、页数、NCT、角色、版本和授权记录。证据 JSON 不持久化密钥或不必要的完整正文。

## 11. 现有 QC/测试能证明什么

本轮全文读取的核心测试覆盖：

- preparation 的锁定范围、PNH/RA分支、确认复用、失败项重试、重启恢复和202接口；
- translation 的双门、lineage陈旧、部分失败、幂等、fidelity blocked、无自动审核/准入；
- OCR路由、200 DPI、8并发、精确模型 allowlist；
- document planner 的 segment range、顶层边界、一次纠正重试、不可变 plan/chunk/integration；
- Hy对齐单元、复杂表行、数字/单位/比较符/否定/量表/时间点保真；
- durable job 的租约、取消、ownership loss、失败恢复和跨项目隔离。

但它们使用 deterministic fakes，不能替代本批真实模型证据。

`scripts/qc/writing_reference_admission_e2e.py` 目前：

- 硬编码两个旧 translation ID；
- 从医学批准开始，随后执行 admission 和 DeepSeek Pro写作修订；
- 不覆盖 search/preparation/download/OCR/chapter translation；
- 会产生审批、准入和修订线程写入。

因此不能直接用于本批准备/翻译验收；只能在隔离运行时、替换为本批新 translation ID 且医学审核已完成后，作为末端 admission QC。

## 12. 下一条最安全的执行命令/接口序列

### 12.1 第一条命令：只做运行前状态核对

在授权、Pro升级和 OCR PNG证据缺口关闭后，先执行：

```bash
API_BASE=http://127.0.0.1:8911
curl -fsS "$API_BASE/api/health"
curl -fsS "$API_BASE/api/medical-writing/reference-translation/ai-status"
curl -fsS "http://127.0.0.1:8000/v1/models"
```

通过条件：API健康；translation AI status 为已配置的直连 DeepSeek Flash、body model 精确为 Hy-MT2 且 `deepseek_body_translation_allowed=false`；oMLX模型清单含两个精确模型。任何一项失败都不创建批次。

### 12.2 接口顺序

1. `GET .../{project_id}/medical-writing/authoring-journey`，确认当前项目和 snapshot。
2. `GET .../references/search-snapshots/{snapshot_id}`，核对 NCT、document ID、日期、大小、rights。
3. 通过现有 competitor-triage/discovery confirmation 流程形成当前 retained candidate 和 related decision；不得直接改数据库。
4. `POST .../references/preparation-batches`，每个项目各一次，使用稳定 idempotency key。
5. 轮询 preparation batch GET；只对 `failed` 调 batch retry。`review_required` 进入人工内容核对。
6. 对每个当前 extraction 做原文/页码/章节/12页 OCR/复杂表视觉核对，再 `POST .../extraction-reviews` 批准；不得批量自动批准。
7. `GET .../translation-batches/preview`；确认两项目均无 `validation_* / structure_review_* / unmapped` 意外排除。
8. `POST .../translation-batches`；记录 `batch_id + durable_job_id`。
9. 轮询统一 job GET 和 translation batch GET；瞬时失败只走 batch/job retry，`fidelity_blocked` 转人工。
10. 完成逐章医学审核后才可 admission；最后在隔离运行时改造并运行 admission QC，不自动写正式方案正文。

**当前下一动作不是启动模型，而是先关闭四个阻断项：两项目来源授权、CRSwNP当前分诊确认、MY009 UC锁定快照/分诊、Pro升级与OCR PNG持久证据。**
