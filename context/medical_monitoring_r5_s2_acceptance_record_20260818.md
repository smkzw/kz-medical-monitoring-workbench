# R5 S2 Runtime 接受记录（2026-08-18）

## 结论

`ACCEPT_R5_S2`

接受范围仅为 synthetic/offline、renderer-neutral 的 R5 S2 第一条薄纵切：

`项目风险 → 中心单元 → Risk Inspector → Subject Workspace / 时间锚点 → 精确来源`

不接受 UI、浏览器行为、真实项目、真实模型、临床事实、医学写作、产品、
生产、安全专项或 S3-S8。

## 独立审阅关闭过程

原独立 reviewer 首轮返回 `REVISE_R5_S2`，指出四项决定性缺口：

1. 调用方可替换 individual-member registry；
2. `ModelEvidence` 未闭合全部 evaluation/output/source/adjudication identity；
3. source `locator_kind` 可与 `EvidenceRef` 漂移；
4. W3 使用固定窗口，未与真实 R4 analysis window 闭合。

纠偏后，同一 reviewer 在不修改文件的条件下重放攻击并返回
`ACCEPT_R5_S2`。其首尾 10 个审阅 SHA 完全一致。

## 当前实现与不变量

- individual members 只能由冻结 typed R4 `Member` tuple 唯一解析；任何外部
  registry，包括结构合法的替代 registry，均拒绝。
- `ModelEvidence` 精确绑定 receipt evaluation identity、两次 worker output
  identity/hash、shared input、模型/ensemble、source refs/pairs、visible conflict、
  independent adjudication、role/permitted leaf 和 canonical binding hash。
- source locator id/kind/file/row/lineage 与 `EvidenceRef` 精确相等；无 nearest
  fallback。
- 单一闭合 R4 analysis window 是 baseline、两个 worker claimed window 和 W3
  Workspace/deep-link window 的共同权威；坏窗口拒绝，合法变窗完整传播。
- Builder AST 不存在 `[0]` 语义对象选择。
- S3/S4/S5 deferred leaves 保持空；公共 Inspector 不泄露 packet-only
  `ModelEvidence` 或 worker outputs。

## 决定性门禁

- R5 normal：`427 passed, 15 subtests passed`。
- R5 `PYTHONOPTIMIZE=2`：`427 passed, 15 subtests passed`。
- W1/W2/challenge：`105 passed`；W3 focused：`37 passed`。
- R4 full adjacent：`4396 passed, 11258 subtests passed`。
- 前置 generator/verifier normal/optimized：21 invariants、12 imported
  dataclasses、13 tamper probes，全部通过。
- Ruff F、normal/optimized compile、root public API object identity、11 项
  R4/R5 read-only SHA gate：通过。
- 8911：`connect_ex=61`，未监听。

## 接受快照

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_contracts.py`
  - `8f9cc2ad1865943dd8bc0f2b6dcfd5359ced882f5bc5107b254205728a4ad20c`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_authority_builder.py`
  - `6c8a18bdbc31af57a9086e0366f0e387d06ef2732ffe62a90432698d809793c7`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_thin_slice.py`
  - `0721cef73792a9ccf7cfd4131798b3c4a11a6b6962aeb11ec42e0f0cf46fcbf9`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py`
  - `0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_s2_readonly_sha256.json`
  - `6cec5b39fe325bf644e2ae31174a5175b2ad94e190d98cb43b00b33636ff21af`

## 下一安全动作

先冻结并实现 S3 项目驾驶舱与中心图谱的 authority/quantity/current-risk/
change-band 合同；继续只读引用 R4/D09/D10，不在 R5 重算风险、分子、分母或
裁决。8911、浏览器、真实项目/模型和医学写作继续隔离，直至计划中的 S7。
