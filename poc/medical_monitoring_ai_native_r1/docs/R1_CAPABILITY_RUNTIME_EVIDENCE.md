# R1 Capability Runtime 隔离证据

## 接受边界

本记录只接受 `capability_runtime.py` 的 synthetic/offline 隔离切片，不接受 R1
总体完成、真实 API/provider/harness 就绪、产品集成、真实项目运行或医学结论。
实现不自行选择模型；用户提供的 provider/model/selector/effort 被固化为
`ExecutionProfile`，API transport 由测试注入，harness 仅执行本地合成进程。

## 实现锚点

- `src/mm_r1/capability_runtime.py`：公共 JSON-RPC 形请求、执行身份、API/harness
  transport、manifest revision 前后检查、超时/取消/重复、恢复与覆盖分类；配置
  durable journal 时每次读取以 journal 为权威，不允许进程内缓存绕过完整性校验。
- `src/mm_r1/store.py`：应用拥有的 SQLite attempt journal；请求在 dispatch 前冻结，
  `BEGIN IMMEDIATE` 原子认领，租约过期转 `interrupted`，终态结果可跨重开重放，
  迟到完成被拒绝。请求身份、终态字段与结果内容互相校验；终态字段与结果共同
  纳入不可变哈希。versioned domain object 读取会核验外层哈希；raw 记录还核验
  ref/run/hash/immutable 与嵌套原始 JSON，候选 artifact 会沿 `raw-output:` 证据引用
  重新校验；恢复只报告损坏，不修复或重建。
- `src/mm_r1/adapters.py`：先封存 raw provenance，再登记 candidate-only artifact；
  提供 typed raw loader，读取必须经过 Store 的权威完整性路径；不写正式事实、
  不确认风险、不发布。
- `tests/test_capability_runtime.py`：51 项 focused 合成测试，覆盖 profile 冻结、
  API/harness 公共合同、`shell=False`、resume 身份门、完整 raw 保留、coverage
  分母 fail-closed、partial/truncated/failed/timeout/cancel/duplicate、双连接认领、
  重开重放、另一 PID 过期回收、迟到回调、journal 损坏、固定进程 envelope、
  raw 外层/嵌套损坏、删除后幂等重放拒绝、`NaN` 恢复报告，以及 macOS
  Seatbelt 文件/网络/exec/环境/同进程组负向边界。

## 设计决定与外部依据

- 不新增依赖，保留应用拥有的领域合同；公共 envelope 采用 JSON-RPC 2.0 的
  request id/result/error 形态，不把 JSON-RPC 实现库引入运行时。
- harness 使用显式 argv、`shell=False`、非空绝对固定 cwd、JSON stdin/stdout；
  执行文件与允许的环境值在冻结后校验，避免 shell 拼接和静默身份漂移。
- API transport 保持注入式；本轮无网络 provider 调用、无凭证、无真实项目。
- 普通 process envelope 仍不是 OS sandbox。显式配置 `macos_seatbelt_r1` 时，
  当前 macOS 合成 POC 会使用系统已有但已弃用的 `/usr/bin/sandbox-exec` 实际强制
  文件内容、网络和 exec 规则，并以进程组处理超时/取消；不可用时不降级。
- 选择、候选比较、当前系统探针、限制和迁移出口见
  `R1_HARNESS_ISOLATION_EVIDENCE.md`。该路径不构成生产级恶意代码隔离。

参考：

- Python subprocess: https://docs.python.org/3/library/subprocess.html
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
- OWASP OS Command Injection Defense: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html

以上资料仅用于设计核查，没有采用新的外部可执行依赖。

## 确定性验证

基础 capability runtime 的独立审阅先后识别并关闭 coverage fail-open、manifest
reader、resume 顺序、非终态、raw 持久化顺序和执行身份等问题。durable journal
扩展随后在同一 fresh-context 审阅会话中经历四次 VETO，分别关闭：

1. 过期租约可被同 owner 再认领、迟到结果仍可能提交；
2. resume 在重建完整身份前可能 dispatch，cwd 可退化为继承目录，终态状态门不完整；
3. request JSON 与 journal 行身份未完全对账，进程内缓存可绕过 journal；
4. 终态结果有哈希但终态字段未被哈希覆盖，可形成“行状态失败、重放结果完成”。

最终冻结实现由同一独立 reviewer 重跑测试并用只读/内存探针复现 fail-closed 后接受。

最终复现命令及结果：

```text
.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py
47 passed

.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests
150 passed
```

raw 读取完整性审阅首次复现 `NaN` recovery crash 与删除记录后的 ledger 重放并
给出 VETO；修复后同一会话重跑结果为 focused `47 passed in 0.72s`、full core
`150 passed in 1.43s` 并接受。最终冻结 SHA-256：

- `capability_runtime.py`: `296b95a29707ec6aeb091eabf7365bcc3cbb09a06b9b0afe7db336f6d6c9d6d1`
- `store.py`: `e47fa6b67cac709192886cf4f63dc42504df8b979a982d8076d1d2c1dfde83e7`
- `adapters.py`: `a60a2fbe374f49b23f411c6798d006607b7fe505e6ce7cc65f3bcd6e180d2c96`
- `test_capability_runtime.py`: `76c673b6cef78dba378d92948123b9c648939ee4cb30c42d28fb19263e3e4ba4`

Durable journal reviewer session：`019fe63e-92d5-7f40-8c6b-93799569db8c`；raw 读取完整性
reviewer session：`019fe66c-0ba1-7111-89ae-8b467544f51c`；最终 verdict：`ACCEPT`
（均仅限各自 synthetic 隔离切片）。

后续 execution-isolation 子门把原有未强制的 process envelope 补为可选、失败关闭的
macOS Seatbelt R1 后端。当前 Codex 实测为 capability `51 passed`、R1 core
`154 passed`；文件、网络、未声明 exec、环境和 timeout/cancel 同进程组负向证据见
`R1_HARNESS_ISOLATION_EVIDENCE.md`。独立 fresh-context reviewer
`/root/capability_runtime_review` 复现 focused `4 passed, 47 deselected`、capability
`51 passed`、core `154 passed` 并给出 ACCEPT。当前冻结 SHA-256：

- `capability_runtime.py`: `906c48fe1eefc8a9aeb34aafedbbd0c0d74d7b3529c9f5280dd32bf11a2bee9f`
- `__init__.py`: `5e082c5c586d69b6972e2f5175a1d952be69fbb9562797de208ca5ce89fbcb05`
- `test_capability_runtime.py`: `455bc19ab66c6e9c589a09ea3be9400b9ea6a6c41fe6915b66b8f0441042acf6`

## 仍为 OPEN / RESIDUAL

- allowed-tools 的业务语义仍只是 profile 元数据；harness 文件内容、网络、exec、
  环境和进程树已有 macOS synthetic 强制门，但 API 与生产路径尚无等价隔离；
- 真实 API/provider/harness 兼容性、用户显式 fallback 和 keychain 集成；
- 当前已验证 SQLite 重开重放、另一 PID 过期回收、新 attempt 续接，以及 harness
  timeout/cancel 同进程组后代回收；新建 session 的对抗性逃逸、真实 OS 强杀与
  harness 内部 checkpoint 恢复未验证；
- journal 与 SQLite raw 记录的读取时损坏已 fail-closed；hash-only 不能防御同时改写
  内容与记录哈希的协调攻击，完整持久化崩溃原子性仍未实现；
- ensemble、独立 adjudication binding/session、真实 token/费用不可得语义；
- API 非协作 transport 超时/取消后底层调用可能继续；
- executable identity 尚未覆盖全部传递依赖/安装包；
- credential/environment/argv 派生哈希的数据策略仍需在后续治理中明确。
