# Codex Conference Review: mm_r8_gate3_notification_contract_review_20260831

Date: 2026-08-31

## Verdict

`PASS_AFTER_SAME_SESSION_REVISIONS`.

最终独立结论：`ACCEPT_G3_CONTRACT_V0_3`，P0/P1/P2/P3/P4=`0/0/0/0/0`。

## Boundary Compliance

- 会商只读取授权工作区内的 G0/G2/G3/System Design/实施计划及两处 UI 缺口证据。
- 三轮均未修改文件，未启动产品服务、端口、浏览器或产品模型，未访问真实项目或医学写作子系统。
- runner 持久化了三轮输出和 stdout；同一 Pi session `01a05623-1bec-7000-af0c-b1250077b9a4`，无 fallback。

## Participant Outputs Reviewed

- Round 1：`REVISE_G3_CONTRACT`，对 Path A 原文、双通道、终态/可访问双门、导航绑定、投递证据、§15.4 清单和 G6 binding 提出阻断性修订。
- Round 2：确认 v0.2 的五项 P1 已全部关闭；仅保留“`revoked | re_admission_required` 不得新建通知事实”一项 P2。
- Round 3：重开 v0.3 并逐项确认上述发现、取消/中断说明入口、四类非终态零触发和统一项目文案已关闭，返回全零。

## Conference Panel Review

- 接受：G0 Path B 仅表示用户明确接受仅页面内状态；应用内持久记录只是 Path A 的降级/对账面。
- 接受：通知事实完整绑定 `project_ref + admission_id + run_id + terminal_status + terminal_revision`；通道结果不改写运行终态，点击只导航。
- 接受：原样保留 `partial/final_partial/truncated/failed/timed_out/cancelled/interrupted/blocked`；`analysis_complete` 只是上游 `complete` 在结果可访问后的通知投影。
- 拒绝：会商提出但上位合同明确排除的签名/密钥系统，以及无依据的任意 100 次重放门槛。
- 拒绝：在用户查看型看板上增加“人工复核未完成”待办式标记；合同已明确“分析完成不等于医学正确”。

## Main-Venue Codex Review

- Codex 逐项重开权威合同和当前草案，没有把 participant 的信心当作接受证据。
- 对每轮发现分别处置：可追溯到 G0/System Design 的要求落入合同；签名/密钥、任意重放次数与待办式人工复核标记因超出冻结边界被拒绝。
- 本会商由 Pi 路由执行，未经 Hermes 转发；Codex 保留最终接受权。

## Codex Independent Verification

- 重开 G0 §§3.3、8.2–8.4、9、13、15，G2 接受记录，System Design §§15.1–15.4，以及 G3 v0.3 全文。
- 非 LLM 结构校验：Path A 双信号、九类通知终态、四类能力状态、双硬门、导航无启动副作用、§15.4 十三项清单、G6 synthetic binding 与 P0/P1/P2 门齐全。
- 最终合同 SHA-256：`97fba80a9d53901ac2c2c21abc828b22c1620b133347e58c0b1739b326026fdd`。
- G2 synthetic profile/code 锚点：`synthetic_manifest.py` SHA-256 `c7928ac0625e7acedc609321f8e33c25cd06423b989aeb8a17f655862aaae001`；release manifest SHA-256 `80970fa97376a563b43607215436a1ac0bacb28bb07031545c0391610a246440`。
- 8911/5174/8984 均 `connect_ex=61`，保持停止。本阶段不需要也不允许 browser/PPT/PDF/image 验收。

## Final Decision

`ACCEPT_G3_CONTRACT_V0_3`。冻结 G3 `NOTIFICATION_DECISION_LOCKED`，只解锁 G4 synthetic/offline 通知 seam 与 §15.4 程序；G5–G8 继续关闭。
