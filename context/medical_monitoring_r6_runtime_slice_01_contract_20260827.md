# R6 第一纵切执行合同（2026-08-27）

状态：`READY_FOR_GOVERNED_EXECUTION`

## 目标

把已接受的 R6 v0.1 prose、`contract.json` 与 86 行 challenge matrix 变成可重复执行的 synthetic/offline 确定性验证纵切。该纵切只证明机器合同、fixture、validator 与 metadata oracle 一致，不产生医学结论，也不等于 R6 产品或真实报告接受。

## 来源与前置状态

- `context/medical_monitoring_r5_s7_event_icon_refinement_checkpoint_20260827.md`：R5-S7 已接受，允许进入 R6。
- `context/medical_monitoring_r6_contract_acceptance_record_20260827.md`：R6 v0.1 合同稳定字节已接受。
- `context/medical_monitoring_r6_runtime_readiness_audit_20260827.md`：第一纵切最小范围、create-only 建议与完成门。
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md`、`artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/{contract,challenge_matrix}.json`：运行时唯一合同权威。

## 三个独立工作项

1. 合同与 fixture：只读加载并校验两份已接受 JSON；构造确定性 baseline fixture catalog，确保每个 JSON Pointer 在变异前存在且等于冻结 baseline。
2. 验证器与执行器：以 Python 标准库实现 11 个 validator 的最小 dispatcher，逐行执行一次 RFC 6902 replace，返回 canonical failure、blocking 与 projection。
3. 独立验证：覆盖 86/86 单变异、正向无阻断、49 个诊断码映射、禁止未声明诊断、normal/`-O`/`-OO`、多 `PYTHONHASHSEED`、双遍字节一致和只读边界。

## 允许创建的路径

仅允许在 `poc/medical_monitoring_ai_native_r6/` 下创建：

- `src/mm_r6/__init__.py`
- `src/mm_r6/contracts.py`
- `src/mm_r6/fixtures.py`
- `src/mm_r6/validator.py`
- `tests/conftest.py`
- `tests/test_contracts.py`
- `tests/test_validator.py`
- `tests/test_challenge_matrix.py`
- `evidence/r6_contract_runtime_receipt.json`
- `README.md`

以及本任务受治理的 `plans/`、`prompts/`、`runs/`、`logs/`、`metrics/`、`reviews/`、`context/` 过程与验收记录。若现状要求额外代码路径，必须先回到本合同修订，不得自行扩面。

## 禁止边界

- 不修改 `frontend/**`、`services/**`、`packages/**`、`runtime/**`、`deploy/**`、R1-R5 已接受代码/工件或任何医学写作路径。
- 不读取或运行真实项目、真实报告、OCR、模型/provider；不启动 8911、5174 或浏览器。
- 不增加数据库、服务、API、解析框架、插件框架、模型适配或第三方依赖。
- 不把 fixture/receipt 称为医学结论、报告审阅完成、产品接受或真实项目证据。

## 完成证据

- 86 个挑战各执行一次且 only-once；实际 outcome/error/projection 与 metadata oracle 一致。
- 11 个 validator、49 个诊断码、16 项禁止边界、三模式 output scope 和 raw/display 数值规则均有确定性检查。
- normal、`-O`、`-OO` 与至少三个 `PYTHONHASHSEED` 结果一致；fixture 双遍 canonical bytes 一致。
- 只读输入 SHA、医学写作聚合 SHA、Python 版本和运行结果写入 receipt；8911/5174 保持停止。
- governed execution audit 通过，独立 verifier 对稳定字节接受；Codex 复核源码、测试和边界后才关闭本纵切。
