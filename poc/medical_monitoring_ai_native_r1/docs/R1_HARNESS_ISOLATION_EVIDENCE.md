# R1 Harness 执行隔离决策与证据

日期：2026-08-09  
范围：`medical_monitoring_ai_native_r1` 的 synthetic/offline harness；不含产品、医学写作、8911、真实 provider、真实项目或生产发布。

## 1. 决策

R1 仅在当前 macOS 合成 POC 中采用 `/usr/bin/sandbox-exec` + 参数化 Seatbelt
profile，并命名为 `macos_seatbelt_r1`。请求该隔离时，如平台、固定可执行文件、
声明目录或 `/usr/bin/sandbox-exec` 任一不可用/漂移，执行在派发前失败关闭。

此选择不是长期生产架构。当前 macOS 26.5.1 的本机手册明确把
`sandbox-exec` 标记为 `DEPRECATED`，Apple 推荐 App Sandbox。因此：

- 当前 R1：用已存在的 Seatbelt 工具验证文件内容、网络、exec 与进程树边界；
- 后续原生产品候选：签名的 App Sandbox helper，使用 entitlement 和用户授权文件范围；
- 若威胁模型需要隔离不可信/可对抗代码：再评估 Lima/Podman 管理的 Linux VM；
- 在完成相应迁移、打包、签名、升级与回滚验证前，不把本切片称为生产级沙箱。

## 2. 候选比较

| 路径 | 实际强制力 | 当前机器/许可 | 运维与回滚 | R1 处置 |
|---|---|---|---|---|
| 原有 `Popen(shell=False)` 进程包络 | 固定 argv/cwd/env，但不能阻止文件读取、联网或子 exec | 无新增依赖 | 最低；直接回滚 | 保留为未请求隔离的旧兼容路径，不得标记为已隔离 |
| macOS Seatbelt / `sandbox-exec` | 当前系统可实际拒绝文件内容、网络和未声明 exec；`setsid/killpg` 处理同一进程组 | 系统自带；参考了 Apache-2.0 的 OpenAI Codex Seatbelt 实现模式；本机工具已弃用 | 无安装、可删除策略接线回滚；未来系统兼容风险高 | 选作 R1 synthetic POC，能力探测与身份漂移均失败关闭 |
| Apple App Sandbox helper | Apple 官方、内核强制；按 entitlement、容器和用户选取文件授权 | macOS 原生；需要应用 target、签名/entitlement 与 helper 继承配置 | 工程、签名、文件授权迁移成本较高；长期支持路径更明确 | 作为后续原生产品首选候选，本轮未签名、未安装、未启动 |
| Lima VM | 独立 Linux VM，主机仅显式共享目录/端口 | 本机 `limactl 2.1.3`；Apache-2.0；当前无 instance | 隔离更强，但有镜像、启动、资源、共享目录、升级与回滚成本 | 本轮未创建/启动；高威胁模型再做独立 POC |
| Podman machine | macOS 上经 VM 承载 Linux container 边界 | Apache-2.0；本机未安装 Podman；官方说明 macOS 必须使用 VM | 引入 VM 与容器镜像供应链、生命周期和磁盘成本 | 不为本轮安装；若选择 VM 路径再与 Lima 一并评估 |

权威参考：

- Apple, [Configuring the macOS App Sandbox](https://developer.apple.com/documentation/xcode/configuring-the-macos-app-sandbox)：App Sandbox 由 macOS 内核强制，限制文件、网络及其他系统资源。
- Apple, [Protecting user data with App Sandbox](https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox)：应用容器、用户目录限制与嵌入命令行 helper 的继承要求。
- OpenAI Codex, [core sandbox support matrix](https://github.com/openai/codex/blob/main/codex-rs/core/README.md) 与 [Seatbelt implementation](https://github.com/openai/codex/blob/main/codex-rs/sandboxing/src/seatbelt.rs)：macOS 路径固定使用 `/usr/bin/sandbox-exec` 并按解析后的文件/网络策略生成 Seatbelt 参数；仓库为 Apache-2.0。
- Lima, [official repository](https://github.com/lima-vm/lima) 与 [license](https://github.com/lima-vm/lima/blob/master/LICENSE)：Linux VM、文件共享/端口转发，Apache-2.0。
- Podman, [podman machine documentation](https://docs.podman.io/en/latest/markdown/podman-machine.1.html) 与 [official repository](https://github.com/podman-container-tools/podman)：macOS/Windows 必须经 VM 运行 Linux containers，Apache-2.0。

访问日期均为 2026-08-09。

## 3. 已实现合同

`HarnessIsolationPolicy` 冻结并进入 `ExecutionProfile.fingerprint`：

- `readable_roots`：声明的输入/运行材料内容范围；
- `writable_roots`：唯一允许写入的范围，同时允许读取；
- `allowed_executables`：精确可执行文件闭包，符号链接路径和解析目标均冻结；
- `deny_network=True`：Seatbelt 显式 `deny network*`；
- `terminate_process_group=True`：harness 使用 `start_new_session=True`，超时/取消对进程组先 `SIGTERM` 后 `SIGKILL`；
- profile 通过 `-D KEY=value` 传入路径，SBPL 不直接拼接路径字符串；
- sandbox 工具、argv 文件及可执行闭包均记录 SHA-256，运行前复核；
- API profile 禁止携带 harness 隔离元数据；未请求隔离的 harness 记录空 isolation 字段，不伪装为已隔离。

R1 的系统运行基线允许读取声明目录之外的 macOS/Python 系统运行材料，但排除
`/Users`、`/private/tmp`、`/private/var/folders`、`/Volumes`、`/Network`
下的文件内容；声明目录以更具体规则放行。它不是“任意未知程序零信任”边界，
也没有验证所有 macOS Mach/XPC 数据通道。

如果 Python 解释器来自用户目录下的 virtualenv，该 virtualenv 根目录必须作为
只读运行时闭包显式写入 `readable_roots`；否则 Seatbelt 会正确拒绝
`pyvenv.cfg`/site-packages。这不是隐式放宽，而是可审计、进入 profile fingerprint 的
必要运行时输入。

## 4. 决定性负向证据

测试全部只使用 pytest 临时目录、synthetic 字符串和回环端口 9：

1. 声明输入读取成功；同一临时根下未声明 sibling 文件读取返回 `EPERM`。
2. 声明输出写入成功；未声明 sibling 写入返回 `EPERM`，且文件未出现。
3. `127.0.0.1:9` 连接返回 `EPERM`，没有真实数据外发。
4. `/usr/bin/true` 未在可执行闭包中，子 exec 返回 `EPERM`。
5. 父进程未允许的 synthetic secret 环境变量在 harness 中不可见。
6. backend 路径在 profile 冻结后变为不可用时，派发前抛出
   `CapabilityRuntimeError`，attempt 列表保持空。
7. 超时和主动取消两条路径均启动同进程组的延迟子进程；终止后等待超过子进程原定写入时间，
   “survived” marker 均未出现。

## 5. 验证快照

```text
focused isolation: 4 passed, 47 deselected in 2.05s
capability runtime: 51 passed in 2.68s
R1 core: 154 passed in 3.39s
Ruff (capability_runtime.py + test_capability_runtime.py): All checks passed
```

### 2026-08-09 `.venv` 运行时声明纠正

用本项目文档指定的 `.venv/bin/python` 重跑时，3 项隔离测试首先失败，原因是
synthetic profile 未把 `.venv` 声明为只读运行时，Seatbelt 拒绝读取
`.venv/pyvenv.cfg`。测试 helper 已纠正为：仅当当前解释器确实位于 virtualenv
时，显式把 `sys.prefix` 加入冻结 `readable_roots`。产品默认策略未改。纠正后：

```text
focused .venv isolation: 3 passed, 48 deselected
capability runtime under .venv: 51 passed
R1 core under .venv: 165 passed
```

因测试 helper 内容已变更，下方早期 reviewer 冻结 test SHA 仅是历史快照；
当前接受必须以最新 SHA 和本次 `.venv` 复现为准。

本机观测：macOS 26.5.1 (25F80)；`sandbox-exec` 存在且手册标记
`DEPRECATED`；`limactl 2.1.3` 存在但 `No instance found`；Podman 不存在。
本轮没有创建/启动 VM、服务或端口，没有安装依赖。

独立 fresh-context reviewer `/root/capability_runtime_review` 对冻结代码只读复核并
重跑：focused isolation `4 passed, 47 deselected`、capability `51 passed`、R1 core
`154 passed`，结束前 SHA 仍稳定；verdict 为 ACCEPT，仅限本 synthetic/macOS 子门。

## 6. 残余风险与退出条件

- Seatbelt 接口已弃用，OS 更新可能使本后端不可用；此时必须失败关闭，不能自动降级为普通 `Popen`。
- 当前证明是 synthetic、当前 macOS 构建和当前 Python executable closure 的行为证据，不能外推到任意 harness、真实 provider 或真实项目。
- 文件元数据、系统运行材料和未覆盖的 macOS IPC 面没有完成恶意代码威胁模型验证。
- `killpg` 只证明同一 session/process group 的后代回收；恶意程序主动创建新 session
  的逃逸未验证，只有 VM/cgroup 类边界才能作为更强威胁模型候选。
- 进入产品前必须重新选择并验证签名 App Sandbox helper 或 VM 边界，形成最小 entitlement/共享目录、网络策略、资源配额、升级与回滚证据。
- R1 总体验收仍未完成；本文件只处置 execution isolation 子门。
