原审阅读取受限，现通过内联冻结源文本完成同session恢复；不用工具，不请求权限，不声称读过其他文件。以下是a7217af原始源码真实行号和拟议计划。作为独立挑战者给分级意见、计划修订、不确定性。只返回正文，由runner保存。不得声称全仓逐行/浏览器验收。
计划：W00基线/路线/成功证据复用；W01项目+结果/facts/来源不可变解析；W02文件角色先验后存、版本回执、解释型确认/异步隔离；W03语义映射facts/完整工具覆盖、删除疾病风险/版本投票画像、正式来源双模型知识；W04命题双路核验反证/零发现/全域覆盖、持久调度收尾；W05公开Finding到中文工作清单/真实时间8轨旅程/来源/研究中心流向；W06兼容增量三模式/草稿报告；W07五项目全量/适用增量/恢复启动性能用户验收。前端在DTO稳定后可并行fixture开发，不等真实模型。不新增通用引擎/审批。每工作包整组改完一次相关回归，只有共享合同变化跑相邻，最终一轮全回归+ego。失败按根因批修，禁止一改一测/反复全测/反复真实全量。专家28项加原全部要求，不缩水。当前旧goal仍paused，本轮只出包。审议遗漏、依赖与过度设计。
# 产品边界与待决项 · 0922V2

## 已确认且不得回退

产品是完整临床数据、Patient Profile、纵向时间线、医学风险与可选Query草稿的一体化工作台，不是文件审批工具，也不是两套模型输出的一致率看板。

风险直接可读；不增加逐条风险批准、签名、正式Query发送/回复/关闭或外部系统写入。输入文件用途确有歧义时可以有限澄清，但不能把技术失败、校验错误或所有模型分歧都转成“请用户确认”。

保留Graph全局状态/依赖/恢复，Loop负责局部有界取证/修复。保留授权、项目隔离、盲态、真实来源、版本、审计、幂等和可取消恢复。不得用关闭校验、伪造结果身份、借其他事件来源或少看临床数据来提速。

完整原始记录与正常值仍可访问。受试者/事件/时间窗/来源身份贯穿各视图；UI可以折叠、分页、虚拟化，不得在API截掉原始事实、否定或反证。纯浏览不新增模型调用。

## 本轮不擅自作出的决定

1. “风险列表替换默认首页”仍不是用户已确认事项。先提供清晰切换、记忆最近视图并保留研究概览。
2. 文件未齐就执行完整医学监查，不等同于此前认可的部分结果可用。
3. 不按开发者回忆撤换模型或索要新密钥；当前路由只需按实际授权配置、冻结身份、记录观测，路由恢复不应阻塞UI/状态修复。

## 资料未齐时的能力分层建议

| 能力 | 输入条件 | 状态表达 |
|---|---|---|
| 原始Listing/文件/导入台账查看 | 文件合法、解析和权限满足 | 可用；未识别语义单列，不冒充已确认映射 |
| 已确认字段的受试者明细与时间线 | 身份/日期/单位等该视图必需语义已核验 | 局部可用；缺字段的轨道或时间关系明确缺口 |
| 不依赖研究方案的基础医学线索分析 | 所需语义、事实与上下文满足且此能力经产品确认 | 建议独立标识分析范围；不声称“全方案监查完成” |
| 入排、洗脱/禁药、访视窗、AESI等依赖方案/IB的判断 | 对应版本文档和规则有效 | 依赖未满足时不可评估；不能以用户点击“无此文件”补足 |

前两项属于现有渐进可用原则的落实。第三项“文档未齐先执行基础医学AI分析”需要单独确认启用范围，不能以本包默认授权。第四项缺依赖不得伪装已完成。

## 正确区分确认

文件角色选择只确认“使用哪份文件承担哪种用途”；内容警告确认只处理一条可解释、可追溯且允许覆盖的具体不确定性。它们都不证明全部正文正确、不证明实际模型独立，也不批准医学结论。

文件损坏、哈希不符、跨研究来源串用等技术/身份错误不由普通确认按钮覆盖。确属元数据或上下文告警时，显示预期值、实际提取值、对应证据和影响范围；保留被授权用户的真实身份与版本化决策，不自动写成“已医学核对”。

### frontend/src/features/medical-monitoring/MedicalMonitoringAdmissionWizard.jsx
55:     empty: "空列",
56:   })[value] || "类型待定";
57: }
58: 
59: function DocumentReadinessPanel({ state, onFiles, onRetry, onAdjudicate, onContentConfirm }) {
60:   const [choices, setChoices] = useState({});
61:   if (!state || (state.phase === "loading" && !state.payload)) {
62:     return <p className="monitoring-admission-loading" role="status">正在核对研究文档…</p>;
63:   }
64:   const payload = state.payload || {};
65:   const processing = [
66:     "uploading", "analyzing", "reviewing", "adjudicating", "cross_checking",
67:   ]
68:     .includes(state.phase);
69:   const userChoices = Array.isArray(payload.user_choices) ? payload.user_choices : [];
70:   const allAnswered = userChoices.every(
71:     (choice) => typeof choices[choice.role] === "string",
72:   );
73:   return (
74:     <section className="monitoring-admission-documents" aria-label="研究文档准备情况">
75:       <header>
76:         <strong>{payload.headline || "正在核对研究文档"}</strong>
77:         <span>{payload.guidance || "系统会自动识别，无需填写技术信息。"}</span>
78:       </header>
79:       <ul>
80:         {(payload.roles || []).map((item) => (
81:           <li key={item.role}>
82:             <span><strong>{item.label}</strong><small>{item.status_text}</small></span>
83:           </li>
84:         ))}
85:       </ul>
86:       {(payload.content_confirmations || []).length ? (
87:         <fieldset className="monitoring-admission-user-choices">
88:           <legend>内容核对确认（逐项核对后确认沿用）</legend>
89:           {(payload.content_confirmations || []).map((entry) => (
90:             <div key={entry.source_entry_id} role="group" aria-label={`内容核对：${entry.filename}`}>
91:               <strong>{entry.filename}</strong>
92:               <small>
93:                 {" "}角色 {entry.role} · 内容核对：{entry.content_status} · 使用状态：{entry.use_status}
94:               </small>
95:               <button
96:                 type="button"
97:                 className="monitoring-admission-secondary"
98:                 disabled={processing}
99:                 onClick={() => onContentConfirm?.(entry)}
100:                 title="我已核对该文件内容，确认按当前内容沿用"
101:               >
102:                 我已核对，确认沿用
103:               </button>
104:             </div>
105:           ))}
106:         </fieldset>
107:       ) : null}
108:       {userChoices.length ? (
109:         <fieldset className="monitoring-admission-user-choices">
110:           <legend>请确认每个文件角色对应的文件（医学判断以您为准）</legend>
111:           {userChoices.map((choice) => (
112:             <div key={choice.role} role="group" aria-label={`文件角色：${choice.role}`}>
113:               <strong>角色：{choice.role}</strong>
114:               {choice.options.map((option) => (
115:                 <label key={option.candidate_id || "__missing__"} style={{ display: "block" }}>
116:                   <input
117:                     type="radio"
118:                     name={`doc-role-${choice.role}`}
119:                     checked={(choices[choice.role] || "") === option.candidate_id}
120:                     onChange={() => setChoices((current) => ({
121:                       ...current,
122:                       [choice.role]: option.candidate_id,
123:                     }))}
124:                   />
125:                   {" "}
126:                   {option.candidate_id
127:                     ? `这是${choice.role}文件：${option.filename}`
128:                     : `没有${choice.role}文件（该角色缺失）`}
129:                 </label>
130:               ))}
131:             </div>
132:           ))}
133:           <button
134:             type="button"
135:             className="monitoring-admission-secondary"
136:             disabled={!allAnswered || processing}
137:             onClick={() => onAdjudicate?.(
138:               userChoices.map((choice) => ({
139:                 role: choice.role,
140:                 candidate_id: choices[choice.role] || "",
141:               })),
142:             )}
143:             title={allAnswered ? "提交裁决并继续核对" : "请先为每个角色作出选择"}
144:           >
### frontend/src/features/medical-monitoring/MedicalMonitoringWorkspace.jsx
1826: }
1827: 
1828: export function QueryWorkspaceView({ payload, route, onSubjectSelect, onSource, onFindingSelect, onBack }) {
1829:   const projection = payload.projection;
1830:   const subjectsByRef = new Map((projection.subjects || []).map((subject) => [subject.subject_ref || subject.subject_id, subject]));
1831:   const risks = (projection.currentRisks || [])
1832:     .filter((risk) => !risk.aggregate && ["critical", "high", "medium"].includes(risk.severity))
1833:     .sort((left, right) => ["critical", "high", "medium"].indexOf(left.severity) - ["critical", "high", "medium"].indexOf(right.severity));
1834:   const totalCount = projection.aggregation?.risk_count ?? risks.length;
1835:   const aiFindings = Array.isArray(projection.aiQueryFindings) ? projection.aiQueryFindings : [];
1836:   const aiAccepted = aiFindings.filter((item) => item.state === "accepted").length;
1837:   const aiEscalated = aiFindings.filter((item) => item.state === "escalated").length;
1838:   const aiGaps = aiFindings.filter((item) => item.state === "unverifiable_gap" || item.state === "coverage_gap").length;
1839:   return (
1840:     <div className="monitoring-view-stack monitoring-query-workspace" data-monitoring-query-count={risks.length}>
1841:       {aiFindings.length ? (
1842:         <section className="monitoring-panel monitoring-panel-wide">
1843:           <div className="monitoring-section-heading"><span className="monitoring-eyebrow">双模型分析</span><h2>AI 跨表线索（{aiFindings.length} 条 · 双cohort一致 {aiAccepted} · 分歧 {aiEscalated} · 待补核 {aiGaps}）</h2></div>
1844:           <p className="monitoring-query-intro">以下线索由主分析与独立盲核（双模型全量盲核对）产出；模型一致性是核验状态而非医学结论，最终判断由您对照原始记录作出。</p>
1845:           <ul className="monitoring-query-card-list">
1846:             {aiFindings.map((item) => {
1847:               // N4：subject身份由服务端投影解析（subject_ref），不再按
1848:               // subject-${label}猜ID；分页外受试者仍可按ref导航。
1849:               const subject = (item.subject_ref && subjectsByRef.get(item.subject_ref))
1850:                 || (projection.subjects || []).find((row) => row.subject_label === item.subject_label)
1851:                 || (item.subject_ref ? { subject_ref: item.subject_ref, site_ref: item.site_ref, spine_ref: item.spine_ref } : null);
1852:               const stateBadge = item.state === "accepted" ? "双cohort一致" : item.state === "escalated" ? "分歧待裁决" : "待补核";
1853:               const claims = Array.isArray(item.claims) ? item.claims : [];
1854:               const anchorEvent = Array.isArray(item.anchor_event_refs) && item.anchor_event_refs.length
1855:                 ? item.anchor_event_refs[0] : "";
1856:               return (
1857:                 <li key={item.finding_id} className="monitoring-query-card" data-query-finding={item.finding_id} data-finding-state={item.state} data-finding-kind={item.kind || "finding"}>
1858:                   <header className="monitoring-query-card-head">
1859:                     <span className={`monitoring-query-state-chip monitoring-query-state-${item.state}`}>{stateBadge}</span>
1860:                     <strong>{item.title}</strong>
1861:                     <span className="monitoring-query-card-target">
1862:                       受试者{" "}
1863:                       {subject ? (
1864:                         <button type="button" className="monitoring-subject-link" onClick={() => onSubjectSelect?.(subject)}>{item.subject_label || "查看"}</button>
1865:                       ) : (
1866:                         <span>{item.subject_label || "待确认"}</span>
1867:                       )}
1868:                     </span>
1869:                   </header>
1870:                   <div className="monitoring-query-card-body">
1871:                     {claims.length ? (
1872:                       <section aria-label="观察与依据"><h3>观察与依据</h3>
1873:                         <ul className="monitoring-claim-list">
1874:                           {claims.map((claim, claimIndex) => (
1875:                             <li key={claimIndex} data-claim-kind={claim.kind || ""}>
1876:                               {claim.text}
1877:                               {claim.evidence_ids?.length ? (
1878:                                 <span className="monitoring-claim-evidence">（证据 {claim.evidence_ids.length} 条）</span>
1879:                               ) : null}
1880:                             </li>
1881:                           ))}
1882:                         </ul>
1883:                       </section>
1884:                     ) : (
1885:                       <section aria-label="发现"><h3>发现</h3><p>{item.text || item.title}</p></section>
1886:                     )}
1887:                     {item.kind === "coverage_gap" ? (
1888:                       <section aria-label="覆盖说明"><h3>覆盖说明</h3><p>{item.state_reason_zh || "本轮双cohort未能完成该受试者的核实，覆盖不足如实标出，待下轮补核。"}</p></section>
1889:                     ) : null}
1890:                   </div>
1891:                   <footer className="monitoring-query-card-actions">
1892:                     <button type="button" disabled={!subject} onClick={() => subject && onSubjectSelect?.(subject)}>进入受试者医学旅程</button>
1893:                     {item.anchor_event_refs?.length && onFindingSelect ? (
1894:                       <button type="button" className="monitoring-back-button" onClick={() => onFindingSelect?.(item)}>定位关联事件</button>
1895:                     ) : null}
1896:                   </footer>
1897:                 </li>
1898:               );
1899:             })}
1900:           </ul>
1901:         </section>
1902:       ) : null}
1903:       <section className="monitoring-panel monitoring-panel-wide">
1904:         <div className="monitoring-section-heading"><span className="monitoring-eyebrow">查询工作区</span><h2>请核实事项（{risks.length} 项待核对 · 全量锚点 {numberText(totalCount)}）</h2></div>
1905:         <p className="monitoring-query-intro">以下每张卡片按「依据 — 发现 — 请核实事项」三段呈现：先看数据依据，再看医学发现，最后由您核对原始记录后决定是否发出数据核查问题。AI 只定位证据和风险，医学判断由您终审。</p>
1906:         {risks.length === 0 ? (
1907:           <div className="monitoring-empty-inline">当前范围内没有待核实的查询事项。</div>
1908:         ) : (
1909:           <ul className="monitoring-query-card-list">
1910:             {risks.map((risk) => {
1911:               const subject = subjectsByRef.get(risk.subjectRef);
1912:               const evidence = risk.evidenceSummary || {};
1913:               return (
1914:                 <li key={risk.riskInstanceRef || risk.riskRef} className="monitoring-query-card" data-query-risk={risk.riskInstanceRef || risk.riskRef}>
1915:                   <header className="monitoring-query-card-head">
1916:                     <RiskBadge risk={risk} />
1917:                     <strong>{risk.riskType}</strong>
1918:                     <span className="monitoring-query-card-target">
1919:                       受试者 {text(risk.subjectLabel, risk.subjectRef)} · 中心 {risk.siteLabel}
1920:                     </span>
### frontend/src/features/medical-monitoring/MedicalMonitoringProductLoop.jsx
1155:   }, [navigate, resultPayload, route]);
1156:   // N4：finding锚点事件精确定位——从AI线索卡片进入受试者旅程并聚焦
1157:   // 该线索真实关联的事件（不默认选第一条AE）。
1158:   const selectResultFinding = useCallback((finding) => {
1159:     if (!resultPayload || !finding) return;
1160:     const subject = (resultPayload.projection.subjects || []).find((row) => clean(row.subject_ref || row.subject_id) === clean(finding.subject_ref)) || {
1161:       subject_ref: finding.subject_ref,
1162:       site_ref: finding.site_ref,
1163:       spine_ref: finding.spine_ref,
1164:     };
1165:     const window = selectedSubjectWindow(resultPayload, subject, route);
1166:     const eventRef = Array.isArray(finding.anchor_event_refs) && finding.anchor_event_refs.length
1167:       ? finding.anchor_event_refs[0]
1168:       : "";
1169:     navigate("journey", {
1170:       site_ref: finding.site_ref || subject.site_ref || subject.site_id,
1171:       subject_ref: finding.subject_ref || subject.subject_ref || subject.subject_id,
1172:       spine_ref: finding.spine_ref || subject.spine_ref || subject.spineRef,
1173:       window_start: window.start,
1174:       window_end: window.end,
1175:       event_ref: eventRef,
1176:       risk_instance_ref: "",
1177:       risk_anchor_ref: "",
1178:     });
1179:   }, [navigate, resultPayload, route]);
1180:   const selectResultCenter = useCallback((center) => navigate("site_overview", { site_ref: center.siteRef || center.site_ref }), [navigate]);
1181:   const selectResultEvent = useCallback((event) => navigate(routeView, {
1182:     event_ref: event.eventRef || event.event_ref,
1183:     visit_ref: event.visitRef || event.visit_ref,
1184:     risk_anchor_ref: event.riskAnchorRefs?.[0] || event.risk_anchor_refs?.[0],
1185:     risk_instance_ref: "",
### packages/medical_monitoring/api/r7_product/facts_mode_outputs.py
333:     def public_findings(
334:         self,
335:         projection: Optional[Mapping[str, Any]] = None,
336:         project_ref: str = "",
337:     ) -> list[dict[str, Any]]:
338:         """Audience-facing projection of the dual-cohort findings.
339: 
340:         N1阅读模型：稳定finding_id贯穿（不按index重编号，显示序号另存
341:         display_seq）；保留claims真实证据引用与服务端可解析的事件/来源
342:         锚点；无标题的覆盖缺口以kind=coverage_gap可见（不依赖标题存活）；
343:         state与artifact身份经 public_findings_meta 暴露。
344:         """
345: 
346:         read = self._read_ai_findings()
347:         if read["state"] not in ("completed_with_findings", "completed_no_findings"):
348:             return []
349:         subjects_by_label: dict[str, Mapping[str, Any]] = {}
350:         for subject in (projection or {}).get("subjects", []) or []:
351:             label = str(
352:                 subject.get("subject_label")
353:                 or subject.get("label")
354:                 or ""
355:             ).strip()
356:             if label:
357:                 subjects_by_label.setdefault(label, subject)
358:         anchor_index_cache: dict[str, dict[str, tuple[str, int]]] = {}
359:         rows: list[dict[str, Any]] = []
360:         for index, item in enumerate(read["findings"]):
361:             cohort = (item.get("primary") or item.get("verifier")) or {}
362:             state = str(item.get("state", "escalated"))
363:             title = str(cohort.get("title", "")).strip()
364:             kind = "finding"
365:             if state == "unverifiable_gap" and not title:
366:                 kind = "coverage_gap"
367:                 title = "覆盖缺口（本轮未能完成该受试者的双cohort核实）"
368:             subject_label = str(item.get("subject_label", ""))
369:             # 服务端解析subject身份（不猜ID）：projection.subjects由包授权
370:             # 投影给出subject_ref/site_ref/spine_ref。
371:             subject_row = subjects_by_label.get(subject_label) or {}
372:             evidence_ids = self._finding_evidence_ids(item)
373:             claims = self._finding_claims(item)
374:             rows.append(
375:                 {
376:                     "finding_id": str(item.get("finding_id", "")) or f"aemh-unid-{index:04d}",
377:                     "display_seq": index + 1,
378:                     "kind": kind,
379:                     "subject_label": subject_label,
380:                     "subject_ref": str(subject_row.get("subject_ref") or subject_row.get("subject_id") or ""),
381:                     "site_ref": str(subject_row.get("site_ref") or subject_row.get("site_id") or ""),
382:                     "spine_ref": str(subject_row.get("spine_ref") or ""),
383:                     "state": state,
384:                     "state_reason_zh": str(item.get("reason_zh", "")),
385:                     "title": title[:200],
386:                     "text": str(cohort.get("text", ""))[:2000],
387:                     "evidence_ids": evidence_ids,
388:                     "claims": claims,
389:                 }
390:             )
391:         return rows
392: 
393:     def _finding_claims(self, item: Mapping[str, Any]) -> list[dict[str, Any]]:
394:         """真实工件payload的语义分点（观察/缺口/核实建议，供ul/li渲染）。
395: 
396:         真实形态：observations=观察事实条目；data_gaps=资料缺口条目；
### packages/medical_monitoring/api/r7_product/facts_mode_outputs.py
479:     def _read_findings_binding(self) -> dict[str, Any]:
480:         """V5-04：读取发布指针binding（当前结果指针；发布结果不可变）。
481: 
482:         binding由发布方（finalize/发布流程）落盘：{artifact,
483:         content_sha256, project_id, snapshot_digest}。读取时校验
484:         文件内容与binding声明一致——不接受同名冒充。
485:         """
486: 
487:         if self._artifacts_dir is None:
488:             return {}
489:         try:
490:             value = json.loads(
491:                 (Path(self._artifacts_dir) / self._FINDINGS_BINDING).read_text(
492:                     encoding="utf-8"
493:                 )
494:             )
495:         except (OSError, ValueError):
496:             return {}
497:         if not isinstance(value, dict):
498:             return {}
499:         artifact = str(value.get("artifact", "")).strip()
500:         digest = str(value.get("content_sha256", "")).strip()
501:         if (
502:             not artifact
503:             or "/" in artifact
504:             or ".." in artifact
505:             or len(digest) != 64
506:         ):
507:             return {}
508:         return value
509: 
510:     def _read_ai_findings(self) -> dict[str, Any]:
511:         """读取AI findings工件，返回带状态与身份的读取结果。
512: 
513:         - missing：工件不存在（项目无双cohort lane）
514:         - read_failed：存在但JSON损坏或hash校验不符——调用方不得用
515:           备用生成冒充AI分析（事实观察可另路展示并独立标状态）
516:         - completed_no_findings / completed_with_findings：完成态分离
517:           （有效空数组≠缺失）
518:         目标解析顺序（V5-04冻结结果合同）：
519:         1) binding指针存在→读binding声明的工件，并验证工件payload
520:            hash==binding.content_sha256（同名不同内容判read_failed）
521:         2) 无binding→legacy固定冻结名（历史工件自申报hash校验）
522:         不glob+mtime取最新——旧run不得读到新工件。
523:         """
524: 
525:         if self._artifacts_dir is None:
526:             return {"state": "missing", "findings": None, "artifact": None,
527:                     "error": "artifacts_dir未配置"}
528:         binding = self._read_findings_binding()
529:         if binding:
530:             artifact_name = str(binding["artifact"])
531:             expected_digest = str(binding["content_sha256"])
532:             project_id = str(binding.get("project_id", "")).strip()
533:             if (
534:                 self._project_ref
535:                 and project_id
536:                 and project_id != str(self._project_ref)
537:             ):
538:                 return {"state": "read_failed", "findings": None,
539:                         "artifact": artifact_name,
540:                         "error": "binding_project_mismatch"}
541:             artifact_path = Path(self._artifacts_dir) / artifact_name
542:         else:
543:             artifact_name = _AI_FINDINGS_ARTIFACT
544:             expected_digest = ""
545:             artifact_path = Path(self._artifacts_dir) / artifact_name
546:         if not artifact_path.is_file():
547:             return {"state": "missing", "findings": None,
548:                     "artifact": artifact_name, "error": None}
549:         try:
550:             with open(artifact_path, encoding="utf-8") as handle:
551:                 artifact = json.load(handle)
552:         except (OSError, ValueError) as exc:
553:             return {"state": "read_failed", "findings": None,
554:                     "artifact": artifact_name,
555:                     "error": f"json_decode: {exc}"}
556:         if not isinstance(artifact, dict):
557:             return {"state": "read_failed", "findings": None,
558:                     "artifact": artifact_name, "error": "not_object"}
559:         declared = str(artifact.get("content_sha256", "")).strip()
560:         verify = {k: v for k, v in artifact.items() if k != "content_sha256"}
561:         recomputed = content_hash(verify)
562:         if declared and recomputed != declared:
563:             return {"state": "read_failed", "findings": None,
564:                     "artifact": artifact_name,
565:                     "error": "content_sha256_mismatch"}
566:         if expected_digest and recomputed != expected_digest:
567:             # 同名工件内容被替换：与binding声明不符（V5-04 R5-11反例）
568:             return {"state": "read_failed", "findings": None,
569:                     "artifact": artifact_name,
570:                     "error": "binding_digest_mismatch"}
571:         findings = artifact.get("findings")
572:         if not isinstance(findings, list):
573:             return {"state": "read_failed", "findings": None,
### packages/medical_monitoring/projections/facts_publication.py
413: 
414:     def _load_domains(self) -> dict[str, list[dict[str, Any]]]:
415:         """按持久化不可变清单加载事实表（WP1：不扫描碰巧同名的JSON）。
416: 
417:         首次加载时从"64位十六进制内容hash命名+单表结构"的严格形态文件
418:         构建facts-manifest.json（同表多文件取mtime最新，其余记为
419:         superseded）；此后一律按清单逐文件校验sha256后加载——同目录的
420:         findings/布局/方案画像等非事实文件永不混入，字节篡改fail-closed。
421:         """
422:         artifacts = self._workspace / "runtime" / "artifacts"
423:         manifest_path = artifacts / _FACTS_MANIFEST_NAME
424:         manifest: dict[str, Any] | None = None
425:         if manifest_path.is_file():
426:             try:
427:                 manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
428:             except (OSError, ValueError):
429:                 manifest = None
430:             if not isinstance(manifest, dict) or manifest.get("schema") != _FACTS_MANIFEST_SCHEMA:
431:                 manifest = None
432:         if manifest is None:
433:             manifest = _build_facts_manifest(artifacts)
434:             _atomic_write_json(manifest_path, manifest)
435:         domains: dict[str, list[dict[str, Any]]] = {}
436:         for entry in manifest.get("tables", []):
437:             path = artifacts / str(entry["file"])
438:             try:
439:                 raw = path.read_bytes()
440:             except OSError as exc:
441:                 raise FactsPublicationError(
442:                     f"facts manifest entry unreadable: {entry['file']}: {exc}"
443:                 ) from exc
444:             if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
445:                 raise FactsPublicationError(
446:                     f"facts manifest digest mismatch (tampered or replaced "
447:                     f"artifact): {entry['file']}"
448:                 )
449:             payload = json.loads(raw.decode("utf-8"))
450:             table = str(entry["table"])
451:             rows = payload.get(table) if isinstance(payload, dict) else None
452:             if not isinstance(rows, list):
453:                 raise FactsPublicationError(
454:                     f"facts manifest entry shape invalid: {entry['file']}"
455:                 )
456:             domains[table] = rows
457:         return domains
458: 
459:     # -- packet ------------------------------------------------------------
460: 
461:     def get_authority(self, identity: Any, **_: Any) -> R5AuthorityPacket:
462:         cache_key = (
463:             str(getattr(identity, "project_ref", "")),
464:             str(getattr(identity, "snapshot_ref", "")),
465:         )
466:         cached = self._cache.get(cache_key)
467:         if cached is not None:
468:             return cached
469:         packet = self._build(cache_key)
470:         self._cache[cache_key] = packet
471:         return packet
472: 
473:     def get_packet(
474:         self,
475:         project_ref: str,
476:         run_ref: str | None = None,
477:         snapshot_ref: str | None = None,
478:         cutoff_ref: str | None = None,
479:     ) -> R5AuthorityPacket:
480:         """Positional adapter consumed by R5ProductAdapter._packet."""
481:         key = (str(project_ref), str(snapshot_ref or "facts-snapshot-001"))
482:         cached = self._cache.get(key)
483:         if cached is not None:
484:             return cached
485:         packet = self._build(key)
486:         self._cache[key] = packet
487:         return packet
488: 
489:     def _build(self, cache_key: tuple[str, str]) -> R5AuthorityPacket:
490:         domains = self._load_domains()
491:         snapshot_ref = cache_key[1] or "facts-snapshot-001"
492: 
### packages/medical_monitoring/projections/facts_publication.py
528:         def _locator(table: str, index: int) -> R5SourceRecord:
529:             ref = f"loc-{table}-{index:06d}"
530:             record = R5SourceRecord(
531:                 locator_ref=ref,
532:                 snapshot_ref=snapshot_ref,
533:                 source_file_ref=f"listing:{table}",
534:                 source_revision_ref=f"src-rev-{table}",
535:                 source_revision_content_hash=content_hash({"table": table})[:64].replace("-", "0"),
536:                 record_ref=f"row-{table}-{index:06d}",
537:                 canonical_location=f"{table}!row{index + 1}",
538:                 excerpt=f"{table} 第{index + 1}行原始数据（已校验）",
539:             )
540:             sources.append(record)
541:             return record
542: 
543:         def _add_event(
### packages/medical_monitoring/analysis/protocol_profile.py
1: """Generic protocol/IB structured profile for the anti-overfit analysis lane.
2: 
3: Extracts a content-addressed profile from the project's registered study
4: documents (protocol, IB): CTCAE grading version, AE grading policy anchors,
5: indication/drug-class hints and their expected risk directions. The profile
6: is project-agnostic — everything is derived from document text with pattern
7: rules, never from a hard-coded drug or protocol.
8: """
9: from __future__ import annotations
10: 
11: import json
12: import re
13: from dataclasses import dataclass, field
14: from pathlib import Path
15: from typing import Any, Mapping, Optional
16: 
17: from ..intelligence.primitives import content_hash
18: 
19: _CTCAE_PATTERNS = (
20:     re.compile(r"CTCAE\s*(?:版本|version)?\s*[vV]?\.?\s*([0-9](?:\.[0-9])?)"),
21:     re.compile(r"不良事件术语认定标准\s*([0-9](?:\.[0-9])?)"),
22:     re.compile(r"（CTCAE\s*([0-9](?:\.[0-9])?)）"),
23: )
24: _MEDDRA_PATTERN = re.compile(r"MedDRA\s*(?:版本|version)?\s*([0-9]{1,2}(?:\.[0-9])?)", re.IGNORECASE)
25: _INDICATION_HINTS = (
26:     ("过敏性鼻炎", "过敏性鼻炎", "抗组胺/鼻用糖皮质激素相关嗜睡、鼻部刺激、局部感染风险"),
27:     ("哮喘", "支气管哮喘", "支气管痉挛、口咽念珠菌感染、声嘶风险（吸入糖皮质激素）"),
28:     ("特应性皮炎", "特应性皮炎", "皮肤感染、烧灼感、免疫系统抑制风险"),
29:     ("2型糖尿病", "2型糖尿病", "低血糖、胃肠道反应、体重变化风险"),
30:     ("高血压", "原发性高血压", "低血压、电解质紊乱、肾功能变化风险"),
31:     ("类风湿", "类风湿关节炎", "感染、肝功能异常、血液学异常风险"),
32:     ("实体瘤", "晚期实体瘤", "骨髓抑制、感染、器官毒性风险"),
33:     ("淋巴瘤", "淋巴瘤", "骨髓抑制、感染、输注反应风险"),
34: )
35: _AE_SEVERITY_RULES_HINT = re.compile(r"(?:严重程度|分级|grade).{0,40}(?:CTCAE|毒性)", re.IGNORECASE)
36: 
37: 
38: @dataclass(frozen=True)
39: class ProtocolProfile:
40:     content_sha256: str
41:     ctcae_version: str = ""
42:     meddra_version: str = ""
43:     indication_zh: str = ""
44:     risk_direction_zh: str = ""
45:     anchors: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (quote, where)
46: 
47:     def to_payload(self) -> dict[str, Any]:
48:         return {
49:             "content_sha256": self.content_sha256,
50:             "ctcae_version": self.ctcae_version,
51:             "meddra_version": self.meddra_version,
52:             "indication_zh": self.indication_zh,
53:             "risk_direction_zh": self.risk_direction_zh,
54:             "anchors": [{"quote": q[:200], "where": w} for q, w in self.anchors[:10]],
55:             "unknown_visible": not (self.ctcae_version or self.risk_direction_zh),
56:         }
57: 
58: 
59: def _docx_text(path: Path) -> str:
60:     import docx  # noqa: PLC0415
61: 
62:     parts = []
63:     for paragraph in docx.Document(str(path)).paragraphs:
64:         parts.append(paragraph.text)
65:     try:
66:         for table in docx.Document(str(path)).tables:
67:             for row in table.rows:
68:                 parts.append(" | ".join(cell.text for cell in row.cells))
69:     except Exception:
70:         pass
71:     return "\n".join(parts)
72: 
73: 
74: def _pdf_text(path: Path) -> str:
75:     from pdfminer.high_level import extract_text  # noqa: PLC0415
76: 
77:     return extract_text(str(path), maxpages=60)
78: 
79: 
80: def _document_text(path: Path) -> str:
81:     suffix = path.suffix.lower()
82:     if suffix == ".docx":
83:         return _docx_text(path)
84:     if suffix == ".pdf":
85:         return _pdf_text(path)
86:     if suffix == ".txt":
87:         return path.read_text(encoding="utf-8", errors="ignore")
88:     return ""
89: 
90: 
91: def build_protocol_profile(files_dir: Path) -> Optional[ProtocolProfile]:
92:     """Derive the profile from every registered document; newest wins per field.
93: 
94:     Fields stay empty (and ``unknown_visible`` turns true) when no document
95:     carries the evidence — coverage gaps are surfaced, never guessed.
96:     """
97:     ctcea_candidates: list[str] = []
98:     meddra_candidates: list[str] = []
99:     indication = ""
100:     risk_direction = ""
101:     anchors: list[tuple[str, str]] = []
102:     total_chars = 0
103:     for path in sorted(files_dir.glob("*")):
104:         if path.suffix.lower() not in (".docx", ".pdf", ".txt"):
105:             continue
106:         try:
107:             text = _document_text(path)
108:         except Exception:
109:             continue
110:         total_chars += len(text)
111:         where = path.name[:24]
112:         # 方案（docx）是项目标准版本的权威来源：其匹配权重高于IB等背景资料。
113:         weight = 3 if path.suffix.lower() == ".docx" else 1
114:         for pattern in _CTCAE_PATTERNS:
115:             for match in pattern.finditer(text):
116:                 ctcea_candidates.extend([match.group(1)] * weight)
117:                 anchors.append((match.group(0), where))
118:         for match in _MEDDRA_PATTERN.finditer(text):
119:             meddra_candidates.extend([match.group(1)] * weight)
120:             anchors.append((match.group(0), where))
121:         for keyword, indication_name, direction in _INDICATION_HINTS:
122:             if keyword in text:
123:                 indication = indication_name
124:                 risk_direction = direction
125:                 anchors.append((f"适应症：{indication_name}", where))
126:                 break
127: 
128:     def _elect(candidates: list[str]) -> str:
129:         # 多文档投票：出现最多的版本胜出；平票取数值更高者。
130:         if not candidates:
131:             return ""
132:         counts: dict[str, int] = {}
133:         for value in candidates:
134:             counts[value] = counts.get(value, 0) + 1
135:         return max(
136:             counts,
137:             key=lambda v: (counts[v], float(v) if v.replace(".", "").isdigit() else 0),
138:         )
139: 
140:     ctcae = _elect(ctcea_candidates)
141:     meddra = _elect(meddra_candidates)
142:     payload = {
143:         "ctcae_version": ctcae,
144:         "meddra_version": meddra,
145:         "indication_zh": indication,
146:         "risk_direction_zh": risk_direction,
147:         "anchors": anchors[:10],
148:         "total_document_chars": total_chars,
149:     }
150:     profile = ProtocolProfile(
151:         content_sha256=content_hash(payload),
152:         ctcae_version=ctcae,
153:         meddra_version=meddra,
154:         indication_zh=indication,
155:         risk_direction_zh=risk_direction,
156:         anchors=tuple(anchors[:10]),
157:     )
158:     if total_chars == 0:
159:         return None
160:     return profile
161: 
162: 
163: def profile_artifact_path(workspace: Path) -> Path:
164:     return workspace / "runtime" / "artifacts" / "protocol-profile.json"
165: 
166: 
### packages/medical_monitoring/analysis/ae_mh_cross_analysis.py
402: def _clues_agree(primary: Any, verifier: Any) -> bool:
403:     """Pairing: shared evidence rows AND compatible proposition direction.
404: 
405:     Two independent models often cite different rows of the same subject while
406:     describing the same finding (e.g. both discuss the hypertension history,
407:     one citing MH rows and the other CM rows). Evidence overlap alone would
408:     mis-file those as disagreements.
409: 
410:     N5命题核验：evidence_id重叠是必要条件而非充分条件——两条线索引用
411:     同一证据但命题方向相反（"存在AE"vs"未见AE"）不得判为一致。
412:     方向通过正/负标记词频比较，neutral方向不做方向否决。
413:     """
414:     shared_evidence = _clue_fingerprint(primary) & _clue_fingerprint(verifier)
415:     domains = _clue_domain_pair(primary) & _clue_domain_pair(verifier)
416:     shared_entities = _clue_entities(primary) & _clue_entities(verifier)
417: 
418:     has_evidence_overlap = bool(shared_evidence)
419:     has_entity_match = bool(domains) and len(shared_entities) >= 2
420: 
421:     if not has_evidence_overlap and not has_entity_match:
422:         return False
423: 
424:     # V5-06命题核验降级：词频方向仅是候选配对信号，不是确认依据。
425:     # 确认（accepted）只允许双方立场都明确为positive且无数值/分级冲突；
426:     # 任一方neutral（无法判定方向）、同负向词频、或有分级差异，一律
427:     # 不判一致（保守升级为可见分歧，交人工/定向核实裁决）。
428:     primary_stance = _clue_stance(primary)
429:     verifier_stance = _clue_stance(verifier)
430:     if primary_stance != "positive" or verifier_stance != "positive":
431:         return False
432:     primary_grades = _grade_terms(primary)
433:     verifier_grades = _grade_terms(verifier)
434:     if primary_grades and verifier_grades and not (
435:         primary_grades & verifier_grades
436:     ):
437:         # "3级"vs"1级"类分级矛盾：词频同向也不能判一致
438:         return False
439:     return True
440: 
441: 
442: _GRADE_RE = re.compile(r"(?:^|[^0-9])([1-5])\s*级|grade\s*([1-5])", re.IGNORECASE)
443: 
444: 
445: def _grade_terms(candidate: Any) -> set[str]:
446:     """Extract explicit severity-grade mentions ("3级"/"grade 2") from a clue."""
447: 
448:     text = _clue_direction_text(candidate)
449:     if not text:
450:         return set()
451:     grades = set()
452:     for first, second in _GRADE_RE.findall(text):
453:         grades.add(first or second)
454:     return grades
455: 
实际隔离探针：
{
  "scope": "actual modules with synthetic temporary fixtures; no API/browser/provider calls",
  "cases": [
    {
      "id": "R10-keyword-risk",
      "defect_reproduced": true,
      "observed": {
        "content_sha256": "c8cdd234f1ce2936ff0a76941cd74edee5e701a4bac1dc88f587a20308c143b7",
        "ctcae_version": "",
        "meddra_version": "",
        "indication_zh": "过敏性鼻炎",
        "risk_direction_zh": "抗组胺/鼻用糖皮质激素相关嗜睡、鼻部刺激、局部感染风险",
        "anchors": [
          {
            "quote": "适应症：过敏性鼻炎",
            "where": "candidate.txt"
          }
        ],
        "unknown_visible": false
      }
    },
    {
      "id": "R10-version-vote",
      "defect_reproduced": true,
      "observed": {
        "content_sha256": "4d6cf352fd08525e77cc1dc31a9e53b3c652c07717616671701f9761fd3cfe00",
        "ctcae_version": "5.0",
        "meddra_version": "",
        "indication_zh": "",
        "risk_direction_zh": "",
        "anchors": [
          {
            "quote": "CTCAE 5.0",
            "where": "background.txt"
          },
          {
            "quote": "CTCAE 5.0",
            "where": "background.txt"
          },
          {
            "quote": "CTCAE 4.0",
            "where": "candidate.txt"
          }
        ],
        "unknown_visible": false
      }
    },
    {
      "id": "R04-opposite-predicate",
      "defect_reproduced": true,
      "observed": {
        "accepted": 1,
        "escalated": 0,
        "coverage_gap": 0,
        "unverifiable_gap": 0
      }
    },
    {
      "id": "R03-bad-binding",
      "defect_reproduced": true,
      "observed": {
        "state": "completed_with_findings",
        "artifact": "aemh-findings-facts-snapshot-001.dualvlm-full1.json"
      }
    },
    {
      "id": "R05-public-dto",
      "defect_reproduced": true,
      "observed": [
        "claims",
        "display_seq",
        "evidence_ids",
        "finding_id",
        "kind",
        "site_ref",
        "spine_ref",
        "state",
        "state_reason_zh",
        "subject_label",
        "subject_ref",
        "text",
        "title"
      ]
    },
    {
      "id": "R03-bound-missing",
      "defect_reproduced": true,
      "observed": {
        "state": "missing",
        "findings": null,
        "artifact": "missing.json",
        "error": null
      }
    },
    {
      "id": "R11-corrupt-manifest",
      "defect_reproduced": true,
      "observed": {
        "tables_after_corrupt_manifest": [
          "AE",
          "LB",
          "MH"
        ]
      }
    },
    {
      "id": "R11-unbound-snapshot",
      "defect_reproduced": true,
      "observed": {
        "snapshot_ref": "nonexistent-history",
        "run_ref": "run-facts-001"
      }
    },
    {
      "id": "R06-invalid-persisted",
      "defect_reproduced": true,
      "observed": {
        "rejected": true,
        "persisted": [
          {
            "role": "protocol",
            "candidate_id": "invalid",
            "actor": "medical_manager",
            "decided_at": "2026-09-22T14:42:22.184790"
          }
        ]
      }
    }
  ]
}
