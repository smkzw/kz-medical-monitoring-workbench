# Codex Conference Review: medical_monitoring_r4_d03_stable_acceptance_20260811

Date: 2026-08-12

## Verdict

**PASS / ACCEPT（仅当前 synthetic/offline R4-D03 快照）**。

## Boundary Compliance

- 只审阅冻结 D03 合同、R4-D03 源码/测试、D02 相邻导出与任务记录；未访问任何真实项目。
- 未启动产品、服务或 8911；最终检查确认 8911 无监听进程。
- 未触碰医学写作子系统；未实施 R5 UI、真实项目或产品验收。
- 参与者只读审阅。Codex 在独立验收前完成两项有证据的最小纠偏：核算单位统一换算、派生 assignment 非歧义时间窗绑定。
- 会商经 Hermes workflow guard 管理上下文、prompt preflight 与 review gate；Codex 保留最终接受权。

## Participant Outputs Reviewed

1. `general_pi_qwen38` 的声明路由未形成可用 Qwen 会话，按已声明链路落到 Pi/OpenCode Go DeepSeek V4 Flash；round 1 以 `REVISE` 发现发放、回收和已记录给药量跨单位直接比较，round 2 在同一 session `019ff16f-baf1-7000-9e95-c8adcd19acdd` 复核后 `ACCEPT`。
2. Grok Build 原 session `bc72212c-ee90-4b3e-a907-47034909f356` 两次恢复仍未取得可执行证据；round 3 与 Cursor fallback 因无 Shell 证据均为 `BLOCKED`，不能作为接受依据。Cursor 的静态审阅仍有效指出派生 assignment 未校验时间窗，Codex 随后从合同和源码独立证实并修复。
3. 原生 `gpt-5.6-luna` probe 被当前 App 工具明确拒绝，未静默改用 Sol/Terra；按全局规则使用 CLI compatibility fallback。隔离 session `019ff190-22aa-7f51-9de1-f5863f67ab6a` 对修复后稳定快照独立执行全部门禁并给出 `ACCEPT`。

## Conference Panel Review

- 第一轮有效否决阻止了跨单位研究药核算误报；转换缺失现在 fail closed，challenge cases 50/51 分别证明换算后闭合与无依据时不可评价。
- 第二个有效挑战阻止了仅凭 subject+site+role+phase 绑定错误治疗窗口。当前派生绑定要求 episode 完整落入唯一 assignment 计划窗口；明确不相交者排除，部分日期、缺失/持续中端点、exact+unresolved 或多 exact 候选均不能绑定。
- 早期 Qwen `ACCEPT` 发生在时间窗纠偏之前，因此只作为单位换算复核证据，不被冒充最终快照接受。最终接受以 Luna 新鲜隔离验收和 Codex 独立验证为准。
- Cursor/Grok 的 `BLOCKED` 是审阅环境没有可执行 Shell，不是产品缺陷；其静态发现已被吸收，但其 verdict 未被改写。

## Main-Venue Codex Review

Codex 对冻结合同 §4 的“subject＋site＋role＋phase＋非歧义时间窗”与 `resolve_episode_assignment` 逐行比对，确认原实现漏掉时间窗。最小修复位于 `poc/medical_monitoring_ai_native_r4/src/mm_r4/ip.py`，回归位于 `poc/medical_monitoring_ai_native_r4/tests/test_ip_slice.py`。未修改 D02、投影、fixture、root exports 或医学写作代码。

用户可见语义继续满足既定边界：六类研究药风险使用具体中文名称；`accountability_proxy` 显示“按发放/回收核算”，不宣称“实际服药天数”；三段式 Query 仍是待核实草稿；Patient Journey 使用给药、发放、回收、调整、医学事件、疗效和访视等类型化事件，不退化成“已记录事项/风险项”。

## Codex Independent Verification

- `test_ip_slice.py -k AssignmentBinding`: **12 passed**。
- R4 全量：**681 passed**；R2：**598 passed**；R3：**339 passed**。
- `python3 -m ruff check ...`: **All checks passed**；`compileall`: exit 0。
- case 11 projection payload SHA-256：`f575a16827f25595094d0b104b34656a89e01d75bdd057fda6a7a499495429aa`；含“按发放/回收核算”，不含“实际服药天数”。
- 冻结 11 个合同/源码/测试文件在验证前后 SHA-256 一致；D02 `cm.py`/`cm_projection.py` 哈希未改变。
- Luna 另行执行 35 项核算、代理文案、typed join、root export、D01/D02 相邻聚焦测试，并用对抗 probe 证明 missing/ongoing/partial/multiple/exact+unresolved 绑定不会产生 positive/negative。
- `lsof -nP -iTCP:8911 -sTCP:LISTEN` 无输出，8911 保持停止。

## Final Decision

接受当前 R4-D03 研究药暴露、依从性、核算、给药处置关系及 renderer-neutral Patient Journey 纵切。该结论只覆盖 synthetic/offline POC 与列明回归，不代表 R5 前端、真实项目、产品或商业化验收。下一步可按实施计划进入下一 R4 风险域或 R4 聚合收口；不得把本结论扩张到真实数据运行。
