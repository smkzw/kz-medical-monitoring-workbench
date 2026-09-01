# R2 Batch C Independent Acceptance — 2026-08-10

## Verdict

`ACCEPT`，仅限隔离、synthetic/offline 的 R2-C 用户功能底座；不代表产品、真实项目、R3+、医学写作子系统或生产就绪。

## Frozen Snapshot

- R2 Python 内容清单：`69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`
- R1 只读基线：`ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`
- R2-C 聚焦回归：`105 passed`
- R2 全量回归：`598 passed`
- 内存编译：33 个 Python 文件
- 无 `__pycache__` / `.pytest_cache`；8911 无监听。

## Accepted Functional Contracts

1. SQLite 保存、关闭、重开后，当前发布、历史、来源/快照/事实/风险/基线引用保持一致。
2. 同一保存键的并发重复提交产生一次提交与一次 replay，不重复历史、不暴露 SQLite 原始冲突。
3. 当前发布只解析为已登记、完成、可读且 embedded contract 与 revision/envelope/reference 一致的内容寻址制品。
4. revision、保存键、请求摘要、ledger scope/result、业务历史与发布历史逐项对账；导入不接受缺失、重复、覆盖式或交叉绑定状态。
5. 迁移要求全新数据库目标与空制品目录；导入使用非覆盖 INSERT，备份/恢复与回滚保持当前发布和历史。
6. R1 adapter 使用 SQLite `mode=ro`，项目与 snapshot 均必须是 synthetic；fact 使用 `(run_id, fact_hash)`，risk 使用 `(kind, object_id, version)`，不静默合并。
7. CanonicalFact 仅可由权威 bundle 重建，并逐项核对 13 个声明的身份/来源字段。

## Independent Review History

- 原生 `gpt-5.6-luna/max` 能力探测被当前 App 明确拒绝，按规则使用 Luna CLI compatibility route。
- Luna 同一会话 `019fe9a4-4324-7940-bfe5-6fa98056f78d` 连续三轮返回 VETO，并给出可复现的功能一致性缺陷；Codex 逐轮做有界修正和回归。
- 同会话恢复额度耗尽后，按声明路线切换到 fresh-context `pi/cms-smk/cms-model/high` 独立复核；其报告 `runs/conference/medical_monitoring_r2_c_acceptance_20260810/independent_pi_final.md` 返回 `ACCEPT`，未触发后续 fallback。

## Non-blocking Limits

- 同一个 `R2Store` 对象不是跨线程共享对象；并发合同为每个调用方独立连接。
- 全新数据库的首次 schema 初始化应由单一启动路径完成；多线程同时首次初始化属于后续 runtime 集成事项。
- 这是用户功能所需的数据一致性底座，不新增或声称系统安全、访问控制、电子签名或攻防能力。

## Next Safe Action

冻结 R2-A/B/C 为不可变已验收历史；进入 R3 Study Intelligence 与异构 listing，在新的隔离 namespace 中实现资料分类/版本/范围、方案/IB/外部证据结构化、listing 结构画像、语义 mapping、日期/单位/编码/部分日期与 snapshot diff。产品、医学写作、真实项目和 8911 继续冻结。
