# R7 Slice-03 产品挂载与项目工作区合同

日期：2026-08-28
状态：`FROZEN_R7_SLICE_03_PRODUCT_MOUNT_CONTRACT_V1`

## 1. 目标

把已受限验收的 R7 Slice-02 API/运行入口接入现有医学监查产品服务，但只形成可导入、可用 TestClient 离线验证的产品接缝；本切不启动 8911/5174、不调用模型、不运行真实项目、不新增前端，也不修改医学写作模块。

## 2. 产品路由

- 产品前缀固定为 `/api/projects/{project_id}/modules/medical-monitoring/r7`，不得把隔离 POC 的无项目路径 `/api/medical-monitoring/r7` 直接暴露到产品应用。
- 保留 Slice-02 的四类端点语义：工作区显式引导、ExecutionProfile 追加/读取、Run 绑定/读取。
- 所有 R7 产品错误统一为顶层 `{code, message}`；`message` 使用面向医学监察员的中文，不拼接 Python、SQLite、profile id、selector、字段栈或其他后端详情。适配 router 自己返回响应，禁止在产品 `app` 安装 Slice-02 的全局异常处理器，以免改变其他子系统既有错误合同。
- 本切不增加“执行 Run”、模型健康检查、凭据值编辑、后台任务、进度、恢复/重试端点。

## 3. 项目与工作区绑定

- 路径 `project_id` 是项目层和 Run 层的唯一产品项目身份。
- 产品适配器把工作区解析为 `RUNTIME_DIR / "medical_monitoring_r7" / <canonical_project_id>`；调用方不得提交任意文件路径。
- `project_scope_key` 在产品 DTO 中不由客户端提供：适配器先在已解析的项目工作区中检查项目层；存在时固定使用 canonical project id，不存在时传空值跳过。
- `run_override_scope_key` 也不由客户端提供：存在与 `run_id` 同名的 Run 层时自动应用，不存在时跳过。不得通过一次 Run 请求引用其他 Run 的配置层。
- `CreateRunRequest.project_id` 不再由客户端重复提交；由路径 canonical project id 注入，消除路径/正文身份分叉。

## 4. 生命周期与挂载

- `main.py` 只注册一个产品 router factory；不得在模块导入或 router 构造时创建目录、SQLite、schema、默认配置或业务修订。
- 每个请求在当前执行线程创建 `MonitoringRunEntry(project_workspace_dir)`，并在 `finally` 关闭两个 SQLite 连接。
- 只有显式 `POST .../workspace/bootstrap` 可首次创建工作区目录、数据库和内置 MTPLX medium 全局默认修订；重复调用返回原 revision 1。
- R7 router 内局部处理领域异常、HTTP 异常和请求校验，不注册 app-wide handler；R7 路径不得出现 FastAPI 默认 `{detail: ...}`，非 R7 路径响应必须保持原样。

## 5. Harness 语义

- 默认仍为 `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`。
- capability/project/run 层可用 `user_config_name="deepseek/DeepSeek V4 flash"` 显式选择注册的 DeepSeek V4 Flash max；不得自动 fallback。
- 本切仅冻结配置和 Run 身份，不实际调用 harness/model。

## 6. 既有边界

- 复用现有医学监查 server-principal/project canonicalization seam；配置写入使用既有 `ADMINISTER_RUNTIME`，读取使用 `READ_AI_RUN`。不新增、不重构、不专项测试安全功能，也不得绕过现有宿主边界。
- 禁止修改 `medical_writing*`、writing-reference、共享医写数据库、前端和 R1-R6。
- `WORKBENCH_R5_S7_FIXTURE_MODE` 只属于既有 R5 synthetic fixture，不得复用于 R7。

## 7. 最小实现面

- 新增一个产品适配 router 模块及其聚焦测试。产品模块通过工作台根目录下的 namespace 路径 `poc.medical_monitoring_ai_native_r7.src.mm_r7` 复用冻结核心；不得改写 `sys.path`、复制核心或建立第二套实现。后续正式打包时再迁移为安装包。
- `main.py` 只增加 import、router 构造和 include；若无法在不触发其他运行态写入的情况下测试，则先以独立 host-app contract test 证明，不导入完整 `main.py`。
- R7 POC 通过已接受公共 API 被调用，不复制 profile/run-binding 逻辑。

## 8. 退出门

- 构造/导入零 R7 业务写入；bootstrap 才创建项目工作区。
- 路径项目身份、Run 项目身份、project scope 三者一致且无客户端双写。
- MTPLX 默认、名称型 DeepSeek 显式选择、三模式、full/incremental、replay/conflict、中文错误、连接关闭有产品路由测试。
- 产品 router 前缀不冲突；无 `/api/medical-monitoring/r7` 产品暴露。
- 非法/未配置项目必须在任何 R7 目录或 SQLite 创建前失败；两个项目的 Run 不可互读。
- 非 R7 dummy route 的既有 `detail` 错误形状在挂载前后完全不变。
- R7 全套、产品聚焦/相邻监查测试、R6 全套通过；8911/5174 停止；医学写作聚合不变。
- 独立会商与 Codex 验收后才可称为 Slice-03 受限接受；不得称 R7 完成。
