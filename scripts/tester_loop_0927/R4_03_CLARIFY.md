# R4-03 口径澄清：导入概况 59 张表 vs 字段识别 22 张表

- 发现出处：`scripts/tester_loop_0927/round_04/report_B.md` F4（同一页面「1 个文件 · 59 张数据表 · 3557 行数据」vs「已识别 22 张数据表」，无口径说明）。
- 澄清日期：2026-09-29。方法：代码级追链路 + 隔离环境（`runs/tester_loop_iso_20260928`）第4轮 B 位 MY008 尝试的落库数据逐表重算。

## 一、结论（一句话）

**22 不是「剔除了代码对照表/名册页等辅助表」的正确口径，而是字段识别主队列未收敛时的部分计数（识别漏识别口径）：59 张工作表全部被提交识别（含 Code_List、SUBJ、DOMAIN_NAME），主队列最终只为其中 22 张产出了字段候选，其余 37 张的作业全部终态 `stale_input`（个别 `failed`），候选为零。**

判定：`isDefect = true`（按任务二分法落入「漏识别」侧）。根因不是新的分类/排除缺陷，而是已知「后台任务收敛性」缺陷族（R2-05/R2-10/R4 报告§六建议的家族归并）在 59 表真实清单上的表现；R5 冲刺已落病根修复（commit `4c0ea2b`：worker 兜底轮询），但本次尝试的 37 张表作业已终态、不会自行补齐。

## 二、两个数字的代码级来历

1. **59（第2步「导入概况」）**：`frontend/src/features/medical-monitoring/medicalMonitoringAdmissionWizardState.mjs:416`
   `summaryText = ${files} 个文件 · ${tableViews.length} 张数据表 · ${rows} 行数据`，
   `tableViews` 来自后端 admission profile 的 `payload.tables`——即导入文件被解析出的**全部工作表**（数据级核实：该尝试 domain object `data_admission/stg-0e1364ec…` 的 `summary = {files:1, rows:3557, tables:59}`，`tables` 数组含 `Code_List`、`SUBJ`、`DOMAIN_NAME`）。
2. **22（第3步「已识别 N 张数据表」）**：`frontend/src/features/medical-monitoring/MedicalMonitoringAdmissionWizard.jsx:314`（修改前行号）渲染 `tables.length`，其来源是 `medicalMonitoringAdmissionMappingConfirmState.mjs:152-174` 对 `payload.candidates` 按 `domain` 去重——即**已完成识别作业已产出字段候选的表数**。
3. 候选组装：`packages/medical_monitoring/admission/mapping_pipeline.py:1870-1940`（`_project`）只收集 `status == "completed"` 作业的 `field_mappings`；作业集合经 `list_candidates`→`_latest_job_cohort`（同文件 :270-369）限定为主分析队列（primary cohort）。

## 三、「排除逻辑」核实结果：不存在名册/代码表排除

- 映射输入构造 `packages/medical_monitoring/admission/mapping_bridge.py:367-419`：`admission_record_to_harness_input` 对 admission record 的 `tables` **逐表全部**生成字段画像并入 `expected_domains`，无任何按表名/表形态剔除代码表或名册页的分支。
- 全后端检索 `名册`：仅出现在 `packages/medical_monitoring/projections/facts_publication.py:1001,1014`（事实投影的记录来源文案），与导入/识别无关；`Code_List` 仅出现在前端显示用兜底字典 `medicalMonitoringAdmissionWizardState.mjs:347-365`（给表名补中文标注，不是排除）。
- 物理完整性层 `packages/medical_monitoring/admission/workbook_manifest.py` 只按 `content_kind`（empty/header_only/data）与可见性处理**空表/隐藏表**并要求显式 `omission_reason`（隐藏数据表甚至阻断），本次 59 张全部 emitted（`source_profile_reconciliation` 在 technical_details 中，无 omission）。
- **数据级反证（最强证据）**：`runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3` 中该尝试（`proj_user_0df3e40fb754` / `stg-0e1364ec768940f3893ca2599b74144b`）共提交 354 个 `listing_field_mapping` 作业（主/校验队列各 177 个），**两个队列的作业各覆盖全部 59 张 sheet，包含 `Code_List`、`SUBJ`、`DOMAIN_NAME`**；校验队列甚至已为 `Code_List` 产出 4 个字段候选。即：系统没有、也没打算把辅助表排除在识别之外。

## 四、37 张表逐张核对（59-22）

重算方法：候选表 `monitoring_ai_candidates`（按 `structured_payload.field_mappings` 聚合）联作业表按 business_key 分队列；sheet 名单取 admission record。状态为该次尝试全部作业的终态（2026-09-29 03:21 UTC 后不再变化）。

| sheet | 主队列作业 | 主队列候选字段 | 校验队列作业 | 校验队列候选字段 |
|---|---|---|---|---|
| DOMAIN_NAME | stale_input (1) | 0 | failed (1) | 0 |
| AE | completed,stale_input (7) | 25 | completed,failed (7) | 49 |
| CM6 | stale_input (5) | 0 | completed,failed (5) | 40 |
| DM | stale_input (2) | 0 | completed (2) | 24 |
| DS | stale_input (2) | 0 | completed (2) | 19 |
| DS1 | stale_input (2) | 0 | completed (2) | 18 |
| DS2 | completed,stale_input (3) | 2 | completed (3) | 26 |
| DS3 | stale_input (2) | 0 | completed (2) | 22 |
| DS4 | stale_input (2) | 0 | completed (2) | 21 |
| DS_NEXT | stale_input (2) | 0 | completed (2) | 17 |
| EC1 | stale_input (3) | 0 | completed (3) | 34 |
| EC2 | stale_input (3) | 0 | completed (3) | 32 |
| EG | stale_input (3) | 0 | completed (3) | 34 |
| IE | stale_input (2) | 0 | completed (2) | 20 |
| LB | stale_input (2) | 0 | completed (2) | 23 |
| LB1 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB10 | stale_input (3) | 0 | completed (3) | 36 |
| LB11 | completed,stale_input (3) | 1 | completed (3) | 25 |
| LB12 | stale_input (3) | 0 | completed (3) | 36 |
| LB13 | stale_input (3) | 0 | completed (3) | 36 |
| LB14 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB15 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB16 | stale_input (3) | 0 | completed (3) | 36 |
| LB17 | stale_input (3) | 0 | completed (3) | 36 |
| LB18 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB2 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB3 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB4 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB5 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB6 | stale_input (3) | 0 | completed (3) | 36 |
| LB7 | stale_input (3) | 0 | completed (3) | 36 |
| LB8 | completed,stale_input (4) | 1 | completed (4) | 37 |
| LB9 | stale_input (3) | 0 | completed (3) | 36 |
| MH1 | stale_input (3) | 0 | completed (3) | 33 |
| MH3 | completed,stale_input (5) | 2 | completed (5) | 50 |
| MH4 | stale_input (2) | 0 | completed (2) | 19 |
| MHAL | stale_input (2) | 0 | completed (2) | 21 |
| MO | stale_input (3) | 0 | stale_input (3) | 0 |
| MO2 | stale_input (3) | 0 | stale_input (3) | 0 |
| PC1 | stale_input (2) | 0 | stale_input (2) | 0 |
| PC2 | stale_input (2) | 0 | stale_input (2) | 0 |
| PC3 | stale_input (2) | 0 | stale_input (2) | 0 |
| PE | stale_input (3) | 0 | stale_input (3) | 0 |
| PE2 | completed,stale_input (6) | 1 | stale_input (6) | 0 |
| PR | stale_input (3) | 0 | stale_input (3) | 0 |
| PR4 | stale_input (4) | 0 | stale_input (4) | 0 |
| QS1 | stale_input (2) | 0 | stale_input (2) | 0 |
| RP | stale_input (3) | 0 | stale_input (3) | 0 |
| RP2 | stale_input (2) | 0 | stale_input (2) | 0 |
| SU1 | completed,stale_input (2) | 12 | stale_input (2) | 0 |
| SUBJ | stale_input (2) | 0 | stale_input (2) | 0 |
| SV1 | completed,stale_input (2) | 12 | stale_input (2) | 0 |
| SV2 | completed,stale_input (4) | 12 | stale_input (4) | 0 |
| VA | completed,stale_input (2) | 12 | stale_input (2) | 0 |
| VS1 | completed,stale_input (3) | 12 | stale_input (3) | 0 |
| VS3 | completed,stale_input (3) | 12 | stale_input (3) | 0 |
| XT | completed,stale_input (3) | 12 | stale_input (3) | 0 |
| XT2 | completed,stale_input (4) | 12 | stale_input (4) | 0 |
| Code_List | stale_input (1) | 0 | completed (1) | 4 |

读法：37 张「缺口」表的统一被排除理由 = **没有任何排除规则，只是它们的主队列识别作业没有完成**（stale_input=提交后在认领时输入版本复核不匹配被判废，`services/api/app/monitoring_ai_service.py:2466-2479` + `monitoring_ai_repository.stale_claimed`；本批 213 个 stale 标记集中在 2026-09-29 02:00–03:21 UTC 的一轮队列清扫）。`Code_List`/`SUBJ`/`DOMAIN_NAME` 与临床表同等待遇，进一步证明「辅助表被剔除」的解读不成立。

### 与 B 位观察的时间线吻合（主队列）

| UTC 时间 | 累计字段 | 累计表数 |
|---|---|---|
| 15:31:47 | 16 | 3 |
| 15:32:35 | 20 | 7 |
| 15:33:26 | 25 | 12 |
| 15:34:08 | 52 | 16 |
| 15:34:59 | 100 | 20 |
| **15:35:21** | **124** | **22** |
| 17:15:13 | 136 | 22（此后主队列再无新候选） |

B 报告的成长序列「0→16→20→25→52→100→124 后纹丝不动」与上表逐点一致（导入发生于 15:16 UTC ≈ 北京 23:16）。「冻结」即主队列在 15:35 后停止产出；同时段校验队列仍在缓慢完成（至次日 02:49 共 46 表/1152 字段），资源被校验队列占满（`WORKBENCH_MONITORING_AI_PARALLELISM=2`）。

## 五、与「反过拟合正面证据」假说的关系

假说被否定：这不是泛化排除逻辑首次生效，因此**不存在「值得被看见」的正面证据**；`round_04/REPORT.md` §一提出的「若 22 为排除后域表数」前提不成立。真正的正面信息只有一条：59 张表（含辅助表）全部进入识别管道，无静默丢弃——完整性方向无缺陷。

## 六、落地（本次提交）

修改 `frontend/src/features/medical-monitoring/MedicalMonitoringAdmissionWizard.jsx`：

1. 第2步导入概况：summaryText 下新增一行口径说明（表数=文件内全部工作表，含辅助表，识别逐表进行，不预先剔除）。
2. 第3步「已识别 N 张数据表」下方新增口径说明：该数只统计**已产出识别结果**的表；generating/needs_attention 态附「识别仍在生成中/部分任务未完成」短语；明确「不会静默排除任何表」。
3. **替换** commit `4c0ea2b`（R5 冲冲「R4-03表数口径注记」）引入的错误注记——原文称「代码对照表、名册页等非数据域表不在此列」，与本次数据级核实相反，属于无依据的排除式解释，必须纠正为诚实口径。

验证（本机执行）：
- `node --test src/features/medical-monitoring/*.test.mjs` → 77/77 pass；
- `node --test $(find src -name "*.test.mjs")`（frontend 全量）→ 83/83 pass；
- 用渲染测试同一 esbuild 夹具重渲各状态：第2步新注、第3步新注均出现，旧排除式文案在所有状态中消失。

## 七、复核命令（数据级，可在隔离环境重跑）

```sh
cd implementation/workbench/runs/tester_loop_iso_20260928/runtime
sqlite3 medical_monitoring_r7/proj_user_0df3e40fb754/runtime/monitoring_runtime.sqlite3 \
  "SELECT json_extract(object_json,'$.summary') FROM domain_objects WHERE kind='data_admission';"
sqlite3 medical_monitoring_ai.sqlite3 \
  "SELECT business_key, status FROM monitoring_ai_jobs WHERE project_id='proj_user_0df3e40fb754' AND task_type='listing_field_mapping';"
```
第一条应返回 `{"files":1,"rows":3557,"tables":59}`；第二条按 business_key 前缀分队列后应见 59 个不同 sheet 名（两队列各一），主队列 completed 作业的候选 domain 去重恰为 22 个。

## 八、遗留（不在本次范围）

- 37 张表的主队列作业终态 `stale_input` 的触发链（认领时 `current_admission_mapping_revision` 复核为何在 09-29 02:00 后整体判废）未在本任务内根因定位，归属「后台任务收敛性」家族（R5 已落 worker 兜底轮询修复，需下轮验证对 stale 判废链是否同样生效）。
- 本尝试（stg-0e1364ec…）如需补齐 22→59，须重新发起识别（重新提交作业），旧作业不会自愈。
