# R5 S4 Runtime 接受记录（2026-08-19）

## 结论

`ACCEPT_R5_S4`

接受范围仅为 synthetic/offline、renderer-neutral 的 Risk Inspector runtime：
baseline、0/1/N 独立分析、raw/parsed 分离、七维确定性核验、冲突、独立裁决、正反证、
来源、三分句 Query 草稿、历史链与 Journey 跳转投影。它不接受 UI、浏览器、真实项目/
模型、产品、生产、临床真值、医学写作或 S5+。

## 合同纠偏

parent runtime contract 保持 SHA
`58848c51bbf25acddf1b34e2631d32f9294f8df22ecf6b5df438705ddcf16f54`。
因 accepted authority anchor 只有六条唯一 attempt rows，版本化 erratum 将当前执行上限
冻结为 `min(10,A)=6`，未改写或重签 parent/anchor：

- erratum SHA：`6faa30ffc0b09741bcfaa166972780bddeeb5163e77bcc01daa08324f0398792`
- erratum verdict：`ACCEPT_R5_S4_RUNTIME_ERRATUM`
- 当前有效矩阵：N=0、1、2、6；不得声称或伪造 N=10。

## 独立审阅闭环

独立 reviewer 先后复现并否决：验证器嵌套 fail-open、候选自签 hash 通过、typed
authority join 缺失、ModelEvidence permit 漂移、active ensemble identity 漂移、外来
history、错误 receipt/Inspector/source/Query/adjudication、raw/parsed 混淆、缓存越界与
公共 API 过宽。全部修订后 reviewer 重放攻击并返回 `ACCEPT_R5_S4`。

## 决定性门禁

- Focused normal/O2：各 `495 passed`，0 skip。
- Adjacent normal/O2：各 `1637 passed, 5 deselected`。
- 89 条 runtime challenge：逐条真实执行；challenge module `180 passed`。
- Ruff、fresh `python -B` import、递归结构/全叶/hash/authority probes：通过。
- 23 frozen SHA 无漂移；S4 `.pyc` 为 0；root init 未变。
- 8911 无监听。

## 接受快照

- `src/mm_r5/s4_contracts.py`: `0ea6de7495c9226007308752df69ec3c21ac3f1b23891ef44ca1e1b0e37d58d3`
- `src/mm_r5/s4_authority_builder.py`: `af98919b5806ebe0123290091a8b73026d7cca30730c1117d5f3d5bb6c5d2396`
- `src/mm_r5/s4_projection.py`: `b6c8e85f6066225ad3ea558d5fe71512ec06b763513fc36d174652adb2327834`
- `src/mm_r5/s4_validator.py`: `a0912d3bf4f9437f63ceaef8513deab4ae5a6e3d09794a7973fd644dab3bc0ff`
- `tests/s4_runtime_fixtures.py`: `a8accebc313cec7059d4503398af5e093f07fbb09bd030a31633d27e56e75b4d`
- `tests/test_s4_contracts.py`: `d41a811a7511be37cafa9f80130c6eabcc9af7b1dae86f11022a1018c0f5c0f8`
- `tests/test_s4_authority_builder.py`: `c868e363a6044b9ff05a2324d3a3b7acb97a0808d32392760f320c75012e65d8`
- `tests/test_s4_projection.py`: `18c23dd48cfbd65db5b59c9b753ef53b68e9425ad9fa0d46945d847a226514ce`
- `tests/test_s4_validator.py`: `06381bb20b3ea1da274338eaa94fa348e811ce7f08eb124309f529a1de650c74`
- `tests/test_s4_readonly_gate.py`: `2d966449611caf04714203be6cd1dd4892c6b2ab4a2093df309dd9dc41f2fe2a`
- `tests/challenges/test_s4_runtime_challenges.py`: `c3b572c4dd7663faeb7af0c09b64300f39459377465459e89082c455b705340e`
- `evidence/r4_r5_s4_readonly_sha256.json`: `53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822`
- root `src/mm_r5/__init__.py`: `0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd`

## 下一安全动作

按 R5 阶段合同进入 S5 Subject Workspace 合同冻结：统一 Journey/Profile/Timeline 的
访视轴、时间窗与选择状态，覆盖八域事件、点/闭区间/开放区间、部分/冲突/缺失日期、
AE/MH 后补匹配历史，并继续只读引用 S1–S4 authority。S5 合同接受前不写实现，8911
保持停止，前端/浏览器仍留到既定 S7 产品接入片。
