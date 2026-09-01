# 医学监查 R5-S5 公共权威实现合同 v0.1

日期：2026-08-19  
状态：`IMPLEMENTATION_CONTRACT_FROZEN_FOR_INDEPENDENT_REVIEW`

## 1. 边界

本快照只固化 `subject-temporal-public-v1` 与 `aemh-match-history-public-v1` 的未来 Python 实现合同。它不创建 producer/runtime/test/evidence，不修改既有 R1–R5、root init、frontend/services/packages/runtime/deploy/医学写作或真实项目，不启动 8911，不签发任何接受判定。

## 2. Exact public API

- Python `>=3.9`；三个源模块仅使用 3.9 可用语法。
- 共享六个 packet object，subject 总数精确 17，AE/MH 总数精确 13；序列化字段与已接受 schema 递归完全一致，任何 extra leaf 失败关闭。R5C-157 至 R5C-163 的 AE/MH 正例使用不复用 base 的全局唯一 decision ref/authority identity，并冻结合法 exact/ambiguous/rejected/withdrawn/reappeared 前置序列；本阶段不生成 final-graph hash。
- Subject builder/validator 共用 exact `SubjectTemporalSourceBundle`；AE/MH builder/validator 共用 exact `AEMHMatchHistorySourceBundle`，`previous_packet` 仅作为两个 API 的独立 typed optional 参数。`R5AuthorityReceipt` 与 cutoff binding 都在 common bundle 显式可达；不接受 `Mapping`、`Any`、artifact 或 fixture 作为权威。
- `source_type_access_paths` 固化从两个 root bundle 到每一种外部 source type 的逐段可达性；272 行另以 structured ref JSON 逐段固化 field/one-many-optional/terminal，verifier 独立递归解析 exact input schema 与 pinned Python AST。
- schema/authority version 固定 `2026-08-19.1`，audience 固定 `contract.s4.1`。

## 3. 权威连接与不变量

`source_join_matrix.json` 对 272 个 contract/object/leaf 实行逐叶唯一覆盖。身份、visibility、source revision-content pair、locator、cutoff、日期/研究日、访视、八域、membership、receipt/hash 和 AE/MH 跨 snapshot 追加历史均从已命名 typed source 联接；nearest、fixture、sentinel 或本地推测均不得替代权威。

每一行同时冻结 source dataclass 类与字段路径、source/output semantic class、join key、derivation/reducer/closed mapping、cardinality/nullability/ordering 与 unavailable fail-closed code；verifier 逐段解析所有钉住的 Python AST，并拒绝字段虽存在但语义类别错误的替换。风险 content identity 只来自同一 accepted risk authority；severity 只来自 accepted risk severity 及具名 closed conversion；`risk_type_zh` 只走八域冻结中文映射；applicability 使用区分 `not_applicable`/`not_provided` 且空成员的 exact controlled record；cutoff locator 唯一绑定一条 reachable cutoff record。风险日期仅能经 `ControlledTemporalEndpointBinding` 的 target/endpoint-role/authority-ref/closed date-field selector/locator 链路解析，binding 禁止携带日期、临床值、研究日、范围或 hash，也禁止从 `RiskCandidate.detail` 推测。

AE/MH append 输入为 exact `AEMHDecisionAuthorityRecord`：event/match/reason 为 closed enum，fact/candidate/locator 均引用 bundle 可达对象，并携带具名 decision authority identity/content hash/source。该 owner-authored controlled record 具有唯一 generation/validation contract；本文明确不假装已有上游 append-only decision ledger。

81 个已接受 error code 按 `invariant_error_matrix.json` 的 1..81 优先级收集后稳定排序；normal 与 O2 不得不同。任何 issue 存在时不得发出 packet。

## 4. Future runtime 禁止项

三个源模块禁止文件 I/O、dynamic import、reflection、`importlib`/`pathlib`/`open`/read/write/getattr/eval/exec/compile 及其 alias/indirect call、artifact/test import、Python `assert`、nested import、`*args`/`**kwargs` 和基于 case id 或 fixture/sentinel 字符串的分支。symbol table 扫描 Assign/AnnAssign/NamedExpr/tuple-list/container/subscript/parameter/definition/import-alias 等绑定形态，拒绝 `SourceRevision=__builtins__['open']`；同时精确允许 `@dataclass(frozen=True)`、`dataclasses.replace`、`str.encode`、`hashlib.sha256(...).hexdigest()`。builder 必须返回 exact packet constructor flow，`return source` 失败；validator 必须由 exact `PublicAuthorityValidationResult` constructor 返回，拒绝 candidate/source 异型恒真比较，且 `issues/ok/primary_code` 每个 sink 都联合依赖 candidate+source，AE/MH 非初始还依赖 previous。10 个动态 vectors 只在未来专用 normal/O2 pytest node 执行。另有 `python3 -I -B` isolation probe：只在hook前解析/校验并bootstrap冻结src/tests路径、导入三个producer，随后安装audit hook，仅在四个public API调用窗口拒绝文件、网络、subprocess、dynamic import/exec/eval/compile；合法初始import不得被hook误拒。

## 5. 测试与门禁

- future execution contract 精确为 231 个独立 executable spec，覆盖 236 个 accepted case trace（subject 48 + 95，AE/MH 16 + 77）；5组别名精确为 PA-007/R5C-103、PA-034/PA-120、PA-035/PA-121、PA-118/R5C-108、PA-129/R5C-111，仅是non-semantic dedup，不是当前运行证据。
- inherited 64 行原样嵌入 accepted registry：10 行保持 accept polarity、typed packet type 与 canonical hash recipe（不伪造未来 hash），54 行保持 reject 及 exact typed outcome/error。
- 全部 116 行 `fully_reseal_after_mutation=true` 原样保留；合同只验证 reseal operations 的语法、类型、路径、写顺序与 DAG。64 个 inherited 谱系拆分为 10 个 accepted `source_to_builder_output` expected-value/diff specs 与 54 个 rejected `constructor_decode` exact-error specs；全部仍为 `contract_spec_only=true, producer_executed=false`，reject 不再冒称 builder。
- reviewer v4 的历史发现为 15 组/104 行；因完整旧成员未交付，只如实保留已知 PA-007/008、PA-025/026、R5C-157/158 示例，不臆造其余成员。reviewer v5 的 10 个 duplicate groups 与四个已知冲突对均经 case-specific authority field/subgraph transformation 消除。当前只审计 adapter 后完整输入constructor graph+harness lane 的spec identity，不含 case/rule/label/oracle/reseal mode；相同输入只可有相同outcome，当前 `current_conflict_groups=[]`、`contradictory_identical_specs=[]`。producer acceptance 才能产出 actual graph hashes/traces。
- `fixture_catalog` 内建 5 个 subject/AE-MH 完整 constructor graph；231 个独立 future executable spec 覆盖 236 个 accepted case ID，嵌入 closed source/candidate/corruption adapter、before/after predicate、allowed/protected diff 与 typed packet/error oracle。structured value terminal 与 relation key 分离；每个authority/context reference均纳入DAG，output key必须strictly prior，历史v8的207个future/self component/69 leaves当前均为0。历史1168个label/field mismatch当前为0；exact-one/one-or-more/zero-or-one与48个显式none分支逐行解释。
- 余下 22 行 artifact-governance 案例不计入 runtime；当前 verifier 先验证每个原 artifact 零 issue，再重放 mutation，并要求实际 issue 有序列表与冻结 oracle 完全相等。PA-147/148/149 合法冻结父 verifier 的两码顺序，primary 为第一码，secondary 不得丢弃。
- verifier 重放已接受公共合同 verifier，并检查 10 文件快照、全部 source/protected pins、542 文件医学写作聚合、exact path sets、producer/bytecode 不存在与 8911 停止。
- 合同工具为无 shebang、不可执行文件，统一通过 `python3 -B` 调用。
- verifier 仅对 5 处为保持 Python 3.9 可解析 `Optional`/`Union` 语法的注解使用行级 `UP007`/`UP045` 抑制，未增加项目级宽泛 Ruff ignore。
- 唯一 Ruff acceptance command：`/Users/smkzw/.local/bin/uvx --offline ruff check --no-cache tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py`
- verifier 在内存中执行 72 个 controls；保留7个reviewer-v9定向反例，并新增6个reviewer-v10定向反例：非法TimeRef ISO日期、ScopeBinding cutoff AUTH占位、跨源cutoff不一致、authority/context反射引用、selected reducer值与output leaf不一致、R5C-109缺任一linked operation，均核对精确拒绝码。5个fixture逐维度关闭PublicScopeIdentity all-equal与完整cutoff chain；R5C-109先应用5个同源linked source operation再机械构造builder预期规格；R5C-110/116在baseline output真实实例上应用exact source diff；R5C-157..163冻结完整accepted-schema packet并独立重算entry/thread/membership/projection/receipt/packet。其余controls继续覆盖alias、relation-key、reseal、scanner、sensitivity、isolation与governance顺序；另独立执行全部22个governance exact-ordered issue probes。

## 6. 共享 common 无效化规则

未来两个 producer 的验收证据必须同时 pin `public_authority_common.py` 同一 SHA-256。common 任一 byte 变化立即同时使两个 producer acceptance token 失效，必须重跑 normal/O2、Ruff、231个独立spec/236个trace、source/SHA/boundary 门禁并重新独立审阅。

## 7. 解锁规则

只有后续独立审阅者对这一不变 SHA 集签发 `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT`，才可创建 manifest 中精确 11 个 producer 路径。该 token 不接受任一 producer，不解锁 S5，不代替 `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1` 或 `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`。
