# R7 Slice-07C-4 中文产品闭环合同 v0.1

日期：2026-08-29  
状态：`SUPERSEDED_IN_PART_BY_V0_2_REVIEW_TOGETHER`

> 冻结审查必须同时读取
> `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_2_20260829.md`；冲突时 v0.2 优先。

## 1. 目标

把 07C-1～07C-3 已接受的 synthetic/offline 服务端能力接成资深医学监察员可直接使用的一条
产品路径：选择监查方式和数据范围，确认特殊关注规则，启动后离页，返回时继续查看真实进度，
结果完成后进入同一运行的项目/中心看板，并从风险、流向或受试者表进入同一身份的 Patient Journey。

本切不新增医学推理，不以静态 fixture 冒充已发布结果，不运行真实项目或真实模型，不启动 8911，
不触碰医学写作，不设计或测试系统安全功能。

## 2. 用户任务与首屏

项目风险概览是默认入口。首屏只回答四个问题：

1. 当前有没有正在进行或等待开始的监查；
2. 如果没有，能否开始一次新的监查；
3. 当前运行到了哪里、正在做什么；
4. 若结果可用，如何进入本次结果。

项目概览顶部使用一个紧凑“本次监查”工作条，不额外堆叠工程状态卡：

- 无当前运行：主按钮“开始一次监查”，旁边是“查看历史”；
- `waiting_start/running/interrupted/completed + result_available=false`：主按钮“查看本次进度”；
- `completed + result_available=true`：主按钮“查看本次结果”；
- 不显示角色、权限、内部 run id、manifest、receipt、authority、publication、token、只读等后端术语；
- 中心页继承当前项目运行和结果身份，只显示“本次结果范围”和返回项目概览，不在中心页重复启动向导。

## 3. 四步中文向导

向导为项目页内抽屉或对话框，桌面宽度 720～880 px；不跳离当前项目。四步固定为：

1. **选择监查方式**：具体三类卡片与执行基础以 v0.2 §12 为准；只使用服务端 options 文案和
   可用性，不从文件名或前端状态推断。
2. **确认数据范围**：显示当前完整数据版本、截止时间、中心范围；增量模式同时显示推荐的同模式
   已发布基线和原因。多候选可选择；不可比较、过期、跨项目或未发布基线明确禁用。
3. **选择特殊关注**：列出项目已确认规则 revision 的中文摘要、适用范围和起始运行；默认沿用服务端
   推荐，但用户可取消。页面提供“增加特殊关注”，自然语言 preview 只展示 2～5 个解释候选；用户
   选定并确认后才创建 revision，再回到本步显式勾选。
4. **确认并开始**：用一屏摘要列出监查方式、数据范围、比较基线、中心数量、受试者数量、工作项
   总数和特殊关注。主按钮“确认并开始监查”；开始后立即关闭向导并进入该 public run 的进度。

前端不得自己计算工作项分母、增量差异或 idempotency identity；规范请求和推荐理由均来自服务端。
只有用户实质改变模式、数据、基线或规则选择时才换新 idempotency key。同 key 超时后先查询 public
run；不存在时只重试一次。输入和选择在失败后保留。

## 4. 历史与主动作

“查看历史”打开右侧抽屉，按服务端倒序展示有限条目：监查方式、数据截止、状态中文、精确百分比、
结果是否可用及一个主动作。历史不显示数据库状态名或内部失败码。

- 正在执行/等待/中断/结果整理中：动作“查看本次进度”；
- 结果可用：动作“查看本次结果”；
- 已完成但不可用：仍进入进度并显示“分析已结束，结果整理未完成”；
- `blocked` 使用具体中文原因并隐藏普通用户恢复动作；管理员动作仍只存在于既有进度面板；
- 历史与当前主动作必须读取同一 `/runs` 投影，不在前端二次解释 `completed`。

离页时不停止、不取消、不写运行状态。返回项目时先读取历史确定当前 public run，再加载该运行进度；
页面隐藏时暂停轮询，恢复可见时立即刷新。MTPLX 只要服务端仍报告租约/心跳有效，页面保持运行中，
不得因长时间无文本、一次请求超时或前端轮询失败显示失败。

## 5. 进度面板贯通

复用 07A 组件与真实 progress 投影，不建立第二套进度状态：

- 百分比、分子、分母和阶段数字均来自服务端冻结 manifest/work-unit；
- 当前工作和最近进展保持滚动、可扫读，普通用户不见底层 adapter/model/session；
- `publication_state` 只转成用户文案；完成但结果未整理好时进度保持可见；
- 只有管理员看见停止、继续、整理/重新整理动作；医学监察员只查看；
- 刷新失败保留上一次事实并标明最后读取时间，不把旧数据伪装成实时。

## 6. 公开结果上下文桥

07C-3 `result-entry` 只返回公开运行、快照、截止、中心选项和 `result_context_token`，而既有 R5 GET
接口以内部 run/snapshot/cutoff 读取 authority packet。07C-4 必须由服务端增加一个最小公开解析桥，
前端不得收到或保存内部 run id、authority digest 或 receipt identity。

公开结果读取固定为三类 GET（命名可按现有 router 习惯调整，但语义不可改变）：

- project/site overview：以 `project_id + result_context_token + optional site_ref` 读取；
- subject workspace：再加 `subject_ref`、窗口和可选风险/事件定位；
- source evidence：再加风险实例与 source locator。

每次请求都必须重新解析 token 到同一可用 ResultPublication，核对 project/public run/snapshot/cutoff/
publication revision/R5 packet digest/site coverage 后，再调用既有 R5 adapter/provider；不得复制 S4→R5
组装器。返回给前端的 envelope 使用公开运行和公开快照语义，且由服务端重新生成一致的 response digest。
token 失效、结果不再可读、中心越界或 authority 漂移时整页失败关闭，不回退上一运行或 synthetic fixture。

## 7. 结果看板与 Patient Journey

结果入口先打开项目风险概览，显示本次监查方式、数据截止和中心范围的简短身份条；主体复用已接受的
R5 项目/中心看板、受试者流向图、风险列表和表格。不得另做一套结果卡片。

- 项目 → 中心：保留同一 result context，仅增加合法 `site_ref`；
- 项目/中心 → 受试者：服务端返回可投影受试者的公开 subject/spine/window 定位；
- 风险或流向逐例 → Journey：进入既有共享访视/时间轴，保留风险、事件和来源定位；
- Journey 必须是一条横向访视轴，事件按日期/研究日位于轴下对应轨道；AE、MH、合并用药、试验药、
  检验/检查、住院/操作、症状/疗效、方案符合性使用已有不同图形和轨道，风险是独立叠加标记；
- 点击紧凑编号事件显示详细内容并对应下方编号明细，不把长文本平铺进时间轴；
- Patient Profile/指标趋势、事件明细和原始来源继续从同一 Journey 上下文跳转；
- 1280/1440/1920 桌面宽屏下访视轴尽量完整显示在内容列，窄屏只允许组件内部横向滚动。

## 8. 前端状态与中文错误

页面只保留五类产品状态：加载中、可开始、已有运行、结果可用、暂不可用。具体错误按服务端中文显示：

- options/token 过期：`监查范围已更新，请重新确认`，保留输入并重读 options；
- 同 key 异请求：`本次设置已发生变化，请重新确认后开始`；
- 无稳定业务键：`当前数据尚不能与上次结果逐项比较`；
- 结果尚未整理：`分析已结束，结果整理未完成`；
- 中心越界：`该中心不在本次监查范围`；
- 结果身份或来源无法核对：`本次结果暂不可查看，请返回进度页`。

不得显示 `waiting_start`、`publication_state`、`result_context_token`、HTTP status、stack、adapter、
manifest、authority、candidate、正式事实、候选信号、只读等用户无关词。

## 9. 最小实现边界

允许修改：

- `frontend/src/features/medical-monitoring/r7/` 新增 setup/history/result-context 的 API、纯投影、交互组件与 CSS；
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`、R5 adapter/route state 的最小接线；
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css` 的相关布局；
- `services/api/app/medical_monitoring_r7_product_router.py` 的公开结果上下文桥；
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py`：仅 additive token 列、
  `(project_id, result_context_token)` 唯一索引、finalize 写入与按 token 读取；不得改变 07C-3 状态机；
- 现有 R5 `validateEnvelope` 不得改写；公开结果使用新的 product result-context client；
- 相关 product/R5/R7/Node/render/ego synthetic tests 与 task evidence。

禁止修改医学写作路径、R1-R6 已接受医学算法、真实项目资料、全局导航结构或安全功能。优先复用现有
R5/R7 adapter、route state、progress store、SubjectFlow/Journey 和视觉 token；不引入新依赖或新状态库。

## 10. 决定性验收矩阵

1. 三类模式 options→确认→prepare-and-start；日常增量/全面分析、锁库前多基线和核查前新固定范围分别覆盖。
2. 规则 preview 歧义/确认/选择/取消；过期 options 后保留输入并重确认。
3. 同 key 同请求重放、异请求 409、一次超时查询/重试；不重复创建运行。
4. 历史主动作三态与 `completed + result_available=false`；离页/返回恢复同一 public run。
5. 进度数字、当前工作、最近进展与服务端 payload 一致；隐藏页面暂停，恢复可见立即刷新。
6. result context 正常、过期、跨项目、中心越界、publication drift、R5 authority drift 全部失败关闭。
7. 项目看板→中心→流向/风险→Journey→Profile/事件/来源保持同一公开结果身份。
8. Journey 横向访视轴、八域事件、独立风险叠加、编号详情与宽屏无页面级横向溢出。
9. 1280/1440/1920 ego(lite) 完成医学监察员从零操作；同时复核键盘焦点、中文可读性、密度和空/错态。
10. 聚焦 Node/render、产品/R7/R5 相邻 Python、Vite build、console/network、8911/5174 停止和医学写作
    保护门禁通过。

## 11. 接受边界

只有合同独立会商通过后才实施。实现接受仅代表 synthetic/offline 用户闭环和视觉交互可用；不代表真实
项目解析、真实模型医学质量、R7 总体或 R8。真实项目与真实模型仍在后续独立阶段验收。
