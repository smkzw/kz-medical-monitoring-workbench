# 测试轮1R会商修复计划（P0群：监查项目从零建项路径断裂）

来源：三测试者报告（/tmp/kz_test_round1/report_[ABC]_*.md，2026-09-21）。
主线（既有项目深链）已验证可用；断的是**新用户从零到监查的UI路径**。

## 根因链
1. 新建项目对话框只有"医学写作项目"类型 → 监察员被建成MW-*写作壳。
2. 用户项目无监查模块绑定语义：看板模块矩阵/来源台账/侧栏对无绑定项目
   全部显示"功能未配置"或不含监查。
3. 数据接入向导（选文件夹/上传/识别结构/确认字段）存在但被
   "监查项目就绪"门挡住——未接入的项目恰恰需要它。
4. r7 resolve_project走project_resolver别名表：新项目接入前不可达
   （admission upload用同一resolver——需验证admission是否可为新项目
   初始化工作区并注册别名，test_medical_monitoring_r7_data_admission
   用固定项目名，需实测新id）。

## 修复垂直切片（按序）
### F1 建项类型（前端+存储）
- 新建项目对话框增加"医学监查"项目类型；UserProjectCreateRequest加
  `modules: list[str]`（默认["medical_writing"]，监查选["medical_monitoring"]）；
  user_projects表加modules列（迁移：ALTER+默认回填）。
### F2 监查意图的项目解析与工作区初始化（后端）
- r7 admission路由对`modules`含medical_monitoring的用户项目放行：
  resolve前若id不在别名表→调admission初始化（建workspace骨架+注册别名）
  或提供`POST /api/projects/{id}/monitoring-bootstrap`。
- 实测新项目id走/data-admissions/upload的行为，确定最小放行点。
### F3 接入向导门（前端）
- MedicalMonitoringProductLoop对`modules含monitoring但未就绪`的项目
  显示数据接入向导（上传listing→attempt→映射确认→物化→完成），
  而非"功能未配置"死胡同。
### F4 模块矩阵（前端/后端）
- 看板modules列表按用户项目modules字段渲染medical_monitoring入口。
### F5 503写作闸门盖侧栏（前端CSS）
- writing-runtime-gate-page改为仅覆盖内容区（不挡侧栏导航热区）。
### F6 方案导入反馈（写作侧，可后置）
- "导入并提取"加超时/进度/失败态；至少失败可见。

## 再测条件
F1-F4落地后重派三测试者（换新研究：可从研究方案库选Povor BE/TLL-018
生成第三profile），验证从零建项→上传→监查闭环。

## 第一轮作废与转交记录
- 轮1（作废）：入口5173错误→三报告测的是入排审核应用（已存档
  *_round1_invalid_wrongapp.md）。入排应用自身P0（解构草稿失败job=
  653676a/1414ed57、项目名冲突阻断提交、xlsx无入口）属另一子系统，
  转交其负责方。

## F2实测进展（2026-09-21，端到端API序列已验证至第4步）
1. POST /api/projects（modules=["medical_monitoring"]）→ proj_user_*创建 ✅（F1）
2. manifest自动含medical_monitoring绑定（intake_pending）→ r7可达 ✅（F2/F4）
3. POST r7/data-admissions/upload（multipart xlsx）→ attempt创建，10表/590行profile ✅
4. POST r7/data-admissions/{a}/study-documents/analyze（方案docx）→ 202，
   双AI（document-authority primary+verifier）后台完成 ✅（需mapping_gate
   常量对齐现役路由——已修，见下）
5. **当前卡点**：POST .../study-documents/resolve（batch_id）返回
   state=reviewing不推进promoted，尽管双AI job已completed且候选已产出。
   待查：advance()对completed job的候选聚合条件（_ANALYSIS_GENERATION
   版本匹配/候选挂载位置）。
6. ready后链路：mapping-candidates→mapping-draft→adjudicate→confirm→
   facts（fact_routes POST /data-admissions/{a}/facts）→监查模块就绪。

## mapping_gate常量对齐（已完成）
- MONITORING_C3_MAPPING_PROVIDER: zhipu-coding-plan→cms-router（主）
- MONITORING_C3_VERIFIER_PROVIDER: deepseek→opencode-go（盲核）
- 历史身份zhipu保留进PRIMARY_RUNTIME_PAIRS（旧作业/回执可重验）
- 文档权威工作流身份校验因此修复（此前500：runtime identity does not match）
- 注意：eCRF文档为readiness必需项（protocol+ecrf required_now=true），
  测试场景包需补合成eCRF docx（generate_test_listing.py待扩展）。
