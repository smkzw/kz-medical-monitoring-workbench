# 医学监查 P10 v8 访视改期语义角色离线纠偏无损暂停

日期：2026-08-01
状态：离线纠偏 PASS；主 Goal 未完成；等待用户后续指令

## 当前结论

- v8 离线 prompt/classifier/cutover 纠偏已通过 Codex 最终验收和 Luna
  独立只读终审。
- 这不是 v8 canary、RUX 协议门通过、发布批准、MY009 授权或候选决定。
- 所有 candidate accept/reject/adopt/confirm/activate 权限仍属于用户。
- v4-v7 终态不得 retry/reuse/salvage。

## 最终实现

- 当前协议 prompt：
  `monitoring-protocol-clause-structuring-v8`。
- v7 已进入显式终态 legacy 集；queued/failed v7 不复用，新工作生成不同 v8
  identity。
- initial/repair provider 合同均明确：
  - 改期候选可以保留作为 title/trigger/object/target/action modifier 的
    计划访视或窗口语言；
  - 独立 schedule obligation 与 reschedule action 必须拆分。
- 分类器已覆盖：
  - exact v7 `计划访视改期原则`；
  - title/object/target/window definition；
  - structured fields 跨 newline/分号/句号条件—动作链；
  - modal/auxiliary 与量词作用域；
  - schedule predicate 在 term 前后；
  - `进行/完成` 直接支配补访或计划外访视；
  - pure schedule/reschedule/unscheduled 和真实 mixed-family 负控。
- 未引入 global reschedule precedence。
- medication -> dispensing/PK -> withdrawal -> safety -> collection -> family
  顺序、candidate-indexed 全错误、一次 repair、全响应原子性、C1-C5、
  C3 8→15 与结构/证据 blocker 均保持。

## 路由与审阅

- Pi/deepseek-v4-flash session：
  `019fba70-4de6-7000-b944-c145c409f6db`。
- 完成 initial + 两次 same-session recovery；之后独立验收仍发现缺口。
- 按声明 fallback 复用原生 Codex child：
  `/root/v7_lexical_corrective`。
- 独立 Luna reviewer 始终复用：
  `/root/rux_protocol_v4_audit`。
- Kimi 未使用；没有重复 Pi dispatch。
- 详细实现与终审：
  - `runs/codex-subagent_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801.md`
  - `runs/codex-subagent_monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801_final_review.md`

## 最终文件与 SHA-256

- `services/api/app/monitoring_ai_service.py`
  `0485440a2af4c75bb243c0de36f6d5603bd39dfbdffb77dcf2a813c2bd81057d`
- `services/api/app/monitoring_protocol_preparation_service.py`
  `0231e1386cc7c37fd1f5f0eed4c226d6bc43f98bf1a0dbdb4da105c0d7624830`
- `tests/test_monitoring_ai_service.py`
  `39bd0a580d4cd22c97a88f8e3b05035b9b836ef4b80b25642cd3bfafed816398`
- `tests/test_monitoring_protocol_preparation.py`
  `df0bc517d66ca90d4fa74da46f43e77bec0c655ef70472fa1b096d39bc016bf1`
- `tests/test_monitoring_ai_api.py`
  `81dfad4abb39e80ccfe65ee242dc78ba65fe88a365dd9cae73fc22ed1ae28c8e`

## 最终验证

- 五文件 `py_compile`：PASS。
- 三文件聚焦：`376 passed in 10.34s`。
- 全医学监查：
  `1371 passed, 4299 deselected, 27 warnings in 679.52s`。
- 医学写作相邻五文件：`200 passed in 1.50s`。
- Luna 最终 delta review：PASS。
- 27 warnings 为既有 SWIG/FastAPI/openpyxl 警告，无新增失败。

## 冻结运行状态

- 8911：无 listener，暂停期间必须保持停止。
- 5174：无 listener，暂停期间保持停止。
- 无本任务 pytest、runner、Pi、Codex fallback 或 monitoring worker 后台进程。
- 只读 runtime 计数：
  - v4：8 jobs / 8 attempts / 8 candidates；
  - v5：1 / 1 / 0；
  - v6：1 / 1 / 0；
  - v7：1 / 1 / 0；
  - v8：0 / 0 / 0。
- 未写 runtime DB，未启动真实项目，未创建 v8 job/candidate，未作候选决定。

## 下一安全动作

仅在用户下一次明确继续本 Goal 后：

1. 重读最新全局/项目 AGENTS、本暂停记录、v8 review 与 LOOP ledger。
2. 只读复核五文件 hash、8911/5174 为 0 listener、v4-v8 计数不漂移、
   无中断的 runner/worker/局部修改。
3. 对 21 个 runtime 主库做一致的 pre-canary 备份与完整性检查。
4. 只启动 8911，先验证 readiness/schema/capability 和 v4-v7 终态历史不被
   startup/cutover 改写。
5. 仅创建一个新 ID 的 RUX v8 `visit_window_and_order` canary；不得复用旧 job，
   不得启动其他 topic/MY009/三个真实项目。
6. 使用一次长硬等待，不固定轮询、不重复 POST、不 retry；终态后立即停止 8911。
7. 复用 Luna reviewer 做独立只读审查，并再次运行聚焦、全监查与医学写作相邻门。
8. 只有 canary 与独立审阅通过，才讨论下一项目门；仍不得自行作候选决定。

本切片已无损暂停。8911 必须保持停止。
