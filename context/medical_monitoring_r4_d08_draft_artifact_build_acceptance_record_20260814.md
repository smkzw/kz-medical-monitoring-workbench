# R4-D08 合同草稿冻结制品构建放行记录

日期：2026-08-14  
状态：`ACCEPTED_V0_6_FOR_FREEZE_ARTIFACT_BUILD_ONLY`

## 放行对象

- 合同：`reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_5_20260814.md`
- 文件 SHA-256：`51b635dd561e06a79c8e325dace0e93439f43c586b56c93243db6eb668197412`
- 本阶段 semantic hash：对完整合同执行 UTF-8 解码、CRLF/CR→LF、Unicode NFC 后取 SHA-256，结果同为 `51b635dd561e06a79c8e325dace0e93439f43c586b56c93243db6eb668197412`

## 独立审阅证据

- Pi/CMS-SMK DeepSeek v4 Flash 同会话终审：`runs/conference/medical_monitoring_r4_d08_contract_20260814/general_pi_qwen38_round5.md`，SHA-256 `bea7d8f447d8daaa82452de7abcfdaee66c55de80e279787eca46b5e2281f480`，结论 `ACCEPT_D08_DRAFT_FOR_FREEZE_ARTIFACT_BUILD`。
- Grok Build 4.6 同会话终审：`runs/conference/medical_monitoring_r4_d08_contract_20260814/general_grok46_round5.md`，SHA-256 `d34561d8d34f250ce54ea7cc65dc62fc9e479383593e3f52e9bb17ac5585315c`，结论相同。
- Codex 主审复核 v0.5 的 cutoff、not-found、方向关系、waiver、fanout、内部守恒/受众投影及增量修订边界，无剩余可复现的双读 L1/expected-set 结果。

## 授权与阻断

仅授权在隔离 synthetic/offline 范围构建 `catalog/oracle/registry/generator` 及其验证脚手架。此记录不是 `ACCEPT_D08_CONTRACT`，不允许 D08 runtime、D09/D10、R5 UI 或真实项目执行。完整合同接受仍要求：制品 exact-key/hash/bijection/anti-overfit/negative mutation 验证、R1-R3/D01-D07 相邻校验、同一不可变快照独立 verifier 明确返回 `ACCEPT_D08_CONTRACT`。

8911 必须保持停止；不得读取真实项目数据；不得修改产品 UI、医学写作子系统或系统安全面。

## 下一安全动作

以该合同哈希为不可变输入，按已接受 D07 模式构建不少于 200 条 D08 typed synthetic cases、独立 expected-outcome oracle、五列双射 registry 和只验证/哈希/装配的 generator。制品冻结前补齐 gate signal 闭集与 `time_missing + all-out-of-cutoff` 负向用例。

## 2026-08-14 制品首检勘误

worker_02 的首个 catalog 正确暴露 v0.5 §12 的结构缺口：冻结 case key 列表未包含承载 typed fixture 的 `typed_input`。Codex 已将合同窄修为 v0.6，明确第 16 个 key、typed input 对象要求及 catalog leaf-set 的 null 占位规则。本记录的 v0.5 哈希放行因此失效；在同会话复审接受 v0.6 并建立新哈希记录前，oracle/registry 构建保持阻断。

## v0.6 当前放行锚点

- 合同：`reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- 文件/full-NFC-LF semantic SHA-256：`ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`
- Pi 同会话窄复审：`runs/conference/medical_monitoring_r4_d08_contract_20260814/general_pi_qwen38_round6.md`，SHA-256 `92fc350a5f0d3b2173071de1508b4003b32b3c7ca45b2ef2276d2a5c582daa04`，结论 `ACCEPT_D08_DRAFT_FOR_FREEZE_ARTIFACT_BUILD`。
- Grok Build 同会话窄复审：`runs/conference/medical_monitoring_r4_d08_contract_20260814/general_grok46_round6.md`，SHA-256 `02e0d9d68356c7911d20f25b9736bb7f5b0203a1aec4120cf8753eda602c6eb5`，结论相同。
- 当前 233-case catalog 的 16-key shape 与 v0.6 一致，但 generator/catalog 中旧 v0.5 contract hash 必须由后续 worker 重新绑定并重生成；在此之前它们不是冻结制品。
