# R7 Slice-06 Harness Runtime Implementation 阶段记录

日期：2026-08-28  
任务：`mm_r7_slice_06_harness_runtime_implementation_20260828`  
角色：`worker_03`  
状态：`synthetic_offline_conference_accepted_pending_matrix14_live_smoke`

## 1. 边界与来源

本阶段只执行冻结合同中 worker_03 的工作项：补齐 R7 fake catalog/transport
故障注入、并发与租约回归、R6 receipt 到 R1 状态映射回归、公开响应泄漏扫描、
项目级产品路由回归，并更新 README、receipt 和本阶段记录。

使用的权威来源：

- `context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_20260828.md`
  （SHA-256：`3c879889e30541b2556bc8c2643758029b52e7cc9876f9b27d7e0e5b73bbbc21`）；
- `context/medical_monitoring_r7_slice_05_review_and_slice06_plan_20260828.md`；
- 当前 R7 `harness_runtime.py`、`background_recovery.py`、`runtime_progress.py`、
  产品 router 与既有 R7 测试；
- R1 controller/runtime/store 与冻结 R6 `agent_harness.py`，仅作只读接口依据。

硬边界保持：未修改 R1/R6、前端或医学写作；未启动 8911/5174；未启动服务、
真实项目或真实模型；所有本阶段 transport 均由 fake 注入。

## 2. 实施内容

### Fake seam

`poc/medical_monitoring_ai_native_r7/tests/fake_harness.py` 现在支持：

- valid/invalid catalog；预检异常及稳定的 secret-bearing 异常文本；
- complete/partial/truncated/timed_out/failed/not_evaluable receipt；
- profile、input、invocation identity mismatch，fallback 和 unsupported operation；
- 可配置 blocking release timeout 与逐次 transport exception；
- 记录安全的 catalog/profile/preflight 观测，并保存实际传给 invoke 的同一
  `PreflightResult` 对象，便于证明没有 claim 后重新读取 catalog。

### Regression seam

`test_harness_runtime.py` 新增/补强：

- receipt 六状态经未修改的 R1 classifier 得到对应状态；
- preflight exception 保持零 assignment/attempt/transport、diagnosis 去敏且只调用一次；
- 同时竞争的两个 background claimer 只有一个 transport call；
- blocked transport 的 run lease 续租、cancelling 不领取下一项；
- timeout/truncated 单次 linked retry、attempt lease 漂移的迟到写回拒绝与续作；
- 六类 receipt/identity/transport fault fail-closed、raw evidence 不泄露 path/secret。

`tests/test_medical_monitoring_r7_product_router.py` 新增/补强：

- 默认 MTPLX medium 与显式 DeepSeek max 的 selector/effort/profile digest 绑定一致；
- transport exception 的失败状态和公开中文投影；
- active harness stop 文案、当前调用完成可能性及不领取下一项；
- 产品响应的 provider/model/selector/attempt/lease/path/hash/secret 泄漏扫描。

## 3. 验证记录

已完成的离线命令与结果：

| 命令 | 结果 |
|---|---|
| `PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_harness_runtime.py -q` | `30 passed` |
| `PYTHONHASHSEED=0 python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q` | `33 passed` |
| `PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r1/tests --ignore=poc/medical_monitoring_ai_native_r1/tests/test_background_progress.py -k 'not seatbelt and not isolated_harness_timeout' -q` | `311 passed, 4 deselected` |
| `PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r6/tests -k 'not medical_writing_aggregate_unchanged' -q` | `758 passed, 5 deselected` |
| `python3` 的 `compile()` 检查 3 个本阶段 Python 文件 | `passed` |

R7 全量在 receipt 写入前仅因 create-only allowlist 缺少该 receipt 失败：
`151 passed, 1 failed`；worker 写入 receipt 后为 `152 passed`。Codex 随后发现并修复
`timed_out` receipt 在 profile/input/fallback 身份漂移时仍会误归入可续作 timeout 的缺口；
新增 3 个参数化用例后，聚焦 harness 为 `30 passed`、R7 全量为 `155 passed in 13.12s`。

receipt JSON 解析通过；目标端口 `8911` 与 `5174` 的 socket probe 均为
`connect_ex=1`（未监听）。7 个 R7/产品相关 Python 文件的 `compile()` 检查通过。
R6 四个固定文件的 SHA-256 与冻结值一致；当前 R7 边界测试报告医学写作 443 个
非缓存文件、聚合 SHA-256 为
`394746881c0b8b312805ee6e22047f6e32b66559d76987a7337ab151ed04a1c1`。
直接 `py_compile` 曾因解释器试写受限的
`/Users/smkzw/Library/Caches/com.apple.python/...` 失败，未向该路径写入；随后
使用不落盘的 `compile()` 完成同等语法检查。

## 4. 环境限制与未宣称内容

一次 R1 全探针得到 `327 passed, 6 failed`。6 个失败均为当前受限环境：3 个
测试无法绑定临时 loopback HTTP listener，3 个 macOS Seatbelt/进程隔离测试未能
完成；因此没有把该探针写成全量绿色证据。R6 全量的 5 个失败为既有 542-file
medical-writing 边界断言与当前文件快照不一致，使用既有的非边界 functional 子集
`758 passed`，未修改 R6。

不据此宣称真实模型调用、provider cancel、provider exactly-once、真实项目、前端/视觉
接受或 R7 总体接受。receipt 是 worker evidence，Codex 保留最终 source、边界、
全量回归和 acceptance 权限。

## 5. 下一安全动作

Codex 可继续复核 receipt-allowlist、相邻回归选择和最终边界；本 worker 不执行真实
smoke、服务启动、前端或医学写作路径操作。

## 6. Codex 恢复后纠偏

Codex 从 `medical_monitoring_r7_slice_06_immediate_pause_20260828.md` 恢复并先核查
中断遗留，再完成 worker_03 原任务包。独立代码审查确认：纯 `timed_out` receipt 可按
冻结规则有限续作，但一旦同一 receipt 同时出现 profile digest、input digest 或 fallback
漂移，必须归为不可续作 `failed`。修复位于共享 `_classify_r6_receipt`，未在调度层增加
第二套例外规则。纠偏后复跑：harness `30 passed`、产品路由 `33 passed`、R7 全量
`155 passed`、R1 离线功能 `311 passed, 4 deselected`、R6 功能 `758 passed, 5 deselected`。
本记录仍不代表独立实现会商、真实模型 smoke 或 Slice-06 总体接受。

## 7. 独立会商纠偏与离线接受

独立会商由 `google-antigravity/gemini-3.7-flash:high` 与
`grok-build/grok-4.6:medium` 分别完成，均未 fallback。Grok 首轮提出两个
P1 候选；Codex 逐项复现：

- claim 后、bind 前中断并不会形成 pending zombie。新增 crash-window
  回归证明：首次 attempt 保持 interrupted/unbound 且零 transport；用户明确
  “继续”后由 R1 interruption observer 先绑定 ordinal 1，再由 R7 建立唯一的
  ordinal 2 续作并完成。该路径无需新增 R7 journal 枚举。
- 某 AI 单元两次不完整后、仍有另一独立 pending 单元时，公开状态错误隐藏
  `继续`。`_public_overlay` 现仅在 INTERRUPTED 且确有 continuable/runnable
  工作时保留 `继续`；新增双单元回归锁定该行为。

纠偏后：harness `32 passed`、产品路由 `33 passed`、R7 全量 `157 passed`、
R1 功能 `311 passed, 4 deselected`、R6 功能 `758 passed, 5 deselected`，
compileall 通过。Grok 同 session 第二轮撤回错误 P1 并接受修复；会商结论为
冻结的 synthetic/offline Slice-06 无遗留 P0/P1/P2，可进入独立 matrix-14
真实 synthetic smoke 门禁。仍未宣称真实模型、真实项目、服务、浏览器或 R7
总体接受。

## 8. Matrix-14 真实 synthetic smoke 与当前阻断

首次 MTPLX worker02 实跑经完整 R7 后台链路进入冻结 R6 适配器，但 R1
冒号分隔 attempt ID 不符合 R6 invocation ID 语法，因而在进程启动前以
`invalid_invocation_id` 失败。Codex 在 R7 桥接层增加确定性的
`r7_<sha256-prefix-128bit>` 映射，并补齐要求模型只返回 JSON、逐字复制覆盖项的
确定性输出契约；R1/R6 未修改。

独立 Pi/Gemini 与 Grok Build 会商均接受映射。Grok 指出的“测试仅使用 fake、未钉住
冻结 R6 语法”缺口已用真实 `OmpPrintAdapter` 离线语法门回归修复。最终离线结果：
harness `34 passed`、R7 `158 passed`、产品路由 `33 passed`、R1
`311 passed, 4 deselected`、R6 `758 passed, 5 deselected`，compileall 通过。

随后仅授权一次新临时目录中的 MTPLX medium 受控重验。attempt-1 确实进入
OMP/model 调用，但在冻结的 120 秒上限后得到 terminal timeout receipt：
`state=timed_out`、`parse_state=unparsed`、`analysis_complete=false`、
`fallback_used=false`、exit 143。运行时创建的唯一 linked attempt-2 因外层证据
读取器在 180 秒结束而失去活动进程；租约过期后由内置恢复逻辑标为
`interrupted`，公开状态为“本项分析未完成，已达到本次重试上限。”无 OMP 残留，
8911/5174 均保持停止。

因此 matrix-14 和 Slice-06 仍未总体接受；DeepSeek max worker03 按串行门禁保持
pending，不作为 MTPLX 的替代或 fallback。下一安全动作见
`context/medical_monitoring_r7_slice06_matrix14_live_smoke_checkpoint_20260828.md`。

## 9. Matrix-14 timeout=300 新包与双模型串行验收

按用户“本地 MTPLX 给更长等待时间”的补充要求，新建受治理执行包，在 R7
既有 run-level override 中冻结 300 秒超时，不改 R1/R6，不把 DeepSeek 作为
MTPLX fallback。先由 worker01 只读验证冻结路径，再由 Codex 串行放行真实调用。

MTPLX medium 在正确的临时 workspace `mm_r7_matrix14_4spl13_m` 中仅产生一次
attempt：R1 journal 为 terminal `complete`，R7 control 为 `finished`，work unit
为 `passed`；R6 receipt 为 `state=complete`、`parse_state=parsed`、
`analysis_complete=true`、exit 0、`fallback_used=false`，精确覆盖 synthetic
受试者，真实 adapter 时长 156.852 秒。worker02 报告最初列出的 `w23e14ng`
是早期空跑目录，Codex 已从日志与 SQLite 纠正，未将其作为成功证据。

仅在 Codex 独立接受 MTPLX 后，DeepSeek V4 Flash max 才在另一临时 workspace
`mm_r7_matrix14_ds_csqz_ebu` 中执行。它同样仅有一次 terminal `complete`
attempt，control `finished`、work unit `passed`；冻结 selector 为
`deepseek/deepseek-v4-flash`、effort `max`、timeout 300 秒、fallback 为空，
R6 receipt 解析完整且精确覆盖 synthetic 受试者，真实 adapter 时长 16.461 秒。

双腿均由 Codex 直接读取冻结 binding 与运行 SQLite 验收。当前 R7 与产品路由
回归 `192 passed`，compileall 通过；R1/R6 固定哈希不变；无 OMP 残留，
8911/5174 均保持停止。该结论只接受 Matrix-14 synthetic live-smoke 与
Slice-06 harness bridge 的既定范围，不外推到真实项目、产品服务、浏览器、
前端视觉、医学结论或 R7 总体完成。
