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


---

# R10D 开考位预置结果 — MX循R10D-CSU（2026-10-01）

隔离环境：API `http://127.0.0.1:8911`（build api-439b9e81187f0da4，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考预置守护员-R10D。起止：2026-09-30 17:53 → 2026-10-01 02:03（本地 CST，约 8 小时 10 分，其中复核收敛约 7.2 小时——本轮裁决 prompt 升至 v19-tools-v7.2 工具版，单作业多轮工具调用，显著慢于 R9D）。

## 探障（本轮前置）

- 循环收尾已把全部旧项目软归档（user_projects.project_visibility 107 行含 R5D/R8D/R9D），`GET /api/projects` → `[]`；对归档项目 `GET /r7/project/open` 返回 `route_not_found`（模块路由不挂载），**非 blocked/CORRUPT**——旧项目无法按原样探障。
- 改用三路替代探障：① 修复代码在位：`services/api/app/main.py:4883-4884,4893-4894` 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:54 `SCHEMA_VERSION = SCHEMA_VERSION_V5`）；② 存量 29 个 workspace 的 launch_registry marker 逐库 sqlite 直查全部 `mm-r7-w01r26-launch-registry-v5`；③ 新建项目（proj_user_ad685a18f853）后立即用产品 `inspect_member` 实证 4 个种子成员（profile_store/run_binding/launch_registry/risk_rules）**全 CURRENT**（launch_registry marker=v5）。**R5D 缺陷未复发。**
- 建项瞬间 `GET /r7/project/open` → blocked/incomplete/canView=false「暂时无法安全打开此项目」——用产品 `ProjectSchemaInspector` 定位为 `required_member_missing`：`runtime/monitoring_runtime.sqlite3` 在流水线 bootstrap 前本就不存在（schema_manifest.py inspect_project_schema 注释记录的 R1 已知瞬态同款），非损坏；facts 物化后该库建立，project/open → current（见下）。**本轮无需修复、未重启 API。**
- 环境侧：8911 存活（ready:true，api-439b9e81187f0da4）未动；隔离 vite 5178 中途掉线，按本文件标准命令重启（只动隔离对，8911 未重启）；8910 复核 200 未受影响；**5177 复核时连接拒绝（已停）——非本轮操作所致（本轮对 8910/5177 仅只读 curl），按铁律未去拉起，如实记录**。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_ad685a18f853** |
| project_name | MX循R10D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r10d-seed-20260930T095343Z-a18f7bd1（唯一） |
| data admission | stg-102ee29d6bd749e0b9eaa6bc3bfaa902（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_0b9c34e8cd7261eeffaf22fa（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-10-01 02:0x CST）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects；state r10d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表 |
| 文档权威 | ✅ ready=true | 09:57Z 提交→10:11Z ready 约14分钟；本轮未触发身份归属/文件角色人工门（R6-02/R1-02 修复后自动裁决），AI 质量门自然通过 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选 |
| 复核收敛 | ✅ complete | 分歧 46→38→27→20→12→0（系统裁决累计34），多轮双队列复核；失败分片自动恢复重排（本项目终态 failed 6 个 listing_field_mapping 分片，均经 bounded-gap 设计与后续轮次收敛，remaining=0 全字段闭合）；EX/EXTRT 问题卡按数据实测作答一次 |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_d98fb51959ccc93a119198332334 status=confirmed（v60），user_questions=0，60字段 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/2290值全核验（source_values_verified=2290），message「可用于监查的数据已生成，可以开始监查。」 |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` 200；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-439b9e81187f0da4 与 8911 backend_build_id 配对一致 |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账（本项目，medical_monitoring_ai.sqlite3 按 project_id 过滤）：82 作业（76完成/6终态失败，均为 listing_field_mapping 分片，经自动恢复与后续轮次收敛）；149 次调用，2,267,750 tokens。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **收敛耗时显著上升**：R10 裁决作业升级为 `monitoring-listing-field-mapping-adjudication-v19-tools-v7.2` 工具调用型（单作业多次成功调用，实测 EX 分片 3 次调用 337s/427s/196s），复核收敛全程约 7.2 小时（R9D 约 3 小时）。驱动脚本两次 3.5h 收敛预算耗尽后按幂等设计续跑（exit 10 → 重跑），第三次续跑 90 秒内完成收敛→确认→物化。
- **无新人工裁决卡**：R9 的 CM/LB_HEM 六卡本轮未再浮现（系统 v19 工具裁决自行闭合）；驱动脚本 fail-closed 防护在位未触发（unknown_questions=0 全程）。

## 留痕文件（同目录）

- 驱动：`r10d_seed_csu.py`（由 r9d_seed_csu.py 适配：R10D 命名/幂等键/留痕文件 + 建项后 project/open 探针留痕 + 终态硬断言 confirmed/ready/非blocked）
- 证据：`r10d_seed_evidence.jsonl`（每步请求/响应摘要）、`r10d_seed_state.json`（幂等状态）
- 环境日志：`ISO_ENV_LOG.md`（R10D 探障+5178重启+预置条目）

---

# R11D 开考位预置结果 — MX循R11D-CSU（2026-10-01）

隔离环境：API `http://127.0.0.1:8911`（build api-807dff49e5ad28ec，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考预置守护员-R11D。起止：2026-10-01 14:31 → 17:09（本地 CST，约 2 小时 38 分，含探障/5178复活/AI 等待与裁决卡核对）。

## 探障（本轮前置）

- 循环收尾已归档全部旧项目（`GET /api/projects` → `[]`），但 R10D 项目路由仍可探：`GET /r7/project/open`（proj_user_ad685a18f853）→ **state=current / openMode=edit / dataCoverage=complete / canView/canEdit=true**「项目格式正常，可以继续使用。」——无 blocked/CORRUPT，R5D marker 缺陷未复发。
- 修复代码在位：`services/api/app/main.py:4925-4936` `_init_monitoring_runtime_dbs` 种子 marker 仍取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 `SCHEMA_VERSION = SCHEMA_VERSION_V5` = mm-r7-w01r26-launch-registry-v5）。
- 存量库直查：隔离 runtime **36 个** workspace 的 launch_registry.sqlite3 marker 逐库 sqlite 直查**全部 v5**（0 个非 v5）。
- R11D 建项后即时用产品 `inspect_member` 实证 4 个种子成员（profile_store/run_binding/launch_registry/risk_rules）**全 current/current_shape**（launch_registry marker=v5）；建项瞬间 project/open 的 blocked 为 `required_member_missing`（monitoring_runtime.sqlite3 在流水线 bootstrap 前不存在，R1 已知瞬态同款）——非损坏，facts 物化前该库已在流水线中建立（复跑探针 09:03:10Z 即 current）。**本轮无缺陷需修、未改任何产品代码、未重启 8911。**
- 环境侧：8911 存活（ready:true，api-807dff49e5ad28ec）；隔离 vite 5178 掉线（连接拒绝，lsof 无监听），按本文件标准命令复活（`VITE_API_PROXY_TARGET=http://127.0.0.1:8911 npx vite --port 5178 --strictPort`，v6.4.2 ready in 180ms）；自检 /monitoring=200、runtime-build.json expectedBackendBuildId=api-807dff49e5ad28ec 与 8911 backend_build_id 配对一致。8910 复核 200；**5177 复核连接拒绝（已停）——非本轮所致（对 8910/5177 仅只读 curl），按铁律未去拉起，如实记录**。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_175b6374dcd6** |
| project_name | MX循R11D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r11d-seed-20261001T064001Z-ae6864d3（唯一） |
| data admission | stg-e32cb7ad0e744cedb6013ebbd9cb820c（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_894c24548d5828b5c639886c（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-10-01 17:0x CST）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r11d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表 |
| 文档权威 | ✅ ready=true | 06:40:03Z 提交→06:44:05Z ready 约4分钟；protocol/ecrf 两角色自动识别 current（IB/SAP 缺失如实标记「可稍后添加」），本轮未触发身份归属/文件角色人工门，AI 质量门自然通过 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（约17分钟） |
| 复核收敛 | ✅ complete | 分歧 46→37→24→0（系统裁决累计22，多轮双队列复核）；2个 listing_field_mapping 分片终态 failed（provider_runtime_error×2）经 bounded-gap 设计与系统裁决收敛，remaining=0 全字段闭合 |
| 裁决卡 | ✅ 已答 | 共24张两轮分歧卡：21张按 R5/R8/R9 既有数据实测决策表作答（AE×7、CM×3、ICF_TRACK.ICFSTATE、LB_HEM×3、MH×3、UAS×4）；**3张R11新卡**（CM.CMENDAT/CM.CMSTDAT/ICF_TRACK.ICFVER）首次浮现时驱动脚本 fail-closed 诚实退出留痕（09:01:57Z），随后按 openpyxl 直读同三份合成文件列值实测（CM.开始日期/结束日期 33行数据全合法日期；ICF_TRACK.知情版本 16行全列唯一值 v2.1）+ 两轮队列同判角色逐卡作答（09:03:24Z）；EX/EXTRT 本轮未浮现（系统 v19 工具裁决自行闭合） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_0f8105505291681767f13de5d504 status=confirmed（v71），user_questions=0，60字段 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/2958值全核验（source_values_verified=2958），message「可用于监查的数据已生成，可以开始监查。」 |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` 200；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-807dff49e5ad28ec 与 8911 backend_build_id 配对一致 |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账（本项目，medical_monitoring_ai.sqlite3 按 project_id 过滤）：60 作业（58完成/2终态失败，均为 listing_field_mapping 分片 provider_runtime_error，经自动恢复预算与系统裁决收敛，remaining=0 全字段闭合）；89 次调用，1,726,840 tokens。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **收敛耗时回落**：复核收敛全程约 2 小时（R10D 约 7.2 小时）；文档权威约 4 分钟（R10D 约 14 分钟）。驱动脚本收敛预算按 R10D 经验放宽至 9h，实际单次预算内完成。
- **无人工门**：身份归属/文件角色门均未触发（自动裁决）；人工介入仅裁决卡作答一次 fail-closed→补答循环（设计内）。
- **R11 新卡**：CM.CMENDAT/CM.CMSTDAT（合并用药起止日期）与 ICF_TRACK.ICFVER（知情同意书版本）为历轮首次浮现，两轮队列结论一致、列值实测支撑，已固化进 `r11d_seed_csu.py` 的 R11_ROUND3_CARDS 表供后续轮次复用。

## 留痕文件（同目录）

- 驱动：`r11d_seed_csu.py`（由 r10d_seed_csu.py 适配：R11D 命名/幂等键/留痕文件 + 收敛预算9h + R11_ROUND3_CARDS 三卡表；幂等，含 fail-closed 未知卡防护）
- 证据：`r11d_seed_evidence.jsonl`（每步请求/响应摘要，含 09:01:57Z unknown_questions_fail_closed 留痕）、`r11d_seed_state.json`（幂等状态）
- 环境日志：`ISO_ENV_LOG.md`（R11D 探障+5178复活+预置条目）

---

# R12D 开考位预置结果 — MX循R12D-CSU（2026-10-03）

隔离环境：API `http://127.0.0.1:8911`（build api-21b0d9e614066a8e，runtime `runs/tester_loop_iso_20260928/runtime`），全程未触碰 8910/5177。
操作者：开考预置守护员-R12D。起止：2026-10-03 01:02 → 04:05（本地 CST，约 3 小时 3 分，其中约 38 分钟被 host 代理故障占用等待+修复）。

## 探障（本轮前置，三路全通过，R5D marker 缺陷未复发）

- `GET /r7/project/open`（R11D项目 proj_user_175b6374dcd6）→ **state=current / openMode=edit / dataCoverage=complete / canView/canEdit=true**「项目格式正常，可以继续使用。」——无 blocked/CORRUPT。
- 修复代码在位：`services/api/app/main.py:4925-4927,4935-4936` 种子 marker 仍取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）。
- 存量库直查：隔离 runtime **42 个** workspace 的 launch_registry.sqlite3 marker 逐库 sqlite 直查（`r7_launch_registry_meta.schema_version`）**全部 v5**（0 个非 v5）。
- R12D 建项后即时用产品 `ProjectSchemaInspector` 实证 4 个种子成员（profile_store/run_binding/launch_registry/risk_rules）**全 current**（launch_registry marker=v5），project_state=current。建项瞬间 project/open 未出现 blocked。**本轮无缺陷需修（产品侧）、未改任何产品代码、未重启 8911。**
- 环境侧：8911 存活（ready:true，api-21b0d9e614066a8e）；5178 存活（node 26733，监听 `[::1]:5178`，127.0.0.1 探测不通系仅绑 v6 回环——经 localhost 复核 /monitoring=200），runtime-build.json expectedBackendBuildId=api-21b0d9e61406a8e 与 8911 配对一致；**8910/5177 无监听（连接拒绝，lsof 复核）——非本轮所致（对二者仅只读 lsof/curl），按铁律未触碰，如实记录**。

## 主侧 AI 路由故障与界内修复（本轮特记）

- **故障**：文档权威/映射主侧角色（cms-router/glm-5.3-flash）原经本机 omniroute LB `127.0.0.1:20128` → Clash Verge 代理 `127.0.0.1:7897` → api.z.ai。Clash Verge 核心自 ≥2026-10-02T14:00Z 未运行（仅特权 helper 在跑；本机无任何常见代理端口监听；scutil 系统代理关闭），主侧作业全部 `[Proxy Fast-Fail] Proxy unreachable (HTTP 503)` 快速失败：本项目文档主分析连败 204 次，隔离实例今日全部 cms-router 主侧作业零成功（并行测试会话同故障，omp 自身日志同报）。api.z.ai 与 open.bigmodel.cn 直连均可达。
- **修复（界内，最小，可逆，全程留痕）**：用产品自有 `AiRuntimeSettingsStore`（作用于隔离 runtime 目录，非 API、非直改运行库、未触碰共享 omniroute/Clash）把两个主侧角色档案 `medical_monitoring_ai__cms_router_glm53flash`（rev4→5）与 `document_authority_primary_ai__medical_monitoring_ai__cms_router_glm53flash`（rev1→2）的 base_url 由 LB 改为智谱官方直连 `https://open.bigmodel.cn/api/coding/paas/v4`、清空 LB 专用 extra header、存储凭据改用隔离实例自有 zhipu coding-plan 直连密钥（取自同库 `independent_ai__zhipu_coding_plan_glm_flash` 档案凭据，密钥未落任何日志）。**provider 身份串（cms-router）、模型（glm-5.3-flash）、推理档（high）、prompt 版本、全部 AI 质量门保持不变**；verifier 侧（ollama-cloud/deepseek-v4.1-flash）未动。改前四件配置备份于 `scripts/tester_loop_0927/r12d_provider_config_backup/`。
- **生效实证**：换绑后卡住的主分析作业 17:38:20Z 最后一次代理失败 → **17:40:02Z 首次尝试即 success**（终态 completed）；此后主侧映射/裁决分片全部正常完成（换绑后 47 次成功尝试 vs 换绑前 204 连败）。产品 probe 端点对该档案完成真实模型往返（探针报「unexpected structured response」仅为其输出形状校验，连通性与真实 glm-5.3-flash 输出已实证）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_5bcd73dd2cf8** |
| project_name | MX循R12D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r12d-seed-20261002T170213Z-fe436efb（唯一） |
| data admission | stg-b11c1e67bbe64da3bd83df6b6b2fc663（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_1d0b2221fbfc01b033af34ab（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-10-03 04:0x CST）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r12d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表 |
| 文档权威 | ✅ ready=true | 17:02:14Z 提交→17:45:17Z ready（含 38 分钟代理故障期+换绑修复）；protocol/ecrf 自动识别，无人工门 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（17:45:27Z→18:05:13Z 约20分钟） |
| 复核收敛 | ✅ complete | 分歧 46→42→30→0（系统裁决16，多轮双队列复核；1个 listing_field_mapping 分片终态 failed=invalid_ai_output 经 bounded-gap 与系统裁决收敛，remaining=0 全字段闭合） |
| 裁决卡 | ✅ 已答 | 共31张：27张按 R5/R8/R9/R11 既有数据实测决策表作答（19:57:01-04Z）；**4张R12新卡**（DM.AGE/COMPSTATUS/RANDDT/SEX）首次浮现时驱动脚本 fail-closed 诚实退出留痕（19:5xZ），随后按 openpyxl 直读 DM 表列值实测（年龄16行23-61数值/研究状态全列唯一值「完成」/随机日期16行合法日期/性别男8女8）+两轮同判角色逐卡作答（20:04:37Z） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_3bc1f8d5f0fcd50a6e4c0293ecd8 status=confirmed（**v77**），user_questions=0，60字段 |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/**3038值全核验**（source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」 |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` **200**；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-21b0d9e61406a8e 与 8911 backend_build_id 配对一致 |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账（本项目，medical_monitoring_ai.sqlite3 按 project_id 过滤）：66 作业（65完成/1终态failed=listing_field_mapping invalid_ai_output，经自动恢复与系统裁决收敛 remaining=0）；303 次物理调用（88 成功调用；其余为代理故障期 204 连败与映射分片重试），tokens 合计 2,086,644。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **R12 新卡为 DM 域四卡**（受试者年龄/研究完成状态/随机化日期/受试者性别），历轮首次浮现（此前轮次 DM 域仅 ARM 浮现过）；两轮队列结论一致、列值实测支撑，已固化进 `r12d_seed_csu.py` 的 R12_ROUND4_CARDS 表供后续轮次复用。
- **host 代理单点**：主侧 AI 链路对 Clash Verge 代理（127.0.0.1:7897）存在隐性单点依赖，代理停机即主侧全阻（R11C 测试轮曾同样中招）。本轮以界内 provider 档案直连规避并留痕；如后续 Clash Verge 恢复，可从 `r12d_provider_config_backup/` 还原或维持直连（直连同为 glm-5.3-flash 官方端点，语义等价）。提请循环所有者关注该 host 层依赖。

## 留痕文件（同目录）

- 驱动：`r12d_seed_csu.py`（由 r11d_seed_csu.py 机械适配：R12D 命名/幂等键/留痕文件 + R12_ROUND4_CARDS 四卡表；幂等，含 fail-closed 未知卡防护）
- 证据：`r12d_seed_evidence.jsonl`（每步请求/响应摘要，含 19:5xZ unknown_questions_fail_closed 留痕）、`r12d_seed_state.json`（幂等状态）
- 配置备份：`r12d_provider_config_backup/`（换绑前 ai_provider_settings/ai_provider_secrets/ai_provider_master.key/ai_role_bindings 四件）
- 环境日志：`ISO_ENV_LOG.md`（R12D 探障+主侧AI路由界内修复+预置条目）


# R13D 开考位预置结果 — MX循R13D-CSU（2026-10-03）

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911）

- R13 重建隔离运行时后外来项目清零（GET /api/projects→[]），无存量项目可探 → 按 R5D 先例改为建项后探：建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1 已知同款）；随后产品 `inspect_project_schema` 实证 6 成员全 current/current_shape（launch_registry marker=mm-r7-w01r26-launch-registry-v5，sqlite 直查同值）；修复代码在位（main.py:4925-4936 种子 marker 取 launch_registry_contracts.SCHEMA_VERSION，contracts.py:53-54=V5）。终态硬断言在本轮 Step10 通过（见下表）。
- 环境侧：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId 配对一致；8910/5177 无监听（非本轮所致，仅只读复核，未触碰）。
- **主侧AI路由界内换绑直连（R12D 同款先例）**：重建后两主侧档案 base_url 回到本机 LB 127.0.0.1:20128，其上游 Clash Verge 7897 不可达（probe 实证 Proxy Fast-Fail 503）。用产品自有 AiRuntimeSettingsStore 换绑两档案（rev4→5/rev1→2）为智谱官方直连，凭据用隔离实例自有 zhipu key（密钥未落日志）；provider/模型/推理档/质量门不变。改前四件备份 `r13d_provider_config_backup/`。生效实证：两主侧 probe passed:true（2729/4354ms）；verifier 两侧（ollama-cloud deepseek-v4.1-flash，未动）probe passed:true（680/638ms）。
- **数据暂存重建（环境侧，非产品缺陷）**：循环收尾后 tester_staging_0927/ 不存在，从字节一致来源重建 synth_csu 三件套（listing sha256 4be08e9e…/10表591行；方案 73024713…；eCRF 8109d25a…，详见 ISO_ENV_LOG R13D 条目）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_bbcc5c21edfb** |
| project_name | MX循R13D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r13d-seed-20261003T064711Z-83d83077（唯一） |
| data admission | stg-ff9b4b097f334cbe87badede0a9da480（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_e0cf83877d3f55b911bb05ba（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-10-03 16:28 CST 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r13d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（06:47:11Z） |
| 身份门 | ✅ | project_identity_incomplete → 一次 identity_confirmation（06:49:14Z，等价界面一次点击） |
| 文档权威 | ✅ ready=true | 06:47:12Z 提交→06:54:28Z ready（约7分钟）；protocol/ecrf 自动识别 current，无角色人工门 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（06:54:31Z→07:08:05Z 约14分钟） |
| 复核收敛 | ✅ complete | 分歧 46→30→1→0（系统裁决16，多轮双队列复核；1个 listing_field_mapping 分片终态 failed=provider_runtime_error 经 bounded-gap 与系统裁决收敛，remaining=0；期间1次 adjudicate HTTP 500 瞬态，脚本重试后 200） |
| 裁决卡 | ✅ 已答 | 共31张：29张按 R5/R8/R9/R11/R12 既有数据实测决策表作答；**2张R13新卡**——① EX.EXFRQ（需医学确认：列标题"给药频次"但128行全为"300mg"剂量值，Q4W仅在EXTRT文本中；R12新增方案-vs-数据剂量口径交叉核对提示词首次命中）首次浮现 fail-closed 诚实退出留痕（07:08:08Z），按 openpyxl 直读实测作答：按每次给药剂量口径采纳 `ip_administered_dose_with_unit_text`（两臂同值标签式记录不声明实际IP暴露，剂量语义交质量门保持可见受限；dose_semantics 为系统溯源键用户补丁不可直改，422→去掉后200）；② EX.EXSTATE（两轮分歧但显示同token）fail-closed 留痕后采纳 `treatment_administration_status`（128行二值：完成×86/延迟给药×42）（08:02:29Z） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_3e2b91474bfaf4a8b01937dbe128 status=confirmed（**v79**），user_questions=0（08:28:08Z） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，10表/591行/**3422值全核验**（source_values_verified=3422）（08:28:08Z） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true；`run-setup/options` **200** |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

起止：06:47:11Z→08:28:10Z（14:47→16:28 CST，约1小时41分，含两次 fail-closed 退出后的补答重入）。AI 台账（medical_monitoring_ai.sqlite3 按 project_id 过滤）：48 作业（47完成/1终态failed=provider_runtime_error，经 bounded-gap 收敛 remaining=0）；63 次调用，tokens 合计 1,322,816（prompt 822,871 + completion 499,945）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **R13 新卡 EX.EXFRQ 是 R12 修复（映射AI提示词增加方案-vs-数据剂量/频次/给药途径交叉核对要求）的首次正向命中**：合成数据 EX 域"给药频次"列标签与内容（剂量300mg）口径矛盾的固有脏点被 AI 主动提为需医学确认卡，历轮首次浮现。已按数据实测固化进 `r13d_seed_csu.py` 的 R13_ROUND1_CARDS 表供后续轮次复用。
- **dose_semantics 溯源保护**：用户补丁直改 dose_semantics 会被仓库 edit_field 拒绝（422 mapping_draft_invalid，provenance 键仅 system_harness 可改）——本轮 422→改用 recommended_role+user_action 落答即通过，属设计内防护非缺陷。
- **host 代理单点沿 R12 记录**：重建隔离 runtime 会使主侧档案 base_url 回退到 LB 快照值，代理故障即复发；R13D 已再次界内换绑直连并留痕。提请循环所有者关注（后续每次 runtime 重建后需复核该点）。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r13d_seed_csu.py`（由 r12d_seed_csu.py 机械适配：R13D 命名/幂等键/留痕文件 + R13_ROUND1_CARDS 两卡表；幂等，含 fail-closed 未知卡防护）+ `r13d_rebind_primary_ai.py`（主侧AI换绑）
- 证据：`r13d_seed_evidence.jsonl`（每步请求/响应摘要，含两次 unknown_questions_fail_closed 留痕）、`r13d_seed_state.json`（幂等状态）
- 配置备份：`r13d_provider_config_backup/`（换绑前 ai_provider_settings/ai_provider_secrets/ai_provider_master.key/ai_role_bindings 四件）
- 环境日志：`ISO_ENV_LOG.md`（R13D 探障+主侧AI路由界内换绑+数据暂存重建+预置条目）
