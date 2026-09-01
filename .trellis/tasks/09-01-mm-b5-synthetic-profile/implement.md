# B5 实施计划（worker_02 执行；worker_03 删除与验证）

前置阅读：`design.md`（合同以它为准）、`.trellis/spec/medical-monitoring-engineering.md`。
每步先跑该步验证再进入下一步；任一步验证不过不得推进。本计划不含 worker_03 的删除动作（见 §B）。

## A. worker_02：fixture 外置 ＋ `--synthetic` profile

### A1. 落数据文件（不接加载器，纯新增）

- 新建 `tests/fixtures/medical_monitoring/`，按 `design.md` §2 写三个 JSON：
  - `r5_authority_fixture.json`：把 `packages/medical_monitoring/projections/product_fixtures.py` 的 `_build_base_records`＋`_build_flow_records` 字面量逐条转换（§2.2 规则：只存源数据；`snapshot_ref`/cutoff 等随请求身份不入 JSON；`location_labels` 特例展开为 `record_ref`/`canonical_location` 显式字段）。
  - `r7_setup_fixture.json`：把 `packages/medical_monitoring/api/r7_product/synthetic_setup.py` 现值转入，项目拼接引用用 `{project_id}` 模板。
  - `synthetic_run_fixture.json`：运行种子（run_id=`s7-run-current-001`、mode=daily、cutoff/revision 与 r7 setup 的 current 快照一致、work_units 两条，样式同 `tests/test_medical_monitoring_r7_product_router.py:1193` 的 `_slice04_units`，中文 stage/label）。
- 验证：`python3 -m json.tool` 三个文件全部通过；与源字面量逐条人工对照一次（条数：sources 4、sites 3、subjects 3、events 12、visits 6、risks 3、histories 1、flow_stages 7、flow_paths 3、snapshots 2、baselines 4、work_units 2）。

### A2. 加载器

- 新建 `packages/medical_monitoring/projections/fixture_data.py`（若 import 方向不干净则放 `runtime/fixture_data.py`）：`load_r5_fixture`/`load_r7_setup_fixture`/`load_synthetic_run_fixture`，`lru_cache`，`FixtureDataError`；目录解析（包位置向上推导仓库根＋`MM_SYNTHETIC_FIXTURES_DIR` 覆盖）与白名单键校验按 `design.md` §2.1/§2.2。
- 验证：新测试文件 `tests/medical_monitoring/test_fixture_data.py`（跟随 B4 已建目录）覆盖：合法加载、未知键拒绝、缺文件拒绝、env 覆盖生效。`python3 -m pytest tests/medical_monitoring/test_fixture_data.py -q` 绿。

### A3. R5 侧切换

- `product_fixtures.py`：`build_synthetic_r5_authority_packet` 数据源改为 `load_r5_fixture()`；`_build_base_records`/`_build_flow_records` 删除；保留 `_source`/`_risk` 派生逻辑（改为从 JSON 字段取 `record_ref`/`canonical_location`）、变体选择/过滤/改写、包级身份派生、三类 `*_NOT_IN_SYNTHETIC_PACKET` 错误。对外签名不动（`design.md` §3）。
- 验证：`python3 -m pytest tests/test_medical_monitoring_r5_product_adapter.py tests/test_medical_monitoring_r5_subject_flow.py tests/test_medical_monitoring_r5_product_router.py -q` 全绿（37 个，不允许改断言）。确认 `product_fixtures.py` <250 行且无 >200 行字面量。

### A4. R7 侧切换

- `synthetic_setup.py`：函数体改为 JSON→`from_mapping` 构造（模板 `.format(project_id=...)`）；签名与返回类型不变；更新顶部注释。
- 验证：`python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q` 全绿（不改断言；opaque token 不变的直接证据）。

### A5. `--synthetic` 启动

- 新建 `services/api/app/__main__.py`：仅 `--synthetic` 开关；调用 `main.enable_synthetic_profile()`（把 `main.py:3374-3402` 环境变量段收拢为模块函数，逻辑不变）；随后 `uvicorn.run(app, host="127.0.0.1", port=8911)`。`services/*` 全部是隐式命名空间包（无 `__init__.py`），`python3 -m services.api.app` 依赖仓库根在 `sys.path`（与 `start_stable_backend.zsh` 的 `cd "$ROOT"` 一致），不需要补 `__init__.py`。
- `--synthetic` 分支内做 §2.5 种子（幂等：工作区已有 `s7-run-current-001` 绑定即跳过），复用产品 runtime/setup API，不写平行逻辑。
- 同步更新 `tests/test_medical_monitoring_r5_product_allowlist.py:59-65` 结构断言到新缝（include 唯一＋`enable_synthetic_profile`）；移除 `WORKBENCH_R5_S7_FIXTURE_MODE`。
- 验证：`python3 -m pytest tests/test_medical_monitoring_r5_product_allowlist.py tests/medical_monitoring/test_fixture_data.py -q` 绿；新增种子幂等测试绿。

### A6. 冒烟自检（非验收）

- `python3 -m services.api.app --synthetic` 启动成功并打印地址行；`curl` 冒烟四链路（等价截图页数据源）：R5 overview（`/api/projects/s7-synthetic-project-001/modules/medical-monitoring/r5/overview?run_ref=...&snapshot_ref=...&cutoff_ref=...`，带 200/409 断言即可）、R7 setup 目录、运行绑定＋prepare、progress 200。
- 验证：四条 curl 全部符合预期状态码；记录请求样例进报告。停止进程，清理本次生成的工作区运行数据（如落在仓库 `runtime/`，报告路径）。浏览器截图与视觉验收**不在本工单**，Codex 另行安排。

### A7. 收尾

- 跑一次聚焦全量：`python3 -m pytest tests/test_medical_monitoring_r5_product_adapter.py tests/test_medical_monitoring_r5_product_router.py tests/test_medical_monitoring_r5_subject_flow.py tests/test_medical_monitoring_r7_product_router.py tests/test_medical_monitoring_r5_product_allowlist.py tests/medical_monitoring/ -q`。
- commit（一次语义一提交：fixtures、加载器、R5 切换、R7 切换、启动缝可分开）；commit message 记录验证命令与结果。

## B. worker_03：删除与回归（等 A 全绿后）

1. `git rm -r deploy/medical_monitoring_local`。
2. 删除依赖该树的测试（以删除前完整 `DEPLOY_DIR`/模块名扫描为准；最终确认 10 个，详见 `design.md` §5）。
3. 回归：A7 聚焦集＋`python3 -m pytest tests/ -q -k medical_monitoring`（允许长跑）；确认无残留 import（`rg -n "deploy.medical_monitoring_local|synthetic_ego|g6_runtime|g6_manifests|g6_observer|actual_app" packages/ services/ tests/ frontend/src` 仅允许命中历史归档目录）。
4. 前端不回归：`cd frontend && npm run build`；医学监查前端单元测试是独立 node 脚本（`node:assert` 计数式，逐文件直接运行），逐个执行 `node src/features/medical-monitoring/*.test.mjs`（或按 git 改动范围挑受影响文件），确认各文件末尾 `N checks passed` 无断言失败。
5. 医学写作非回归：跑 `services/api/app` 相关既有医学写作路由测试子集（以 B4 验证用过的集合为准）。

## 边界提醒

- 不动医学写作路由/assets、旧链 `monitoring_*`、五个真实项目目录。
- 不刷新任何 digest、不补 manifest、不新增平行 runtime/observer。
- fixture JSON 放 `tests/fixtures/medical_monitoring/`，不新增 `context/`、`reviews/` 过程记录。
- 遇产品 router 直接 import poc 树的路径（如 `tests/test_medical_monitoring_r7_product_router.py:46` 仍 import `poc...launch_registry`），这是 B6 迁移遗留，不在本任务改；如阻塞验证，报告并等 Codex 决定。
