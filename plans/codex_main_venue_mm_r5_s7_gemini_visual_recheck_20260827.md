# Codex Main-Venue Plan: mm_r5_s7_gemini_visual_recheck_20260827

Date: 2026-08-27
Objective: 以首次接触系统的资深中文医学监察员身份，使用真实Playwright双视口复核当前R5-S7合成离线产品页面的医学内容、风险层级、Patient Journey访视轴、视觉与交互；不得读源码、不得修改产品；按P0-P4输出可复现证据。显式用户路由为pi/google-antigravity/gemini-3.7-flash:high。

## Task Decomposition

1. 只读读取视觉验收合同与 26 行浏览器矩阵。
2. 使用真实 Playwright/Chromium 从 `/monitoring` 深链进入，在 1440×900、1600×1000 两个视口完成矩阵与 T1-T6。
3. 以资深医学监察员视角审阅医学重点、风险层级、Patient Journey 访视轴、八域事件、风险覆盖、证据追溯、中文表达、视觉层级和交互负担。
4. 只在 runner 输出中报告 P0-P4、复现步骤、可见证据、未验证边界；不改源码、不写医学状态。

## Source Packet

- `artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/visual_review_contract_20260826.md`
- `artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`
- 实际运行入口：`http://127.0.0.1:5174/monitoring`
- 仅 synthetic/offline R5 页面；不得读取源码、既有审阅报告或真实项目。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_pi_k3_256k` | `google-antigravity`（用户显式覆盖） | `gemini-3.7-flash:high` | `runs/conference/mm_r5_s7_gemini_visual_recheck_20260827/visual_pi_k3_256k.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 由 runner 记录开始/结束、会话 ID、工具轨迹、终态与显式路由覆盖；仅在终态或 120 分钟 hard wait 返回时检查。

## Codex Verification Checklist

- 复核真实浏览器工具轨迹，而非源码推断或旧截图。
- 核对双视口、矩阵覆盖、P0-P4、中文用户语义和未验证边界。
- Codex 独立复核报告中的关键截图/运行证据后决定是否接受。
