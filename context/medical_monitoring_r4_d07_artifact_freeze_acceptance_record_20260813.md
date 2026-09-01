# R4-D07 合同与验证工件冻结接受记录

Date: 2026-08-13  
Status: `ACCEPTED_SYNTHETIC_OFFLINE_D07_CONTRACT_AND_ARTIFACT_FREEZE_V1`

## 接受范围

接受 R4-D07 临床安全性、实验室、生命体征、心电、体检、影像/其他检查纵切的 v0.4 语义合同及其 144 条 synthetic/offline 验证工件，作为后续 D07 runtime 实现的不可变输入。合同本体不回写状态，以免改变 semantic hash；本记录以文件哈希绑定接受状态。

不接受或未验证：D07 runtime、真实项目/真实模型、产品服务、R5 UI、中心/项目聚合、正式安全性结论或监管报告。8911 保持停止，医学写作子系统未触碰。

## 冻结锚点

- 合同文件 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`；semantic `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`。
- catalog 文件 `419f2a060e0d46550c0e1faaeabddd5094a12556ba7f9ba9f66d99be5b5ee4cd`；content `cfc382ad81b786965da9a3e46c41218982eb2b6f93aafb3fcf1e0b0c51ce1669`。
- oracle 文件 `6ef89feb9d5527b54a81870af444e82fa24082571a7927467170f686e66360a8`；content `e0bf81c81d96a0c476ebe34ed95fc51cf8a985bca3c931ff5807a9e06cb52ada`。
- registry 文件 `01f036f2b086cb92c5c63ed755a38c1fe17ff43ff8868a6d6519aa55af29e9ca`；content `396db04fc88eeca387171ada1fb21d721e7ccdfffbed22ff0c2a041b1606ebd4`。
- generator `1b230c374830d69c7bc37323960696f9a50ed3bba16bfa9f8996e6a64ce44a9b`；focused tests `1099234b13b1d9f26826ad97a7f8bb4604e993fdafdbef146b666c2581e14790`。

## 决定性证据

- v0.4 语义审阅 session `019ffae1-ee77-7070-8043-0bb7c22c5fe2` 最终 `ACCEPT_SEMANTIC_CONTRACT_V0_4`，报告 SHA `467aa75c2714a010eeab825b73d463726590a9fe6c2632e10b5cafb65acbcd63`。
- 工件审阅 session `019ffb6f-02a8-7ee3-86ef-b1790585f6e5` 初次 `REVISE` 后同会话最终 `ACCEPT_D07_ARTIFACT_FREEZE`，报告 SHA `4d94c14f778bedf2cde4b0f5729c5b04aad7f5870caed425a399720e30204aa7`。
- 144 条连续 ID；分布 `12/16/16/16/14/18/14/12/10/8/8`；五向双射成立。
- `--check-inputs`、`--check-refs`、registry `--check` 通过；4,732 reference leaves、7,605 解析值、0 failing；focused `125 passed`；两次 registry 重建字节一致。
- 017 年龄/范围一致；006/007/009 分别覆盖有权威的不适用、空表 L0 gap、D05 open-gate 阻断；wrong-run 已进入 `N-WRONG-RUN-REF`。
- 8911 无监听。

## 下一安全动作

在 `poc/medical_monitoring_ai_native_r4` 内按冻结 registry 实施 synthetic/offline D07 runtime/entrypoint，先建立 pre-evaluator integrity 与 exact raw-output/oracle/DSL replay，再实现医学评价、priority/owner/Query/Journey/lifecycle。任何合同或工件语义变更必须新版本并重新独立接受。
