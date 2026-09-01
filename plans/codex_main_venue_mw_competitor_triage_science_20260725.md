# Codex Main-Venue Plan: mw_competitor_triage_science_20260725

Date: 2026-07-25
Objective: 独立审阅UC、CRSwNP、D017真实ClinicalTrials.gov竞品分诊结果的适应症、分期、药理干预、公开Protocol/SAP价值和误纳误排风险；不得替代产品独立AI，不得修改生产状态

## Task Decomposition

1. 冻结UC、CRSwNP、D017各自的ClinicalTrials.gov快照、产品独立AI v12运行及job result。
2. 两个参与者独立逐条检查适应症关系、分期、药理干预、公开Protocol/SAP价值、误纳误排和
   来源定位；不得读取彼此输出，不得写生产状态。
3. 项目覆盖的Qoder会商角色读取两份参与者输出和同一证据包，汇总冲突、阻断项、可安全
   确认项和需要Codex复现的问题。
4. Codex回到真实快照、产品运行、ClinicalTrials.gov定位符和确定性脚本复核所有高影响
   结论；外部模型意见只作审阅证据，不替代产品AI或医学确认。

## Source Packet

- 冻结目录：
  `records/active_slices/medical_writing_production_rebaseline_20260722/evidence/three_project_competitor_triage_20260725/`
- 必需文件：
  - `uc_snapshot.json`、`uc_v12_run.json`、`uc_v12_job_result.json`
  - `crswnp_snapshot.json`、`crswnp_v10_run_rejected.json`、
    `crswnp_v12_run.json`、`crswnp_v12_job_result.json`
  - `d017_snapshot.json`、`d017_v10_run_pre_version_gate.json`、
    `d017_v12_run.json`、`d017_v12_job_result.json`
  - `crswnp_v12_acceptance.json`、`d017_v12_acceptance.json`、
    `SHA256SUMS.final`
- 代码/确定性边界：
  `services/api/app/medical_writing_competitor_triage.py`、
  `tests/test_medical_writing_competitor_triage_crswnp.py`、
  `scripts/qc/d017_competitor_triage_v5_acceptance.py`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_competitor_triage_science_20260725/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_competitor_triage_science_20260725/general_opencode_deepseek_flash.md` |

北京时间已过2026-07-25 08:30，`general_aishuo_cms`使用
`Hermes/aishuo/cms-model`。两个参与者并行开始，各自只进行一次完整首轮；只有发现具体
缺失证据、矛盾或截断时才在同一session发送合并后的定向补充。

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | existing QoderVIP `qodercli` | `qwen3.8-max-preview` | `runs/conference/mw_competitor_triage_science_20260725/general_chair_grok45.md` |

该角色按项目级Qoder覆盖规则替代原Grok chair。必须复用
`/Users/smkzw/Downloads/QoderVIP/start.command`启动的现有可见`qodercli`会话，通过
AppleScript直接输入，不得无头调用或启动替代进程。若无法确认会话lineage/model，按
项目规则回退原Grok及后续链路。

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 参与者首轮：内部轮次预算128，外部硬等待120分钟。
- chair首轮：内部轮次预算192，外部硬等待240分钟。
- 不发送“进度如何/继续”等状态消息；通过进程退出、会话、runner输出和完成标记判断。
- 对每个角色记录开始/结束时间、provider/model/session、首轮是否完整、是否有针对性续轮、
  fallback、纳入或拒绝原因。

## Codex Verification Checklist

- [ ] 三项目v12运行均为`review_ready`，provider/model/prompt/schema身份正确。
- [ ] 三项目快照与运行哈希、候选覆盖数和来源定位可复现。
- [ ] CRSwNP关键混合人群、拼写错误、明确无息肉、AFRS和非药理边界逐条复核。
- [ ] D017 v12确定性接受脚本通过，CRSwNP规则未污染PNH。
- [ ] UC宽检索中的异适应症、非药理和仅文件可用但临床不相关项被识别。
- [ ] 参与者和chair未修改生产状态、未替代产品AI、未把会商文字写入语料库。
- [ ] Codex复现所有阻断项后才决定是否确认篮子。
