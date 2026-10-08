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


# R14D 开考位预置结果 — MX循R14D-CSU（2026-10-03）

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- R13轮次修复员已于本轮开始前重启隔离对（8911/5178 进程 12:56Z 拉起，非 runtime 重建，R13D 项目仍在）。`GET /r7/project/open`（R13D 项目 proj_user_bbcc5c21edfb）→ **state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true，无 blocked/CORRUPT** → 按本轮指令判定无需修复。修复代码在位复核：main.py:4925-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:54 = mm-r7-w01r26-launch-registry-v5）。
- R14D 建项瞬间 project/open blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1/R13D 同款）；随后产品 `inspect_project_schema` 实证 R14D 新项目成员全 current/current_shape（launch_registry marker=mm-r7-w01r26-launch-registry-v5）。终态硬断言见下表（project/open 必须 current）。
- 主侧AI路由沿 R12D/R13D 先例复核：R13D 换绑的直连配置在本轮重启后仍生效，产品 `/api/ai-gateway/probe` 四档案真实往返全 passed:true（两主侧 cms-router/glm-5.3-flash 3063/3211ms；两 verifier ollama-cloud/deepseek-v4.1-flash 681/608ms），**本轮无需换绑**。
- 环境侧：8911 /api/health ok、/api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40）；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_588084370b49** |
| project_name | MX循R14D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r14d-seed-20261003T130929Z-174dc92d（唯一） |
| data admission | stg-77d9531264f249608bb0c013e208e930（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_501bf7540ce877aff57e0a70（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |

## 全链状态（自验实测，2026-10-03 14:39-14:52Z 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r14d_seed_state.json（13:09:29Z） |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（13:09:29Z） |
| 身份门 | ✅ 未触发 | 本轮 documents_resolve 自动归属确认（analyzing→cross_checking→ready），无 project_identity_incomplete 状态，无角色人工门 |
| 文档权威 | ✅ ready=true | 13:09:30Z 提交→13:19:01Z ready（约9.5分钟）；protocol/ecrf 自动识别 current |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（13:19:05Z→13:33:45Z 约14.5分钟） |
| 复核收敛 | ✅ complete | 分歧 46→（系统裁决16）→30 remaining→0；48/48 作业全 completed（首轮1个分片短暂 failed 后重试完成，无终态 failed） |
| 裁决卡 | ✅ 已答 | 共30张：29张按 R5/R8/R9/R11/R12/R13 既有数据实测决策表作答；**1张R14新卡 EX.EXDAT**（两轮分歧：主分析 treatment_administration_date vs 独立复核 administration_date，历轮首次浮现）首次浮现 fail-closed 诚实退出留痕（14:2xZ），按 openpyxl 直读实测作答：采纳卡面推荐 `treatment_administration_date`（来源列标题'给药日期'，128行全为合法ISO日期2026-03-02~2026-07-08、16名受试者各8条Q4W给药记录，与'给药药物'/'给药状态'同行配对；受试者级治疗身份以DM.试验分组为准，不据此声明实际IP暴露）（14:39:03Z） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_df096d4513fe2f965946b6bc1530 status=confirmed（**v77**），user_questions=0（14:39:19Z，独立复验 14:4xZ 同值） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，10表/591行/**3422值全核验**（source_values_verified=3422）（14:39:19Z） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true；`run-setup/options` **200** |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

起止：13:09:29Z→14:39:23Z（21:09→22:39 CST，约1小时30分，含 EXDAT 新卡 fail-closed 退出后的补答重入一次）。AI 台账（medical_monitoring_ai.sqlite3 按 project_id 过滤）：48 作业全 completed；63 次调用，tokens 合计 1,577,719（prompt 1,055,579 + completion 522,140）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **R14 新卡 EX.EXDAT 为 EX 域给药执行语义族的历轮首次分歧卡**：主分析与独立复核对给药日期给出 treatment_administration_date/administration_date 两个 token；已按数据实测采纳卡面推荐角色并固化进 `r14d_seed_csu.py` 的 R14_ROUND1_CARDS 表供后续轮次复用。
- 本轮 documents 链未触发身份门与角色人工门（自动归属确认），与 R13D（一次 identity_confirmation）不同——属设计内条件门差异，非缺陷。
- 主侧AI直连绑定在重启后保持生效（R12D/R13D 换绑结果跨重启持久），本轮未再换绑；host 代理单点风险沿 R12D/R13D 记录，提请循环所有者后续 runtime 重建时复核。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r14d_seed_csu.py`（由 r13d_seed_csu.py 机械适配：R14D 命名/幂等键/留痕文件 + R14_ROUND1_CARDS 一卡表；R5/R8/R9/R11/R12/R13 既有裁决卡决策表原样保留；幂等，含 fail-closed 未知卡防护）
- 证据：`r14d_seed_evidence.jsonl`（每步请求/响应摘要，含 EXDAT unknown_questions_fail_closed 留痕）、`r14d_seed_state.json`（幂等状态）、`r14d_seed_console.log`/`r14d_seed_console2.log`（两段运行控制台输出）
- 环境日志：`ISO_ENV_LOG.md`（R14D 探障+预置条目）

# R15D 开考位预置结果 — MX循R15D-CSU（2026-10-03）

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- `GET /r7/project/open`（R14D 项目 proj_user_588084370b49）→ **state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true，无 blocked/CORRUPT** → 按本轮指令判定无需修复。修复代码在位复核：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）。
- 隔离 runtime 存量 10 个 workspace 的 launch_registry marker 逐库 sqlite 直查**全部 v5**（R13 重建 runtime 后的存量），无 v4/shape_mismatch。
- R15D 建项瞬间 project/open blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1/R13D/R14D 同款）；随后产品 `inspect_project_schema` 实证 R15D 新项目 6 成员全 current/current_shape（launch_registry marker=mm-r7-w01r26-launch-registry-v5）；数据接入后 project/open 即转 current/complete。终态硬断言见下表（project/open 必须 current）。
- 主侧AI路由沿 R12D/R13D 先例复核：直连配置跨重启仍生效（base_url=open.bigmodel.cn 直连），产品 `/api/ai-gateway/probe` 三档案真实往返全 passed:true（两主侧 cms-router/glm-5.3-flash 5358/3319ms；verifier ollama-cloud/deepseek-v4.1-flash 535ms），**本轮无需换绑**。
- 环境侧：8911 /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R14 轮一致，本轮无代码变更）；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_b556e56f50ba** |
| project_name | MX循R15D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r15d-seed-20261003T175809Z-f69ce3fd（唯一） |
| data admission | stg-c2e8050af8ba4db1b4e144c49c5c7b9b（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_3cc1450700092fc19a46a9e3（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |
| 三件套 sha256 | listing 4be08e9e…b27968 / 方案 73024713…9a504199 / eCRF 8109d25a…ede15289（与 R13D 重建版逐字节一致） |

## 全链状态（自验实测，2026-10-03 19:28-19:32Z 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r15d_seed_state.json（17:58:09Z） |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（17:58:09Z） |
| 身份门/角色门 | ✅ 未触发 | documents_resolve 自动归属确认（analyzing→reviewing→adjudicating→ready），无人工门 |
| 文档权威 | ✅ ready=true | 17:58:10Z 提交→18:02:58Z ready（约4.8分钟）；protocol/ecrf 自动识别 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（18:03:03Z→18:16:56Z 约13.9分钟） |
| 复核收敛 | ✅ complete | adjudicate 轨迹：running(remaining=46) → 第二轮双队列46作业 → blocked(remaining=26, 系统裁决20) → 裁决卡作答 → complete(remaining=0)；2个终态失败分片（provider_runtime_error×1 reasoning-only、invalid_ai_output×1）经自动恢复后按 bounded-gap 设计收敛，未跳门 |
| 裁决卡 | ✅ 已答 | 共27张：1张首轮卡 EX.EXFRQ（R13 决策表）+ 22张既有表（R5/R8/R9/R11/R12 决策表）+ **4张R15新卡 VS.DBP/VS.HRRATE/VS.RESP/VS.SBP**（两轮分歧卡，历轮首次浮现，卡片显示主分析与独立复核同判同角色 token）首次浮现 fail-closed 诚实退出留痕（19:21:45Z），按 openpyxl 直读实测补答：VS 表 64 行测量数据（16受试者×4访视 R/W2/W4/W8），心率次分58-94/收缩压mmHg 98-140/舒张压mmHg 60-88/呼吸次分16-22 全为整数测量值，采纳卡面推荐 diastolic_blood_pressure/heart_rate/respiratory_rate/systolic_blood_pressure（19:27:45Z） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_23b664f6059daaaf1a96cf905a54 status=confirmed（**v74**），user_questions=0（19:28:00Z） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，10表/591行/**3038值全核验**（source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」（19:28:01Z） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true；`run-setup/options` **200** |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

起止：17:58:09Z→19:28:04Z（2026-10-04 01:58→03:28 CST 北京，约1小时30分，含 VS 新卡 fail-closed 退出后的补答重入一次）。AI 台账（medical_monitoring_ai.sqlite3 按 project_id 过滤）：46 作业（44完成/2终态failed均为 mapping 分片，经 bounded-gap 收敛 remaining=0）；73 次调用，tokens 合计 1,427,947（prompt 917,171 + completion 510,776）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **R15 新卡 VS 域四列为生命体征域的历轮首次分歧卡**：DBP/HRRATE/RESP/SBP 主分析与独立复核同判同角色 token 仍入裁决（分歧由两侧论证路径而非结论产生），已按数据实测采纳并固化进 `r15d_seed_csu.py` 的 R15_ROUND1_CARDS 表供后续轮次复用。
- 本轮 documents 链未触发身份门与角色人工门（自动归属确认），与 R14D 一致。
- 主侧AI直连绑定跨重启保持生效（R12D/R13D 换绑结果），本轮未再换绑；host 代理单点风险沿 R12D/R13D 记录。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r15d_seed_csu.py`（由 r14d_seed_csu.py 机械适配：R15D 命名/幂等键/留痕文件 + R15_ROUND1_CARDS 四卡表；R5/R8/R9/R11/R12/R13/R14 既有裁决卡决策表原样保留；幂等，含 fail-closed 未知卡防护）
- 证据：`r15d_seed_evidence.jsonl`（每步请求/响应摘要，含 VS 四卡 unknown_questions_fail_closed 留痕）、`r15d_seed_state.json`（幂等状态）、`r15d_seed_console.log`/`r15d_seed_console2.log`（两段运行控制台输出）
- 环境日志：`ISO_ENV_LOG.md`（R15D 探障+预置条目）

# R16D 开考位预置结果 — MX循R16D-CSU（2026-10-04）

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- 循环收尾已把旧项目全部软归档（`GET /api/projects` → `[]`），无存量项目可按原样探 → 按 R13D-R15D 先例建项后探：R16D 建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1/R13D/R14D/R15D 同款）；数据接入与 facts 物化后终态 project/open → current/complete（终态硬断言见下表）。
- 修复代码在位复核：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；R16D 新建 workspace 的 launch_registry marker sqlite 直查 = **v5**（现行进程写入实证），存量 15 个 workspace 逐库直查全部 v5，无 v4/shape_mismatch。
- 环境侧（R15 修复员 2026-10-04 凌晨双重启 8911+5178 后的现行进程）：8911 /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40）；5178 /monitoring=200（[::1]）且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_e82b9e8acc60** |
| project_name | MX循R16D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r16d-seed-20261004T001015Z-c018a8b7（唯一） |
| data admission | stg-e62b469df0b54c9a94866be0b8cef25e（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_76e97b66cde8d4a2c47a2954（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |
| 三件套 sha256 | listing 4be08e9e…b27968 / 方案 73024713…9a504199 / eCRF 8109d25a…ede15289（与 R15D 逐字节一致） |

## 全链状态（自验实测，2026-10-04 02:07-02:20Z 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r16d_seed_state.json（00:10:16Z） |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（00:10:16Z） |
| 身份门 | ✅ 触发一次 | documents_resolve → project_identity_incomplete → identity_confirmation 提交（00:12:42Z，等价界面一次点击，R5D同款手势）；角色门未触发（protocol/ecrf 自动识别 current） |
| 文档权威 | ✅ ready=true | 00:10:17Z 提交→00:14:43Z ready（约4.4分钟） |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（00:14:47Z→00:30:08Z 约15.3分钟） |
| 复核收敛 | ✅ complete | adjudicate 轨迹：running(remaining=46) → 第二轮队列44作业（中途1个 mapping 分片 failed 自动重试完成，终态44/44全completed，无 bounded-gap 缺口）→ blocked(remaining=23, 系统裁决23) → 已知裁决卡作答 → complete(remaining=0)，未跳门 |
| 裁决卡 | ✅ 已答 | 25次作答事件/23张唯一卡**全部由既有决策表覆盖**（R5/R8/R9/R11/R12/R13/R14/R15 表；EX.EXFRQ、EX.EXTRT 跨轮重复浮现各作答两次）——**本轮无新卡、无 fail-closed 退出** |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_09ce60ee5b30df2e05d3cbfd5ebb status=confirmed（**v72**），user_questions=0（02:07:46Z） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，10表/591行/**3550值全核验**（source_values_verified=3550），message「可用于监查的数据已生成，可以开始监查。」（02:07:46Z） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` **200** |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

起止：00:10:16Z→02:07:50Z（2026-10-04 08:10→10:07 CST 北京，约1小时58分，单段运行无中断）。AI 台账（medical_monitoring_ai.sqlite3 按 project_id 过滤）：44 作业全 completed（document_authority_analysis×2 + document_authority_review×2 + listing_field_mapping×40）；62 次调用，tokens 合计 1,344,591（prompt 876,253 + completion 468,338）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- 本轮无新裁决卡浮现：R15 及以前的决策表首次完整覆盖全部浮出卡（R8 的 AE.AENUM 本轮由系统自动裁决未浮卡）；VS 四卡也未再浮现。
- 身份门本轮触发一次（R14D/R15D 为自动归属确认），同三份文件跨轮行为有差异，按设计内人工门如实提交 identity_confirmation，未绕过。
- 主侧AI直连绑定沿 R12D/R13D 起保持生效，本轮未换绑、未复核 probe（无故障征兆）。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r16d_seed_csu.py`（由 r15d_seed_csu.py 机械适配：R16D 命名/幂等键/留痕文件；R5/R8/R9/R11/R12/R13/R14/R15 既有裁决卡决策表原样保留；幂等，含 fail-closed 未知卡防护）
- 证据：`r16d_seed_evidence.jsonl`（324 条事件，每步请求/响应摘要）、`r16d_seed_state.json`（幂等状态）、`r16d_seed_console.log`（运行控制台输出）
- 环境日志：`ISO_ENV_LOG.md`（R16D 探障+预置条目）

# R17D 开考位预置结果 — MX循R17D-CSU（2026-10-04）

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- 循环收尾已把旧项目全部软归档（`GET /api/projects` → `[]`），无存量项目可按原样探 → 按 R13D-R16D 先例建项后探：R17D 建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1 已知同款）；随后产品 `inspect_project_schema` 实证 R17D 新项目 6 成员全 current/current_shape（launch_registry marker=mm-r7-w01r26-launch-registry-v5，sqlite 直查同值）；数据接入后终态 project/open → current/complete（终态硬断言见下表）。
- 修复代码在位复核：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；隔离 runtime 存量 20 个 workspace（本轮建项前逐库 sqlite 直查）全部 v5，无 v4/shape_mismatch。
- 主侧AI路由沿 R12D/R13D 先例复核：直连配置跨重启仍生效（两主侧档案 base_url=open.bigmodel.cn 直连），产品 `/api/ai-gateway/probe` 双档案真实往返 passed:true（主侧 cms-router/glm-5.3-flash 3577ms；verifier ollama-cloud/deepseek-v4.1-flash 1018ms），**本轮无需换绑**。
- 环境侧：8911 /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，R16 修复员重启后的现行进程）；5178 存活（node 67415 监听 [::1]:5178）；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_6d794c3dfd2f** |
| project_name | MX循R17D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r17d-seed-20261004T132225Z-4d453cfc（唯一） |
| data admission | stg-ed22e6108aa04ace9423b87c542da86f（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_7e9b2f05ba8cfcbcbb237f18（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |
| 三件套 sha256 | listing 4be08e9e…b27968 / 方案 73024713…9a504199 / eCRF 8109d25a…ede15289（与 R15D/R16D 逐字节一致） |

## 全链状态（自验实测，2026-10-04 19:25-19:4xZ 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r17d_seed_state.json（13:22:25Z） |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（13:22:26Z） |
| 身份门/角色门 | ✅ 未触发 | documents_resolve 自动归属确认（analyzing→…→adjudicating→ready），无人工门 |
| 文档权威 | ✅ ready=true | 13:22:26Z 提交→13:33:00Z ready（约10.5分钟）；protocol/ecrf 自动识别 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（13:33:13Z→13:53:27Z 约20分钟） |
| 复核收敛 | ✅ complete | 16 次 adjudicate_drive 多轮双队列复核，终轮 blocked(remaining=9, 系统裁决37) → 9张裁决卡作答 → complete(remaining=0)；5个 listing_field_mapping 分片终态 failed=provider_runtime_error（retryable）经自动恢复预算与系统裁决收敛，未跳门 |
| 裁决卡 | ✅ 已答 | 共11次作答：首轮2张（EX.EXFRQ、EX.EXTRT，既有决策表）+ 终轮9张（AE.AENUM、AE.AEOUT、CM.CMENDAT/CMINDC/CMONGO/CMSTDAT/CMTRT、ICF_TRACK.ICFSTATE/ICFVER）**全部由既有决策表覆盖（R5/R8/R9/R11/R12/R13/R14/R15 表）——本轮无新卡、无 fail-closed 退出** |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_053c44ea0607a6086bb7d1b27dda status=confirmed（**v58**），user_questions=0，60字段（19:24:57Z confirm 200；独立复验同值） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/**1896值全核验**（values=source_values_verified=1896），message「可用于监查的数据已生成，可以开始监查。」（19:24:57Z facts 201） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` **200**（含 10表/591行 已核验事实快照） |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

起止：13:22:25Z→19:25:01Z（约6小时03分；其中复核收敛 13:56→19:24 约5.5小时，为本循环历轮最慢——多轮双队列+16次adjudicate）。AI 台账（medical_monitoring_ai.sqlite3 按 project_id 过滤）：102 作业（97完成：document_authority_analysis×2 + document_authority_review×4 + listing_field_mapping×91；5终态failed=provider_runtime_error，均经自动恢复与系统裁决收敛 remaining=0）；193 次调用，tokens 合计 2,947,513（prompt 1,788,654 + completion 1,158,859）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **收敛耗时异常拉长**：R16D 全程约2小时，本轮约6小时（复核收敛5.5小时）。作业失败模式未变（listing_field_mapping provider_runtime_error×5 与历轮相同、retryable），多轮双队列复核轮次明显多于近轮（16次 adjudicate_drive vs R16D 数次）；v19 工具型裁决单作业耗时波动（R10D 曾7.2小时）属已知慢模式，但本轮耗时回升提请循环所有者留意 provider 侧时延。
- **facts values 计数较近轮偏低**：本轮 1896（R16D 3550/R13D 3422/R12D 3038）。facts summary 的 values 计数随本轮确认版草稿的字段覆盖与列值非空分布变化，state=ready 且 values=source_values_verified 全核验、10表/591行与历轮一致；如实记录差异，不判为缺陷。
- **无新裁决卡**：终轮9张卡全部由 R8-R15 既有决策表覆盖，fail-closed 防护在位未触发（unknown_questions=0 全程）。
- 主侧AI直连绑定沿 R12D/R13D 起保持生效，本轮未换绑（probe 双档案 passed 预检在先）。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r17d_seed_csu.py`（由 r16d_seed_csu.py 机械适配：R17D 命名/幂等键/留痕文件；R5/R8/R9/R11/R12/R13/R14/R15 既有裁决卡决策表原样保留；幂等，含 fail-closed 未知卡防护）
- 证据：`r17d_seed_evidence.jsonl`（664 条事件，每步请求/响应摘要）、`r17d_seed_state.json`（幂等状态）、`r17d_seed_console.log`（运行控制台输出）
- 环境日志：`ISO_ENV_LOG.md`（R17D 探障+预置条目）

# R18D 开考位预置结果 — MX循R18D-CSU（2026-10-05）【受阻进行中：主侧AI服务方计划级限流】

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- 存量直探：R17D proj_user_6d794c3dfd2f 与 R17P proj_user_20c4a3880375 的 `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常」（归档仅影响列表展示，直接 API 探障可用）。
- 修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；隔离 runtime 全部 25 个存量 workspace 逐库 sqlite 直查 marker 全部 v5；R18D 新建 workspace marker 亦为 v5（现行进程写入实证）。`proj_mgk10_sar_real` 的 blocked 为该参考项目 workspace 不在本隔离 runtime，非缺陷。
- 主侧AI路由：角色绑定与 R17D 一致（medical_monitoring_ai→cms-router/glm-5.3-flash 直连 open.bigmodel.cn；verifier→ollama-cloud/deepseek-v4.1-flash），本轮**未换绑**；probe 实测 verifier passed:true、主侧 429（详见下）。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_74e02b4af07c** |
| project_name | MX循R18D-CSU |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r18d-seed-20260905T031600Z-dddcb662（唯一） |
| data admission | stg-87131078840646e1984b76b8fa1fb0fb（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_1f38738598938b07f25dc852（verifier 侧已 completed；主侧 429 卡住） |
| 三件套 sha256 | listing 4be08e9e…b27968 / 方案 73024713…9a504199 / eCRF 8109d25a…ede15289（与 R15D/R16D/R17D 逐字节一致） |

## 全链状态（截至 2026-10-05 08:20Z，如实记录）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects 03:16:00Z；state r18d_seed_state.json |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（03:16:00Z） |
| 文档权威 | ⛔ 卡住 | verifier 侧 03:21:17Z completed（25,568 tokens）；主侧 cms-router/glm-5.3-flash 连续 HTTP 429：01:16:12Z（台账最后一次主侧成功）→08:20Z 零成功，本批次 1,602 次尝试全 429，产品 infra 自动恢复反复 requeue 无法穿透 |
| 映射/确认/facts | ⏸ 未达 | 文档权威门 fail-closed 在前，未启动 |

## 卡点与恢复路径（未跳门、未改绑、未伪造状态）

- **卡点**：主侧AI服务方（open.bigmodel.cn 计划密钥）计划级配额冻结——同计划两个档案 probe 均 429、verifier（ollama-cloud）正常；主侧消耗 10-03=8.45M / 10-04=42.27M / 10-05（冻结前）=5.88M tokens；连续零成功 >7h（超 R16B 事件 5h 纪律线）。属外部服务方配额，非产品缺陷，守护员无权限处理（换绑主侧档案属循环所有者决策）。
- **恢复**：`r18d_supervise.sh`（nohup 独立存活）每 50 分钟重拉幂等驱动 `r18d_seed_csu.py`，resolve 轮询自动 requeue；配额恢复后自动推进至 confirmed+facts 停住（Step10 硬断言与 R17D 同口径）。验收：`r18d_seed_state.json` 出现 confirmed/facts_materialized、R5_SEEDED_PROJECT 本节更新终态表。
- 驱动与留痕：`r18d_seed_csu.py`（由 r17d_seed_csu.py 机械适配，diff 验证仅轮次命名差异；既有裁决卡决策表原样保留）、`r18d_seed_state.json`、`r18d_seed_evidence.jsonl`（1633 条）、`r18d_seed_console.log`、`r18d_supervise.sh`。

# R19D 开考位预置结果 — 常驻项目 MX循开考-CSU（2026-10-05）

> **常驻语义（本轮起生效）**：本项目为跨轮持久存在的开考项目，项目名固定「MX循开考-CSU」（无轮次后缀）。后续轮次开考预置**先查存量**：若 mapping confirmed + facts ready + project/open current 三者俱在，直接复用（零重复预置）；复盘按轮次归档时**不得删除/重建**本项目。本轮为该常驻名**首轮新建**（存量实测 user_projects 中 project_name='MX循开考-CSU' count=0）。

隔离环境：API `http://127.0.0.1:8911`（build api-a9bb87fb5ee7ab77，R18轮次修复员双重启后的现行进程），全程未触碰 8910/5177。
操作者：开考预置守护员-R19D。起止：2026-10-05 19:04:52Z → 20:44:23Z（约 1 小时 40 分，单段运行无中断）。

## 探障（本轮前置，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）

- 存量检查（常驻名首轮）：sqlite 直查 `user_projects` 中 project_name='MX循开考-CSU' **count=0** → 按 ask 新建；`GET /api/projects` → `[]`（历轮项目均已软归档，沿 R13D 起常态）。
- 修复代码在位：`services/api/app/main.py:4925-4936`（实测 4926 行导入 `SCHEMA_VERSION as _LAUNCH_REGISTRY_SCHEMA_VERSION`、4935-4936 行 launch_registry.sqlite3 种子 marker 取该常量；contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）。
- 存量库直查：隔离 runtime **30 个** workspace 的 launch_registry.sqlite3 marker 逐库 sqlite 直查**全部 v5**（0 个非 v5）；R19D 新建 workspace marker sqlite 直查 = **v5**（现行 build 写入实证）。
- 主侧AI路由：R18轮次任务所有者已于 10-05 11:13 把两主侧档案从直连换回 OmniRouter LB（127.0.0.1:20128，*.pre_omni_restore_1005_1113 快照留痕，见 ISO_ENV_LOG 同日条目）。本轮沿用现行配置，产品 `/api/ai-gateway/probe` 三档案真实往返全 passed:true（两主侧 cms-router/glm-5.3-flash 5853/753ms；verifier ollama-cloud/deepseek-v4.1-flash 661ms）——R18D 上午的 429 冻结已随路由纠错解除，**本轮无需换绑**。
- 环境侧：8911 /api/runtime-readiness ready:true（build api-a9bb87fb5ee7ab77）；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-a9bb87fb5ee7ab77 与 8911 backend_build_id 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- 建项瞬间 project/open blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1/R13D-R18D 同款，留痕 probe_recorded）；终态硬断言见下表。

## 项目

| 项 | 值 |
|---|---|
| project_id | **proj_user_6ef58ac151e1**（常驻，后续轮次复用勿删） |
| project_code | MW-PHASE-2210A806 |
| project_name | **MX循开考-CSU** |
| indication / product_name | 慢性自发性荨麻疹 / MG-K10 |
| modules | ["medical_monitoring"] |
| 幂等键 | r19d-seed-20260905T190452Z-5f59e580（唯一） |
| data admission | stg-cd69899943ba42618f589ba07a134a59（合成listing 591行/10表） |
| 文档权威批次 | mmbatch_06432a73d31b1d87094f90fd（方案V1.3 docx + eCRF指南V1.0 docx 双VLM） |
| 三件套 sha256 | listing 4be08e9e…b27968 / 方案 73024713…9a504199 / eCRF 8109d25a…ede15289（与 R13D-R18D 逐字节一致） |

## 全链状态（自验实测，2026-10-05 20:4x-20:5xZ 独立复验）

| 步骤 | 状态 | 证据 |
|---|---|---|
| 建项 | ✅ 201 | POST /api/projects（幂等键唯一）；state r19d_seed_state.json（19:04:52Z） |
| 数据接入 | ✅ | data-admissions/upload → attempt，591行/10表（19:04:55Z） |
| 身份门/角色门 | ✅ 未触发 | documents_resolve 自动归属确认（analyzing→reviewing→…→ready），无人工门（与 R14D/R15D/R17D 同款自动路径） |
| 文档权威 | ✅ ready=true | 19:04:55Z 提交→19:13:29Z ready（约8.6分钟）；protocol/ecrf 自动识别 |
| 映射双队列 | ✅ candidates_ready | 10主+10盲核，60字段候选（19:13:38Z→19:32:03Z 约18.5分钟） |
| 复核收敛 | ✅ complete | adjudicate 轨迹：running(remaining=46) → 第二轮双队列46作业 → blocked(remaining=32, 系统裁决14) → 33张裁决卡作答 → complete(remaining=0)；2个 listing_field_mapping 分片终态 failed（invalid_ai_output×1 不可重试、provider_runtime_error×1 可重试）经 bounded-gap 设计与系统裁决收敛，未跳门 |
| 裁决卡 | ✅ 已答 | 共33张**全部由既有决策表覆盖**（EX.EXTRT + R5/R8/R9/R11 各表：AE×8、CM×6、LB_HEM×7、MH×5、DM.ARM、ICF_TRACK.ICFSTATE、SV.VISDAT、UAS×4、MH.MHNUM）——**本轮无新卡、无 fail-closed 退出**（unknown_questions_fail_closed=0 全程，历轮首次单段零中断跑完全链） |
| **字段映射确认** | ✅ **confirmed** | GET mapping-candidates：confirmation_status=confirmed，draft monmapdraft_73abe5c6c9561a9e95eec2056991 status=confirmed（**v80**），user_questions=0，60字段（20:44:16Z confirm 200；独立复验同值） |
| **facts 物化** | ✅ **ready** | GET facts：state=ready，facts_generated=true，10表/591行/**3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」（20:44:16Z） |
| 界面可开始运行监查 | ✅ | `GET /r7/project/open` → state=current/openMode=edit/dataCoverage=complete/canView/canEdit=true「项目格式正常，可以继续使用。」；`run-setup/options` **200**；5178 /monitoring=200 且前后端 build 配对一致 |
| 停在 facts（未启动监查） | ✅ | GET runs → {"runs":[]} |

AI 台账（本项目，medical_monitoring_ai.sqlite3 按 project_id 过滤）：46 作业（44完成：document_authority_analysis×2 + document_authority_review×4 + listing_field_mapping×38；2终态failed 经自动恢复与系统裁决收敛 remaining=0）；76 次调用（68成功/8次 provider_error 重试路径），tokens 合计 1,628,699（prompt 1,073,162 + completion 555,537）。全程 AI 质量门自然通过，未跳门、未伪造状态。

## 本轮观察（如实记录，非阻断）

- **R19 新卡：零**。R15 及以前的决策表再次完整覆盖全部浮出卡；主侧路由回到 OmniRouter LB 后作业时延恢复常态（全程 1h40m，vs R17D 6h03m、R18D 卡阻 12h+）。R12D/R13D 直连换绑已由任务所有者纠错回 OmniRouter（ISO_ENV_LOG 2026-10-05「主侧路由纠错」条目），本轮沿用未动。
- **常驻项目就位**：后续轮次预置员的存量检查三条件（mapping confirmed + facts ready + project/open current）以本项目为准；本项目被循环收尾软归档不影响直接 API/界面使用（R18D 已实证归档项目 project/open 仍 current）。若某轮复盘归档逻辑按项目名前缀匹配轮次，请注意「MX循开考-」前缀不属于任何轮次、不应被归档删除。
- 8910/5177 无监听（沿 R11 起记录），本轮仅只读复核未触碰。

## 留痕文件（同目录）

- 驱动：`r19d_seed_csu.py`（由 r18d_seed_csu.py 机械适配：常驻项目名 MX循开考-CSU/幂等键/留痕文件；R5/R8/R9/R11/R12/R13/R14/R15 既有裁决卡决策表原样保留；幂等，含 fail-closed 未知卡防护；roundtrip diff 验证仅命名差异）
- 证据：`r19d_seed_evidence.jsonl`（每步请求/响应摘要）、`r19d_seed_state.json`（幂等状态）、`r19d_seed_console.log`（运行控制台输出）
- 环境日志：`ISO_ENV_LOG.md`（R19D 探障+预置条目）

# R20D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-06，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启。**

隔离环境：API `http://127.0.0.1:8911`（build api-a9bb87fb5ee7ab77，R19轮次修复员 R19-01/02 修复后现行进程），全程未触碰 8910/5177。
操作者：开考预置守护员-R20D。时点：2026-10-06（单次只读复验，无推进动作）。

## 存量检查（ask 步骤0，全部现场 curl 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且为常驻名 | ✅ | `GET /api/projects` → 全实例仅 1 项目 `[{proj_user_6ef58ac151e1, MX循开考-CSU}]`（R19 复盘归档刻意保留，见 round_19/REPORT.md:90） |
| 字段映射 confirmed | ✅ | `GET …/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，user_questions=0，candidate_count=60 |
| facts ready | ✅ | `GET …/facts` → state=ready，facts_generated（10表/591行/**3038值全核验** values=source_values_verified），message「可用于监查的数据已生成，可以开始监查。」 |
| project/open current | ✅ | `GET …/r7/project/open` → state=**current**/dataCoverage=complete/openMode=edit/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/study-documents` → ready=true「研究文件已准备好」 |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → HTTP 200；5178（[::1]）/monitoring=200 且 runtime-build.json expectedBackendBuildId=api-a9bb87fb5ee7ab77 与 8911 backend_build_id 配对一致 |
| 未启动监查 | ✅ | `GET …/r7/runs` → 仅 1 条 `run:0bf83a78bae2a60856267103`，**run_state=waiting_start**、result_available=false（R19 轮测试者开考时经向导创建的运行设置，从未启动；R19 归档已留痕「向导四步＋运行创建 run:0bf83a78…」，round_19/REPORT.md:35）。本轮未启动任何运行——运行启动留给随后的攻坚验证 |

## 探障（只读，未修码未重启）

- R5D marker 缺陷未复发：修复代码在位 `implementation/workbench/services/api/app/main.py:4925-4936`（种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`）；contracts `packages/medical_monitoring/runtime/launch_registry_contracts.py:53-54` = mm-r7-w01r26-launch-registry-v5；本项目 workspace `runs/tester_loop_iso_20260928/runtime/medical_monitoring_r7/proj_user_6ef58ac151e1/launch_registry.sqlite3` sqlite 直查 marker = **v5**。
- 8911 `/api/runtime-readiness` ready:true（build api-a9bb87fb5ee7ab77）；8910/5177 无监听（连接拒绝，沿 R11 起记录，仅只读复核未触碰）。
- 5178 vite 监听 [::1]（127.0.0.1 连接失败属监听地址特性，R17D 起已记录），[::1]:5178 实测 200。

## 本轮观察（如实记录）

- **零重复预置达成**：R19D 建立的常驻项目语义（跨轮持久、先查存量、仅补缺失）首轮生效，本轮无建项/上传/AI 作业/确认/fats 物化动作，AI 消耗=0；已确认状态为 R19D 当轮全链自然通过（46作业、无跳门）的持久终态，本轮零新增 AI 质量门交互，无可跳之门可伪造之状态。
- waiting_start 运行设置为 R19 开考测试遗留资产（非本轮产生、非启动态），保留不删（删除开考测试资产超出预置员权限且毁证据）；攻坚验证可直接启动该运行或另建新运行。
- 幂等键沿用 r19d-seed-20260905T190452Z-5f59e580（本轮未新建项目故无新键）。

## 留痕文件（同目录）

- 本轮无新驱动脚本（复用即结论）；证据为本节表内各 curl 实测值 + `ISO_ENV_LOG.md`（R20D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized 与现场实测一致）。

## R20 第二次复验（攻坚/修复轮之后的现态，2026-10-06 15:16Z 现场实测）

> 首验（上表）之后，同日 R19 攻坚工程师第1次与 R19 轮次修复员（R19-01/03）先后对隔离对 8911/5178 做过多次重启并加载新代码，且攻坚验证在常驻项目上启动并跑完了监查运行（见 ISO_ENV_LOG 同日条目）。本次复验确认：**常驻项目预置三条件在上述环境变更后依然全部成立**，本轮（开考预置守护员-R20）再次零新建、零 AI 作业、零代码修复、零重启、零启动运行。

| 条件 | 实测结果（本轮 curl/sqlite 现场值） | 证据 |
|---|---|---|
| 项目存在且 active | ✅ | `GET /api/projects` → 5 项目含 `proj_user_6ef58ac151e1 / MX循开考-CSU`（另 4 个为本轮他位项目 R20A-RUX/R20B-MY008/R20C-CSU/R20P-CSU，非本预置员所建） |
| 字段映射 confirmed | ✅ | `GET …/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → confirmation_status=**confirmed**，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，user_questions=0，candidate_count=60（与 R19D/R20D 首验同版未漂移） |
| facts ready | ✅ | `GET …/facts` → state=ready，facts_generated=true，10表/591行/**3038值全核验**（values=source_values_verified），message「可用于监查的数据已生成，可以开始监查。」 |
| project/open current | ✅ | `GET …/r7/project/open` → state=**current**/dataCoverage=complete/openMode=edit/canView/canEdit=true「项目格式正常，可以继续使用。」 |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **200**（data_batches/current_data/modes/rule_revisions 等就绪）；study-documents ready=true「研究文件已准备好」 |
| 修复代码在位 | ✅ | `services/api/app/main.py:4925-4927,4935-4936` 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54=mm-r7-w01r26-launch-registry-v5）；本项目 workspace launch_registry.sqlite3 marker sqlite 直查=**v5** |
| 前后端配对 | ✅ | 8911 `/api/runtime-readiness` ready:true（backend_build_id=api-a9bb87fb5ee7ab77）；5178 `[::1]/monitoring`=200，runtime-build.json expectedBackendBuildId=api-a9bb87fb5ee7ab77 一致 |
| 8910/5177 | 未触碰 | lsof 复核均无监听（沿 R11 起记录），本轮仅只读 curl/lsof |
| 监查运行现态 | 3 条 completed（非本轮启动） | `GET …/r7/runs` → run:0bf83a78…（R19 遗留 waiting_start，已被攻坚验证启动并完成）+ run:c22165ecc…/run:3ee655a0…，全部 run_state=completed/result_available=true；本轮零启动动作 |

本轮环境观察：8911 现行进程响应偶发慢（runtime-readiness 一次 25.9s，后续请求 1.7s 内）——与 ISO_ENV_LOG 同日「R7-01 事件循环独占画像」记录相符，属已知环境现象，未影响任何复验判据。

---

# R21D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-06T18:33-18:47Z，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启、零启动运行。**（常驻项目语义第 3 次复验：R19D 新建、R20D 两验、R21D 本验）

隔离环境：API `http://127.0.0.1:8911`（build **api-1d25bf363b10c2a5**，R20 轮次修复员重启后现行进程，见 ISO_ENV_LOG 2026-10-06 18:46 写作Agent适配落地与 2026-10-07 R20 修复员条目），全程未触碰 8910/5177。
操作者：开考预置守护员-R21（D位）。时点：2026-10-06T18:33→18:47Z（单次只读复验，无推进动作；宿主机时区 CEST，时间戳一律 UTC）。

## 环境漂移观察（R20D 15:16Z 复验之后、本轮之前由他位角色发生，非本轮动作）

- 后端 build 由 api-a9bb87fb5ee7ab77 变为 **api-1d25bf363b10c2a5**（ISO_ENV_LOG 同日两条重启记录；8911 /api/runtime-readiness ready:true 实测 0.46s 返回该值）。
- 隔离 runtime 根现为 `implementation/workbench/runs/tester_loop_iso_20260928/runtime/`（lsof 8911 进程 pid 12958 打开文件实证；仓库根 `runs/tester_loop_iso_20260928` 已不存在——R21D 首查曾按旧路径落空，如实记录）。
- 常驻项目监查运行 3→6 条（新增 run:7e110483518e034a843a612b / run:273d37362cda3d1a383d7f2d / run:b8f424d9c3a84a2f92467044，全部 completed、result_available=true，为 R20 攻坚/测试角色所启动，非本轮）。
- `GET /api/projects` 现仅 1 条（R20D 复验时 5 条：R20A/B/C/P 等他位项目已按轮次收尾归档，符合 R13D 起常态）；常驻项目 `proj_user_6ef58ac151e1` 保留且 status=active。

## 存量检查（ask 步骤0，全部现场 curl/sqlite 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且 active（常驻名） | ✅ | `GET /api/projects` → 全实例仅 1 项目 `proj_user_6ef58ac151e1 / MX循开考-CSU / 慢性自发性荨麻疹 / MG-K10`，status=active，modules 含 medical_monitoring（另有 dashboard/medical_writing/approvals） |
| 字段映射 confirmed | ✅ | `GET …/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，confirmation_status=**confirmed**，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，draft.user_questions 列表=0 项，summary candidate_count=60/field_count=60（与 R19D/R20D 同版未漂移） |
| facts 物化 ready | ✅ | `GET …/facts` → state=**ready**，facts_generated=true，10表/591行/**3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」；workspace facts-manifest.json 在盘（attempt=stg-cd69899943ba42618f589ba07a134a59，mapping_version=monmaprev_a8a8d780a593da9eaf100400fcbe，snapshot facts:f4bebca7701a87d2b6eec2ed，10表 AE/CM/DM/EX/ICF_TRACK/LB_HEM/MH/SV/UAS/VS，mtime Oct 5 22:44） |
| project/open current | ✅ | `GET …/r7/project/open` → state=**current**/dataCoverage=complete/openMode=edit/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/study-documents` → ready=true |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **HTTP 200**（data_batches/current_data/modes/rule_revisions/recommended_mode 等就绪）；5178 `[::1]/monitoring`=200 且 runtime-build.json expectedBackendBuildId=api-1d25bf363b10c2a5 与 8911 backend_build_id 配对一致 |
| 未启动监查（本轮零启动） | ✅ | `GET …/r7/runs` → 6 条全部 run_state=completed、result_available=true（3 条 R19/R20 攻坚遗留 + 3 条本轮窗口前他位新增）；本轮零启动动作——运行启动留给随后的攻坚验证 |
| R5D marker 缺陷未复发 | ✅ | 修复代码在位 `services/api/app/main.py:4925-4936`（种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`，import 实证）；contracts `packages/medical_monitoring/runtime/launch_registry_contracts.py:53-54` = mm-r7-w01r26-launch-registry-v5；本项目 workspace launch_registry.sqlite3 sqlite 直查（只读）`schema_version=mm-r7-w01r26-launch-registry-v5` |
| 8910/5177 未触碰 | ✅ | lsof 只读复核：8910/5177 均 0 监听（沿 R11 起记录）；本轮仅 curl/lsof/sqlite 只读 + 文档追加 |

AI 台账：本轮 **0 作业 0 调用**（复用即结论，无任何新 AI 质量门交互）；`/api/ai-gateway/status` 只读探看 configured（zhipu-coding-plan/glm-5.3-flash，无 route_validation_errors、无 missing_env），未做付费 probe。

## 本轮观察（如实记录，非阻断）

- **candidates 投影两处计数与权威终态不一致（新 build 投影怪癖，仅记录不判读）**：mapping-candidates 响应顶层 `facts_generated=False`（facts 端点与在盘 manifest 均为已物化，以权威 facts 端点为准）；summary 内 `pending_confirmation_count=60/user_question_count=1`（draft.status=confirmed 与 draft.user_questions=0 项为权威确认终态，同 R19D/R20D 实测一致）。如后续轮次发现该投影误导界面，提请修复员核 mapping_candidate_routes 投影字段语义。
- 常驻项目跨轮、跨 build（a9bb87fb→1d25bf36）、跨多轮重启后三条件依然成立——常驻复用语义经受住环境漂移考验。

## 留痕文件（同目录）

- 本轮无新驱动脚本/状态文件（复用即结论）；证据为本节表内各 curl/sqlite/lsof 实测值 + `ISO_ENV_LOG.md`（R21D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized，与现场实测一致）。

---

# R22D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-07T05:0x-05:27Z，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启、零启动运行。**（常驻项目语义第 4 次复验：R19D 新建、R20D 两验、R21D、R22D 本验）

隔离环境：API `http://127.0.0.1:8911`（build **api-1d25bf363b10c2a5**，与 R21D 同 build；进程 pid 已由 12958 变为 **54721**——R21 轮次修复员 2026-10-07 双重启所致，见 ISO_ENV_LOG「R21轮次·修复员」条目），全程未触碰 8910/5177。
操作者：开考预置守护员-R22（D位）。时点：2026-10-07T05:0x→05:27Z（单次只读复验，无推进动作；宿主机时区 CEST，时间戳一律 UTC）。

## 探查路径笔误更正（如实记录，非产品缺陷）

本员首轮按前几轮台账的简写路径 `…/api/projects/{pid}/r7/…` 探查，三个端点均 404，一度疑似「项目打不开」缺陷复发。核对 `r19d_seed_csu.py:516`（`mm = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/r7"`）与 8911 `/openapi.json`（43 条 r7 路由全部注册，路径含 `/modules/medical-monitoring/` 段）后确认：**404 系本员用了台账简写、漏掉 `/modules/medical-monitoring/` 段所致**，修正前缀后全部 200。未修码、未重启（无缺陷可修）。

## 存量检查（ask 步骤0，全部现场 curl/sqlite 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且 active（常驻名） | ✅ | `GET /api/projects` → 全实例仅 1 项目 `proj_user_6ef58ac151e1 / MX循开考-CSU / 慢性自发性荨麻疹 / MG-K10`，status=active，modules 含 medical_monitoring（另有 dashboard/medical_writing/approvals） |
| 字段映射 confirmed | ✅ | `GET …/modules/medical-monitoring/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，confirmation_status=**confirmed**，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，draft.user_questions=0 项，candidate_count=60/field_count=60（与 R19D-R21D 同版未漂移） |
| facts 物化 ready | ✅ | `GET …/facts` → state=**ready**，facts_generated=true，10表/591行/**3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」；workspace facts-manifest.json 在盘（`runtime/artifacts/facts-manifest.json`，attempt=stg-cd69899943ba42618f589ba07a134a59，mapping_version=monmaprev_a8a8d780a593da9eaf100400fcbe，10表 AE/CM/DM/EX/ICF_TRACK/LB_HEM/MH/SV/UAS/VS，mtime Oct 5 22:44:16——与 R21D 记录一致无漂移） |
| project/open current | ✅ | `GET …/r7/project/open` → state=**current**/openMode=edit/dataCoverage=complete/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/study-documents` → ready=true |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **HTTP 200**（data_batches/current_data/modes/rule_revisions/recommended_mode 等就绪）；5178 `[::1]/monitoring`=200 且 runtime-build.json expectedBackendBuildId=api-1d25bf363b10c2a5 与 8911 backend_build_id 配对一致 |
| 未启动监查（本轮零启动） | ✅ | `GET …/r7/runs` → 9 条全部 run_state=completed、result_available=true（R21D 时 6 条 → 现新增 run:6d60bb0c585fbf8ac186c87b / run:2ad95d98599ea6bddd7c723c / run:64254e31021f1b14fcc0f91d，为 R21 开考/攻坚角色所启动，非本轮）；本轮零启动动作——运行启动留给随后的攻坚验证 |
| R5D marker 缺陷未复发 | ✅ | 修复代码在位 `services/api/app/main.py:4925-4936`（本员直读 4900-4960 行实证：`from packages.medical_monitoring.runtime.launch_registry_contracts import SCHEMA_VERSION as _LAUNCH_REGISTRY_SCHEMA_VERSION`，launch_registry 作业 marker 取该常量，`if db_path.exists(): continue` 不碰已存在文件）；本项目 workspace `…/runtime/medical_monitoring_r7/proj_user_6ef58ac151e1/launch_registry.sqlite3` sqlite 只读直查 `schema_version=mm-r7-w01r26-launch-registry-v5`（v5） |
| 8910/5177 未触碰 | ✅ | lsof 只读复核：8910/5177 均 0 监听（沿 R11 起记录）；本轮仅 curl/lsof/sqlite 只读 + 文档追加 |
| runtime 就绪 | ✅ | 8911 `/api/runtime-readiness` → ready=true，backend_build_id=api-1d25bf363b10c2a5，runtime_schema_version=16 |

AI 台账：本轮 **0 作业 0 调用**（复用即结论，无任何新 AI 质量门交互）；`/api/ai-gateway/status` 只读探看 configured=true（zhipu-coding-plan/glm-5.3-flash，route_validation_errors=[]、missing_env=[]、deployment_profile_approved=true），未做付费 probe。

## 本轮观察（如实记录，非阻断）

- **candidates 投影怪癖沿 R21D 持续**：mapping-candidates 响应顶层 `facts_generated=False`、summary 内 `pending_confirmation_count=60/user_question_count=1`，与权威终态（facts 端点 state=ready 已物化、draft.status=confirmed、draft.user_questions=0 项）不一致。同 R21D 记录，仅记录不判读，提请修复员核 mapping_candidate_routes 投影字段语义。
- 常驻项目跨轮、跨进程重启（pid 12958→54721，R21 修复员重启加载 riskId/duplicate_of 等四项修复）后三条件依然全部成立且数据版本零漂移——常驻复用语义第 4 次经受住环境变更考验。
- `GET /api/projects/{pid}`（不带模块段）返回 405 Method Not Allowed（该项目详情无此 GET 路由），非阻断，仅记录。

## 留痕文件（同目录）

- 本轮无新驱动脚本/状态文件（复用即结论）；证据为本节表内各 curl/sqlite/lsof/openapi 实测值 + `ISO_ENV_LOG.md`（R22D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized，与现场实测一致）。

---

# R23D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-07T08:3x-08:4xZ，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启、零启动运行。**（常驻项目语义第 5 次复验：R19D 新建、R20D 两验、R21D、R22D、R23D 本验）

隔离环境：API `http://127.0.0.1:8911`（build **api-e041fb3ab9060114**——R22D 复验时的 api-1d25bf363b10c2a5 之后，R22 轮次修复员重启加载三项修复所致，见 ISO_ENV_LOG「2026-10-08 R22轮次·修复员」条目，属本轮之前他位动作），全程未触碰 8910/5177。
操作者：开考预置守护员-R23（D位）。时点：2026-10-07T08:3x→08:4xZ（单次只读复验，无推进动作；时间戳一律 UTC）。

## 探查路径更正（如实记录，非产品缺陷）

本员首轮按 R20D 台账简写路径 `…/r7/…`（漏 `/api/projects/{pid}/modules/medical-monitoring/` 前缀）与 `…/r7/study-documents`（漏 attempt 段）各得 404——前者 R22D 已记录同款笔误、后者核对 `r19d_seed_csu.py:554`（`{att}/study-documents`，att 为 attempt 基路径）与 `/openapi.json`（study-documents 路由挂 `…/r7/data-admissions/{attempt_id}/study-documents`）后确认均系本员探查路径笔误，修正后全 200。未修码、未重启（无缺陷可修）。

## 存量检查（ask 步骤0，全部现场 curl/sqlite 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且 active（常驻名） | ✅ | `GET /api/projects` → 全实例仅 1 项目 `proj_user_6ef58ac151e1 / MX循开考-CSU / 慢性自发性荨麻疹 / MG-K10`，status=active，modules 含 medical_monitoring（另有 dashboard/medical_writing/approvals） |
| 字段映射 confirmed | ✅ | `GET …/modules/medical-monitoring/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，confirmation_status=**confirmed**，draft **v80 status=confirmed**，draft.user_questions=0 项，candidate_count=60/field_count=60（与 R19D-R22D 同版未漂移） |
| facts 物化 ready | ✅ | `GET …/facts` → state=**ready**，facts_generated=true，10表/591行/**3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」 |
| project/open current | ✅ | `GET …/r7/project/open` → state=**current**/openMode=edit/dataCoverage=complete/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/r7/data-admissions/{attempt}/study-documents` → HTTP 200，ready=true |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **HTTP 200**（data_batches/current_data/modes/rule_revisions/recommended_mode/recommendation_reason 等就绪）；5178（node pid 13827 监听 [::1]:5178）/monitoring=200 且 runtime-build.json expectedBackendBuildId=api-e041fb3ab9060114 与 8911 backend_build_id 配对一致 |
| 未启动监查（本轮零启动） | ✅ | `GET …/r7/runs` → 12 条全部 run_state=completed、result_available=true（R22D 时 9 条 → 现新增 run:11bf9d406a9034e58b8504bf / run:c1175d6ba3d980bd3ae0dccb / run:98389c6e1b554500f4496b8b，为 R22 开考/攻坚角色所启动，非本轮）；本轮零启动动作——运行启动留给随后的攻坚验证 |
| R5D marker 缺陷未复发 | ✅ | 修复代码在位 `services/api/app/main.py:4920-4940`（本员直读实证：`from packages.medical_monitoring.runtime.launch_registry_contracts import SCHEMA_VERSION as _LAUNCH_REGISTRY_SCHEMA_VERSION`，launch_registry 作业 marker 取该常量）；contracts `launch_registry_contracts.py:53` `SCHEMA_VERSION = SCHEMA_VERSION_V5`；本项目 workspace `…/runtime/medical_monitoring_r7/proj_user_6ef58ac151e1/launch_registry.sqlite3` Python sqlite3 只读直查 `r7_launch_registry_meta.schema_version=mm-r7-w01r26-launch-registry-v5`（v5） |
| 8910/5177 未触碰 | ✅ | lsof 只读复核：8910/5177 均 0 监听（沿 R11 起记录）；本轮仅 curl/lsof/sqlite 只读 + 文档追加 |
| runtime 就绪 | ✅ | 8911 `/api/runtime-readiness` → ready=true，backend_build_id=api-e041fb3ab9060114，runtime_schema_version=16 |

AI 台账：本轮 **0 作业 0 调用**（复用即结论，无任何新 AI 质量门交互）；`/api/ai-gateway/status` 只读探看 configured=true（route_validation_errors=[]、missing_env=[]、deployment_profile_approved=true），未做付费 probe。项目状态源文件 `r19d_seed_state.json`（confirmed=true / facts_materialized=true，updated_at 2026-10-05T20:44:16Z）与现场实测一致。

## 本轮观察（如实记录，非阻断）

- **candidates 投影怪癖沿 R21D/R22D 持续**：mapping-candidates 响应顶层 `facts_generated=False`、summary 内 `pending_confirmation_count=60/user_question_count=1`，与权威终态（facts 端点 state=ready/facts_generated=true、draft.status=confirmed、draft.user_questions=0 项）不一致。同前两轮记录，仅记录不判读，提请修复员核 mapping_candidate_routes 投影字段语义。
- 常驻项目跨轮、跨进程重启、跨新 build（a9bb87fb→1d25bf36→**e041fb3a**）后三条件依然全部成立且数据版本零漂移（draft v80 / facts 3038 值，R19D 终态原样）——常驻复用语义第 5 次经受住环境变更考验。
- `GET /api/projects/{pid}`（不带模块段）返回 405（沿 R22D 记录，该项目详情无此 GET 路由），非阻断，仅记录。

## 留痕文件（同目录）

- 本轮无新驱动脚本/状态文件（复用即结论）；证据为本节表内各 curl/sqlite/lsof/openapi 实测值 + `ISO_ENV_LOG.md`（R23D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized，与现场实测一致）。

---

# R24D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-07，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启、零启动运行。**（常驻项目语义第 6 次复验：R19D 新建、R20D 两验、R21D、R22D、R23D、R24D 本验）

隔离环境：API `http://127.0.0.1:8911`（build **api-06744bbced9d86a2**——R23D 复验时的 api-e041fb3ab9060114 之后，先后经 R23-01 修复员双重启（线程池扩容+写锁上限修复）与 R24 隔离环境守护员在循环收尾停机后恢复隔离对，均属本轮之前他位动作，见 ISO_ENV_LOG 2026-10-08 R23-01 与 2026-10-07 17:44 R24 守护员条目），全程未触碰 8910/5177。
操作者：开考预置守护员-R24（D位）。时点：2026-10-07（单次只读复验，无推进动作；时间戳一律 UTC）。

## 环境漂移观察（R23D 之后、本轮之前由他位角色发生，非本轮动作）

- 后端 build 由 api-e041fb3ab9060114 变为 **api-06744bbced9d86a2**；隔离环境曾于 10-07 17:18 循环收尾时整体停止、17:44 由 R24 隔离环境守护员按 ask 恢复 8911+5178（runtime 目录在盘、指纹配对一致，见 ISO_ENV_LOG 同日条目）——常驻项目跨「停机→恢复」周期存活。
- 常驻项目监查运行 12→15 条（新增 3 条全部 completed、result_available=true，为 R23 开考/攻坚角色所启动，非本轮）。

## 存量检查（ask 步骤0，全部现场 curl/sqlite/lsof 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且 active（常驻名） | ✅ | `GET /api/projects` → 全实例仅 1 项目 `proj_user_6ef58ac151e1 / MX循开考-CSU / 慢性自发性荨麻疹 / MG-K10`，status=active，modules 含 medical_monitoring（另有 dashboard/medical_writing/approvals） |
| 字段映射 confirmed | ✅ | `GET …/modules/medical-monitoring/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，confirmation_status=**confirmed**，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，draft.user_questions=0 项，summary candidate_count=60/field_count=60（与 R19D-R23D 同版未漂移） |
| facts 物化 ready | ✅ | `GET …/facts` → state=**ready**，facts_generated=true，summary **10表/591行/3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」 |
| project/open current | ✅ | `GET …/r7/project/open` → HTTP 200，state=**current**/openMode=edit/dataCoverage=complete/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/r7/data-admissions/{attempt}/study-documents` → HTTP 200，ready=true |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **HTTP 200**；5178 `[::1]/monitoring`=200 且 runtime-build.json expectedBackendBuildId=api-06744bbced9d86a2（frontendBuildId=web-61cf3eec89de9bcb）与 8911 backend_build_id 配对一致 |
| 未启动监查（本轮零启动） | ✅ | `GET …/r7/runs` → 15 条全部 run_state=completed、result_available=true（R23D 时 12 条 → 新增 3 条为 R23 开考/攻坚角色所启动，非本轮）；本轮零启动动作——运行启动留给随后的攻坚验证 |
| R5D marker 缺陷未复发 | ✅ | 修复代码在位 `implementation/workbench/services/api/app/main.py:4936`（`from …launch_registry_contracts import SCHEMA_VERSION as _LAUNCH_REGISTRY_SCHEMA_VERSION`）+ `main.py:4946`（launch_registry.sqlite3 种子 marker 取该常量）；`packages/medical_monitoring/runtime/launch_registry_contracts.py:54` `SCHEMA_VERSION = SCHEMA_VERSION_V5`；本项目 workspace `…/runtime/medical_monitoring_r7/proj_user_6ef58ac151e1/launch_registry.sqlite3` Python sqlite3 只读直查（r7_launch_registry_meta 为 key/value 表）`('schema_version','mm-r7-w01r26-launch-registry-v5')` = **v5** |
| 8910/5177 未触碰 | ✅ | lsof 只读复核：8910/5177 均 0 监听（沿 R11 起记录）；本轮仅 curl/lsof/sqlite 只读 + 文档追加 |
| runtime 就绪 | ✅ | 8911 `/api/runtime-readiness` → ready=true，backend_build_id=api-06744bbced9d86a2，runtime_schema_version=16 |

AI 台账：本轮 **0 作业 0 调用**（复用即结论，无任何新 AI 质量门交互，无可跳之门可伪造之状态）；已确认终态为 R19D 当轮全链自然通过（46作业）的持久状态。项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized）与现场实测一致。

## 本轮观察（如实记录，非阻断）

- **candidates 投影怪癖沿 R21D-R23D 持续**：mapping-candidates 响应顶层 `facts_generated=False`、summary 内 `pending_confirmation_count=60/user_question_count=1`，与权威终态（facts 端点 state=ready/facts_generated=true、draft.status=confirmed、draft.user_questions=0 项）不一致。同前三轮记录，仅记录不判读，提请修复员核 mapping_candidate_routes 投影字段语义。
- 常驻项目跨轮、跨进程重启、跨新 build（a9bb87fb→1d25bf36→e041fb3a→**06744bbc**）、跨环境停机恢复后三条件依然全部成立且数据版本零漂移（draft v80 / facts 3038 值，R19D 终态原样）——常驻复用语义第 6 次经受住环境变更考验。
- `GET /api/projects/{pid}`（不带模块段）返回 405（沿 R22D/R23D 记录，该项目详情无此 GET 路由），非阻断，仅记录。

## 留痕文件（同目录）

- 本轮无新驱动脚本/状态文件（复用即结论）；证据为本节表内各 curl/sqlite/lsof 实测值 + `ISO_ENV_LOG.md`（R24D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized，与现场实测一致）。

---

# R25D 开考位预置结果 — 复用常驻项目 MX循开考-CSU（2026-10-08T00:5xZ，零重复预置）

> **本轮动作：查存量 → 三条件现场实测全过 → 直接复用，零新建、零 AI 作业、零代码修复、零重启、零启动运行。**（常驻项目语义第 7 次复验：R19D 新建、R20D 两验、R21D、R22D、R23D、R24D、R25D 本验）

隔离环境：API `http://127.0.0.1:8911`（build **api-157c89f897d07331**，进程 pid 74159），全程未触碰 8910/5177。
操作者：开考预置守护员-R25（D位）。时点：2026-10-08T00:5xZ（单次只读复验，无推进动作；时间戳一律 UTC）。

## 环境漂移观察（R24D 之后、本轮之前由他位角色发生，非本轮动作，均见 ISO_ENV_LOG 同期条目）

- 后端 build 由 api-06744bbced9d86a2 变为 **api-157c89f897d07331**：R24 轮次修复员（R24-03/04/05/06、R18-03、R22-06 修复）双重启加载新代码；随后 R25 隔离环境守护员于 10-08 00:29-00:31 对 API 假死（pid 69228 响应超时）做恢复性重启（现行 pid 74159）并重启 5178（node pid 74210）。
- 常驻项目监查运行 15→19 条（R24D 时 15 条 → R24 开考/攻坚角色 +3、R24 轮次修复员诊断验证 R18-03 放行分支时在常驻项目上真实创建 run:4d16d078ea9ae0d29ae898ae +1，修复员日志已如实留痕「18→19 条」）。
- `main.py` marker 修复代码行号由 4936/4946 平移至 **5020/5030**（R24 轮代码插入所致，修复本身仍在位，本员直读实证）。

## 存量检查（ask 步骤0，全部现场 curl/sqlite/lsof 实测）

| 条件 | 实测结果 | 证据 |
|---|---|---|
| 项目存在且 active（常驻名） | ✅ | `GET /api/projects` → 全实例仅 1 项目 `proj_user_6ef58ac151e1 / MX循开考-CSU / 慢性自发性荨麻疹 / MG-K10`，status=active，modules 含 medical_monitoring（另有 dashboard/medical_writing/approvals，implementation_status=real_source_slice） |
| 字段映射 confirmed | ✅ | `GET …/modules/medical-monitoring/r7/data-admissions/stg-cd69899943ba42618f589ba07a134a59/mapping-candidates?focus=all` → state=candidates_ready，confirmation_status=**confirmed**，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 status=confirmed**，draft.user_questions=0 项，summary candidate_count=60/field_count=60（与 R19D-R24D 同版未漂移） |
| facts 物化 ready | ✅ | `GET …/facts` → state=**ready**，facts_generated=true，summary **10表/591行/3038值全核验**（values=source_values_verified=3038），message「可用于监查的数据已生成，可以开始监查。」；workspace 在盘 facts-manifest.json（`…/proj_user_6ef58ac151e1/runtime/artifacts/facts-manifest.json`，attempt=stg-cd69899943ba42618f589ba07a134a59，mapping_version=monmaprev_a8a8d780a593da9eaf100400fcbe，10表 AE/CM/DM/EX/ICF_TRACK/LB_HEM/MH/SV/UAS/VS，mtime Oct 5 22:44——与 R21D/R22D 记录零漂移） |
| project/open current | ✅ | `GET …/modules/medical-monitoring/r7/project/open` → state=**current**/openMode=edit/dataCoverage=complete/canView=true/canEdit=true「项目格式正常，可以继续使用。」 |
| 研究文件 ready | ✅ | `GET …/r7/data-admissions/{attempt}/study-documents` → HTTP 200，ready=true |
| 界面可开始运行监查 | ✅ | `GET …/r7/run-setup/options` → **HTTP 200**（data_batches/current_data/modes/rule_revisions/recommended_mode=daily 等就绪，current_data 快照 10表/591行/3038值100%往返校验）；5178（node pid 74210 监听 [::1]:5178）`/monitoring`=200 且 `/runtime-build.json` expectedBackendBuildId=api-157c89f897d07331（frontendBuildId=web-61cf3eec89de9bcb）与 8911 backend_build_id 配对一致 |
| 未启动监查（本轮零启动） | ✅ | `GET …/r7/runs` → 19 条全部 run_state=completed（18 条 result_available=true；1 条 false 为 R19 向导遗留 run:0bf83a78，R20D 已留痕其非启动态演变）；本轮零启动动作——运行启动留给随后的攻坚验证 |
| R5D marker 缺陷未复发 | ✅ | 修复代码在位：`services/api/app/main.py:5020`（`from …launch_registry_contracts import SCHEMA_VERSION as _LAUNCH_REGISTRY_SCHEMA_VERSION`）+ `main.py:5030`（launch_registry.sqlite3 种子 marker 取该常量）；`packages/medical_monitoring/runtime/launch_registry_contracts.py:53-54` `SCHEMA_VERSION = SCHEMA_VERSION_V5`；本项目 workspace `…/runtime/medical_monitoring_r7/proj_user_6ef58ac151e1/launch_registry.sqlite3` Python sqlite3 只读直查（uri mode=ro）`schema_version=mm-r7-w01r26-launch-registry-v5`（v5） |
| 8910/5177 未触碰 | ✅ | lsof 只读复核：8910/5177 均 0 监听（沿 R11 起记录）；本轮仅 curl/lsof/sqlite 只读 + 文档追加 |
| runtime 就绪 | ✅ | 8911 `/api/runtime-readiness` → ready=true，backend_build_id=api-157c89f897d07331，runtime_schema_version=16，runtime_store_ready=true，independent_ai configured=true（zhipu-coding-plan/glm-5.3-flash，route_validation_errors=[]） |

AI 台账：本轮 **0 作业 0 调用**（复用即结论，无任何新 AI 质量门交互，无可跳之门可伪造之状态）；已确认终态为 R19D 当轮全链自然通过（46作业）的持久状态。项目状态源文件 `r19d_seed_state.json`（confirmed=true/facts_materialized=true，updated_at 2026-10-05T20:44:16Z）与现场实测一致。

## 本轮观察（如实记录，非阻断）

- **candidates 投影怪癖沿 R21D-R24D 持续**：mapping-candidates 响应顶层 `facts_generated=False`、summary 内 `pending_confirmation_count=60/user_question_count=1`，与权威终态（facts 端点 state=ready/facts_generated=true、draft.status=confirmed、draft.user_questions=0 项）不一致。同前四轮记录，仅记录不判读，提请修复员核 mapping_candidate_routes 投影字段语义。
- 常驻项目跨轮、跨进程重启、跨新 build（a9bb87fb→1d25bf36→e041fb3a→06744bbc→**157c89f8**）、跨 API 假死恢复周期后三条件依然全部成立且数据版本零漂移（draft v80 / facts 3038 值，R19D 终态原样）——常驻复用语义第 7 次经受住环境变更考验。
- R24 轮次修复员在常驻项目上创建的 run:4d16d078 属诊断性放行验证（ISO_ENV_LOG 已留痕），本轮 runs 19 条全 completed、无 waiting_start 残留，不影响「停在 facts、运行启动留给攻坚验证」的轮次交接语义。

## 留痕文件（同目录）

- 本轮无新驱动脚本/状态文件（复用即结论）；证据为本节表内各 curl/sqlite/lsof 实测值 + `ISO_ENV_LOG.md`（R25D 复用条目）；项目状态源文件 `r19d_seed_state.json`（confirmed/facts_materialized，与现场实测一致）。
