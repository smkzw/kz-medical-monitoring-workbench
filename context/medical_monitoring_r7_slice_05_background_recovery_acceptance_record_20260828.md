# R7 Slice-05 后台执行与中断恢复有限验收记录

日期：2026-08-28  
结论：`ACCEPT_R7_SLICE_05_BACKGROUND_RECOVERY_SYNTHETIC_OFFLINE_LIMITED`

## 已接受范围

接受当前 receipt 哈希锁定的 synthetic/offline 实现：单 Run 控制记录、租约与 generation
领取、依赖调度、后台线程、停止/继续、过期重建、R1 进度投影和产品中文动作接口。

独立会商复现并促成关闭：过期租约后“停止”回滚恢复、最后一个工作项完成后仍提示“继续”、
重复停止非幂等、进度响应内部词扫描缺口、产品停止/继续覆盖不足及过期恢复证据缺口。

## 决定性证据

- focused runtime/determinism：47 passed；产品路由：28 passed。
- R7：125 passed；R1 core：327 passed。
- R6 功能回归：758 passed；5 个旧缓存计数断言 deselected，详见独立缓存排除纠偏记录。
- isolated compileall：70；receipt JSON 有效；8911/5174 `connect_ex=61`。
- Pi/Gemini 与 Grok Build 两席完成；Grok 在同一 session 内复核修订后的最终字节并给出有限接受建议。

## 合同解释与相邻边界

v0.2 合同保持原哈希。单独勘误明确：进度读取可以先把过期租约持久化为 interrupted，再从
后续 deferred read transaction 读取一致受众快照；不得启动/继续 worker 或改变 R1 进度。

医学写作保护改用 443 个非缓存文件的稳定聚合；未写医学写作产品源码，也未修改 R6。
R6 的 5 个 542 文件缓存快照断言作为已知旧门禁保留，不虚称 R6 全量绿色。

## 未接受范围

不包括 R7 总体、真实模型/项目、真实 retry/continuation、两进程 kill-9、exactly-once、服务、
前端、视觉或浏览器验收。下一安全动作是冻结 Slice-06 capability-attempt owner/lease/retry 合同，
仍不启动服务、模型或真实项目。
