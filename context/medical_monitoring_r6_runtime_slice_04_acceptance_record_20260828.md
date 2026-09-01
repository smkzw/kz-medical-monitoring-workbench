# R6 runtime slice-04 acceptance record

Date: 2026-08-28

## Decision

`ACCEPT_R6_RUNTIME_SLICE_04_SYNTHETIC_OFFLINE`

接受范围仅为 synthetic/offline：三模式 ModeContract、Run gate、通用 ModeOutput、daily 四输出、结构化 Query 草稿及其失败关闭边界。

## Final evidence

- focused `tests/test_mode_output.py`: 96 passed。
- full POC: 473 passed。
- normal / `-O` / `-OO` × `PYTHONHASHSEED=0/1/42`: 9/9，每格 96 passed。
- `mode_output.py`: `38076dd337fd2bf10923a7245df6128ed25712823c66a74789023e61d4d1a514`。
- `test_mode_output.py`: `304f5e49ff6258944a0d22be006f5a0f4a8343a7c34fe51cfeb63e3c91b3d642`。
- 医学写作边界：542 files，aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911/5174 保持停止；未使用真实项目。

## Corrective history

初轮会商拒绝“仅因 460 tests 绿色即接受”。Codex 关闭了入口证据与资格默认、承接来源、锁定身份、数字语义、变化来源、Query identity/scope 与畸形输入失败开放；最终由原 Pi/Grok session 针对性复核，均判定 CLOSED。

## Explicit residuals

- pre_lock/post_lock 深层 payload 生成器尚未在本纵切实现。
- Agent Harness 与模型路由尚未接入；后续默认目标为 `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并保留 `deepseek/DeepSeek V4 flash:max` 接入能力。
- 不接受产品 runtime、真实项目/报告、医学/监管结论、Query 外发、PD 登记/关闭、视觉界面或 R6 总体完成。

## Next safe action

按 R6 计划定义下一独立纵切；仍只用 synthetic/offline fixture，保持 8911/5174 停止并保护医学写作子系统。进入 Agent Harness 时先冻结 provider/model adapter 合同，再分别验证默认 MTPLX 路由与 DeepSeek V4 Flash max 能力，不把配置存在当作调用成功。
