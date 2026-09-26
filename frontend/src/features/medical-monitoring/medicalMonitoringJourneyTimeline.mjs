/**
 * Shared horizontal timeline geometry for Patient Journey.
 * Dates are positioned on one calendar/study window; missing dates stay off-axis.
 */

const DAY_MS = 24 * 60 * 60 * 1000;
const PRIORITY = Object.freeze({ critical: 0, high: 1, medium: 2, low: 3 });

export function parseTimelineDate(value) {
  if (value === null || value === undefined || value === "") return null;
  const raw = String(value).trim();
  // R24V2-U07：UK/UNK/XX等未知日token不入前缀解析——返回null交给
  // 待确认集合，绝不补成01日。
  if (/[^\d-]/.test(raw)) return null;
  // W05-J2：尾锚——'2025-09-01-99'等数字后缀必须完整拒绝（进待确认），
  // 不再按'YYYY-MM'前缀接受。
  // W05-J2 J03：仅年月不返回精确日——'YYYY-MM'不补01当实际日，
  // 返回null交给待确认集合（精度语义由timelineDatePrecision表达）。
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(raw);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = match[3] ? Number(match[3]) : 1;
  if (!Number.isInteger(year) || month < 1 || month > 12 || day < 1 || day > 31) return null;
  const parsed = Date.UTC(year, month - 1, day);
  const checked = new Date(parsed);
  if (checked.getUTCFullYear() !== year || checked.getUTCMonth() !== month - 1 || checked.getUTCDate() !== day) return null;
  return parsed;
}

// W05-J2：精度表达——'YYYY-MM'是月精度而非'01日'实际日期。
// 返回'day'|'month'|null，供上轴区间呈现与label/aria精度标注使用。
export function timelineDatePrecision(value) {
  if (value === null || value === undefined || value === "") return null;
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return "day";
  if (/^\d{4}-\d{2}$/.test(raw)) return "month";
  return null;
}

function daysInMonthOf(iso) {
  const match = /^(\d{4})-(\d{2})$/.exec(String(iso).trim());
  if (!match) return 1;
  return new Date(Date.UTC(Number(match[1]), Number(match[2]), 0)).getUTCDate();
}

export function visitAxisDate(visit) {
  if (!visit) return null;
  const actual = visit.actual_date ?? visit.actualDate ?? null;
  if (actual) return actual;
  const dateState = visit.date_state ?? visit.dateState ?? null;
  if (dateState === "missing") return null;
  return visit.nominal_date ?? visit.nominalDate ?? null;
}

export function eventIsPendingDate(event) {
  if (!event) return true;
  const dateState = event.dateState || event.date_state;
  // W05-J2 A19：partial是注册表合法状态——无论start是否完整，部分精度
  // 一律进待确认集合，不以补01日的方式上轴。
  if (dateState === "partial") return true;
  if (event.date_precision === "partial" || event.datePrecision === "partial") return true;
  if (dateState === "missing" || dateState === "conflicted") return true;
  const start = event.start ?? event.start_date ?? null;
  if (!start) return true;
  // R24V2-U07/U08：部分精度（2025-09-UK/2025-09）与无效日期（2025-02-30）
  // 进入待确认集合——不前缀宽松解析成01日，不静默跳过。
  if (parseTimelineDate(start) == null) return true;
  return false;
}

export function eventGeometry(event) {
  if (eventIsPendingDate(event)) return "pending";
  const start = event.start ?? event.start_date ?? null;
  const end = event.end ?? event.end_date ?? null;
  if (end && start && String(end) !== String(start)) return "interval";
  // R24V2-U11：ongoing（明确持续，如"目前仍持续"标志或end_state=ongoing）
  // 与end_unknown（结束未知）不坍缩成point——几何分类保真。
  if (event.ongoing === true || event.end_state === "ongoing") return "ongoing";
  if (event.end_state === "unknown" || event.end_unknown === true) return "end_unknown";
  return "point";
}

// W05-J1 §3②：时间视窗（timeViewport）与信息密度（detailDensity）是两个
// 独立控制轴——px/day与scale范围只由viewport决定，密度只影响聚合阈值/
// collisionWidth/标签详略。切换密度不得改变scale.startMs/endMs/pxPerDay/
// width（A17不变性判据）。
export const TIME_VIEWPORTS = Object.freeze(["fit", "custom", "focus"]);
export const DETAIL_DENSITIES = Object.freeze(["compact", "standard", "detailed"]);

function pxPerDayForViewport(viewport, timeZoom) {
  if (viewport === "custom") {
    // 自选显式时间缩放：更密=5px/天，更疏=14px/天，未选层级=8px/天。
    if (timeZoom < 0) return 5;
    if (timeZoom > 0) return 14;
    return 8;
  }
  return 8;
}

export function buildTimelineScale({
  windowStart,
  windowEnd,
  visits = [],
  events = [],
  viewport = "fit",
  timeZoom = 0,
  containerWidth = null,
  focusWindow = null,
} = {}) {
  const dated = [];
  for (const visit of visits) {
    const iso = visitAxisDate(visit);
    const ms = parseTimelineDate(iso);
    if (ms != null) dated.push(ms);
  }
  for (const event of events) {
    if (eventIsPendingDate(event)) continue;
    const startMs = parseTimelineDate(event.start ?? event.start_date);
    const endMs = parseTimelineDate(event.end ?? event.end_date);
    if (startMs != null) dated.push(startMs);
    if (endMs != null) dated.push(endMs);
  }
  let startMs = parseTimelineDate(windowStart);
  let endMs = parseTimelineDate(windowEnd);
  if (startMs == null && dated.length) startMs = Math.min(...dated);
  if (endMs == null && dated.length) endMs = Math.max(...dated);
  // R24V2-U09：全无有效日期时不制造假2026时间窗——hasValidDates=false
  // 供UI显示“无有效日期”，不进入假轴。
  const hasValidDates = startMs != null && endMs != null;
  if (startMs == null) startMs = Date.UTC(2026, 0, 1);
  if (endMs == null || endMs <= startMs) endMs = startMs + 30 * DAY_MS;
  // W05-J1：聚焦视窗——scale范围收窄到选中问题周边窗口（调用方给出）；
  // 范围只由viewport决定，与密度无关。
  if (viewport === "focus" && focusWindow && typeof focusWindow === "object") {
    const focusStart = parseTimelineDate(focusWindow.start);
    const focusEnd = parseTimelineDate(focusWindow.end ?? focusWindow.start);
    if (focusStart != null) {
      startMs = focusStart;
      endMs = focusEnd != null && focusEnd >= focusStart ? focusEnd : focusStart + 30 * DAY_MS;
    }
  }
  const spanMs = Math.max(endMs - startMs, DAY_MS);
  const pad = 72;
  // R24V2-U01：默认fit——绘图区宽度=容器宽度-标签/边距，真实日期线性
  // 投影到可用宽度；px/day只作为自选显式时间缩放（viewport=custom）时的
  // 密度，不作为默认无限画布的来源。
  let pxPerDay = pxPerDayForViewport(viewport, timeZoom);
  let rawContentWidth = Math.ceil(spanMs / DAY_MS) * pxPerDay;
  // W05-J1 §3②：删除640px下限——fit=实际容器宽；窄区不再被人为撑出
  // 横向滚动。宽度未测得/过窄时保持px/day回退画布，等待ResizeObserver
  // 重新测量（等待重测职责在宿主组件）。
  let width = rawContentWidth + pad * 2;
  if (
    (viewport === "fit" || viewport === "focus")
    && typeof containerWidth === "number"
    && containerWidth > pad * 2 + 200
  ) {
    width = Math.max(1, Math.floor(containerWidth));
    rawContentWidth = width - pad * 2;
    pxPerDay = rawContentWidth / Math.ceil(spanMs / DAY_MS);
  }
  const contentWidth = width - pad * 2;

  function xFor(iso) {
    // W05-J2 A21：xFor恒返回有限number（或null=无效日期）——窗外语义改由
    // beyondFor独立通道暴露，不再混型返回{x,beyond}对象（旧混型让聚合
    // 标签渲染'[object Object]px'，且x==null拦不住对象）。
    const ms = parseTimelineDate(iso);
    if (ms == null) return null;
    const clamped = Math.min(Math.max(ms, startMs), endMs);
    return pad + ((clamped - startMs) / spanMs) * contentWidth;
  }

  // W05-J2：窗外方向独立通道——'before'|'after'|null（窗口外不伪装同日，
  // clamp只影响绘图位置，不影响语义；渲染层据此画继续符号并标注原始
  // 日期与方向）。
  function beyondFor(iso) {
    const ms = parseTimelineDate(iso);
    if (ms == null) return null;
    if (ms < startMs) return "before";
    if (ms > endMs) return "after";
    return null;
  }

  // W05-J2 A23/J09：无有效日期时不返回可被UI误用的假日期窗——
  // isos为null，UI据hasValidDates显示明确空态。
  return Object.freeze({
    windowStartIso: hasValidDates ? new Date(startMs).toISOString().slice(0, 10) : null,
    windowEndIso: hasValidDates ? new Date(endMs).toISOString().slice(0, 10) : null,
    startMs,
    endMs,
    spanMs,
    width,
    pad,
    contentWidth,
    pxPerDay,
    hasValidDates,
    xFor,
    beyondFor,
  });
}

function isPriorityRisk(severity) {
  return severity === "critical" || severity === "high" || severity === "medium";
}

/**
 * Assign vertical stack rows for overlapping marks in one swimlane.
 * Collision threshold is in px; intervals overlap when ranges intersect.
 */
export function assignLaneStacks(marks, { collisionPx = 16 } = {}) {
  const sorted = [...marks].sort((left, right) => {
    const dx = (left.x ?? 0) - (right.x ?? 0);
    if (dx) return dx;
    return (PRIORITY[left.severity] ?? 9) - (PRIORITY[right.severity] ?? 9);
  });
  const rows = [];
  return sorted.map((mark) => {
    const width = mark.geometry === "interval"
      ? Math.max(mark.width || 0, collisionPx)
      : Math.max(mark.collisionWidth || 0, collisionPx);
    const left = mark.geometry === "interval" ? mark.x ?? 0 : (mark.x ?? 0) - width / 2;
    const right = left + width;
    let row = 0;
    while (rows[row]?.some((placed) => !(right <= placed.left || left >= placed.right))) row += 1;
    if (!rows[row]) rows[row] = [];
    rows[row].push({ left, right });
    return { ...mark, stackRow: row };
  });
}

/**
 * Build per-domain dated marks and pending events for the shared journey canvas.
 * W05-J1 §3②：detailDensity决定聚合阈值——compact聚合全部低风险/常规点，
 * standard保留单点低风险，detailed全部可见；medium/high/critical任何密度
 * 下都不聚合隐藏。scale范围与px/day只由viewport/timeZoom决定。
 * 旧``zoomLevel``参数保留shim：1→custom+detailed / 0→fit+standard /
 * -1→custom+compact。
 */
export function layoutJourneyTimeline({
  domains = [],
  events = [],
  visits = [],
  risks = [],
  pendingDates = [],
  windowStart = null,
  windowEnd = null,
  viewport = null,
  timeZoom = 0,
  density = null,
  focusWindow = null,
  zoomLevel = 0,
  containerWidth = null,
} = {}) {
  const effectiveViewport = viewport || (zoomLevel === 0 ? "fit" : "custom");
  const effectiveTimeZoom = viewport ? timeZoom : zoomLevel;
  const effectiveDensity =
    density
    || (zoomLevel === 1 ? "detailed" : zoomLevel === -1 ? "compact" : "standard");
  const risksByAnchor = new Map(risks.map((risk) => [risk.riskAnchorRef || risk.risk_anchor_ref, risk]));
  const pendingRefSet = new Set(
    pendingDates.map((item) => (typeof item === "string" ? item : item?.item_ref || item?.event_ref)).filter(Boolean),
  );

  const enriched = events.map((event) => {
    const risk = (event.riskAnchorRefs || event.risk_anchor_refs || [])
      .map((ref) => risksByAnchor.get(ref))
      .filter(Boolean)
      .sort((left, right) => (PRIORITY[left.severity] ?? 9) - (PRIORITY[right.severity] ?? 9))[0] || null;
    return {
      ...event,
      visitRef: event.visitRef || event.visit_ref || "",
      risk,
      severity: risk?.severity || null,
      geometry: eventGeometry(event),
    };
  });

  const pendingEvents = enriched.filter((event) => event.geometry === "pending" || pendingRefSet.has(event.eventRef));
  const pendingEventRefs = new Set(pendingEvents.map((event) => event.eventRef));
  const datedEvents = enriched.filter((event) => !pendingEventRefs.has(event.eventRef));

  const positionedVisits = [];
  const pendingVisits = [];
  for (const visit of visits) {
    const iso = visitAxisDate(visit);
    // W05-J2 J12：非法日历日（如2025-02-30）与缺失日期同权——进待确认
    // 集合，不从可访问集合消失。
    if (!iso || parseTimelineDate(iso) == null) {
      pendingVisits.push(visit);
      continue;
    }
    positionedVisits.push({ visit, iso });
  }

  const scale = buildTimelineScale({
    windowStart,
    windowEnd,
    visits: positionedVisits.map((item) => item.visit),
    events: datedEvents,
    viewport: effectiveViewport,
    timeZoom: effectiveTimeZoom,
    containerWidth:
      effectiveViewport === "custom" ? null : containerWidth,
    focusWindow,
  });

  const visitMarks = positionedVisits.map(({ visit, iso }) => ({
    visitRef: visit.visit_ref || visit.visitRef,
    iso,
    x: scale.xFor(iso),
    beyond: scale.beyondFor(iso),
    visit,
  })).filter((mark) => mark.x != null);

  const lanes = domains.map((domain) => {
    const domainKey = domain.domain;
    const domainEvents = datedEvents.filter((event) => event.domain === domainKey);
    const priorityEvents = domainEvents.filter((event) => isPriorityRisk(event.severity));
    const otherEvents = domainEvents.filter((event) => !isPriorityRisk(event.severity));

    const visible = effectiveDensity === "detailed" ? [...domainEvents] : [...priorityEvents];
    const aggregates = [];
    if (effectiveDensity !== "detailed") {
      const buckets = new Map();
      for (const event of otherEvents) {
        const bucket = String(event.start || event.start_date || "").slice(0, 10) || "undated";
        if (!buckets.has(bucket)) buckets.set(bucket, []);
        buckets.get(bucket).push(event);
      }
      for (const [bucket, group] of buckets) {
        // Standard密度保留单点低风险；compact密度聚合全部低风险/常规点。
        if (effectiveDensity === "standard" && group.length === 1) {
          visible.push(group[0]);
          continue;
        }
        // A21：xFor恒为有限number——聚合坐标不再出现'[object Object]px'。
        const x = scale.xFor(group[0].start || group[0].start_date);
        if (x == null || !Number.isFinite(x)) continue;
        aggregates.push({
          aggregateKey: `${domainKey}:${bucket}`,
          domain: domainKey,
          count: group.length,
          x,
          label: `另有 ${group.length} 条低风险或常规记录`,
          eventRefs: group.map((event) => event.eventRef),
        });
      }
    }

    const marks = [];
    for (const event of visible) {
      const startIso = event.start || event.start_date;
      const endIso = event.end || event.end_date || startIso;
      // W05-J2 A21：坐标恒为有限number；窗外方向走独立通道。
      const x0 = scale.xFor(startIso);
      if (x0 == null || !Number.isFinite(x0)) continue;
      const x1 = scale.xFor(endIso);
      // 区间首尾越界分别保留标志（03_FRONTEND_DELTA §24）：
      // before=整个开始于窗前，after=结束于窗后，渲染层画继续符号。
      const beyondStart = scale.beyondFor(startIso);
      const beyondEnd = scale.beyondFor(endIso);
      const beyond = beyondStart ?? beyondEnd;
      const geometry = event.geometry;
      const startPrecision = timelineDatePrecision(startIso);
      // 月精度起点上轴呈现为当月区间（宽度=当月天数×px/day）——不以
      // 01日为实际日；ongoing/end_unknown呈开放条形（延伸到轴右端），
      // 与point区分（A22）。
      let width = 0;
      if (geometry === "interval") {
        width = Math.max(10, (x1 ?? x0) - x0);
      } else if (geometry === "ongoing" || geometry === "end_unknown") {
        width = Math.max(10, scale.pad + scale.contentWidth - x0);
      } else if (startPrecision === "month") {
        width = Math.max(10, daysInMonthOf(startIso) * scale.pxPerDay);
      }
      marks.push({
        eventRef: event.eventRef,
        domain: domainKey,
        geometry,
        x: x0,
        beyondStart,
        beyondEnd,
        beyond,
        width,
        // 密度只影响碰撞宽度（标签详略的空间预算），不影响px/day。
        collisionWidth: event.risk
          ? (effectiveDensity === "detailed" ? 220 : effectiveDensity === "standard" ? 90 : 40)
          : (effectiveDensity === "detailed" ? 150 : 24),
        event,
        severity: event.severity,
        risk: event.risk,
      });
    }

    const stacked = assignLaneStacks(marks);
    const maxStack = stacked.reduce((max, mark) => Math.max(max, mark.stackRow), 0);
    const aggregatedCount = aggregates.reduce((sum, item) => sum + item.count, 0);
    return {
      domain: domainKey,
      encoding: domain,
      marks: stacked,
      aggregates,
      eventCount: domainEvents.length,
      riskAnchorCount: domainEvents.reduce((count, event) => count + (event.riskAnchorRefs?.length || event.risk_anchor_refs?.length || 0), 0),
      hiddenLowRiskCount: aggregatedCount,
      stackRows: Math.max(1, maxStack + 1),
    };
  });

  return Object.freeze({
    scale,
    visitMarks,
    pendingVisits,
    pendingEvents,
    pendingDates,
    lanes,
    datedEventCount: datedEvents.length,
    pendingEventCount: pendingEvents.length,
  });
}
