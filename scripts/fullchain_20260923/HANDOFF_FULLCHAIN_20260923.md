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
