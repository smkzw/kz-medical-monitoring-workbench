# AI Medical Manager Workbench Scaffold

This scaffold is the non-visual foundation for the AI full-process medical manager workbench.

Current scope:

- canonical multi-project catalog and project-scoped module route bindings for RUX, D001, MY009, MY008 PNH, MG-K10 CRSwNP, and the explicit MG-K10 SAR demo;
- shared contracts for project, evidence, data batches, risk cases, approval gates, protocol documents, and AI revision threads;
- deterministic realistic demo data, including medical-monitoring subject drilldowns for timeline, efficacy/safety trends, and timepoint risk prompts;
- minimal FastAPI service exposing dashboard, module read models, subject-level monitoring drilldown, the first real-data `证据调研与方案设计` manifest, the first real-data `数据分析与TFL` manifest, the first typed `安全信号与PV协同` manifest, and the first real-DOCX `医学写作` manifest;
- unit tests and browser QC scripts for the contract, backend services, and current frontend prototype.

Current verified foundation: real projects fail closed when a module is not configured and do not borrow another project's package or demo content. This is a routing/privacy foundation only; subsystem commercialization still requires two real studies, independent AI/OCR/VLM success paths, restart recovery, and full browser workflow evidence.

The current prototype is an implementation scaffold for local single-machine verification. It must remain deployable later to a private intranet or personal private network environment.

## UI Naming

User-facing workspace labels must use business names only.

Clinical medical subsystems:

- 证据调研与方案设计
- 入排审核
- 医学监查
- 数据分析与TFL
- 医学写作

## 范围 (R3-B / worker_02)

worker_02 拥有 listing 结构画像、语义 mapping、稳定 record identity 与规范化语义合同：

| 模块 | 职责 |
|---|---|
| `src/mm_r3/normalization.py` | 日期/部分日期/单位/编码/重复/缺失值规范化；保留原始值、规范化值与显式不确定性 |
| `src/mm_r3/identity.py` | 稳定 record identity（行/列/显示变化稳定）、identity algorithm、歧义暴露、重复检测 |
| `src/mm_r3/listing.py` | workbook/table/field 结构画像；field role 推断；内容寻址 |
| `src/mm_r3/mapping.py` | 语义 mapping 候选/置信度/依赖/显式决策（accepted/rejected/needs_confirmation/not_evaluable）|
| `tests/test_r3_b_*.py` | normalization/identity/listing/mapping 确定性测试（173 tests）|

## 关键合同 (R3-B)

1. **结构画像内容寻址**。`WorkbookProfile`/`TableProfile`/`FieldProfile` 不可变；内容哈希排除随机代理 id，相同结构产生相同哈希；绑定真实 source revision id。
2. **稳定 record identity**。`IdentityAlgorithm` 冻结；digest 在行顺序、列顺序、显示格式（空白/大小写）变化下稳定；真正内容/键变化产生新身份或歧义，不误合并。
3. **歧义暴露不静默**。全部 key 缺失或部分 key 缺失（默认）产生 `AmbiguousIdentity`（`none` kind），阻断 baseline eligibility；重复键暴露但不合并。
4. **mapping 候选可解释**。每个候选携带分数、证据（name/role/value/domain/position match）和显式决策；低置信度永不静默接受。
5. **identifier 永需确认**。identifier role 的 mapping 即使高分也标记 `needs_confirmation`；`requires_confirmation` target 同理。
6. **显式决策四态**。`accepted`/`rejected`/`needs_confirmation`/`not_evaluable`；accepted 必须命名 chosen candidate；非 accepted 阻断 baseline。
7. **规范化保留原始值**。`NormalizedValue` 保留 raw_value + normalized + quality + uncertainty；exact quality 不带不确定性；partial/ambiguous/imputed 必须携带不确定性说明。
8. **公共规则无项目硬编码**。三种异构 listing 形态（wide AE / long labs / multi-table workbook）测试不含项目绝对路径或项目名。
- 安全信号与PV协同

Workbench-level surfaces:

- 项目总看板
- 审批中心

Non-medical lifecycle steps are intentionally out of scope. Do not build standalone subsystems for project startup/activation, EDC or data-collection-system construction, site operations, visit execution, or recruitment operations unless the user later changes the product boundary.

## 范围 (R3-C / worker_03)

worker_03 拥有 snapshot diff/临床影响传播与自然语言规则生命周期合同：

| 模块 | 职责 |
|---|---|
| `src/mm_r3/snapshot_diff.py` | 全量快照 diff（added/removed/disappeared/unchanged/modified）、scope coverage、临床影响传播 |
| `src/mm_r3/rules.py` | 自然语言规则结构化草稿、模拟、版本化激活、evaluation scope |
| `tests/test_r3_c_*.py` | snapshot diff/impact propagation/rule lifecycle 确定性测试与隐藏反过拟合挑战 |

## 关键合同 (R3-C)

1. **输入始终是全量快照**。`SnapshotFacts` 不可变、内容寻址，绑定 source revision 与冻结 identity algorithm；diff 在两个全量快照之间计算。
2. **消失记录不静默解除**。基线有而当前无的记录默认为 `disappeared`（coverage 未确认），不得直接解除风险；仅在显式 `ScopeCoverageNote(covered=True)` 时才记为 `removed`。
3. **diff 确定性可复现**。`SnapshotDiff` 按 `record_id` 排序；摘要计数由变更记录派生，不接受外部声明；相同两个快照产生相同 diff。
4. **影响传播显式分类**。`ImpactPropagation` 将 added→`new_finding`、modified→`data_correction`、disappeared→`potential_loss`、removed→`confirmed_removal`；`potential_loss` 永远 `requires_review`。
5. **规则只能先草稿后模拟**。`RuleDraft` 携带自然语言原文 + 结构化条件 + 来源绑定；`simulate_rule` 在激活前强制执行模拟。
6. **激活需显式版本与 scope**。`RuleActivation` 强制 `version` + `EvaluationScope`；模拟 content_hash 必须匹配草稿；machine 激活不能 `user_confirmed`。
7. **三类 evaluation scope**。`full_history`/`current_snapshot`/`future_only`；scope 在激活时冻结，后续变更需新版本化激活。
8. **公共规则无项目硬编码**。隐藏反过拟合挑战使用重命名/重排的异构结构，证明 diff 与规则评估不依赖项目名或路径。

Do not show lifecycle numbers in navigation, page titles, breadcrumbs, buttons, approval lists, exports, or help text. Internal module keys may remain stable for traceability, but all visible labels must be business names.

## Frontend Experience Priority

All subsystem frontends are desktop-first production workspaces. Do not remove or simplify desktop functions, clinical context, dense tables, timelines, rich editors, review rails, or approval controls merely to improve mobile layout.

Desktop browser QC is blocking. Mobile browser checks are smoke/degradation checks only: the mobile surface should not catastrophically overlap or become completely inaccessible where feasible, but mobile limitations must not drive feature cuts unless explicitly approved by the user.

## Commands

```bash
python3 scripts/generate_demo_data.py
python3 -m unittest discover -s tests
python3 -m uvicorn services.api.app.main:app --reload --port 8910
```

For a read-only ego-browser smoke check against an already isolated local UI:

```bash
cd frontend
APP_URL=http://127.0.0.1:5174/ npm run qc:ego:readonly
```

The check opens an agent-owned ego task space, validates the rendered app root, DOM snapshot and screenshot, then closes the task space. It does not issue application mutations.

## API

- `GET /api/health`
- `GET /api/projects`
- `GET /api/projects/{project_id}/dashboard`
- `GET /api/projects/{project_id}/risks`
- `GET /api/projects/{project_id}/subjects/{subject_id}/monitoring`
- `GET /api/projects/{project_id}/evidence-design/manifest`
- `GET /api/projects/{project_id}/tfl/manifest`
- `GET /api/projects/{project_id}/safety-pv/manifest`
- `GET /api/projects/{project_id}/medical-writing/manifest`
- `GET /api/projects/{project_id}/protocol`
- `GET /api/projects/{project_id}/revision-threads`
- `POST /api/projects/{project_id}/revision-threads`
- `POST /api/projects/{project_id}/revision-threads/{thread_id}/actions`
- `POST /api/projects/{project_id}/approvals/{approval_id}/actions`
- `GET /api/projects/{project_id}/data-batches`

`GET /api/projects/{project_id}/subjects/{subject_id}/monitoring` returns the internal monitoring module key with the user-facing label `医学监查`, plus:

- `subject`: subject/site/treatment/status context;
- `timeline`: visit, MH, CM, lab, efficacy score, AE, PD, and query events;
- `efficacy_trends`: metric series such as rTNSS and rTOSS;
- `safety_trends`: lab or symptom safety-follow-up series;
- `risk_prompts`: visit/timepoint-level prompts linked to source domains, risk cases, query IDs, PD IDs, and evidence spans.
