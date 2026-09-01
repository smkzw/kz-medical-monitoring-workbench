# 医学监查 R8 G3 离页通知决策接受记录

日期：2026-08-31  
状态：`ACCEPT_R8_G3_NOTIFICATION_DECISION_LOCKED`  
范围：只接受 synthetic/offline 通知决策合同；不接受真实通知、产品实现、用户已看到、真实项目/模型/浏览器、医学质量或 §15.4 完成

## 接受对象

- 合同：`reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`
- 合同 SHA-256：`97fba80a9d53901ac2c2c21abc828b22c1620b133347e58c0b1739b326026fdd`
- G2 synthetic profile/code 锚点：`deploy/medical_monitoring_local/synthetic_manifest.py` SHA-256 `c7928ac0625e7acedc609321f8e33c25cd06423b989aeb8a17f655862aaae001`
- G2 release manifest 锚点：`deploy/medical_monitoring_local/release_sources.json` SHA-256 `80970fa97376a563b43607215436a1ac0bacb28bb07031545c0391610a246440`

## 冻结决定

1. 选择 R8-0 §8.2 Path A：离页运行完成信号与失败信号均必须真实可见。
2. 应用内持久通知记录只是 Path A 的降级/对账面；它不是 G0 Path B，也不单独满足离页可见验收。
3. 唯一通知事实绑定 `project_ref + admission_id + run_id + terminal_status + terminal_revision`；双通道共享同一 revision、中文模板与导航意图。
4. 上游原始终态不折叠；`analysis_complete` 仅是 `complete + 结果可访问` 的通知投影。
5. 通知通道证据不改写运行终态，不由平台接受 API 推导用户已看到。
6. 点击只导航到唯一已有运行；不启动、重试、续跑或取消分析。
7. `revoked | re_admission_required` 不得新建通知事实；既有记录仅作历史证据，不用于打开当前结果。

## 独立审阅

- governed conference：`mm_r8_gate3_notification_contract_review_20260831`
- 路由：`Pi/cms-router/minimax-m3:xhigh`，同一 session `01a05623-1bec-7000-af0c-b1250077b9a4`，三轮，无 fallback。
- Round 1 `REVISE_G3_CONTRACT`；Round 2 确认所有 P1 关闭、仅余一项 P2；Round 3 `ACCEPT_G3_CONTRACT_V0_3`，P0/P1/P2/P3/P4=`0/0/0/0/0`。
- conference validation 与 Codex review/metrics gate 必须与本记录一并保留。

## 非 LLM 验证

- 合同结构校验覆盖 Path A 双信号、全部终态、四类能力状态、双硬门、导航无启动副作用、§15.4 十三项清单、G6 synthetic binding 与 P0/P1/P2 门。
- 8911/5174/8984 均 `connect_ex=61`，保持停止。
- 未修改产品源码，未启动产品服务/浏览器/模型，未访问真实项目或医学写作子系统。

## 下一安全动作

进入 G4 `SYNTHETIC_15_4_PROCEDURE_READY`：先冻结最小实施分解，再在 `deploy/medical_monitoring_local` 的 synthetic/offline 边界内实现通知 outbox/降级记录/只导航意图及 R8-0 §8.3 十三项程序。不启动产品服务、浏览器或模型，不访问真实项目；G5-G8 保持关闭。
