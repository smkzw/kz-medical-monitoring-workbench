# R5-S5 公共权威合同接受记录

日期：2026-08-19  
判定：`ACCEPT_R5_S5_PUBLIC_AUTHORITY_CONTRACT`

## 冻结对象

- 合同说明：`reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md`
- 合同说明 SHA-256：`edc448a1d1e51e7e80b2830f9363408b82f506152742cbd664d8646d6f834d9a`
- Manifest：`artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json`
- Manifest 文件 SHA-256：`92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270`
- Manifest 内容哈希：`2cb6af131e1c1e4038d822e8b83c25adeb17c3aa0ade12d03fde825dab569c14`
- 独立审阅者：fresh-context `codex/gpt-5.6-sol:high`

其余冻结 SHA 由 manifest 的 `artifact_raw_sha256`、`source_file_sha256` 和
`protected_accepted_pins` 精确承载；本记录不建立第二份可漂移的权威清单。

## 接受范围

本判定只接受两项公共权威 producer 的合同形状、机器可执行约束和后续实现边界，
并仅解锁另行冻结、另行独立验收的 public-authority implementation contract。

本判定不是、也不得解释为：

- `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1`
- `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`
- `ACCEPT_R5_S5_CONTRACT`
- S5 runtime、UI、浏览器、真实项目/模型、临床真值、产品或生产接受

## 决定性证据

- normal/O2 generator `--check` 均通过，冻结产物数为 8。
- normal/O2 verifier 均通过：64 条父合同投影案例、194 条公共权威合同门禁，
  其中 138 条为完整重封的一致性案例。
- Ruff 通过。
- 两合同的 schema/version/audience 绑定、全部时间端点与研究日算法、八域适用性、
  source/visibility/locator、AE/MH 证据身份与 append-only 状态机均由机器门禁覆盖。
- 父 deferred overlay 为 52 条 exact pair：subject-temporal 45，AE/MH 7；source
  matrix 为 17 条，未把 reference-only 或未实现 producer 冒充为公共权威。
- 15 个 source pins、4 个保护路径 pins 与医学写作 542 文件聚合均复算一致；医学写作
  aggregate 为 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- verifier normal/O2 内置执行 no-runtime/no-test 与 8911 gate；公共权威/S5 runtime/test
  文件不存在，8911 无监听。
- 最终隔离审阅未发现 P0-P4 或新的完整重封 fail-open，并返回接受判定。

## 下一门禁

下一步只能创建并冻结 public-authority implementation contract。只有该实现合同被新的
隔离审阅者接受后，才可在其精确 create-only allowlist 内实现并测试两个 producer。
两个 producer 必须分别获得 `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1` 与
`ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`；在此之前 S5 合同与 runtime 继续锁定，8911
继续保持停止。
