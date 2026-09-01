# P10 V10 字段映射部分完成块医学/数据语义质量审阅

## 1. 审阅目的与边界

本次仅对 `proj_rux_03_002`、`prompt_version=monitoring-listing-field-mapping-v10` 在固定截点前已经完成并形成候选的字段映射块进行只读医学与数据语义审阅，重点检查：

- 输入 field profile 是否逐字段、恰好一次地被输出映射覆盖；
- `recommended_role` 是否准确、稳定且可跨域、跨项目泛化；
- AE、MH、LB、疗效、访视、受试者、中心关键字段是否可支持后续医学监查；
- CM 非试验用药与试验药物给药、发放、回收、剂量调整及依从性的边界；
- 日期、数值、单位、参考范围的配对与语义；
- 编码字段和派生字段的血缘；
- `confidence`、`uncertainty`、`user_action` 是否真正帮助医学经理完成确认。

本次没有修改代码、数据库、运行队列、候选、草稿、映射状态或既有记录，也没有读取后写回任何状态。本文不记录任何受试者级原始值。

## 2. 数据源与固定截点

### 2.1 实际读取的数据源

工作区内 `runtime/medical_monitoring_ai.sqlite3` 为 0 字节空文件；当前运行态实际使用的数据源为工作台总运行目录下的 `medical_monitoring_ai.sqlite3`。本次以运行态数据库为来源，只读查询其主库及 WAL 可见状态。

后续应避免仅凭相对路径开展 QC；每次审阅前应先确认 API 实际解析后的运行目录和数据库非空，防止误读占位文件。

### 2.2 审阅截点

- 固定截点：`2026-07-29T17:14:40.779049+00:00`，即北京时间 `2026-07-30 01:14:40`。
- 纳入条件：项目、提示词版本匹配，job 状态为 `completed`，存在候选，且 `updated_at` 不晚于固定截点。
- 纳入 34 个完成块、359 个字段映射。
- 纳入域：AE、AH、BSA、CDLQI、CM、CODE_LIST、DAA、DAB、DLQI、DM。
- 队列在审阅期间继续运行；固定截点后新完成的块不纳入本文，也不据此更新本文结论。

各域纳入情况：

| 域 | 完成块 | 字段数 | 最低置信度 | 未映射字段 |
|---|---:|---:|---:|---:|
| AE | 6 | 67 | 0.35 | 3 |
| AH | 1 | 11 | 0.82 | 0 |
| BSA | 3 | 29 | 0.62 | 0 |
| CDLQI | 4 | 46 | 0.55 | 0 |
| CM | 5 | 59 | 0.62 | 0 |
| CODE_LIST | 1 | 4 | 0.20 | 4 |
| DAA | 3 | 30 | 0.72 | 0 |
| DAB | 4 | 40 | 0.30 | 1 |
| DLQI | 4 | 46 | 0.70 | 0 |
| DM | 3 | 27 | 0.60 | 0 |

AH 仅完成第 2/2 块，内容为通用技术/身份元数据；不能据此评价病史术语、起止日期或持续状态。LB 在固定截点前没有完成块，因此本文不评价实验室结果、单位、参考范围、异常标志或临床意义判断。

## 3. 总体结论

### 3.1 已达到的质量

1. **逐字段覆盖通过。** 34 个完成块的输入 `(domain, field)` 与输出 `(domain, source_field)` 集合完全一致；359 个字段均恰好出现一次，未见遗漏、重复或越界新增。
2. **基础证据字段完整。** 359 项均有 evidence、uncertainty 和 user_action；没有空证据、空不确定性或空用户动作。
3. **核心身份字段总体识别正确。** `SUBJID`、`SITEID`、`VISTOID`、重复键和删除标志等技术字段大多由确定性规则识别为 `source_metadata`，受试者、中心和访视关联的基础具备。
4. **CM 与药物管理域未发生直接混域。** 已完成块中，CM 均使用非试验用药/治疗语义；DAA/DAB 保留为试验药物发放、回收或药物管理相关语义，没有被归入 CM。
5. **对证据不足的派生语义总体较克制。** 当前没有把字段直接标为 `deterministic_derived`；全空 CODE_LIST 字段全部保留为 `unmapped`，AE 的可疑派生日期也未强行认定为确定性派生。

### 3.2 当前不能直接激活的主要原因

1. 同一来源字段跨域产生多个角色名，部分 `field_kind` 也不一致，尚不具备稳定的跨域统一语义层。
2. DAA/DAB 内多个试验药物管理字段含义仍不确定，个别角色可能错误地把“间隔/数量/结果编码”解释为“给药频率”或泛化的“评估结果”。
3. AE 的 MedDRA 层级和 CM 的药品编码血缘判定不一致；部分字段被标为标准编码，但编码体系身份或版本适用性仍未得到充分证明。
4. AE/CM 的起止日期存在 mixed 类型，尚未显式承载部分日期、精度及解析状态；不能直接按完整日期参与时间窗、先后顺序或漏报规则。
5. DLQI/CDLQI 的题目值、显示文本、条件分支和总分血缘尚不充分；BSA 的“标准化结果”名称可能超出当前证据。
6. 低置信度字段虽然给出了动作，但大量高置信度技术元数据重复使用同一模板动作，对医学经理没有有效决策价值。
7. TRT/实际给药或暴露、完整 AH/MH、LB 等关键域尚未在本固定截点完成，无法完成全项目边界验证。

**结论：V10 部分完成块的结构完整性可接受，但医学语义层尚未达到项目映射激活门槛。**

## 4. 逐项问题与精确定位

以下问题均只针对固定截点前完成的候选。

| 优先级 | job | business_key | domain | source_field | 问题 | 建议 |
|---|---|---|---|---|---|---|
| P0 | `monai_3aa46a9fe85f0f463af5eebea057` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0004-of-0006` | AE | `HLGTCODE`、`HLGTTERM`、`HLTCODE`、`HLTTERM`、`LLTCODE`、`LLTTERM` | 这些层级被标为 `standardized_coded`，但同一 MedDRA 链中的 PT 被标为来源采集、SOC 代码被保留为未映射，导致同一编码链判定不一致。 | 将 MedDRA 层级作为一个整体复核：逐层确认 code-term 同行配对、`MDRAVER` 适用性和语言字段；统一 PT、LLT、HLT、HLGT、SOC 的 field_kind 和血缘规则。 |
| P0 | `monai_721ba1d6706ec72270ee4bd58195` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0005-of-0006` | AE | `PTCODE`、`PTTERM` | 已识别为 MedDRA PT，但仍为 `source_collected`，与同批 HLGT/HLT/LLT 的 `standardized_coded` 判定冲突。 | 在完整域关系和版本适用性证据下统一处理；证据不足时整条 MedDRA 链均不应被当作已确认标准编码用于规则。 |
| P0 | `monai_a76e2a3e4048035cfa6daaa764b1` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0006-of-0006` | AE | `SOCCODE`、`SOCTERM` | SOC 代码为 `unmapped`、SOC 术语为 `source_collected`，同样与其他 MedDRA 层级的处理不一致。 | 与 PT/LLT/HLT/HLGT 一并复核并建立统一编码血缘。 |
| P0 | `monai_860129dca95c8d55819fb1c8cb18` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0004-of-0005` | CM | `DRUGPTCD` | 标为 `standardized_coded`，但 coding system 实际仅表述为“项目药品词典首选术语代码”，尚未确认具体词典身份；`DRUGVER` 也可能是导出版本而非词典版本。 | 激活前必须确认具体药品词典名称、版本字段、代码-首选术语同行关系和版本适用范围；未确认前降级为来源采集编码，不能作为标准药品编码事实。 |
| P0 | `monai_2d4581401390641a8ae48a718b35` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0001-of-0004` | DAB | `DAADOFRQ` | 推荐角色为 `dosing_frequency`，但画像只能支持其可能是频率、间隔、周期天数或药物管理数量；该解释可能直接影响依从性和方案违背判断。 | 在 CRF/数据字典确认前设为未确认药物管理参数，不得进入给药频率或依从性规则。确认后采用明确的 `ip_*` 角色，例如给药频次、发药间隔或日供给量。 |
| P0 | `monai_a042366196b435b089d1c78aa593` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0002-of-0004` | DAB | `DAPDOFRQ` | 推荐角色为 `prior_drug_dispense_offset_day`，但缺少参照日期、计算公式和 CRF 定义。 | 确认是否为前次发药间隔、计划天数或其他管理参数；未确认前不得参与时间窗或依从性计算。 |
| P0 | `monai_7a4c636ebb4fa9d30e936e21a0ed` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAA:0001-of-0003` | DAA | `DAAORRES`、`DAAPRES`、`DAAREFID` | `original_result_count`、`present_or_dispensed_count`、`reference_identifier` 仍无法明确区分发放数量、领取数量、药物编号或记录编号。 | 必须结合“研究药物发放”CRF 和数据字典明确每个字段对象、单位和主键关系；角色使用 `ip_dispense_*` 命名，避免通用 `result`/`reference`。 |
| P1 | `monai_9e2735d4695c7bba3897200fe986` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0003-of-0005` | CM | `CMPERYN_TXT` | 角色为 `concomitant_medication_persistent_use_flag_text`，但字段名更接近 periodic；“周期性使用”与“持续使用”医学含义不同。 | 对照 CRF 确认是周期性、长期持续还是其他标志；确认前不得用于持续用药或停药逻辑。 |
| P1 | `monai_f39c46d1334160dd27bf388deb93` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0003-of-0006` | AE | `AESTDAT`、`AESTDATD` | `AESTDAT` 为 mixed 类型；`AESTDATD` 虽为日期型但缺少公式和派生血缘。候选把前者作为开始日期、后者谨慎保留为未映射，方向正确但仍缺日期精度模型。 | 保留原始日期文本、解析结果、精度和解析状态；`AESTDATD` 仅在数据字典或公式确认后才能作为派生日期。 |
| P1 | `monai_b3c3f0305453cab35abac352c69c` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0001-of-0006` | AE | `AEENDAT` | mixed 类型被映射为 AE 结束日期，若包含部分日期或非日期标记，直接参与持续时间计算会产生错误。 | 要求日期精度和解析状态；与 ongoing 标志联合判断，禁止静默补齐缺失年月日。 |
| P1 | `monai_83227a41f2b99f7f916c9faeddac` / `monai_9e2735d4695c7bba3897200fe986` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0002-of-0005` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0003-of-0005` | CM | `CMENDAT`、`CMSTDAT` | 两个日期均为 mixed 类型；当前角色未显式表达部分日期与解析精度。 | 与 AE 日期采用同一跨域日期模型，保留原文、最小/最大可能日期和精度，不得把部分日期当完整日期。 |
| P1 | `monai_227c9a0fca963a90abeb94cc330d` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:BSA:0001-of-0003` | BSA | `BSARESS` | 角色命名为 `bsa_result_standardized_numeric`，但没有公式或标准化规则；field_kind 仍为来源采集。角色名可能使下游误以为已标准化。 | 在确认其为 EDC 直接采集值还是派生/标准化值前，使用中性角色；若为派生值，补充源字段、公式、单位转换和复算证据。 |
| P1 | `monai_0c432a452bd65df8010d84858865` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CDLQI:0002-of-0004` | CDLQI | `CDLQIRES` | 可疑总分字段未关联各题目字段，也没有评分公式；与 DLQI 总分候选的 related_fields 处理不一致。 | 确认是采集总分还是系统计算总分；若为计算值，补充题目、条件分支、缺失处理和总分公式后再建立派生血缘。 |
| P1 | `monai_722e6a00492cabcae70affe174d2` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DLQI:0003-of-0004` | DLQI | `DLQIRES` | 已关联题目字段但仍缺少可复算公式、条件项和缺失规则，不能视为确定性派生。 | 保留为来源采集总分，直至使用完整量表规则进行独立复算；复算不一致应单独形成数据质量风险。 |
| P1 | `monai_c2a8b5b44d0fcd09b2b376d793f8` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DLQI:0002-of-0004` | DLQI | `DLQIQ7`、`DLQIQ7_TXT`、`DLQIQ7NO`、`DLQIQ7NO_TXT` | 已识别条件分支，但缺少正式题干、触发逻辑和计分规则；数值字段有时命名为 value、有时其他域命名为 code。 | 建立统一的“采集代码/显示文本/计分值”三层角色；确认条件分支后再用于总分复算和缺失检查。 |
| P1 | `monai_de92ed92ceca0a84ea07120050e4` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CDLQI:0001-of-0004` | CDLQI | `CDLQ7NA`、`CDLQ7NA_TXT` | 低置信度识别为条目代码/术语，但没有同行 code-term 关系或正式量表定义。 | 作为待确认条件项，不得直接用于量表评分或标准术语判断。 |
| P1 | `monai_3aa46a9fe85f0f463af5eebea057` / `monai_860129dca95c8d55819fb1c8cb18` / `monai_a042366196b435b089d1c78aa593` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0004-of-0006` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0004-of-0005` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0002-of-0004` | AE / CM / DAB | `FORMNM` | 同名技术字段 `FORMNM` 在已完成域中出现 4 种 recommended_role。 | 统一为跨域稳定角色，例如 `metadata.form_display_name`；表单具体名称应作为值或域属性，不进入角色名。 |
| P1 | `monai_3aa46a9fe85f0f463af5eebea057` / `monai_44d691c00e9a6c74da9a91659c7c` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0004-of-0006` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:DAB:0003-of-0004` | AE / DAB | `GROUPID`、`ISDEL`、`PAGELMBY`、`PAGELMDT` | 同一技术字段在不同域被加上 AE/EDC 前缀或不加前缀，形成不同角色。 | 对 EDC 技术元数据采用固定全局角色，不按业务域改名；域由独立字段表达。 |
| P1 | `monai_e5e0425d51480912f54f839293ba` / `monai_f4a0204fe7512a9a838b3088dd95` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:BSA:0002-of-0003` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0005-of-0005` | BSA / CM | `PSTUDYID`、`PSTUDYNM` | BSA 中为 `source_collected`，CM 中为 `source_metadata`；同一项目标识字段来源性质不一致。 | 统一为项目级来源元数据，并由项目主数据核验；不应因业务域不同改变 field_kind。 |
| P1 | `monai_fd6ac90fe8a9e401f74b172e9075` / `monai_f4a0204fe7512a9a838b3088dd95` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:BSA:0003-of-0003` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CM:0005-of-0005` | BSA / CM | `VISIT` | 同一字段分别命名为 `visit_name`、`visit_display_name`。 | 统一为 `visit.display_name`；计划访视标识、访视日期、计划外访视和访视窗应由独立角色表达。 |
| P2 | `monai_fbcec91a192894841721c12a6b4f` | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:CODE_LIST:0001-of-0001` | CODE_LIST | 全部 4 个字段 | 全空字段全部标为 `unmapped`，符合证据边界；但这一空表不能承担任何代码字典证明。 | 维持未映射，不阻塞其他域；后续若导入非空代码表，应重新画像而非沿用本候选。 |
| P2 | `monai_3aa46a9fe85f0f463af5eebea057` / `monai_fd6ac90fe8a9e401f74b172e9075`（代表性定位） | `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:AE:0004-of-0006` / `listing-field-mapping:monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb:BSA:0003-of-0003` | AE / BSA（同类问题跨多域） | `FORMOID`、`FORMREP`、`RECREP`、`SITEID`、`SUBJID`、`VISTOID` 等 | 61 个字段使用完全相同的 user_action：“如项目数据字典将该字段定义为业务采集值，请在映射草稿中修订。”对医学经理重复且价值低。 | 对高置信度确定性元数据默认折叠为“系统元数据，已自动确认”；仅在跨域冲突或用户主动展开时显示修订入口。 |

## 5. 跨领域医学语义评价

### 5.1 AE

- AE 发生、报告术语、起止日期、严重性、严重标准、因果关系、采取措施、转归、分级和编码层级均被识别，覆盖面较好。
- `AETOXGR`/`AETOXGRH` 可作为来源采集分级，但当前没有 CTCAE 版本血缘；不得直接表述为已按某一 CTCAE 版本标准化。
- MedDRA 版本和语言字段存在，但整个 PT/LLT/HLT/HLGT/SOC 层级的 field_kind 不一致，是激活前必须解决的问题。
- 部分日期必须保留精度，不能静默转为完整日期。

### 5.2 MH/AH

- 固定截点仅纳入 AH 的技术元数据块，未纳入病史临床字段。
- 不能评价病史术语、开始/结束日期、持续状态、MedDRA 编码或 AE/MH 漏报所需的跨域匹配能力。
- AH/MH 临床块完成后，应单独复核病史原始术语、编码术语、活动状态、起止日期精度以及与 AE/CM 的关联字段。

### 5.3 LB

- 固定截点没有 LB 完成块。
- 不能评价检验项目、原始/标准化结果、单位、正常参考范围上下限、异常标志、CS/NCS、采样日期时间、访视或实验室来源。
- 在 LB 完整复核前，禁止声称 V10 已支持实验室异常、CTCAE 分级上升或参考范围判断。

### 5.4 疗效与量表

- BSA 已识别评估日期、部位、数值、单位、是否执行和未执行原因，基础结构较好。
- DLQI/CDLQI 已识别题目值、显示文本、完成状态、评估日期和总分，但正式题干、编码字典、条件分支和评分公式不足。
- 量表总分只能先作为来源采集值；只有在完整量表规则下可独立复算时，才可建立确定性派生血缘。

### 5.5 受试者、中心与访视

- `SUBJID`、`SITEID`、`VISTOID` 等技术标识识别稳定。
- `SITENM` 在多个域中被标为 `source_collected`，但其更可能来自 EDC/项目主数据；应统一来源性质。
- `VISIT` 是显示名，不等于访视日期，也不证明访视窗合规。计划访视、计划外访视、访视日期和访视窗必须独立建模。

### 5.6 试验药物与 CM 边界

- 当前已完成块没有把 DAA/DAB 误并入 CM，方向正确。
- CM 明确代表非试验用药/治疗；后续规则不得用 CM 承载试验药物给药、剂量调整、停药、重启、发放、回收或依从性。
- DAA/DAB 仍需用 CRF/数据字典澄清发放、回收、重量、数量、频率/间隔、依从性和记录标识。
- 固定截点没有完成 TRT/实际给药或暴露域，尚不能验证“试验药物实际给药/剂量调整”和“药物发放回收”的完整边界。

## 6. 置信度与用户动作评价

精确置信度分层：

| 置信度 | 字段数 | 评价 |
|---|---:|---|
| `<=0.60` | 16 | 必须人工确认；未确认前不得进入风险规则或正式映射。 |
| `0.61-0.79` | 85 | 中等不确定；若涉及核心医学语义、时间、剂量、编码或量表，必须人工确认。 |
| `>=0.80` | 258 | 可作为候选优先项，但不能绕过跨域一致性、编码血缘和来源性质门禁。 |

当前优点：

- 低置信度项普遍解释了证据不足原因，并提出查看 CRF、数据字典、词典版本或公式等具体动作。
- 未见以高置信度掩盖确定性派生公式缺失的情况。

当前不足：

- `confidence` 更像单字段语义置信度，不代表其已满足下游使用条件。高置信度的角色仍可能跨域不一致。
- 61 个技术元数据字段的 user_action 完全重复，会制造不必要的审批负担。
- 医学经理需要的是“为什么需要确认、若不确认影响哪个功能、可选择什么”，而不是统一的“请确认”。

建议将 user_action 收敛为四类：

1. **自动确认并折叠：** 确定性技术元数据，无冲突时不占据主界面。
2. **需选择：** 提供 2–4 个互斥语义候选，并说明对风险规则的影响。
3. **需补来源：** 明确要求 CRF、数据字典、词典版本、量表规则或方案条款。
4. **保持未映射：** 全空、证据不足且不影响核心监查的字段，可明确忽略。

## 7. 建议激活门槛

| 门禁 | 要求 | 本次状态 |
|---|---|---|
| G1 完整覆盖 | 每个输入字段恰好映射一次，无重复、遗漏、越界字段 | **通过（仅限 34 个完成块）** |
| G2 核心身份 | 受试者、中心、访视、记录键角色稳定且跨域统一 | **部分通过；角色命名/field_kind 需统一** |
| G3 CM/IP 边界 | CM、实际给药/暴露、剂量调整、发放、回收、依从性清晰分离 | **未通过；TRT 未完成，DAA/DAB 有歧义** |
| G4 日期与数值 | 部分日期有精度；数值与单位成对；核心值含来源和解析状态 | **部分通过；AE/CM mixed 日期及 DAA/DAB 语义待确认** |
| G5 LB 参考范围 | 项目、结果、单位、参考下限/上限、异常标志、CS/NCS 可追溯 | **未评价；LB 未完成** |
| G6 编码血缘 | 代码、术语、编码体系、版本和同行配对完整一致 | **未通过；MedDRA/药品词典判定不一致** |
| G7 派生血缘 | 所有派生字段有源字段、明确公式、单位规则和可复算证明 | **尚无已确认派生字段；量表总分/BSA 标准化值待确认** |
| G8 低置信度处置 | `<=0.60` 全部人工处置；核心字段 `<0.80` 必须确认 | **未完成** |
| G9 用户动作 | 动作简洁、可执行、说明影响，不让医学经理重复审批技术元数据 | **部分通过；61 项模板动作应折叠** |
| G10 全域完成 | AE、MH、LB、疗效、访视、受试者、中心、CM、IP/暴露均完成并复核 | **未通过；本文为部分完成块 QC** |

### 推荐的最终放行规则

1. 任一完成块出现覆盖遗漏、重复或越界字段：硬阻断。
2. 受试者/中心/访视主键不能稳定关联：硬阻断。
3. CM 与试验药物实际给药、剂量调整、发放回收边界不清：硬阻断。
4. 影响风险判断的日期、剂量、数值、单位或参考范围缺少语义/精度：硬阻断对应规则；不影响其他已确认域。
5. `standardized_coded` 缺少明确编码体系、版本字段和同行 code-term 证据：降级，不得作为标准编码事实。
6. `deterministic_derived` 缺少明确公式和复算证据：不得启用。
7. `confidence <=0.60`：必须人工处置；核心医学字段 `<0.80`：必须人工确认；高置信度也必须通过跨域一致性门禁。
8. 未完成域不得由其他域外推，不得在产品说明中宣称已支持。

## 8. 建议的下一轮只读复核重点

1. 队列全部完成后重新执行全量逐字段覆盖检查。
2. 优先复核 AH/MH 临床字段、LB、TRT/实际给药或暴露、剂量调整和关键疗效域。
3. 用统一角色词典检查所有同名来源字段的 recommended_role 和 field_kind。
4. 对 AE MedDRA 链、CM 药品词典链进行整域血缘复核。
5. 对 DAA/DAB 使用 CRF/数据字典做药物发放、回收、依从性和间隔字段的语义确认。
6. 对 AE/CM mixed 日期建立部分日期和精度门禁。
7. 对 DLQI/CDLQI 及其他量表建立题目、条件分支、采集代码、显示文本、计分值和总分公式的完整模型。

本报告仅是固定截点下部分完成块的医学/数据语义 QC，不构成 V10 全量映射通过或激活批准。
