# P10 LOOP 3.16：稳定 API 恢复与 V15/V16 真实候选重跑

日期：2026-07-31  
状态：进行中；MG-K10 V16 已通过候选科学性门，RUX V16 与方案证据包正在运行

## 目标

在规则身份/治疗对象四项纠偏通过后，受控恢复稳定 API，证明产品独立 AI 与提示词合同
切换正确，再以正式 API 串行重跑三项目 V15 字段映射。候选通过项目级科学性门之前，不
进入 adopt、draft assembly、医学确认或激活。

## 已完成边界

- 8911/5174 启动前均无监听。
- 21 个父级真实 runtime SQLite 已建立一致备份：
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_resume_20260731/`。
- 只启动 `scripts/start_stable_backend.zsh`；8911 readiness 为 ready。
- 独立 AI：`alibaba_token_plan/qwen3.8-max-preview`；
  `codex_runtime_dependency=false`。
- 三项目 V15 启动前均无当前合同 job；V13 历史不被当前状态接口选中。

## 当前运行

项目：`proj_mgk10_sar_real`  
批次：`monbatch_075b99489baf448a88b83c483ecf8eab`  
profile：`f1c6be3720e7dad13e36c8636914e79ca86923d4ce5998b42d0ce59770265e47`  
input：`4a1d76858751b4fb826699b99f40c4c224098fec6b11c99ea33cdba14c889fff`  
字段/作业：1,493 / 150  
首次进度：8 running、2 completed、140 queued

## 科学性验收顺序

1. 先检查 `EX1/EX2/EX4/EX5/EX7` 背景治疗是否保持 non-IP，不能启用
   `ip_exposure_adherence`。
2. 检查真实 `EX.EXPDOSE` 是否继续保留不确定语义，禁止自动合并计划/实际剂量。
3. 检查 `RES_7.ITOSSNUM` 是否为来源采集 iTOSS 总分，而非 procedure number 或
   无公式派生值。
4. 检查当前 listing 的 IP 暂停/恢复/剂量调整能力缺口是否显式保留，不能由
   CM、背景治疗、AE action 或自由文本补造。
5. 上述项目级门和跨项目 CM/IP、量表边界通过后，才启动 RUX、MY009 当前 V15，
   仍不自动 adopt。

## 恢复点

8911 由当前 Codex unified exec session 持有。不要重复启动服务或重复提交 MG-K10
V15。若任务中断，先查询同一批次 `field-mapping-status`；只有终态 failed/blocked
作业才允许通过正式 `retry_failed=true` 路径重试。

## 运行中早期科学性观察

在 43 completed / 8 running / 99 queued 时，只读检查已经完成的关键域首块：

- `EX1/EX2/EX4/EX5/EX7` 均将真实背景治疗标记为
  `object_identity=background_therapy`；给药日期/时间/执行字段保持 neutral 或
  background-treatment 语义，剂量为 unresolved。未观察到 IP 自证。
- 真实 `EX` 域中的 `EXDOSE` 与 `EXPDOSE` 均为 `object_identity=unresolved`、
  `dose_semantics=unresolved`，未自动合并为计划/实际剂量，也未启用 IP 依从性。
- `RES_7` 尚未进入执行，iTOSS 总分门待后续同一 V15 作业完成后检查。

这些是候选级早期观察，不等于整项目采用或 activation 通过；API 当前仍隐藏候选 payload
直至 150 个作业全部完成，且 draft/active mapping 均为空。

## V15 终态与 V16 定向纠偏

- MG-K10 V15 已完成 150/150；背景治疗、计划/实际剂量边界正确，但
  `RES_7.ITOSSNUM` 仍被输出为 `clinical_score_or_assessment_number`，同一问题也使
  两个量表总值保留 total/item 歧义。只读候选审计为 2 errors、32 warnings、
  9 observations，故 V15 未 adopt、未组装、未确认、未激活。
- 字段映射合同升级为 `monitoring-listing-field-mapping-v16`。服务端质量门只在量表/
  评估语境成立且同前缀至少有两个条目字段时，把来源已有的 `*NUM` 总值闭合为
  `scale.total_score`；保持 `source_collected`，不补造公式或派生值。候选审计同步新增
  score+number 混合角色阻断。
- 聚焦及联合回归：AI 服务、候选审计与语义质量 `242 passed`；AI API、启动恢复与 V7
  repair `39 passed`；全监查 `1016 passed, 25 warnings`。相关 Python 编译通过。
  当前环境无 Ruff，未声称 Ruff 通过。
- 相邻医学写作大集合 `2257 passed, 2 failed`；两项均为并行写作
  competitor-triage 当前措辞与旧测试不一致，不涉及本切片修改文件，未越界修复。

## MG-K10 V16 真实科学性门

- 正式 V16 作业 150/150 completed；两次单作业失败分别通过正式
  `retry_failed=true` 路径受控重试，最终无 failed/blocked。
- 背景治疗未被解释为 IP；`EXDOSE/EXPDOSE` 均保持
  `treatment_administration_dose + unresolved identity + unresolved dose semantics`
  和 `source_collected`。
- `ITNSSNUM/ITOSSNUM` 均闭合为 `scale.total_score`，保留真实同前缀条目关系，
  `derivation_lineage` 为空，未把来源总分伪装为系统复算。
- 候选审计为 0 errors、33 warnings、11 observations。证据：
  `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/mgk10_candidate_audit.json`
  与 `.md`。
- 纯内存正式语义质量评估覆盖 1,493 字段：`pass_with_warnings /
  activate_restricted`，0 global blockers、4 capability blockers。
  `ip_change_lifecycle` 因当前 listing 不能建立足够的试验药物对象与变更证据而
  `blocked_by_quality`；这是明确证据缺口，不是“未发生变更”。
- 当前候选仍全部为 proposed，draft、semantic-quality persistence 与 active mapping
  均为空；未执行医学决定。

## RUX V16 与方案证据包当前恢复点

- RUX 项目 `proj_rux_03_002`、批次
  `monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb` 已通过正式 API 创建 V16
  1,805 fields / 175 jobs。profile：
  `bc23dca0f1b85107110d0c1bbb7264014813751e01b26e2ca1db889c472e02ab`；
  input：
  `c856b63631897df44819391a5aee0eba2f50b64d603c707d15e3a0fac42a1f0b`。
- RUX V1.3 方案版本
  `protov_21c4b5a4a3883a8119d74e18` 的当前合同作业中，合并用药主题已有一个
  `proposed/pending_user_confirmation` 候选，保持未决定。
- 其余 7 个失败主题已通过唯一一次正式 `/start` 请求复用原 job 并执行
  `retry_terminal`；仓储按原 attempt count 加 2 扩展受控上限。请求返回时
  3 running、4 queued、0 failed。不得重复提交或自动决定候选。
- 8911 仍由当前 unified exec session 唯一持有；5174 仍停止。后续只做低频状态观察，
  RUX 全量终态后先生成只读候选审计与科学性断言，通过后才启动 MY009 V16。

## 2026-07-31 16:16 CST 无损暂停更新

用户要求在当前细分任务完成后无损暂停。方案 absence 否定语境假阳性和 MedDRA
词典支持字段 draft 归一已完成并通过全监查 `1129 passed`；RUX 方案终态为
2 candidate_review / 6 failed，RUX mapping 停点为
45 completed / 8 leased-running state / 122 queued。8911/5174 均已停止，
21 个 runtime SQLite 已做停机一致备份。详细恢复边界见
`context/monitoring_p10_loop316_v16_protocol_pause_20260731.md`。
