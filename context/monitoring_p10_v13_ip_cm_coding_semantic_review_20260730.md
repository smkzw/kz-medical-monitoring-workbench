# 医学监查 P10：V13 IP/CM、编码、AE/MH 与量表语义专项审阅

## 1. 目标与边界

本轮对当前已完成的真实 V13 字段映射候选进行只读专项审阅，重点核对：

- RUX DAA/DAB 中试验药物实际给药、剂量调整、暂时停药、永久停药、重启、
  发放、回收和依从性是否与 CM 非试验用药严格分离；
- CM 中 WHO Drug、ATC 和项目药品代码是否具备真实编码体系、来源字段和独立版本血缘；
- AE/MH 报告术语、编码链、日期、严重性和严重程度是否保持独立；
- 量表来源总分是否被误当成工作台可复算总分。

运行库只通过 SQLite URI `mode=ro` 打开，并设置 `PRAGMA query_only=ON`。本轮没有：

- 接受、拒绝或修改任何 candidate decision；
- 组装、确认或激活字段映射；
- 直接写运行数据库；
- 修改 `main.py`、前端、方案监查准备、风险导出或医学写作文件。

## 2. 冻结审计快照

专项冻结报告：

- JSON：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_ip_cm_coding_review/audit_rux_final.json`
- Markdown：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_ip_cm_coding_review/audit_rux_final.md`
- 证据索引：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_ip_cm_coding_review/focused_evidence_index.json`

报告时点覆盖：

- 真实项目：RUX-03-002；
- 已完成 V13 作业：47；
- 项目-数据域：14；
- 字段出现次数：509；
- 候选层错误：0；
- 警告：26；
- 观察：3。

报告 SHA-256：

- JSON：`05f06e9562ad9fc927820d2689dec8bc7f3abb37a7d09ef7c86f4daff21081f2`
- Markdown：`7c143843bd3a1edaa2a112d8cd315608f2f3952be4eeabccd2b0d828ffa843df`
- 证据索引：`c61ef96e4e5845c56855ee2df638c3dfbe703dc5c6bed07bba0b917e3916f287`

审计完成后队列继续正常运行，RUX 已完成数增长到 48；上述报告仍是可复核的固定截点，
不把并发 worker 的正常写入归因于只读审计。

## 3. 发现与处理

### 3.1 DAA/DAB：未混入 CM，但 IP 能力曾可能被误报为 ready

当前 CM 候选没有被映射为试验药物实际给药或药物管理动作，候选层也没有把多个 IP
动作压成一个正式角色。因此，不重复既有“CM/IP 越界为 0”的结论。

新的缺口在于：DAB 已出现明确表达回收、未回收和依从性的来源角色，但这些角色仍落在
通用来源角色中。旧 full draft 质量门只检查“一个角色是否合并多个动作”，不会检查
“已表达动作但尚未进入闭合 IP 角色”，因此可能把 `ip_exposure_adherence` 误报为
`ready`。

代表性证据：

| 字段 | 证据 ID | Job | Business key | 结论 |
|---|---|---|---|---|
| `DAB.DABMECO` | `profile_cb213444d8745d714c2bab832e8a` | `monai_551722a37505adc2d5ce963e53da` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0001-of-0004` | 来源依从性百分比可展示，未绑定复算公式前不得形成确定性依从性结论 |
| `DAB.DABNRYN` | `profile_f40fc330719855f27ff98285890e` | 同上 | 同上 | 来源回收标志可展示，不能与实际给药混同 |
| `DAB.DABWDOSE` | `profile_3f46db73775ff1b87fa44807a17b` | `monai_9dff598c8935d9b99b888af151e3` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0002-of-0004` | “withdrawn dose”在缺少 CRF 标签时仍有回收量、取用量等歧义，不强制归类 |

修订：

- 新增 `G-CMIP-003`：单一回收、依从性、剂量调整等动作已被表达，但未进入闭合 IP
  角色时，保留来源值并阻断 `ip_exposure_adherence`；
- 不把该情况提升为全局阻断，也不自动替医学经理选择具体动作；
- DAA 的 `DAADAT`、`DAAPRES`、`DAAWEIGH` 继续保持保守来源语义。仅凭字段名和数值
  不能判定其是发放、处方、实际使用、回收或净重，因此不做项目特异硬编码；但新增
  `G-CMIP-004`，只要候选已表达药物呈交、称量、撤回剂量或盘点含义却未显式进入
  独立 IP 责任/盘点角色，就限制 `ip_exposure_adherence`，避免 full draft 静默放行。

DAA 代表定位：

- Job：`monai_e59cd28ddf98db9c7c1a375c3913`
- Business key：
  `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAA:0001-of-0003`
- Evidence：`profile_2816913b2139b80aa550632ff46c`、
  `profile_6502ddceef9f198133be67dd8bed`、
  `profile_66fd2dd2c08877793021703bed4a`

### 3.2 CM 药品编码：term-code 对应和“项目字典”不能冒充标准体系

RUX CM 当前存在三类来源字段：

1. ATC 各层级 code/term；
2. `DRUGCODE/DRUGPTCD/DRUGPTNM` 等药品代码和术语；
3. 独立字段 `DRUGVER`。

当前候选均保守保留为 `source_collected` 或 `source_metadata`，没有直接声明为
`standardized_coded`，这一点正确。但旧质量门存在三个遗漏：

- 只识别部分 ATC 角色，可能漏掉药品代码和术语；
- `MDRAVER/MDRALANG/DRUGVER` 等真实支撑字段未全部进入闭合角色目录；
- 仅有 `coding_system + dictionary_version` 字符串即可通过，未验证来源字段真实存在，
  也未验证版本来自同域独立字段。

代表性证据：

| 字段 | 证据 ID | Job | Business key | 结论 |
|---|---|---|---|---|
| `CM.ATC1CODE` | `profile_57eabde8fdf9446cc6b6bab7056e` | `monai_6d93516027ba3aad05be68e0a0df` | `...:CM:0001-of-0005` | 形态和 term-code 对应不能证明编码体系及版本 |
| `CM.DRUGCODE` | `profile_bc385ce06e44db6dacd1e8a023c4` | `monai_572bc13e67b6c1092c5dd0876e9d` | `...:CM:0003-of-0005` | 缺少明确词典身份和独立版本绑定 |
| `CM.DRUGPTCD` | `profile_b77bdf3ff5fff8a913f8f2bb856d` | `monai_9fa48ac94b9e2c7eb7e15e696d55` | `...:CM:0004-of-0005` | term-code 配对仍只是来源事实 |
| `CM.DRUGVER` | `profile_8c487cf9ceff7b3397c26a9d0a04` | 同上 | 同上 | 版本字段存在，但尚未绑定到一个已明确的标准药品词典 |

修订：

- 补齐 MedDRA/药品词典版本、语言、药品报告代码/术语和 ATC code/term 的闭合角色；
- 编码血缘必须同时具备：
  - 明确且非“项目字典/未明确字典/term-code 对应”的编码体系；
  - 真实存在的来源字段；
  - 同域、独立、可识别为版本支撑字段的 `dictionary_version_field`；
- `source_collected` 血缘不足时只阻断 `standard_coding_rules`，原始 term/code 仍可展示；
- 已声明 `standardized_coded` 却缺少上述血缘时仍为全局阻断。

因此，`DRUGVER` 不能单独证明 WHO Drug；ATC 字段也不能因名称和代码形态直接升级为
标准编码。

### 3.3 AE/MH：严重性与严重程度正确分离，但 MedDRA 链缺少报告术语锚点

当前真实候选中：

- `AETERM` 为来源报告术语；
- `AESER` 为严重性；
- `AETOXGR` 为严重程度/毒性分级；
- MedDRA LLT/PT/HLT/HLGT/SOC 代码和术语保持独立；
- `MDRAVER` 为独立版本字段。

没有发现严重性与严重程度合并，也没有发现 AE 与 MH 来源角色互换。

代表性证据：

| 字段 | 证据 ID | Job | Business key |
|---|---|---|---|
| `AE.AESER` | `profile_2e93cf8f3a950661f81d592ae261` | `monai_67d45de95cd591a1000ab73809c4` | `...:AE:0002-of-0006` |
| `AE.AETERM` | `profile_3b95e617ea427192c8c5d20187d2` | `monai_811df599dd9f73603005c668c8e0` | `...:AE:0003-of-0006` |
| `AE.AETOXGR` | `profile_cc97348071ca4f4a108a9880dd9c` | 同上 | 同上 |
| `AE.MDRAVER` | `profile_75d5c4c9543840f87b6f404a062d` | `monai_bada17433ea600cd6f8ea3794b43` | `...:AE:0005-of-0006` |
| `AE.PTCODE` | `profile_950f70d3ec01e3ead2c27fd3ad01` | 同上 | 同上 |

遗漏在于：当前 MedDRA 字段的 `source_fields` 只在 code 和 term 之间互相引用，并未把
`AETERM` 作为报告术语来源锚点。旧审计因此把 10 个 MedDRA 结果判为“完整血缘”，
但该链不能证明“报告术语 → 标准术语/代码”的确定性追踪。

修订：

- 新增 `G-AEMH-001`：存在报告术语和标准 MedDRA 链，但编码链没有引用报告术语时，
  阻断 `ae_mh_reconciliation`，不否定来源编码字段本身；
- 新增项目中立的 AE/MH 域互换检查；
- 新增严重性与严重程度合并检查；
- 当前候选只触发“来源锚点缺失”，不触发后两项错误。

### 3.4 量表：当前边界正确，不做额外代码修改

当前来源总分：

- `CDLQI.CDLQIRES`：
  `profile_dbb00891f3bd25953062a41070aa`
- `DLQI.DLQIRES`：
  `profile_75f9a52b1254c83b3f79c8c47c20`
- `EASI.EASISCOS`：
  `profile_17974b8403b4940c1823f0fb3f84`

均为 `source_collected`。审计只将其列为观察项；正式质量门继续以 `G-SCALE-001`
限制 `scale_recalculation`。没有发现把来源总分声明为工作台复算结果的证据，因此本轮
不改量表规则。

## 4. Full draft 质量门变化

对已完成 RUX 候选做非正式、只读的子集投影后，结果由“IP/AE-MH 能力可能误报为
ready”改为：

- `raw_source_review`：ready；
- `subject_timeline`：limited；
- `patient_profile`：limited；
- `standard_coding_rules`：blocked_by_quality；
- `ae_mh_reconciliation`：blocked_by_quality；
- `ip_exposure_adherence`：blocked_by_quality；
- `scale_recalculation`：blocked_by_quality。

该投影不是正式 full draft：队列仍未全部完成，候选也尚未接受。正式组装时还会从冻结
字段画像注入部分日期 `value_constraints`，因此候选子集当前显示的
`precise_temporal_rules=ready` 不代表最终精确时间能力可用。

## 5. 代码与测试

修改范围：

- `services/api/app/monitoring_mapping_semantic_quality.py`
- `scripts/monitoring_mapping_candidate_audit.py`
- `tests/test_monitoring_mapping_semantic_quality.py`
- `tests/test_monitoring_mapping_candidate_audit.py`

聚焦回归：

- candidate audit + semantic quality：67 项通过；
- semantic quality、draft、activation、batch lifecycle、daily run、capability guard、
  record resolver 联合：161 项通过；
- `py_compile`：通过；
- Ruff `E4/E7/E9/F`：通过。

默认全规则 Ruff 仍报告该脚本及相邻旧文件的既有风格/现代化建议；本轮未以专项语义修订
为由扩大格式化范围。

## 6. 只读状态复核

复核时：

- `PRAGMA query_only=1`；
- RUX V13 共 175 个作业；
- 48 completed、125 queued、2 running；
- 48 个候选全部为 `proposed`；
- `decided_at/decided_by/decision_reason` 非空记录为 0。

因此，本轮没有 candidate decision、确认或激活副作用。

## 7. 后续使用点

1. 等待全部 V13 作业完成后重跑本审计，不沿用当前截点代替全量结论。
2. DAA/DAB 的具体动作必须结合 CRF/ODM 标签、方案条款及实际行级关系确认；不能把
   `DABWDOSE` 等歧义字段按名称硬编码为发放、回收或实际给药。
3. 若项目能确认实际药品词典身份，应在正式 draft 中将 `DRUGVER` 绑定到对应编码链；
   若不能确认，保留来源代码并继续限制标准编码规则。
4. MedDRA 链需补充 `AETERM` 来源锚点，或明确说明该链仅是来源系统已编码结果且不能
   用于报告术语追踪。
5. 只有完整 draft 的全局不变量通过后，才允许受限激活；本轮没有提供任何 override。

## 8. 三项目检查点复核与最新结论

### 8.1 权威检查点与修订后快照

新增冻结检查点：

- `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_semantic_gate/audit_checkpoint_0358.json`
- `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_semantic_gate/audit_checkpoint_0358.md`
- 覆盖 3 个项目、114 个完成作业、42 个项目-数据域、1,195 个字段出现；
- 0 error、36 warning、30 observation；
- JSON 文件 SHA-256：
  `ec10d309d91d408bc89b4d869ad0584666970a74a51deb65292d13030647fff4`；
- Markdown 文件 SHA-256：
  `249dcc8d21f8118f69983dc28f999cb6368814b052f2aeb1f2f130f70a590699`。

修订后以同一 SQLite `mode=ro/query_only` 路径重跑时，队列已自然增长至 124 个完成
作业、45 个项目-数据域和 1,298 个字段出现。结果仍为 0 error；48 个 warning 中，
新增的是此前漏检的 IP 盘点候选和后续完成作业，不是把既有错误降级为通过。

修订后证据：

- JSON：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_semantic_gate/v13_clinical_semantic_review_20260730/audit_revised.json`
- Markdown：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_semantic_gate/v13_clinical_semantic_review_20260730/audit_revised.md`
- 完成候选质量门投影：
  `runs/execution/medical_monitoring_p10_20260730/loop_1_v13_semantic_gate/v13_clinical_semantic_review_20260730/completed_candidate_semantic_projection.json`
- 对应 SHA-256：
  `7de18fd44ec67d762c52f04f85058f0c54a9e62ed538b35ff903f6d753129c78`、
  `16f3e46fce34ca7d2619d7a557f7b0c92d7108b10a70e1bd5b2210f9f249792d`、
  `dc0440d6a65a942d59ebba0d5b828acbe59dd34adc89884f08e44b1748933b66`。

### 8.2 IP 动作与责任/盘点：目录缺口和候选真错已分开

确认属于项目中立目录缺口并已修订：

| 来源 | Evidence | Job | Business key | 处理 |
|---|---|---|---|---|
| `EX.EXDAT/EXTIM` | `profile_4a283ef2f390b2a03bda56a4e395` / `profile_0ebed2e2308ceb3044180b7ad82a` | `monai_3e87187e9edce75a14a6bc914d4c` | `listing-field-mapping:monbatch_075b99489baf448a88b83c483ecf8eab:EX:0001-of-0003` | `exposure_administration_*` 归入独立 IP 实际给药日期/时间 |
| `DAB.DAADOFRQ` | `profile_06384f9b4b2ba73a0d2340e7a69b` | `monai_551722a37505adc2d5ce963e53da` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0001-of-0004` | 归入 IP 给药频率/间隔原始值，不冒充已标准化频率 |
| `DAB.DABMECO` | `profile_cb213444d8745d714c2bab832e8a` | 同上 | 同上 | 归入独立 IP 依从性来源结果；无公式时仍不得复算 |
| `DAB.DABNRYN` | `profile_f40fc330719855f27ff98285890e` | 同上 | 同上 | 归入独立 IP 回收状态，不与给药或 CM 混同 |

仍属候选真错或真实歧义、没有通过别名静默消除：

- `ECA.ECADAT/ECANOTE` 使用项目缩写角色，虽然文字提示 administration，但未显式声明
  通用 IP 角色；继续触发 `XJOB-IP-ACTION-ROLE-UNRESOLVED`。定位：
  `monai_ff312662677d7d20c00d3f44a3e6` /
  `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:ECA:0001-of-0003`，
  Evidence `profile_c0319e2ef005615c7524850908da`、
  `profile_c8f692eb1197b785c478596420fc`。
- `DAB.DABNRNUM` 明确写成 returned 或 unreturned 二选一，不能自动断言是回收量；
  `DAB.DABNRFID` 也未证明是药盒、发药号还是回收容器。二者继续限制 IP 暴露/依从性能力。
- DAA 的药物呈交量、称量值以及 DAB 的 withdrawn dose 被新增
  `XJOB-IP-ACCOUNTABILITY-ROLE-UNRESOLVED` / `G-CMIP-004` 捕获；保留原始值，
  但不能直接进入发放、回收、实际给药或依从性计算。
- 后续完成的 ECB 剂量调整候选使用 `ecb_*` 项目角色，亦保持未闭合状态；剂量调整没有
  被合并到 administration、interruption、discontinuation 或 restart。

因此，`administration / dose_adjustment / interruption / discontinuation / restart /
dispense / return / compliance` 仍是八个独立动作族，IP 与 CM 边界没有因目录扩展而
放宽。

### 8.3 RUX AE MedDRA：由 draft assembly 消化，但不能隐式推定

检查点的跨 chunk 警告是组装层义务，不是单个候选作业能够独立消除的问题：

- 报告术语定位：
  `monai_811df599dd9f73603005c668c8e0` /
  `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0003-of-0006` /
  `AE.AETERM`；
- PT 与版本定位：
  `monai_bada17433ea600cd6f8ea3794b43` /
  `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0005-of-0006` /
  `AE.PTCODE`、`AE.PTTERM`、`AE.MDRAVER`。

审计现在显式标记
`resolution=draft_assembly_cross_chunk_anchor`。正式 draft assembly 应在同一项目、
同一数据域、同一冻结输入修订内形成可审计的 `AETERM -> LLT/PT/...` 来源锚点；在该
锚点真实写入 draft 之前，`G-AEMH-001` 继续只阻断 `ae_mh_reconciliation`，不能由
质量门凭字段共存自动推定血缘。后续同会话窄实现已按第 9 节补入 draft assembly，
没有改变候选或运行库状态。

### 8.4 RUX CM 与 MY009 重复 AETERM：能力限制，不是全局阻断

结论保持：

- RUX ATC、`DRUGCODE/DRUGPTCD/DRUGPTNM` 仅可作为来源 code/term 展示；在缺少明确
  编码体系、真实来源字段和独立版本绑定时，触发 `G-CODE-002`，仅限制
  `standard_coding_rules`。
- `DRUGLANG` 若本身仍被候选标成 `source_collected`，不能充当独立版本/语言支撑字段；
  只有字段性质和角色均为元数据支撑时才可进入血缘。
- MY009 `AETERM__3` 至 `AETERM__6` 当前是 `unmapped` 的 MedDRA 样候选，未声明
  `standardized_coded`，因此仅保留来源并限制标准编码能力。定位：
  `monai_ad8a66b2df3249c47186b8c75e9e` /
  `listing-field-mapping:monbatch_71a1d2023a4b4432b954ffc74934a60e:AE:0003-of-0004`，
  Evidence `profile_110fad03f6755a5503bbae7eee05`、
  `profile_da0defc59642267c89760b1763a0`、
  `profile_44e11bba3fcc6e8f91912a021409`、
  `profile_d96b8ca9c0472114ea22b23a5cb1`。
- 只有字段主动声明 `standardized_coded` 且血缘仍不完整时，才触发
  `G-CODE-003` 全局阻断；本检查点没有此类 error。

### 8.5 Full draft 误判风险与验证

只读完成候选投影不是正式 draft，但可验证质量门方向：

- RUX：`pass_with_warnings / activate_restricted`；AE/MH 对账、IP 暴露/依从性、
  标准编码和量表复算均按缺口限制，没有全局阻断。
- MY009：`pass_with_warnings / activate_restricted`；重复 AETERM 仅限制标准编码。
- MG-K10-SAR：仍由 `EX.EXPDOSE` 的“计划或实际剂量混合文本”触发一个
  `G-ROLE-002` 全局阻断；这是候选真实歧义，不应通过目录扩展消除。

验证：

- semantic quality + candidate audit：69 项通过；
- semantic quality、candidate audit、draft、activation、batch lifecycle、daily run、
  capability guard、record resolver 联合：190 项通过；
- `py_compile`：通过；
- Ruff `E4/E7/E9/F`：通过。

最终只读复核时 V13 候选自然增长至 130 个，全部仍为 `proposed`；
`decided_at/decided_by/decision_reason` 非空计数均为 0。本轮没有 candidate decision、
确认、激活或数据库直写。

## 9. MedDRA 跨 chunk source anchor 组装闭环

### 9.1 组装合同

`monitoring_mapping_draft_repository` 现在只在完整 source set 已通过原有冻结校验后，
为明确闭合的 MedDRA 编码链补充报告术语锚点。必须同时满足：

1. 所有作业属于同一项目、同一批次、同一完整字段画像和同一输入修订；
2. 预期数据域、chunk 槽位和字段覆盖完整，且每个 chunk 只有一个已接受候选；
3. draft 字段与 `field_sources` 一一对应，来源作业全部属于本次
   `expected_job_ids`，输入修订与本次冻结修订一致；
4. 在同一个 `AE` 或 `MH` 域内，存在闭合的报告术语角色，字段性质仍是
   `source_collected`；
5. 同域存在闭合的 MedDRA 标准术语/代码角色，且候选已明确声明为
   `standardized_coded`；
6. 同域存在独立的 `MDRAVER` 版本角色，字段性质为 `source_metadata`，并且标准字段
   原有 lineage 已显式引用该版本字段；
7. 标准字段原有 `coding_system` 明确为 MedDRA，原有 `source_fields` 均真实存在于
   同域、本次完整冻结 source set。

全部条件满足时，组装层只在标准字段既有 `derivation_lineage.source_fields` 中追加
报告术语字段，并写入 `monitoring_meddra_source_anchor_v1` 显式合同。合同记录：

- 同项目、同域、完整冻结 source set 的作用域；
- 报告术语字段和独立版本字段；
- 输入修订 SHA-256 和 source set SHA-256。

组装层不会：

- 修改任何字段的 `field_kind`；
- 将 `source_collected` 因字段共存升级为 `standardized_coded`；
- 补写或猜测词典版本值；
- 为缺失编码体系、版本绑定或来源字段的 lineage 代填信息；
- 跨 AE/MH 域或跨项目借用报告术语。

任何条件缺失时，draft 保持候选原样，能力继续由质量门限制。

### 9.2 G-AEMH-001 的逐域关闭

`G-AEMH-001` 已由原来的全体 AE/MH 聚合判断改为逐域判断：

- 每一个同域标准 MedDRA 字段都必须锚定同域报告术语；
- 同域缺少报告术语时直接保持 `ae_mh_reconciliation` capability-blocked；
- AE 的报告术语不能使 MH 的编码链通过，反之亦然；
- 编码体系、真实来源字段和独立版本绑定仍由 `G-CODE-*` 独立验证。

该修订只关闭此前报告 8.3 所述的误判窗口，不改变 AE/MH 报告术语、严重性、严重程度
或日期边界，也不放宽标准编码声明。

### 9.3 验证

隔离临时库覆盖：

- 跨 chunk 成功：`AETERM`、PT code/term、`MDRAVER` 分属不同 chunk，组装后每个
  标准字段均形成可审计锚点，`G-AEMH-001` 关闭；
- 缺版本：不补锚点，`G-AEMH-001` 保持，编码 lineage 继续由 `G-CODE-*` 处理；
- 缺报告术语：不补锚点，同域 AE/MH 对账能力保持受限；
- 跨域：AE 报告术语不能锚定 MH MedDRA 链；
- 来源字段不得升级：MedDRA 样 code/term 若仍是 `source_collected`，组装后字段性质
  与 lineage 均保持原样。

验证结果：

- draft repository + semantic quality 聚焦测试：95 项通过；
- semantic quality、candidate audit、draft、activation、batch lifecycle、daily run、
  capability guard、record resolver 相邻联合回归：197 项通过；
- `py_compile`：通过；
- Ruff `E4/E7/E9/F`：通过。

修改范围：

- `services/api/app/monitoring_mapping_draft_repository.py`
- `services/api/app/monitoring_mapping_semantic_quality.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_semantic_quality.py`

未修改 `main.py`、前端、方案准备、风险导出、医学写作或运行数据库。真实 RUX 证据定位
仍为 8.3 中列出的 `AE.AETERM` 与 `AE.PTCODE/PTTERM/MDRAVER` 作业；这些候选仍未由
用户接受，因此本窄实现没有越权组装真实 draft，也不把隔离测试结果冒充生产数据验证。
