# 医学监查 R8 G5 预真实联合独立审阅第 2 轮

日期：2026-08-31  
处置：`ACCEPT_G5`  
边界：只读 synthetic/offline；未访问真实项目、模型、浏览器或服务，未修改文件

## 独立证据

- G5 evidence manifest 共 21 项，全部 path 存在且 SHA-256 匹配，无 stale/superseded。
- 独立指定聚焦/相邻套件 `118 passed`；Codex 扩大相邻套件 `210 passed, 3 non-failing warnings`。
- 当前发布清单 157 文件，digest
  `33fa98a46b8b0306839fd8dc7b6e86e628b002c01e4903c756a6f2db273a3263`；
  154 Python、1 JSON、1 Markdown、1 zsh。
- 仅复制 release manifest 文件到临时 release 根后，§15.4 十三项全部 `passed`，digest
  `aec859cf59e4d3bac812f45293dff6175f4117df1f7b985fffc9f8e28d659475`。
- 运行期间加载的 107 个 `mm_r1`–`mm_r7`/fixture 模块全部来自隔离 release 根，未回落原工作台。
- 8911/5174/8984 前后均停止；医学写作目录只读指纹
  `ba4975e20315482607bee43693d5c775c415fc2547df2f1a403348f205e5a018`。

## 原 P1 关闭

### P1-1：终态版本与当前目标绑定

已关闭。事件消费校验当前 revision、binding、source/output manifest 和目标存在性；同一 run
冻结后拒绝另一 revision；导航重新核对 revision、binding、manifest、目标存在性与可访问性。
独立反例证明旧 revision 为 `terminal_revision_stale`，同 run 另一 revision 为
`terminal_revision_conflict`，六类失效导航均 blocked 且无导航副作用。

### P1-2：§15.4 发布运行闭包

已关闭。发布清单纳入 R1-R7 Python 包目录闭包；仅复制清单文件的隔离副本可完成 13/13，
并对所有相关已加载模块逐个证明来源位于副本内。

## P0-P4

`P0=0, P1=0, P2=0, P3=0, P4=0`，无新阻断。

## 允许的下一动作

可恢复 G4 synthetic/offline 接受并形成 G5 `PRE_REAL_INDEPENDENT_ACCEPTED`；其后只允许先冻结
独立 G6 synthetic `ego(lite)` 受众验收合同。合同冻结前不得启动应用或浏览器。

## 仍未接受

真实通知送达或用户实际看到、真实 §15.4、真实项目/模型/harness、产品浏览器、医学质量、
G6-G15、R8 总体及生产/商业化/监管/合规声明。
