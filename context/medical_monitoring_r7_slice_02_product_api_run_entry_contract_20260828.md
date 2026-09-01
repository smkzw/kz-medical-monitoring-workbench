# R7 Slice-02 产品 API / 运行入口合同

状态：`FROZEN_FOR_IMPLEMENTATION`

## 1. 目标与边界

本纵切在已受限接受的 R7 Slice-01 持久化与 Run 绑定之上，冻结一个可由产品层调用的最小 API/运行入口。它只证明：用户配置可写入版本化 ExecutionProfile，产品启动流程可显式播种内置默认配置，一次 Monitoring Run 可按四层优先级冻结 effective profile 并不可变绑定。

本纵切仍是隔离实现，不挂载工作台 `main.py`，不启动 8911/5174，不调用真实模型，不运行真实项目，不修改前端或医学写作子系统。通过本纵切后，下一纵切才把同一合同迁入并挂载产品服务。

## 2. 不变量

1. `ProfileStore` 构造器保持无业务写入；内置默认配置仅由显式 workspace bootstrap 调用播种。
2. bootstrap 幂等：首次创建一个 `global_default/*` 修订；重复调用返回同一修订，不新增版本。
3. 内置默认为 `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`；DeepSeek `deepseek/DeepSeek V4 flash:max` 仍通过 capability/project/run 层显式选择，不作为自动 fallback。
4. effective profile 严格按 `global_default < capability_agent < project < run_override` 合并；缺少全局默认、引用不存在、字段非法、凭据值或隐式 fallback 一律失败关闭。
5. Run 身份至少冻结 `run_id × project_id × mode × data_cutoff/source_revision_id × execution_basis × prior_accepted_snapshot_ref × effective ExecutionProfile identity`。
6. `incremental` 必须引用先前已接受快照；`full` 不得携带该引用。三种 mode 仅为 `daily | pre_lock | post_lock_pre_cfdi`。
7. 同一 `run_id` 同输入重放返回同一 binding；任何 profile/data 身份变化均冲突，不覆盖旧记录。
8. 公共响应不得出现 credential value、环境变量值、命令原始输出、医学事实/风险/Profile/Timeline/Query/报告对象或临时日志标签。

## 3. 最小接口

隔离 router 前缀：`/api/medical-monitoring/r7`。

- `POST /workspace/bootstrap`：显式播种并返回全局默认公共投影及 `replayed`。
- `POST /execution-profiles/{layer_kind}/{scope_key}`：追加一版允许字段；只返回公共投影。
- `GET /execution-profiles/{layer_kind}/{scope_key}`：读取最新公共投影；不存在返回稳定错误。
- `POST /runs`：接收 Run 身份与 scope 选择，加载四层、冻结 effective profile、写入不可变 binding，返回公共投影及 `replayed`。
- `GET /runs/{run_id}`：读取 binding 公共投影。

错误响应使用稳定 `code + 中文 message`；内部字段名可以进入 JSON 合同，但用户界面不得直接显示这些后端术语。本纵切不增加编辑凭据值、模型调用、后台任务、继续/恢复/取消或 Run 执行端点。

## 4. 允许路径与分工

- worker_01：`poc/medical_monitoring_ai_native_r7/src/mm_r7/run_entry.py` 及必要的 `__init__.py` 导出。
- worker_02：`poc/medical_monitoring_ai_native_r7/src/mm_r7/api.py`。
- worker_03：`poc/medical_monitoring_ai_native_r7/tests/test_run_entry.py`、`tests/test_api.py`、`evidence/r7_product_api_run_entry_receipt.json`、`README.md`。
- Codex：合同、跨文件整合、缺陷修订、回归、会商、状态记录和最终接受。

不得修改 R1-R6、工作台产品服务/前端、运行库、真实项目、医学写作、现有 Slice-01 receipt 或已冻结源文件；若实现确需改变 Slice-01 文件，必须先由 Codex记录为显式新修订并重跑相邻门禁。

## 5. 完成门

- bootstrap 首次/重放、默认 MTPLX、显式 DeepSeek、四层优先级、三模式、full/incremental、Run 重放/冲突、关闭重开、非法/秘密字段、公共响应去敏全部有确定性测试；
- R7 全量测试与相邻 R6 全量测试通过；跨 `PYTHONHASHSEED` 与 `-O/-OO` 的关键向量一致；
- 8911/5174 无监听，医学写作聚合未变；
- execution audit、独立 conference review、Codex 源码与证据审阅均通过；
- 接受结论必须明确为 Slice-02 受限接受，不得声称产品已挂载、模型已实际调用、三模式已贯通或 R7 完成。
