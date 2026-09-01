# R4-D07 oracle 窄范围勘误决定

Date: 2026-08-14  
Status: `APPROVED_FOR_NARROW_REFREEZE`

## 边界

本决定只修正已被合同、typed input 与实际 Decimal 运算共同证明不可能成立的 oracle 叶值。合同、catalog、generator、运行时与测试代码均不在本次修改范围。不得放宽 exact-leaf/DSL 校验，不得按 case ID 修改运行时逻辑。

修改前冻结锚点：

- contract file SHA-256 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`；semantic hash `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`。
- catalog file SHA-256 `419f2a060e0d46550c0e1faaeabddd5094a12556ba7f9ba9f66d99be5b5ee4cd`；content hash `cfc382ad81b786965da9a3e46c41218982eb2b6f93aafb3fcf1e0b0c51ce1669`。
- oracle file SHA-256 `6ef89feb9d5527b54a81870af444e82fa24082571a7927467170f686e66360a8`；content hash `e0bf81c81d96a0c476ebe34ed95fc51cf8a985bca3c931ff5807a9e06cb52ada`。
- registry file SHA-256 `01f036f2b086cb92c5c63ed755a38c1fe17ff43ff8868a6d6519aa55af29e9ca`；content hash `396db04fc88eeca387171ada1fb21d721e7ccdfffbed22ff0c2a041b1606ebd4`。
- generator SHA-256 `1b230c374830d69c7bc37323960696f9a50ed3bba16bfa9f8996e6a64ce44a9b`。

## 已证明的矛盾与批准修改

1. AST 分级采用该项目冻结输入中的正常上限 40，以及合同区间 G1 `[1,3)`、G2 `[3,5)`、G3 `[5,8)`、G4 `>8`。因此 96/40=`2.4` 只能为 G1，192/40=`4.8` 只能为 G2。批准把 cases 010、093、094、100、101、102、106 的 `units.1.grade` 从 G3 改为 G2；case 085 从 G2 改为 G1，并把其 `units.1.monitoring_priority` 从 medium 改为 low。
2. cases 129–133、136 与已正确携带计数的 case 134 采用同一共享访视轴与风险标记输出合同；当锚定结果数非零时，没有任何合同谓词允许只在 case 134 输出计数。批准在 `expected_leaf_set` 增加 `journey.risk_marker_anchored_result_count`：129=`2`、130=`2`、131=`3`、132=`1`、133=`2`、136=`1`。

合计只允许 15 个叶级修改。重建后的 manifest/registry 哈希变化属于上述 oracle 叶变化的机械派生结果，不构成额外语义修改。

## 独立复核证据与限制

- conference `medical_monitoring_r4_d07_oracle_adjudication_20260814` 的 Pi 路径在同一会话 `019ffd2c-6f3a-7000-9637-f51eba01121e` 独立复算并支持上述两类勘误。
- Grok 路径会话 `954be65a-b49a-472f-88c9-76221695dc96` 两次均取消/未形成可用结论，不计作接受证据。
- Codex 直接运行当前 D07 entrypoint，观察到上述实际值，并确认 case 134 已有同类非零计数叶。

## 仍按运行时缺陷处理

source jump/reverse binding、visit ref、case 017 grade state、case 103 priority、case 106 trend 仍须用 case-free 合同逻辑修复；除非新的独立证据证明 oracle 另有矛盾，否则不得继续改 oracle。

## 重冻结退出条件

- 脚本首先验证全部修改前文件哈希与每个旧叶值；任一不符即停止。
- oracle embedded content hash、manifest、registry 重新生成并通过 `--check-inputs`、`--check-refs`、`--check`。
- catalog、contract、generator 修改前后 SHA-256 完全一致。
- 记录修改后 oracle/registry 文件与 content hash，再进入剩余运行时纠偏。

## 重冻结结果

Status: `REFROZEN_AND_SELF_CONSISTENT`

- 实际修改叶数：15；未出现额外叶变化。
- oracle file SHA-256 `28b792a39676aaf9be442e2d2bc349f8f33b214c485bed1d487e752876c3626b`；content hash `cc85edefeefda2cafa7ade573b8abfa531b48cf081e275de6c65fda4d4e733f8`。
- registry file SHA-256 `470bfc41b390358697d1066e9611ee18ac2944bebabfe0352244cd1b09e1b4a0`；content hash `9a543edfb539911c63aa7427d348e3392d656b79ce73ffb850a99c522ff098c0`；manifest hash `86d205d5f0e64e99ca2284ad48c9deb4af71f4474db04abea5480ae051345795`。
- contract、catalog、generator 修改前后 SHA-256 完全一致。
- generator `--check-inputs`、`--check-refs`、registry `--check` 均通过；144 cases、4,732 reference leaves、7,605 resolved values、0 failing reference problems、五向双射成立。
- 重冻结后的挑战矩阵由 63 降为 55 个失败 case；cases 085、094、129–133、136 已精确通过，其余差异与本决定列出的运行时缺陷带一致。

## 补充勘误：case 030 source jump

Status: `INDEPENDENTLY_ACCEPTED_FOR_SECOND_NARROW_REFREEZE`

运行时完成其余 case-free 纠偏后，只余 case 030 的 `source.source_jump_target_pairs` 与 `source.reverse_binding_count`。Codex 直接复算与独立只读 Luna verifier 均证明：case 002/030 中和合成 ID、locator/reference 及由其派生的 18 个 hash 后，typed input canonical JSON 完全相等；两者 expected medical/trace leaves 也相同，只有 source leaves 冲突。合同 §14.2 不允许相同 substantive input 因 case binding 产生不同 raw output。

独立报告：`runs/review/medical_monitoring_r4_d07_case030_verifier_20260814.md`；verdict `ACCEPT_ORACLE_ERRATUM_CASE030`。原生 Luna spawn 被当前 App 工具明确拒绝，因此按全局规则使用 Codex CLI compatibility route，请求模型 `gpt-5.6-luna`、effort `max`、read-only；未替换为 Sol/Terra。

批准仅修改 case 030 的两个 `expected_source_leaf_set` 叶：

- `source.reverse_binding_count`: `2` → `3`。
- `source.source_jump_target_pairs`: 从 listing + `SYN-TREND-1` 改为与该 `required_missing` action 输入一致的 listing + `SYN-GRADESET-ALT-5` + `SYN-MR-ALT-ACTION-1`。

禁止修改其他 oracle 叶、合同、catalog、generator、运行时或 exact-leaf/DSL 规则。修改前锚点为 oracle file `28b792a39676aaf9be442e2d2bc349f8f33b214c485bed1d487e752876c3626b` / content `cc85edefeefda2cafa7ade573b8abfa531b48cf081e275de6c65fda4d4e733f8`，registry file `470bfc41b390358697d1066e9611ee18ac2944bebabfe0352244cd1b09e1b4a0` / content `9a543edfb539911c63aa7427d348e3392d656b79ce73ffb850a99c522ff098c0`。

补充勘误重冻结结果：

- oracle file SHA-256 `c2c2c4694f4dfe49415c949664d5e174e9ffd0a42ddb83ddc03712aabe93881f`；content hash `e0e244d03d06a30127daeb71769733439e8620d62722b78074eb2e2068a3f4e9`。
- registry file SHA-256 `f63ff8fa9e5857c574f8b9f924807f04def19d4089bc39cd72d1ba610f36a2d6`；content hash `c6351e79d4e3bd088de24a6e8cf301bb729084b4e7219eb49b064e337708e5af`。
- contract、catalog、generator 仍与原冻结 SHA-256 完全一致。
- `--check-inputs`、`--check-refs`、`--check` 通过；挑战矩阵 `298 passed`，D07 runtime/Query-Journey/replay/mutation `1090 passed`，无剩余 exact-leaf 差异。
