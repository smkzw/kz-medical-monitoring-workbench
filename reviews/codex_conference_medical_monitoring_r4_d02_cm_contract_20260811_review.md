# Codex Conference Review: medical_monitoring_r4_d02_cm_contract_20260811

Date: 2026-08-11

## Verdict

**ACCEPT — 仅冻结隔离、合成 R4-D02 CM 用药合理性、适应证与禁限用药实现合同。**

- 冻结合同：`reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`。
- 状态：`FROZEN_R4_D02_CONTRACT_V1`。
- SHA-256：`adf6150ecb25886ac4f31123cc639ad13c3530812bfe1607958b9d68e68e4cd7`。
- 本结论不接受 D02 代码、产品/R5、真实项目/词典/provider、浏览器界面、正式 PD 或临床结论就绪。

## Boundary Compliance

- 本轮只修改任务合同和本任务 `context/plans/prompts/runs/reviews/metrics/logs`；未修改 R4 产品实现、冻结 R1/R2/R3、医学写作子系统或真实项目。
- 未启动服务、8911、浏览器或五个真实项目；未做系统安全设计/测试。
- 参与者均为只读审阅，不互读输出；Codex 逐项回到冻结共同矩阵和当前 D01 公共面裁决。

## Participant Outputs Reviewed

1. 医学路线 declared `pi/alibaba/qwen3.8-max:xhigh`，北京日间 effective `pi/cms-smk/cms-model:high`：首轮 session `019fee42-0121-7000-8f86-d7ed22f72e7c` 返回 `ACCEPT_WITH_GAPS`，发现 indication subtype 重叠、role boundary/not-evaluable 冲突、笼统适应证、缺失标签、priority/Query/跨域边界问题。
2. 医学差异复核因 runner 的 Qwen 日间重写记录为新 effective CMS session `019fee4e-e04e-7000-aa56-77ee0905f942`，返回 `ACCEPT_WITH_GAPS`；Codex 随后在该实际 CMS session 原会话继续终末微调核对，最终 `ACCEPT`。
3. 工程 Grok Build session `ae34e41d-6171-48a3-9528-90c09081344d` 首轮 `cancelled` 且只有过程文字，不计结论；同会话 round 2 `VETO`，准确发现 stable-core/lineage 混写、生命周期 D01 类型耦合、复方 unresolved expected-set 漏项和跨域所有权缺口；round 3 对 v1.1-rc1 返回 `ACCEPT_WITH_GAPS`，确认 I-1-I-10 已关闭并提出 G1-G6 精度项。

## Conference Panel Review

- 医学与工程路线一致支持：缺失/笼统适应证必须保持 not-evaluable/coverage gap；明确研究期治疗且缺事件记录时 subtype 2 优先；role 单纯缺失不属于 boundary。
- 复方按成分/规则拆分，unresolved component 必须进入 expected-set；episode 汇总只能显示并存状态，不能覆盖 not-evaluable。
- D02 风险身份拆为 stable classifier 与 versioned scope/lineage；普通快照/revision 不进入稳定事件键，lineage 变化走 supersede，竞争 binding 走 identity_ambiguous。
- D02→D01 只传 `CrossDomainEvidenceRef`；两域可共享来源和关联显示，但不共享 candidate/risk/Query/lifecycle，也不因同源静默合并不同风险身份。
- Query 保持中文“依据＋发现＋行动项”，PD 只请求有权方核实；CM journey 为独立区间轨道和具体风险标签。

## Main-Venue Codex Review

- Codex接受并收口医学 B1-B4/N1-N8 与工程 I-1-I-10；未采用“共享来源即跨域风险去重”的过度建议，保留不同 domain risk identity，只允许 evidence_ref 分组显示。
- 工程 round 3 的 G1-G6 已全部写入冻结文本：Protocol/UnitEvaluation 分层、中性 identity/priority 常量、ingredient-resolution 金标 token、canonical cross-domain hash、L1/L3 not-evaluable 分离、IP-only 零 CM 单元。
- 医学方唯一残留的 unknown-priority 对齐措辞已写入 §9.1，并在相同 effective CMS session 终末核对为 `ACCEPT`。
- 共享 `contracts.py/lifecycle.py/aemh.py` 被明确设为单 owner 串行前置；D01 224 项保持通过后才能并行 D02-owned 文件，禁止复制第二个生命周期 adapter。

## Hermes/Delegation Review

本会商未使用 Hermes 参与者。guard/runner 只负责既定 Pi/Grok 路线、日间替换、会话恢复与报告持久化；外部模型意见均为独立反证，不能替代 Codex 对冻结矩阵、实际合同文本、哈希与边界的最终验收。

## Codex Independent Verification

- 冻结合同状态、30 个合成 challenge、六个 positive subtype 用户标签、PD 边界、结构协议、两层身份、跨域引用和 serial ownership 均由 Codex逐段复读。
- 冻结共同矩阵 SHA-256 保持 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`。
- 已接受 R4-D01 cache-excluded 摘要保持 `f100a0344db27f1d6e404a8b1fdd88a849dd43e5f0996a2e9e609b1c42546550`；本合同会商未改源码。
- 8911 无监听。
- 本轮是合同冻结，不运行代码/浏览器/真实项目测试；这些属于随后 D02 execution package 的退出门，未被本结论冒充完成。

## Final Decision

冻结 R4-D02 合同并关闭合同会商。下一安全动作是按照 §13 先串行完成公共结构协议适配并证明 D01 全量不回归，再实现 D02 CM engine/projection/fixtures 和 challenge 1-30；仍只在隔离合成 R4 内，不进入 R5 或产品/真实项目。
