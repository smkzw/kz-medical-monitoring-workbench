# 医学监查 R8 G5 预真实联合独立审阅第 1 轮

日期：2026-08-31  
处置：`REVISE_G5`  
边界：仅审阅 synthetic/offline 当前文件与证据；未访问真实项目、模型、浏览器或服务

## 已核对证据

- G5 evidence manifest 当时列出的 16 项 path/SHA 全部匹配。
- G0/G1→G2→G3→G4 顺序与禁止声明边界未发生越级。
- 当时 G4 聚焦 67 项、扩大相邻 205 项及 9/9 确定性均通过。

## P1-1：终态版本与跳转目标未绑定当前可访问对象

通知事实虽以 `terminal_revision` 入键，但消费端没有把事件 revision 与当前结果目标的
revision/manifest 身份绑定；同一 run 的较新 revision 后仍可能消费较旧事件。点击跳转时也
没有重新核对目标仍存在、当前 revision 及 source/output manifest，因此旧通知可能导航到
已变更或不可访问的对象。

必须完成：事件消费时校验当前 revision、binding digest、source/output manifest 与目标存在性；
同一 run 冻结后拒绝另一 revision；导航点击时重新核对当前目标，并用回归证明失效关闭。

## P1-2：§15.4 发布清单不构成自包含运行闭包

当时 `release_sources.json` 只列出部分 R7 文件，遗漏 `mm_r7.profile_store`、
`mm_r7.project_verifier` 及其 R1-R6 传递依赖。发布 manifest 可生成不等于其中包含的
§15.4 程序可在脱离工作台源码后运行。

必须完成：发布清单纳入实际运行依赖闭包，并从“只复制发布 manifest 所列文件”的隔离副本
完整运行十三项程序，证明不回落到原工作台路径。

## 门禁处置

- G4 原接受记录在两项 P1 关闭并重新独立复核前不得作为当前通过证据。
- G5 不接受，G6 保持锁定。
- 唯一允许动作是完成两项纠偏、聚焦/相邻/确定性回归、重建当前证据并回到同一独立审阅会话。
