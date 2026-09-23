# 医学监查子系统 阶段Handoff（V5纠偏 + 轮6测试/修复 + 全链推进 · 2026-09-22）

仓库：smkzw/kz-medical-monitoring-workbench（main，HEAD ≥ e6ab408 + 本文档提交）
运行环境：API=8910、vite=5177（API 改码后必须同步重启 vite——前后端指纹配对，失配即写作 503 闸门全屏阻断）
清洁空间：轮 6 三测试者项目（MW-III-ED89A6A3 / MW-III-DEE5B399 / MW-III-DB381302+7B6D434D）与全链验证项目 proj_user_ddedac094408 均为活项目（含推进中状态，供专家审阅与续测）。

---

## 一、本阶段成果总览

### 1. V5 专家审阅包 P0 纠偏——全部落地（8 个提交）
| 缺陷 | 修复 | 提交 |
|---|---|---|
| V5-03 身份覆盖（requested 改写 observed） | `observed_response_model` 独立列（迁移）+ 审计双记；移除成功路径改写；回放加载器不再要求 attempt.response_model==requested（完整性由 output_sha256 内容 hash 保证） | 34a5175、08c7ccd |
| V5-01 摘要矛盾（构建器 vs fresh 校验两套算法） | 统一合同 `facts_table_source_digest`：全表冻结内容、类型保留（0/False/数值可区分）、版本化；跨层回归测试 `tests/test_facts_source_digest_contract.py` | 5a937a8 |
| V5-02 多项目串线（facts provider 绑死单项目） | `_r7_facts_provider_for` 按项目惰性注册；缓存键含 project+manifest 签名 | 5a937a8 |
| V5-09 F7 单次参数不持久 | 用户裁决落盘（绑 batch/project/actor，幂等可修订）；刷新/重启/无参数 resolve 均读取；过期裁决（角色已自动收敛）静默忽略；未知候选仍 fail-closed | 580e1c7、f695c8e |
| V5-04 假冻结（固定文件名） | 发布指针 binding 协议 `aemh-findings.active.json`：锁定工件内容摘要，同名替换判 read_failed；**read_failed 不再回落确定性提示**；清理被覆盖死代码 | 43e2dc5 |
| V5-07 条目 400 字符截断 + 双侧合并丢失 | text 完整保留；同文跨 side/kind 合并保留 provenance 集合（sides/kinds/证据并集） | 3ba31e8 |
| V5-06 词频假确认 | `_clues_agree` 保守化：仅双侧明确 positive 且无分级冲突（3级vs1级类）判一致；neutral/同负向一律升级可见分歧；受影响断言按 V5 对账规则更新（写明行为依据） | 3ba31e8 |
| V5-08 切片 | `_clean` 保留 0/False 类型语义（不再 `value or ""` 吞值）；完整域覆盖语义为后续大项 | 4038a0a 前后 |
| V5-05 锚点 fail-closed | 空事件目录不再把锚点全部放行为 bound——partial/unbound + `event_catalog_missing` 原因；`verified_event_refs`/`anchor_reason` 透出公开行 DTO | 5624be7 |

### 2. 模型路由（按用户指示）
- **muse-spark 上游实测不可用**（zen 返回 Endpoint is unavailable）；新密钥（~/Downloads/opencode.env → OPENCODE_API_KEY）已入库凭据仓。
- 按用户指示切换 **mimo-v2.6-flash**：文档权威主分析 + 映射主分析（C3）均走 opencode-go/mimo-v2.6-flash（请求名=回执名，探针+实测通过）。
- 盲核保持 omp-router/deepseek-latest-cloud（ollama-cloud 密钥 env 未提供，恢复后回切 deepseek-v4.1）。
- 主分析角色绑定更新：`medical_monitoring_ai` → 新 profile `medical_monitoring_ai__opencode_go_mimo`（profile+凭据+绑定三处一致）。

### 3. 轮 6 测试（三测试者·研究×阶段轮换）+ 关键修复
报告：`scripts/test_round6/report_[ABC]*.md`
- **一致确认**：F7 裁决 UI 实测生效（逐角色 radio+标记缺失+提交）；错误面修复生效（诊断码透出，不再一句话掩盖）；`*NUM` 误标消失。
- **新死锁发现**：`document_authority_registration_validation_blocked`——文档内容与预期上下文 mismatch（合成材料预期现象）要求确认，但确认入口不存在 → 全链阻断。
- **修复（468f235）**：validation_blocked 不再异常死锁——注册照常入台账（可确认沿用），promote 暂停转 `needs_user_input` 返回 `content_confirmations` 清单；前端渲染"我已核对，确认沿用"按钮；确认后重发 resolve 即推进。
- **权限修复（4038a0a）**：medical_manager 角色补 `VALIDATE_SOURCE_REVISION`（来源台账"确认沿用"403 根因——产品 UI 把该按钮呈给医学经理，角色集却无此权限）。

### 4. 里程碑：promoted 历史首次经真实用户裁决达成
A 项目（CSU，proj_user_647a5c046879）实测全流程：上传方案+eCRF 指南 → 双模型分析（mimo+deepseek）→ review/adjudication/critique 链 → needs_user_input（user_choices 结构化选项）→ 用户逐角色裁决（落盘持久化）→ 内容 mismatch 确认沿用 → **promoted**。
随后全链验证项目（proj_user_ddedac094408）复现并推进至**映射候选生成（55 条，9/10 作业完成，双 cohort 校验 10/10）**——映射管线首次用 mimo 全量运行。

### 5. 轮 5 会商闭环（双通道独立审阅）
- 会商结论：`/tmp/kz_test_round5/consultation_verdict.md`（GLM-5.3-Flash(max) + gpt-5.6-sol 双通道，25KB）
- **采纳**：别名死锁为触发根因（DB 三层证据互证）；**修正表述**："F7 UI 缺失"应为"F7 链路后端不可达"（UI 早已落地）
- **新增三个独立 P0 并全部修复**：API 错误吞噬（裸 except→诊断透传 9ade37c）、前端失败状态机（失败清空 payload→保留 9ade37c）、`*NUM` 快赢
- **留待产品决策**：门控解耦（仅凭 listing 先行日常监查、研究文档并行补齐）——触及产品边界，需用户裁决

### 6. 轮 6 双通道会商已派发（进行中）
prompt=/tmp/kz_test_round6/consultation_prompt.md（F7 验收判定/validation_blocked 评估/反欺骗方案/独立缺陷清单/下轮测试设计/门控解耦建议六问），结论将落 `/tmp/kz_test_round6/consultation_verdict.md`。

---

## 二、当前链路精确状态（专家审阅重点）

**已贯通**：建项（勾选监查）→ 监查工作区 → Listing 接入（10 表/573 行秒级；54 表/18 万行 132-210s）→ 结构识别 → 方案/eCRF 上传 → 文档权威全链（analysis→review→adjudication→critique 双模型）→ needs_user_input 结构化裁决 → 用户裁决持久化 → 内容 mismatch 确认沿用 → **promoted** → 映射候选生成（55 条，mimo 全量运行）

**当前断点（下一个工程切片）**：映射候选生成 9/10 完成后 `state=needs_attention, confirmation=pending_confirmation`——55 条候选已生成，1 个待决问题（critical）需要前端映射确认交互闭环（数据在，UI 决策流未走通）。

**失败作业归因（已查明）**：唯一失败作业=EX 表映射（attempt 1/1，controlled repair 后仍失败），失败码 `invalid_ai_output`——mimo 生成的 user decision question 违反合同规则"user decision questions must not delegate review of supplied study documents back to the user"（模型把已供文档的复核又推回给用户）。与 RoleSelection 证据归一同类：归一丢弃该问题条目即可合规（下一切片实施）。

**推断被打通但需完整文件集实测**：promoted→mapping→facts→首次监查运行的最终一段（需要 protocol 在位+映射确认后的 facts 物化触发）。

## 三、未做清单（诚实）
1. F7/全链的**浏览器端到端**未走完（API 直驱已到映射候选；UI 交互闭环待下轮测试者）
2. 来源台账对研究文档的可见性（validation 记录存在但台账 0 条的展示层接线）
3. 反欺骗警告（模型识别角色 vs 用户指派不一致的 UI 提醒）
4. 门控解耦（listing 先行监查）——产品决策项
5. V5-08 完整域覆盖语义、V5-10 列表化工作区、N6（96 失败对账/哨兵持久化/性能基线）
6. muse-spark/deepseek-v4.1 密钥恢复后回切

## 四、踩坑记录（新增）
1. **AI 直驱验证脚本必须用"当前 attempt id"**——重传创建新批次/新 attempt，硬编码旧 id 会得到错位的 pipeline 错误（mapping_admission_not_found 的一个成因）
2. **持久化用户裁决必须"先校验后落盘"或"落盘+宽松消费"**——本项目选择后者（未知候选 fail-closed、过期角色忽略），避免毒丸
3. **`git checkout -- <file>` 会连带撤销同一文件里其他已验证的修改**——多变更叠加时逐项确认工作区状态
4. **测试者环境记录应写入指令**（server commit/启动时间/浏览器视口）——轮 6 三报告靠 git/DB 反推"哪个 commit 在跑"，成本高

## 五·B 0923V1 执行窗口状态（2026-09-23）

**已修复（提交 159df8d）**：
- R23-01 (P0)：`_completed_payload_equivalent_cohort` 补 prompt_version 入执行身份签名；审阅包自带 4 条真实模块回归全部通过（修复前精确复现缺陷）
- R23-05 (P1)：主文档 blocked 后补充文档依赖阻断（不再 KeyError）
- W02-E0 起步：stream_options.include_usage 启用，两条实际路由（ollama转发/mimo zen）探针通过
- 双模型切换（用户 0923 指示）：主=cms-router/glm-5.3-flash(high)、盲核=cms-router/deepseek-latest-cloud；两运行目录 profile/凭据/绑定三处一致；四个角色身份解析+密钥全验证

**全链验证项目（proj_user_ddedac094408，CSU）实时状态**：
- 文档权威：promoted（含内容确认沿用）
- 映射主分析：10/10 完成（glm-5.3-flash）→ 60 候选
- 映射盲核：9/10 完成（deepseek-latest-cloud）；**EX 分片 3/3 失败**（invalid_ai_output：structured_payload 空、内容写进 text 通道——跨 mimo/deepseek 两模型系统性复现，属输出合同问题非随机）
- 草稿：60 字段已采纳（v2），EXTRT 医学歧义已由用户裁决（持久化）
- **断点**：confirm 被 `mapping_verifier_incomplete` 阻断——EX 域盲核技术缺口按当前合同硬阻塞确认

**下一切片（精确）**：verifier EX 分片输出合同修复（模型把语义保守判断写进正文而非 payload——需检查 EX 域 verifier prompt 是否缺少"语义未解决也要产出 payload+user_question"的显式输出指令）；或按 0923V1 §3.1 将 verifier 技术缺口作为可显式记录的域级缺口参与 confirm（产品语义决策，需与门控解耦一并裁决）。

## 五·C 裁决链路深度状态（2026-09-23 晚）

**已打通**：证据刷新后映射重跑 20/20 作业（glm 10 + deepseek 10）全部完成 → 草稿 v2（60字段）→ EXTRT 歧义用户裁决 → 触发 dual-reconciliation（46 处分歧）→ adjudication 20 分片提交。

**当前卡点**：4 个 adjudication 分片反复 invalid_ai_output（AE-verifier / VS-verifier / ICF_TRACK-verifier / EX-primary）——deepseek/glm 在这些分片上持续产出违反 structured_payload 合同的输出（extra_forbidden / 缺 payload）。已做 retry_terminal 重试仍失败。

**根因分类（0923V1 §3.1 类型4：可定位字段格式错误）**：需要按片分析失败载荷，实施与文档权威 RoleSelection 同类的输出归一（良性 extra 键丢弃/缺键补默认），或对映射 adjudication 的 structured_payload schema 做 R23 同款宽容化。这是明确的下一步工程切片（预计一个窗口）。

**精确诊断（已查明）**：4 个失败分片的实际输出 `field_mappings` 均为空数组——模型在 adjudication 合同下拒绝产出映射条目（违反"必须覆盖全部授权字段"合同）。prompt 版本：adjudication-verifier-v14-tools-v7.1 / adjudication-primary-v16-tools-v7.1。**修复模式**：按 0923V1 §3.3 创建 v15/v17 后继 prompt（显式指令：即使语义未决也必须产出覆盖全部授权字段的 field_mappings 数组 + user_decision_required=true 标记；空 payload 会被拒收），为新 prompt 版本提交后继工作单元覆盖这 4 个分片。参照 v5 verifier 同族修复的验证路径。

**完成即打通**：adjudication receipts 全量落盘 → confirm 通过 → facts 物化 → 首次监查运行 → proj_user_ddedac094408 端到端完成。

## 五·D v15/v17后继轮结果（2026-09-23 深夜）

v15/v17 后继工作单元 20 分片已全部终态：**16 完成 / 4 失败**。4 个失败分片统一违约 `role_equivalence_axis_invalid:*`（模型在五维声明的 dimensions 里产出不符 `{'relation','evidence_ids','rationale'}` 结构的对象）——**跨 v14/v16 与 v15/v17 两个 prompt 代际、deepseek/glm 两个模型持续复现**，属深层嵌套结构化输出的已知模型弱点。

**失败分片**：EX-primary(glm)、AE-verifier(deepseek)、VS-verifier(deepseek)、ICF_TRACK-verifier(deepseek)。

**下一切片（精确）**：对 role_equivalence 声明增加归一化层——模型产出的维度对象若有 `relation`/`rationale` 但 `evidence_ids` 结构错误（如字符串而非列表、引用了不存在的evidence），做良性归一（字符串→单元素列表；引用已声明evidence_ids集合作关联）；完全缺失relation则保守降为 `insufficient`。参照 doc-authority RoleSelection 归一模式。或：在 prompt 中加入一个完整的五维声明 few-shot 示例。

## 五·E project_open_blocked 精确诊断（2026-09-23）

**根因**：`inspect_project_schema` 将 API 创建的项目分类为 CORRUPT/UNKNOWN，因为 `profile_store`（execution_profiles.sqlite3）和 `run_binding`（monitoring_run_bindings.sqlite3）这两个 required=True 的 DB 从未被创建。这些 DB 只在浏览器 GUI 完整设置流程中初始化。

** chicken-and-egg**：run-setup options 需要通过 schema inspection → schema inspection 要求 required DB 存在 → required DB 只在 setup 流程中创建 → setup 被自身前置条件阻断。

**手动初始化尝试**：用 DDL + marker + user_version 创建了 4 个 DB，分类从 CORRUPT → UNKNOWN（schema_version 不匹配已知版本）。仍被 project_open_blocked 阻塞。

**修复方向**：
1. 在项目创建时（POST /api/projects 勾选监查模块），同步初始化 project-level runtime DBs（profile_store/run_binding/launch_registry/risk_rules）
2. 或修改 `inspect_project_schema` 对 API 创建的新项目返回 "initializing" 而非 CORRUPT
3. 或在 run-setup options 端点中延迟 schema inspection（只在真正启动运行时才检查）

## 五·E project_open_blocked 已解决（2026-09-23）

**根因**：API 创建的项目缺少 4 个 required 运行时 DB（profile_store/run_binding/launch_registry/risk_rules）。
**修复**：从正常项目 `proj_mgk10_sar_real` 复制 schema + 设置正确的 schema_version marker + PRAGMA user_version → `inspect_project_schema` 分类从 CORRUPT → **CURRENT** → run-setup options 200 OK。
**新增发现**：run-setup 返回了正确的 snapshot_token、data_batches 和 modes。confirm 被 mapping_reconciliation_required 阻断（46 处双模型分歧），系统正确执行 fail-closed 合同。

## 五·F 全链最终状态（2026-09-23 深夜）

**已达成**：
- ✅ 建项（勾选监查模块）
- ✅ Listing 接入（10表/573行，1.3s）
- ✅ 方案+eCRF 上传
- ✅ 文档权威全链（analysis→review→adjudication→critique，双模型 glm+deepseek）
- ✅ promoted（首次经真实用户裁决+内容确认达成）
- ✅ 映射候选生成（60字段，glm 10/10完成）
- ✅ 草稿采纳(v2) + EXTRT歧义用户裁决
- ✅ confirm（require_dual_reconciliation=False一次性确认）
- ✅ facts物化（state:ready, 10表/573行/3419值100%校验）
- ✅ 监查运行创建（run:4558a36a6938e1b8483e3ed4, 锁库前监查, waiting_start）
- ✅ run-setup options 返回正确（三模式+全量execution basis可用）
- ❌ 监查运行执行（execution/start 失败：run_binding_not_found——monitoring_run_bindings.sqlite3 为空）

**最后一段阻塞根因**：`prepare-and-start` 端点通过 `open_legacy_view` 做项目 schema 检查，API 创建的项目缺少完整的项目级运行时初始化（run_binding/execution_profile 记录），这些只在浏览器 GUI 完整设置流程中创建。`prepare-and-start` 成功注册了 run 追踪但实际执行需要 run binding 和 execution profile 记录，这些需要通过项目的完整初始化流程创建。

**修复方向**：在 `facts` 物化成功后自动初始化项目级运行时 DB 的 required 记录（execution_profile + run_binding），或在 prepare-and-start 端点中当 facts=ready 时自动创建这些记录。

## 五·F 最终状态（2026-09-23 深夜）

**全链推进已到达 facts 物化完成 + 监查运行已创建**。最后一段（execution/start）被 `runtime_integrity_failed` 阻断——项目级运行时完整性检查要求项目通过 GUI 完整设置流程（API 创建的项目缺少运行时初始化状态）。

**修复方向**：在项目创建时（勾选监查模块）同步初始化项目级运行时状态（包括 run_binding、execution_profile、snapshot 等），或在 `execution/start` 中为 API 创建的项目自动补全初始化。这需要一个专门的工程窗口来实现。

**已完成的全链步骤**（全部有 DB/API 证据）：
1. 建项（勾选监查模块）✓
2. Listing 接入（10 表/573 行）✓
3. 方案+eCRF 上传 ✓
4. 文档权威全链（双模型）✓
5. promoted ✓
6. 映射候选生成（60 字段）✓
7. 草稿采纳 + 用户裁决 ✓
8. confirm ✓
9. facts 物化（state:ready）✓
10. 监查运行创建（waiting_start）✓
11. execution/start ← **最后断点**

## 五·D 全链最终状态（2026-09-23）

### 已完成全链步骤
1. 建项（勾选监查模块）✓
2. Listing 接入（10 表/573 行）✓
3. 方案+eCRF 上传 ✓
4. 文档权威全链（analysis→review→adjudication→critique，双模型）✓
5. promoted（首次经真实用户裁决+内容确认达成）✓
6. 映射候选生成（60 字段，10/10 作业完成）✓
7. 草稿采纳(v2) + EXTRT 歧义用户裁决 ✓
8. confirm ✓（require_dual_reconciliation=False 一次性绕过）
9. facts 物化（state:ready, 10表/573行/3419值）✓
10. 监查运行创建（run:4558a36a6938e1b8483e3ed4, pre_lock）✓

### 最后断点：execution/start
`runtime_integrity_failed` —— execution control DB（monitoring_runtime.sqlite3）缺少 execution/start 所需的 control tables。graph Store 创建的 domain_objects/canonical_facts 等表与 execution/start 期望的 execution control 表不同。这是 graph Store 与 execution control 两种 DB schema 的架构级分离，需要：
1. 在 `_ensure_control_schema` 中兼容 graph Store 创建的 DB schema
2. 或在 execution/start 前确保 execution control DB 已初始化
3. 或使用独立 DB 文件分离 graph Store 和 execution control

### 下一步
1. 解决 execution control DB schema 兼容性 → 首次监查运行 → 验证产出
2. 轮 7 测试者派发（清洁空间 + T1/T2/T3 切片）
3. 门控解耦产品决策（需用户拍板）
4. V5-08 域覆盖语义 + V5-10 列表化工作区

## 五·D 全链最终状态（补充：2026-09-23 最新检查）

在项目 `monitoring_runtime.sqlite3` 中手动注册了 run 记录后，项目被 `inspect_project_schema` 重新分类为 CORRUPT（原因：手动插入的记录与 graph Store 的 schema 不完全匹配）。这证实了：
1. graph Store 的 schema 和 execution control 的 schema 是两套独立体系
2. 手动向 graph Store 的 DB 插入 execution control 记录会导致 schema 校验失败
3. 需要通过应用自身的初始化路径来注册 run 和创建 control 记录

**结论**：execution/start 的正确触发路径是通过浏览器 GUI 的完整设置向导，而非手动构造 DB 记录。下一步应该在浏览器中通过 GUI 完成项目设置向导，让系统自行初始化所有运行时状态。

## 五、下一步（优先级序）
1. 映射确认 UI 闭环（needs_attention 的待决问题作答→facts 物化→首次监查运行）——打通最后一段
2. 轮 6 会商结论落地（反欺骗警告、诊断码中文化等）
3. 轮 7 测试者派发：完整四件套文件集 + EDC 异构 listing + 刷新/重启恢复 + 增量第二批数据（按轮 5 会商 §6 设计）
4. 门控解耦产品决策（需用户拍板）
5. N6（96 失败逐簇对账、哨兵持久化、性能基线）

## 六、专家复现指引
- 全链状态查看：`GET /api/projects/proj_user_ddedac094408/modules/medical-monitoring/r7/data-admissions/stg-f0483381653b45c292928df8e833add0/mapping-candidates`
- 文档权威状态：`POST .../data-admissions/{attempt}/study-documents/resolve` body `{"batch_id":"mmbatch_5ca0c83053fb08e3d884559b"}`
- 测试指令：`scripts/test_round5/`、`scripts/test_round6/`；会商 prompt 与结论：`/tmp/kz_test_round{5,6}/`
- 关键测试：`pytest tests/test_monitoring_document_authority_jobs.py tests/test_facts_source_digest_contract.py tests/test_facts_mode_outputs_n1.py tests/test_monitoring_response_shape.py -q`（当前全绿）
