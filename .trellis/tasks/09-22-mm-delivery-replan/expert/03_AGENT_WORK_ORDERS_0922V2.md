# Agent实施主指令与工作包 · 0922V2

固定审阅HEAD：`07b6a09c1644c9261e6e3637f4e497bf775c33a1`。前版基线：`9b0e199f05dcb9cd9ee3bfbd32b06808c181136b`。

本文件替代V5的当前执行排序；既有N0-R/N0-D/N1-R/N2/N3/N4/N5-M/N6继续，不推倒平台，不创建第二套调度器。所有产物、分支/PR描述、测试记录和HANDOFF标记本轮 **0922V2**。

## 0. 目标与禁止事项

目标：完整临床资料→核验语义→医学分析→风险工作区→正确受试者/时间/原始依据→按需Query草稿，用户直接查看，无最终风险审批、签名或正式Query发送/回复/关闭。

文件用途歧义允许有限澄清；确认文件缺失不证明对应分析完成。共同授权、盲态、审计、版本、幂等和恢复机制保留。风险的临床判断、模型核验状态、执行失败和来源缺口分别表达。

禁止reset/checkout覆盖dirty工作、不改真实历史作业ID/身份、不清空项目、不批量杀端口进程、不重放真实临床模型任务作为默认诊断。任何生产队列/来源变更先核实runtime、进程归属、在途任务、已有授权和可恢复状态。

不要为了通过验收删除freshness/receipt verifier、将source digest回退为行数、修改历史结果摘要、借其他受试者/第一条AE的证据、把缺资料改成“无风险”，或把所有问题转给用户批准。不要让路由更换、索取密钥成为布局和状态修复的前置。

## 1. 先进行证据对账，不重新修已改好的代码

1. 记录本地HEAD/dirty diff、实际API/前端启动SHA、runtime、依赖、启动时间。远端变化时做增量，不回滚到本包SHA。
2. 读根HANDOFF和 `scripts/test_round6/HANDOFF_ROUND6.md`；把“当前全部P0落地”拆成可验证关闭项。更新根HANDOFF为最新入口索引，保留历史文档。
3. 保留 shared `facts_table_source_digest`、分析层0/False清理、观测模型名记录、400字符条目截断取消、显式read_failed不备用生成、空目录不标bound等有效修改。
4. 先用实际产品模块/仓储/API为0922V2-01～08写失败回归；本包18探针只提供反例，不是可复用的产品测试绿灯。
5. 当前“一个失败映射作业”先取得脱敏的job/attempt/failure_code/运行身份/输入revision与失败阶段，不能先假定模型差。明确9/10和10/10分别计数什么。

## 2. 推荐执行图

```text
基线与失败回归
  ├─ N0-R + N1-R：请求项目/冻结结果 resolver ── DTO稳定 ── N2/N3/N4 UI与导航
  └─ N0-D：持久决策 + promotion receipt replay + 内容确认恢复
                     ↓
             一个完整浏览器用户切片
                     ↓
        保留旧项目/旧结果，刷新/重启/增量/第二研究
                     ↓
          N5-M新分析质量验证 + N6性能/覆盖/历史测试对账
```

前端不需要等新全量模型分析；可以使用真实API合同和合成冻结工件。新医学分析先在小范围、通用fixture验证正确性，再跑研究全量。小切片是验收方法，不是将最终系统拟合为一个病例。

## N0-R / N1-R · 请求范围与冻结结果（首要P0）

### 写入范围

`main.py` 的 `_r7_facts_provider_for`、`_r7_real_setup_inputs`、FactsPublicationAdapter/Dispatcher组装、`_facts_domains_loader`、FactsModeOutputProvider初始化和router注入；`facts_mode_outputs.py`；`publication_routes.py::get_public_result_overview`；现有result/run manifest。

### 实施要求

1. 建立或复用**唯一请求范围解析入口**：经过授权的project + run/result + input manifest + policy。setup/freshness/publication/mode/evidence/public read都消费它，不各自猜目录。
2. 删除生产结果链路对特定SAR目录、first provider、是否存在某历史研究的条件依赖。历史fixture通过显式fixture配置，不参与新项目可用性。
3. 惰性注册不仅更新provider字典，还必须让setup和adapter/dispatcher可立即消费；冷启动无项目、进程运行中首次导入后可以继续到结果，不要求重启。
4. `FactsModeOutputProvider`的project检查不能默认空后永远不生效。project参数、目录、artifact声明与输入manifest必须一致；不同项目同SUBJID合法存在，不用标签合并身份。
5. 每个已发布result绑定不可变finding工件与digest。active指针可更新，但旧result读取不能再次解引用project active。与现有publication manifest整合，不新增平行真相仓。
6. 丢失binding与binding损坏不同。显式binding下丢失工件/摘要不符/跨项目/错误schema都为read_failed，不能静默读legacy或触发备用风险。legacy用明确版本适配，不用异常后fallback。
7. 一次读取获得经校验的finding set及meta，再投影行和计数，避免两个读调用跨版本。状态为missing/read_failed/zero/with_findings/partial时语义稳定。
8. 全表摘要作为源身份可以保留；按manifest预计算并缓存，增加受试者/事件依赖摘要服务增量。不要在每个受试者或每次轮询重复扫描/哈希所有表而未测量；缓存键不能只有max mtime。
9. legacy `response_model`与新observed字段在消费者中明确语义。真实模型身份、alias policy、identity verification state随job/receipt冻结；输出hash证明字节未变，不证明实际模型身份或独立性。

### 验收

A01–A08、A21、A25、A26。重点：没有历史SAR工程也能建首个项目；两研究同患者号不同数据不串；旧result A在B发布后保持A；坏binding不能降级“成功”；异步进程新增项目无需重启。

## N0-D · 人工文件用途澄清与回执重放（首要P0）

### 写入范围

`monitoring_document_authority_workflow.py`选择持久化与advance；`monitoring_document_authority_jobs.py` resolution/promote/verify；SourceRegistryService及document evidence resolver实际调用链；对应r7 routes与AdmissionWizard。

### 实施要求

1. **先校验再持久化**。未知候选、错batch/project、缺必需字段、无权限请求不得进入有效选择集；无效请求保证持久状态零变化。
2. 有效选择绑定project/attempt/document batch/digest/role以及真实认证principal；记录revision、幂等键、提交时间和理由。使用现有事务仓/CAS，不依赖共享`.json.tmp`完成并发控制。
3. 输入修改保留历史记录，不能只覆写同角色最后一个值。刷新/重启/无参数resolve读到明确有效revision；损坏不是“未选过”。
4. 角色已收敛时：相同选择幂等；与既有选择不同则显式冲突/过期/修订流程。禁止默默忽略后仍对用户表现为已应用。人可以澄清文件用途，但不能因此跳过文件合法性/权限/完整性。
5. **晋升回执必须冻结本次有效人工决策**的ID/digest/revision。verify函数使用receipt绑定的历史决策重放，不能不传、不能读latest。同时保留由模型给出的角色判断与用户澄清的不同来源。
6. 晋升收据schema同步更新所有校验器、注册元数据、重放加载和向后兼容；旧receipt仍可按原规则只读验证，不就地补写新身份。
7. 修复主文件blocked、补充文件allowed组合：先计算完整依赖状态，再构造supplementary_of；依赖主项未就绪时返回具体阻断/确认项，不触发KeyError、不独立晋升补充件。事务部分成功规则明确。
8. 内容确认只处理允许覆盖的警告。响应包括check_id/code、预期/实际值、具体证据、作用范围、替代动作。哈希损坏/越权/明确跨研究错误不能靠泛化确认消除。
9. 前端去掉自动泛化“医学核对已完成”的固定证明语。提交实际选中的可覆盖check和具体理由；认证actor服务端赋值；请求有in-flight与generation/cancel保护。
10. 文件上传/解析/可用于分析状态分离；来源台账不能在识别成功后长期为0且无解释。复用现有admission元数据，不伪造“已核验”登记。

### 验收

A09–A15。首要：机器仍有歧义+人工合法选择→promoted→同一receipt验证true→DocumentEvidenceResolver可读→mapping可取原文，刷新/重启后仍同样成立。修改当前选择后旧receipt仍重放旧决定，篡改旧决定则失败。

## N1-R / N3 / N4 · 同一Finding对象到原始证据

1. typed阅读DTO明确包含finding_id、claim_id、subject/site/spine、时间/精度、priority及其来源、kind、verification/coverage、verified_event_refs、source targets、unbound理由。display_seq只用于显示。
2. `public_findings`与mode输出使用同一投影函数和冻结证据索引。当前mode里存在锚点不等于公开API有锚点；以真实 `/results/{token}/overview` 为合同测试入口。
3. claim级证据支持多对多。payload级pool不能显示成每条都已精确核验；相同文本的sides/kinds集合保留显示来源，但底层还需保留side-kind-evidence对应关系，不靠笛卡尔积猜配对。
4. 空目录、部分引用未找到、外项目记录、版本不符分开处理。未解析引用仍留在覆盖状态中，不能只统计命中的event_refs宣称全部bound。
5. 受试者号是真实可复制/新标签打开的路由；问题标题定位该问题与事件窗口；每条证据能直接查看对应原始记录。没有AE也支持实验室/病史证据，不补造风险ID。
6. 同病例多事件可逐个定位，不把第一个相关事件当唯一来源。返回列表恢复filter/sort/page/cursor/selection/scroll/focus，快速切人不会混入旧请求。
7. 所有浏览动作0模型调用。Query仅按需生成/编辑/复制/导出，绑定所据finding/result，绝不加入确认→发送→关闭主线。

验收A18–A20、A22–A24；前后端公开字段白名单同步版本化，不能为方便导航删除授权或schema校验。

## N2 · 让宽屏成为工作区，而不只是更宽的卡片

当前已解除限宽/截图留白，保留这些修改。本阶段默认提供紧凑风险工作列表与选中详情；研究概览保留可切换，尚未确认替换默认首页。

列表首层显示受试者、具体问题、发生时间、优先级及原因、覆盖/核验状态；详情区用有语义条目分别呈现观察、推断、反证/局限、缺口和核实点，不强制每条填满固定模板。完整条目可展开，主列表不一次绘制成千上万条完整claim。

先移除重复流程说明和双层“风险真相”堆叠，正常正文13–14px/行高约1.35–1.45只是起点，不以缩字达成密度。证据计数应能展开并跳转；有临床含义的“疑似/未见/不能排除”等限定不能删。

用真实宿主页面测1366/1920/2560、200%缩放、长药名/多证据/长否定句。首屏建议≥8条可扫读的标准合成列表记录，不把这个建议变成剪掉内容的硬指标。记录computed styles、目标导航与0模型调用，而不是只给截图或卡片宽度。

## N5-M · 从主题配对变为医学命题验证

1. `_clues_agree`正向词频与等级集合只适合候选配对/警示，禁止继续当最终支持关系。至少区分same_topic、supported、refuted、insufficient、different_finding。
2. 命题以subject/event/predicate/value/unit/time/condition/negation/uncertainty表示。等级归属于具体事件和时间，数值单位不能仅比字符串，否定限定不能拆散。能确定性验证的部分先计算，剩余语义用有界定向核验。
3. 同负向或一致无风险不是医学争议；普通综合分析允许0/1/多条发现，数量限制作为资源上限而非要求凑数。全适用人群的覆盖状态保留；无发现集合有独立抽检/升级，不只核验阳性。
4. 全域由已确认语义映射驱动，研究药、背景治疗、救援、合并治疗分开。不要因只有一个域或没有AE就排除病例；缺数据表达为某分析主题不可评估。
5. 完整原文/原值存储与prompt预算分离。受试者和事件窗索引、按需原文、分块及覆盖账本替代“一次全表全字段塞两遍”。全表digest计算一次复用；增量范围由依赖决定。
6. 新策略用新版本与小规模完整fixture检验误报/漏报/错配/重复/覆盖/耗时，然后扩展研究全量；旧804条结果不原地改写为新策略已核验。

验收A16–A17、A25–A27；本轮相反趋势、给药前后、时间上下文分级只是最低反例，不能仅新增正则拟合。

## N6 · 测试/部署与完成口径（贯穿）

- 实际失败→修复后的模块/仓储/API测试，使用真实枚举/验证模型；审阅探针不是生产实现，不要把转录文件拷入应用作为补丁。
- 从头完整浏览器切片：合法完整资料→映射剩余语义澄清→facts→首轮分析→病例→证据→草稿。API直驱可用于诊断，但不得标成GUI通过。
- 保留同一项目验证刷新/重启/合法修订/取消恢复/同名文件更新；旧结果不变。第二研究要有真实表结构/域/时间差异，不只更改名称。
- 预期工作单元、queued/running/completed/failed/cancelled、字段覆盖、语义核验、发布可用性分别计数。不得把“身份校验10/10”当作“作业10/10完成”。
- 将测试C候选呈现、用户指派、校验拒绝、真正晋升、规则引用分层；当前“没读正文/已完全放行”推断缺少证据，必须改写。负向fixture不能通过放宽所有校验转绿。
- 96历史失败在同依赖base/head按regression/stale_contract/fixture/environment/unknown分类，每个断言变更有理由。不声称全部陈旧，不只跑绿色子集。
- 性能拆queue wait、provider、repair/retry、hash/parse、投影/UI；采集实际阶段计时和调用/token。旧口头“一天”不是性能基线；也不能用上传计时代表模型分析计时。
- 临时sentinel/脚本退出主路径须先盘点在途任务，安全迁入现有持久Graph/队列；不建新旁路watchdog。写作模块故障不能用全屏遮罩阻断监查只读导航。

## 3. 文件所有权与合入约束

| 负责人 | 主写范围 | 约束 |
|---|---|---|
| 运行/数据绑定 | main.py、project/result resolver、publication/mode读取 | N0-R/N1-R统一合同，不建立多个临时provider |
| 文档接入 | workflow/jobs/receipt/registry/F7路由 | 持久决策和重放schema同批改，补充依赖也在此完成 |
| 前端 | Workspace/ProductLoop/AdmissionWizard/公开route schema/CSS | 以真实DTO为准，N2/3/4单一合入负责人 |
| 医学分析 | ae_mh/规则/语义映射/覆盖 | 不为追求一致率放宽命题核验 |
| 独立验证 | fixture、实际模块/API/浏览器、性能/历史测试 | 不修改业务实现后自行用简化mock宣布端到端通过 |

角色可由同一Agent分阶段承担，不要求额外常驻进程。改同文件的工作串行合入；不得用checkout恢复整个文件覆盖别人的已验证修改。

## 4. 每个工作包必须交付

修改文件/调用链、原失败与修复后测试、实际部署版本与依赖、fixture与原始响应身份、用户路径证据、性能/覆盖统计、历史兼容与迁移、未验证项、下一步阻断。

关闭标签使用 `verified_fixed_module` / `verified_fixed_api` / `verified_fixed_browser` / `changed_unverified` / `partially_fixed` / `open` / `blocked`，同时记录证据路径。本轮审阅的selected-logic成功只能是局部证据，不升级成产品验收标签。

**0922V2首个交付定义：一份完整资料经正常UI形成结果；人工输入选择可重放；项目/结果/病例/事件/来源均不串；风险直接可用；刷新和增量后旧结果仍可靠。**
