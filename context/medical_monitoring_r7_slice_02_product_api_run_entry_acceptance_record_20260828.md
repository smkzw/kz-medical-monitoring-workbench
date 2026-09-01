# R7 Slice-02 产品 API / 运行入口受限验收记录

日期：2026-08-28

## 结论

R7 Slice-02 以“隔离、离线、受限范围”通过 Codex 验收。

本结论只覆盖 `poc/medical_monitoring_ai_native_r7` 内的产品 API / 运行入口接缝：显式工作区引导、四层执行配置、默认 MTPLX medium、显式 DeepSeek V4 Flash max、全量/增量约束、运行重放/冲突以及中文错误响应。它不代表产品 `main.py` 已挂载、真实模型已调用、真实项目已运行、三种监查模式端到端完成或 R7 整体完成。

## 会商发现与纠偏

- 独立审阅复现：只填写用户可见的 DeepSeek 配置名时，写入成功但冻结失败。现已由已注册别名解析出 `profile_id`，并以 API 正向回归固定。
- 公开错误不再拼接适配器英文详情，只保留稳定错误码和中文消息。
- 新增 `create_isolated_app_from_run_entry(workspace_dir)`，作为包含中文错误处理器的完整隔离应用入口。低层 router 若由宿主挂载，宿主必须同时安装异常处理器。
- 构造参数明确为工作区目录；SQLite 文件名被拒绝，避免下一纵切误接。
- 工作区首次引导固定 revision 1；后续全局默认覆盖不会破坏引导重放。

## 决定性证据

- Slice-02 聚焦测试：37 passed。
- R7 全套：93 passed；其中 `PYTHONHASHSEED × -O/-OO` 九宫格全部通过。
- 相邻 R6：763 passed。
- 新增/修改文件 Ruff：通过；R7 `compileall`：通过。
- Slice-01 冻结源哈希未变：`profile_store.py d5a6c4fe...f298`；`run_binding.py 84d16f28...ccc2`。
- 8911、5174 均无监听；未启动服务、未调用真实模型、未运行真实项目、未修改产品服务/前端或医学写作子系统。

## 已知边界

- `project_scope_key` 当前是显式配置作用域，不自动强制等于 `project_id`；产品挂载纵切需要决定由 API 自动绑定还是保留显式共享作用域。
- `create_router_from_run_entry` 只是低层 wiring；产品挂载不得绕过 `install_exception_handlers`。
- SQLite 并发策略、后台运行、进度条、真实 harness 调用和前端入口均属于后续纵切。

## 下一安全动作

R7 下一纵切先冻结产品挂载/迁移合同：只把已经受限验收的 API 接入医学监查产品路径，明确工作区目录解析、项目作用域绑定、每请求连接生命周期和中文错误处理；继续禁止启动 8911/5174、真实模型与真实项目，直至独立离线回归通过。
