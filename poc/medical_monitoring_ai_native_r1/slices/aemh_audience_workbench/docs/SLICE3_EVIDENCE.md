# R1 Slice 3 Evidence — AE/MH 受众监查看板

## Acceptance scope

本证据只接受隔离合成 R1 Slice 3：将已验收 Slice 1 的 AE/MH 领域结果投影为
项目、中心、受试者、Profile/Timeline、证据和 Query 的只读中文看板。它不代表
产品、真实项目、医学结论、生产运行或框架选型已完成。

## Accepted behavior

- 默认变化优先，不把主风险列表截断为 3–5 条；低风险可由用户主动展开。
- 项目 → 中心 → 受试者 → 原始记录可追溯下钻。
- Profile 与 Timeline 共用同一访视/时间轴和时间窗；正式事实与漏报候选通过
  形状、线型、文字同时区分。
- 候选不计入正式 AE/MH；高危风险因本次数据缺失不得自动结案。
- Query 草稿采用“依据 + 发现 + 行动项”，并通过共享证据定位符绑定到明确风险
  身份；不按受试者猜测，不提供提交、分派或虚构人工待办。
- 完成态显示精确 `6/6`，细节可展开；界面不暴露 workflow 枚举、哈希身份、
  绘图参数、worker/build 名称或 synthetic 控制字段。

## Decisive evidence

- Integrated tests: `121 passed in 28.82s`.
- Browser matrix: Chromium + WebKit × 1280x800 / 1440x900 / 1920x1080 /
  2048x1024; 8/8 pass.
- Screenshots: 40 original-resolution PNGs covering project, center, evidence,
  Profile and Timeline states.
- Browser telemetry: no page error, console error, HTTP(S) request, horizontal
  overflow or applicable design §16.4 defect.
- Exact drawer opener focus restoration passes in both required engines.
- Independent verifier round 6: ACCEPT after 18 tests and live audience-language
  scan; Codex then removed the final wording residual and reran the 121-test gate.

## Payload anchor

- `data/mm_r1_data.js`: 309272 bytes.
- File SHA-256:
  `b7bb8319968982cca1622b7c6b9ee8182eff856dd95dffac2548518866b52d2c`.
- Payload content hash:
  `3b3b62c326b84d9f792ad6bbaeef99605c7a1d72d2ab8e5e3c42e66a4a754929`.
- Source rows: 24.
- Delta counts: current 3, carry-forward 3, resolved 3, all other groups 0.

## Protected boundaries

No accepted Slice 1 source/test, frontend, service, medical-writing, runtime,
real-project, dependency or lockfile path was edited. The browser remains a
local `file://` test mechanism; no product service or port was started.
