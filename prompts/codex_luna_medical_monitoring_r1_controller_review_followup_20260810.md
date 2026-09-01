请在同一审阅会话中对上轮 VETO 做增量复审。仍为只读，不得修改文件，不得启动服务/8911/真实 provider/真实项目。

上轮三个否决项已按传播路径修订，请不接受文字说明，直接检查当前文件：

1. 并发 assignment 冲突：
   - `Store.put_domain_object` 已在 `BEGIN IMMEDIATE` 内重读 latest；
   - `capability_work_assignment` 与 `adapter_raw_output` 均是特殊不可变 kind，已有对象不得产生 v2；
   - 新增两 SQLite 连接、同 attempt/不同 request 的真并发测试，验证只有一个 v1 且可恢复。
2. claim gate：
   - `bind_capability_attempt_to_work_unit` 已明确拒绝 `declared` attempt；
   - 新增 declared 未 claim 不能伪造 running 的 Store 负向测试；
   - terminal/interrupted replay 仍可绑定，因为其审计生命周期必定包含既往 claim。
3. retry/resume：
   - failed/blocked work unit 现可在严格 `continued_from` 链下通过 `work_unit_attempt_bound` 重开为 running，清理当前终态快照但保留审计历史；
   - 权威投影已支持 terminal → retry-running → terminal 的事件序列；
   - controller 新增 `resume()`，先从旧 journal 重建并校验同一 input/version/profile，预注册新 assignment，再调用 runtime.resume 与原 observer；
   - 新增 partial → failed → continuation running → passed 和 interrupted → blocked → continuation → passed 测试。

主会场当前确定性锚点：
- controller + authoritative progress + capability runtime：`100 passed`
- R1 全套：`271 passed`
- 改动范围 Ruff：`All checks passed!`
- compileall 通过；8911 无监听。

请完整复查上轮 P0 和两个 P2 是否真正消除，并检查新的 terminal → retry 状态投影、幂等回放和并发交错是否引入新 P0-P4。请返回 `VERDICT: ACCEPT` 或 `VERDICT: VETO`，按 P0-P4 列出问题、验证范围、未验证范围和当前关键文件 SHA-256。
