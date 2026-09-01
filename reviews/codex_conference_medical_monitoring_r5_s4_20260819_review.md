# Codex Conference Review: medical_monitoring_r5_s4_20260819

Date: 2026-08-19

## Verdict

`PASS_FOR_CONTRACT_IMPLEMENTATION`。两条独立会商均认为现有 `R5RiskInspectorProjection` 只能作为公共壳，不能直接视为 S4 合同；必须新增 S4 typed packet、0/1/N、逐模型基座回查、raw/output 双哈希、确定性复核、不可隐藏冲突、独立裁决、三分句 Query/历史/Journey 以及 audience/audit 双平面。

## Boundary Compliance

- 全程只读审查；未修改 R4、既有 R5 runtime、前端、服务、医学写作或真实项目。
- 未启动 8911、浏览器、模型执行或产品 runtime。
- Qwen 首路因 terminal 429 无输出；按声明 fallback 使用 fresh native Luna。Grok 首轮工具失败后在原 session 完成 round 2。

## Participant Outputs Reviewed

- `runs/conference/medical_monitoring_r5_s4_20260819/general_grok46.md`
- `runs/conference/medical_monitoring_r5_s4_20260819/general_pi_qwen38_fallback_codex_luna.md`
- Pi/Qwen 失败原始记录仍保存在 `general_pi_qwen38.md` 与对应 stdout log，不冒充会商产物。

## Conference Panel Review

- 共同结论：S2 固定 N=2 特例不可上升为 S4；现有 Inspector ref-bag 不足以机械证明 0/1/N、逐 worker baseline assessment、conflict member set 和 source resolution。
- 必须分离普通中文 audience 与 audit metadata；“分析一/分析二/独立核对”可见，provider/model/attempt/hash 不得出现在普通层。
- 必须用独立 raw-byte artifact 填补 R4 structured output hash 不能代表原始输出的缺口。
- 基座不是 gold；单模型无 consensus；多数票与裁决不能隐藏高风险、mutual negation、baseline miss 或 single-model addition。
- Query 固定为依据/发现/行动项草稿；不得发送、回复、关闭或任务化。

## Main-Venue Codex Review

- 采纳独立 `R5S4Packet` + public/audit projections + exact mapping/join recipe + named deferred 的方案。
- 合同最少覆盖八个挑战家族，每个 case 有独立 mutation、typed outcome/fixed error code、禁止 audience output 与非 LLM oracle；不得复制 expected 文本形成 self-proof。
- 合同接受仅解锁 S4 runtime，不能宣称 UI、真实项目/模型、产品或生产接受。

## Codex Independent Verification

- Codex 已核对 System Design §9/§10/§12/§17、R5 stage contract §6/S4 Done、exact contract Inspector fields/mappings、R4 ensemble/D10 classes、R5 S2/S3 接口与接受记录。
- 两份 prompt preflight 均通过；路由 session、失败原因与同 session recovery 均保留。
- 浏览器/视觉不属于 S4 合同阶段；8911 必须保持停止。

## Final Decision

允许进入 S4 合同工件实施与独立冻结审阅；不允许进入 S4 runtime。最终合同仍须由 fresh isolated reviewer 对稳定 SHA 返回 `ACCEPT_R5_S4_CONTRACT`。
