# Codex Main-Venue Plan: mm_r6_runtime_slice_04_acceptance_20260828

Date: 2026-08-28
Objective: 独立审阅 R6 第四纵切 synthetic/offline ModeContract、ModeOutput、daily 四输出与结构化 Query 草稿是否满足 slice-04 合同和权威 §8/contract.json；重点寻找 Run/mode/carry-forward、output identity/eligibility、authority/numeric、Query 依据+发现+行动项及 sent/closed/PD 边界失败开放；核对 460 回归与 9 宫格。不得修改文件或接受产品/真实项目/医学范围。

## Task Decomposition

1. 独立审阅冻结合同与当前实现，寻找失败开放。
2. 对可复现缺陷作最小共享根因修订并增加阴性测试。
3. 运行 focused、full POC、normal/-O/-OO × hash seed 9 宫格。
4. 在原参与者 session 针对性复核修订后的当前字节。
5. Codex 核对边界、SHA、receipt，完成限域验收。

## Source Packet

- slice-04 合同；权威 §8 与 contract.json。
- 当前 `mode_output.py`、`test_mode_output.py`、runtime receipt。
- slice-01 oracle、slice-02/03 邻接收据、医学写作 aggregate 与端口停止证据。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r6_runtime_slice_04_acceptance_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r6_runtime_slice_04_acceptance_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Pi 初轮 151.876 s，原 session follow-up 56.602 s；completed，未 fallback。
- Grok 初轮 366.123 s，原 session follow-up 132.641 s；completed，未 fallback。
- 所有输出均在终验前纳入；慢响应按 7200 s hard wait 处理，没有轮询催促或重开 session。

## Codex Verification Checklist

- [x] 初轮参与者输出与独立证据均已审阅。
- [x] D1-D7 与 malformed 输入缺陷已修订并由原 session 复核。
- [x] focused 96 passed；full POC 473 passed。
- [x] 9 宫格 9/9，每格 96 passed。
- [x] receipt SHA 与磁盘一致；slice-03 runtime SHA 未变。
- [x] 8911/5174 停止；未使用真实项目；医学写作边界未变。
- [x] 明确不接受产品、真实项目、医学结论和后续深层输出。
