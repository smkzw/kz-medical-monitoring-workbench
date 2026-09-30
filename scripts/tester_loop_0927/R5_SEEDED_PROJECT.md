# R5D 开考位预置结果 — MX循R5D-CSU（2026-09-29）

隔离环境：API `http://127.0.0.1:8911`（build api-39dd6f40246a95ce，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考门槛预置员（R5D）。起止：2026-09-29 12:50 → 17:37（本地 CST，约 4 小时 47 分，含轮询等待）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_9ce08d6a722d** |
| project_name | MX循R5D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r5d-seed-20260929T045029Z-444e1a1a（唯一） |
| data admission | stg-68d7a08f01b3472196931402184b53c4（合成listing 591行/10表，同步解析） |
| 文档权威批次 | mmbatch_b941ebb0895ff818a59fae94（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-09-29 17:4x）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects；state r5d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行 |
| 文档权威 | ✅ ready=true | 6个AI作业完成；文件角色人工裁决（ecrf→eCRF指南docx；IB/SAP缺失如实标记）+身份归属确认一次 |
| 映射双队列 | ✅ candidates_ready | 第一轮10主+10盲核全完成，60字段候选 |
| 医学问题卡 | ✅ 已答 | EX/EXTRT（依据数据实测：两臂128行同值，治疗身份以DM.试验分组为准）+ 最终8张两轮分歧裁决卡，全部决策前缀留痕 |
| 复核收敛 | ✅ complete | 分歧 46→32→27→23→8→0，4轮第二轮双队列；失败分片自动恢复+bounded-gap |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft status=confirmed（v57），user_questions=0 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/2400值全核验，message「可用于监查的数据已生成，可以开始监查。」 |
| 界面可开始运行监查 | ⚠️ **被缺陷阻断** | `GET /r7/project/open` → blocked/dataCoverage=incomplete；`GET /r7/run-setup/options` → **409 project_open_blocked**（见下） |

AI 台账：92 作业（87完成/5失败：provider_reasoning_only×4、invalid_ai_output×1，均按设计自动恢复预算与 bounded-gap 收敛）；183 次调用，2,653,827 tokens。

## 阻断缺陷（新发现，如实上报，未绕过）

**建项种子写入过期 launch_registry schema marker → 全部 API 建项的监查项目被判 CORRUPT → 运行监查入口全挡。**

- 界面/接口现象：项目打开被拒（"暂时无法安全打开此项目，请保留原项目并联系支持"，canView=false）；`/r7/run-setup/options` 409 project_open_blocked；运行入口（runs/prepare-and-start 等）经同一 mutable gate（packages/medical_monitoring/api/r7_product/project_operations.py:786-805）。
- 根因：`services/api/app/main.py:4850`（`_init_monitoring_runtime_dbs`）以 manifest 现行 **v5 DDL** 创建 `launch_registry.sqlite3`，却写 marker **mm-r7-slice08b-launch-registry-v4**（`main.py:4849-4851`）。schema 检验按 marker 匹配 v4 形状 → shape_mismatch → CORRUPT。
- 实证：隔离 runtime **全部 14 个** workspace 的 launch_registry 同样 shape_mismatch（含并行会话 MX循R5-CSU-c2ae 等）；用当前 `LaunchRegistry` 代码新建文件出生即 v5 且检验 CURRENT（packages/medical_monitoring/runtime/launch_registry_core_mixin.py:171 写 SCHEMA_VERSION=v5）——写入方自洽，仅建项种子 marker 过期（R24 于 0923V1 修过同类漂移，W01-R26 升 v5 后再落后一版）。
- 影响范围：本次全链（文档权威→映射→确认→facts）不受影响、已全部真实完成；仅「开始运行监查」的门面被挡。修复需后端将种子 marker 改为 v5（建议直接取 launch_registry_contracts.SCHEMA_VERSION），存量库可走 launch_registry 自身的 v4→v5 原地升级路径。本轮未改任何库、未跳任何质量门。

## 留痕文件（同目录）

- 驱动脚本：`r5d_seed_csu.py`（建项→接入→文档→映射→adopt→adjudicate→confirm→facts，幂等）、`r5d_question_cards.py`、`r5d_final_cards.py`（医学卡作答）、`r5d_converge.py`（复核收敛驱动）
- 证据：`r5d_seed_evidence.jsonl`（每步请求/响应摘要）、`r5d_seed_state.json`（幂等状态）
- 环境日志：`ISO_ENV_LOG.md`（R5D 起止与作业数条目）

---

# R8D 开考位预置结果 — MX循R8D-CSU（2026-09-30）

隔离环境：API `http://127.0.0.1:8911`（build api-700a1dd6ecebb56e，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考预置守护员-R8D。起止：2026-09-30 02:06 → 05:07（本地 CST，约 3 小时，含约 1 小时裁决卡依据核对）。

## 探障与修复（本轮前置，R5D 遗留阻断缺陷）

- 探障实测：R5D 项目 `GET /r7/project/open` → `state=blocked / dataCoverage=incomplete / canView=false`（「暂时无法安全打开此项目」）；`run-setup/options` → 409 project_open_blocked。产品 `inspect_member` 实证隔离 runtime **21/21** workspace 的 launch_registry 均 corrupt/shape_mismatch（v4 marker + v5 形状）。
- 修复①（产品代码）：`services/api/app/main.py` `_init_monitoring_runtime_dbs` 种子 marker 由硬编码 v4 改取 `launch_registry_contracts.SCHEMA_VERSION`；临时 runtime 实测新种子 inspect → current/current_shape。
- 修复②（存量库）：`r8d_repair_launch_registry.py` 按 `LaunchRegistry.open()` 同语义守卫式原地升级，21 个库 corrupt→current（证据 r8d_repair_evidence.jsonl）。
- 重启隔离对 8911/5178（只动隔离对）：ready:true、指纹配对 api-700a1dd6ecebb56e、8910/5177 复核 200。重启后 R5D 项目 project/open → **current/complete**、run-setup/options **200**（409 消除）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_6ae946bc497a** |
| project_name | MX循R8D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r8d-seed-20260929T180648Z-80a50af6（唯一） |
| data admission | stg-dcc4681ae6b44cf49db24922eb29b6bf（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_b5dd4c1eb2e15b22b114559a（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-09-30 05:0x CST）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects；state r8d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行 |
| 文档权威 | ✅ ready=true | 8个AI作业（2分析+6复核）；ecrf→eCRF填写指南docx 按文件名裁决 + 身份归属确认一次（IB/SAP缺失如实标记） |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核全完成，60字段候选 |
| 复核收敛 | ✅ complete | 分歧 46→36→21→0，3轮双队列；失败分片自动恢复重排（R5-03修复生效） |
| 裁决卡 | ✅ 已答 | 21张两轮分歧卡逐卡作答：15张R8新卡（AE域×8、DM.ARM、LB_HEM.LBUNIT、MH.MHTERM、UAS×4）以 R5D 同数据已确认版 monmaprev_e4c1fe85a816792f0814cbec2179 的已确认角色 + 列值实测为依据；6张R5D同款卡按既有数据实测决策；首次遇未知卡时脚本 fail-closed 诚实退出留痕后再答 |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：draft status=confirmed（v68），user_questions=0，60字段 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/2834值全核验，message「可用于监查的数据已生成，可以开始监查。」 |
| **界面可开始运行监查** | ✅ | `GET /r7/project/open` → state=current/dataCoverage=complete/canView/canEdit=true「项目格式正常」；`run-setup/options` 200（含已核验事实快照与运行模式） |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账：64 作业（61完成/3终态失败：invalid_ai_output×1、provider_runtime_error×2——经自动恢复与后续轮次收敛，adjudication remaining=0 全字段闭合）；105 次调用，1,942,073 tokens。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 留痕文件（同目录）

- 驱动：`r8d_seed_csu.py`（幂等全链驱动，含 fail-closed 未知卡防护）、`r8d_repair_launch_registry.py`（存量库 v4→v5 原地升级）
- 证据：`r8d_seed_evidence.jsonl`（每步请求/响应摘要）、`r8d_seed_state.json`（幂等状态）、`r8d_repair_evidence.jsonl`（21库修复前后检验）
- 环境日志：`ISO_ENV_LOG.md`（R8D 探障修复+重启+预置条目）

---

# R9D 开考位预置结果 — MX循R9D-CSU（2026-09-30）

隔离环境：API `http://127.0.0.1:8911`（build api-ff4268b99214365a，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考预置守护员-R9D。起止：2026-09-30 11:02 → 15:00（本地 CST，约 3 小时 58 分，含 AI 等待与 12 分钟裁决卡依据核对）。

## 探障（本轮前置）

- `GET /r7/project/open`（R8D 项目 proj_user_6ae946bc497a）→ **state=current / dataCoverage=complete / canView/canEdit=true**「项目格式正常」——无 blocked/CORRUPT，R5D 遗留缺陷未复发。
- 修复在位确认：`services/api/app/main.py:4883-4884,4893-4894` `_init_monitoring_runtime_dbs` 种子 marker 仍取 `launch_registry_contracts.SCHEMA_VERSION`（R8D 修复，现行 build api-ff4268b99214365a 含之）。本轮 R9D 新建 workspace 的 launch_registry 经产品 `inspect_member` 实测 **current/current_shape（mm-r7-w01r26-launch-registry-v5）**——新种子出生即合格。
- 结论：无需修复、无需重启（本轮对 8911/5178 无任何启停操作）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_f650151b5a42** |
| project_name | MX循R9D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r9d-seed-20260930T030202Z-9b9b988e（唯一） |
| data admission | stg-0c60b04f735c441ca6330224d7892b47（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_6683c5dcf63c33745580994c（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-09-30 15:0x CST）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r9d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行 |
| 文档权威 | ✅ ready=true | 11:02→11:21 约19分钟；身份归属确认一次（project_identity_incomplete 门，等价界面一次点击） |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核（含1失败分片自动恢复重排），60字段候选 |
| 复核收敛 | ✅ complete | 分歧 46→37→33→28→12→0，5轮 adjudicate（4轮双队列复核）；失败分片（listing_field_mapping×4终态failed）经自动恢复预算与后续轮次收敛 |
| 裁决卡 | ✅ 已答 | 首轮无卡；第4轮后浮现 **6张R9新卡**（CM.CMINDC/CMNUM/CMONGO/CMTRT + LB_HEM.LBREF/LBTEST），首次遇到未知卡时脚本 fail-closed 诚实退出留痕（06:47Z），随后按 openpyxl 直读同三份合成文件列值实测 + 两轮队列同判结论逐卡作答（06:59Z） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft status=confirmed（v59），user_questions=0，60字段 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/2724值全核验（source_values_verified=2724），message「可用于监查的数据已生成，可以开始监查。」 |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → current/complete/canView/canEdit=true；`run-setup/options` 200 |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账（本项目，medical_monitoring_ai.sqlite3 按 project_id 过滤）：88 作业（84完成/4终态失败，均为 listing_field_mapping 分片，经自动恢复与后续轮次收敛，adjudication remaining=0 全字段闭合）；139 次调用，2,471,717 tokens。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **角色词汇换代**：R9 草稿词汇相对 R8D 确认版整体换代（如 `medication_name`→`cm_treatment_name`、`ae_outcome`→`adverse_event_outcome`、`treatment_arm_assignment`→`treatment_arm`）。6张新卡按当前草稿 token 作答，语义与列值实测一致；R5D/R8D 旧卡表沿用旧 token，若后续轮次旧字段再浮现卡片需按当轮词汇换算（本轮未触发，fail-closed 防护在位）。

## 留痕文件（同目录）

- 驱动：`r9d_seed_csu.py`（幂等全链驱动，由 r8d_seed_csu.py 适配 + R9_ROUND4_CARDS 六卡表）
- 证据：`r9d_seed_evidence.jsonl`（每步请求/响应摘要，含 06:47Z unknown_questions_fail_closed 留痕）、`r9d_seed_state.json`（幂等状态）
- 环境日志：`ISO_ENV_LOG.md`（R9D 探障+预置条目）

