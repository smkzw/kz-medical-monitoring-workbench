# 0922V2 独立挑战意见：前端用户路径与公开 DTO 跨层消费

## 0. 本次审阅的证据基础（先划清能证明什么）

本轮**没有使用任何工具**，全部结论来自你内联的冻结源片段与探针观测，属于**对给定摘录的静态阅读 + 探针结果对照**。不是全仓逐行审阅，不是 API/browser 验收，不是医学结论验收。

明确未提供、因此**未读**的关键上下文：`_clue_stance` / `_clue_fingerprint` / `_clue_domain_pair` / `_clue_entities`（命题方向判定实际逻辑）、`selectedSubjectWindow`、`numberText` / `text()` / `clean()`、`DocumentReadinessPanel` 的父组件与 admission 请求层、投影装配层（`projection.aiQueryFindings` / `public_findings_meta` 的产出点）、八轨旅程/时间线组件、Query 草稿组件、`1920` 行之后的 `QueryWorkspaceView` 尾部、专家包 28 项清单。凡涉及这些地方的判断，一律标为**未知**，不替代你核。

下述"确证调用链"的确证程度分两档，逐条标注：
- **[码内确定]**：仅凭给出的代码片段即可推出，不依赖任何外部假设。
- **[码+探针]**：代码路径 + 你给的隔离探针观测互相印证。
- **[待一次核验]**：代码指向明确、但结论依赖一行未读代码或一个未读组件。

---

## 1. 分级发现

分级口径：**P0** = 会让用户读到错误结论/错误身份，属医学安全与来源真伪；**P1** = 用户路径断裂或结论不可信；**P2** = 一致性、可用性、可维护性。

### P0-1｜"零发现"是假的：missing、read_failed、binding 目标缺失全部塌缩成"没有待核实的查询事项"

**确证调用链 [码+探针]**

- 产出侧：`packages/medical_monitoring/api/r7_product/facts_mode_outputs.py:346-348`
  ```python
  read = self._read_ai_findings()
  if read["state"] not in ("completed_with_findings", "completed_no_findings"):
      return []
  ```
  `missing` 与 `read_failed` 都被压成空数组，**状态在场外丢失**（docstring 343 行声称"state与artifact身份经 public_findings_meta 暴露"，但本视图没有消费它）。
- 消费侧：`frontend/src/features/medical-monitoring/MedicalMonitoringWorkspace.jsx:1835`
  `const aiFindings = Array.isArray(projection.aiQueryFindings) ? projection.aiQueryFindings : [];`
  再接 `1841` `{aiFindings.length ? (...) : null}` —— **空数组时整段不渲染，用户看不到任何"这里本该有东西"的提示**。
- 风险清单侧更糟：`1906-1908`
  ```jsx
  {risks.length === 0 ? (
    <div className="monitoring-empty-inline">当前范围内没有待核实的查询事项。</div>
  ) : (...)}
  ```
  `risks.length === 0` 的成因至少有五种：真无发现、工件读失败、binding 项目不符、模型未运行、严重度过滤掉全部条目。**用户看到的是同一句话**。

**探针印证**：`R03-bound-missing` 观测 `{"state":"missing","findings":null,"artifact":"missing.json","error":null}`，`defect_reproduced: true`。binding 明确声明了一个工件、该工件不存在，系统报成普通 `missing` 且 `error` 为空 —— 这是**发布了结果指针却读不到目标**的完整性事件，被降级成"本项目没有双 cohort lane"。`missing` 与"指针指向的目标缺失"必须分开。

**最小修复边界**
1. 产出侧：`public_findings()` 不得把非完成态折叠为 `[]`。要么返回带 `state` 的占位结构，要么把 `read["state"]` 与 `error` 通过已存在的 `public_findings_meta` 一并交给前端（不新建概念，用 docstring 已承诺的那个出口）。
2. 消费侧：`QueryWorkspaceView` 的空态文案必须由**状态**决定，不是由 `length` 决定；`missing`/`read_failed`/`not_run` 各给独立文案，且**不得**使用"没有待核实事项"这类可被读成"本研究干净"的措辞。
3. `_read_ai_findings` 增一个具名状态（如 `binding_target_missing`），与 `missing` 区分。
4. 前端此视图必须消费 meta；若 meta 不存在，W01 补上，不许前端自行推断。

**为什么是 P0**：这是本次审阅范围内最重的医学安全问题。医学监察员读到"当前范围内没有待核实的查询事项"会直接当作"该范围无需核查"，而真实情况可能是工件不可读。它同时命中委托里"零发现与缺口是否真实"与"不得用关闭校验伪造结果身份"两条。

---

### P0-2｜未知/历史快照静默回落到默认快照，纵向时间身份被伪造

**确证调用链 [码+探针]**

`packages/medical_monitoring/projections/facts_publication.py:473-487`
```python
def get_packet(self, project_ref, run_ref=None, snapshot_ref=None, cutoff_ref=None):
    key = (str(project_ref), str(snapshot_ref or "facts-snapshot-001"))
    cached = self._cache.get(key)
    ...
```
`_build` 在 `491` 行同样把空快照归一成 `"facts-snapshot-001"`。

三个问题叠在一起：
1. **`run_ref` 与 `cutoff_ref` 被接收后完全丢弃**，连缓存 key 都不进。调用方请求特定 run / cutoff，拿到的是通用包，**无任何错误或降级标记**。
2. **未知 `snapshot_ref` 不回退失败**，而是落到默认快照。
3. `461-471` 的 `get_authority` 用 `(project_ref, str(identity.snapshot_ref or ""))` 作 key，`get_packet` 用 `(project_ref, snapshot_ref or "facts-snapshot-001")` —— **同一个逻辑包有两个缓存键形态**，`("p1","")` 与 `("p1","facts-snapshot-001")` 各存一份。

**探针印证**：`R11-unbound-snapshot` 观测 `{"snapshot_ref":"nonexistent-history","run_ref":"run-facts-001"}`，`defect_reproduced: true` —— 请求一个**不存在的历史快照**，系统照常返回包。

**最小修复边界**
- 快照解析集中到一处：`snapshot_ref` 不在可用集合内 → **fail-closed**，返回具名错误，绝不回落默认。
- `run_ref` / `cutoff_ref` 要么进 key 并被真正使用，要么从签名中删除（保留一个被静默忽略的参数比删掉更危险）。
- 两个入口共用同一个 key 构造函数，去掉 `""` 与 `"facts-snapshot-001"` 的双形态。
- `self._cache` 增加发布版本参与的失效条件；否则**重新导入/重新发布后，进程内继续返回旧事实且 `_load_domains` 的 sha256 校验永远不会再跑到**（`466-471`、`482-486` 都是先查缓存直接 return）。

**为什么是 P0**：它直接破坏"受试者/事件/时间窗/来源身份贯穿各视图"和"保留纵向时间"。对医学监察员而言，在历史时点标签下看到当前事实，比读不到数据严重得多。这一条落在 W07"五项目全量/恢复"的验收路径上，不修就会"验收通过但读的是错快照"。

---

### P0-3｜"原始记录"是模板字符串，还自称"已校验"；来源 content hash 与内容无关

**确证调用链 [码内确定]**

`packages/medical_monitoring/projections/facts_publication.py:528-541`
```python
def _locator(table: str, index: int) -> R5SourceRecord:
    ref = f"loc-{table}-{index:06d}"
    record = R5SourceRecord(
        ...
        source_revision_content_hash=content_hash({"table": table})[:64].replace("-", "0"),
        canonical_location=f"{table}!row{index + 1}",
        excerpt=f"{table} 第{index + 1}行原始数据（已校验）",
    )
```

- `excerpt` **不是原始行内容**，是格式串拼出来的占位文本，且硬编码"（已校验）"三个字。用户点"原记录"看到的是这句话。
- `source_revision_content_hash` 由 `{"table": table}` 派生 —— **同一张表所有行共用一个与行内容无关的哈希**。字段名声明自己是内容指纹，实际不是。
- 讽刺的是，真实指纹就在同一文件 `444` 行被算出来了：`hashlib.sha256(raw).hexdigest() != entry["sha256"]`，然后被丢掉。

**最小修复边界**
- `excerpt` 从**已在内存里的行 payload**（`domains[table][index]`）截取真实内容；`（已校验）`只有在其确经过校验时才保留，否则删除。
- `source_revision_content_hash` 传 `manifest entry["sha256"]`（同一次加载里已有的值），不要新算。
- 若某视图根本不展示 `excerpt`，必须确认它不展示 —— 一个"看起来像原始记录"的假字符串在来源面板里出现即构成伪证。

**为什么是 P0**：命中边界"真实来源、版本、审计"与"不自动写成已医学核对"。这是四条 P0 里唯一一条**修复成本最低、收益最直接**的（改两行、复用已有 sha256）。

---

### P0-4｜身份校验的失败策略在库内不一致：entry 级 fail-closed，指针/容器级 fail-open

**确证调用链 [码+探针]**

同一个文件里两种相反策略并存：

| 校验对象 | 失败行为 | 行号 |
|---|---|---|
| facts 单文件 sha256 不符 | **raise `FactsPublicationError`**（fail-closed） | `facts_publication.py:444-448` |
| facts manifest 自身损坏/schema 不符 | **静默重建并原子写回**（fail-open） | `facts_publication.py:425-434` |
| findings binding 项目不符 | fail-closed（`read_failed`） | `facts_mode_outputs.py:533-540` |
| findings binding 同名内容替换 | fail-closed（`binding_digest_mismatch`） | `facts_mode_outputs.py:566-570` |
| findings binding **本身畸形**（路径/摘要长度非法） | **返回 `{}` → 落到 legacy 固定名**（fail-open） | `facts_mode_outputs.py:499-508` → `528-545` |

两处 fail-open 的具体后果：

1. **畸形 binding 会读到 legacy 工件**。`_read_findings_binding` 返回 `{}` 后，`_read_ai_findings` 走 `542-545` 的 `else` 分支读 `_AI_FINDINGS_ARTIFACT`，只要该文件自申报哈希匹配就返回 `completed_with_findings`。**指针被破坏 = 退回读旧工件**，正好违反 docstring 521 行自己写的"不glob+mtime取最新——旧run不得读到新工件"。探针 `R03-bad-binding` 观测 `{"state":"completed_with_findings","artifact":"aemh-findings-facts-snapshot-001.dualvlm-full1.json"}`，`defect_reproduced: true`。
2. **损坏的 facts manifest 被静默重建**。`432-434` 走 `_build_facts_manifest(artifacts)` —— 重新打开目录扫描，用"64 位十六进制命名 + 单表结构"启发式 + **mtime 最新者胜**，其余标记 `superseded`。等于把 docstring 415 行"不扫描碰巧同名的JSON"这条防线在 manifest 被破坏时整个撤销，且 `superseded` 会让某张表的旧版本**静默退出加载集合**，临床事实集被替换而无任何错误。探针 `R11-corrupt-manifest` 观测 `tables_after_corrupt_manifest: ["AE","LB","MH"]`，`defect_reproduced: true`。

顺带一处同类漏洞：`facts_mode_outputs.py:559-566`，legacy 工件若**没有** `content_sha256` 字段，`declared` 为空 → 自申报校验跳过；legacy 路径 `expected_digest` 也为空 → **两个校验都被跳过，身份完全未验证即接受**。

**最小修复边界（一条规则、四处应用，不是四个补丁）**
> 身份/完整性校验失败一律 fail-closed 到具名状态；**绝不回退到另一个工件、另一个快照、或目录扫描**。`missing`（不存在）与 `read_failed`/`inconsistent`（存在但不可信）在任何 DTO 中必须可区分。

四处：`facts_mode_outputs.py:499-508`（畸形 binding → 具名状态，不落 legacy）、`559-566`（无自申报哈希的 legacy 工件 → 拒绝或显式标 `unverified`）、`facts_publication.py:425-434`（manifest 损坏 → 具名错误，重建必须是**显式动作**而非隐式）、`facts_publication.py:473-487`（未知快照 → 具名错误）。

**为什么是 P0**：这不是四个孤立 bug，是一个策略缺陷。若计划按"逐发现修"处理，必然四处各修一次且仍会漏掉新加的第五处；按一条策略修则一次收敛。

---

### P1-1｜"定位关联事件"是死代码：公开 DTO 不含 `anchor_event_refs`，`event_ref` 恒为空串

**确证调用链 [码+探针]**

- 产出侧 `facts_mode_outputs.py:374-390` 的 `rows.append({...})` 共 **13 个键**，逐字为：`finding_id, display_seq, kind, subject_label, subject_ref, site_ref, spine_ref, state, state_reason_zh, title, text, evidence_ids, claims`。**没有 `anchor_event_refs`**。
- 消费侧 `MedicalMonitoringWorkspace.jsx:1893-1895`
  ```jsx
  {item.anchor_event_refs?.length && onFindingSelect ? (
    <button ... onClick={() => onFindingSelect?.(item)}>定位关联事件</button>
  ) : null}
  ```
  条件恒假 → **按钮永不渲染**，`onFindingSelect` 在此视图不可达。
- 下游 `MedicalMonitoringProductLoop.jsx:1166-1175`
  ```js
  const eventRef = Array.isArray(finding.anchor_event_refs) && finding.anchor_event_refs.length
    ? finding.anchor_event_refs[0] : "";
  navigate("journey", { ... event_ref: eventRef, ... });
  ```
  `eventRef` 恒为 `""` → 即使被调用，也只进入旅程、**不聚焦任何事件**。

**探针印证**：`R05-public-dto` 观测的键集合（字母序 13 项）与代码 `374-390` 完全一致，仍无 `anchor_event_refs`。

**后果比"没实现"更差**：`1156-1157` 的注释写"不默认选第一条AE"，而实际行为是**完全不选**。医学监察员从线索卡片进入长时线后需要手工找事件，这正是"可直接读风险、纵向时间可读"要避免的。

**残余不确定（[待一次核验]）**：若投影装配层（未提供）对 `projection.aiQueryFindings` 做了补充，注入 `anchor_event_refs`，本结论不成立。一次 `rg "anchor_event_refs"` + `rg "aiQueryFindings"` 即可定案。**在定案前不得把该按钮记为"已实现"。**

**最小修复边界**
- 若工件里确实有事件锚点：在 `public_findings()` 补 `anchor_event_refs`，**服务端校验每个 ref 能在 projection 中解析**，不可由前端拼。已存在的 `subject_ref/site_ref/spine_ref` 解析模式（`369-382`）就是现成的权威写法，照它做。
- 若工件里没有锚点：**删掉按钮和 `selectResultFinding` 的锚点分支**，不要留一个看着能用、点了没反应的入口。文档字符串 340-343 声称"保留…服务端可解析的事件/来源锚点"，与实际返回不一致，二者必须对齐一个。

---

### P1-2｜来源与证据没有点击目标：`onSource` 声明未用，`evidence_ids` 只显示条数

**确证调用链 [码内确定]**

- `QueryWorkspaceView` 签名 `MedicalMonitoringWorkspace.jsx:1828` 接收 `onSource`、`onBack`，但在 `1829-1920` 摘录范围内**无任何调用点**。`onSource` 未使用即"来源下钻入口缺失"的直接代码证据。
- `1877-1879`
  ```jsx
  {claim.evidence_ids?.length ? (
    <span className="monitoring-claim-evidence">（证据 {claim.evidence_ids.length} 条）</span>
  ) : null}
  ```
  只渲染**数量**，`evidence_ids` 的具体内容与跳转没有任何可点目标。

**残余不确定 [待一次核验]**：`1920` 行之后可能使用 `onSource`/`onBack`。需确认摘录截断处之后的内容。

**最小修复边界**：`evidence_ids` 在 DTO 里已有（`facts_mode_outputs.py:387`），这是**已有数据权威**，只需在卡片内把每个证据 id 渲染成可点项并接到已有 `onSource`；不新增证据通道、不新建来源组件。若 `onSource` 的真实用途与证据不同，先定案再改，避免造第二个来源入口。

---

### P1-3｜角色"缺失"选项在 `candidate_id` 为 `null`/`undefined` 时不可选、不可提交

**确证调用链 [码内确定]**

`MedicalMonitoringAdmissionWizard.jsx:69-72`
```js
const allAnswered = userChoices.every(
  (choice) => typeof choices[choice.role] === "string",
);
```
`119-123`
```jsx
checked={(choices[choice.role] || "") === option.candidate_id}
onChange={() => setChoices((current) => ({ ...current, [choice.role]: option.candidate_id }))}
```
`115` 的 `key={option.candidate_id || "__missing__"}` 说明作者预期"缺失选项"的 `candidate_id` 是 falsy。三种取值下的行为：

| `option.candidate_id` | radio 能否显示为已选 | `allAnswered` | 能否提交"该角色缺失" |
|---|---|---|---|
| `""` | 能（`"" === ""`） | `true` | 能 |
| `null` | **不能**（`"" === null` 为假） | **恒 false** | **否，按钮永久 disabled** |
| `undefined` | **不能** | **恒 false** | **否** |

`133-143` 的裁决按钮 `disabled={!allAnswered || processing}` 因此在该场景下**永久禁用**，用户无法表达"这份文件不存在"。

**为什么是 P1 而不是 P2**：结合边界第 4 行能力分层——"入排、洗脱/禁药、访视窗、AESI 等依赖方案/IB 的判断……不能以用户点击'无此文件'补足"。当前设计里"该角色缺失"就是那个"点击"。若它同时不可提交（本缺陷）或可提交即被当作依赖满足（设计缺陷），两种失效方向都会让 row-4 判断在缺依赖时被放行。**必须一次把两件事一起定**：缺失选择可提交 + 缺失只写入"依赖未满足"状态，**不得**被任何视图当作已满足。

**最小修复边界**
- 用显式哨兵值（如 `"__missing__"`）作为缺失选项的 `candidate_id`，使 `typeof === "string"` 成立、`checked` 可比较；提交时按同一哨兵回传。
- 校验层必须区分"选择了某个文件"与"声明该角色缺失"，后者进入依赖未满足状态。
- 补一条组件级断言：三种 `candidate_id` 形态下"缺失"选项均可选可提交。

---

### P1-4｜同一面板内数字与空态自相矛盾：`currentRisks` 过滤口径 ≠ `risk_count`

**确证调用链 [码内确定]**

`MedicalMonitoringWorkspace.jsx:1831-1834`
```js
const risks = (projection.currentRisks || [])
  .filter((risk) => !risk.aggregate && ["critical","high","medium"].includes(risk.severity))
  .sort(...);
const totalCount = projection.aggregation?.risk_count ?? risks.length;
```
`1904` 标题 `请核实事项（{risks.length} 项待核对 · 全量锚点 {numberText(totalCount)}）`，`1906-1908` 空态文案见 P0-1。

当 `aggregation.risk_count` 非 0、而 `currentRisks` 全部为 `low` 或 `aggregate` 时，面板会同时渲染：
> 请核实事项（0 项待核对 · 全量锚点 37）
> 当前范围内没有待核实的查询事项。

这是**同一屏内的直接矛盾**，用户无法解释那 37 去哪了。

两个独立问题：
- `risk_count` 的口径未知：它可能是"风险实例数"，而标签写"全量锚点"。术语与数字语义不一致 [待一次核验：产出 `aggregation.risk_count` 的代码]。
- `aggregate` 风险被整类过滤。委托的 W05 明确含"研究中心流向"，聚合风险正是中心级线索；它们被排除后**没有任何可见入口**。

**最小修复边界**：W05 的 DTO/UI 对照表里必须写清 `currentRisks` 的过滤规则、`risk_count` 的确切口径、以及被过滤掉的两类（`low`、`aggregate`）各自的可见入口。"折叠/分页/虚拟化可以，API 截掉原始事实不行"——当前是 UI 静默丢弃，需要至少一个"被过滤 N 条，查看"的诚实出口。

---

### P1-5｜方案画像：硬编码 8 条适应症表，且文档字符串声称"从不硬编码"；`unknown_visible` 被罐装风险方向击穿

**确证调用链 [码+探针]**

- `packages/medical_monitoring/analysis/protocol_profile.py:1-8` 文档字符串：
  > "The profile is project-agnostic — everything is derived from document text with pattern rules, **never from a hard-coded drug or protocol**."
- 同文件 `25-34`：
  ```python
  _INDICATION_HINTS = (
      ("过敏性鼻炎", "过敏性鼻炎", "抗组胺/鼻用糖皮质激素相关嗜睡、鼻部刺激、局部感染风险"),
      ("哮喘", "支气管哮喘", "支气管痉挛、口咽念珠菌感染、声嘶风险（吸入糖皮质激素）"),
      ... 共 8 条
  )
  ```
  这是一张**写死的适应症→风险方向对照表**，而 `risk_direction_zh` 直接写入 profile（`121-126`）。文档字符串与实际实现相反。
- `55` `"unknown_visible": not (self.ctcae_version or self.risk_direction_zh)` —— 只要有**任一**字段非空，未知就被声明为不可见。

**探针印证**：`R10-keyword-risk` 观测
```json
{"ctcae_version": "", "meddra_version": "", "indication_zh": "过敏性鼻炎",
 "risk_direction_zh": "抗组胺/鼻用糖皮质激素相关嗜睡、鼻部刺激、局部感染风险",
 "anchors": [{"quote": "适应症：过敏性鼻炎","where":"candidate.txt"}],
 "unknown_visible": false}
```
CTCAE 版本未知、MedDRA 未知，**`unknown_visible` 却是 false** —— 一句罐装的 `risk_direction_zh` 把两个真实的未知一起掩盖了。上游若按此判断"无重要缺口"，用户会以为画像完整。

**最小修复边界**
- 删除 `_INDICATION_HINTS` 罐装风险方向（计划 W03 已含此项，确认执行）。
- `unknown_visible` 改为**逐字段**语义，例如 `unknown_fields: ["ctcae_version","meddra_version"]`，而不是一个由任一非空字段决定的布尔。
- 文档字符串必须改到与实现一致；否则下一个读者会继续相信"never hard-coded"。

---

### P1-6｜权威版本由"出现次数 + 文件后缀"选举，而不是由用户已确认的文件角色决定

**确证调用链 [码+探针]**

`protocol_profile.py:103` `for path in sorted(files_dir.glob("*")):` —— 扫描目录里的**每一个** docx/pdf/txt，包含 IB、背景资料、任何无关文件。`112-113` 用后缀给权重（docx 权重 3，其余 1）。`128-138` `_elect`：
```python
def _elect(candidates):
    ...
    return max(counts, key=lambda v: (counts[v], float(v) ...))
```
"出现最多的版本胜出；平票取数值更高者"。

**探针印证**：`R10-version-vote` 观测 `ctcae_version: "5.0"`，anchors 来自 `background.txt`（2 次）与 `candidate.txt`（1 次）—— **背景资料靠重复次数压过方案文件**，因为两者后缀都是 `.txt`，权重不区分。

两个更深的点：
- 权重设计（112-113 的注释自己说"方案是项目标准版本的权威来源"）与用户已经在准入向导里确认过的**文件角色**（`MedicalMonitoringAdmissionWizard.jsx:110` "请确认每个文件角色对应的文件（医学判断以您为准）"）完全脱节。系统先让用户确认角色，然后在方案画像里改用扫描+投票。**这是 W02→W03 的依赖断裂。**
- "平票取数值更高者"是系统替用户做了版本判断。文档冲突属于边界要求"可见"的类别，静默取高版本不是。

**最小修复边界**：`build_protocol_profile` 的输入从 `files_dir` 改为**角色已确认的文档集合及其内容哈希**；未确认角色时 fail-closed 到 `unknown`，不投票。冲突（多文档给出不同版本）**必须可见**，不得静默择高。

---

### P1-7｜命题方向门在反例探针下失效：`accepted = 1`

**确证调用链 [码+探针]**

`packages/medical_monitoring/analysis/ae_mh_cross_analysis.py:424-438` 明确写了方向否决：
```python
primary_stance = _clue_stance(primary)
verifier_stance = _clue_stance(verifier)
if primary_stance != "positive" or verifier_stance != "positive":
    return False
```

**探针印证**：`R04-opposite-predicate` 观测 `{"accepted": 1, "escalated": 0, "coverage_gap": 0, "unverifiable_gap": 0}`，`defect_reproduced: true`。用例名即"命题相反"，结果却被判为一致。**代码意图存在，防护在该用例下无效。**

**残余不确定 [待一次核验]**：`_clue_stance` 未提供。最可能的失效点是它的负向标记词表覆盖不到被测表述（返回了 `"positive"`）。**修复必须从钉死 `_clue_stance` 开始**，不能靠在 424-438 再加条件。

**最小修复边界**：为 `_clue_stance` 建一组**双向**断言用例（存在/NOT、有/无、阳性/阴性、未见/阴性），断言"命题相反 ⇒ 不得 accepted"；同时补一组"双方同为阴性 ⇒ 当前必然 escalated"的基线，把该行为显式记录为已知语义（见 P2-4 相邻讨论）。

**顺带一条设计问题（交给 W04 定，不是 bug）**：`432-438` 的分级冲突检测要求**双方都有**分级词才比对。一方写"3级"、另一方完全没提分级时，检查被跳过，两者仍可 accepted。对医学比较而言，"一边说 3 级、一边沉默"正是需要标出的情形。这需要产品判断，应在 W04 的验收条件里写成明确规则（例如：单侧有分级 ⇒ 至少 escalated），不要留给实现者现场决定。

---

### P1-8｜四行能力分层没有进入计划；row-3 的启用范围与 row-4 的依赖门都无人拥有

边界文档给了明确的能力分层表与三条硬约束：

| 行 | 约束 | 计划中的归属 |
|---|---|---|
| 1 原始Listing/文件/台账查看 | 未识别语义单列，不冒充已确认映射 | **未见于 W00-W07** |
| 2 已确认字段的明细与时间线 | 局部可用；缺字段的轨道明确标缺口 | **未见于 W00-W07** |
| 3 不依赖方案的基础医学线索分析 | **"需要单独确认启用范围，不能以本包默认授权"** | W03/W04 实际会构建并启用 → **冲突** |
| 4 依赖方案/IB 的判断 | 依赖未满足时不可评估；**不能以用户点击"无此文件"补足** | **未见于 W00-W07** |

这是**计划的最大遗漏**。W03"语义映射/工具覆盖"、W04"零发现/全域覆盖"按现文写法会直接把 row-3 跑起来，而边界明确说"不能以本包默认授权"。同时 P1-3 的"角色缺失"选项正是 row-4 被禁止的那个补足动作。

**最小修复边界**
- W03/W04 增一行显式约束：本轮**不默认启用** row-3；启用需单独确认，且启用后必须独立标识分析范围、**不声称"全方案监查完成"**。
- row-4 需要一个"依赖未满足"状态，由"角色=缺失"或"版本已过期"写入，并让所有依赖方案的判断在 UI 上呈现为**不可评估**（不是"无发现"）。与 P0-1 合流：不可评估 ≠ 零发现。
- row-1/row-2 是"现有渐进可用原则的落实"，需要至少一个视图明确标注"未识别语义单列"与"轨道缺口"，否则这两行只是文档承诺。

---

### P2 级（一致性/可用性/可维护性）

| # | 发现 | 调用链 | 最小修复边界 |
|---|---|---|---|
| P2-1 | `processing` 用**白名单枚举**判断，服务端新增任何阶段都会让按钮在操作进行中变可点 | `MedicalMonitoringAdmissionWizard.jsx:65-68` 列出 5 个阶段；`98`/`136` 用它 disable | 反转为"默认处理中，只在已知空闲/终态集合内放行"。计划 W02/W04 明确要加阶段与回执，**不改这里等于计划自己引入回归** |
| P2-2 | 文档角色状态列表不显示文件名、无打开入口；同一屏的角色选项却显示文件名 | `MedicalMonitoringAdmissionWizard.jsx:79-85`（仅 `label`/`status_text`） vs `127`（`option.filename`） | 状态列表补文件名与"打开文件"入口，复用已有文件视图 |
| P2-3 | 内容核对确认的 DTO 缺"预期值/实际提取值/证据/影响范围"；按钮文案"我已核对，确认沿用"暗示已核对正文 | `86-105` 仅渲染 `role`/`content_status`/`use_status`；`100-102` 按钮文案 | 边界要求的是"元数据/上下文告警"展示四要素；W02 需补 DTO 字段，并把文案降级为"已知晓该提示，确认沿用当前版本"；同时断言落盘记录**不会**被渲染成"已医学核对" |
| P2-4 | `state` 无白名单：未知/拼错的 state 落到 `"待补核"` 分支且**不计入 `aiGaps`**，四个数字对不上总数 | `MedicalMonitoringWorkspace.jsx:1836-1838` 只统计四类；`1852` 其余一律 `"待补核"`；产出侧 `facts_mode_outputs.py:362` 原样透传 | 服务端 `state` 白名单化，未知态 ⇒ 显式可见的契约违规态；前端四项统计必须与总条数自洽 |
| P2-5 | 同一组件内两套命名：`currentRisks` 项是 camelCase（`subjectRef`/`evidenceSummary`/`riskInstanceRef`），`aiQueryFindings` 项是 snake_case（`subject_ref`/`evidence_ids`） | `1831-1834` vs `1836`；`1911`/`1914`/`1919` | 在边界上统一一种命名并**只做一次适配**。禁止在各视图各写一层翻译（那就是"第二套框架"的起点） |
| P2-6 | 缓存无失效条件；双 key 形态；缓存命中后 `_load_domains` 的 sha256 校验不再执行 | `facts_publication.py:461-487` | 见 P0-2；另外缓存的是整表 domains，需确认内存上限（W07"恢复启动性能"相关） |
| P2-7 | 面向"中文原生、不懂AI电脑"的医学监察员，界面用"双cohort""AI 跨表线索"等工程术语 | `MedicalMonitoringWorkspace.jsx:1843-1844` | W05 的"中文工作清单"应包含一次术语审校（如"双cohort一致"→"两组独立分析一致"）。`1844` 的免责说明方向正确，保留 |
| P2-8 | 同一文件被解析两次 | `protocol_profile.py:63` 与 `66` 各自 `docx.Document(str(path))`；且第二次在 try 内，失败则表格静默丢失 | 一次解析复用；表格失败应记入未知而非静默 |

**跨范围提示（后端持久化，交主线程，我不重复探针）**：`R06-invalid-persisted` 的观测**自相矛盾** —— `"rejected": true` 同时 `persisted` 非空并含 `{"role":"protocol","candidate_id":"invalid",...}`。这有两种可能：探针读取时序在判定之前，或校验是 fail-open（先写后判/判失败仍写）。**在时序定案前，这条不能计入"已修复"证据**；若确为 fail-open，它属于 P0-4 同一条策略缺陷（身份校验失败不得落盘）。

---

## 2. 计划修订建议

对 W00-W07 与三条执行约束（整组一次回归、根因批修、前端 fixture 并行）的审议。**总体判断：批量策略方向正确，可以保留；问题在依赖排序与两处过度设计。**

### 2.1 遗漏

1. **W01 缺少"诚实性契约"这一条主线**。P0-1/P0-2/P0-3/P0-4 是同一个东西：身份与完整性校验失败时的统一策略，加上"missing 与 read_failed 在任何 DTO 中可区分"。现在它们散落在四个包（W01 解析、W04 零发现、W05 来源、W07 恢复），逐包修会漏第五处。**建议把 W01 改名为"身份与真实性契约"，并授予它唯一的跨包阻塞权。** 这是最小改动、最大收敛。
2. **W05 看起来是纯前端包，但它的三个点击目标里两个没有产出方**：`anchor_event_refs`（P1-1）与来源/证据下钻（P1-2、P0-3 的 `excerpt`/`content_hash`）。按现文写法 W05 会被前端"等 DTO 稳定"卡住，与计划声称的"DTO 稳定后并行 fixture 开发"自相矛盾。**修正：把"DTO 产出方字段补齐"放进 W01**，W05 才能真正并行。
3. **W07 的多项目/恢复验收依赖 P0-2 与 P2-6**。不修快照 fail-closed 与缓存失效，W07 会在"读错快照"的状态下验收通过。**修正：W01 吸收快照解析与缓存失效；W07 只做验收。**
4. **W06 三种兼容增量模式依赖 P0-4 的 manifest 策略**。manifest 静默重建 + `superseded` 静默剔除，会让"增量"在数据层面不可解释。**修正：同样归 W01。**
5. **边界第 1 条（风险列表是否替换默认首页）无人拥有**：边界要求"清晰切换、记忆最近视图、保留研究概览"，且明确"不是用户已确认事项"。W05 把工作清单推到显著位置后这个问题必然回归。**修正：W05 或 W06 显式认领，实现为切换 + 记忆最近视图 + 保留研究概览，不新建导航框架。**
6. **边界第 3 条（不按开发者回忆撤换模型/索要新密钥）** 未在计划中出现。需要一个显式约束行，防止 W03/W04 实施时把"路由恢复"当成前置条件而阻塞 UI/状态修复。

### 2.2 依赖（按真实关键路径重排）

现计划的表面顺序是 W01→W07，实际关键路径**不是** W03/W04，而是：

```
W01 身份与真实性契约（含 DTO 产出方字段补齐）
   ├─→ W02 角色/确认/异步隔离（依赖角色状态模型，产出"依赖已满足"信号）
   │        └─→ W03 删除罐装画像 + 角色驱动版本（依赖 W02 的角色确认输出）
   │                 └─→ W04 命题核验（依赖 W03 的画像与知识来源）
   └─→ W05 前端路径（DTO 稳定后可并行 fixture）
            └─→ W06 增量/草稿
                     └─→ W07 尺度与恢复验收
```

**W02→W03 那条依赖是最容易被忽略、后果最重的一条**：P1-6 的根因就是方案画像没接角色确认。如果 W03 先做而 W02 的哨兵值/依赖状态未定型，版本选举会继续按后缀+票数决定权威版本。

### 2.3 过度设计风险

1. **W03 体量过大，会阻塞 W04/W05**。"删除疾病风险/版本投票画像" + "正式来源双模型知识"是两件性质不同的事：前者是**删代码 + 让 unknown 可见**（小、高价值、立刻解除 P1-5 的误导）；后者是**新增知识通道**（大、依赖外部来源、需要单独的来源权威设计）。**建议拆开**：删除与 `unknown_visible` 逐字段化立刻做（约 3 行核心改动 + 删一张表），双模型知识后置，不等它。这样 `unknown_visible` 从"假已知"变真，是 W04 谈"零发现/全域覆盖"的前提。
2. **不要把 P0-4 做成"校验框架"**。它需要的是四处就地 fail-closed + 一条写下来的策略，不需要抽象校验层、不需要通用的 artifact 解析器。这符合"不新增通用引擎"。
3. **不要新增测试框架**。见第 4 节的探针登记表方案：现有 9 个探针已经是"合成 fixture + 无 API/browser/provider"的正确形态，直接当验收脊柱用，比新造一套更省、更贴"复用现有数据权威"。

### 2.4 对"失败按根因批修"的具体化

"根因批修"现在是一条原则，落地时会退化成"看到什么修什么"。建议加一条**判定规则**：一个发现只有在能被映射到下面某一类时才进入批修队列——

| 根因类 | 覆盖发现 | 一次修完的判据 |
|---|---|---|
| R-A 身份/完整性校验失败策略 | P0-1(部分)、P0-2、P0-4、R06 待定 | 四处 fail-closed；`missing` 与 `read_failed` 在 DTO 可区分 |
| R-B 真实来源与出处 | P0-3、P1-2 | 展示的是真实行内容与真实 sha256 |
| R-C 生产方与消费方字段契约 | P1-1、P1-4、P2-4、P2-5 | 每条 UI 可点目标都有生产方字段；命名统一一次 |
| R-D 状态门与依赖门 | P1-3、P1-8、P2-1 | 缺失/未满足/未运行/零发现在任何视图下互不冒充 |
| R-E 语义判定有效性 | P1-7、P1-5、P1-6 | 每条门有双向反例断言；画像不投放罐装结论 |

不相属的发现不要塞进同一批，否则"批修"变成"顺手改"，这正是当前缺陷（死按钮、假零发现）活下来的方式。

---

## 3. 合并为三个用户工作切片

按"用户能感知到什么"合并，而不是按代码模块合并。

### 切片 A — **看得见真假**（W00 + W01 + W02）
用户可见结果：能区分"没有发现"与"没读到/没运行"；点开的"原始记录"是真记录；"该角色缺失"是真的缺失且会挡住依赖它的判断；技术/身份错误永远不会变成一个待点确认按钮。

范围：R-A 全部（四处 fail-closed、快照解析、缓存失效、manifest 与 binding 策略）、R-B（`excerpt` 与真实 sha256）、P1-3 哨兵值、P2-1 阶段门反转、P2-3 确认 DTO 四要素、P1-8 的四行能力分层状态化。

**这是唯一有跨包阻塞权的切片**，也是"整组一次回归"能真正生效的前提。

### 切片 B — **走得通**（W03 删除部分 + W04 + W05 + W06）
用户可见结果：从导入→角色确认→结果→风险/AI 线索清单→受试者医学旅程→时间/八轨→原记录→返回→Query 草稿，全程每个可点元素都真的有目标；数字与列表口径自洽；聚合风险有入口；术语是中文医学语言。

范围：R-C 全部（含 P1-1 的锚点补齐或删按钮、P1-4 的口径对齐、P2-5 命名统一）、P1-2 证据下钻、P0-1 的空态文案状态化、P2-2、P2-4、P2-7、边界第 1 条的首页/记忆视图。

依赖：切片的 DTO 产出方字段已在 A 落地，故 B 可与真实模型解耦、用 fixture 推进（符合原计划意图）。

### 切片 C — **跑得动、退得回**（W03 新增部分 + W06 增量 + W07）
用户可见结果：换项目/换快照不串数据；重新导入立刻生效；长任务可取消可恢复；五项目全量可用。

范围：P1-5 的双模型知识通道、P1-6 的角色驱动版本（含冲突可见）、P1-7 的方向门（依赖 `_clue_stance` 钉死）、P2-6、P2-8、W07 全量验收。

**注意**：C 里的 P1-6/P1-7 并不真的等到最后——它们的**前提条件**在 A（角色状态）和 B（画像输入改变）里。C 只放"新增能力"与"尺度验收"。

---

## 4. 批量验收策略（细化，不是照抄）

原计划三条约束（整组改完一次相关回归；只有共享合同变化跑相邻；最终一轮全回归 + ego；禁止一改一测/反复全测/反复真实全量）**方向正确，保留**。补四点让它可执行：

1. **每包必须能用合成 fixture 在零 HTTP/零模型下执行**。否则"整组一次回归"会退化成"末尾一次手工冒烟"——当前这批缺陷正是这样活下来的。你的隔离探针已经证明这套形态可行（`scope: "synthetic temporary fixtures; no API/browser/provider calls"`），照它做。
2. **把已有 9 个探针变成验收脊柱**，而不是另写测试：
   - 建立探针登记表：`探针 id → 对应发现 → 当前 defect_reproduced → 归属切片 → 翻转判据`。
   - 一个发现的判据是 **`defect_reproduced` 翻转为 `false`**，不是"代码改了"。
   - 新增缺陷 ⇒ 新增探针；不允许"口头确认已修"。
   - 复用现有资产，不新建框架、不新建第二套调度。
   - 已知的探针证据问题（R06 自相矛盾）必须先定时序再计入。
3. **相邻回归的触发条件写成合同清单，不写成"感觉相关"**：
   - A→B 相邻触发：公开 DTO 的字段集合或命名变更（`public_findings()`、`aiQueryFindings`、`currentRisks`、`content_confirmations`）。
   - B→C 相邻触发：快照/缓存/发布指针语义变更。
   - 只有清单命中才跑相邻；未命中的一律只跑本包探针。
4. **明确列出禁止动作**（写进计划正文，避免执行时"为了稳妥"扩大）：
   - 不逐编辑运行；不每包全量；不重复真实全量；不为每个发现新写测试文件；**真实全量只在 C/W07 一次**；不在包内重跑已翻绿的探针。
5. **端到端只做一次，且必须包含五条用户路径的**走查：导入→确认→结果→线索/风险→旅程/时间/原记录→返回→Query 草稿，加上换项目与换快照各一次、重新导入一次。ego 放在这一轮之后，不做中途 ego。

---

## 5. 已修片段 / 仍开项 / 未知

### 已有代码证据、判定为**本轮已落地**（仍属静态判断）

| 项 | 证据 |
|---|---|
| subject 身份由服务端投影解析 `subject_ref`，不再按 `subject-${label}` 猜 ID | `MedicalMonitoringWorkspace.jsx:1847-1851`、`MedicalMonitoringProductLoop.jsx:1160-1164`、产出侧 `facts_mode_outputs.py:369-382`；探针 R05 含 `subject_ref/site_ref/spine_ref` |
| `finding_id` 稳定贯穿 + `display_seq` 单独承载显示序号 | `facts_mode_outputs.py:375-376`；前端 `1857` 以 `finding_id` 为 key |
| `coverage_gap` 不依赖标题存活 | `facts_mode_outputs.py:364-367`；前端 `1887-1888` 渲染"覆盖说明" |
| 声明式 claims 渲染 + 证据条数 | `facts_mode_outputs.py:393` `_finding_claims`；前端 `1871-1886` |
| 加载态可访问（`role="status"`） | `MedicalMonitoringAdmissionWizard.jsx:61-63` |
| 裁决前必须全部作答 | `69-72` + `136` |
| facts 单文件 sha256 fail-closed | `facts_publication.py:444-448` |
| binding 项目不符 / 同名内容替换 fail-closed | `facts_mode_outputs.py:533-540`、`566-570` |
| binding 路径穿越防护 | `facts_mode_outputs.py:499-506` |
| 分级冲突比对 + 命题方向否决的**代码意图** | `ae_mh_cross_analysis.py:424-438`、`432-438`、`442-454` |
| 前端对模型一致性的免责表述正确 | `MedicalMonitoringWorkspace.jsx:1844`（"模型一致性是核验状态而非医学结论"） |

### 仍开项（按上面分级）

P0：P0-1 零发现塌缩、P0-2 未知快照回落、P0-3 假 excerpt/伪 content hash、P0-4 指针与容器级 fail-open（含 legacy 无自申报哈希即接受）、R06 探针自相矛盾待定时序。
P1：P1-1 定位关联事件死代码、P1-2 来源/证据无点击目标、P1-3 角色缺失不可提交、P1-4 数字与空态自相矛盾、P1-5 罐装画像 + `unknown_visible` 被击穿、P1-6 版本选举脱离角色、P1-7 方向门在反例下失效、P1-8 四行能力分层未入计划。
P2：P2-1 至 P2-8 共 8 项。

### 未知（必须由主线程或一次定案核验，我不给结论）

1. `projection.aiQueryFindings` 的装配层是否注入 `anchor_event_refs`（一次 `rg` 定案；未定案前 P1-1 不得记为"已实现"）。
2. `_clue_stance` 的负向标记词表（P1-7 修复起点）。
3. `selectedSubjectWindow` 的窗口计算逻辑：若它把窗口钳到默认值，P1-1 修好锚点后**聚焦仍可能落在窗口外**。W05 需一条断言："锚点事件必须落在传入窗口内"。
4. `1920` 行之后 `QueryWorkspaceView` 尾部是否使用 `onSource`/`onBack`，以及是否已有 Query 草稿入口。
5. 八轨旅程/时间线组件是否

（承接上一条被截断的报告，续 **第 5 节"未知"** 余项与结论）

### 未知（续）

5. **窗口钳制**：`selectedSubjectWindow` 未提供。若它把窗口钳到默认值，P1-1 补齐锚点后聚焦仍可能落在窗口外。W05 需一条断言：锚点事件必须落在传入 `window_start/window_end` 之内。
6. **准入请求层与陈旧选择**：`DocumentReadinessPanel` 的父组件未提供。三项决定 P1-3 相邻风险是否存在——(a) 是否有请求令牌/取消，使被取代的响应不生效；(b) `state.payload` 变化时 `choices`（`MedicalMonitoringAdmissionWizard.jsx:60`）是否重置；(c) 父组件是否按 payload 版本给面板加 `key`。若三者皆无，则重新分析后**旧的 role→candidate 选择会被原样提交**，`allAnswered`（`69-72`）仍为真，等于用旧映射确认了新一批文件。这是"技术变更被普通确认覆盖"的一个具体入口。
7. **`numberText` / `text()` / `clean()` 实现**：`text(risk.subjectLabel, risk.subjectRef)`（`1919`）的回退语义、`clean()`（`1160`）是否归一大小写与空白、`numberText`（`1904`）的千分位/兜底——三者影响 P1-1 的 subject 匹配与 P1-4 的数字呈现。
8. **`public_findings_meta` 的前端消费点**：P0-1 修复的落点。docstring（`facts_mode_outputs.py:343`）声称状态经此暴露；在给定摘录内没有任何消费点。
9. **`_AI_FINDINGS_ARTIFACT` 常量值与 legacy 分支的真实读取面**：决定 P0-4 第 1 项的影响半径（畸形 binding 到底会退到哪个文件）。
10. **`aggregation.risk_count` 与 `currentRisks` 的产出代码**：P1-4 的口径定案依据。
11. **专家包 28 项清单**：我没有该清单，只有边界文档。计划里"专家 28 项加原全部要求，不缩水"是**唯一一条我判定为未经验证的主张**。建议 W00 基线直接附一份 28 项 ↔ 工作包对照表，否则"不缩水"无法被任何人核。
12. **R06 的写入/读取时序**：跨范围，交主线程，我不重复探针。

### 对"旧 goal 仍 paused、本轮只出包"的一点意见

这条安排可以接受，但代价需要写明：**P0-1 与 P0-3 是当前代码正在向用户输出错误信息的两处**——一处让医学监察员把"工件不可读"读成"该范围无需核查"，一处让他把模板字符串当作"已校验的原始记录"。两者都是本地的、可逆的、改动面极小的静态修复（P0-3 约两行，P0-1 一处状态透传 + 一段空态文案）。若"只出包"意味着完全不动代码，这段时间里用户依然会看到那两句错误结论。是否把这两条作为独立最小补丁先评估，由主线程决定；我只把代价摆出来。

### 一句话总括

计划的四条执行约束——整组一次回归、禁止逐改逐测、前端 fixture 并行、不新增通用引擎/审批——**我认可，建议保留**。需要修订的是排序与归属：W01 升级为"身份与真实性契约"并持有唯一跨包阻塞权；W05 三个点击目标里两个的产出方前置到 W01；W03 拆成"删罐装画像"与"新增双模型知识"两半，前者立刻做以解除 `unknown_visible` 的误导；W02→W03 的角色依赖显式写出；边界四行能力分层（尤其第 3 行需单独确认、第 4 行不许用"无此文件"补足）必须进计划。所有结论限于你给的摘录，未做全仓逐行审阅，未做 API/browser 验收，未做医学验收；凡依赖未读代码或未读组件之处，均已在文中标为未知，未替主线程下结论。
