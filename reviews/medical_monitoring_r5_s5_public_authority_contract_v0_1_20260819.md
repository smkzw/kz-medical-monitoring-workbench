# 医学监查 R5-S5 公共权威合同 v0.1

日期：2026-08-19  
状态：`PUBLIC_AUTHORITY_CONTRACT_FROZEN_FOR_INDEPENDENT_REVIEW`  
机器合同：`subject-temporal-public-v1` 与 `aemh-match-history-public-v1`

## 1. 边界

本文件只冻结两个未来公共 producer 的 exact contract。它不创建 producer、adapter、validator runtime 或测试，不改写既有 R1–R5，也不启动 8911。当前 R1/R4 访视、Journey、AE/MH 和 R5 S4 对象只按 `source_matrix.json` 复用已有 exact leaves；字典投影、`Any` 字段、synthetic fixture、私有 `_ReportedMatchOutcome` 与 R1 `historical_evidence_refs` 均不得冒充直接公共权威。

本合同本身不签发 `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1`、`ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1` 或 `ACCEPT_R5_S5_CONTRACT`。即使本合同随后被独立接受，也只解锁另行冻结的 public-authority implementation contract，S5 runtime 仍保持锁定。

## 2. subject-temporal-public-v1

- exact 对象数：17；closed enums：15；closed errors：53。
- 唯一 packet 为 `SubjectTemporalAuthorityPacket`，receipt variant 固定 `subject_temporal`。
- project/run/snapshot/cutoff/site/subject/spine、visibility、source-revision/content、locator 和 membership 必须全闭合。
- projection `schema_version` 与 receipt `authority_contract_version` 必须逐字等于 subject schema 的 `schema_version`；receipt `audience_contract_id` 固定为已 pin 的父 R5 常量 `contract.s4.1`，不得使用推造的版本名称。
- visibility 的 evaluation/projectable/hidden member/site 集合必须等于当前 scope 的精确 subject/site universe；source pair 与 locator 必须构成 sorted-unique、无空项、无闲置项的全分区。
- calendar 为默认轴；study day 仅在 exact accepted anchor 存在时生成。名义、实际和非计划访视分开；非计划访视禁止 planned binding/assignment，访视间事件不吸附、不 nearest fallback。
- 验证器扫描 cutoff、visit nominal/actual、event、risk、phase 与 pending mirror 的全部 temporal endpoint；任一 `study_day` 或 study-day 轴均要求同一 membership spine 内的 exact、可投影且有接受来源的 anchor event。
- study-day 数值只由 accepted anchor 的 exact calendar date 推导：anchor=0 时 `study_day=calendar_delta`；anchor=1 时不存在 day 0，delta>=0 使用 `delta+1`、delta<0 使用 `delta`。anchor 只能为 0/1；`study_day_zero_exists` 无 anchor 时必须为 null，有 anchor 时精确等于 anchor 是否为 0，不能自报。
- start/end 各自携带 exact/partial/conflicted/missing、候选值/范围、来源、主轴可投影性；几何固定 point/closed_interval/open_start/open_end。缺失端点不进入主轴，相关对象进入 `pending_date_items`。
- exact/partial/conflicted 候选与范围均执行真实日历解析；range 与 interval 必须有序。partial/conflicted 仅在存在合法有界范围且 `range_projection_authorized=true` 时才允许 `main_axis_projectable=true`。
- partial/conflicted 的 range 必须等于候选值展开后的精确 envelope；相同非缺失端点只能是 point，closed interval 必须存在可区分的有序端点。pending item 必须与目标 endpoint/domain/source 完全镜像，并精确覆盖所有缺失或不可投影的 visit/event/risk/phase，禁止遗漏、重复或额外项。
- 八域固定且恰好各一 track：ae, mh, cm, ip, lab_exam, hospital_procedure, symptom_efficacy, protocol_compliance。`applicable` 当且仅当该域实际发出 event/risk member；`not_applicable`/`not_provided` 必须 refs 为空且不得与该域成员共存。unknown 与 OTHER fail-closed。
- 每个已发出的 event 自身也必须是 `applicable`，并与对应 applicable domain track 精确一致；event-level `not_applicable`/`not_provided` 只能通过该域无 event/risk member 且 track refs 为空表达。
- 每个 source locator 必须由实际 axis/member/endpoint 消费；仅出现在 receipt pair、membership 或 evaluation identity 中不能掩盖闲置 locator。

## 3. aemh-match-history-public-v1

- exact 对象数：13；closed enums：11；closed errors：56。
- 唯一 packet 为 `AEMHMatchHistoryAuthorityPacket`，receipt variant 固定 `aemh_match_history`。
- projection `schema_version` 与 receipt `authority_contract_version` 必须逐字等于 AE/MH schema 的 `schema_version`；receipt audience 同样固定为父 R5 `contract.s4.1`。
- 每个 thread 从 immutable `reminder_created` 开始；`match_decided` 只允许 exact/ambiguous/rejected；withdrawn 与 reappeared 只能 append。
- later fact 同时保留 ref 与 content identity；证据集合只能单调扩张；原 reminder 和全部历史不可删除或重写。
- 每个 thread 恰好一个 seq=1 的 `reminder_created`，`original_reminder_ref` 必须精确指向它；后续 reminder fail-closed。
- `entry_id` 在整个 projection 全局唯一；每个 `original_reminder_ref` 必须在全局唯一解析，并解析到本 thread 唯一的 seq=1 reminder。
- exact/ambiguous 决策必须保留 candidate 与 later-fact identity evidence，rejected 必须保留非空 considered identity evidence；三种决策均必须保留 source evidence locator。
- identity evidence 为 exact typed object，分别标注 candidate/later_fact/considered_fact；entity ref/content identity 必须绑定 thread candidate 或 entry later fact，并同时绑定 entry snapshot 对应的实际 source locator ref、locator content hash 与 raw payload hash。整条 later-fact ref/content/membership 同步改写但没有相同 accepted locator authority entity 的输入仍 fail-closed。
- 非初始 projection 必须绑定 previous projection ref/hash 与逐 thread accepted prefix seq/head/content；验证器将前一包与当前包机械比较，拒绝跨版本前缀重写，而不只验证单包 hash chain。
- previous/current thread ref 集合与 prefix-anchor ref 集合必须双向相等；跨版本 project/site/subject/domain/candidate/reminder identity 必须稳定，禁止 thread 删除、phantom prefix 或候选冲突。
- history snapshot lineage 同样闭合：保留前缀逐字保留既有 snapshot，新增 suffix entry 必须使用当前 scope snapshot，任何 foreign snapshot 均拒绝。
- 每个 thread 最多一次 `match_decided`。withdrawn 必须引用本 thread 此前 match_decided 的同一 later-fact ref/content identity；reappeared 仅可发生在该 exact fact 已 withdrawn 后，并保持 identity 不变。无 match 的 withdrawn/reappeared、无 withdrawal 的 reappeared、重复 match 均 fail-closed。
- AE/MH locator 必须由 cutoff、thread evidence 或 history retained evidence 实际消费；receipt/source-pair/membership/evaluation-only 引用不构成消费。
- 每条 history entry 的 `risk_lifecycle_effect` closed enum 只有 `none`。补录/撤回/再出现均不得自动关闭、解决、降级或改写风险。

## 4. Hash、receipt 与来源

所有 hash 使用 UTF-8 canonical JSON、sorted object keys、无多余空白与 SHA-256；数组按 schema 声明区分 semantic order 与 set-like order。projection 先独立封口，receipt 再绑定 projection id/hash、visibility closure、evaluation content identities 和 source revision-content pairs，packet 最后绑定 receipt/projection hashes。任一身份、来源、顺序、成员或 hash 漂移均 fail-closed。

`source_matrix.json` 共 17 行，明确区分 reusable upstream leaves、reference-only projections 与两项 `contract_only_not_implemented` external producer requirements。

`exact_overlay.json` 的 `(target,parent_deferred_contract)` 必须与 accepted parent 的 deferred `(target,deferred_contract)` 构成精确 sorted-unique 集合，数量相等不足以通过，重复、遗漏、替换或乱序均 fail-closed。

Verifier 独立重建 overlay 的 exact root、unlock rule 和每一 mapping row，逐项核对 replacement source path、receipt variant、implementation status 与父 mapping recipe。`source_matrix.json` 的 root、17 个有序 entry、classification vocabulary、两个 future producer packet/projection path 和 `contract_only_not_implemented` status 由独立 canonical hash 与 exact producer contract 双重冻结，不依赖 generator 自证。

Manifest 的全部 protected pins 均解析到实际路径并重新计算。医学写作边界固定为 `deploy/frontend/packages/runtime/services` 五个 roots 下 relative path 匹配 `medical[-_]writing` 的 regular files；仅对匹配文件读取 bytes，按 UTF-8 relative POSIX path byte order 排序，逐项拼接 `path + NUL + lowercase sha256(file bytes) + LF` 后再 SHA-256；期望 count=542 与 aggregate 均必须匹配。

Contract stage 的 no-runtime/no-test 文件面同样冻结在 manifest：只扫描 `poc/medical_monitoring_ai_native_r5/src/mm_r5` 与 `poc/medical_monitoring_ai_native_r5/tests` 的路径名；任何 subject-temporal public、AE/MH match-history public 或 `s5_*` module/test 的 regular file 或 symlink 均 fail-closed。该扫描在 verifier main 的 normal/O2 路径中执行，不读取匹配文件内容。

## 5. Challenge registry

`challenge_registry.json` 原样投影已接受父合同 `R5C-101..164` 共 64 行，不创建第二 quota ledger；另有 194 个针对 locator/source/visibility/cutoff/date/geometry/pending/duplicate/reference/evaluation/history/prefix/cross-version identity 的 bounded contract tamper cases。合同阶段只冻结规范并执行 deterministic in-memory tamper rejection，不宣称未来 producer/runtime 行为已实现。

## 6. 生成与验证

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py
PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py
```

Verifier 必须检查 exact artifact set、全部 protected path/SHA/count/aggregate、parent/source SHA、schema exact keys/types/enums/nullability/cardinality、sorted-unique exact-set/source-partition closure、cutoff 双态、真实日历/range/geometry/pending/reference、study-day 算法、typed AE/MH identity evidence、跨版本 thread/prefix/stable identity、overlay/source-matrix exact artifact consistency、evaluation identity 闭合、hash recipes、64+194 challenge rows、脚本无 Python assertion statement，并执行 tamper-failure gates。任何失败均非零退出。
