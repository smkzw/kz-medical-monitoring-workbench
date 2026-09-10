# 医学监查实施计划 v3.0

日期2026-09-06。完整设计：`.trellis/spec/medical-monitoring-system-design-v2.md`。本计划替代v2.0中尚未完成的C–F前瞻顺序；A/B历史保留，C不冒称完成，最终五项目目标不删减。

## 原阶段对应

| 原阶段 | 当前事实 | 新安排 |
|---|---|---|
| A/B | Git/迁移/单feature已做；部分巨型服务和旧兼容仍在 | 不重做；按真实缺陷局部整合 |
| C | 正确MG首轮双模型完成；696分歧复核未完；无正确facts完成证据 | P1/P2收束，保留已完成证据 |
| D | 真实AE/MH风险至用户闭环未接通 | P3优先于其余四项目全面mapping |
| E | 多域/三模式/报告有离线资产但真实接线未验收 | P4/P5复用接通 |
| F | 真实备份恢复、打包/成本基线未验收 | P6 |

## P0 接管审阅与合同重建（进行中）

- [x] 读原goal、handoff、设计/计划、Git与最新适用AGENTS；旧goal保持paused。
- [x] 前端原生独立静态review完成；下游原生审阅容量失败，主线程接手，无替代模型冒充。
- [x] 256项接入链测试、Vite build；研究ID前缀误匹配和混合PDF覆盖最小复现。
- [x] 独立临时runtime的ego(lite)首页/导航/历史/导入入口检查；18911/15174已停止、空间关闭。
- [x] 新设计、计划、goal prompt成文（仍须最终交叉核对）；不以成文冒充实现。
- [ ] 补关键下游/模型队列的行为验证及丢失迁移测试盘点，完善问题矩阵。
- [x] 新goal已由get_goal核实active；此前工具替换阻挡已解除，无受保护runtime数据库修改。

## P1 正确性止血（第一批实施）

2026-09-06：身份/裁决偏置、队列持久暂停与原位有界恢复、重复代退役、零变化/数值/导入交互修复已提交。独立队列审阅与f76bf59回答绑定复核完成，后者指出的中断回执与409跳转已修正，实际API异常及恢复行为验证通过。ego实际截图/点击与趋势柱高检查完成。P1工程修复已形成证据；正确MG临床闭环及自主补证据仍属P2/P3，不以测试数代替验收。

1. 研究身份：移除双向任意前缀；明确环境后缀及登记别名；测试TRIAL-01/010、短前缀、多研究值、缺身份、合法PROD后缀。影响admission及revalidate；旧数据只重验证不改历史。
2. 自动裁决：把二轮分歧无条件primary_retained改为证据决定或明确未解决；保留用户已答内容；同义归一不掩盖治疗/日期/单位差异。测试两路都自信但相反、单路证据无效、需要更多材料、保守不可评估和少量用户问题。
3. 调度：当前代未完不建新代；终态失败只重试对应分片；已有g02先只读盘点和恢复计划，禁止手改SQL、删除、整批重跑。
4. 暂停：持久禁止新claim；在途结果完整落盘；重启保留pause；离开前端仍继续未暂停任务。测试多worker/过期lease/重复wake/重启。
5. 前端准确性：零变化比较、未知核对数、真实趋势尺度、导入预览重挂载。先复现后修，不夹带视觉重写。

完成证据：新回归可复现旧缺陷并验证新行为；原256项及受影响相邻测试；不触碰写作。独立复核修复diff（若容量失败如实记）；journal记本阶段结果/下阶段计划。

## P2 证据完整与工具化harness

2026-09-06：87个误建g02经备份和等价验证通过仓储退役，571jobs/321候选完整保留。MG仍持久暂停、未恢复真实模型；工具化接线按新提示版本隔离验证后再启动对应未解决分片。

1. 梳理候选文件识别与完整文档内容解析的区别；建立物理内容coverage。
2. Excel保留全表确定性统计，模型按需读取罕见/冲突/异构行；首轮两路全列覆盖；增加分页、邻列与文档补读工具。
3. PDF混合页覆盖检测；图片区域OCR/VLM，不能把12条excerpt预算当全文预算。Word脚注/图表/修订检查在监查adapter实现，不改写作解析器。
4. 轻量状态查询与大证据读取分开，job引用冻结artifact；测实际内存/耗时再迁移，保持兼容旧input payload。
5. 文档/字段/风险分任务契约，裸API工具循环可独立请求补读、验证、裁决；失败有界且不默默缩覆盖。
6. 同输入继续MG现有证据；新prompt/新parser按影响生成新代，旧成功证据复用须证明等价，不隐式套新语义。

完成证据：混合PDF/图表Word/异常Excel合成挑战；至少正确MG模型独立闭合映射与facts并抽查源；第二种异构项目用作反过拟合检查但不并行全量启动。

### P2当前接线拆分（2026-09-06，实施中）

从用户目标出发，自动补读应减少工程化确认，不应把固定摘要当完整理解。新版本已接入有限工具循环和持久读回执，旧版本路径保持兼容。冻结Listing分页/罕见值、文档正文分页及实际引用验证已实现，整合724项通过；双路真实正文工具补读及quote_ref引用已验证；隔离AE映射仍有分歧，图片语义及标准lookup未完成。按以下依赖实施：

- 先实现冻结来源读取适配器：table_binding_id/物理列索引及source revision定位，按范围返回原始行与邻列；每个结果附覆盖、分页和截断，不能用字段名模糊定位。复用现有snapshot hash及locator校验，不读取原始项目目录。
- 再加有限工具回合协议：独立provider请求工具→harness读冻结证据→同provider继续。主分析/盲核对上下文隔离；逐回合模型身份及input revision复查；工具预算耗尽不得标完成。保留当前任务schema和最终输出校验，工具请求不冒充候选结果。
- 接线处在MonitoringAiService的provider调用层及main组合根；读取器不提供任何临床解释。先用合成provider行为测试真实循环，再用已绑定裸API跑小范围真实证据，最后恢复正确MG对应未解决分片。
- 检测/正文覆盖与候选预览分离。混合PDF检测单元已派发两文件执行，不能凭candidate摘录12条宣称全文完成。文档search/分页读取及标准lookup分别绑定注册版本；不改医学写作解析器。
- 模型工具回合/新提示属于新语义版本；不得在旧g01任务下静默替换。需要为受影响分歧记录明确新revision和旧成功证据复用依据，同时保留前述原位技术重试的区别。
- 2026-09-06实际独立复核结果：12字段二轮3一致，剩9聚焦后2新增一致，7字段仍为参考说明/关联字段差异；未生成facts，不将严格阻断直接转成用户问题。下一步版本化区分可执行语义与说明性元数据，并保留实质依赖和标准差异。同步审计模型输出后量表/剂量/治疗归一：源码可验证闭合约束和拒绝无依据结果，不得用列名/代表值启发式替模型改写解释或掩盖双路分歧。
- 来源微基线：当前复验约7.8秒，单正文读取由7.4秒降至2.7秒（隔离同文件重复2次，当前role及补充来源重新检查，外围完整packet重验保留）；这是局部测量，不是最终性能验收。视觉区域提取节点与比较合同独立审议并行，等待真实回执再整合。

### P2最新增量（2026-09-06）

- 显式依赖tools-v2已通过独立复核及隔离12字段双路实际调用，均一次完成、0补读、3一致/9分歧；不得与v1聚焦累计5一致混算。修复纯参考说明对缺省字段的伪差异后仍9项未解决，实际报告`runs/mm_p2_tool_trial_20260906/dependency_comparison_201260a.json`。
- 新语义路径保留模型原始解释，旧量表后处理吞并角色的合成反例已封堵；原MG默认路径尚未切换。独立审阅确认metadata追加不覆盖AI项。治疗锚点不足时整分片拒绝仍需关注，不因当前小样本无失败就关闭该风险。
- PDF区域/Word指定嵌图提取已提交f768fd3，主线程旋转/字节预算验证通过；可选toolset接线中。图片原字节须经监查专用裸API真正发送，提取摘要不等同VLM已阅读；不改共享写作网关。视觉传输为独立两文件执行，主线程负责工具循环、双方上下文隔离和真实调用验收。
- 下步先消除新旧提示对related_fields/dependency_fields的冲突，并审议逐字段、双模型独立证明的角色表示规范化；不建立Codex判定的全局同义词库，不放宽对象/剂量/日期/版本/依赖比较。设计会商尚未结论，不先采用该规范化。

## P3 一条真实医学工作闭环

1. 显式读C3 fact-set → subject/site/事件身份 → SemanticRecordSet；项目知识包提供AE窗、用药、终点和规则，模型负责临床概念理解。
2. 真实MiniMax发现＋GLM盲核对，既有AE/MH结构评估器只消费验证过的typed inputs；补反证搜索。
3. 后台图节点推进→coverage/QC→风险生命周期→真实publication provider→同版本看板/旅程/来源；不调用synthetic provider补空。
4. Query“依据—发现—请核实事项”编辑保存与草稿导出。
5. 用户从项目风险→受试者访视轴→源记录→Query，以ego(lite)实际操作；真实样本精确定位，分母与风险解释抽查。

完成证据：MG独立运行不需Codex补语义；未处理域明确不可评估；用户可实际使用该域。不得因此称其余域或五项目完成。

## P4 医学域与日常增量

按资料适用性接CM/IP及背景治疗、PD/入排/访视、疗效、安全/CTCAE、跨模块关联。知识/标准lookup冻结版本；CTCAE强度与严重性/因果性/预期性分开。中心与研究按分母/随访展示，不黑箱评分。

加入兼容双快照diff和影响传播：新增/修改/消失/范围改变、补录AE、撤回后重现、单位/规则变化、同一事件重开。数据变动与分析变动分别展示；零变化是有效结果。

完成证据：至少一个真实兼容增量、风险与Query变化对照、未知身份不合并/关闭。

## P5 三模式、报告与五项目泛化

1. 锁库前多轮query修订全量输入与增量影响；锁库后固定版本研究/中心/个例/checklist包。
2. 外部报告上传、claim提取、证据/遗漏对照、批注副本和草稿；页表图脚注覆盖。
3. 其余四项目逐个至少一次真实全量；未知药物/疾病/列名不改公共内核硬编码；参考基座可挑战，不压制新发现。
4. 五项目统一验收清单：数据覆盖、来源、风险、Profile/Journey、Query、报告、模式输出，用户确认留真实状态。

## P6 交付与维护

工作台一键启动/停止，真实暂停重启、备份恢复校验、通知一次确认；真实性能/调用/存储基线。经引用证明确无使用的版本化旧组件可逐项删除；历史85GB与旧数据库另询问，不碰Codex session。最终明确未实现能力/缺陷，用户确认后才完成goal。

## 验证命令基线

` .venv/bin/python -m pytest tests/test_mm_c3_mapping_bridge.py tests/test_mm_c3_mapping_confirmation.py -q -p no:cacheprovider `

` .venv/bin/python -m pytest tests/test_medical_monitoring_r7_data_admission.py -q -p no:cacheprovider `

其他C1/C3文件按本次review记录列出；前端 `npm --prefix frontend run build` 使用明确隔离outDir。交互以ego(lite)测真正挂载/effect/导航，不以源码字符串匹配替代。

每阶段开始写用户目标/检查点，结束写实际证据/缺陷/下一阶段顺序。进度只写本计划、journal、Git；不新增context/reviews过程文件。遇到更高优先级风险先调整本计划并记录原因，不重开整套门序。


## 2026-09-06 用户要求无损暂停（当前有效检查点）

已完成当前证据编号修复批次后暂停；不启动新模型任务、服务或下一阶段。任务与goal未完成，Trellis保留in_progress，paused为用户要求的运行状态。

### 本批结果与审阅处置

- 视觉裸API接线及413有界拒绝已提交（8f11114、2b79e57）；两路小型合成图片真实识别通过，仅证明传输，不代表医学图表理解或最大请求体性能验收。
- frozen-2214961的GLM独立审阅已完成，报告位于tool-review/runs/conference/mm-p2-tools-review-20260906/role_contract_review.md。其P2-a有效：轴证据原先校验模型自报编号，而materialize之后可能删除该编号。现改为先物化最终证据、再绑定证书；拒绝任何未闭合轴引用。新v10/v8 tools-v5提示预先提供同算法生成的字段画像证据编号，区分source_entry_id和evidence_id，不由Codex替模型填语义或转换证据。
- 仅空standards_reference对象规范为null，非空残缺标准继续拒绝，不臆造标准版本。诊断补字段/轴定位；审阅所述重复except死代码当前源码不存在，不另改。大小写min规则保持原选项token，不采用casefold改写；说明长度上限及额外草稿下游场景留待复核，不作为已完成。
- 最新完整受影响回归：692 passed，5项既有SWIG相关弃用警告，15.70秒；git diff --check通过。日志evidence/pause-current-batch-20260906-pytest.log。此前50项草稿持久化/用户答案/中断重放验证保留；不同测试集合不累计。
- 新v10/v8修复尚未接受独立新版本审阅、尚未真实双模型验证，默认主项目未启用。旧v4隔离9字段：MiniMax任务monai_cf5d5b5c58b95b5304fad9ee0ca3失败（空可选标准对象后修复输出不完整），GLM任务monai_f809c902b9d755bfa352ddcf64f6完成但9项均未声明等价证书；不称双路通过、未生成facts。原始attempt与证书审计保留在runs/mm_p2_tool_trial_20260906/，不得手工补声明。

### 暂停状态与保留

- 实测8911未监听；原MG库monitoring_ai_queue_control中proj_mgk10_sar_real paused=1，更新时间2026-09-06T00:30:13.659860+00:00。当前工具试验/会商runner进程检查无存活匹配；本轮未启动服务。
- 原库runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_ai.sqlite3仅读取。先前571 jobs/321候选及recovery/20260906-before-queue-repair.sqlite3备份保留；本次未重新统计候选数。历史持久running行不代表活跃调用，恢复时先核实租约再通过repository恢复，不直接改SQL。
- 未提交过程目录及原始回执完整保留，不批量纳入Git，不清理真实输入、隔离试验、失败输出、恢复备份或session历史。五真实项目原件和医学写作子系统未改。

### 恢复后的严格顺序

1. 读取当前全局AGENTS及本检查点，检查Git/进程/队列，核实当前修复提交；不要重建历史A/B门序。
2. 对v10/v8证据闭合修复补独立复核；关注可选证书单路缺失但原角色字符串一致时是否不必要阻断、说明长度及canonical草稿下游/跨代场景。未完成设计判断不得静默放宽。
3. 使用新的隔离命名空间开展v10/v8两路真实9字段验证，保留v4失败证据。读取工具、冲突解释与裁决由产品MiniMax/GLM独立完成，Codex只改harness及验证工程合同；不得手工补语义，也不把GLM单路完成称双核对通过。
4. 证据/真实双路验收通过后，才按repository恢复原MG未解决分片；不重启全部首轮，不自动将未闭合结果产facts。
5. P2仍待完整图片/标准lookup及证据覆盖验收；P3正确MG facts→真实AE/MH及反证→看板→旅程→来源→Query尚未闭环。P4医学扩域与兼容增量、P5三模式报告/五项目真实全量及适用增量、P6备份恢复/一键启动/性能与用户验收继续按既有v3计划。不得因本批测试通过宣称项目完成。


## 2026-09-07 用户明确恢复连续实施
从540d2c3恢复，原暂停记录保留为历史。机制选择conference：证据闭合及可选等价声明影响自动接受，需要独立挑战；主线程负责整合与真实隔离双路验证，当前无独立写入单元，不额外派执行节点。先冻结540d2c3独立审阅，再隔离v10/v8验证；原MG队列暂保持paused直到新合同通过，不缩减P2–P6。

2026-09-07恢复复核：540d2c3独立审阅终态完成（Pi/Cursor default自动路由，底层具体模型未可核实，独立模型身份存在限制；运行session与报告保留于evidence-review-20260907）。审阅源码及15项聚焦验证确认最终物化后证据绑定和公布ID一致；同角色单路equivalent可选声明造成假分歧已复现，后续按新比较策略修复，不放宽不同角色、distinct/insufficient或硬属性冲突。报告R2首轮等价auto_pass的假设不符当前接线：reconcile_with_verifier在mapping_confirmation.py:1150未传等价policy，只有裁决路径:817传入，因此暂不修改首轮草稿。v10/v8真实隔离运行已启动，未修改原MG队列或运行库；待两路终态再统计，不以dispatch当完成。

2026-09-07实测v5：MiniMax monai_a1fe2c38a262d51d8172e874623a失败invalid_ai_output，GLM monai_d2d0c293b8de3990ad207c5f53cd完成，两路0工具读，不能称双路通过。失败记录只保存解析后对象；共享解析器可能从破损外层摘出内层对象，因此尚不能断言原始响应仅返回一个字段。改变假设：先在监查adapter增加opt-in原始响应保真/完整JSON校验/finish_reason，不修改写作共享网关；两文件执行节点有独立写入范围，按当前E03实际派发。主线程修复可选等价声明假分歧（比较v2，保留v1）及上层接线。100项比较/确认回归通过，未产facts。

### 2026-09-07 严格回复解析集成（执行中）
- 独立复核 optional-proof-review.md 已验证 5842540 的 v2 同角色可选声明处理，并撤回首次分析自动通过丢失声明的 R2（当前路径不会到达该前提）；不扩改该路径。
- 执行节点完成 transport 严格外层 JSON 解析；主线程合并重复 HTTP 实现，保留默认旧行为，共享 gateway/医学写作未改。
- 新 tools-v6 裁决提示启用严格解析与原始文本摘要/finish_reason 记录。截断内层对象不再被接受，一次受控修复仍需完整 schema。
- 服务测试发现并修复二次无效输出失败分支丢失诊断；517 项相关回归通过（/tmp/mm-strict-service-regression-20260907.log）。这不是医学或真实双模型验收。
- tools-v6 隔离真实任务已启动，日志 /tmp/mm-role-v6-real-20260907.log；正式 MG 队列仍暂停，等待真实回执后接续处理，不重派健康进程。
- 47b3e7d 冻结独立复核：59项测试通过，无阻断缺陷；已将服务测试诊断键对齐生产 strict_raw_preview，2项聚焦通过。
- tools-v6 MiniMax job monai_df027cc76d76896a8abdb331fe58 已完成：首回执严格解析 truncated_fence、finish_reason=length、22494字符；受控修复 ok、stop、16566字符。真实证据确认输出截断存在，严格解析阻止内层误收；GLM仍待完成，未声称双核对或语义闭环。
- tools-v6 两路最终完成，产品比较 role_v6_reconciliation.json：9字段7一致、2分歧（AEENDAT/AEOUT 的依赖声明），覆盖/合同违规均0、工具读取均0、dual_model_pass=false、facts_generated=false。仅对剩余2字段使用既有独立双路裁决启动新隔离输入（adjudicate_role_residue.py；/tmp/mm-role-v6-residue-20260907.log），保留原候选和全部回执，不由主线程填写语义或放宽依赖比较。

### 2026-09-07 用户要求无损暂停（最新停止点）
- 用户最新指令“无损暂停”已执行。现有隔离全9字段、残余2字段和独立审阅进程均 exit 0，未遗留本轮运行进程；exit 0只是脚本终态，不代表所有业务job成功。未启动新阶段或tools-v7。
- 提交历史：5842540 可选角色声明v2；47b3e7d 严格完整回复及诊断；3f702c7 测试诊断字段保真；c983c07 双路真实与残余裁决证据。相关回归517通过，独立冻结复核59通过，测试字段修正2通过。
- 第一次tools-v6双路终态：MiniMax monai_df027cc76d76896a8abdb331fe58 completed（首回length截断被拒，修复stop成功）；GLM monai_44aa61170fb0972f3460059b361e completed。9字段7一致2分歧；dual_model_pass=false，facts_generated=false。
- 剩余2字段复核终态：MiniMax monai_22fd3eff03918161fe88ccc51b01 failed/invalid_ai_output，受控修复后 AE/AEENDAT: role_equivalence_option_set_mismatch；GLM monai_a83b6306e70afae593beb8732517 completed。两路工具读0，不声称重新达成一致或来源覆盖闭合。
- 已查到 _anonymous_review_rows 将前轮 semantic_verdict.role_equivalence 连同旧option_ids嵌入新匿名选项，存在旧新编号混淆风险；这是待验证工程假设，未删证明、未修改语义、未放宽比较。下一安全动作：核对失败回执使用的编号与当前选项绑定，设计版本化的历史证明/本轮选项分离，保持历史证据和原始输入不变；补通用回归及独立复核，再仅用隔离残余输入验证，不能直接恢复MG。
- 正式MG queue_control paused=1（2026-09-06原暂停时间未改），现场核对8911未监听。原始5项目及医学写作均未改，未启用本地Qwen。本轮Qwen加载追踪见会话说明：oMLX在16:06加载、16:13卸载，具体调用方未证明，不能归因本产品。
- 隔离DB/比较结果/日志哈希：runs/mm_p2_tool_trial_20260906/pause_20260907_strict_response_manifest.json；临时运行/回归日志已复制至同一隔离目录。既有未跟踪执行/审阅证据目录全部保留，未做清理删除。无需重新建立git基线、重读废止门序或恢复已删除父JSONL。
- P2尚未完成（映射闭合、标准lookup/证据覆盖等），P3–P6继续沿既有v3计划；任务不标完成。等待用户恢复指令，不再自行派发任务。

### 2026-09-08 恢复连续实施
用户已恢复连续构建，前次暂停仅为历史。机制选择conference：本批匿名选项投影影响双路证据绑定，主线程做小范围修复和隔离验证，独立审阅挑战冻结修复；暂无值得分离的执行写入范围。
已用真实失败回执核实，AEENDAT/AEOUT修复输出option_ids均等于前轮嵌入声明，均不等于当前选项ID。tools-v7投影仅移除新选项内历史role_equivalence，保留原存储证书及其他语义/依赖约束，重新绑定当前完整投影。旧版本请求验证仍兼容。73项角色/确认回归通过；独立审阅和真实隔离验证待完成。正式MG暂不恢复；P2–P6范围不变。
- tools-v7真实隔离残余2字段：MiniMax monai_b78ea3123b3cd60b39ef6c3c6a8f及GLM monai_53547c1fbf2ab8c0374151eecc55均completed，工具读取0；role_v7_reconciliation.json由现有比较器生成，2一致/0分歧/0覆盖违规/0合同违规，dual_model_pass=true但facts_generated=false，仅本轮2字段。561项受影响回归通过；新冻结独立审阅仍运行。正式组合根尚未启用新裁决标志，未恢复原MG队列。

### 2026-09-08 用户无损暂停（当前停止点）
- 用户最新暂停指令覆盖连续实施。代码提交1ce29f9（tools-v7当前选项与历史证明分离）及记录10b82a3保留。当前无未提交产品源码修改；既有未跟踪证据目录全部保留。
- 隔离两路进程50703已exit 0；MiniMax/GLM tools-v7两个job均completed，2字段均agreed，0覆盖/合同违规，0工具读；role_v7_reconciliation.json中dual_model_pass=true仅限此2字段，facts_generated=false。561项服务/角色/确认回归通过，未进行正式MG恢复或后续阶段。
- 独立审阅：current-options-20260908，当前路线ZCode/GLM-5.3-Flash:max；runner运行约17分钟仍未出正式结果。应用户暂停向本任务runner/子进程发SIGINT，runner exit130，随后核实PID49061/49087/49127/49191均已退出。报告仍PENDING占位，无独立验收结论，不视为模型质量失败；未调用fallback。会话恢复ID未取得，不臆造。恢复时先查ZCode已有会话/回执兼容性，存在可恢复会话则优先原会话继续。
- 正式MG queue_control仍paused=1，8911未监听；未修改原始5项目或医学写作，未加载本地Qwen。日志副本/隔离DB及结果hash保存在runs/mm_p2_tool_trial_20260906/pause_20260908_manifest.json。
- 下一安全动作：先恢复/完成1ce29f9独立工程审阅并处理实际意见，确认当前投影不丢硬约束及旧数据兼容；再核查并启用main.py:3629组合根的adjudication_tool_reads/explicit_mapping_dependencies/visual_tool_reads/role_equivalence新裁决配置，以及确认仓储按新命名空间只处理未解决字段的行为。当前main组合根仍旧配置，不可直接运行旧run_mapping_reconciliation.py冒充新合同。原MG队列恢复前保留备份、核查旧lease与重复代，使用repository接口，不能手改SQL或整批重跑。
- P2标准lookup和完整覆盖等缺口、P3正确MG facts→AE/MH反证→看板/旅程/来源/Query、P4–P6全部继续待办。暂停不是完成，等待用户恢复指令。

### 2026-09-11 完整交接（保持暂停，未恢复实施）

用户要求交给另一Agent前形成完整、详细、可接管的handoff。机制选择direct：本批仅汇总并核实已存在的工程与暂停证据，不改产品或裁决医学含义，无需派发新执行/会商节点。

- 新入口：`.trellis/workspace/宋旻恺/HANDOFF_MEDICAL_MONITORING_20260911.md`。覆盖需求及其变更、历史A/B与当前P0–P6、实际goal原文、组件地图、已完成/未完成与测试范围、停滞分析、权威文件、逐步接管顺序。附件位于同目录`handoff-evidence-20260911/`。
- 只读复核：交接前HEAD 18ddfe3，产品逻辑1ce29f9，未提交产品源码变更为零；get_goal仍paused、Trellis仍in_progress；正式MG paused=1、571 jobs/321候选封装，87重复未执行代仍退休，8911未监听。v7隔离2字段一致且未产facts；未完成独立审阅仍需收束。
- 新来源发现：用户`9. DM`与当前冻结`评分SDV`同名MG listing hash不同；不同的5个sheet中cell坐标/类型/值公式子节点/style比较无差异，但隐藏行、筛选、命名范围/视图等元数据有差异。详细hash及方法/限制见附件。不能直接替换旧来源或宣称全局等价；正式恢复前核对来源选择及覆盖/复用合同，必要时生成新SourceRevision。
- 未运行模型/服务/产品回归，未修改源码、运行库、原始项目资料、医学写作或goal；未清理既有回执/ignored运行证据。新Agent获继续实施授权后，按handoff第14节完成v7独立审阅、来源/正式接线、MG有界恢复与真实纵向闭环，再承接P4–P6。此前暂停保持有效。


### 2026-09-11 ZCode 接管：完整工程review + 计划更新 + 连续实施（进行中）

用户授权本会话（ZCode/GLM-5.3）完整接管并进入连续实施。机制：off_peak；主线程审阅+2只读探查子代理+1独立审阅worker（zcode/GLM-5.3-Flash:max 新鲜会话，重派v7审阅）。

接管review结论（全文见`.trellis/workspace/宋旻恺/MM_TAKEOVER_REVIEW_20260911.md`）：
- 现场与交接完全一致；710项聚焦回归通过（7文件集，18.7s）。
- P0问题：正式组合根未启用tools-v7四标志（main.py:3629）；真实facts→AE/MH→看板→Query链未接通；**Query/报告工作区前端实际不存在**（交接§6.4描述与实际不符，需从零新建）。
- P1问题：输入payload无内容寻址层（809M字符，三重放大）；monitoring_ai_service.py 8881行维护债（本批不动，新增功能放新模块）；ProductLoop"服务端范围/推荐/确认"术语泄漏+snapshotToken兜底显示；MG同名来源差异。
- P2清理清单：前端死代码链约5000+行（BatchPanel/DailyRun/RuleRelease/FieldMapping/ProtocolPreparation/DailyAi*/Assurance链，产品树零引用）；八轨标签不一致；空g6/目录。
- MG来源决策（本会话作出）：**保持冻结评分SDV版本为正式来源**，9.DM记为已核实等价备选（cell级无差异证据 mg-source-comparison.json）；仅用户明确要求以DM为业务权威时才建新SourceRevision。

执行顺序（落实handoff §14，无变更）：v7审阅收束→组合根接线+独立runtime验证→有界恢复MG（备份/清点/repository接口，优先AE/MH/CM/IP/PD域）→facts物化→P3纵切+Query工作区→ego验收→P4-P6。阶段性清理按P2清单、清单制、保护证据。

#### 2026-09-11 接管执行记录（ZCode，连续实施中）

- 审阅收束：v7独立工程审阅以新鲜会话完成（原9-08会话用户中止无恢复句柄），报告current-options-20260908/runs/conference/mm-current-options-20260908/general_single_object.md。结论：1ce29f9实现正确无阻断；3项低风险观察（OBS-1已被接线提交解决；OBS-2浅拷贝、OBS-3非dual fail-closed无需行动）。
- 代码批：e703784组合根四标志；4111ad8 v7为当前裁决部署；c800313前端术语/标签/一键确认恢复；e0198b7+d5b44b1死链清理约11700行；79204d5+19f359b修复启动supersession漏verifier-v1的预存缺陷（误退休的151任务+151候选从备份恢复，reconcile复验一致）。
- 切换执行：备份（recovery/20260911-before-zcode-recovery.sqlite3, sha256 bfbe64da…）→retire（v5/v3未执行238个退休，终态保留）→submit（695分歧→v7双cohort各87任务）→resume（02:40 CST）。只读彩排确认reconcile_with_verifier=800一致/695分歧。监控后台运行（cutover_v7_and_recover.py monitor，进程37522）。
- 待办：裁决完成→剩余真医学问题评估→确认/激活→facts物化与抽查→P3纵切。Query工作区前端确认为从零新建（r7 API无对应端点，D10投影为域资产）。
