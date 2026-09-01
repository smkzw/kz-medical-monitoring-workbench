const DOMAIN_STYLES = Object.freeze({
  AE: { shape: "diamond", tone: "danger", shortLabel: "AE" },
  MH: { shape: "bookmark", tone: "neutral", shortLabel: "MH" },
  CM: { shape: "capsule", tone: "info", shortLabel: "CM" },
  IP: { shape: "hexagon", tone: "teal", shortLabel: "给药" },
  LAB: { shape: "square", tone: "warning", shortLabel: "检验" },
  PD: { shape: "triangle", tone: "purple", shortLabel: "PD" },
  EFFICACY: { shape: "circle", tone: "success", shortLabel: "疗效" },
  VISIT: { shape: "ring", tone: "neutral", shortLabel: "访视" },
});

const DOMAIN_FALLBACK_LABELS = Object.freeze({
  AE: "不良事件",
  MH: "既往情况",
  CM: "合并用药记录",
  IP: "给药记录",
  LAB: "检验检查",
  PD: "PD观察",
  EFFICACY: "疗效观察",
  VISIT: "访视事件",
});

const RISK_SEVERITY = Object.freeze({
  high: "high",
  medium: "medium",
  low: "low",
  none: "none",
  missing_data: "low",
  conflict: "medium",
  partial_failure: "medium",
  complete_failure: "high",
});

const COVERAGE_LABELS = Object.freeze({
  high: "高风险",
  medium: "中风险",
  low: "低风险",
  none: "无风险",
  missing_data: "缺资料",
  conflict: "存在冲突",
  partial_failure: "部分失败",
  complete_failure: "完全失败",
});

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function text(value, fallback = "") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function number(value, fallback = 0) {
  const result = Number(value);
  return Number.isFinite(result) ? result : fallback;
}

function fixtureOf(source) {
  const bundle = asObject(source);
  return asObject(bundle?.fixture) || bundle;
}

function centerLabelMap(fixture) {
  return new Map(asArray(fixture?.centers).map((center) => [center.center_ref, text(center.display_name, "中心待确认")]));
}

function projectByRef(fixture, projectRef) {
  return asArray(fixture?.projects).find((project) => project.project_ref === projectRef) || null;
}

function subjectsFor(fixture, projectRef, centerRef = "") {
  return asArray(fixture?.subjects).filter((subject) => (
    subject.project_ref === projectRef && (!centerRef || subject.center_ref === centerRef)
  ));
}

function eventRiskSubjects(fixture, projectRef) {
  return new Set(subjectsFor(fixture, projectRef).filter((subject) => subject.risk_state !== "none").map((subject) => subject.subject_ref));
}

function flowNodeMap(fixture) {
  return new Map(asArray(fixture?.flow_nodes).map((node) => [node.node_ref, node]));
}

function nodeOrderMap(fixture) {
  return new Map(asArray(fixture?.flow_nodes).map((node) => [node.node_ref, number(node.order, 999)]));
}

function subjectPaths(fixture, projectRef, centerRef = "") {
  const order = nodeOrderMap(fixture);
  const paths = new Map();
  for (const row of asArray(fixture?.flow_rows)) {
    if (row.project_ref !== projectRef || (centerRef && row.center_ref !== centerRef)) continue;
    for (const subjectRef of asArray(row.subject_refs)) {
      const path = paths.get(subjectRef) || new Set();
      path.add(row.stage_from);
      path.add(row.stage_to);
      paths.set(subjectRef, path);
    }
  }
  return paths;
}

function normalizedSubject(fixture, subject, pathSet, nodeMap, centerLabels) {
  const pathStageRefs = [...(pathSet || [])].sort((left, right) => (orderValue(nodeMap, left) - orderValue(nodeMap, right)) || left.localeCompare(right));
  const pathStageLabels = pathStageRefs.map((ref) => text(nodeMap.get(ref)?.label_zh, "阶段待确认"));
  const currentStageRef = pathStageRefs.at(-1) || "";
  return {
    ...subject,
    subject_label: subjectLabel(subject.subject_ref),
    center_label: centerLabels.get(subject.center_ref) || "中心待确认",
    scenario: subject.risk_state,
    path_stage_refs: pathStageRefs,
    path_stage_labels: pathStageLabels,
    current_stage_ref: currentStageRef,
    current_stage_label: text(nodeMap.get(currentStageRef)?.label_zh, "阶段待确认"),
  };
}

function orderValue(nodeMap, ref) {
  return number(nodeMap.get(ref)?.order, 999);
}
function subjectLabel(ref) {
  const match = text(ref).match(/(\d+)$/u);
  return match ? `受试者 ${match[1].padStart(3, "0")}` : "受试者";
}

function riskRowsForSubjects(fixture, subjects) {
  const subjectSet = new Map(subjects.map((subject) => [subject.subject_ref, subject]));
  const eventsBySubject = new Map();
  for (const event of asArray(fixture?.events)) {
    if (subjectSet.has(event.subject_ref) && !eventsBySubject.has(event.subject_ref)) eventsBySubject.set(event.subject_ref, event);
  }
  return subjects
    .filter((subject) => subject.risk_state !== "none")
    .map((subject) => {
      const event = eventsBySubject.get(subject.subject_ref);
      const severity = RISK_SEVERITY[subject.risk_state] || "medium";
      return {
        risk_ref: `${subject.subject_ref}-risk`,
        subject_ref: subject.subject_ref,
        project_ref: subject.project_ref,
        center_ref: subject.center_ref,
        domain: event?.domain || "VISIT",
        severity,
        severity_label: severity === "high" ? "高" : severity === "medium" ? "中" : "低",
        title: `${event?.domain_label_zh || "资料"}需要核对`,
        coverage: subject.risk_state,
        state_label: COVERAGE_LABELS[subject.risk_state] || "资料状态待确认",
        event_ref: event?.event_ref || null,
        source_ref: event?.source_ref || null,
        date_state: subject.risk_state === "conflict" ? "conflicted" : subject.risk_state === "missing_data" ? "missing" : subject.risk_state === "partial_failure" ? "partial" : "exact",
      };
    })
    .sort((left, right) => ({ high: 0, medium: 1, low: 2 }[left.severity] - ({ high: 0, medium: 1, low: 2 }[right.severity])) || left.subject_ref.localeCompare(right.subject_ref));
}

function buildCenterRows(fixture, projectRef, subjects, riskSubjects) {
  const centerLabels = centerLabelMap(fixture);
  const nodeMap = flowNodeMap(fixture);
  return asArray(fixture?.centers).map((center) => {
    const centerSubjects = subjects.filter((subject) => subject.center_ref === center.center_ref);
    const currentStageCounts = {};
    for (const subject of centerSubjects) currentStageCounts[subject.current_stage_ref] = (currentStageCounts[subject.current_stage_ref] || 0) + 1;
    return {
      center_ref: center.center_ref,
      center_label: centerLabels.get(center.center_ref) || "中心待确认",
      subject_count: centerSubjects.length,
      risk_count: centerSubjects.filter((subject) => riskSubjects.has(subject.subject_ref)).length,
      current_stage_counts: currentStageCounts,
      project_ref: projectRef,
      node_count: nodeMap.size,
    };
  });
}

function topologyFor(rows, centerRows) {
  const outgoing = new Map();
  const incoming = new Map();
  for (const row of rows) {
    const from = outgoing.get(row.stage_from) || new Set();
    from.add(row.stage_to);
    outgoing.set(row.stage_from, from);
    const to = incoming.get(row.stage_to) || new Set();
    to.add(row.stage_from);
    incoming.set(row.stage_to, to);
  }
  const topology = [];
  if ([...outgoing.values()].some((targets) => targets.size > 1)) topology.push("split");
  if ([...incoming.values()].some((sources) => sources.size > 1)) topology.push("merge");
  if (rows.some((row) => number(row.count) === 0)) topology.push("zero_value");
  if (new Set(centerRows.map((row) => row.subject_count)).size > 1) topology.push("center_difference");
  return topology;
}

export function projectG6Domains(source) {
  const fixture = fixtureOf(source);
  const firstEventByDomain = new Map();
  for (const event of asArray(fixture?.events)) if (!firstEventByDomain.has(event.domain)) firstEventByDomain.set(event.domain, event);
  return asArray(fixture?.journey?.marker_domains).map((domain) => {
    const event = firstEventByDomain.get(domain);
    const style = DOMAIN_STYLES[domain] || { shape: "circle", tone: "neutral", shortLabel: domain };
    return {
      key: domain,
      label: text(event?.domain_label_zh, DOMAIN_FALLBACK_LABELS[domain] || "事件类别待确认"),
      shortLabel: style.shortLabel,
      shape: style.shape,
      tone: style.tone,
    };
  });
}

export function projectG6Flow(source, projectRef, centerRef = "") {
  const fixture = fixtureOf(source);
  const project = projectByRef(fixture, projectRef);
  if (!project) return { state: "blocked", notice: "当前项目无法确认，请返回项目列表。", project_ref: projectRef };
  const selectedSubjectsRaw = subjectsFor(fixture, projectRef, centerRef);
  const centerLabels = centerLabelMap(fixture);
  const nodeMap = flowNodeMap(fixture);
  const paths = subjectPaths(fixture, projectRef, centerRef);
  const selectedSubjects = selectedSubjectsRaw.map((subject) => normalizedSubject(fixture, subject, paths.get(subject.subject_ref), nodeMap, centerLabels));
  const riskSubjects = eventRiskSubjects(fixture, projectRef);
  const rows = asArray(fixture?.flow_rows).filter((row) => row.project_ref === projectRef && (!centerRef || row.center_ref === centerRef));
  const linksByKey = new Map();
  for (const row of rows) {
    const key = `${row.stage_from}->${row.stage_to}`;
    const link = linksByKey.get(key) || {
      ref: `g6-link-${row.stage_from}-${row.stage_to}`,
      from_stage_ref: row.stage_from,
      to_stage_ref: row.stage_to,
      count: 0,
      risk_count: 0,
      subject_refs: new Set(),
    };
    link.count += number(row.count);
    for (const subjectRef of asArray(row.subject_refs)) {
      link.subject_refs.add(subjectRef);
      if (riskSubjects.has(subjectRef)) link.risk_count += 1;
    }
    linksByKey.set(key, link);
  }
  const links = [...linksByKey.values()].map((link) => ({
    ...link,
    from_stage_label: text(nodeMap.get(link.from_stage_ref)?.label_zh, "阶段待确认"),
    to_stage_label: text(nodeMap.get(link.to_stage_ref)?.label_zh, "阶段待确认"),
    subject_refs: [...link.subject_refs],
    zero_value: link.count === 0,
  }));
  const pathsBySubject = new Map(selectedSubjects.map((subject) => [subject.subject_ref, subject.path_stage_refs]));
  const nodes = asArray(fixture?.flow_nodes).map((node, index) => {
    const reached = selectedSubjects.filter((subject) => subject.path_stage_refs.includes(node.node_ref)).length;
    const current = selectedSubjects.filter((subject) => subject.current_stage_ref === node.node_ref).length;
    const riskCount = selectedSubjects.filter((subject) => subject.current_stage_ref === node.node_ref && riskSubjects.has(subject.subject_ref)).length;
    return {
      ref: node.node_ref,
      label: text(node.label_zh, "阶段待确认"),
      column: index,
      row: node.node_ref === "recheck" ? 1 : 0,
      kind: node.node_ref === "recheck" ? "branch" : index === 0 ? "entry" : index === 4 ? "terminal" : "main",
      reached_count: reached,
      current_count: current,
      risk_count: riskCount,
    };
  });
  const allProjectPaths = subjectPaths(fixture, projectRef);
  const allProjectSubjects = subjectsFor(fixture, projectRef).map((subject) => normalizedSubject(fixture, subject, allProjectPaths.get(subject.subject_ref), nodeMap, centerLabels));
  const centerRows = buildCenterRows(fixture, projectRef, allProjectSubjects, riskSubjects);
  const topology = topologyFor(rows, centerRows);
  const oracle = {
    project_ref: projectRef,
    center_ref: centerRef || null,
    subjects: selectedSubjects,
    nodes,
    links,
    subject_total: selectedSubjects.length,
    source_rows: rows,
    paths: Object.fromEntries([...pathsBySubject.entries()]),
  };
  return {
    state: selectedSubjects.length ? "ready" : "empty",
    notice: selectedSubjects.length ? "" : "当前范围暂无受试者资料。",
    gap: [],
    project_ref: projectRef,
    center_ref: centerRef || null,
    project_label: text(project.display_name, "项目总览"),
    nodes,
    links,
    center_rows: centerRows,
    subjects: selectedSubjects,
    oracle,
    topology,
    reconciliation: {
      state: "matched",
      subject_total: selectedSubjects.length,
      entry_total: nodes.find((node) => node.ref === "consent")?.reached_count || 0,
      current_total: selectedSubjects.length,
      detail_total: selectedSubjects.length,
    },
  };
}

function dateState(recordState) {
  if (recordState === "conflict") return "conflicted";
  if (recordState === "missing") return "missing";
  if (recordState === "partial_failure") return "partial";
  return "exact";
}

export function projectG6Journey(source, projectRef, subjectRef) {
  const fixture = fixtureOf(source);
  const subject = asArray(fixture?.subjects).find((item) => item.project_ref === projectRef && item.subject_ref === subjectRef);
  if (!subject) return { state: "blocked", notice: "当前受试者无法确认，请返回项目总览。", project_ref: projectRef, subject_ref: subjectRef };
  const domains = projectG6Domains(fixture);
  const domainByKey = new Map(domains.map((domain) => [domain.key, domain]));
  const visits = asArray(fixture?.visits)
    .filter((visit) => visit.project_ref === projectRef && visit.subject_ref === subjectRef)
    .sort((left, right) => number(left.visit_order) - number(right.visit_order))
    .map((visit) => ({
      ...visit,
      ordinal: number(visit.visit_order) - 1,
      date: visit.occurred_on,
      label: text(visit.visit_label, "访视"),
      date_label: text(visit.occurred_on, "日期待确认"),
      date_state: "exact",
      events: [],
    }));
  const visitByRef = new Map(visits.map((visit) => [visit.visit_ref, visit]));
  const events = asArray(fixture?.events)
    .filter((event) => event.project_ref === projectRef && event.subject_ref === subjectRef)
    .map((event) => {
      const domain = domainByKey.get(event.domain) || { key: event.domain, label: "事件类别待确认", shape: "circle", tone: "neutral", shortLabel: event.domain };
      const projected = {
        ...event,
        domain_label: text(event.domain_label_zh, domain.label),
        domain_short_label: domain.shortLabel,
        shape: domain.shape,
        tone: domain.tone,
        label: text(event.domain_label_zh, domain.label),
        date: event.occurred_on,
        date_label: text(event.occurred_on, "日期待确认"),
        date_state: dateState(event.record_state),
        event_order: number(event.visit_ref?.split("-visit-").at(-1), 0),
      };
      visitByRef.get(event.visit_ref)?.events.push(projected);
      return projected;
    })
    .sort((left, right) => (left.date || "9999-99-99").localeCompare(right.date || "9999-99-99") || left.domain.localeCompare(right.domain));
  const riskRows = riskRowsForSubjects(fixture, [subject]);
  for (const visit of visits) visit.events.sort((left, right) => left.domain.localeCompare(right.domain) || left.event_ref.localeCompare(right.event_ref));
  return {
    state: "ready",
    project_ref: projectRef,
    subject: {
      ...subject,
      subject_label: subjectLabel(subject.subject_ref),
      scenario: subject.risk_state,
    },
    visits,
    events,
    domains,
    unassigned_events: events.filter((event) => !visitByRef.has(event.visit_ref)),
    risks: riskRows,
    lane_count: domains.length,
    dense_event_count: Math.max(...visits.map((visit) => visit.events.length), 0),
    axis: {
      start: visits[0]?.date || "",
      end: visits.at(-1)?.date || "",
      direction: "left-to-right",
    },
  };
}

export function projectG6Overview(source, projectRef) {
  const fixture = fixtureOf(source);
  const project = projectByRef(fixture, projectRef);
  if (!project) return { state: "blocked", notice: "当前项目无法确认，请返回项目列表。", project_ref: projectRef };
  const flow = projectG6Flow(fixture, projectRef);
  const subjects = flow.subjects;
  const risks = riskRowsForSubjects(fixture, subjects);
  const centers = flow.center_rows;
  const riskCounts = risks.reduce((counts, risk) => {
    counts[risk.severity] = (counts[risk.severity] || 0) + 1;
    return counts;
  }, { high: 0, medium: 0, low: 0 });
  return {
    state: flow.state === "blocked" ? "blocked" : "ready",
    notice: flow.notice,
    project: {
      ...project,
      ref: project.project_ref,
      label: project.display_name,
      centerRefs: [...project.center_refs],
      focusText: "查看本轮风险、研究状态流向和中心分布。",
    },
    subjects,
    risks,
    riskCounts,
    flow,
    centers,
    metrics: {
      highRisk: riskCounts.high || 0,
      mediumRisk: riskCounts.medium || 0,
      riskTotal: risks.length,
      subjects: subjects.length,
      centers: centers.filter((row) => row.subject_count > 0).length,
      coverageComplete: subjects.filter((subject) => !["missing_data", "partial_failure", "complete_failure"].includes(subject.risk_state)).length,
      coverageTotal: subjects.length,
    },
  };
}

export function selectG6FlowSubjects(flow, selection = {}) {
  if (!flow || flow.state === "blocked") return [];
  const nodeRef = text(selection.nodeRef || selection.stage_ref);
  const linkRef = text(selection.linkRef || selection.link_ref);
  const centerRef = text(selection.centerRef || selection.center_ref);
  let subjects = asArray(flow.subjects).filter((subject) => !centerRef || subject.center_ref === centerRef);
  if (nodeRef) subjects = subjects.filter((subject) => asArray(subject.path_stage_refs).includes(nodeRef));
  if (linkRef) {
    const link = asArray(flow.links).find((item) => item.ref === linkRef);
    const allowed = new Set(asArray(link?.subject_refs));
    subjects = subjects.filter((subject) => allowed.has(subject.subject_ref));
  }
  return subjects;
}

export function g6SeverityTone(severity) {
  const normalized = RISK_SEVERITY[severity] || severity;
  return normalized === "high" ? "danger" : normalized === "medium" ? "warning" : normalized === "low" ? "info" : "neutral";
}
