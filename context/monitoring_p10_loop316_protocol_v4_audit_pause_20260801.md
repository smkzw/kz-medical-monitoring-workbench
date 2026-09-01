# P10 LOOP 3.16 / RUX 协议 v4 科学审计无损暂停检查点

时间：2026-08-01 00:30 CST  
Goal：保持 active；本文件只记录细分任务暂停边界，不代表 P10 上线完成。

## 当前结论

- RUX V16 mapping：`175/175 completed`；175 个候选仍全部 proposed；正式候选审计
  `0 errors / 73 warnings / 8 observations`；只读内存投影为
  `pass_with_warnings / activate_restricted`。未 adopt、未组装、未确认、未激活。
- RUX 协议 v4：`2 candidate_review / 6 failed / 0 running / 0 queued`。
- 8 个协议候选仍全部 `proposed/pending_user_confirmation`；本轮零候选决定。
- 协议科学门未通过，MY009 未启动且不得启动。

## 协议候选审计

- 一个失访候选可在保留“如可能 3 次电话”等限定并隔离 AE 随访尾项后继续人工复核。
- 其余候选需要至少一种处理：原子拆分、主题重路由或严格限域。
- 主要主题错位：
  - IP 发放/回收/称重不能留在提前退出，也不能落入 CM；
  - 伴发事件/缺失值处理必须进入统计/estimand；
  - SAP 锁库前定稿和缺失数据程序必须进入统计/SAP 治理。
- 六个失败响应不可自动捞取。它们只证明 provider 输出未满足表头、同行或列表闭合，
  不能证明方案无条款，也不能作为候选来源。

完整审计：

- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.md`
- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_protocol_v4_candidate_audit.json`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v4_audit_20260731.md`
- `reviews/codex_monitoring_p10_loop316_protocol_v4_audit_20260731_review.md`

## 下一安全动作

恢复后不要启动 8911、5174、MY009 或 provider job。先做一个离线有限代码切片：

1. 为协议结构 evidence 定义 typed bundle identity 和 repair lineage。
2. 只允许从同一冻结 packet 补精确表格行+表头路径或列表祖先标题。
3. 不自动补全部同级列表项；claim-bearing item 必须由 provider 原始选择或明确的
   whole-list identity 支持。
4. 原始语义支持 ID 与自动结构上下文 ID 分栏保存；自动上下文不得成为唯一语义锚点。
5. 候选文本、主题、actor/action/condition、极性、模态和 hash 不变。
6. 补齐后继续运行全部现有医学门；50-ID 上限按补齐后计算，歧义、冲突或超限失败关闭。
7. 先完成负向测试和 Codex review，再决定是否只对一个失败主题做 canary；不得原样
   retry 六项，不得批量重发。

只有 canary 经 unchanged validators 通过并完成新的只读科学审计后，才重新评估 RUX
协议门。MY009 仍在该门之后。

## 运行与回滚边界

- 8911：已优雅停止，listener=0。
- 5174：listener=0。
- 停服后备份：
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pause_loop316_protocol_v4_audit_20260801_0030CST/`
- 21 个 SQLite；18 个非空库全部 `PRAGMA integrity_check=ok`；3 个空库按字节保留。
- 备份 `medical_monitoring_ai.sqlite3` SHA-256：
  `46d8f2411da6612860e36bd6f4e9d0e9c36aea357ac4e2a788bdfe608bb2e7aa`。

本轮没有修改产品源码或医学写作业务文件，没有运行 pytest，没有启动前端。

