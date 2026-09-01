# 摘要异步修复 Codex 在途源码审阅

状态：Worker仍在运行；以下是只读审阅反例，不是对在途实现的最终判定。完成后须
以Worker最终源码重新复核。

## P0/P1候选

1. **Chunk claim没有所有权校验到提交。** `_claim_chunk()`生成并写入
   `claim_token`，但只返回布尔值；`_complete_chunk()`和`_fail_chunk()`的UPDATE
   不带`claim_token`/`status='running'`条件，也不检查`rowcount`。旧Worker即使租约
   已过期并被新Worker接管，仍可覆盖新Worker结果。
2. **租约短于真实模型调用且无chunk heartbeat。** 默认
   `claim_timeout_seconds=360`，而既有真实MY009调用约11分钟。Chunk执行期间没有
   续租线程；启动恢复或第二进程会在第一次调用仍活跃时重领同一chunk，造成重复
   调用、费用/时延增加和竞态写入。
3. **多Worker跳过live chunk后可能错误进入merge。** Worker遇到无法claim的chunk
   直接`continue`，循环结束后即执行merge；若该chunk仍由另一Worker运行，本Worker
   可用不完整done集合提前merge并提交。
4. **最终merge未要求done数量等于chunk_total。** `_merge_chunks()`只要求至少一个
   done row，未断言索引0..N-1全部完成、无重复、无failed/running/pending。
5. **冷恢复测试不足。** 当前`test_crash_after_chunk1_then_recovery_without_replay`
   只断言`requeued >= 0`，没有等待新实例完成、没有断言chunk1调用次数不增加、没有
   验证最终结果/进度/来源。它在未实现真正恢复时也可能通过。
6. **并发claim测试有竞态假设。** 测试先`start_job()`，后台线程可能已经claim或完成
   chunk，再由测试直接调用`_claim_chunk()`；并未构造确定性的两个并发事务或屏障。
7. **过期租约测试媒体类型拼写错误。** 使用
   `application/vnd.openxmlformats-officedocumented.wordprocessingml.document`，
   可能在到达租约断言前由文件类型校验失败。
8. **失败关闭被best-effort吞掉。** 确定性anchor materialization用宽泛
   `except Exception: pass`，然后注释称验证会捕获，但本函数没有显式运行与原整文
   一致的来源忠实度验证；需证明后续model validation能发现锚点缺失，否则应失败。
9. **恢复的source元数据被伪造/丢失。** `recover_stale_jobs()`重建source时将
   `actual_size=1`、parser/extraction revision为空、角色/适应症强制matched，未从
   持久字段恢复原始校验状态和warning。恢复后结果可能与首次执行不等价。
10. **取消响应返回错误job_id。** `cancel_job()`仍返回`idempotency_key`而不是数据库
    中持久`job_id`，违背一个稳定公开任务身份。
11. **job_id作用域不完整。** 当前job_id只由`project_id|content_sha256`决定；同一
    项目、同一文件、不同expected indication/文件名/任务请求会共享公开ID，但DB和
    状态路由仍以idempotency key寻址。需明确公开ID唯一性并统一所有status/result/
    cancel/recover路由。
12. **progress写入可回退。** 多Worker均可调用`_update_progress()`，没有基于已提交
    done chunk计数重算，也没有monotonic WHERE条件；较慢Worker可把较新进度写回旧值。

## Worker结束后的最小验收

- claim必须返回token；heartbeat按远低于lease的周期续租；complete/fail/cancel均以
  token和状态CAS，rowcount不为1即丢弃旧结果。
- merge只在全部索引done后执行；不是全部done则退出或等待，不得提交部分结果。
- 两个真实Service实例、同一SQLite文件、屏障Provider：证明只有一次调用，过期后
  只有新owner能提交，旧owner迟回被丢弃。
- 冷恢复必须终止旧执行上下文或用可控假崩溃：新实例完成、已完成chunk调用数不变、
  最终结果和来源元数据一致。
- 取消、恢复、幂等重放和所有状态接口返回同一persisted job_id。
- provider输出、anchor materialization、deterministic merge之后运行完整来源忠实度
  gate；不能以Pydantic结构校验替代精确来源校验。
