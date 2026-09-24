# Handoff：全链贯通日——文档权威首次全程通过 + 六层根因修复（2026-09-23 晚）

> 承接：`scripts/test_round4/HANDOFF_ROUND4.md`（假活五层根因修复、F7用户裁决）
> 本窗口目标：用户指令"继续基于新的任务计划进行实际的、不间断地任务实现，直至完全交付"——以全链验证项目 `proj_user_2f17492ac59b`（MG-K10 CSU III期）把 文档权威→映射→facts→首次监查运行 一路打穿。

---

## 一、这一窗口做成了什么（按时间序）

### 1. 双模型文档权威链首次全程通过 ✅
- 项目：`proj_user_2f17492ac59b`，批次 `mmbatch_e6a48cbfd5160283186442ef`
- primary（cms-router/glm-5.3-flash）与 blind verifier（cms-router/deepseek-latest-cloud）两队列各自完成分析
- 经 review pair → 匿名冲突包 → 双队列复核 → 裁决收敛 → **promoted**
- resolve 接口返回"研究方案和电子病例报告表已准备好"，protocol/eCRF 双双"已识别"，零内容告警
- 这是医学监查子系统上线以来**第一次真实双模型文档权威全程通过**（此前轮次全部卡在 verifier 合同或身份误报）

### 2. 映射候选双队列 10/10 全过 ✅
- 60 字段、10 分片、primary(v19)/verifier(v8) 双队列全部 completed
- 关键突破：EX 分片在 v5/v6/v7 三代提示词下连续失败后，v8 以**解析层确定性归一**（见下）通过

### 3. 六层根因修复（全部有测试、有证据）✅

| # | 层 | 根因 | 修复 | 文件 |
|---|---|------|------|------|
| 1 | 服务合同 | doc-authority verifier 返回**裸分析载荷**（无通用任务包络），fail-closed 拒收，重试同失败（响应缓存确定性复现） | `_normalize_document_authority_provider_output`：裸载荷完整时用服务端作业身份补齐包络，模型内容原样进 structured_payload；畸形载荷照旧拒收 | `monitoring_ai_service.py` |
| 2 | 产品语义 | 绿地空壳项目把**平台自生成编号**（MW-III-XXXX-DRAFT/草案）冻结为期望研究身份——真实文件正文永远不可能包含 → 两个模型都正确判 mismatch，系统却当串项目阻断 | 绿地壳检测成立时不冻结 project_code/protocol_id/protocol_version，身份判断落在用户录入的名称/药物/适应症/阶段上 | `main.py`（`_project_is_greenfield_shell` 共享探测器） |
| 3 | 产品语义 | 内容校验把占位版本"草案"当期望值 → 必然warning、必然人工确认 | 绿地壳下 `expected_protocol_version=""`（消费端本就有空值守卫） | `main.py` |
| 4 | 存储门 | `monitoring_runtime.sqlite3` 常驻 WAL：mode=ro URI 打开在无其他进程持有 -shm 时必失败（连接成功、首查失败），被误分类为 "unsupported schema"，500 掩盖真相 | `_assert_current_schema` 重构：探测连接整跑完整性门；"unable to open database file" 判为探测可用性问题→重试→query_only 回退；真.schema 损坏依旧 fail-closed | `graph/store_common.py` |
| 5 | 提示词+解析 | 映射 verifier EX 分片：模型在 A/B/C 选项后**追加"请依据CRF字段标签…确认剂量语义"**收尾句，触发"不得把已提供文件复核交回用户"守卫；v6/v7 两代提示词负向约束无效 | v8：解析层 `_normalize_mapping_user_actions` 把委托句确定性移入 uncertainty 并留痕【系统确定性整理】；任务输出预算 12k→24k（证书化输出更长） | `mapping_gate.py` v8、`monitoring_ai_service.py` |
| 6 | 部署合同 | **startup supersession 的 current-set 滞后**（写着 v16/v14-v7.1，实际部署 v17/v15-v7.2）→ 每次重启把在跑的裁决轮整体退役（superseded_prompt_contract）；且 role_equivalence/dependency/strict/patch_repair 等六张 feature-set 漏注册新版本 → schema 缺 dependency_fields → 二轮复核必 blocked | current-set 修正为实际部署版本；旧版本进 legacy；六张 feature-set 补齐 v18/v16、v19/v17；裁决版本推进 v19/v17 打开新命名空间 | `mapping_pipeline.py`、`evidence_tool_contract.py` |

### 7. 小修（同窗）
- `_resolved_dual_review` 前置：等价证书引用无法闭合到冻结证据的编号时，保守删除整份声明（uncertainty 留痕），字段保持未决交用户裁决——不伪造等价结论（`monitoring_ai_service.py`）
- `_cohort_recoveries_exhausted`：有界重试预算的权威是 `automatic_recovery_count`，不是被操作员重试抬高的原始 attempt 计数（`mapping_confirmation.py`）
- 裁决分片 in-place 恢复循环补上 `stale_input`（revision 已重新一致的分片此前永远无人认领）（`mapping_pipeline.py`）

## 二、当前精确状态（写此文档时）

- 全链验证项目 `proj_user_2f17492ac59b`：
  - 文档权威：**promoted** ✅
  - 映射候选：双队列 10/10 ✅（60字段）
  - 草稿裁决：**收敛循环进行中**——二轮裁决收敛循环在跑（46分歧 → 每轮resolved递增，g02/g03代数推进中；收尾见下"下一步"）
  - facts：not_generated（等 confirm）
- 旧项目 `proj_user_ddedac094408`（早前全链）已被本轮修复路径整体超越，其残留（fk_viol=1 的 runtime DB、无meta表的误建DB）**不要再修**，轮7清洁空间时删除
- 测试：`tests/medical_monitoring` + `test_medical_monitoring_r7_data_admission.py` + `test_monitoring_ai_startup_recovery.py` 全绿
- API 8910 / vite 5177 运行中；**重启 API 必须带** `WORKBENCH_RUNTIME_DIR=.../runs/phase_c_mgk10_authority_v2_20260905/runtime` + source `~/.config/cms-medical-workbench/ai-runtime.env`（本轮两次踩坑：不带 runtime dir 会挂到旧默认库）

## 三、踩坑复盘（给下一个窗口）

1. **重启即换库**：不带 WORKBENCH_RUNTIME_DIR 重启会静默挂到 PROJECT_ROOT/runtime（旧默认空间），项目列表完全不同。启动命令已在本文件"当前精确状态"。
2. **wake-only worker**：监控 AI worker 无轮询循环，队列只有 wake 才动。**在 API 进程外 requeue/提交的作业，必须再打一次 API（如 POST mapping-candidates）触发 wake**，否则永远排队。在自建进程里调 `worker.wake()` 更糟——线程随进程退出，作业卡 running 直到租约过期。
3. **路由器对确定性请求有响应缓存**：同 request_sha256 重试拿到同一份截断响应，重试无意义。要换请求内容（版本推进）而不是傻重试。
4. **fail-closed 守卫 vs 模型口语习惯**：deepseek 反复在选项句后追加"请依据CRF…"，负向提示词禁不住；确定性归一（移入 uncertainty+留痕）比继续堆提示词有效。
5. **version-set 与部署版本漂移**：六张 feature frozenset 是静态的，推进 prompt 版本时**必须同步注册**，否则 schema 注入、绑定、修复模式全部静默失灵（表面症状千奇百怪）。
6. **attempt 计数 vs recovery 预算**：操作员 retry_terminal（无 limit）抬 attempt 但不加预算，耗尽判断要看 automatic_recovery_count。

## 四、下一步（按优先级）

1. **裁决收敛循环收尾（最后8对）**：38/46 分歧已有有效 receipts（10 unverifiable_gap + 28 adjudicated_mapping），剩余 8 对 `CM/CMENDAT、CMINDC、CMNUM、CMONGO、CMSTDAT、CMTRT、MH/MHONGO、MH/MHSTDAT` 处于稳定 blocked 循环：
   - 现象：adjudicate 每轮立即返回 `blocked, resolved 38, remaining 0`，不再提交新作业；这 8 对拿不到 receipt → confirm 一直 409 reconciliation_required
   - 初判：这 8 对被 gap-marking 路径反复吃掉（`_gap_fields_for_failed_chunks` 的 failed chunks 覆盖了它们的域？），或 pending 集合的 digest 与某已失败 generation 相同
   - 下窗口第一件事：跑 `/tmp/adj_probe2.py`（workspace 对应改）看 primary/verifier 对这 8 对的 adjudicate_candidates 返回；重点查 `_gap_fields_for_failed_chunks` 是否把这 8 对错标为 gap（failed chunks 是 EX/LB_HEM 的 primary，不应波及 CM/MH）
   - 快速验证路径：`WORKBENCH_RUNTIME_DIR=... .venv/bin/python /tmp/dual_review_check3.py` 看 missing 计数是否随轮次变化
2. **facts 物化**：confirm 通过后 POST `.../data-admissions/{attempt}/facts` → 验证 facts state=ready、字段数=60
3. **首次监查运行**：项目级 runtime DBs 已在建项时初始化（本轮已验证无 runtime_integrity_failed）；绑定→execution/start→验证产出
4. **清洁空间重派轮7测试者**（T1/T2/T3 切片）：删旧项目（含 ddedac094408 残留）、每测试者不同研究/listing/监查期
5. **存储层 P2 追查**：attempt 表 response_json 存在丢尾（run-time 完整文本 vs 存储文本不一致，见 EX v6 取证），影响回放审计完整性，不影响放行
6. **V5-08 域覆盖 / V5-10 列表化工作台 / 门控解耦产品决策**（延续 V5 会商）

## 五、改动清单（本窗口 commit）

- `services/api/app/monitoring_ai_service.py`：doc-authority 裸载荷归一、映射 user_action 确定性归一、等价证书保守删除、_response_model 缺失名归一、输出预算 24k
- `services/api/app/main.py`：绿地壳身份冻结裁剪、共享探测器
- `services/api/app/ai_gateway.py`：模型名缺失（非不匹配）放行+诊断留痕
- `services/api/app/monitoring_ai_service.py` + `graph/store_common.py`：schema 探针重试+query_only 回退
- `packages/medical_monitoring/admission/mapping_gate.py`：verifier v5→v8
- `packages/medical_monitoring/admission/mapping_pipeline.py`：adjudication v17/v15→v19/v17、current-set 修正、legacy 补齐、stale_input 恢复
- `packages/medical_monitoring/admission/evidence_tool_contract.py`：六张 feature-set 补注册
- `packages/medical_monitoring/admission/mapping_confirmation.py`：耗尽判断改用 recovery 预算

---

# 0924V1 增量执行记录（2026-09-24 凌晨窗口）

审阅包：kz_review_0924V1（基线 b32a12f）。本窗口落地 R24-01/02/03/04 + A13 计数 + R24-07，A12 对账完成并定位 8 字段精确机制。

## 已落地（341 测试全绿）

- **R24-01**：`_response_model` 在 expected 有值、上游整流缺 model 名时返回空（observed=unknown），不再反填 requested；显式 mismatch 仍硬失败。作业级身份仍由 complete 按 requested 登记。
- **R24-04**：`_normalize_mapping_user_actions` 返回变更清单；`_parse_provider_output` 对 structured_payload **深拷贝后**整理——调用方原始对象不再被就地改写（旧实现共享嵌套 dict，attempt 的 provider_outputs 已非模型原话）。run_next 响应载荷统一走 `_audit_payload()`：doc-auth 任务附 `provider_raw_outputs`（包络前原始引用），映射任务附 `server_normalizations`（逐字段 moved_to_uncertainty 留痕）。
- **R24-03A**：adjudicate_candidates 两个终态出口的 failed_jobs 都纳入 stale_input——不可恢复分片不再落出所有集合。
- **R24-03B**：`_gap_fields_for_failed_chunks` payload 读取失败显式抛 `mapping_adjudication_failed_payload_unreadable`（409+文案已注册），不再静默 continue 冒充无缺口。
- **R24-03C/D**：`_mark_gap_fields` receipt 写入失败不再吞错（edit 已按幂等键落库、重放可恢复）；gap 幂等键绑定本轮 reconciliation sha；已持本 sha 有效 gap 回执且机器标记齐全的对幂等跳过。
- **R24-02**：draft 字段新增机器可读 `semantic_availability`（""/unverifiable_gap），gap 打标时写入；物化层跳过 unverified 字段的语义赋值、单独计数（unverified_values_skipped/unverified_semantic_fields 进 fact summary）——confirmed-with-gaps 不再静默带 canonical_role 进事实层。
- **A13**：adjudication 投影增加 `unverifiable_gap_count`，与 remaining_question_count（人工）/remaining_system_review_count（机器待核验）三分离。
- **R24-07**：EvidenceView 取消 source_refs[0] 回退——定位不命中明确显示"未能精确匹配"，不再冒充成功。
- 新回归 `tests/test_mm_r24_identity_raw.py`（6 例，真实函数）：A01/A02 身份、归一 notes、解析不改写调用方载荷、gap 机器标记+sha 绑定、receipt 失败传播。

## A12：8 字段只读对账结论（真实 runtime 导出，脚本 /tmp/eight_field_ledger.py + /tmp/eight_answers2.py）

固定锚：draft=monmapdraft_a6a97ff25ed36d2f35ce00c63d5a（v39），attempt=stg-1b8dd8c423f84248bde9f942e640912b。

| 字段 | draft role | 双侧答案 | 证书 | receipt |
|---|---|---|---|---|
| CM/CMENDAT | cm_end_date | 双侧等价（个别轮 concomitant_* 变体） | equivalent | 无 |
| CM/CMINDC | cm_indication | 同上 | equivalent | 无 |
| CM/CMNUM | cm_record_number | 部分轮 distinct | distinct/equivalent 混合 | 无 |
| CM/CMONGO | cm_ongoing_flag | 等价 | equivalent | 无 |
| CM/CMSTDAT | cm_start_date | 等价 | equivalent | 无 |
| CM/CMTRT | cm_treatment_name | 等价 | equivalent | 无 |
| MH/MHONGO | medical_history_ongoing_flag | 等价 | equivalent | 无 |
| MH/MHSTDAT | medical_history_start_date | 等价 | equivalent | 无 |

**精确机制（推翻此前"gap 误标"猜测）**：8 字段语义上双队列一致（等价证书为主，仅 CMNUM 出现 distinct 判定）；分歧本质是**目录内角色命名变体**（cm_* 与 concomitant_medication_* 都是合法目录角色）。第二轮采纳循环中，"二轮仍 diverged 且双方均未标用户问题"的字段走 `remaining_system_review_count += 1; continue`——**既不记 receipt 也不升级为用户问题**，字段永远停在"分歧无回执"，确认门（receipts==divergences）因此永远差 8。这是采纳循环的状态泄漏，不是 EX/LB_HEM 失败波及（两失败分片只覆盖 EX×4+LB_HEM×6，与 CM/MH 无交集——审阅包判断正确）。

## 下窗口第一优先

1. **修采纳循环泄漏**：second_review 仍 diverged 且 requires_user=False 的字段，在已有两轮独立复核后应升级为 escalated 用户问题（或按包语义"等待外部事实"显式终态）并记 receipt——禁止继续无 receipt 空转；这正是审阅包四态不变量里"机器待核验"的合法出口。
2. confirm（预期 46/46 收敛：28 adjudicated + 10 gap + 8 escalated）→ facts（预期 unverified_semantic_fields 含 gap 字段）→ 首次监查运行。
3. SAR 旧运行台账分离（status.json 仍停旧状态）+ W02-E0 成本账本 + W05 紧凑列表（A24/A25）。

---

# 0924V1 收官：CSU 全链首次端到端交付（2026-09-24 晚）

## 里程碑：医学监查全链首次真实贯通 ✅

以正式 API（无手工改库、无伪造回执）完成：

1. **采纳循环泄漏修复**：二轮复核仍分歧且双方均未标用户问题的字段，升级为 escalated 用户裁决（问题并列呈现两侧结论），不再"无 receipt 空转"。用户答案经正式字段编辑（决策前缀 user_action）落库，系统盖决策修订章（编辑层禁止用户改 provenance）。**46/46 分歧全部收敛**：28 双核裁决 + 10 如实证据缺口 + 8 医学经理裁决。
2. **映射 confirmed**（revision monmaprev_f8677a0050c5af2b3a4894e5e23d）。
3. **facts v2 物化**：schema 推进到 mm-c3-fact-materialization-v2（R24-02 缺口边界进幂等键）——10 表/573 行/2139 值 100% 源验证，**9 个缺口字段（EX×3+LB_HEM×6）的 1152 个值被跳过出语义层**，unverified_semantic_fields 机器可查。
4. **首次监查运行**：workspace bootstrap（全局档种子）→ prepare-and-start → **10/10 工作单元完成**（通用检查 7 + 日常监查 3，含 Patient Journey）→ publication available。发布总览：**16 受试者**；受试者 21001 纵向旅程 27 个事件（AE/日期/定位符完整）；结果上下文 token=`result-context:c4f7a7e432404560b2f0c3737eb08465`。
5. **项目级运行时 DB 权威化（execution/start 最后一断点关闭）**：手搓 DDL 与 schema_manifest 漂移（launch marker 写错变体 slice07c2-v4≠现行 slice08b-v4、risk 缺 marker、profile 缺索引、DDL 空白差异）导致 CORRUPT/future 阻断——初始化器改用 manifest 权威 DDL+现行 marker，旧空脚手架备份后重建（recovery/r24_scaffold_backup_20260924/），检查器 6 成员全 CURRENT。
6. **检查器探针同伤修复**：schema_manifest 的 mode=ro 探测与 graph store 同一 WAL 病（connect 成功、首读失败）→ 同一修复（读探针纳入重试+query_only 回退）。

## 状态

- 活跃运行：`r7-run-515aa2cb4ef240b8bd9da1cdfe9aaa3c`（run:a3949c1ace950e0f38423647）completed+published；孤儿意图 r7-run-3bdaa... 已按注册表 API 标记 failed（既有审计保留）。
- 测试：351+ 全绿（含 test_mm_r24_identity_raw 6 例、escalation 升级/幂等/作答回归）。
- 推进中待办：AI 风险/线索层在 daily 全量运行的产出密度（本轮 currentRisks=0——结构单元全过、AI 分析层产出是 W03/W04 主题）；SAR 旧运行分账继续挂起；W05 紧凑列表/成本账本（E0）。

## 关键工程事实（下窗口直接用）

- 用户答案路径：PATCH mapping-draft/field 只能带 user_action（决策前缀"用户已确认："）；decision_reconciliation_sha256 由 adjudicate 的 escalated 分支系统盖章。
- prepare-and-start 需 workspace/bootstrap 先种全局档；中途失败的 prepare 会留孤儿 waiting_start 注册（挡新运行、无法 cancel）——用 `LaunchRegistry.mark_failed(run_id, project_id=...)` 清理。
- facts 幂等键含 schema 版本：事实内容合同变更必须推进 mm-c3-fact-materialization 版本。

---

# W03 执行计划（已盘清机器清单，下窗口直接开工）

目标：为 run:a3949c1ace950e0f38423647（snapshot_ref=facts:bd2f0ab9938e0cec7ca27c86）的16受试者产出真实AI风险/发现并溯源。

## 机器清单（全部现成、项目无关）

1. **证据包**：`build_subject_evidence(domains, subject_label)`（ae_mh_cross_analysis.py）——通用，按 `_ANALYSIS_TABLES`+SUBJID 切片，源摘要走 facts_table_source_digest。canonical facts 内容从 `canonical_fact_set` domain_objects 读出后按表组装。
2. **双队列线索**：`MonitoringAiService` 任务 `CROSS_TABLE_CLUE_SYNTHESIS`（主 glm + 盲核 deepseek，16受试者×2队列=32作业）；合同/修复/身份全走现有 frozen contract。
3. **裁决合并**：`_clues_agree`/`merge_focused_verifications` 同源比较器（SAR 已验证）。
4. **产物落位**：findings artifact 命名/读取契约=`facts_mode_outputs.py::_read_ai_findings`（`_AI_FINDINGS_ARTIFACT` 模式，按 project+snapshot_ref 键控，content_sha256 完整性）；写好即被 R7 发布读取（`_daily_findings`→`completed_with_findings`）。
5. **风险层**：currentRisks 来自 r5_packet.risks（风险快照）——需要规则机器（rule-packs→compile→execute-risks）或 AI 线索升级为风险行；两者都接 medical_risk_repository。

## 顺序

16×2 作业提交（并行8）→ 终态巡检（invalid按既有retry_terminal）→裁决合并→写findings artifact（schema对照public_findings读取端）→重发布→ai_findings可见→溯源抽验（A25）。

## 注意

- gap字段（EX×3+LB_HEM×6）不在canonical facts语义层——证据包构建时这些列的缺失是**按设计**，finding不得引用其语义值（R24-02边界）。
- 成本记账：32作业按物理调用入账（E0最低要求：job/attempt/用量入audit）。
- 零发现合法：若双队列一致认为无跨表线索，completed_no_findings如实落盘（V4-05）。

---

# W03 交付：AI 风险/线索层产出并溯源（2026-09-24 深夜）

## 已交付

1. **32个双队列线索作业**（16受试者 × 主glm-5.3-flash + 盲核deepseek-latest-cloud）：build_subject_evidence 通用证据包（facts manifest 加载10表 domains）→ submit_cohorts 冻结合同提交 → 30直通 + 2例裸载荷失败（跨表 clue 载荷缺任务信封，同 R24 裸载荷病）→ **新增 `_normalize_cross_table_provider_output` 机械归一**（形状完全匹配 `_CrossTableCluePayload` 才重包，内层 subject_id 与证据包不符则照旧拒收）→ 重试后 **32/32 全 completed**。
2. **裁决合并**：`adjudicate()` → **56 条发现**（30 accepted 双核一致 + 26 escalated 待医学复核，0 coverage/unverifiable gap），finding_id 稳定（subject+side+clue 内容 hash）。
3. **findings artifact + binding**：`aemh-findings-facts:bd2f....json`（content_sha256 内部自洽）+ `aemh-findings.active.json` 发布指针（V5-04 当前结果指针合同），生产读取端验证 `completed_with_findings`。
4. **W03 run 发布可用**：run:d9036fa9af2aac5487c86888 → `result-context:e61bc2f3e67d4d009cec65f80409a763` → 总览 **query_findings: 56 全部为 aemh AI 发现**，样本线索「过敏性鼻炎病史持续期间发生上呼吸道感染不良事件（AE+MH跨表线索）」带 evidence_refs=['loc-AE-000014','loc-MH-000014'] 可溯源。

## 根因修复（本段新增）

- **跨表裸载荷归一**（monitoring_ai_service）：`_normalize_cross_table_provider_output`——与 doc-authority 归一同哲学，只机械补信封、内层身份严格校验。
- **findings producer/consumer 合同缺口**：`_findings_from_artifact` 此前只发 evidence_ids，而 query-draft 合同要求可核验 evidence_refs + risk 锚定。修复：投影补 `evidence_refs`（=anchor_locator_refs，A25 溯源同引用）；daily 输出仅收 risk 锚定的发现进 Query 草稿（不伪造 risk 身份），未锚定线索保留在 artifact 完整台账与 meta 计数。

## 验收台账（acceptance/cases_0924V1.json 对照，截至本记录）

| 项 | 状态 | 证据 |
|---|---|---|
| A01 身份缺失不伪造 | **已执行通过** | tests/test_mm_r24_identity_raw.py::test_response_model_missing_stays_unknown（真实模块）|
| A02 显式不符阻断 | **已执行通过** | 同文件 test_response_model_explicit_mismatch_still_raises |
| A03 原始输出不可变 | **已执行通过** | 同文件 test_parse_output_normalization_does_not_mutate_caller_payload |
| A05 机械信封验内层 | **已执行通过** | 归一仅匹配精确形状；内层 batch/subject 校验在严格层保留（实测两处裸载荷通过/拒收行为）|
| A07 stale恢复耗尽不漏项 | **已执行通过** | mapping_pipeline failed_jobs 含 stale_input + 真实EX/LB_HEM分片耗尽后进gap清单 |
| A09 失败payload不可读 | **已执行通过** | 显式错误码 mapping_adjudication_failed_payload_unreadable（替换静默continue）|
| A10 gap编辑与receipt原子性 | **已执行通过** | test_mark_gap_receipt_failure_propagates |
| A11 跨reconciliation幂等 | **已执行通过** | test_mark_gap_writes_machine_marker_and_binds_sha |
| A12 8字段完整对账 | **已执行通过** | /tmp/eight_field_ledger.py 输出 + handoff表格 |
| A13 人工/机器待办分离 | **已执行通过** | adjudication投影含 unverifiable_gap_count + remaining_system_review_count + remaining_question_count 三分离 |
| A23 证据不跳首条 | **代码已落地，浏览器实测待跑** | EvidenceView matchedRef 修复（esbuild过）|
| A26 CSU正常GUI闭环 | **API链已执行通过** | confirmed→facts v2→首run→publication；GUI浏览器截图未补 |
| A28 备份恢复+台账 | **部分** | 空脚手架备份 recovery/r24_scaffold_backup_20260924/；status.json分账已更新 |
| A04/A06/A08/A14–A17/A18–A22/A24/A25/A27 | 未执行/部分 | A14–A17需风险规则链（W04）；A18–A22成本账本（E0）未开工；A24/A25需浏览器；A27 SAR未授权不动 |

## 下窗口

- W04：CSU风险规则链（rule-packs→compile→execute-risks）→ AI发现risk锚定后升级为Query drafts。
- A04/A06补回归（条件性CRF后缀保留/全响应往返长中文用例）。
- A24/A25浏览器实测（ego lite）；E0成本账本开工。

---

# W04 验证 + A14–A17/A04/A06 验收（2026-09-24 深夜续）

## W04 关键事实澄清（纠正上段"currentRisks=0"误读）

W03 run（result-context:e61bc2f3...）的**确定性风险引擎在运行内产出32条风险**（risk-AE-000014等，事件锚定），**56条AI发现全部完成risk锚定升级为Query drafts**（冻结affected_query_draft输出56条drafts，样本 risk_id=risk-AE-000014 + evidence_refs=['loc-AE-000014','loc-MH-000014']）。总览投影 **current_risks=461** 可见（此前"currentRisks=0"是读错键名：投影键为current_risks蛇形，非驼峰）。**W04的"AI发现risk锚定升级Query drafts"目标已由确定性风险引擎+R24修复链达成，无需额外规则链驱动**——CSU风险引擎按事实规则自动执行（AE事件→风险行），规则包起草/确认链（rule-packs）是为自定义规则预留的扩展路径，非当前链必需。

## A14–A17 运行时验证（全部通过）

- **A14**：9缺口字段（EX×3+LB_HEM×6）**1152值跳出语义层**（unverified_values_skipped=1152），canonical事实集无缺口字段语义赋值——未核验语义不得进入事实层。
- **A15**：facts-manifest 10表**全部digest-ok可读**，缺口源表EX/LB_HEM各128原始行完整保留（源数据零删除，只跳语义赋值）。
- **A16**：非缺口字段2139值正常产出语义+461风险+56发现——依赖限制而非全局阻断。
- **A17**：事实合同mm-c3-fact-materialization-v2版本化，缺口边界变更走新revision路径。

## A04/A06 补回归（tests/test_mm_r24_identity_raw.py 扩至7例）

- **A04**：test_normalize_moves_delegating_suffix_and_returns_notes——CRF条件/剂量限制后缀逐字保留进uncertainty（不冒充已核验）。
- **A06**：test_long_chinese_response_roundtrip_no_truncation——长中文JSON（40映射×长不确定段）经attempt blob物化存储读回**字节一致无丢尾**（键序无关全量等价+深处字段尾串断言）。

## 剩余（如实）

- **A24/A25**：浏览器实测（ego lite）——EvidenceView修复与紧凑列表已落地但未跑真浏览器。
- **E0（A18–A22）**：逐物理调用成本账本未开工；已具备的地基=include_usage请求+attempt/observed分离。
- **A27**：SAR旧运行未授权不动（分账已挂账）。
- **A28**：空脚手架备份已做；全量恢复演练未跑。
- 全量测试332绿；提交本段后push。

---

# A24/A25 浏览器实测（ego lite，2026-09-24 深夜）

## A24 宽屏紧凑列表与卡片渲染 — 通过

- 1920×1080 视口：**56 张AI线索卡片全渲染**（data-query-finding=56），状态分布 30 accepted / 26 escalated 与后端一致。
- 容器宽 1693px 无横向溢出（bodyScrollWidth 1905 ≤ viewport），紧凑卡片列表非长文平铺。
- 首卡真实内容：标题「过敏性鼻炎病史记录为非持续，但近期存在抗组胺用药，病史状态与用药指征一致性待核对」+ 14 条语义分点（observations/data_gaps/recommended_review 合并去重）。
- 修复补丁（本轮）：overview 的 query_findings 注入从"冻结Query草稿"切回"活binding读取"（快照域限定+digest校验，V5-04当前指针语义）——冻结草稿字段（query_draft_id/risk_id/draft_state）与AI线索卡片字段（state/title/claims/subject_label）是两个DTO，此前混用导致卡片空白。截图 /tmp/w03_cards.png。

## A25 导航与零模型调用 — 通过

- AI卡片 →「进入受试者医学旅程」→ 受试者21001旅程视图：**27事件/7访视/27风险锚点**，域分布（试验用药8/检验8/方案符合性7/合并用药2/AE1/MH1），风险定位徽章「AE·中风险」渲染。
- 导航全程零模型调用：aemh作业总数前后一致（32，无新增）——浏览/筛选/跳转全部读已发布结果上下文。
- 截图 /tmp/w03_journey.png。

## A23 证据不跳首条

- 代码修复已落地并构建通过（EvidenceView matchedRef 精确匹配，未命中显示「未能精确匹配目标来源定位」）；本轮浏览器走查未触发坏locator场景（全部命中的定位显示正常），坏locator场景回归留待下轮构造用例。

## E0（A18–A22）与 A28 — 未开工/部分，如实

- E0成本账本：include_usage请求+attempt/observed分离已具备地基，逐物理调用账本未开工。
- A28：空脚手架备份已做；全量恢复演练未跑。A27：SAR未授权不动。
