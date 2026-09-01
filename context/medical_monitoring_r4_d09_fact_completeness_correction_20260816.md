# R4-D09 fact completeness / fail-closed 纠偏记录（2026-08-16）

## 触发原因

原 Luna 独立审阅会话对 Worker01 follow-up2 候选返回
`REVISE_D09_CORRECTED_FREEZE`。虽然候选达到 179/179、537/537 clean
parity，但负向探针证明数值阈值、Query policy/proof 与 source verification
仍可被默认、遗漏或篡改而通过。

## 本轮修复

- `ResolvedAuthorityDecision` 现在显式承载重复风险最小受试者数、系统性
  缺口阳性最小机会数、趋势阳性最小受试者数，以及 ModeContract version、
  authority ref/locator/content hash；各 pattern kind 缺失或非法阈值在评价前
  fail closed，运行时和 oracle 不再存在 `2/4/3` 回退/硬编码。
- 新增完整 `CenterQueryPolicy` typed object；`max_query_member_fanout` 无
  dataclass 默认值，必须与版本化 policy 一致。
- `QueryRedundancyDecision` 必须通过 owning-member set hash、covered/uncovered
  精确分区、member Query refs、coverage proof hash 与 fanout 一致性校验；只有
  非空 uncovered set 的 `site_process_delta_present` 才可生成 Query。
- source verification records 必须与顶层 revision/hash 一一对应；空集、重复/
  错 revision、declared hash 不一致，以及 `verified` 时 declared/verified 不等均
  fail closed。
- `evaluate()` 公共入口自行调用完整验证，不能通过绕过 adapter 获得未验证
  医学输出。
- catalog 中重复 revision set 去重；fully-covered Query fixture 补齐明确的成员
  Query refs。重新生成 catalog/quota/resolved registry；oracle 语义输出保持不变。

## 当前候选 SHA-256

- contract（只读、不变）：`9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- catalog generator：`4a257242c83cafe212c2a6749236f894da569c83c173934f77f894e24e8f1702`
- oracle generator：`19a73474174bbe7ff3d887fbda13c8ac86707c5ebb5de0d6ab51e8e1a738ee5e`
- catalog：`93a737989eb05d75cb15ca09860949890013059663c601868b2f2a93c5c710eb`
- quota：`4b80f36a4904e0beb0f7f14b428db010109de4d3bd71becdc367996e9085b50a`
- registry：`b697c43199047a15ed5666f55ef1b1d99762c34b3925c9e36815497ebd92f179`
- oracle：`045990cfa9d0286e5b8c007d5c942faff0489a8afb06d09158c0f4733cb0c86a`
- artifact tests：`170418760176906c3f6e01d9a9dd5ceb3f7ef880673a0c5472c16e843cf1e78f`
- runtime contracts：`42fdda3b36e08e77810847f8dcea4cd13572c3d1a6f08eaea80a7eca0c14765f`
- runtime evaluator：`0b4aa08a51b84d0020133313ad30a886bcebdde67846d0efc639852e90c06743`
- adapter tests：`9788183fd0193e60f9b69283078f2784c7961c3b0e37bf6baddc50ece7c9f6b4`
- runtime tests：`d38b50ff76f1efcb409417aadcddf7ad678b9a22acc70ee2eebd3d84bcd9984c`
- registry normalized generator pin：
  `ea5e56a9b5996003122149b7d12317e13a7ce16246c3090a2757cf89b42aee23`

## Codex 本地验证

- 179/179 cases、537/537 leaf sets，0 mismatch。
- D09 artifact：99 passed。
- D09 runtime/adapter：71 passed、3 subtests。
- D08 artifact adjacency：54 passed、10 subtests。
- D08 runtime adjacency：186 passed。
- catalog/registry 与 oracle 双生成 determinism、stage-B linkage 均通过。
- Ruff、`py_compile` 通过；合同 SHA 不变；TCP 8911 `STOPPED`。

## 当前状态与下一动作

当前只是新的 freeze candidate，不是 ACCEPT。Worker02/03 继续锁定。下一动作是
由原 `/root/d09_artifact_freeze_review` Luna fresh-context verifier 对上述不可变
SHA 重新执行负向探针与合同复核；仅 `ACCEPT_D09_CORRECTED_FREEZE` 后才更新
artifact freeze acceptance 并解锁后续 runtime projection。
