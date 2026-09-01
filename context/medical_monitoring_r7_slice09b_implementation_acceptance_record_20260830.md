# R7 Slice-09B 实现接受记录（2026-08-30）

## 状态

`ACCEPT_R7_SLICE_09B_SYNTHETIC_OFFLINE`

本记录接受冻结 v0.2 合同范围内的 synthetic/offline 项目格式识别、staging-only 升级、恢复点、原子切换/回滚、崩溃恢复、legacy 只读能力与中文产品投影。它不等于 Slice-09、R7、R8、真实项目迁移、可视页面或产品发布接受。

## 冻结边界

- 普通 R1/R7 持久化 constructor 只接受 current 格式；legacy/unknown/malformed 在写连接前 fail closed。
- legacy 只通过 `ReadOnlyProjectView` 查询，不暴露 mutable store/registry。
- 支持的旧格式只经 sibling staging 专用迁移；live 路径不得作为 migration 输入。
- 09A 恢复点先于迁移，SQLite marker-last，切换前重新核对 writer、WAL、成员集合、指纹与闭包。
- 崩溃恢复入口包括 open、同键重放和 startup scan；`retained_for_triage` 不自动解除。
- 产品 DTO 只含固定中文字段；`dataCoverage` 仅 `complete/incomplete`，只有成功升级到 100% 且 `requiresReopen=true`。

## 最终实现

- R1/R7 共享唯一 schema-shape helper；R1 不依赖 R7。
- launch constructor、manifest 与 migration 共享唯一 canonical DDL。
- 09B 复用公开的 09A workspace snapshot/fingerprint/member-byte/artifact-closure seams。
- source-derived writer/background-writer 快照覆盖 R1 Store、ProfileStore、RunBindingStore、LaunchRegistry、RiskRuleRegistry 与后台进度/恢复 writer。
- legacy upgrade、backup、restore recovery-point 路由有显式正向 allowlist；普通写路由仍返回只读阻断。
- current/legacy_complete/legacy_required_missing/future/marker3/corrupt/upgrade_in_progress/upgrade_rolled_back/upgrade_unresolved 九态 DTO 矩阵已固定。
- 真实 `live_verifying` 中断通过六个 fresh coordinator 入口恢复，未见 live 损坏、重复写、身份漂移或提前成功。

## 决定性证据

- R7 + product router：`566 passed, 1 expected warning`。
- R1 core：`327 passed`。
- 09A adversarial：`69 passed, 1 expected warning`。
- focused contract：`150 passed, 1 expected warning`。
- live-verifying recovery：`6 passed`。
- 完整确定性矩阵：5 个 `PYTHONHASHSEED` × normal/`-O`/`-OO`，15/15 单元，每单元 70 tests，全通过。
- `compileall`、execution audit、conference validation 全通过。
- 独立同 session 三轮会商最终 `P0=P1=P2=P3=P4=0`，无 fallback。
- 8911/5174/8984 均停止；未运行真实项目、浏览器或模型，未触碰医学写作子系统。

## 冻结摘要

实现文件与 SHA-256 以 `artifacts/mm_r7_slice09b_implementation_20260830/manifest.json` 为准；schema manifest digest 保持：

`32f081a61730001e9cc69482b958de7a8b3af6e226b14bf445caad398a7c6a8a`

## 下一安全动作

进入 Slice-09C：先冻结 business audit、日志轮转/保留、容量与故障可观测性合同，再 governed implementation。继续保持 synthetic/offline、服务停止、真实项目/模型/浏览器与医学写作隔离；不得把 09B 接受外推为用户可见完整产品接受。
