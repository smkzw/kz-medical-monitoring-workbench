# R5 S0 合同冻结接受记录（2026-08-18）

## 结论

`ACCEPT_R5_CONTRACT`

该结论仅关闭 R5 S0 并解锁 S1。它不接受产品 UI、浏览器行为、真实项目、真实模型、生产或后续 S2–S8。

## 冻结对象

- 合同：`reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
  - SHA-256：`1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6`
- 生成器：`scripts/generate_medical_monitoring_r5_contract_v0_3_artifacts.py`
  - SHA-256：`250863b74b9e74696ccbc6c2a7e27e97f18a24e1a0467314b5aee5ec4e329e55`
- 独立机械验证器：`scripts/verify_medical_monitoring_r5_contract_v0_3_artifacts.py`
  - SHA-256：`8fd78c68e51b6d5e046c8478c3e76513901271e5f29427d35b17061e8fd207c4`
- `challenge_registry.json`：`ef459f58ad6997a823c3ff57d51256cdf531b806d9033df636ab2912085b0887`
- `exact_contract.json`：`3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`
- `quota_ledger.json`：`aeec1482b1c374d175a89660dd11cc312b6ba2612cf6c5a709379f2b05163b37`
- `manifest.json`：`2298ff58a5f693e5d3deca7200920cfc12d54f59a9e04cae4aed41fd780363dd`

## 决定性证据

- 普通模式与 `PYTHONOPTIMIZE=2` 验证器均返回 `ok=true`。
- 204 条 challenge specification 与 204 条 ledger instance 逐一绑定且 rule/path/case identity 唯一。
- R4 direct/derived source path 逐 dataclass 字段解析；嵌套可见性 ID 精确到 `visibility_decision.decision_id`。
- 当前上游不足的中心语义格、当前风险集、逐成员定量度量与 Inspector 证据叶使用具名 deferred contract，不伪装为已可派生。
- Workspace 与返回上下文哈希只允许由非哈希 canonical fields 确定性派生。
- R4 缺失 cutoff 保持 `None`，不得改写为空字符串或占位值。
- 八个业务域的事件编码必须各有且仅有一项；“症状与疗效”固定为圆形事件，历时变化只由趋势线表达，风险覆盖层继续使用事件域禁用的双折角标记。
- 独立隔离审阅者首尾复核七项 SHA 稳定后给出唯一 verdict `ACCEPT_R5_CONTRACT`。
- 8911 无监听。

## 修订接受历史

最初冻结快照已在 S1 接线时由上述修订快照替代。修订只处理 R4 缺失 cutoff 的无损表达、八域编码完整唯一性及“症状与疗效”事件/趋势消歧；没有扩大 S0 或 S1 权限。隔离审阅者对新七项 SHA 首尾复核稳定，普通与优化模式验证器均通过，并再次返回 `ACCEPT_R5_CONTRACT`。旧 SHA 仅属于历史接受，不再是当前实现基线。

## S1 写入与禁止边界

- 唯一实现写域：`poc/medical_monitoring_ai_native_r5/**`。
- 任务记录可写 `context/**`、`plans/**`、`reviews/**`、`metrics/**`、`prompts/**`、`runs/**` 中本任务具名文件。
- R4 仅只读 import；任何 R4 字节漂移即 gate fail。
- 禁止触碰 `frontend/**`、医学写作、既有 R1–R4、真实项目资料、真实模型、生产与安全专项。
- S1 不启动 8911；只有 S7 浏览器验收片允许临时启动并在验收后停止。

## 下一安全动作

实现 S1：exact typed contracts/canonical hash、R4 authority adapter/receipt、S1 对应真实 challenge tests 与 immutable R4 SHA gate；由 fresh reviewer 接受后才解锁 S2。
