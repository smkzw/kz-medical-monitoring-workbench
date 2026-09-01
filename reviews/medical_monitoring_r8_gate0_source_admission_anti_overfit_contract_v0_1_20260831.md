# 医学监查子系统 R8-0 联合准入合同 v0.1

状态：`CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`  
日期：2026-08-31  
适用范围：R8 首次真实资料、真实 harness/LLM 与真实应用验证之前的联合门禁  
上位依据：System Design v1.1、R0-R8 实施计划 v1.1、R7 阶段接受记录

## 1. 目的与硬边界

本合同只决定“何时、以什么证据、按什么顺序允许进入 R8 真实验证”，不证明任何真实项目、模型、医学结论或应用能力已经通过。

在本合同经独立审阅、关闭发现、冻结版本和摘要之前，禁止：

1. 列举、`stat/lstat`、读取、哈希、搜索或打开五个真实项目根目录中的任何对象；
2. 将真实项目内容或真实项目语义交给任何模型、harness 或外部服务；
3. 启动真实项目浏览器 E2E；
4. 以真实项目名、药物、疾病、量表、风险、列名、Sheet 名、坐标或目录结构编写公共业务常量；
5. 用 Codex/开发者手工医学答案替代独立 harness/LLM 的项目语义解构；
6. 用 synthetic/offline、组件测试、静态截图或 UI 数字宣称真实项目、真实医学质量、真实应用或 §15.4 已通过。

本阶段只允许 synthetic/offline fixture、空根、受控坏例和工作区内既有设计/合同证据。

五个真实项目在合同中只称 `P1..P5`。其真实路径是运行时受保护绑定，不进入公共合同、测试样例、日志、模型提示或用户界面。

## 2. 完成定义

R8-0 只有在以下六项均被同一冻结版本覆盖，并由 fresh-context 独立审阅接受后，才能解锁首个项目的来源准入：

1. 逐项目只读来源准入与隔离输出；
2. 防过拟合与隐藏挑战；
3. 独立 harness/LLM 职责、输入输出与失败语义；
4. 真实本地应用依赖、启动、停止、重启与一键入口准备；
5. 离页完成/失败通知，或用户明确接受限定范围的仅页面内状态；
6. System Design §15.4 的备份、恢复、迁移、回滚、卸载和真实浏览器验证程序。

任何一项缺失、冲突、不可评估或失败，均不得以其他项的成功抵消。

## 3. 统一状态语义

不得用单一 `complete` 同时表示“执行完成、覆盖完整、医学正确和用户确认”。

### 3.1 资料存在状态

`provided | not_provided | not_applicable`

- `not_provided`：该资料或字段未提供；不是通过。
- `not_applicable`：仅可由冻结的运行模式/覆盖合同及可定位依据确定；不得由“没找到”推导。

### 3.2 评估状态

`evaluable | not_evaluable | conflict | parse_failed | blocked`

- `not_evaluable`、`conflict`、`parse_failed`、`blocked` 均阻断相关完整性声明。
- 未知、未映射、无输出、空输出不得解释为“不适用”或“无风险”。

### 3.3 执行状态

`complete | partial | truncated | failed | timed_out | cancelled | interrupted | blocked`

- `complete` 只表示合同定义范围内的执行完整；不等于医学确认。
- `partial/truncated/timed_out/cancelled/interrupted` 必须保留原始终态，不得提升为成功或阴性结论。
- `no_candidate` 只有在执行完整、覆盖完整、来源范围明确且无阻断项时才允许出现。

### 3.4 处置状态

`candidate | accepted | rejected | superseded | revoked | re_admission_required`

模型结果始终从 `candidate` 开始；模型一致性、置信度或多数票不能直接产生 `accepted`。

## 4. 项目身份与来源绑定

首次来源访问前，必须先创建：

```text
project_ref      = opaque-project:<id>
source_root_ref  = opaque-root:<id>
output_root_ref  = opaque-output:<id>
admission_id     = opaque-admission:<id>
binding_digest   = sha256:<canonical binding bytes>
```

强制不变量：

1. `project_ref` 不含项目名、研究编号、疾病、药物或真实路径；
2. 一个活动的 `project_ref` 只能绑定一个 `source_root_ref`；
3. 一个 `source_root_ref` 不得同时绑定多个项目；
4. `output_root_ref` 按项目和 admission 实例隔离，且不在来源根内；
5. `identity_preflight` 的时间必须早于首次来源访问，且初始 `source_read_count=0`、`source_write_count=0`；
6. 文件中观察到的研究身份仅是 `observed_identity`，不能改写外部绑定；不一致时为 `conflict`；
7. 真实路径只存在于受保护运行时绑定层，对外证据使用 opaque reference 与不可逆绑定摘要；
8. `<id>` 必须由系统生成、在当前 registry 中唯一且不可复用；`binding_digest` 固定覆盖 typed refs、绑定版本、创建时间和当前 admission，重绑定、撤销或重新准入必须产生新 digest；
9. 每个 manifest、envelope 与 artifact 都必须引用当前 `binding_digest`；旧 digest 在撤销后只能作为历史证据，不能重新激活。

本合同不要求 HMAC、签名、密钥或安全凭据；目标是防止工程实现误复用项目身份，不扩展为安全系统设计。

## 5. 逐项目只读来源准入

每个项目必须独立执行，任何项目成功不得替代另一个项目。

```text
I0 contract_gate
→ I1 identity_preflight
→ I2 root_guard
→ I3 inventory_A
→ I4 observe_and_hash_A
→ I5 role_availability_A
→ I6 inventory_B
→ I7 observe_and_hash_B
→ I8 snapshot_compare
→ I9 independent_verify
→ I10 admission_decision
```

### 5.1 文件级证据

每个目录项均需记录；普通文件、包和压缩包至少记录：

- `relative_path`：同时保留原始路径字节摘要与 UTF-8/NFC 展示值；仅允许根内 POSIX 相对路径；禁止绝对路径、`.`、`..`、NUL、双向控制字符、控制字符与逃逸；原始路径或 NFC 规范化后发生碰撞均为 `conflict`；
- `entry_kind`：`directory|regular_file|package|archive|symlink|special|unreadable`；
- `size_bytes`、`mtime_ns`；
- `content_hash`：完整原始字节 `sha256:<64 lowercase hex>`，不是解析后文本或 JSON 的哈希；
- `snapshot_role`：`protocol|ib|listing|grouping|report|supporting|container|excluded|not_evaluable`；
- `read_status`、`evidence_ids`、`container_ref`。

角色不得仅凭文件名、目录名、扩展名、单一列名、固定位置或模型主观判断确定。角色依据只能来自访问前冻结的 operator/registry declaration、通用容器/MIME/结构证据及可重放的确定性 parser。互斥候选为 `conflict`；无法决定为 `not_evaluable`。

### 5.2 特殊对象

- symlink：只记录 `lstat` 与原始 target；不跟随。绝对 target、根外 target、环路或无法证明根内时阻断。
- archive/package：外层原始字节哈希与成员清单均保留；拒绝绝对成员、`..`、NUL、规范化碰撞、特殊对象、嵌套逃逸和解压炸弹；观察不得写回来源根。
- FIFO/socket/device 等 special file：不读取；若属于 required source，则 `blocked`。
- 重复文件：所有路径均保留。哈希相同不允许静默删除；角色、cutoff、来源身份冲突时为 `conflict`。

### 5.3 双快照与可变来源

A/B 必须使用相同绑定、策略、工具链摘要、范围及 `source_scope_spec_digest`。比较路径、类型、大小、mtime、原始字节哈希、symlink target 与容器成员。任一变化均为 `changed`，不得把两个快照拼成“稳定结果”。

若来源在准入后变化、工具链/策略摘要变化、绑定冲突或出现任何来源写事件：尚未 admitted 的候选进入 `re_admission_required`；已经 admitted 的当前 admission 立即 `revoked`，并创建新的 `re_admission_required` 候选。两者均保留原始变更/写事件证据；新 admission 必须重新执行完整 A/B，不得复用旧快照。

### 5.4 零写入来源与隔离输出

来源根必须通过冻结的目标系统 `source_access_profile` 以只读方式打开；不得在其中创建缓存、锁、缩略图、索引、临时文件、提取目录、`.DS_Store` 或应用输出。验证必须同时包括：

1. 前后树清单/摘要；
2. `source_access_profile` 声明的目标系统写事件/文件访问证据，记录监测范围、起止时间、工具/策略版本、退出状态及漏监测条件；
3. 输出根与来源根、其他项目输出根的路径隔离检查。

`source_access_profile` 的具体实现必须在 G2 前冻结，并在目标 macOS 环境的 synthetic shadow root 上验证“允许读取、拒绝写入、写事件可观察、监测失效可识别”。不得对真实来源做写探针。若 profile 不可用、监测范围不完整、存在漏监测条件、终态不明或只有前后树哈希，状态为 `not_evaluable`，不得 admission。任何来源写事件（包括外部进程产生的元数据文件）均使快照 `changed`；不能把副作用列入静默允许名单。

### 5.5 Source / Output manifest

Source manifest 必须包含合同、策略、工具链摘要，opaque identities，A/B 快照，角色 requiredness/availability，重复/冲突，稳定性，零写入证据，独立验证结果与状态转换。

Output manifest 必须包含 `source_manifest_digest`、`binding_digest`、run/binding/input/prompt/schema 摘要、全部输出 artifact 哈希、lineage、发布状态和隔离根。Lineage 至少显式绑定 `raw_output → envelope → parsed_output → validation → adjudication → disposition`，每条边均带 artifact id 与 SHA-256；替换任一 raw/parsed artifact 或跨 admission 复用均必须使验证失败。未列入 output manifest 的产物为 untrusted/quarantine；source/output digest 不一致时不得发布。

Canonical digest 采用冻结的 canonical JSON 规范；规范、schema 与摘要算法必须版本化并可独立重放。每个命名摘要必须在同一规范表中声明：输入字段集合、缺省/空值规则、数组排序键、字符串规范化、序列化器 id/version、哈希算法和独立 replay 命令。摘要表至少覆盖 contract、binding、source manifest、input、unit set、prompt frame、execution profile、raw、parsed、coverage、source anchors、validation 与 output manifest。未定义字段范围的 digest 不得进入 G1。每个 output manifest 都是单独 revision，必须包含单调 `manifest_revision`、`parent_manifest_digest` 与 `emitted_by_binding_digest`；同一 admission 只能有一个 current pointer。Replay 按 revision 链验证，不把多个 manifest 当作无序数组聚合。

## 6. 独立 harness/LLM 职责合同

### 6.1 责任边界

| 角色 | 负责 | 不得负责 |
|---|---|---|
| Codex/开发者 | 中立 prompt frame、schema、hash、parser、确定性 validator、coverage 对账、失败语义、挑战矩阵、产品集成 | 填写项目医学答案；添加项目词典；用静态规则补药物/疾病/风险/量表 |
| Harness adapter | 冻结模型 binding/profile；提交输入；保存 raw；报告超时、取消、恢复、fallback | 隐藏 fallback；改变输入；把 partial/truncated 伪装为完整 |
| 独立 LLM | 从冻结输入与来源锚点提取 listing、研究设计、药物/适应症、风险控制候选 | 凭常识补未提供事实；无锚点形成正式医学结论 |
| Parser | 严格解析 raw、校验 schema、保留错误与未知字段 | 静默修复截断 JSON、丢弃额外字段、补缺失值 |
| Deterministic validator | 校验版本、hash、identity、anchor、coverage、重复、状态迁移；按冻结的 QA 严重度表处理产品缺陷 | 解释医学语义、用字符串相似度修正候选，或从列名直接推导医学事实 |
| 独立 adjudicator/用户 | 基于候选及证据作医学审阅或用户决定 | 伪造确认、把模型置信度当真值 |

独立 harness/LLM 不可用时必须 `blocked/not_evaluable`，不得回退到 Codex 手工项目医学解构。

### 6.2 Canonical extraction envelope

四类能力共享同一 envelope：

```text
contract_ref: contract/schema id, version, digest
capability: listing_structure | study_design | drug_indication | risk_control
run: run/node/project/source revision refs, execution identity
input: source manifest refs, artifact hashes, unit-set digest, selection policy, canonical input hash
prompt_frame: id/version/digest, template/schema/coverage/anchor/normalization policy versions, zh-CN
binding: provider/model/adapter/profile/toolchain/version/effort/parameters, context isolation, timeout/cancel/resume/fallback policy
transport: execution status, interim status(streaming/checkpoint), terminal status exactly preserving complete/partial/truncated/failed/timed_out/cancelled/interrupted/blocked, terminal reason, failure code, start/end
raw_output: immutable artifact ref/hash/media type/length, received_as_is=true
parsed_output: artifact ref/hash, parser id/version, parse/schema status, unknown fields, capability payload
coverage: expected/processed/skipped/failed units, status and reasons
source_anchors: typed, resolvable, revision-bound anchors
validation: deterministic checks and findings
disposition: candidate-only state and independent review ref
```

任何 binding、input、prompt、schema、adapter、toolchain/container digest 或 source revision 变化都产生新的 execution identity 和新的候选；不得覆盖旧 raw output。`streaming/checkpoint` 只是运行中观察，不参与通过/阻断；只有 terminal status 进入 gate 判断。Terminal status 必须逐字保留 §3.3 原始类别，不得把 `timed_out/cancelled/interrupted/truncated` 折叠为 partial；`final_partial` 是 partial 的终态子类，必须同时保留原始 terminal reason，并阻断完整性声明。

### 6.3 项目无关 payload

四类 payload 只定义通用结构，不内置项目答案：

1. `listing_structure`：文件/Sheet/表区、表头层级、字段候选、实体/主键候选、日期/单位/受试者/访视候选、跨表关系、不确定项；
2. `study_design`：研究阶段、设计、组别、访视/时间窗、入排、终点、治疗与禁限用、评估与规则的候选及锚点；
3. `drug_indication`：药物/成分/机制/剂量、适应症、疗效与安全性知识候选、来源版本/日期、冲突和未知；
4. `risk_control`：控制点、适用范围、触发条件、证据需求、风险域、**医学风险分级候选**、例外、来源锚点和不确定性。医学风险分级候选不是 QA 缺陷 P0-P4；两套枚举、字段和处置链必须分离，模型不得直接产生 QA P0-P4。

未知列、实体、布局、药物、疾病、量表或规则必须使用判别式对象显式保留为 `unmapped {reason, source_anchor_or_reason_absent}` 或 `not_evaluable {reason}`；不得缺字段、写 `null`、映射到“最像的已知项”或转换为 `not_applicable`。允许的 reason enum 与覆盖后果必须在 schema 中冻结。

### 6.4 Source anchor

每个实质候选必须至少有一个可解析、版本绑定的 source anchor。Anchor 至少包括：source revision、artifact ref/hash、定位类型、页/Sheet/表/行列/段落或字节区间、引用摘要及解析器版本。Anchor 无法重放、跨 revision、范围越界或与摘要不一致时，候选不得通过确定性门。Validator 只能报告 anchor 的存在、范围、摘要和精确匹配结果；不得用编辑距离、同义词或医学推断把候选标签“修正”为来源文本。

## 7. 防过拟合合同

公共内核、prompt、schema、parser、validator、规则层和 UI 适配层不得依赖：

- 项目名、研究编号、真实路径、文件名或 Sheet 名；
- 特定疾病、药物、成分、机制、量表、终点、安全性风险或风险等级；
- 特定列名、列序号、坐标、固定表头层数或某一种 listing 布局；
- 某个项目已有 Profile/Timeline/checklist 或历史答案；
- case id、oracle、mutation label、hidden challenge 标签或测试元数据。

### 7.1 静态挑战

分别对产品代码/模板/配置、synthetic fixture 和测试期望运行 literal/AST 检查。产品范围发现真实项目、药物、疾病、量表、风险、列名、Sheet、坐标或路径专有分支即阻断；fixture/test 范围只允许虚构数据和明确的 challenge metadata，且这些 metadata 不得进入运行时输入。不得因 fixture 合法示例放宽产品扫描。

### 7.2 动态隐藏挑战

冻结 challenge generator 与 sealed oracle，至少覆盖：

1. 项目、疾病、药物、量表与风险实体换名；
2. 列名同义/异义、顺序改变、缺列、多行表头、合并单元格、纵横表转换；
3. Sheet/文件拆分与合并、未知布局、额外无关表、重复表；
4. 日期、单位、编码、空值与语言变异；
5. 缺失、冲突、partial、truncated、parse failure；
6. 无 baseline、隐藏 baseline、错误/过时 baseline；
7. runtime 无法读取 oracle、case id、mutation class 或 sentinel；
8. 跨项目上下文、缓存、输出根和历史答案隔离。

测试者可改变 prompt/task path，但覆盖范围必须等价。冻结 `challenge_coverage_matrix`，按 capability × mutation class × anchor class × unit class 记录 expected/observed/waived；waiver 必须有独立决定、保留在 expected 总数中且不计通过，直到由等价替代案例覆盖或被上位适用性合同明确判定为 `not_applicable`。任一 expected cell 缺失即 coverage 不完整。通过缩小输入、移除案例、改标签或把失败改成不适用不能制造通过。

### 7.3 模型选择边界

产品默认 profile 可以指向用户指定的 `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并保留 `deepseek/DeepSeek V4 flash:max` 的显式可配置接入；但模型标识不是合同通过证据。

每次真实调用必须冻结实际 adapter/provider/model/profile/effort/参数/超时/恢复/fallback。MTPLX 的等待策略必须允许其声明的长运行窗口；未到冻结的 hard wait 且无明确终态时不得判定失败。运行中的 streaming/checkpoint 不是成功也不是终态失败；`partial/truncated/failed/timed_out/cancelled/interrupted/blocked` 及 `final_partial` 必须保留各自标签并阻断完整性声明。Fallback 必须显式记录并产生新 binding，不能静默替换。

## 8. 真实应用、通知与 §15.4 准备

### 8.1 本地应用入口

在 synthetic/offline 条件下必须证明：

- 依赖闭包及版本可审计；缺依赖以用户可理解的中文 fail-closed；
- start/stop/restart、重复启动、残留进程、异常退出和健康检查失败均有明确终态；
- 用户只执行一个应用入口动作，无需 Python/Node/数据库命令、环境变量或端口管理；
- 应用拥有服务生命周期和 ready/failure 信号；不得把开发服务脚本称为一键应用；
- 失败不创建半初始化、半迁移或不可恢复状态。

### 8.2 离页状态二选一

真实项目运行前必须冻结：

- 路径 A：离页完成和失败信号均真实可见，以 `project_ref + admission_id + run_id` 路由回正确工作面，导航动作不得隐式启动分析；事件幂等、中文可行动，不暴露内部模型/状态码/hash/path；或
- 路径 B：以持久化用户决定记录明确接受限定范围的仅页面内状态；记录至少包含合同/应用版本、适用项目或全局范围、运行模式、决定时间及明确限制。项目绑定、合同/应用版本或适用范围变化时必须重新确认。

路径 B 只能声明 `page_local_status_explicitly_accepted`；不得声明离页通知或通知中心就绪。未选择 A/B 时为 `blocked`。

### 8.3 §15.4 synthetic 程序准备

先用 synthetic/offline 包验证：导出/导入、manifest/identity/lineage、备份损坏、干净恢复、升级前保护、迁移成功、关键边界失败、原版本保持可用、实际 rollback、凭据不随普通包明文导出、默认卸载保留数据、显式数据清除预览/确认/取消、混合版本与迟到回调防护。

这只证明程序准备，不证明真实 §15.4 已通过。

### 8.4 Ego(lite) 边界

预真实联合门通过后，才可用实际本地应用和 synthetic fixture 经 `ego(lite)` 验证一键入口、用户可见失败、通知路径及 §15.4 用户路径。G6 只允许 mock/recorded adapter，必须验证实际 binding digest 为 synthetic profile，禁止调用任何真实模型 binding。直接 URL、组件测试、静态 screenshot 或 API 不能替代 audience-facing 证据。

每项目来源准入和 harness 就绪后，才可进入该项目的真实应用/browser/§15.4 验证。

## 9. 有序 Gate 状态机

```text
G0 BOUNDARY_LOCKED
→ G1 CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED
→ G2 RUNTIME_LAUNCH_READY_SYNTHETIC
→ G3 NOTIFICATION_DECISION_LOCKED
→ G4 SYNTHETIC_15_4_PROCEDURE_READY
→ G5 PRE_REAL_INDEPENDENT_ACCEPTED
→ G6 SYNTHETIC_EGO_READY
→ G7 PROJECT_SOURCE_ADMITTED[P_i]
→ G8 REAL_HARNESS_READY[P_i]
→ G9 REAL_APP_BROWSER_15_4_READY[P_i]
→ G10 FULL_RUN_PASSED[P_i]
→ G11 INCREMENTAL_DISPOSITION[P_i]
→ G12 ROLE_ROUND_MATRIX[P_i]
→ G13 PROJECT_CLEAN_STREAK[P_i]
→ G14 GLOBAL_R8_REVIEW_READY
→ G15 CODEX_FINAL_DECISION
```

澄清：G1 只接受合同；G5 接受依据该合同完成的 synthetic runtime/notification/§15.4 准备。G5 前禁止真实来源、真实模型及任何浏览器；G6 是 synthetic `ego(lite)` 例外。G7 才首次允许逐项目只读来源访问。

失败状态：`FAILED | BLOCKED | REWORK_REQUIRED | CONTAMINATED_REVIEW_HOLD`。前置 gate 未通过不得产生后续通过声明。

## 10. Full / Incremental 与真实项目矩阵

- `full`：冻结截止点的全量 data listing 与适用资料；不得以差异文件代替。每轮冻结 `source_scope_spec`（导出范围、筛选条件、字段/表范围、截止时间与 mapping contract）。
- `incremental`：相对于已接受基线的新一轮全量 listing 或锁定期间修订后的新全量 listing，比较新增、修改、消失记录及前后风险/趋势；不是只读取 delta 文件。只有 baseline/current 的 `source_scope_spec` 经确定性 compatibility check 通过后才可比较；不兼容时为 `conflict/not_evaluable`，不得解释记录增减。
- 若项目没有第二个兼容全量快照，incremental 为 `not_provided`，不得宣称已通过；不阻断该项目明确限定的 full 结论，但阻断“全项目 incremental 已验证”。
- 旧记录消失前必须先验证导出范围、筛选条件和真实删除，不得自动解释为数据删除。

每个项目分别维护：

```text
project × mode(full/incremental) × role(engineer/medical monitor)
× round(1/2) × task-path × coverage × source revision
× model binding × app version × result × open defects
```

工程师与资深医学监察员使用相互隔离的独立会话；每轮 task path/prompt 不同但 coverage 等价。最终要求每个适用 cell 连续两轮无开放 P0-P4。

## 11. 缺陷传播与 clean streak

1. P0-P4 定义在 R8 前冻结；可增案例，不得改严重度制造通过。
2. 任何开放 P0-P4 使相应 cell 失败。
3. runtime、启动、通知、备份迁移、输出隔离、source identity、adapter、schema、状态权威等共享缺陷默认传播到 P1..P5、双角色、两轮；只有带版本的 dependency-edge 证据（producer、consumer、contract、affected gate）才能缩小，不能按标题或文本相似度合并/缩小。
4. 项目特有来源/投影缺陷至少传播到该项目所有受影响模式、角色、输出和相邻消费者。
5. 传播范围不明时按全矩阵处理。
6. 修复必须从最早受影响 gate 重跑；不得只重跑发现问题的页面。
7. 合同、应用版本、harness binding、source revision、任务矩阵或数据窗口变化后，旧 clean streak 失效。
8. “非问题”关闭须有可定位证据、理由、复验证据和独立决定。
9. P0/P1 进入 `CONTAMINATED_REVIEW_HOLD`；P2-P4 阻断受影响 cell；二者均需保存失败证据并重新累计两轮。

## 12. 机器可验证证据

至少提供：

1. 冻结合同、schema、canonicalization、policy 与工具链 digest；
2. synthetic source/output manifests 与 schema validation；
3. canonical JSON/hash replay；
4. A/B mutation、duplicate、conflict、symlink/archive、special-file、path-escape、root-separation 与 write-trace-unavailable 坏例；
5. admission/revocation/re-admission 状态重放；
6. extraction envelope 的 input/prompt/profile/binding/raw/parsed/coverage/anchor digest 重放；
7. strict parser 对未知字段、缺字段、多 JSON、Markdown、截断和非 JSON 的 fail-closed 测试；
8. 静态 hard-code scan 与动态 hidden mutation；
9. app start/stop/restart/one-click/notification/§15.4 synthetic 证据；
10. 独立 reviewer 的发现、修复、复验和最终 gate 决定。

证据有效性由其依赖摘要决定，不使用任意小时数作为“新鲜度”。合同、schema、工具链、目标系统 profile、应用版本、source revision、binding 或覆盖矩阵任一依赖摘要改变，对应旧证据即 `stale/superseded`，不得复用为当前通过证据。

## 13. 硬停止条件

出现以下任一项立即停止相关 gate；涉及边界、来源权威、输出隔离或共享合同则停止全部真实推进：

- G7 前访问任何真实项目文件或元数据；
- G8 前把真实语义提交模型；G6 前启动任何浏览器；
- 来源被写入、修改、删除、重命名、改权限或回写输出；
- 输出进入来源、其他项目或不可识别共享目录；
- 手工端口/服务/数据库成为用户前提；
- 隐式安装、下载、fallback 或模型替换；
- 任一 required evidence 为 partial、truncated、not_evaluable、conflict、parse_failed 或 blocked；
- 用模型输出、UI 数字或多数票替代来源/QC/独立决定；
- 任一真实 P0-P4 开放；
- 角色互看结果、复用上一轮状态或实现者接受自己的修复；
- 缩小矩阵、移除 hidden case、改变标签/严重度或把失败改为不适用；
- 真实缺陷修复后未按传播范围重跑。
- 路径 B 缺少当前范围的持久化用户决定记录，或路径 A 路由到错误 project/admission/run；
- 以 `passed (N/A)`、`complete (not_applicable)`、`out_of_scope` 等措辞把未评估 gate 写成通过。

## 14. 禁止声明

在 G15 前不得声明：

- 真实项目、真实模型泛化、真实医学质量或所有项目已通过；
- R7 synthetic/offline 基线等于真实一键应用；
- 页面内播报等于离页通知；
- synthetic §15.4 等于真实备份/迁移/恢复/回滚/卸载；
- 未经 `ego(lite)` 的页面操作等于真实浏览器验证；
- `not_provided/not_evaluable/conflict/parse_failed/blocked` 等于通过；
- 在 `passed/complete` 后附加 N/A、not_applicable、irrelevant 或 out_of_scope 来暗示通过；
- 候选等于正式 AE/MH、PD、风险、药物/疾病知识或用户确认；
- 模型标识、长等待、非空输出或 clean UI 数字等于医学正确；
- 商业化、生产、法规认证、电子签名、受监管合规或本地文件绝对不可篡改。

## 15. 本草案的当前处置

当前处置：`CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`。三轮同 session 独立会商已关闭可重放、零写入、lineage、coverage、状态、分级、通知、incremental 与 clean-streak 边界发现；HMAC、签名、BLAKE3/CAS、FIFO 全局锁等超出用户范围的安全化/平台化设计未纳入。该标签只接受合同，不接受 R8-0、真实来源、真实模型、真实浏览器、真实 §15.4 或真实医学质量。

下一步仅允许：

1. 冻结当前文件摘要与接受记录；
2. 进入 G2 `RUNTIME_LAUNCH_READY_SYNTHETIC`，实现并验证目标 macOS `source_access_profile`、canonical digest 表、manifest replay 与 synthetic runtime；
3. 后续按 G3-G6 完成通知决定、synthetic §15.4、预真实独立接受和 synthetic ego(lite)；
4. G7 前不得直接读取真实项目。

当前明确禁止：真实项目访问、真实模型调用、服务启动和浏览器运行。
