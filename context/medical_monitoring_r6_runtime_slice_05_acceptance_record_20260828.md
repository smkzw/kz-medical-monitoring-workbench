# R6 runtime slice-05 acceptance record

Date: 2026-08-28

## Decision

`ACCEPT_R6_RUNTIME_SLICE_05_SYNTHETIC_OFFLINE`

接受范围仅为 synthetic/offline 的 pre_lock 四类专属输出：`full_risk`、
`revision_impact`、`check_package`、`query_revision_package`，以及同一 Run、cutoff、
source revision、authority/coverage/QC 下的失败关闭约束。

## Final evidence

- focused `tests/test_mode_output.py`: 204 passed。
- full POC: 581 passed。
- normal / `-O` / `-OO` × `PYTHONHASHSEED=0/1/42`: 9/9，每格 204 passed。
- `mode_output.py`: `34831cf8d8d00fedd108e198a7971e62643761eaee7390e5758997e9080b45ad`。
- `test_mode_output.py`: `0a31f3fb099fe175eb036bf37b89479dcc0852f1eec68b7a84b9ea4aeb8ccfb4`。
- final post-gate receipt: `683e5cd801e6181a48ab312f6fbd70d3e7e7504bb78719b741243584af426587`。
- 医学写作边界：542 files，aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911/5174 保持停止；未使用真实项目。

## Corrective history

worker 初始 116/493 证据未直接接受。Codex 与独立会商通过真实反例关闭了：缺失
authority/population、生命周期类型绕过、风险条目伪终结、定量风险绕过、numeric
人口/cutoff/revision 漂移、不可核查 locator、重复身份、变更来源冒充、Query 自更新、
包级外部工作流/PD 状态别名、可省略计数与 standalone incremental 绕过。Pi 与 Grok
原 session 对最终字节均给出限域接受，无 fallback。

## Explicit residuals

- prior revision / previous Query draft 的真实实体解析属于后续 runtime 集成，不在本纵切。
- post_lock 深层输出、产品/UI、真实项目/报告、医学/监管结论、Query 外发/回复、PD
  登记/关闭与用户确认均未接受。
- Agent Harness 尚未接入；后续默认目标仍为
  `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并保留、真实验证
  `deepseek/DeepSeek V4 flash:max`。

## Next safe action

建立 R6 slice-06 独立合同，优先实现 `post_lock_pre_cfdi` 固定总量下的项目全量报告、
中心材料、受试者材料和 checklist 输出；仍用 synthetic/offline fixture，保持
8911/5174 停止并保护医学写作子系统。Harness adapter 继续作为后续独立纵切。
