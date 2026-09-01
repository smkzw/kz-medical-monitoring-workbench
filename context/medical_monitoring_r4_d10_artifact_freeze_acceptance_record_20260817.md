# 医学监查 R4-D10 artifact freeze 验收记录

> 2026-08-18 修订声明：本记录保留为历史验收证据，但其中 fixture authority
> 的 accepted-source-membership 结论已由
> `context/medical_monitoring_r4_d10_authority_correction_worker01_acceptance_20260818.md`
> 明确取代。四个 intentional external-pair catalog case 的无效 pair 曾被错误写入
> accepted authority；修订链已重新生成、复验并独立接受。不得继续引用本页旧 SHA
> 作为当前 D10 authority/runtime Worker-01 锚点。

日期：2026-08-17  
结论：`ACCEPT_D10_ARTIFACTS`  
范围：仅 D10 synthetic/offline artifact；不包含 D10 runtime、R4 总体、R5/UI、真实项目/模型、产品、生产、正式临床结论或医学写作。

## 冻结对象

- 合同：`reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`，SHA-256 `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`。
- fixture authority generator：`e873783732b0cc0703fe7943852c0cb604867109d89f19f39bf339e35098b640`。
- catalog/registry generator：`deaf7f7124f1028d1e16ecbd65ec0c4f965f496c1d441e990782340c205dbcbc`。
- oracle generator：`5df9282215a359e47026fba38fa041fc43e63361afae0769c302cfbb88b41e99`。
- independent verifier：`3b5c3dd51b6ecb231785b9a6c40f2d55d9737c5a60257a4d701069debc25179c`。
- D10 tests：`26069f705d5dab52efac0cc81f720b1ad3ae5f177195dc5aeaf4fee378c389f1`。
- fixture authority：`e8f8a18aa58461d3870689836274d7a96be0f18d66cf9b1e0b3e3218c4f88d09`。
- typed catalog：`40ce96b2e5c188167cacbe03a8b5a80260886276cbacd1edbd1261f9b7927939`。
- expected-outcome oracle：`da7d87f4e92e3371b4b9e39e992a98a61cacb53df048b2438d4d6077ca1522a1`。
- challenge registry：`e6f735a0d96a54500190fef8dd28e82b3eeca851f659ff6fe45565554988cf02`。
- quota manifest：`3800b83f3b38b1fffe54b6524f92abedc2df0ed3c32543918e252f549049f0a7`。
- verifier 外部 raw-SHA 锚点：`reviews/medical_monitoring_r4_d10_verifier_raw_sha256_anchor_v1_20260817.sha256`，SHA-256 `be8bdbd5ba787f1a51dc9ff24cbd2b10effff5da880f241024acc53986eb9e11`，权限 `0444`，macOS flag `uchg`。

## 决定性证据

- 312 cases；12 个互斥 primary partitions；32 个去重 mandatory attacks；authority/catalog/oracle/registry/quota 闭合。
- fixture-authority、challenge-registry、expected-oracle 三个 generator check 均通过；独立 verifier 为 `0 problems / 0 cases failing`。
- D10 artifact tests：`Ran 106 tests ... OK`；D09 相邻回归：`Ran 99 tests ... OK`。
- 五个末轮语义门全部具备定向负向证据：measure-origin 集合与派生决定；Query canonical/归属/互斥/并集/身份；hidden subject-site pair；accepted source revision/content/locator membership；ModelEvidence 全 provenance 与 authority pin。
- `shasum -a 256 -c reviews/medical_monitoring_r4_d10_verifier_raw_sha256_anchor_v1_20260817.sha256` 返回 `tools/verify_d10_artifacts.py: OK`。该锚点位于 verifier/test 外，可由系统工具直接复验；一字符 verifier 漂移被拒绝。
- 8911 无监听；未启动服务、未读取真实项目、未修改 `src/mm_r4`、R5/UI 或医学写作子系统。

## 独立验收

全新隔离的 Codex Luna/max 只读 verifier `/root/d10_five_gate_independent_review` 首轮只否决外部 verifier raw-SHA 信任根；补齐外部只读 `uchg` 锚点后，在同一审阅会话复验并返回 `ACCEPT_D10_ARTIFACTS`。审阅者首尾 SHA 一致，未修改文件。

## 解锁与继续冻结

D10 artifact phase 已冻结，下一安全动作仅解锁 D10 synthetic/offline runtime 的合同到实现切片。继续冻结 R5/UI、8911、五个真实项目、真实模型医学分析、产品服务、正式临床结论与医学写作子系统。runtime 不得读取 oracle、case-id/index、mutation class、合成哨兵或其他测试意图作为决策依据。
