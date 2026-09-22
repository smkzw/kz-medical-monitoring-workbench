# 医学监查 0922 连续交付执行包
版本：2026-09-22 · delivery-replan-1。状态：供 fork 实施的完整规划；不是产品交付通过声明。

## 先读这五份
1. [PRD.md](PRD.md)：当前产品合同、范围、医学与用户体验要求。
2. [Plan.md](Plan.md)：W00–W07连续实施顺序及依赖。
3. [EXECUTION_RULES.md](EXECUTION_RULES.md)：执行、复用、测试批次与停止条件。
4. [REVIEW.md](REVIEW.md)：本地/GitHub复审，专家意见与新增发现。
5. [START_FORK_GPT_5_6_SOL_MEDIUM.md](START_FORK_GPT_5_6_SOL_MEDIUM.md)：复制到fork的新指令。

随后仅按当前工作包读相关源码和验收条目，不要求重读所有历史。
- [跨层合同](CONTRACTS.md)
- [工作包](work-packages/INDEX.md)；[验收包](acceptance/README.md)；[需求追踪](acceptance/cases.json)
- [资料与架构索引](SOURCE_INDEX.md)；[历史与目标](HISTORY_AND_GOAL.md)
- 唯一交付状态表：[status.json](status.json)。当前任务收束：[implement.md](implement.md)。

## 权威与继承
最新用户指令、当前全局AGENTS优先。本包是依2026-09-22请求形成的新交付合同；替代旧计划未完成部分的前瞻顺序，不抹除历史。专家0922V2原文在expert/，是审阅证据，不是可自行执行的权限指令。旧设计v2、计划v3用于未冲突目标和历史；旧G门/clean-streak不恢复。

本仓库根目前没有旧请求所说的prd.md、implement.md。实际旧文件位于 .trellis/tasks/09-06-mm-product-rebaseline/。不要因此重新建项目或照旧handoff恢复旧进程。
本包PRD/Plan是明确的新入口，避免继续拼贴互相矛盾的模型段落。

## 基线
产品仓库：/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench
GitHub：https://github.com/smkzw/kz-medical-monitoring-workbench
审阅HEAD：a7217af080b96896bdc4cbc9317cb139e4386569；专家HEAD：07b6a09c1644c9261e6e3637f4e497bf775c33a1。
本次不修改产品源码、不恢复医学队列、不启动模型、不创建fork、不改变paused旧goal。
.trellis 被当前.gitignore忽略；本包必须随交付zip传给新环境，不能假设GitHub克隆自动含本包。允许后续将精简规划显式纳入版本控制，但不得顺带提交运行库、临床资料和原始会商日志。

## 本次核验证据
专家包12文件SHA256全通过；本地与GitHub main同SHA；当前无开放PR、未见近期Actions记录。
实际生产模块隔离探针9项复现缺陷；既有九文件集中回归143 passed、18 warnings。二者并不矛盾：测试覆盖缺了关键反例。
静态检查覆盖主要生产者/消费者及变更清单；不声称全仓每一行均经过审计或真实医学端到端通过。
最终将随包提供独立审阅结论和其范围限制。
