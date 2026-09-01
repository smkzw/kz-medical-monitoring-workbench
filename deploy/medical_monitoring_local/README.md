# 医学监查工作台本地管理

本目录是医学监查子系统的本地分发与运维入口。面向非技术用户提供中文的一键启动、停止、运行状态、首次启动检查、升级准备和卸载数据处置预览。它不修改医学写作分发目录，也不在合同验收期间启动真实服务。

## 常用命令

```bash
deploy/medical_monitoring_local/manage.zsh preflight
deploy/medical_monitoring_local/manage.zsh status
deploy/medical_monitoring_local/manage.zsh start
deploy/medical_monitoring_local/manage.zsh stop
deploy/medical_monitoring_local/manage.zsh synthetic-lifecycle --scenario start-stop-restart
deploy/medical_monitoring_local/manage.zsh synthetic-g4-notification
deploy/medical_monitoring_local/manage.zsh synthetic-g4-15-4 run --runtime-root "<临时合成根>"
deploy/medical_monitoring_local/manage.zsh prepare-upgrade
deploy/medical_monitoring_local/manage.zsh uninstall-plan --output-dir "<输出目录>"
deploy/medical_monitoring_local/manage.zsh uninstall-plan --include-project-data --output-dir "<输出目录>"
```

`uninstall-plan` 只生成预览计划，不删除任何数据。默认结果是移除应用、保留项目数据、备份、导出与业务审计；只有显式加上 `--include-project-data` 才会预览“同时清除项目数据”，且文案会明确说明尚未删除任何数据。

## 实际应用入口（G6 synthetic）

双击 `MedicalMonitoring.app` 即可启动实际应用入口；不要用 `manage.py`、终端命令、预开的地址或浏览器书签代替。应用启动前会校验 `entry_manifest.json`、`execution_boundary_manifest.json` 和 `viewport_layout_manifest.json`，只接受合成配置与本机回环通信。

应用只允许一个归属明确的实例。重复双击会回到已有窗口，不会创建第二个实例；正常退出会回收应用状态。健康检查、窗口打开、入口占用或 manifest 校验任一失败，应用会显示中文阻止结果并清理半初始化状态，不接管未知进程。

技术 manifest 用于受控证据，用户窗口不显示路径、端口、进程、digest 或模型路由。

## 首次启动检查

`preflight` 只检查本机 Python、Node.js、前端依赖、运行配置、可写数据目录和运行入口占用。任一缺失都会失败关闭，并给出一条可执行的中文修复提示。检查不会调用模型、不会创建真实项目、也不会启动服务。

未通过首次启动检查时，不得把工作台视为已安装或已就绪。

合成离线验收必须设置 `MM_MONITORING_OFFLINE=1`。在该模式下，`start` 会明确拒绝启动任何服务；它只用于验证本地管理入口、数据处置和失败关闭行为，不能作为真实安装或运行就绪的证据。

## 合成离线一键生命周期演练

`synthetic-lifecycle` 是不访问分发根的合成验收入口。用户只需执行一次管理入口动作；演练由内存中的 synthetic adapter 驱动，不启动服务、不调用模型、不读取项目、不写入文件，也不要求用户管理 Python、Node.js、数据库、环境变量或端口。

```bash
deploy/medical_monitoring_local/manage.zsh synthetic-lifecycle --scenario start-stop-restart
```

可选场景及预期终态：

| 场景 | 预期信号 | 关键后置条件 |
|---|---|---|
| `start-stop-restart` | 就绪 | 启动后停止，再重启并回到就绪 |
| `ready` | 就绪 | 所有合成入口均报告就绪 |
| `failure` | 失败 | 启动失败后自动回滚，不能留下半初始化状态 |
| `partial` | 失败 | 检出残留的部分运行并拒绝继续启动，不静默补齐 |
| `foreign-ownership` | 失败 | 拒绝操作外部归属，外部状态保持不变 |

该入口只证明合成生命周期信号、失败关闭和归属保护可重放；它不证明真实安装、真实服务或真实运行就绪。`start` 在 `MM_MONITORING_OFFLINE=1` 下仍会拒绝启动真实服务，两者不能互相替代。

## 合成离线 G4 通知与 §15.4 程序

R8 G4 提供两条相互独立、可组合重放的合成证据链，均通过 `manage.zsh` 暴露，且**不启动服务、不调用模型、不读取真实项目**。

### 通知 seam（`synthetic-g4-notification`）

```bash
deploy/medical_monitoring_local/manage.zsh synthetic-g4-notification
```

该入口在内存中演练终态投影、幂等 outbox、应用内持久记录、合成系统通道证据与只导航意图。它不解析分发根、不要求 `--root`，也不写入任何文件。

### §15.4 十三项程序（`synthetic-g4-15-4`）

```bash
deploy/medical_monitoring_local/manage.zsh synthetic-g4-15-4 run --runtime-root "<临时合成根>"
deploy/medical_monitoring_local/manage.zsh synthetic-g4-15-4 replay "<manifest.json>" --strict
```

`run` 只接受位于系统临时目录下的合成工作区；**不能**传入医学监查分发根、真实项目路径或用标记文件把其他目录伪装成合成工作区。`replay` 独立校验 canonical manifest，拒绝排序、摘要、identity 或 lineage 被篡改的证据。

十三项全部 `passed` 时 CLI 返回成功；任一项非 `passed` 时返回退出码 4，且用户文案不含端口、路径或内部标识。

## 运行入口归属

医学监查工作台使用三组运行入口：后端、桌面前端和医学监查辅助入口。状态与首次启动检查会读取三者占用；**停止**动作须先确认当前分发根存在且版本正确的 `runtime_config.json`，否则失败关闭且不终止任何进程。停止只终止工作目录**恰好**为当前医学监查分发根或其 `frontend` 的进程，不把更宽 `--root` 下的相邻子目录进程视为本应用。

辅助入口仅在运行配置中显式设置 `aux_enabled=true` 时才算“必须已启动”的组成部分；未启用时，后端与桌面前端已启动即可视为已启动，但仍会检查辅助入口是否被其他应用占用。若运行入口被其他应用占用，启动会被拒绝，且不会终止对方进程。

普通成功文案只使用“医学监查工作台、启动、停止、运行状态、升级准备、保留项目数据、清除项目数据”等中文表达，不展示端口、数据库、进程、表名或绝对路径。

## 升级准备

`prepare-upgrade` 先按已接受的项目备份语义生成升级保护证据，再做兼容性预检。任一步失败都不会推进版本标记、schema 或改写原数据。同项目维护任务并发时，第二次调用返回稳定冲突结果，不创建第二份升级暂存。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 检查或计划生成成功 |
| 2 | 首次启动条件缺失或参数不完整 |
| 3 | 运行入口被其他应用占用，或停止对象不归本应用 |
| 4 | 备份、兼容性或升级准备失败，原数据未更改 |
| 5 | 同项目维护任务正在执行，本次调用未开始 |

## 边界

- 不安装系统服务，不需要管理员权限。
- 不读取真实项目根，不调用真实模型。
- 不修改 `deploy/medical_writing_local` 或医学写作源码。
- 对外的卸载入口只生成预览；§15.4 验收内部会在系统临时目录中完整演练“预览—取消—确认”，不能指向真实项目。
- 真正删除应用或真实项目数据属于未来独立确认工具，不在本入口范围。
