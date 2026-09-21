# 医学监查子系统工程交接文档（Handoff for Engineering Review）

- **交接基线**：main 分支 `30f8633`（2026-09-21）
- **审阅范围**：`a6d89ba → 30f8633` 共 27 个提交，35 个文件，+3553/−490 行
- **仓库**：https://github.com/smkzw/kz-medical-monitoring-workbench
- **文档目的**：供资深工程专家对近期全部改动做代码审阅（Code Review）。含改动清单、设计决策与理由、生产运行证据、已知问题与技术债、运维手册、以及提请审阅人重点关注的开放式问题。
- **诚实声明**：本文档区分三类陈述——`[实测]` 有生产/测试运行证据；`[代码审阅级]` 有代码与单元测试但未在真实端到端验证；`[待验证]` 尚未验证。

---

## 1. 系统一句话背景

本子系统是"医学经理工作台"中的**医学监查（Medical Monitoring）产品**：临床试验的 Data Listing（Excel 数据集）经确定性物化进入事实层，双独立大模型（主分析 + 独立盲核）对每位受试者做跨表医学线索分析（AE×化验矛盾、合并用药×病史逻辑、给药完整性等），结果经裁决/定向核实后发布为只读结果上下文（result-context token），前端以研究看板/受试者旅程/Query 工作区呈现。设计原则：AI lead、用户查看与确认；只产线索与 Query 草稿，不做审批流；未知与覆盖不足必须可见。

关键目录：
- `services/api/app/` — FastAPI 后端（main.py 组装；monitoring_ai_* 为双模型作业系统；ai_gateway.py 为模型传输层）
- `packages/medical_monitoring/` — 领域包（analysis/ 双模型分析；admission/ 数据接入；api/r7_product/ 产品路由；projections/ 事实→R5 产品投影）
- `frontend/src/features/medical-monitoring/` — 监查前端（React）
- `scripts/` — 运维与收尾脚本（dualvlm_*、generate_test_listing.py）

---

## 2. 近期工作年表（27 提交，按主题分组）

### 阶段〇：批跑基础设施与收尾链雏形（a6d89ba，基线前）
双 VLM 全量批跑（278 受试者 × 主+盲核两 cohort）的收尾脚本雏形、身份校验放宽（空 expected=不主张断言）、网关 UA/extra_headers 通用化。

### 阶段一：批跑卡点诊断与传输修复
- `ac353bc` **网关流式 SSE**：glm-5.3-flash@cms-router 对真实大载荷 100% HTTP 504。根因：本机 OmniRoute 中继按 `requestQueue.maxWaitMs=15000ms` 对已派发的非流式请求施加执行过期——48k token 证据包+深思考必然超时被杀，随后凭证冷却 429。修复：`OpenAICompatibleAiProvider` 默认 `stream:true`，复用 SSE 聚合。对照实测：同 59k token 载荷非流式 15s 被杀 / 流式 HTTP 200 全量 24k token 返回（5.3 分钟）。`[实测]`

### 阶段二：收尾链 v2 与批跑托管
- `210b5bc` 双 VLM 收尾链 v2（真对侧定向核实、p5 重试波、watchdog 托管）
- `541daeb` 全局哨兵防重复发布（后被 scoped 哨兵取代）
- `8703c78` watchdog resume 保活（僵尸租约回收）
- `a47f4bb` finalize 预检：批跑未全终态拒绝收尾（防旧自动化按过时映射早发布）

### 阶段三：外部审阅包 V3 整改（WP0A/WP0B/WP1/WP2）
外部资深程序员审阅包（kz_review_v3，基线 a47f4bb）列出 D-01~D-12 缺陷与 WP0~WP6 工作包。整改落地：
- `c22d5ad` **WP0A 传输完整性**（D-04/D-05/D-06/D-12，详见 §3.1）
- `d390ffa` **WP0B 收尾链整改**（D-01~D-03/D-07~D-11，详见 §3.2）
- `7d73600` **WP1 切片 1**：事实快照不可变清单 + 语义域边界（详见 §3.3）
- `fb8fd4a` `2a658a2` **WP2 切片 1/2**：事件结束日期、严重度来源三分、原始记录号（详见 §3.4）
- `b5b9433` WP0A 收敛修复：严格修复路径的截断/非对象正文策略
- `a5fd632` omlx 门界测试随传输统一补迭代协议

### 阶段四：批跑收官（生产验证）
p5 补考波（43 作业）→ finalize 自动链 → **发布**：804 条线索（783 accepted / 16 escalated / 5 unverifiable_gap），token `result-context:296971b6cc6540228365dacbbefa671e`。过程中实战修复 4 个生产 bug：
- `3f2d768` **focused 合同合同层收口**：定向核实"恰好 1 候选"只补了服务层校验，但输出信封还要过 `monitoring_ai_contracts.validate_candidates_for_job` 的同义 2-3 候选校验——169 个正确输出全部在该层被拒（115 失败）。修复按 business_key 侧别标记（`:focus:`/`:focus-p:`）识别定向核实。`[实测]`
- `8eb6937` **merge 状态归一**：仓库返回的 `job.status` 是枚举，`str(enum)` 永不等于 `"completed"`，导致 154 个已完成定向核实全部误标 `verification_failed`。取 `.value` 归一。教训：测试桩用裸字符串未暴露。`[实测]`
- `ded1bcb` fv 波路由别名自动清扫器（仅重试 `response_model_identity` 类失败，12 轮封顶）
- `1aad317` finalize 唤醒 URL 修正（BASE 含 `/r7` 产品面前缀，queue 控制面在其上层）

### 阶段五：测试轮（轮 1 作废 + 轮 1R）
- `23e1824` 测试基础设施：合成研究 listing 生成器 + 三测试者差异化场景指令
- `f7191dd` **项目归档能力**（软删除/恢复/列表过滤——既是清洁派发的硬需求，也是"用户无法清理旧项目"的可用性修复）
- `bb7faeb` 轮 1 作废与指令修正（派发者给错端口，详见 §5）
- `c84fb6e` `45c70ff` 轮 1R 三报告 + P0 群修复计划 F1-F6

### 阶段六：onboarding 垂直切片（修复进行中）
- `30f8633` **F1/F2/F4 后端**：用户项目 modules 字段、监查意图 manifest 绑定、mapping_gate 常量对齐现役路由（详见 §3.5）

---

## 3. 技术改动详解（按模块）

### 3.1 AI 传输层（`services/api/app/ai_gateway.py`，+593/−行级别重构）

**改动前问题**（审阅 D-04/D-05/D-06/D-12）：
1. SSE 聚合只拼 content，不验证终止合同——流里先输出可解析 JSON 再发 error 事件、或 `finish_reason=length` 截断、或连接无 `[DONE]` 中断，残留正文照常被接受为医学结论；
2. 模型身份解析与正文解析是两套容错（畸形 data 行在身份解析处裸抛 JSONDecodeError）；
3. reasoning_content 被静默回退为正文——中间推理可能恰好含合法 JSON 而被当医学候选；
4. 无总时限/字节上限——持续保活可无限拖延任务；
5. 视觉传输（monitoring_visual_transport）维护第二套 POST/重试/解析逻辑，且复制配置时丢失 stream/extra_headers。

**改动后**：
- `_parse_sse_stream()`：**单一解析状态**，一次扫描产出 content/reasoning_chunks/models/usage/finish_reason/saw_done/error_event/keepalive 与 malformed 事件计数。保活块（model=keepalive）与 usage 收尾块（空 choices）安全跳过；畸形业务事件计数后由终态合同判定失败（不静默丢 token）。
- `_extract_completion(body, truncation_policy)`：**终态合同**。`error` 事件→`provider_sse_error_event`；畸形事件→`provider_sse_malformed_event`；无 `[DONE]` 或无 `finish_reason`→`provider_sse_truncated`；`length`→`provider_response_truncated`。即使残留正文可解析 JSON 也不得当医学输出。仅有 reasoning 时→`provider_reasoning_only`（推理永不静默充当正文）。
- `_read_provider_response()`：流式逐行增量读取；**整调用绝对 deadline**（`WORKBENCH_AI_TOTAL_DEADLINE_SECONDS`，默认 1200s，单调时钟，保活不可延长）+ **累计字节上限**（`WORKBENCH_AI_MAX_RESPONSE_BYTES`，默认 128MB）+ socket 空闲超时三层。遥测记录真实首数据时间（不冒充首 token 时间）。
- `_post_and_parse()`：唯一 POST/重试/解析管道；重试只对 http/transport 类错误；截断策略钩子（默认 fail；严格修复模式选 repair，遥测标 `truncated_repair`）；`final_content_policy='raw'` 供严格修复路径不做宽松 JSON 对象强制。
- 视觉路径：`MonitoringVisualOpenAIProvider._run_completion` 改为**完全复用** `_post_and_parse`（删除第二套传输逻辑）；`visual_provider()` 复制清单补 `stream_enabled/extra_headers/total_deadline_seconds/max_response_bytes`；视觉请求补产品 UA 与 provider 特殊头。
- 环境旋钮：`WORKBENCH_AI_STREAM`（默认开）/`WORKBENCH_AI_TOTAL_DEADLINE_SECONDS`/`WORKBENCH_AI_MAX_RESPONSE_BYTES`。

**审阅关注点**：`_extract_completion` 的 JSON 分支对 `finish_reason=length` 且 policy=repair 时返回 content 并标记 `truncated_repair`——请审阅该宽松是否可被滥用（仅视觉 strict 路径 opt-in）；deadline 与字节上限的默认值是否合适。

### 3.2 双 VLM 收尾链（`scripts/dualvlm_finalize.py` 等，重写）

**v1→v2→v3 演进中的关键设计**：
1. **作业选择=按受试者配对的冻结身份校验**（D-01/D-02）：evidence_identity = 输入 revision JSON 中除 `batch_revision`（代际标签）与 `project_id` 外的全部绑定（sources 源内容 hash/mapping/rule/protocol/fact/risk_snapshot/source_binding 修订）的 SHA-256。同受试者主/盲核两侧身份一致才配对；旧代 completed 不静默晋升，未配对=可见缺口。
   - **实测坑**：首轮实现用原始 `input_revision_sha256` 配对——该 hash 混入了代际命名（`facts:...-r3` vs `facts:...-p4`），导致 99 对被误判 mismatch。改为剥离标签的 evidence_identity 后 124 对全对。**教训：身份指纹必须排除命名性字段。**
2. **稳定 finding_id**（`aemh-{subject}-{side}-{content_hash12}`）取代 zip/位置索引作为定向核实关联键；跳项原因全落账。
3. **定向核实四态**（merge_focused_verifications）：confirmed→accepted；refuted（data_gap 反证）→escalated 请用户裁决；insufficient_evidence→escalated；执行状态（missing/failed/timed_out/no_candidates）→escalated 但措辞明确"非医学反证"，不把技术缺口伪装成医学分歧。
4. **版本化 focused 子合同**：payload 注入 `focused_contract={version:"aemh-focused-v1", expected_candidates:1}`，服务端 `_parse_provider_output` 与合同层 `validate_candidates_for_job` 双点识别（**两点都必须识别**——见 §5 坑 1）。
5. **dry-run 零副作用**：不 import 生产 main（直连只读仓储）、`artifacts_dir=None` 不落盘、不碰队列/哨兵/发布。
6. **scoped 原子哨兵**：`/tmp/dualvlm_finalize_done.{project}.{selection_identity+artifact_sha8}.flag`，`O_CREAT|O_EXCL` CAS 获取，失败回滚释放；发布幂等键绑定分析工件 hash；publication 轮询替代固定 sleep(8)；result-entry 空 token 不记成功。
7. **精确 expected 清单预检**（D-09）：全映射文件作业集+project 过滤；空/缺失映射≠全部终态（p5 映射可缺省）。
8. **预算封顶**：每工作单元 p4 两次+p5 两次，watchdog 结构上保证无 p6。

**生产实测卡点与修复**（收官过程）：
- fv 波 90 分钟无人认领——finalize 子进程直写仓库提交后，API 侧 worker 只认 wake 事件。补提交后 resume 唤醒 + 等待窗 120→300 分钟（61a5dbf）。
- verifier 档案 `expected_response_model` 被清空 → `_response_model` 见空即拒，整波身份失败。改回 `deepseek-flash`（opencode-go 端点 ID 稳定，别名偏差本应失败重试）。**注意：settings store 每次读盘无缓存，改 JSON 即生效。**
- opencode-go 上游偶发返回路由别名（identity 不符）——既有惯例单轮重试即恢复；新增有界清扫器。

### 3.3 事实快照层（`packages/medical_monitoring/projections/facts_publication.py`）

1. **不可变清单加载**（替代目录 glob）：首次加载按"64 位内容 hash 命名 + 单表 JSON 形态"严格构建 `facts-manifest.json`（同表多文件取 mtime 最新，其余记 superseded，非事实文件记 skipped——旧 glob 实测会把 4 个 AI findings 工件当临床表吸入）；此后逐文件 SHA-256 校验、篡改 fail-closed。真工作区实测 62 表零混入。
2. **语义域边界**：未知表/列签名无法判定的表→`uncategorized/unclassified`（新增域，前后端契约同步登记），不再默认"方案偏离"；FW（花粉/天气）→未分类；NS（下次访视状态）、PC（采样）→未分类；IE/ICF/RAN→`eligibility_randomization`（资格评估非偏离）；真偏离签名（PDTERM+PDDAT）不变。
3. **事件时间诚实**：`*ENDAT` 精确结束日期如实解析保留（此前恒 None，治疗时长信息全丢）；留空=持续不明不补造；起始列显式优先 `*STDAT`。
4. **严重度来源三分**：R5RiskRecord 新增 `severity_source`（recorded=源记录载明/inferred=系统推定/unknown=源缺失）——AE 无 AESEV 不再伪装"中度"。
5. **原始记录号**：R5EventRecord 新增 `source_record_id`（listing 的 Block 顺序号），与源位置分离，重排/增量下 CM→AE/MH 跨表引用（CMAENO/CMMHNO）不漂移。

### 3.4 项目生命周期（`user_project_store.py` + `project_source_manifest.py` + main.py）

- **归档/恢复**：`DELETE /api/projects/{id}`（软删除，project_visibility 表）/`POST .../restore`；GET /api/projects 过滤已归档。
- **模块意图**：`UserProjectCreateRequest.modules`（medical_writing/medical_monitoring/eligibility_review 多选，默认写作）；user_projects 表加 modules 列（ALTER 迁移，旧行默认写作）。
- **监查意图 manifest 绑定**：`_user_project_manifest` 按 modules 注入 `medical_monitoring` 绑定（implementation_status=intake_pending）——一处改动同时打通 r7 项目解析（`_canonical_module_project_id` 走 manifest.module_binding）、模块矩阵、接入向导门三处。
- **实测**：建项→绑定→`POST /data-admissions/upload`（multipart xlsx）→attempt 创建（10 表/590 行 profile）→`study-documents/analyze`（方案 docx）→双 AI（document-authority primary+verifier）后台完成。`[实测至第 5 步]`

### 3.5 配置对齐（`packages/medical_monitoring/admission/mapping_gate.py`）

文档权威工作流身份常量钉在旧路由（zhipu-coding-plan/deepseek 直连），现役绑定已按用户指令迁移（cms-router/opencode-go）→ 对新项目文档分析直接 500 "runtime identity does not match its role"。修复：常量对齐现役（主=cms-router/glm-5.3-flash、盲核=opencode-go/deepseek-flash），历史 zhipu 对保留进 `PRIMARY_RUNTIME_PAIRS`（旧作业/回执仍可重验）。gate 测试簇 5 败→3 败（余 3 为陈旧断言，归对账批次）。

### 3.6 测试基建

- `tests/test_aemh_dualvlm_contracts.py`（4 例）：dry-run 零落盘/finding_id 稳定性/四态 merge 技术措辞/提交台账+合同标记
- `tests/test_facts_publication_manifest.py`（6 例）：未知表/PK 采样/FW/真偏离签名/清单排除混入/篡改 fail-closed
- `tests/test_facts_publication_event_time.py`（4 例）：结束日期/持续不补造/STDAT 优先/严重度三分/原始记录号
- `tests/test_ai_gateway.py`：+11 例（流式合同/错误事件/截断/推理隔离/deadline/字节上限/视觉传播/配置关闭）
- `tests/test_user_project_archive.py`（2 例）
- `scripts/generate_test_listing.py`：参数化合成研究 listing 生成器（CSU 荨麻疹 16 例/PSO 银屑病 14 例；中文表头交付形态；wide/long/matrix 三布局；内置一致性规则+植入医学矛盾如"3 级血小板降低 vs 化验仅轻度下降"）

**测试方法学**：每个缺陷先写失败回归再修复（本周期共 21 个新失败测试先行转绿）；直接受影响面套件全绿（gateway 64、visual 13、服务与映射 619、r5/r7 adapter+router 118、事实清单与时间 10、归档与合同 6）。

---

## 4. 生产运行证据（双 VLM 全量批跑收官）

- **规模**：278 受试者 × 主（glm-5.3-flash@cms-router，流式）+ 盲核（deepseek-flash@opencode-go）双 cohort
- **结果**：804 条线索 = **783 accepted / 16 escalated / 5 unverifiable_gap**；273/278 受试者通过 evidence_identity 配对（5 缺口可见）；**153 条单侧线索经真对侧定向核实确认**（escalated 169→16，"懒惰监察员"目标达成）
- **发布**：run:3699c3df85b21d61d45bf845，token `result-context:296971b6cc6540228365dacbbefa671e`；ego 浏览器验证查询工作区渲染通过（799 卡片+三态徽章+医学真实内容，如"AE 记'否'但合并用药氯雷他定指征'本研究疾病'"）
- **吞吐实测**：流式修复后 ~20 作业/小时（并行 2，约 3-4 分钟/作业，attempt-1 成功率 ~100%）

---

## 5. 踩坑记录（供审阅人评估工程质量文化的真实性）

1. **合同层双写**：候选数量合同存在于服务层与合同层两处——只修一处时另一处继续拒绝。教训：同一业务规则的多层实现必须在同一提交中同步收口，且失败信息应携带层标识（已加诊断后缀）。
2. **测试桩类型造假象**：merge 的状态比较在测试桩用裸字符串通过，生产返回 pydantic 枚举导致 154 个完成态误判。教训：测试桩应使用与生产相同的类型构造（或对枚举/字符串双形态做归一）。
3. **身份指纹混入命名**：input_revision_sha256 混入代际命名导致跨代配对 99 对误判。教训：冻结身份必须剥离标签性字段。
4. **唤醒衔接遗漏**：子进程直写仓库提交的作业，API 侧 worker 只认 wake 事件——retry 脚本有 resume 而 finalize 漏了，169 作业 90 分钟无人认领。教训：任何绕过 API 写库的组件必须自带唤醒。
5. **派发前未自检目标**：测试轮 1 因给错端口（5173=入排应用）整轮作废。教训已固化：派发指令必须含"打开后应看到的标题"自检项。
6. **小载荷探针≠真实载荷**：15 秒执行过期只杀大载荷——小探针全绿掩盖了主 lane 全灭。教训已沉淀：探针必须用接近真实体量的材料。

---

## 6. 已知问题与技术债（诚实清单）

### 6.1 未完成的修复（F1-F6 计划，`scripts/test_round1/round1R_fix_plan.md`）
- **F2 尾巴**：文档权威状态机停在"adjudication 完成、待 resolve 推进 promoted"（无 in-flight 作业，无损）。恢复链在 memory/§7。
- **F3/F4 前端**：接入向导门与模块矩阵的后端绑定已就绪（manifest 含 intake_pending），前端按 `implementation_status=intake_pending` 渲染向导即可，尚未接线。
- **F5**：写作 503 闸门盖侧栏热区——需浏览器现场诊断后再改 CSS（盲改有风险）。
- **F6**：方案"导入并提取"卡死无反馈（写作侧模块）——后置。

### 6.2 全套测试陈旧断言债（~90 例失败）
完整套件 8705 过/96 败。抽查证实几乎全部为**陈旧断言**（历史有意变更后未同步：旧模型供应商地址、thinking 档位、budget、映射仓储 payload 形态收紧后 fixture 未跟上、前端空项目断言等），非本轮回归。已列"测试基线对账"专项：逐簇核对意图后修断言/fixture，**禁止盲目放宽**。其中 mapping-gate 簇已从 5 败降至 3 败（常量对齐顺带修复）。

### 6.3 明确未做的产品工作项（后续工作包）
- **WP1 剩余**：语义映射/表单定义驱动全部消费者（当前仍有部分名称映射字典）；日期列按语义映射绑定（现以 STDAT 优先级启发式过渡）
- **WP2 剩余**：每事件无条件 RiskRecord 的取消（事件/观察/风险三类分离——涉及严重度枚举契约扩展，本次只落地了 severity_source 铺垫）；episode 聚合不删原始记录
- **WP3**：证据包扩容（去"每表前 6 行/每字段 24 项/每值 120 字符"截断）——**排序约束：必须在当前发布之后随新快照代双 cohort 重跑一起做**（中途改会使全部身份配对失效）；删除"每人 2-3 候选"合同；全适用受试者覆盖；`_clues_agree` 命题级核验
- **WP4**：统一工作区（跨视图状态贯通、风险↔事件↔来源双向定位、severity_source/覆盖状态入前端）
- **WP5/WP6**：分层性能实测、临时脚本（dualvlm_* 三脚本）安全退出主路径并入正式控制器
- **五项目铺开**：其余四项目接入 + 真实兼容增量 + 用户验收清单；备份恢复、一键启动、性能基线
- **场景包缺口**：合成 eCRF docx 生成（document readiness 必需 protocol+ecrf 双文档）

### 6.4 已知运行时事实（运维需知）
- 端口：MM 工作台前端 **5177**（5173 被入排审核应用占用）；API 8910；OmniRoute 中继 20128
- opencode-go 上游偶发路由别名（identity 不符）——单轮重试即恢复；fv_alias_sweep.py 可兜底
- 主项目 runtime 含患者数据，`runs/` 在 .gitignore（数据治理边界）；GitHub 仅源码+文档
- 前端深链形态：`/monitoring?project_id=<id>&view=queries&result_context_token=result-context:<hex>`（project_id 形式可绑定；project_ref 形式渲染但项目待确认——**审阅人可评估统一参数名**）

---

## 7. 恢复链（无损暂停点）

当前暂停点：文档权威状态机停在"adjudication 完成、待 resolve 推进 promoted"（无在途作业，CSU 验证项目 proj_user_8b6c59351f70）。
1. 启 API：`cd implementation/workbench && WORKBENCH_RUNTIME_DIR="$PWD/runs/phase_c_mgk10_authority_v2_20260905/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8910 --log-level warning > /tmp/mm_api_8910.log 2>&1 &`
2. `POST /api/projects/proj_user_8b6c59351f70/modules/medical-monitoring/r7/data-admissions/stg-db2dd4f192464c81835c7df8b7926aa3/study-documents/resolve`，body `{"batch_id":"mmbatch_5415dbecc95549d6fb71705e"}` → 预期推进 promoted
3. 之后：mapping-candidates → mapping-draft → adjudicate → confirm → facts 物化 → 监查模块就绪 → F3/F4 前端接线 → 重派测试

---

## 8. 提请审阅人重点关注的开放式问题

1. **`_extract_completion` 的 repair 策略**：length 截断正文交"单轮修复"是否可被 prompt 注入滥用？仅视觉 strict 路径 opt-in 是否足够？
2. **focused 合同的 business_key 识别**：`:focus:`/`:focus-p:` 子串匹配是否够稳？是否应升级为 job 元数据字段？
3. **绝对 deadline=1200s 默认**：对慢速思考模型是否偶发误杀？当前生产 ~4 分钟/作业，余量大，但换更慢路由需调。
4. **evidence_identity 剥离 batch_revision/project_id**：是否存在两个"同名不同数据"的合法场景被误判同源？（当前实现下 sources 源 hash 变化会改变指纹，理论安全，请复核。）
5. **`_load_domains` 首载自动写 manifest**：投影类在 API 进程内写运行时文件（原子替换），是否应改为物化管线显式产出？
6. **哨兵仍在 /tmp**：按审阅意见应迁入持久仓储（project+frozen input+policy 键）——当前实现是 scoped+原子 CAS 的文件版折中，标注为技术债。
7. **mapping_gate 常量式身份校验**：每次路由迁移都要改常量——是否应改为"角色绑定即真相"的动态校验？

---

## 9. 快速验证命令（审阅人自测）

```bash
# 单元/合同测试（本次新增+受影响面，全部应绿）
WORKBENCH_RUNTIME_DIR="$PWD/runs/phase_c_mgk10_authority_v2_20260905/runtime" \
  .venv/bin/python -m pytest tests/test_ai_gateway.py \
  tests/test_monitoring_visual_transport.py tests/test_aemh_dualvlm_contracts.py \
  tests/test_facts_publication_manifest.py tests/test_facts_publication_event_time.py \
  tests/test_user_project_archive.py tests/test_mm_c3_mapping_confirmation.py -q
# 预期：全部通过（约 105 例）

# dry-run 只读性验证（批跑已收官，预检通过，会走完整只读裁决；期间工件 mtime 不变）
.venv/bin/python scripts/dualvlm_finalize.py --dry-run

# 发布结果 API 探针（需先启 API）
curl -s "http://127.0.0.1:8910/api/projects/proj_mgk10_sar_real/modules/medical-monitoring/r7/results/result-context%3A296971b6cc6540228365dacbbefa671e/overview" | python3 -c "
import json,sys; d=json.load(sys.stdin)
from collections import Counter
print(Counter(f['state'] for f in d['projection']['query_findings']))"
# 预期：{'accepted': 783, 'escalated': 16, 'unverifiable_gap': 5}
```

---

*本文档由构建 Agent 于 2026-09-21 撰写；所有 `[实测]` 陈述的原始证据保存在 /tmp/kz_test_round1/（测试报告）、/tmp/dualvlm_watchdog.log（批跑日志）与 git 提交历史中。*
