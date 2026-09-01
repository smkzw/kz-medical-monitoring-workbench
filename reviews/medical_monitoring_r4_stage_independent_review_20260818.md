# R4 阶段独立审阅（2026-08-18）

## 结论

`REVISE_R4_STAGE`

R4 阶段关闭门规定任何 P0–P4 均阻断。本轮发现 3 项 P2 和 1 项 P4，R5、UI、真实项目和产品运行继续锁定；8911 必须保持停止。

## 阻断项

### P2 — 多模型与 reference baseline 核验闭环缺失

- System Design v1.1 §9.2–9.4 与 R4 计划步骤 9–10 要求 reference baseline 六态核验、gap search、ensemble 1/N、隔离分析、确定性 evidence verifier 和独立 adjudication。
- 当前仅有 D10 `ModelEvidence` 数据载体及浅层 binding/hash 校验；`ensemble_size=0` 仍可通过非负校验。
- 尚不能证明 `ensemble_size>=2` 的不同 session/context、worker 不裁决自身、基座逐项来源回查、基座漏项搜索及高风险分歧持续可见。

决定性复验：1 路不显示伪一致度；N 路要求隔离 identity；0 路 fail closed；worker/adjudicator 分离；基座六态逐项可定位；gap search 能提出漏项；高风险分歧保持可见并标记需关注。

### P2 — D06 按 synthetic sentinel 与唯一 canonical scope 分流

- `efficacy_evaluator.py` 的生产决策路径直接读取 `SYN-WRONG-SUBJECT`，并强制唯一 `CANONICAL_SYNTHETIC_SCOPE`。
- 在 D06 fixture 082/180 中，语义等价的错误 subject 仅因字符串是否等于固定 sentinel，分别落入不同错误阶段与异常类型。

决定性复验：任意错误 project/site/subject/run 均由 typed authority binding 一致 fail closed；整体重命名后的合法 synthetic scope 可执行；生产 evaluator 不含 `SYN-*` 或固定 case/index/mutation 决策分支；运行 D06 focused、property/mutation、D08–D10 adjacent 与全 R4 回归。

### P2 — 公共 coverage matrix 冻结 SHA 漂移

- 当前 SHA：`8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`
- 既有接受记录固定 SHA：`6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`
- 尚无当前版本差异审阅、D01–D10 传播影响评估和显式重新冻结记录。

决定性复验：恢复已接受字节，或完成当前版本的逐项差异、传播影响、重新冻结和阶段证据重跑。

### P4 — Ruff 门失败

5 个 F401：

- `d10_contracts.py`: `field`, `Dict`
- `d10_evaluator.py`: `Sequence`, `CHANGE_CAUSES`, `D10ContractError`

决定性复验：`python3 -m ruff check src/mm_r4 tests` exit 0。

## 已通过的当前证据

- 全 R4：`4268 passed`。
- D10 artifact：`107 passed`；D10 generator/verifier 与 immutable anchor 通过。
- D07、D09 generator/oracle 当前检查通过。
- `src/mm_r4` 与 `tests` 共 90 个 Python 文件内存 compile 通过。
- Query 为“依据＋发现＋行动项”；PD 只形成待核实 Query 草稿，不建立发送/回复/关闭工作流。
- 既有 identity/lifecycle、replay/order/mutation/hidden/negative 与局部高风险投影回归通过。
- 8911 无监听。

## 审阅过程偏离

审阅者对旧 D06/D08 generator 执行 `--help` 时，脚本未帮助短路而执行默认生成，刷新 3 个既有 artifact 的 mtime；生成后文件字节 SHA 仍与冻结接受值一致。该 mtime 刷新不作为只读验证证据。Codex 主会场对 D08 generator 也发生同类 `--help` 误触，最终字节 SHA 未漂移。

## 阶段范围

本结论仅针对 synthetic/offline R4 风险子图；不代表 R5、UI、真实项目、真实医学模型、生产或商业化完成。未启动 8911、服务、浏览器或 UI，未触碰医学写作子系统。
