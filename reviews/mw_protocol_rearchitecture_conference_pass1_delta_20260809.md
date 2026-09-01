# Protocol 正式设计会商 Pass 1 修订核对

日期：2026-08-09  
规格：`plans/mw_protocol_multi_agent_rearchitecture_design_20260809.md`  
当前版本：`design-v1.2 / REVISED_FOR_CHAIR_DELTA_REVIEW`  
判定：`READY_FOR_SAME_SESSION_CHAIR_DELTA_REVIEW`，尚非用户复核 READY。

## 会商输入

- chair Pass 1：
  `runs/conference/mw_system_rearchitecture_audit_20260808/general_chair_pi_qwen38.md`
  — `REVISE_BEFORE_USER_SPEC_REVIEW`，F-01–F-15。
- participant Pass 1：
  `runs/conference/mw_system_rearchitecture_audit_20260808/general_pi_deepseek_flash.md`
  — `REVISE_BEFORE_USER_SPEC_REVIEW`，F1–F12。
- 两者均为 fresh-context 只读审阅；participant 未读取 chair 或 Codex self-review。

## Chair 必改项处置

| Finding | v1.2 处置 |
|---|---|
| F-01 空泛骨架可过门 | 新增 SubstantiveContentContract、positive claims/objects/bindings、skeleton fail-closed 与历史空正文 fixture |
| F-02/F-07 零/无链接证据 | 新增 required/researched/linked 三分母、最小来源类和 RecommendationOption evidence_class；D1禁止伪装竞品全文证据 |
| F-03 44字符/标题准入 | 新增 MedicalAdmissionUnit 正向 schema、locator/context/claim requirements 和永久失败 corpus |
| F-04 finding 被 supersede | Q1 current P0–P4 open_count=0；限定 typed disposition；风险接受/自由文本不能 clean |
| F-05/F-06 编辑/摘要第二事实源 | 新增 EditClass；不确定默认 fact_or_uncertain；Protocol Summary 不能生成事实 |
| F-08 重复语义效果 | logical_source_key+content hash、DecisionRecord CAS、artifact复用和 exactly-once semantic effect |
| F-09 依赖图/重锁 | typed edges、hard/order DAG、cycle fail-closed、高fan-out不截断、确定性重锁谓词 |
| F-10 Word 门被削弱 | D011/D012 PoC失败保持阻断；HTML/LibreOffice不替代Word；新增§23.4原生回执生产者PoC |
| F-11 reviewer相关盲点 | P0/P1 final verifier异执行身份/可用时异模型；repair包不携带代写答案；完整coverage digest |
| F-12 event/checkpoint双写 | event+artifact为权威、checkpoint为执行提示；transactional outbox/inbox和崩溃不一致规则 |
| F-13 审计交付缺失 | 四层通过冻结 SubmissionEvidencePackage，不增加强制会签 |
| F-14 旧Synopsis/CSR措辞 | 新建 `runs/MW_PROTOCOL_DESIGN_D017_SCOPE_SUPERSESSION_20260809.md`；历史不原地改写 |
| F-15 Harness敏感态 | NodeExecutionContract 增 sensitivity/provider/region；fallback重新打包，禁止跨provider搬运原会话 |

## Participant 增量处置

| Finding | v1.2 处置 |
|---|---|
| F1 无Word receipt producer | 新增§23.4并前置到Phase 0/1，真实Word打开/更新/重开/PDF/回流/机器回执；失败不降门 |
| F2 batch复活REJECT | verdict绑定item+revision+hash；batch只采用latest PASS；新证据revision重审是唯一改变方式 |
| F3 vacuous contract | non-vacuous meta-gate和110/110 mechanical registry lint |
| F4 unknown_outcome | append-only ExecutionReservation、三态、同session回收、禁止自动重派、显式retry decision |
| F5 分母自我重分类 | 分母变更必须用户问题卡；无质量豁免；下载/识别困难不能作为排除理由 |
| F6 编辑器PoC无失败路 | 能力合同不让步；转新开源候选/最小自研/原生桥接，Phase保持阻断 |
| F7 EditClass fail方向 | 已明确不确定默认 fact_or_uncertain，纯措辞需正向证明 |
| F8 Agent④抽样clean | 应用生成110/110 coverage digest；允许分片但final reducer逐行闭合 |
| F9 page/PDF歧义 | 页面/PDF仍为必需证据之一，但不是唯一通过条件 |
| F10 rollback/兼容写 | shadow绝对只读；additive旧链兼容；pre-switch snapshot和回滚演练 |
| F11 权威/versioning | registry-approved版本；DomainEvent schema/upcaster；material hash排除revision counters；broken Skill显式迁移/终止 |
| F12 同模型风险 | 风险表增加相关盲点，结合digest、合同驱动和P0/P1异身份硬门 |

## Codex 对参与者四个问题的设计回答

1. E1重分类必须用户 decision card；Agent不得批准。
2. E1没有质量 waiver。仍是真实竞品 Protocol 就必须修复或保持阻断；只有
   新证据证明身份/相关性不成立时可由用户重分类。
3. Word automation 技术不预选，§23.4在目标工作站比较合格路径；无通过者
   则定稿门阻断。
4. Editor PoC失败时 D011/D012 不让步，不能用近似画布冒充；进入替代栈/
   原生桥接/最小自研评估，用户未来若要改变产品承诺需另行决策。

## 确定性复核

- v1.2 共 1024 行、代码围栏 2 个且配对、无相邻非空重复行。
- 所有 chair/participant 必改概念均可在规范中检索到。
- `TODO/TBD/待确认` 只出现在最终产物禁止项/零痕迹验收语境。
- D017 未回退：Protocol-only、Protocol Summary属正文、Standalone Synopsis
  仅定稿后导出、CSR未来另建工作流。
- 未修改产品源码、schema、数据库、服务、OCR/翻译/下载或E2E。

## 下一动作

复用 chair provider session `4942b210-ab2d-4c34-aeb4-58cd5c4e76cb` 做一次
delta-only 比较：读取 participant 报告与 v1.2，逐项确认是否闭合，输出唯一
`READY_FOR_USER_SPEC_REVIEW` 或 `REVISE_BEFORE_USER_SPEC_REVIEW`。不得新建
chair会话或扩大到实施。
