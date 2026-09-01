# R7 Slice-07C-1 运行设置、增量差异与特殊关注规则接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_07C1_SYNTHETIC_LIMITED`

## 1. 本切目标与结果

在不启动服务、不运行真实项目的前提下，完成三类医学监查运行的设置数据合同：日常监查、
锁库前监查、核查前监查。日常监查可在“重新全面分析”和“与同项目、同模式、已发布的前次
结果逐项比较”之间选择；输入载体始终是当前完整 data listing，增量只表示规范化业务键后的
新增、修订、未变化、删除/不再出现和无法比较，不把文件差异冒充医学变化。

用户后续可用自然语言添加项目级特殊关注规则。系统先生成中文预览，歧义时拒绝直接确认；
确认后形成不可覆盖的版本，并可通过不暴露内部身份的公开 token 重新解析到本项目的具体版本。
三种模式的工作范围由同一模板生成，工作项数量、顺序、来源和历史规则版本均可确定性复现。

## 2. 实现面

- 领域合同：`poc/medical_monitoring_ai_native_r7/src/mm_r7/run_setup.py`。
- 产品接口：`services/api/app/medical_monitoring_r7_product_router.py` 新增：
  - `GET /run-setup/options`
  - `POST /risk-rules/preview`
  - `POST /risk-rules`
  - `GET /risk-rules`
- 合成夹具与测试：`fixtures_run_setup.py`、`test_run_setup.py`、产品路由测试。
- 证据：`poc/medical_monitoring_ai_native_r7/evidence/r7_slice07c1_run_setup_receipt.json`。

未实现 prepare-and-start、结果发布、前端启动向导或真实模型/项目运行。

## 3. Codex 纠偏与独立会商

执行初稿存在过多兼容样板和无快照项目未初始化变量。Codex要求同会话纠偏，将领域模块从
1,881 行收敛为 1,311 行，并补齐无快照项目回归。独立 DeepSeek V4 Flash max 会商 Round 1
指出公开规则 token 不可反查、预览 token 重启后错误语义不准、幂等指纹包含重试时间戳、
空 snapshot 参数静默回退。Codex以最小改动全部关闭；同一会话 Round 2 返回 `ACCEPT`。

## 4. 决定性证据

- 聚焦领域测试：`9 passed`。
- 完整 R7 POC：`170 passed in 15.67s`。
- 产品路由：`37 passed in 2.20s`。
- `py_compile` 与证据 JSON 校验通过。
- R7 全套包含跨 hash seed 确定性、create-only allowlist、医学写作聚合哈希不变和保护端口停止。
- 执行审计 `ok=true`；独立会商 Round 2 `ACCEPT`。
- 8911/5174 均无监听；未访问五个真实项目。

## 5. 路由与资源事实

执行包声明的 CodeBuddy 主路由因配额返回终态失败；本地 MTPLX 路由因当时可用内存 18.1 GB
低于其声明的 50 GB 准入条件而未调度，这不是模型调用失败。随后使用执行包已声明的
`openai-codex/gpt-5.6-luna:xhigh` 降级路线完成。独立验收使用不同的
`codebuddy-cli/deepseek-v4-flash:max`，没有 fallback。

## 6. 保留边界与下一步

该接受只证明 synthetic/offline 设置、差异、规则版本和产品 API 合同，不证明真实项目解析、
医学判断、模型质量、运行启动、结果发布、前端体验、R7 总体或 R8。

R7 Slice-07C-2 下一步按已冻结 v0.2 合同实现“一键准备并开始”：服务端根据项目、模式、
当前快照、可选已发布基线和已确认规则 token 生成并冻结 work-unit manifest，再原子接入现有
后台进度状态机。开始前必须补测多候选锁库前基线选择，并明确 SQLite `busy_timeout`、连接回收
和多 worker 写入假设；仍只使用 synthetic 数据，保持 8911 与真实项目停止。

