# 医学监查工作台增量复审 · 0922V2

## 1. 基线、范围和总判断

固定HEAD `07b6a09c1644c9261e6e3637f4e497bf775c33a1`，比较 `9b0e199f05dcb9cd9ee3bfbd32b06808c181136b`，新增16提交。最新提交时间2026-09-22 05:35:04 UTC。根HANDOFF仍指向旧阶段，本轮实际核对 `scripts/test_round6/HANDOFF_ROUND6.md`、测试轮6报告与关键源码。

**总判断：有实质局部修复，但“V5 P0全部落地”不能当作验收结论。** 多项变化只改了生产者或内部辅助函数，真正的读取/回放/前端消费者没有同步闭合。下一步应交付一个可恢复、可重放、按项目和结果版本正确绑定的完整用户工作路径，而不是继续增加通用确认步骤或以候选数/模型一致率作为完成指标。

本轮为增量及关键链路审查，不是全部仓库文件的重新审计。证据类型分为：开发者报告；当前源码静态核对；选定逻辑隔离探针；实际模块/API/浏览器验收。最后一种本轮没有执行。18项隔离探针中8项支持局部修改、10项展示剩余问题/行为风险/必要依赖，不应称为18项产品验收通过。

## 2. 确认应保留的修复

| 改动 | 当前支持的结论 | 不能外推的结论 |
|---|---|---|
| `facts_table_source_digest` 被构建器和fresh校验共同使用 | 旧的子集内容摘要对行数摘要矛盾已在所读调用点消除 | 不能证明全部消费者、缓存及旧快照读取已正确 |
| `_clean` 显式保留0/False | 当前分析证据字段不再把0和False当空 | 不代表全仓库值类型或所有视图完全无损 |
| `observed_response_model` 分列与attempt记录 | 成功路径已把观测模型名写进观测列/attempt | legacy response_model仍写请求名；不能仅据此证明独立模型身份政策已闭合 |
| `_finding_claims` 取消400字符截断并保留sides/kinds集合 | 长条目和另一侧的集合信息不再直接丢弃 | 前端仍主要看首个kind；集合并集不是逐条来源关系的替代品 |
| 显式read_failed返回空且不备用生成 | 该状态分支已改 | binding损坏/丢失目标仍可能被分成另一状态，从而走旁路 |
| 空事件目录返回partial/unbound | 不再把所有推导锚点标为bound | 公开DTO是否带锚点、全部引用是否验证，仍需独立验收 |
| F7选择文件持久化 | 合法选择可在无参数请求重读 | 未校验先落盘、回执重放和决策冲突仍有缺陷 |

位置：`ae_mh_cross_analysis.py`30–168；`main.py`1145–1210；提交34a5175；`facts_mode_outputs.py`300–779；`monitoring_document_authority_workflow.py`345–500。精确读取范围与来源见 `evidence/source_index.json`。

## 3. 关键发现与纠偏

### 0922V2-01｜P0：项目级解析只修了fresh校验，结果生产/读取仍有单研究旁路

**位置：** `services/api/app/main.py`3780–4250，`_r7_facts_provider_for`、`_r7_real_setup_inputs`、`_facts_domains_loader`、FactsModeOutputProvider初始化及r7 router注入。

当前fresh检查调用按项目惰性解析函数，这是有效进展。但是模式输出实例仍绑定 `_FACTS_WORKSPACE_DIR`（特定SAR研究目录）；`_facts_domains_loader` 返回provider字典里的第一个值。路由是否启用该模式输出又取决于SAR单例是否存在。发布adapter字典由启动时provider字典复制生成，后续lazy注册没有同步更新该副本；setup入口仍直接get字典。

**条件性后果：** 新项目首次物化晚于进程启动时可能仍不可用；其他项目可能读取固定研究finding文件，来源锚点却从另一个first provider重建；没有旧SAR项目时，即便其他项目有facts也可能缺r6输出。属于已确认的接线错误/隔离风险，本轮未验证真实跨项目数据泄露。

**修复：** setup、freshness、publication、mode outputs、public reads、evidence统一通过请求所属project与冻结result/run解析对象。禁止固定研究或first-provider兜底；不以每次导入后重启作为产品流程。测试必须包含无任何旧项目的冷启动、进程内新增项目、同SUBJID双项目、结果读取与来源内容对账。

### 0922V2-02｜P0：人工文件用途决策未进入可重放的晋升回执

**位置：** `monitoring_document_authority_jobs.py::promote_document_authority_from_jobs`、`verify_document_authority_promotion_receipt`；`source_intake.py::monitoring_authority_entry_is_verified`；`monitoring_document_evidence.py::_verified_entries`。

晋升调用resolution时传入 `user_role_selections`，允许用户帮助未决角色收敛；但晋升receipt没有冻结有效选择/决策revision/hash，回执verifier重新resolution时也没有传这些选择。对于机器独立结果仍未收敛、依赖人工选择晋升的场景，重放无法复现原结论，或文档身份不一致。真实文档读取通过registry的verifier回调筛选，因此它不是只有调试函数才会遇到的问题。

**证据：** 静态生产者/消费者对照；P17仅演示“有该决策可resolved、缺该决策仍unresolved”的必要依赖，不是完整receipt函数/API实测。不能认定HANDOFF所称那一个失败mapping作业一定由此导致。

**修复：** 将人工用途选择作为版本化、不可变、带真实principal及批次身份的决策工件，晋升receipt记录其ID/digest；重放消费receipt绑定的历史决策，不能读取当前latest选择。后续修改不改变旧receipt的可解释性。校验未通过时给出分层原因，不删除verifier、不强写promoted。

### 0922V2-03｜P0：active指针校验不是历史结果冻结，损坏binding还有legacy旁路

**位置：** `facts_mode_outputs.py::_read_findings_binding/_read_ai_findings/_daily_findings`；`publication_routes.py::get_public_result_overview`（660–805）；`scripts/dualvlm_finalize.py`发布指针。

新增pointer digest能拒绝“指针不变、文件内容被替换”（P06/P07支持）。但公开旧result-token读取时仍在adapter结果上调用共享provider的 `public_findings(projection, project_ref)`，没有传该result/run的冻结finding binding。reader每次读项目active指针，合法切换A→B后旧结果路径也可能叠上B发现。

另有两条旁路：
- `_read_findings_binding` 把已存在但损坏的JSON/错误形态当作 `{}`，随后走legacy固定文件。
- 有效binding指向不存在工件时被判 `missing`，而daily的missing分支会生成确定性备用提示。

**证据：** P12复现reader随active变化；P13复现损坏binding读legacy；P14复现缺目标进入备用分支。真实result API的连接关系已静态读到，未运行HTTP。

**修复：** 每个结果冻结artifact ID/digest、输入manifest、schema和policy；active只负责“当前结果”索引。缺指定工件/坏binding属于read_failed而非无AI lane；legacy仅显式版本适配。rows/meta从同一次验证的对象投影，避免双读不同版本。旧结果继续只读；不要修改其摘要掩盖当前错误。

### 0922V2-04｜P0质量：相反医学命题仍可通过“一致”判定

**位置：** `ae_mh_cross_analysis.py::_clues_agree/_clue_stance/_grade_terms`（350–475）。

新代码拒绝neutral和简单3级/1级冲突，是局部改善（P03/P04）。但双方只要正向词频占优，且没有不相交分级集合，仍直接返回True。

隔离反例：P09 ALT升高/降低；P10 给药前/后异常；P11 本次3级既往1级/本次1级既往3级，均被判agree。最后一例具有相同等级集合，但等级属于不同时间对象。

**修复：** 区分候选主题配对与命题支持关系。正负词频只用于候选检索/保守提示，不作为accepted依据。结构化比较subject/event/predicate/value/unit/time/condition/negation，未知不能默认确认。同负向、无发现也不应自动变成需人工裁决的争议。不要继续按本轮三句话堆正则。新策略在新analysis版本进行验证，历史accepted保留历史含义。

### 0922V2-05｜P1：公开DTO仍无锚点，新增事件按钮缺少真实输入

**位置：** `facts_mode_outputs.py::public_findings`与`_findings_from_artifact`；`MedicalMonitoringWorkspace.jsx::QueryWorkspaceView`1828–1918。

mode投影带 `anchor_event_refs/verified_event_refs/anchor_reason`，但实际public_findings返回对象没有这些字段，只有标签、subject refs、文本、claims与证据ID。前端“定位关联事件”却以 `item.anchor_event_refs?.length` 为渲染条件。公开overview正是注入public_findings，不是mode对象。

**修复：** 同一typed阅读模型贯穿模式输出和公开API；从已授权冻结证据索引解析事件/来源，不在UI按数组位置重建。无AE的实验室问题也可查看自己的来源。多条相关证据全部可访问，未绑定原因可见。修复以真实public API→browser点击→记录ID/文本匹配验收，不以组件有按钮关闭。

### 0922V2-06｜P1：非法输入可先进入持久选择，普通轮询重复失败

**位置：** workflow.advance先调用 `_effective_user_selections`；后者save后才进入jobs层 `_apply_user_role_selections`。

未知candidate在应用阶段被拒，但此前已落盘。后续无参数resolve会重读相同非法值而再次失败（P15）。合法新选择能够替换修复，不能称不可恢复，但普通用户轮询路径无法自愈。

同一角色若已由机器自动收敛，之后合法但不同的用户选择被静默忽略（P16）；这不是要求“用户永远覆盖模型”，而是要求明确反馈未应用/冲突/过期原因。

持久层还存在静态风险：保存的actor默认是角色名不是认证主体；加载不核对project字段；损坏文件当空；fixed `.json.tmp`和read-modify-write没有CAS/历史决策账本。本轮未作并发竞态实测。

**修复：** 完整验证后持久提交；记录batch+attempt+project+decision revision+authenticated principal；无效请求零副作用；幂等键与CAS；保留历史，损坏有显式状态；冲突不能沉默丢弃。它与0922V2-02应由同一负责人串行合入。

### 0922V2-07｜P1：主文档待确认、补充文档可用时会提前KeyError

**位置：** `promote_document_authority_from_jobs`注册循环（约970–1038）。

主文件validation blocked时continue，没有写入 `entry_id_by_claim`。后续同角色supplementary验证通过后立即访问该primary的entry key，产生KeyError，尚未返回content_confirmations。registry事务遇异常回滚，故新增“注册先入账、返回确认清单”不能覆盖此组合。

**证据：** P18复现选定分支，不是完整registry实测。修复应分离注册、验证与依赖装配，补充项标dependency_blocked，等主项就绪后重放；不能把缺少main的补充文档独立晋升。测试方案+修订/附录、IB补充等组合。

### 0922V2-08｜P1产品/可用性：新增确认未解释需确认的事实

**位置：** AdmissionWizard::DocumentReadinessPanel、submitContentConfirmation。

当前确认行只有文件名、角色、content_status/use_status，按钮“我已核对，确认沿用”；提交固定理由、空 `acknowledgedCheckCodes`。源码不足以说明后端允许任意硬错误绕过，因此本报告不作该结论。但界面确实没有充分解释预期/实际差异、证据、影响和可采取的不同动作。

**修复：** 将file_role、study_identity、version、technical_integrity、source_context等不同失败类型分层；只有允许覆盖的警告才出现具体确认，提供预期值/实际值/可定位证据。提供更换文件、补资料、纠正元数据等动作。真实决定绑定修订，禁止仅点击便自动记录泛化“医学已核对”。确认异步请求还需generation/in-flight保护，与原向导生命周期一致。

### 0922V2-09｜P1：医学范围和前端任务仍被接入流程挤占

HANDOFF明确全域覆盖与列表化未做。分析仍硬编码AE/MH/CM/EX2/4/5/7，不包含全部所需临床域，并要求至少两个域；完整字段进入prompt也不代表证据覆盖/核验覆盖均完成。全表hash对所有受试者重复计算，来源版本变化又可能扩大失效范围，需实测与分层依赖摘要，不应再退回行数hash。

当前Workspace仍遍历所有AI长卡片，再显示另一组旧风险卡片；claim不同类型放在“观察与依据”一栏，证据是计数span，受试者是button非可复制的路由链接。宽屏CSS已有改进，本轮不重开该旧问题；下一步要交付风险工作列表/选中详情/正确来源导航，而非继续统一缩字。

## 4. 对HANDOFF和测试报告的评价

### 4.1 不能把API直驱推进写成用户闭环已通过

交接记录同时写了“55条候选、9/10作业完成、双cohort校验10/10”和“浏览器端到端未走完”。这应分别解释分母：预期工作单元、执行作业、结构/身份校验、字段覆盖、未决项、结果完整性；不能据10/10推导整体成功。那个失败作业没有本轮可访问的失败载荷/诊断，不能先归因为某模型输出质量。

### 4.2 对抗测试观测可靠的部分，与推断过度的部分要拆开

测试C确实观察到改名eCRF被列入角色候选、用户指派后遭registration/role collision阻断、没有到达监查结果。这支持“候选/冲突说明不清、恢复困难、缺少可理解的内容提示”。

它不能证明“系统不读正文”“完全没有内容校验”“冒名方案已成功进入监查依据”。候选选择列表代码本来就列出所有文件；晋升还检查技术/内容状态，报告也记录了拒绝。应逐阶段举证：candidate→assigned→validated→promoted→rule-used→result-cited。真正的错误晋升与输出引用要到后两层才有证据。

不能为匹配此过强推断而推倒已有内容处理；也不能用放宽规则让故意混错研究的fixture通过。正向完整材料与负向错角色/错研究材料分别验收。

### 4.3 测试层级

`test_facts_source_digest_contract.py`验证了构建器与共享摘要、类型、clean；文件中没有实际调用main的current resolver。它有价值，但不能独立证明从正式job提交、fresh校验、完成到结果读取已贯通。所有关闭记录应写证据层级而不是只报“全绿”。

## 5. 下一步建议

先闭合项目/result resolver与manual decision replay。随后交付一条完整浏览器工作切片，至少含无发现、明显问题、缺资料和部分日期病例，并保留全部适用数据入口；完成保存/刷新/重启/增量后，再扩大第二研究。UI在稳定DTO上并行推进，不必等全研究LLM重跑。

原始Listing先可查与部分资料可用已在既有边界中，不应重复变成“全部等用户拍板”。但“无方案/IB时先执行何种基础医学AI分析”是更进一步的产品范围，仍需单独确认，不能将二者混同。没有缺失依赖的判断先可用，有依赖的判断显示不可评估，不伪造全量完成。

最终验收单位应是完整用户问题路径，不是promoted字样、模型调用数、accepted比例、card数量或测试者人数。完整工作包、接口约束和验收例见同包主指令与JSON。
