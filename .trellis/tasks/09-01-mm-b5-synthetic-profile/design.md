# B5 技术设计：产品原生 `--synthetic` profile 与外置 fixture 合同

日期：2026-09-02。依据：实施计划 v2.0 阶段 B 第 5/8 项、`prd.md`、`.trellis/spec/medical-monitoring-engineering.md`。设计目标是最小合同：只外置**数据**，不移植任何平行验收机制。

## 1. 现状盘点（检查过的适配器与缝）

当前产品里合成数据有且只有三个 Python 字面量来源，外加一个启动缝：

| 来源 | 位置 | 内容 | 消费方 |
|---|---|---|---|
| R5 S7 权威包 fixture | `packages/medical_monitoring/projections/product_fixtures.py`（422 行） | `_build_base_records`（3 受试者/6 访视/12 事件/3 风险/1 历史/4 来源/3 中心）＋`_build_flow_records`（7 阶段/3 路径）＋`_build_density_records`（程序化生成）＋包级身份字段 | `SyntheticR5AuthorityProvider` → `R5ProductAdapter` → R5 三条只读路由（驾驶舱/中心图谱、Subject Workspace/Journey、来源下钻） |
| R7 setup fixture | `packages/medical_monitoring/api/r7_product/synthetic_setup.py`（123 行，注释标记 B5 移除） | `DataSnapshot`×2 ＋ `PublishedBaseline`×4 的确定性输入 | `project_operations.setup_catalog` → **所有项目**的 R7 setup/launch 目录（现状即如此，非合成模式专属） |
| 平行应用内嵌数据 | `deploy/medical_monitoring_local/synthetic_ego.py`（147KB）等 | G6 验收机件：fixture/binding/adapter/notification-matrix/user-task-evidence/bundle 的 schema＋校验＋replay，数据体 `_build_fixture_body` | 仅 G6 平行前端；随平行应用整体删除，数据不移植（计划 §10 明确不重建平行栈） |
| 启动缝 | `services/api/app/main.py:3374-3411` | 环境变量 `WORKBENCH_R5_S7_FIXTURE_MODE` → 合成 principal（`s7-browser-medical-monitor`，project_scope `["s7-synthetic-project-001"]`）＋ `synthetic_fixture_mode=True` 注入 R5 路由工厂 | R5 路由；`R5ProductAdapter(None, synthetic_fixture_mode=True)` 时回退到内置 fixture provider |

关键既有事实：

- 常量已定：`SYNTHETIC_PROJECT_REF="s7-synthetic-project-001"`、`SYNTHETIC_RUN_REF="s7-run-current-001"`、`SYNTHETIC_CUTOFF_REF="2026-03-31"`、`SYNTHETIC_FIXTURE_MODE="synthetic_offline"`；包合法性要求 `project_ref` 以 `s7-synthetic-` 开头（`product_types.py:623`）。
- `DataSnapshot.from_mapping` / `PublishedBaseline.from_mapping`（`runtime/run_setup.py:183/265`）已带校验，R7 侧加载器直接复用。
- 产品启动方式：`scripts/start_stable_backend.zsh` → `python3 -m uvicorn services.api.app.main:app`（8911）；前端 `scripts/start_stable_frontend.zsh` → Vite 5174 代理 8911。uvicorn 不透传自定义 argv，`--synthetic` 需要程序化启动入口。
- R7 运行进度页走产品自身链路：`POST /workspace/bootstrap` → `POST /runs`（绑定）→ `POST /runs/{run_id}/execution/prepare`（确定性工作单元）→ `GET /runs/{run_id}/progress`（`runtime/runtime_progress.py`，`EXECUTION_KIND_DETERMINISTIC` 不调模型）。
- `synthetic_ego.py` 的机器件（binding/notification-matrix/replay/digest pinning）是被废止的 G 门产物，**合同里没有任何对应物**。

## 2. fixture 数据文件合同

### 2.1 目录与解析

```
tests/fixtures/medical_monitoring/
  r5_authority_fixture.json    # R5 S7 权威包源数据（§2.3）
  r7_setup_fixture.json        # R7 快照与已发布基线（§2.4）
  synthetic_run_fixture.json   # 冒烟用确定性运行种子（§2.5）
```

- 默认目录从包位置解析（`packages/medical_monitoring/.../__file__` 向上到仓库根再拼 `tests/fixtures/medical_monitoring`），**不依赖 CWD**；环境变量 `MM_SYNTHETIC_FIXTURES_DIR` 可覆盖（为将来打包形态预留，本阶段唯一合法用途是测试）。
- 请求合成 profile 而目录或任一文件缺失、非法 → 启动失败并给出中文错误，禁止静默空数据或回退真实数据。

### 2.2 JSON 编写规则（适用于三个文件）

1. 键名与既有 dataclass 字段同名（snake_case）；元组字段写 JSON 数组；可选日期写 `"YYYY-MM-DD"` 或 `null`。
2. **只存源数据，不存派生值**：所有哈希/digest/token（`source_revision_content_hash`、`visibility_decision_hash`、`snapshot_token` 等）仍由构建器按现状算法从内容计算。外置后任何公开 token/digest 都不得变化——由既有测试不动 greens 证明。
3. **随请求变化的身份字段不入 JSON**：`snapshot_ref`/`cutoff_ref`/project 拼接引用由构建器在加载后注入（R5 按 `build_synthetic_r5_authority_packet` 的入参；R7 用 `"{project_id}"` 模板占位）。JSON 里的跨记录引用（`subject_ref`、`event_ref`、`source_locator_refs`、`visit_ref`、`stage_ref`…）逐字存储。
4. 文件顶层带 `"fixture_schema"` 与 `"fixture_version"`（新常量 `mm-medical-monitoring-synthetic-fixture-v1` / `"1"`），加载器按白名单键校验：未知键、缺键、类型错一律 `FixtureDataError`，fail-closed。
5. 语义类型校验仍归既有构造器（`R5SourceRecord(...)`、`DataSnapshot.from_mapping` 等）；加载器只做结构校验，不重复实现领域规则。

### 2.3 `r5_authority_fixture.json`

按记录类型分键：`sources`、`sites`、`subjects`、`events`、`visits`、`risks`、`histories`、`flow_stages`、`flow_paths`，内容 = 现在 `_build_base_records`＋`_build_flow_records` 的字面量逐条转换：

- `sources`：存 `locator_ref`、`revision`、`excerpt`、`record_ref`、`canonical_location`（现在 `_source()` 里 `location_labels` 字典的 5 条特例全部展开为显式字段）；`source_file_ref`、`lineage`、content_hash 由构建器按现公式派生。
- `risks`：存 `_risk()` 的显式入参；`risk_anchor_ref` 派生规则、`prior_snapshot_ref` 条件规则保留在构建器。
- 变体逻辑留在代码：snapshot 白名单（current/comparable/not_comparable/date-edge/aemh/density）、aemh 过滤、`not_comparable` 改写、flow 挂载条件、density 分支。JSON 只有一份基线记录。
- **密度 fixture 保持程序化生成，不外置**：它是生成器（约 60 行代码、1400 条派生记录），不是数据字面量；外置只会把仓库塞满低价值 JSON，且注释明确其"legacy-shape packet 保持 not_provided 状态可达"的行为语义与代码绑定。

### 2.4 `r7_setup_fixture.json`

`{"snapshots": [...], "baselines": [...]}`，逐字段对应 `synthetic_setup.py` 现值；项目拼接引用写模板（如 `"snapshot_ref": "{project_id}:synthetic:daily-prior"`），构建器 `.format(project_id=...)` 后经 `DataSnapshot.from_mapping`/`PublishedBaseline.from_mapping` 构造。合成字符串（rows、cutoff、key_fields、scope_description 等）逐字保留，保证 opaque token 不变。

### 2.5 `synthetic_run_fixture.json`

进度页冒烟种子：`{"run_id", "mode", "data_cutoff", "source_revision_id", "work_units": [...]}`，`work_units` 形状与 R7 路由既有确定性清单一致（`work_unit_id/stage/label/scope/target_ref/ordinal/mandatory/depends_on`）。`--synthetic` 启动时经**产品自身的** setup/launch 路径幂等种子（工作区无该运行才执行 bootstrap→绑定→prepare），进度页由此渲染真实产品运行态；执行仍由用户在 UI 触发（确定性执行，不调模型）。不新建任何运行器/观察器。

## 3. 加载器与 provider 合同

- 新模块 `packages/medical_monitoring/projections/fixture_data.py`：`load_r5_fixture()`、`load_r7_setup_fixture()`、`load_synthetic_run_fixture()`，`lru_cache`，统一 `FixtureDataError(ValueError)`。R7 侧如需避免 projections→api 反向依赖，允许放 `runtime/fixture_data.py`，二选一以 import 方向干净者为准。
- R5 对外 API **签名不变**：`SyntheticR5AuthorityProvider`、`build_synthetic_r5_authority_provider`、`build_synthetic_r5_authority_packet(project_ref, run_ref, snapshot_ref, cutoff_ref)`。数据源换成 fixture_data，变体/校验/派生逻辑不动。现有 37 个 R5 行为测试（adapter 12、subject-flow 17、router 8）与 r7 product router 的 4 处引用必须原样通过——这是"外置不丢行为"的验收证据。
- `synthetic_setup_inputs(canonical_project_id)` 签名不变（R7 路由工厂与测试引用 `_synthetic_setup_inputs`）；函数体改为从 JSON 构造。文件顶部"B5 移除"注释改为指向 fixture 合同。
- `product_fixtures.py` 收敛为 provider 类＋包组装，目标 <250 行、无 >200 行数据字面量；`synthetic_setup.py` 同理收敛。

## 4. `--synthetic` 启动 profile

- 新入口 `services/api/app/__main__.py`：argparse 仅一个开关 `--synthetic`；随后与 `start_stable_backend.zsh` 等价地 `uvicorn.run(app, host=127.0.0.1, port=8911)`。用法：`python3 -m services.api.app --synthetic`。
- `main.py` 把环境变量读取段替换为显式 `enable_synthetic_profile()`（设置合成 principal 与 `synthetic_fixture_mode`，即现有 3374-3402 行逻辑收拢为函数）；`__main__` 在 `uvicorn.run` 前调用。**单一启动路径**：移除 `WORKBENCH_R5_S7_FIXTURE_MODE` 环境变量缝，`tests/test_medical_monitoring_r5_product_allowlist.py:59-65` 的结构断言同步改为断言新缝（include 唯一＋profile 标志）。
- 启动即打印一行：后端地址、前端地址（Vite 5174）、合成项目引用，便于冒烟导航。前端零改动。
- 种子逻辑（§2.5）放 `--synthetic` 分支内，非合成启动零新增 I/O。

## 5. 删除与不移植清单（worker_03 交接）

- 删除 `deploy/medical_monitoring_local` 整树（git 已留档）。
- **前端测试夹具不动**：`frontend/src/features/medical-monitoring/medicalMonitoringProductFixtures.mjs`（522 行）及其 `.test.mjs` 消费方是前端单元测试的本地 mock 包（身份为 `synthetic-project-r5-s7` 等，与后端 S7 身份无关，纯 node:assert 脚本）。它们不属于本合同，不在 B5 统一或后端化。
- 依赖该树的测试随删：`tests/test_medical_monitoring_g6_entry_lifecycle.py`、`test_medical_monitoring_g6_synthetic_bundle_endpoint.py`、`test_medical_monitoring_local_distribution.py`、`test_medical_monitoring_r8_gate4_distribution.py`、`test_medical_monitoring_r8_gate6_synthetic_ego.py`（已 grep 确认为 import deploy/synthetic_ego/g6_* 的全集）。
- 不移植：binding/notification-matrix/user-task-evidence/bundle/observer/digest-release 机件；不新增平行 runtime。
- 医学写作（`services/api/app` 其余路由与 assets）与旧链 `monitoring_*` 冻结不动；`main.py` 仅动医学监查合成缝。

## 6. 风险与对策

| 风险 | 对策 |
|---|---|
| 引用串漂移导致 opaque token 变化 | 身份字段全部派生不改公式；既有公开视图测试兜底 |
| 产品代码引用 `tests/` 目录的脆弱性 | 目录解析不依赖 CWD＋env 覆盖＋缺失即 fail-closed 报错 |
| 种子逻辑污染非合成启动 | 种子只在 `--synthetic` 分支执行；幂等（已有运行即跳过） |
| fixture JSON 写错静默通过 | 白名单键校验＋构造器复用＋加载器校验测试 |

## 7. 新增测试（worker_02）

1. 加载器：合法加载往返（fixture → packet 关键不变量：项目/运行/快照身份、记录计数、flow 覆盖）；未知键与缺文件各自 fail-closed。
2. 环境变量 `MM_SYNTHETIC_FIXTURES_DIR` 覆盖生效。
3. `--synthetic` 种子幂等：重复启动不重复建运行。
4. 更新 `test_medical_monitoring_r5_product_allowlist.py` 至新启动缝。
