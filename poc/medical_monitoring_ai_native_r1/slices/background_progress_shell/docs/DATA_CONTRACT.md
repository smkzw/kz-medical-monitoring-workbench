# Background Progress Shell 数据合同（synthetic/offline）

本切片只消费 `mm_r1.audience_progress.project_audience_progress(store, run_id)`
的返回值。`server.py` 的 `/progress` 端点每次请求都通过 `audience_snapshot`
在同一 WAL 读事务中从 SQLite 重建该投影，不缓存任何 completed/total/percent。

## 受众白名单字段

| 字段 | 内容 |
|---|---|
| `headline` | 总体中文状态语句 |
| `completed` / `total` / `percent` / `progress_text` | 权威数字进度 |
| `status_overview[]` | `{state_label, count}` |
| `stage_progress[]` | `{stage, processed, total, progress_text}` |
| `current_work[]` | `{stage, label, scope_label, target, state_label, elapsed_text, message}` |
| `latest_updates[]` | `{time_text, stage, label, state_label, message}` |

前端 `app.js` 只读取上述字段；未知字段忽略。页面不估算进度，不使用
时间或动画推算数字。

## 禁止暴露

run/node/attempt/provider/model/backend/hash/log/manifest revision 等内部身份
一律不出现在 `/progress` 返回值、页面文字或静态资源中；投影自身已做失败关闭
校验，前端契约测试再逐项断言。

## 运行边界

- 仅 `127.0.0.1:0` 分配的临时端口，测试结束关闭并复验不可连接。
- 数据为虚构合成（`SYN-*` 编号），无真实项目/受试者内容。
- 后台工作由 `BackgroundProgressFacade` 的 daemon worker 在自己的 Store
  连接上推进，页面离开、刷新、多客户端或 facade 重建均通过幂等
  begin/complete 键去重；正常并发时每个工作项只执行一次。
- 若实际工作已返回、但终态写入 SQLite 失败，worker 会记录异常并
  从同一工作项续跑。该故障恢复语义是 `at-least-once`，因此真实
  `unit_step(unit, idempotency_key)` 必须使用传入的稳定幂等身份；本隔离 POC
  不声称外部动作与
  SQLite 之间的事务性 exactly-once。
- 失败（未完成）与受阻（暂时受阻）如实显示，不写成成功。
