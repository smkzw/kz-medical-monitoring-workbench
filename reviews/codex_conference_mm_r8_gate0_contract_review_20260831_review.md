# Codex Conference Review: mm_r8_gate0_contract_review_20260831

Date: 2026-08-31

## Verdict

`PASS_CONTRACT_ONLY`。

接受标签：`CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`。该标签只接受联合合同，不接受 R8-0 readiness、真实资料、真实模型、真实应用、浏览器、§15.4 或医学质量。

## Boundary Compliance

- participant 只读工作区合同/设计/计划，未访问 P1..P5 真实根，未调用真实模型、服务或浏览器，未修改产品源码或医学写作。
- 三轮均复用 session `01a055d7-e931-7000-90f2-720edde28db7`，无 fallback。
- ChatGPT Web advisory 只 dry-run，未启动浏览器；正式 declared executable panel 完成。

## Participant Outputs Reviewed

- Round 1：发现身份复用、零写入策略、digest replay、通知路由、coverage、unknown、lineage、risk/QA severity、incremental 与 clean-streak 合同缺口，结论 `REVISE`。
- Round 2：确认原 P0/P1 已关闭或按用户范围合理降级；新增 N1-N6 窄缺口。
- Round 3：确认 N1/N2/N4/N5/N6 关闭；N3 因通知偏好不依赖模型 binding 而拒绝；无剩余 P0-P3 合同阻断，支持 contract-only accept。

## Conference Panel Review

会商有效识别了实质合同漏洞，也提出了 HMAC、签名、BLAKE3/CAS、Linux 事件监控和 FIFO 锁等超出用户“不做安全设计/测试”与 YAGNI 边界的建议。Codex 只采纳可重放、可失败、可隔离和防过拟合所必需的最小条款；过度设计未纳入。

Hermes 未作为本会商传输或 participant；正式 declared executable panel 为 Pi/cms-router/minimax-m3:xhigh。该记录不把 Hermes 计划文件或历史 session 当作本次接受证据。

## Main-Venue Codex Review

Codex 独立确认：

1. G1 只接受合同；G2-G6 仍需 synthetic readiness；G7 才可首次访问逐项目来源；G8 才可提交真实项目语义给模型。
2. 明确模型名是用户配置要求，不是医学项目硬编码；anti-overfit 扫描针对项目/药物/疾病/量表/风险/列名/布局。
3. 模型和 Codex 的职责没有互换：独立 harness/LLM 生成项目语义候选，Codex 只设计 prompt/schema/validator/coverage/失败语义与验收。
4. 来源零写入、输出隔离、full/incremental、通知、§15.4、P0-P4 与 clean-streak 均 fail-closed。
5. 合同未扩大为安全系统、多人系统、商业化或监管认证设计。

## Codex Independent Verification

- 最终合同：394 行、28176 bytes。
- 最终 SHA-256：`19a855bf51e2ed5cecd3f294cdeed823bc972a01ce84aaa9095a29089e344e74`。
- 定向扫描未发现真实项目路径/名称、疾病/药物专有常量或用户已否定的临时 UI 术语；模型 provider 字符串为用户明确配置要求。
- governed execution audit `ok=true`；conference runner 终态成功、无 fallback。
- 未执行代码测试、服务、浏览器或真实项目，因为本阶段只冻结合同，且这些动作仍被合同禁止。

## Final Decision

`CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`。

下一允许 gate 仅为 G2 `RUNTIME_LAUNCH_READY_SYNTHETIC`。所有真实项目、真实模型、产品浏览器和真实 §15.4 继续禁止。
