/**
 * Slice 4 Patient Journey — offline file:// viewer.
 * Consumes window.MM_R1_JOURNEY + read-only window.MM_R1_DATA.
 * No inline mock data. Read-only browsing only.
 */
(function () {
  "use strict";

  var LANE_ORDER = [
    { id: "exposure", label: "研究药物暴露" },
    { id: "ae_sae", label: "不良事件 / 症状" },
    { id: "mh_cm", label: "病史 / 合并用药 / 住院" },
    { id: "labs", label: "实验室 / 检查" }
  ];

  var SEVERITY_RANK = { severe: 4, high: 3, medium: 2, moderate: 2, mild: 1, low: 1 };
  var SEVERITY_LABEL = {
    severe: "严重", high: "高", medium: "中", moderate: "中", mild: "轻微", low: "低"
  };
  var RISK_TYPE_LABEL = {
    potential_unreported_ae: "疑似 AE 漏报",
    potential_unreported_mh: "疑似 MH 漏报"
  };
  var CONCEPT_LABEL = {
    fatigue: "疲乏",
    headache: "头痛",
    hypertension: "高血压",
    "routine marker": "常规标志物",
    pending_symptom: "日期信息不完整的症状记录"
  };
  var EVENT_TYPE_LABEL = {
    ae: "不良事件",
    mh: "既往病史",
    symptom: "症状",
    cm_indication: "合并用药",
    laboratory: "实验室检查",
    hospitalization: "住院",
    ip_exposure: "研究药物暴露"
  };
  var CLINICAL_DOMAIN = {
    ae: { label: "AE", marker: "AE" },
    mh: { label: "MH", marker: "MH" },
    cm: { label: "CM/合并用药", marker: "CM" },
    ip: { label: "IP给药", marker: "IP" },
    lab: { label: "实验室/检查", marker: "检" },
    hospitalization: { label: "住院/操作", marker: "住" },
    symptom: { label: "症状/体征线索", marker: "症" },
    other: { label: "其他记录", marker: "其" }
  };
  var EVENT_TYPE_DOMAIN = {
    ae: "ae",
    mh: "mh",
    cm: "cm",
    cm_indication: "cm",
    concomitant_medication: "cm",
    ip_exposure: "ip",
    ip_administration: "ip",
    laboratory: "lab",
    vital_sign: "lab",
    ecg: "lab",
    examination: "lab",
    hospitalization: "hospitalization",
    procedure: "hospitalization",
    symptom: "symptom"
  };
  var RISK_TYPE_DOMAIN = {
    potential_unreported_ae: "ae",
    ae_assessment: "ae",
    sae_aesi_review: "ae",
    potential_unreported_mh: "mh",
    mh_eligibility: "mh",
    prohibited_cm: "cm",
    restricted_cm: "cm",
    cm_indication_mismatch: "cm",
    ip_dosing_deviation: "ip",
    ip_exposure_gap: "ip",
    ip_compliance: "ip",
    laboratory_abnormality: "lab",
    vital_sign_abnormality: "lab",
    ecg_abnormality: "lab",
    hospitalization_review: "hospitalization",
    procedure_review: "hospitalization",
    hospitalization_safety: "hospitalization",
    symptom_review: "symptom",
    vital_sign_symptom_review: "symptom"
  };
  var EVENT_LEGEND_DOMAINS = ["ae", "mh", "cm", "ip", "lab", "hospitalization", "symptom"];
  var RISK_LEGEND_DOMAINS = ["ae", "mh", "cm", "ip", "lab", "hospitalization", "symptom"];
  var TABLE_LABEL = {
    ae: "不良事件表",
    mh: "既往病史表",
    symptoms: "症状表",
    concomitant_medications: "合并用药表",
    labs: "实验室检查表",
    exposure: "暴露记录",
    hospitalization: "住院记录",
    visit_schedule: "访视计划"
  };
  var VISIT_TYPE_LABEL = {
    planned: "计划访视",
    actual: "实际访视",
    unscheduled: "非计划访视"
  };
  var GEOMETRY_LABEL = {
    point: "单日记录",
    interval: "持续记录（起止日期完整）",
    interval_open: "持续记录（仍在持续）",
    pending: "日期信息不完整"
  };
  var DATE_STATUS_LABEL = {
    complete: "日期完整",
    missing: "日期缺失",
    partial: "部分日期",
    conflicted: "日期冲突"
  };

  var state = {
    journey: null,
    slice3: null,
    subjectId: "",
    siteId: "",
    tab: "journey",
    axisMode: "actual_date",
    windowStart: "",
    windowEnd: "",
    defaultStart: "",
    defaultEnd: "",
    pxPerDay: 14,
    riskFirst: true,
    selectedEventId: null,
    selectedRiskId: null,
    focusBeforeDrawer: null,
    focusRestore: null,
    drawerOpen: false
  };

  var els = {};
  var DAY_MS = 86400000;

  function $(id) { return document.getElementById(id); }

  function text(v) { return v == null ? "" : String(v); }

  function escapeHtml(v) {
    return text(v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function mapped(map, value, fallback) {
    var raw = text(value);
    var key = raw.toLowerCase();
    return map[key] || map[raw] || fallback || raw || "—";
  }

  function eventDisplayLabel(ev) {
    if (!ev) return "记录";
    if (ev.geometry === "pending" || ev.placement === "pending_date_surface") {
      return "日期信息不完整的症状记录";
    }
    return text(ev.label_zh) || mapped(EVENT_TYPE_LABEL, ev.event_type);
  }

  function riskDisplayLabel(risk) {
    if (!risk) return "风险提示";
    var type = mapped(RISK_TYPE_LABEL, risk.risk_type, "风险提示");
    var concept = mapped(CONCEPT_LABEL, risk.concept, text(risk.concept));
    return concept ? (type + "：" + concept) : type;
  }

  function audienceCopy(value) {
    return text(value)
      .replace(/Patient Journey/g, "受试者医学旅程");
  }

  function normalizedDomain(value) {
    var key = text(value).toLowerCase();
    return CLINICAL_DOMAIN[key] ? key : "other";
  }

  function eventDomain(ev) {
    if (!ev) return "other";
    return normalizedDomain(ev.clinical_domain || EVENT_TYPE_DOMAIN[text(ev.event_type).toLowerCase()]);
  }

  function riskDomain(risk) {
    if (!risk) return "other";
    if (risk.clinical_domain) return normalizedDomain(risk.clinical_domain);
    var type = text(risk.risk_type).toLowerCase();
    if (RISK_TYPE_DOMAIN[type]) return RISK_TYPE_DOMAIN[type];
    if (/(^|_)mh(_|$)|medical_history/.test(type)) return "mh";
    if (/(^|_)cm(_|$)|concomitant|medication/.test(type)) return "cm";
    if (/(^|_)ip(_|$)|dose|dosing|exposure|compliance/.test(type)) return "ip";
    if (/lab|laboratory|vital|ecg|examination/.test(type)) return "lab";
    if (/hospital|procedure|operation|surgery/.test(type)) return "hospitalization";
    if (/symptom|sign|complaint/.test(type)) return "symptom";
    if (/(^|_)ae(_|$)|adverse|safety/.test(type)) return "ae";
    return "other";
  }

  function domainInfo(domain) {
    return CLINICAL_DOMAIN[normalizedDomain(domain)];
  }

  function parseDate(iso) {
    if (!iso || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null;
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }

  function daysBetween(a, b) {
    var da = parseDate(a);
    var db = parseDate(b);
    if (!da || !db) return 0;
    return Math.round((db.getTime() - da.getTime()) / DAY_MS);
  }

  function addDays(iso, n) {
    var d = parseDate(iso);
    if (!d) return iso;
    d.setUTCDate(d.getUTCDate() + n);
    var y = d.getUTCFullYear();
    var m = String(d.getUTCMonth() + 1).padStart(2, "0");
    var day = String(d.getUTCDate()).padStart(2, "0");
    return y + "-" + m + "-" + day;
  }

  function clampDate(iso, start, end) {
    if (!iso) return iso;
    if (start && iso < start) return start;
    if (end && iso > end) return end;
    return iso;
  }

  function severityRank(v) {
    return SEVERITY_RANK[String(v || "").toLowerCase()] || 0;
  }

  function showError(message) {
    els.error.hidden = false;
    els.shell.hidden = true;
    els.errorBody.textContent = message;
  }

  function validate() {
    var j = window.MM_R1_JOURNEY;
    var s3 = window.MM_R1_DATA;
    if (!j || typeof j !== "object") {
      return { ok: false, reason: "缺少旅程数据包（window.MM_R1_JOURNEY）。" };
    }
    if (!s3 || typeof s3 !== "object") {
      return { ok: false, reason: "缺少 Slice 3 数据包（window.MM_R1_DATA）。请确认相对脚本路径可用。" };
    }
    if (j.schema_version !== "patient_journey_r1_slice4_v1") {
      return { ok: false, reason: "旅程数据合同版本不匹配。" };
    }
    if (!j.subject_journey || !j.shared_view_state) {
      return { ok: false, reason: "旅程数据包缺少受试者投影或共享视图状态。" };
    }
    var sid = j.default_subject_id || j.shared_view_state.subject_id;
    if (sid !== "SYNTHETIC-SUBJECT-001") {
      return { ok: false, reason: "默认受试者不是 SYNTHETIC-SUBJECT-001。" };
    }
    if (j.spine_id !== j.subject_journey.spine_id || j.spine_id !== j.shared_view_state.spine_id) {
      return { ok: false, reason: "旅程共享时间脊不一致。" };
    }
    var profile = s3.subject_profiles && s3.subject_profiles[sid];
    var timeline = s3.subject_timelines && s3.subject_timelines[sid];
    if (!profile || !timeline) {
      return { ok: false, reason: "缺少默认受试者的趋势或事件数据。" };
    }
    if (profile.temporal_spine_id !== j.spine_id || timeline.temporal_spine_id !== j.spine_id) {
      return { ok: false, reason: "旅程与 Slice 3 时间脊未能对齐。" };
    }
    return { ok: true, journey: j, slice3: s3 };
  }

  function journey() { return state.journey.subject_journey; }

  function axisRange() {
    return {
      start: state.windowStart || state.defaultStart,
      end: state.windowEnd || state.defaultEnd
    };
  }

  function canvasWidth() {
    var r = axisRange();
    var days = Math.max(1, daysBetween(r.start, r.end));
    return Math.max(720, 120 + days * state.pxPerDay);
  }

  function xForDate(iso) {
    var r = axisRange();
    if (!iso) return null;
    var d = clampDate(iso, r.start, r.end);
    var offset = daysBetween(r.start, d);
    return 120 + offset * state.pxPerDay;
  }

  function visitAxisDate(v) {
    if (!v) return null;
    if (v.visit_type === "planned") return v.nominal_date;
    return v.actual_date || v.nominal_date;
  }

  /**
   * Group planned+actual rows that share the same visit_code into one spatial
   * visit node. Unscheduled visits remain distinct nodes. No hard-coded codes.
   */
  function groupVisitNodes(visits) {
    var nodes = [];
    var byCode = Object.create(null);
    (visits || []).forEach(function (v) {
      if (!v) return;
      if (v.visit_type === "unscheduled") {
        nodes.push({
          kind: "unscheduled",
          visit_code: v.visit_code || "UNS",
          planned: null,
          actual: null,
          unscheduled: v,
          order: v.order != null ? v.order : 9999
        });
        return;
      }
      var code = v.visit_code || v.visit_id || ("visit_" + nodes.length);
      var node = byCode[code];
      if (!node) {
        node = {
          kind: "coded",
          visit_code: code,
          planned: null,
          actual: null,
          unscheduled: null,
          order: v.order != null ? v.order : 9999
        };
        byCode[code] = node;
        nodes.push(node);
      }
      if (v.visit_type === "planned") node.planned = v;
      else if (v.visit_type === "actual") node.actual = v;
      else node.actual = node.actual || v;
      var ord = v.order != null ? v.order : node.order;
      if (ord < node.order) node.order = ord;
    });
    nodes.sort(function (a, b) {
      var da = visitNodeAxisDate(a) || "";
      var db = visitNodeAxisDate(b) || "";
      if (da !== db) return da < db ? -1 : 1;
      return (a.order || 0) - (b.order || 0);
    });
    return nodes;
  }

  function visitNodeAxisDate(node) {
    if (!node) return null;
    if (node.kind === "unscheduled") return visitAxisDate(node.unscheduled);
    // Prefer actual occurrence on the shared axis; fall back to planned nominal.
    if (node.actual) return visitAxisDate(node.actual);
    if (node.planned) return visitAxisDate(node.planned);
    return null;
  }

  function visitNodePrimaryType(node) {
    if (!node) return "";
    if (node.kind === "unscheduled") return "unscheduled";
    if (node.actual && node.planned) return "paired";
    if (node.actual) return "actual";
    if (node.planned) return "planned";
    return "";
  }

  function visitNodeLabelZh(node) {
    if (!node) return "";
    var src = node.actual || node.planned || node.unscheduled;
    return (src && (src.label_zh || src.visit_code)) || node.visit_code || "访视";
  }

  function formatVisitDateLine(iso, studyDay, prefix, compact) {
    if (state.axisMode === "study_day") {
      if (studyDay != null && studyDay !== "") return prefix + labelStudyDay(studyDay);
      return prefix + (iso || "—");
    }
    var shown = iso || "—";
    if (compact && iso && iso.length >= 10) shown = iso.slice(5);
    return prefix + shown;
  }

  function visitNodeAccessibleTitle(node) {
    var parts = [];
    var code = node.visit_code || "访视";
    if (node.kind === "unscheduled") {
      var u = node.unscheduled || {};
      parts.push(mapped(VISIT_TYPE_LABEL, "unscheduled") + " · " + (u.label_zh || code));
      if (u.actual_date) parts.push("实际 " + u.actual_date);
      return parts.join("；");
    }
    parts.push(code + " · " + visitNodeLabelZh(node));
    if (node.planned) {
      parts.push(
        mapped(VISIT_TYPE_LABEL, "planned") + " " + (node.planned.nominal_date || "—")
      );
    }
    if (node.actual) {
      parts.push(
        mapped(VISIT_TYPE_LABEL, "actual") + " " + (node.actual.actual_date || "—")
      );
    }
    return parts.join("；");
  }

  function eventAxisDate(ev) {
    if (ev.geometry === "pending" || ev.placement === "pending_date_surface") return null;
    if (ev.geometry === "interval" || ev.geometry === "interval_open") {
      return ev.start_date || ev.actual_date;
    }
    return ev.actual_date;
  }

  function eventInWindow(ev) {
    if (ev.geometry === "pending" || ev.placement === "pending_date_surface") return true;
    var r = axisRange();
    if (ev.geometry === "interval" || ev.geometry === "interval_open") {
      var start = ev.start_date || ev.actual_date;
      var end = ev.end_date || (ev.open_ended ? r.end : start);
      if (!start) return false;
      if (end && end < r.start) return false;
      if (start > r.end) return false;
      return true;
    }
    var d = ev.actual_date;
    if (!d) return false;
    return d >= r.start && d <= r.end;
  }

  function riskInWindow(risk) {
    var d = risk.anchor_actual_date;
    if (!d) return true;
    var r = axisRange();
    return d >= r.start && d <= r.end;
  }

  function labelStudyDay(day) {
    if (day == null || day === "") return "—";
    return "研究第 " + day + " 天";
  }

  function axisCaption(dateIso, studyDay) {
    if (state.axisMode === "study_day") return labelStudyDay(studyDay);
    return dateIso || "日期未知";
  }

  function sourceLocatorLabel(locator) {
    var parts = String(locator || "").split("|");
    var snapshot = "";
    var table = "";
    var row = "";
    parts.forEach(function (part) {
      if (part.indexOf("snapshot=") === 0) snapshot = part.slice(9);
      if (part.indexOf("journey=") === 0) snapshot = "旅程合成";
      if (part.indexOf("table=") === 0) table = part.slice(6);
      if (part.indexOf("row=") === 0) row = part.slice(4);
    });
    var snapLabel = "当前数据批次";
    var up = String(snapshot).toUpperCase();
    if (up.indexOf("N1") >= 0) snapLabel = "本次全量数据";
    else if (snapshot === "旅程合成" || up.indexOf("JOURNEY") >= 0) snapLabel = "旅程合成记录";
    else if (up.indexOf("N") >= 0) snapLabel = "上次全量数据";
    return snapLabel + " · " + mapped(TABLE_LABEL, table, "数据表") + " · 记录 " + (row || "—");
  }

  function findEvent(eventId) {
    var list = journey().events || [];
    for (var i = 0; i < list.length; i += 1) {
      if (list[i].event_id === eventId) return list[i];
    }
    return null;
  }

  function findRisk(riskId) {
    var list = journey().risks || [];
    for (var i = 0; i < list.length; i += 1) {
      if (list[i].risk_id === riskId || list[i].instance_id === riskId) return list[i];
    }
    return null;
  }

  function riskForEvent(eventId) {
    var list = journey().risks || [];
    for (var i = 0; i < list.length; i += 1) {
      if (list[i].anchor_event_id === eventId) return list[i];
    }
    return null;
  }

  function queryForRisk(risk) {
    if (!risk) return null;
    var queries = journey().queries || [];
    var i;
    for (i = 0; i < queries.length; i += 1) {
      var q = queries[i];
      if ((risk.query_ids || []).indexOf(q.query_id) >= 0) return q;
      var keys = q.risk_identity_keys || [];
      if (risk.identity_key && keys.indexOf(risk.identity_key) >= 0) return q;
      if ((q.risk_ids || []).indexOf(risk.risk_id) >= 0) return q;
    }
    // Prefer Slice 3 query text when bound to same subject
    var s3q = (state.slice3.queries || []).filter(function (item) {
      return item.subject_id === state.subjectId;
    });
    for (i = 0; i < s3q.length; i += 1) {
      var keys2 = s3q[i].risk_identity_keys || [];
      if (risk.identity_key && keys2.indexOf(risk.identity_key) >= 0) return s3q[i];
      if ((s3q[i].query_id && (risk.query_ids || []).indexOf(s3q[i].query_id) >= 0)) return s3q[i];
    }
    return null;
  }

  function slice3Row(locator) {
    var rows = state.slice3.source_rows || {};
    return rows[locator] || null;
  }

  function headerMeta() {
    var cutoff = state.windowEnd || state.defaultEnd;
    els.headerMeta.innerHTML =
      "<p><strong>受试者</strong> " + escapeHtml(state.subjectId) + "</p>" +
      "<p><strong>中心</strong> " + escapeHtml(state.siteId) + "</p>" +
      "<p><strong>当前时间窗截止</strong> " + escapeHtml(cutoff) + "</p>" +
      "<p>合成演示数据</p>";
  }

  function legendHtml() {
    function item(domain, kind) {
      var info = domainInfo(domain);
      var label = kind === "risk" ? info.label + "相关风险" : info.label;
      return "<li class=\"pj-legend__item\" data-domain=\"" + escapeHtml(domain) +
        "\" data-kind=\"" + escapeHtml(kind) + "\"><span class=\"pj-domain-symbol\" data-domain=\"" +
        escapeHtml(domain) + "\" data-kind=\"" + escapeHtml(kind) +
        "\" aria-hidden=\"true\"><span>" + escapeHtml(info.marker) + "</span></span>" +
        escapeHtml(label) + "</li>";
    }
    return "<div class=\"pj-legend-panel\" aria-label=\"事件与风险标记说明\">" +
      "<div class=\"pj-legend-group\"><p class=\"pj-legend-group__title\">事件记录</p><ul class=\"pj-legend\">" +
      EVENT_LEGEND_DOMAINS.map(function (domain) { return item(domain, "event"); }).join("") +
      "</ul></div>" +
      "<div class=\"pj-legend-group\"><p class=\"pj-legend-group__title\">风险提示</p><ul class=\"pj-legend\">" +
      RISK_LEGEND_DOMAINS.map(function (domain) { return item(domain, "risk"); }).join("") +
      "<li class=\"pj-legend__item pj-legend__item--severity\">风险等级：<strong>高</strong><strong>中</strong><strong>低</strong></li>" +
      "</ul></div></div>";
  }

  function setTab(tab) {
    state.tab = tab;
    ["journey", "metrics", "events", "risks"].forEach(function (name) {
      var btn = $("pj-tab-" + name);
      var panel = $("pj-panel-" + name);
      var selected = name === tab;
      if (btn) btn.setAttribute("aria-selected", selected ? "true" : "false");
      if (panel) panel.hidden = !selected;
    });
  }

  function selectIdentity(opts) {
    opts = opts || {};
    if (opts.eventId !== undefined) state.selectedEventId = opts.eventId;
    if (opts.riskId !== undefined) {
      state.selectedRiskId = opts.riskId || null;
    }
    if (opts.eventId && opts.riskId === undefined) {
      var linked = riskForEvent(opts.eventId);
      state.selectedRiskId = linked ? linked.risk_id : null;
    }
    if (opts.riskId && !opts.eventId) {
      var risk = findRisk(opts.riskId);
      state.selectedEventId = risk ? risk.anchor_event_id : state.selectedEventId;
    }
  }

  function isSelectedEvent(eventId) {
    return !!eventId && eventId === state.selectedEventId;
  }

  function isSelectedRisk(riskId) {
    return !!riskId && riskId === state.selectedRiskId;
  }

  function isCrossHighlighted(eventId, riskId) {
    if (riskId && isSelectedRisk(riskId)) return true;
    if (eventId && isSelectedEvent(eventId)) return true;
    if (eventId && state.selectedRiskId) {
      var risk = findRisk(state.selectedRiskId);
      if (risk && risk.anchor_event_id === eventId) return true;
    }
    return false;
  }

  function shouldShowEvent(ev) {
    if (ev.placement === "pending_date_surface" || ev.geometry === "pending") {
      return false; // pending surface is rendered separately
    }
    if (!eventInWindow(ev)) return false;
    if (!state.riskFirst) return true;
    // Risk-first keeps structure + medium/high anchors; collapses low-only candidates unless selected
    if (ev.record_class === "candidate") {
      var linked = riskForEvent(ev.event_id);
      if (linked && severityRank(linked.severity) >= 2) return true;
      if (isSelectedEvent(ev.event_id) || isSelectedRisk(linked && linked.risk_id)) return true;
      var cand = null;
      (journey().candidates || []).forEach(function (c) {
        if (c.anchor_event_id === ev.event_id) cand = c;
      });
      if (cand && severityRank(cand.severity) < 2 && !linked) return false;
    }
    return true;
  }

  function renderVisitRuler(width) {
    var r = axisRange();
    var nodes = groupVisitNodes(journey().visits || []).filter(function (node) {
      var d = visitNodeAxisDate(node);
      if (!d) return false;
      return d >= r.start && d <= r.end;
    });
    var html = "<div class=\"pj-sticky-ruler\" style=\"width:" + width + "px\">";
    nodes.forEach(function (node) {
      var d = visitNodeAxisDate(node);
      var x = xForDate(d);
      if (x == null) return;
      var primaryType = visitNodePrimaryType(node);
      var dateHtml = "";
      if (node.kind === "unscheduled") {
        var u = node.unscheduled || {};
        dateHtml = "<span class=\"pj-visit-mark__date\">" +
          escapeHtml(formatVisitDateLine(u.actual_date, u.study_day, "")) +
          "</span>";
      } else if (node.planned && node.actual) {
        dateHtml =
          "<span class=\"pj-visit-mark__dates\">" +
          "<span class=\"pj-visit-mark__date pj-visit-mark__date--planned\">" +
          escapeHtml(formatVisitDateLine(node.planned.nominal_date, node.planned.study_day, "计划 ", true)) +
          "</span>" +
          "<span class=\"pj-visit-mark__date pj-visit-mark__date--actual\">" +
          escapeHtml(formatVisitDateLine(node.actual.actual_date, node.actual.study_day, "实际 ", true)) +
          "</span></span>";
      } else if (node.actual) {
        dateHtml = "<span class=\"pj-visit-mark__date pj-visit-mark__date--actual\">" +
          escapeHtml(formatVisitDateLine(node.actual.actual_date, node.actual.study_day, "实际 ", false)) +
          "</span>";
      } else if (node.planned) {
        dateHtml = "<span class=\"pj-visit-mark__date pj-visit-mark__date--planned\">" +
          escapeHtml(formatVisitDateLine(node.planned.nominal_date, node.planned.study_day, "计划 ", false)) +
          "</span>";
      }
      html += "<div class=\"pj-visit-mark\" data-type=\"" + escapeHtml(primaryType) +
        "\" data-visit-code=\"" + escapeHtml(node.visit_code || "") +
        "\" style=\"left:" + x + "px\" title=\"" +
        escapeHtml(visitNodeAccessibleTitle(node)) + "\">" +
        "<span class=\"pj-visit-mark__tick\" aria-hidden=\"true\"></span>" +
        "<span class=\"pj-visit-mark__code\">" + escapeHtml(node.visit_code || "访视") + "</span>" +
        dateHtml + "</div>";
    });
    html += "</div>";
    return html;
  }

  function renderPhaseBands(width) {
    var bands = journey().phase_bands || [];
    var r = axisRange();
    var html = "<div class=\"pj-phase-band-row\" style=\"width:" + width + "px\" aria-label=\"研究阶段\">";
    bands.forEach(function (b) {
      if (!b.start_date || !b.end_date) return;
      if (b.end_date < r.start || b.start_date > r.end) return;
      var start = clampDate(b.start_date, r.start, r.end);
      var end = clampDate(b.end_date, r.start, r.end);
      var x1 = xForDate(start);
      var x2 = xForDate(end);
      var w = Math.max(8, x2 - x1);
      html += "<div class=\"pj-phase-band\" data-phase=\"" + escapeHtml(b.phase_id) +
        "\" style=\"left:" + x1 + "px;width:" + w + "px\">" +
        escapeHtml(b.label_zh || "阶段") + "</div>";
    });
    html += "</div>";
    return html;
  }

  function guideLines(width) {
    var visits = journey().visits || [];
    var html = "";
    visits.forEach(function (v) {
      if (v.visit_type === "planned") return;
      var d = visitAxisDate(v);
      if (!d) return;
      var r = axisRange();
      if (d < r.start || d > r.end) return;
      var x = xForDate(d);
      html += "<div class=\"pj-guide\" style=\"left:" + x + "px;height:100%\"></div>";
    });
    return html;
  }

  function markerButton(opts) {
    var selected = isCrossHighlighted(opts.eventId, opts.riskId);
    var cls = "pj-marker" + (selected ? " is-selected is-cross" : "");
    var markerKind = opts.markerKind || (opts.shape === "established_risk" ? "risk" : "event");
    var domain = normalizedDomain(opts.domain);
    var info = domainInfo(domain);
    var severityText = markerKind === "risk" ? mapped(SEVERITY_LABEL, opts.severity, "") : "";
    return "<button type=\"button\" class=\"" + cls +
      "\" data-shape=\"" + escapeHtml(opts.shape) +
      "\" data-marker-kind=\"" + escapeHtml(markerKind) +
      "\" data-domain=\"" + escapeHtml(domain) +
      "\" data-severity=\"" + escapeHtml(opts.severity || "") +
      "\" data-event=\"" + escapeHtml(opts.eventId || "") +
      "\" data-risk=\"" + escapeHtml(opts.riskId || "") +
      "\" data-action=\"select-open\" style=\"left:" + opts.x + "px\" title=\"" +
      escapeHtml(opts.title) + "\" aria-label=\"" + escapeHtml(opts.title) + "\">" +
      "<span class=\"pj-marker__shape\" aria-hidden=\"true\"><span class=\"pj-marker__abbr\">" +
      escapeHtml(info.marker) + "</span></span>" +
      (severityText ? "<span class=\"pj-marker__severity\" aria-hidden=\"true\">" + escapeHtml(severityText) + "</span>" : "") +
      "</button>";
  }

  function intervalEl(opts) {
    var selected = isCrossHighlighted(opts.eventId, opts.riskId);
    var cls = "pj-interval" + (selected ? " is-selected is-cross" : "");
    return "<button type=\"button\" class=\"" + cls +
      "\" data-class=\"" + escapeHtml(opts.recordClass || "") +
      "\" data-domain=\"" + escapeHtml(normalizedDomain(opts.domain)) +
      "\" data-marker-kind=\"event\"" +
      "\" data-open=\"" + (opts.openEnded ? "true" : "false") +
      "\" data-event=\"" + escapeHtml(opts.eventId || "") +
      "\" data-risk=\"" + escapeHtml(opts.riskId || "") +
      "\" data-action=\"select-open\" style=\"left:" + opts.x + "px;width:" + opts.w +
      "px\" title=\"" + escapeHtml(opts.title) + "\" aria-label=\"" +
      escapeHtml(opts.title) + "\"></button>";
  }

  function renderLanes(width) {
    var events = (journey().events || []).filter(shouldShowEvent);
    var risks = (journey().risks || []).filter(riskInWindow);
    var r = axisRange();
    var html = "<div class=\"pj-lanes\" style=\"width:" + width + "px;position:relative\">" + guideLines(width);

    LANE_ORDER.forEach(function (lane) {
      html += "<div class=\"pj-lane\" data-lane=\"" + escapeHtml(lane.id) +
        "\" style=\"position:relative\"><span class=\"pj-lane__label\">" +
        escapeHtml(lane.label) + "</span>";

      events.filter(function (ev) {
        return ev.lane === lane.id && ev.placement !== "pending_date_surface";
      }).forEach(function (ev) {
        var domain = eventDomain(ev);
        var title = domainInfo(domain).label + " · " + (ev.label_zh || mapped(EVENT_TYPE_LABEL, ev.event_type)) +
          " · " + mapped(GEOMETRY_LABEL, ev.geometry);
        var linkedRisk = riskForEvent(ev.event_id);

        if (ev.geometry === "interval" || ev.geometry === "interval_open") {
          var start = ev.start_date || ev.actual_date;
          if (!start) return;
          var end = ev.end_date;
          if (ev.open_ended || !end) end = r.end;
          var x1 = xForDate(clampDate(start, r.start, r.end));
          var x2 = xForDate(clampDate(end, r.start, r.end));
          var w = Math.max(12, x2 - x1);
          html += intervalEl({
            x: x1,
            w: w,
            eventId: ev.event_id,
            riskId: linkedRisk ? linkedRisk.risk_id : "",
            title: title,
            openEnded: !!ev.open_ended || ev.geometry === "interval_open",
            recordClass: ev.record_class,
            domain: domain
          });
          // point marker at start for keyboard hit clarity
          html += markerButton({
            x: x1,
            eventId: ev.event_id,
            riskId: linkedRisk ? linkedRisk.risk_id : "",
            shape: ev.shape || "fact",
            title: title,
            severity: linkedRisk ? linkedRisk.severity : "",
            markerKind: "event",
            domain: domain
          });
        } else {
          var d = eventAxisDate(ev);
          if (!d) return;
          var x = xForDate(d);
          html += markerButton({
            x: x,
            eventId: ev.event_id,
            riskId: linkedRisk ? linkedRisk.risk_id : "",
            shape: ev.shape || "fact",
            title: title,
            severity: linkedRisk ? linkedRisk.severity : "",
            markerKind: "event",
            domain: domain
          });
        }
      });

      // Established risk diamonds spatially on the event's lane
      risks.forEach(function (risk) {
        var anchor = findEvent(risk.anchor_event_id);
        if (!anchor || anchor.lane !== lane.id) return;
        var d = risk.anchor_actual_date || eventAxisDate(anchor);
        if (!d) return;
        var x = xForDate(d);
        html += markerButton({
          x: x + 14,
          eventId: risk.anchor_event_id,
          riskId: risk.risk_id,
          shape: "established_risk",
          title: riskDisplayLabel(risk) + " · 风险等级 " + mapped(SEVERITY_LABEL, risk.severity),
          severity: risk.severity,
          markerKind: "risk",
          domain: riskDomain(risk)
        });
      });

      html += "</div>";
    });

    html += "</div>";
    return html;
  }

  function renderPending() {
    var pending = (journey().events || []).filter(function (ev) {
      return ev.placement === "pending_date_surface" || ev.geometry === "pending";
    });
    if (!pending.length) return "";
    return "<div class=\"pj-pending\" aria-label=\"日期信息不完整的记录\">" +
      "<p class=\"pj-pending__title\">日期信息不完整</p>" +
      "<p class=\"pj-empty\" style=\"padding:0 0 8px\">以下记录日期不完整或存在冲突，暂不放入时间轴。</p>" +
      "<ul class=\"pj-pending__list\">" +
      pending.map(function (ev) {
        var selected = isSelectedEvent(ev.event_id) ? " is-selected" : "";
        return "<li><button type=\"button\" class=\"pj-pending__item" + selected +
          "\" data-action=\"select-open\" data-event=\"" + escapeHtml(ev.event_id) +
          "\">" + escapeHtml(eventDisplayLabel(ev)) +
          " · " + escapeHtml(mapped(DATE_STATUS_LABEL, ev.date_status)) +
          (ev.partial_date_text ? " · " + escapeHtml(ev.partial_date_text) : "") +
          "</button></li>";
      }).join("") +
      "</ul></div>";
  }

  function bindSelectActions(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-action='select-open']"), function (btn) {
      btn.addEventListener("click", function () {
        openFromTrigger(btn);
      });
      btn.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openFromTrigger(btn);
        }
      });
    });
  }

  function openFromTrigger(btn) {
    var eventId = btn.getAttribute("data-event") || null;
    var riskId = btn.getAttribute("data-risk") || "";
    var shape = btn.getAttribute("data-shape") || "";
    selectIdentity({
      eventId: eventId,
      riskId: riskId || null
    });
    // Capture opener identity before re-render detaches the node.
    if (els.drawerRoot.hidden) {
      state.focusBeforeDrawer = btn;
      state.focusRestore = {
        eventId: eventId || state.selectedEventId || "",
        riskId: riskId || state.selectedRiskId || "",
        shape: shape
      };
    }
    renderAll(false);
    openEvidencePanel(null);
  }

  function renderJourney() {
    var width = canvasWidth();
    var r = axisRange();
    var hiddenNote = state.riskFirst
      ? "当前优先显示中高风险及相关事件；日期信息不完整的记录单独列出。"
      : "当前显示所选时间范围内的全部记录。";
    els.panelJourney.innerHTML =
      "<div class=\"pj-card\"><div class=\"pj-card__head\">" +
      "<h2 class=\"pj-card__title\">旅程总览</h2>" +
      "<p class=\"pj-card__sub\">当前显示 " + escapeHtml(r.start) + " 至 " + escapeHtml(r.end) + "</p></div>" +
      "<div class=\"pj-card__body\">" + legendHtml() +
      "<p class=\"pj-empty\" style=\"padding:0 0 10px\">" + escapeHtml(hiddenNote) + "</p>" +
      "<div class=\"pj-journey-scroll\" id=\"pj-journey-scroll\">" +
      "<div class=\"pj-journey-canvas\" style=\"width:" + width + "px\">" +
      renderVisitRuler(width) +
      renderPhaseBands(width) +
      renderLanes(width) +
      "</div></div>" +
      renderPending() +
      "</div></div>";
    bindSelectActions(els.panelJourney);
  }

  function metricDomains() {
    return [
      {
        id: "labs",
        title: "实验室 / 检查",
        filter: function (ev) { return ev.lane === "labs" || ev.event_type === "laboratory"; }
      },
      {
        id: "ae_sae",
        title: "不良事件 / 症状",
        filter: function (ev) { return ev.lane === "ae_sae"; }
      },
      {
        id: "exposure",
        title: "研究药物暴露",
        filter: function (ev) { return ev.lane === "exposure"; }
      },
      {
        id: "mh_cm",
        title: "病史 / 合并用药 / 住院",
        filter: function (ev) { return ev.lane === "mh_cm"; }
      }
    ];
  }

  function renderMetrics() {
    var width = canvasWidth();
    var domains = metricDomains();
    var html = "<div class=\"pj-card\"><div class=\"pj-card__head\">" +
      "<h2 class=\"pj-card__title\">指标趋势</h2>" +
      "<p class=\"pj-card__sub\">与旅程总览共用时间窗与选中状态</p></div><div class=\"pj-card__body\">" +
      "<div class=\"pj-info-grid\">" +
      "<div class=\"pj-info-block\"><h3>医学摘要</h3><p>" +
      escapeHtml("AE/MH 及相关风险摘要（合成演示数据）") +
      "</p></div>" +
      "<div class=\"pj-info-block\"><h3>已记录 AE/MH</h3><p>" +
      escapeHtml(String((journey().facts || []).length)) +
      " 条；风险线索不计入</p></div>" +
      "<div class=\"pj-info-block\"><h3>当前风险</h3><p>" +
      escapeHtml(String((journey().risks || []).length)) +
      " 条</p></div></div>" +
      "<div class=\"pj-metric-grid\">";

    domains.forEach(function (domain) {
      var points = (journey().events || []).filter(function (ev) {
        return domain.filter(ev) && eventInWindow(ev) && ev.placement !== "pending_date_surface";
      });
      html += "<section class=\"pj-metric-strip\" aria-label=\"" + escapeHtml(domain.title) + "\">" +
        "<div class=\"pj-metric-strip__head\"><span>" + escapeHtml(domain.title) +
        "</span><span>" + points.length + " 项</span></div>" +
        "<div class=\"pj-metric-strip__scroll\"><div class=\"pj-metric-plot\" style=\"width:" +
        width + "px\">";
      // reuse visit guides lightly
      (journey().visits || []).forEach(function (v) {
        if (v.visit_type === "planned") return;
        var d = visitAxisDate(v);
        if (!d) return;
        var r = axisRange();
        if (d < r.start || d > r.end) return;
        html += "<div class=\"pj-guide\" style=\"left:" + xForDate(d) + "px;height:100%\"></div>";
      });
      points.forEach(function (ev) {
        var d = eventAxisDate(ev) || ev.start_date;
        if (!d) return;
        var x = xForDate(d);
        var risk = riskForEvent(ev.event_id);
        var row = slice3Row((ev.source_refs || [])[0]);
        var valueLabel = "";
        if (row && row.raw_values && row.raw_values.value) {
          valueLabel = text(row.raw_values.value);
          if (valueLabel === "synthetic-normal") valueLabel = "合成正常";
        }
        var label = eventDisplayLabel(ev);
        if (valueLabel) label = label + " · " + valueLabel;
        var selected = isCrossHighlighted(ev.event_id, risk && risk.risk_id) ? " is-selected" : "";
        html += "<button type=\"button\" class=\"pj-metric-point" + selected +
          "\" data-has-risk=\"" + (risk ? "true" : "false") +
          "\" data-action=\"select-open\" data-event=\"" + escapeHtml(ev.event_id) +
          "\" data-risk=\"" + escapeHtml(risk ? risk.risk_id : "") +
          "\" style=\"left:" + x + "px\">" + escapeHtml(label) + "</button>";
      });
      if (!points.length) {
        html += "<p class=\"pj-empty\">当前时间窗无该项记录</p>";
      }
      html += "</div></div></section>";
    });

    html += "</div></div></div>";
    els.panelMetrics.innerHTML = html;
    bindSelectActions(els.panelMetrics);
  }

  function renderEvents() {
    var list = (journey().events || []).filter(function (ev) {
      return eventInWindow(ev);
    });
    var html = "<div class=\"pj-card\"><div class=\"pj-card__head\">" +
      "<h2 class=\"pj-card__title\">事件明细</h2>" +
      "<p class=\"pj-card__sub\">单日记录、持续记录以及日期信息不完整的记录</p></div><div class=\"pj-card__body\">";
    if (!list.length) {
      html += "<p class=\"pj-empty\">当前时间窗内无事件。</p>";
    } else {
      html += "<div class=\"pj-event-list\">" + list.map(function (ev) {
        var risk = riskForEvent(ev.event_id);
        var selected = isCrossHighlighted(ev.event_id, risk && risk.risk_id) ? " is-selected" : "";
        var when = ev.geometry === "pending"
          ? (mapped(DATE_STATUS_LABEL, ev.date_status) + (ev.partial_date_text ? " · " + ev.partial_date_text : ""))
          : (ev.geometry === "interval" || ev.geometry === "interval_open")
            ? ((ev.start_date || "—") + " → " + (ev.open_ended || !ev.end_date ? "进行中" : ev.end_date))
            : axisCaption(ev.actual_date, ev.study_day);
        return "<button type=\"button\" class=\"pj-event-card" + selected +
          "\" data-action=\"select-open\" data-event=\"" + escapeHtml(ev.event_id) +
          "\" data-risk=\"" + escapeHtml(risk ? risk.risk_id : "") + "\">" +
          "<p class=\"pj-event-card__title\">" + escapeHtml(eventDisplayLabel(ev)) + "</p>" +
          "<p class=\"pj-event-card__meta\">" +
          escapeHtml(domainInfo(eventDomain(ev)).label) + " · " +
          escapeHtml(mapped(GEOMETRY_LABEL, ev.geometry)) + " · " +
          escapeHtml(when) +
          (ev.visit_label ? " · 访视 " + escapeHtml(ev.visit_label) : "") +
          (risk ? " · 关联风险" : "") +
          "</p></button>";
      }).join("") + "</div>";
    }
    html += "</div></div>";
    els.panelEvents.innerHTML = html;
    bindSelectActions(els.panelEvents);
  }

  function renderRisks() {
    var risks = journey().risks || [];
    var candidates = journey().candidates || [];
    var html = "<div class=\"pj-card\"><div class=\"pj-card__head\">" +
      "<h2 class=\"pj-card__title\">风险依据</h2>" +
      "<p class=\"pj-card__sub\">支持依据、排除依据、数据来源与 Query 草稿</p></div><div class=\"pj-card__body\">";

    html += "<div class=\"pj-info-grid\">" +
      "<div class=\"pj-info-block\"><h3>疑似漏报线索与已记录 AE/MH</h3><p>疑似漏报线索 " +
      escapeHtml(String(candidates.length)) + " 条；已记录 AE/MH " +
      escapeHtml(String((journey().facts || []).length)) + " 条。</p></div>" +
      "<div class=\"pj-info-block\"><h3>时间范围说明</h3><p>调整时间范围只影响当前显示，不会改变风险状态。</p></div>" +
      "</div>";

    if (!risks.length) {
      html += "<p class=\"pj-empty\">当前无风险记录。</p>";
    } else {
      html += "<div class=\"pj-risk-list\">" + risks.map(function (risk) {
        var inWin = riskInWindow(risk);
        var selected = isSelectedRisk(risk.risk_id) ? " is-selected" : "";
        return "<button type=\"button\" class=\"pj-risk-card" + selected +
          "\" data-action=\"select-open\" data-risk=\"" + escapeHtml(risk.risk_id) +
          "\" data-event=\"" + escapeHtml(risk.anchor_event_id || "") + "\">" +
          "<p class=\"pj-risk-card__title\">" + escapeHtml(riskDisplayLabel(risk)) +
          "<span class=\"pj-risk-card__sev\" data-level=\"" + escapeHtml(risk.severity || "") + "\">" +
          escapeHtml(mapped(SEVERITY_LABEL, risk.severity)) + "</span></p>" +
          "<p class=\"pj-risk-card__meta\">" +
          escapeHtml(domainInfo(riskDomain(risk)).label) + "相关风险 · " +
          escapeHtml(mapped(RISK_TYPE_LABEL, risk.risk_type)) +
          " · 发生于 " + escapeHtml(risk.anchor_actual_date || "日期未知") +
          (inWin ? "" : " · 当前时间范围外（仍可查看依据）") +
          "</p></button>";
      }).join("") + "</div>";
    }

    html += "</div></div>";
    els.panelRisks.innerHTML = html;
    bindSelectActions(els.panelRisks);
  }

  function queryPart(label, body) {
    return "<div class=\"pj-query-part\"><p class=\"pj-query-part__label\">" +
      escapeHtml(label) + "</p><p class=\"pj-query-part__text\">" +
      escapeHtml(audienceCopy(body) || "—") + "</p></div>";
  }

  function evidenceBodyHtml() {
    var risk = state.selectedRiskId ? findRisk(state.selectedRiskId) : null;
    var ev = state.selectedEventId ? findEvent(state.selectedEventId) : null;
    if (!risk && ev) risk = riskForEvent(ev.event_id);
    if (!ev && risk) ev = findEvent(risk.anchor_event_id);

    var html = "";
    if (ev) {
      html += "<p><strong>选中事件：</strong>" + escapeHtml(eventDisplayLabel(ev)) + "</p>";
      html += "<p>" + escapeHtml(mapped(GEOMETRY_LABEL, ev.geometry)) +
        (ev.actual_date ? " · " + escapeHtml(axisCaption(ev.actual_date, ev.study_day)) : "") +
        (ev.geometry === "pending" ? " · " + escapeHtml(mapped(DATE_STATUS_LABEL, ev.date_status)) : "") +
        "</p>";
    }

    if (!risk) {
      html += "<p>当前记录未关联风险，可继续查看数据来源。</p>";
      html += "<h3>数据来源</h3>";
      (ev && ev.source_refs ? ev.source_refs : []).forEach(function (ref) {
        html += "<div class=\"pj-locator\">" + escapeHtml(sourceLocatorLabel(ref)) + "</div>";
      });
      if (!ev || !(ev.source_refs || []).length) {
        html += "<p>暂未找到对应的数据来源。</p>";
      }
      return html;
    }

    html += "<p><strong>风险类别：</strong>" + escapeHtml(domainInfo(riskDomain(risk)).label) + "相关风险</p>";
    html += "<p><strong>风险：</strong>" + escapeHtml(riskDisplayLabel(risk)) +
      "（" + escapeHtml(mapped(SEVERITY_LABEL, risk.severity)) + "）</p>";
    html += "<p>" + escapeHtml(mapped(RISK_TYPE_LABEL, risk.risk_type)) +
      " · 该风险线索未计入已记录 AE/MH 统计</p>";

    var query = queryForRisk(risk);
    if (query) {
      html += "<h3>Query 草稿</h3>" +
        queryPart("依据", query.basis) +
        queryPart("发现", query.finding) +
        queryPart("行动项", query.action);
    } else {
      html += "<h3>Query 草稿</h3><p>当前风险未关联 Query 草稿；页面不会自行补造或提交。</p>";
    }

    // Counterevidence from Slice 3 profile when concept overlaps
    var counters = ((state.slice3.subject_profiles[state.subjectId] || {}).counterevidence || []).filter(function (c) {
      return text(c.concept).toLowerCase() === text(risk.concept).toLowerCase();
    });
    html += "<h3>支持与排除依据</h3>";
    html += "<p><strong>支持依据：</strong>对应事件及跨表数据线索。</p>";
    if (counters.length) {
      html += "<ul>" + counters.map(function (c) {
        var reason = text(c.reason);
        if (reason === "signal matches an existing reported mh record") reason = "该信号已匹配现有 MH 记录";
        if (reason === "signal matches an existing reported ae record") reason = "该信号已匹配现有 AE 记录";
        return "<li>" + escapeHtml(mapped(CONCEPT_LABEL, c.concept)) + " — " + escapeHtml(reason) + "</li>";
      }).join("") + "</ul>";
    } else {
      html += "<p>暂未发现能够排除此风险的对应记录。</p>";
    }

    html += "<h3>数据来源</h3>";
    var refs = risk.evidence_refs || [];
    if (!refs.length && ev) refs = ev.source_refs || [];
    if (!refs.length) {
      html += "<p>暂未找到对应的数据来源。</p>";
    } else {
      refs.forEach(function (ref) {
        var row = slice3Row(ref);
        var historical = row && (String(row.snapshot_label || "").toUpperCase() === "N" ||
          String(row.snapshot_version || "").toUpperCase() === "SYNTHETIC-N");
        html += "<div class=\"pj-locator\" data-historical=\"" + (historical ? "true" : "false") + "\">" +
          escapeHtml(sourceLocatorLabel(ref)) +
          (historical ? "（历史批次）" : "") +
          "</div>";
      });
    }

    html += "<p style=\"margin-top:12px;color:var(--pj-meta);font-size:13px\">浏览证据不会写入确认或处置结果。</p>";
    return html;
  }

  function getFocusable(container) {
    return Array.prototype.filter.call(
      container.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"),
      function (el) { return !el.disabled && el.offsetParent !== null; }
    );
  }

  function openEvidencePanel(opener) {
    if (!state.selectedEventId && !state.selectedRiskId) return;
    var wasHidden = !!els.drawerRoot.hidden;
    if (wasHidden) {
      if (opener) {
        state.focusBeforeDrawer = opener;
        state.focusRestore = {
          eventId: opener.getAttribute("data-event") || state.selectedEventId || "",
          riskId: opener.getAttribute("data-risk") || state.selectedRiskId || "",
          shape: opener.getAttribute("data-shape") || ""
        };
      } else if (!state.focusRestore) {
        state.focusBeforeDrawer = document.activeElement;
        state.focusRestore = {
          eventId: state.selectedEventId || "",
          riskId: state.selectedRiskId || "",
          shape: ""
        };
      }
    }
    state.drawerOpen = true;
    els.drawerRoot.hidden = false;
    var risk = state.selectedRiskId ? findRisk(state.selectedRiskId) : null;
    var title = risk
      ? ("详情与来源 · " + riskDisplayLabel(risk))
      : "详情与来源";
    els.drawerTitle.textContent = title;
    els.drawerBody.innerHTML = evidenceBodyHtml();
    window.setTimeout(function () {
      els.drawerClose.focus();
    }, 0);
  }

  function restoreFocusAfterClose() {
    var restore = state.focusRestore;
    state.focusRestore = null;
    var back = state.focusBeforeDrawer;
    state.focusBeforeDrawer = null;

    var target = null;
    if (restore) {
      var candidates = Array.prototype.slice.call(document.querySelectorAll("[data-action='select-open']"));
      // Prefer exact shape + risk/event match (e.g. established_risk diamond).
      if (restore.shape) {
        candidates.forEach(function (el) {
          if (target) return;
          if ((el.getAttribute("data-shape") || "") !== restore.shape) return;
          var ev = el.getAttribute("data-event") || "";
          var rk = el.getAttribute("data-risk") || "";
          if (restore.riskId && rk === restore.riskId) target = el;
          else if (!restore.riskId && restore.eventId && ev === restore.eventId) target = el;
        });
      }
      if (!target && restore.riskId) {
        candidates.forEach(function (el) {
          if (!target && (el.getAttribute("data-risk") || "") === restore.riskId) target = el;
        });
      }
      if (!target && restore.eventId) {
        candidates.forEach(function (el) {
          if (!target && (el.getAttribute("data-event") || "") === restore.eventId) target = el;
        });
      }
    }
    if (!target && back && document.contains(back) && typeof back.focus === "function") {
      target = back;
    }
    if (target && typeof target.focus === "function") {
      window.setTimeout(function () { target.focus(); }, 0);
    }
  }

  function closeEvidencePanel() {
    if (els.drawerRoot.hidden) return;
    els.drawerRoot.hidden = true;
    els.drawerBody.innerHTML = "";
    state.drawerOpen = false;
    restoreFocusAfterClose();
  }

  function updateWindowNote() {
    var r = axisRange();
    var outside = (journey().risks || []).filter(function (risk) { return !riskInWindow(risk); }).length;
    els.windowNote.textContent =
      "当前时间窗 " + r.start + " ~ " + r.end +
      "；坐标模式：" + (state.axisMode === "study_day" ? "研究日（派生标签）" : "实际日期") +
      "。当前时间范围外的风险 " + outside + " 条仍可在“风险依据”中查看，风险状态不受影响。";
  }

  function renderAll(preserveScroll) {
    var scroller = $("pj-journey-scroll");
    var left = scroller && preserveScroll ? scroller.scrollLeft : 0;
    headerMeta();
    updateWindowNote();
    setTab(state.tab);
    renderJourney();
    renderMetrics();
    renderEvents();
    renderRisks();
    if (preserveScroll) {
      scroller = $("pj-journey-scroll");
      if (scroller) scroller.scrollLeft = left;
    }
    if (state.drawerOpen) {
      els.drawerBody.innerHTML = evidenceBodyHtml();
    }
  }

  function applyControlsFromDom() {
    state.axisMode = els.axisMode.value || "actual_date";
    state.windowStart = els.windowStart.value || state.defaultStart;
    state.windowEnd = els.windowEnd.value || state.defaultEnd;
    state.pxPerDay = Number(els.zoom.value) || 14;
    state.riskFirst = !!els.riskFirst.checked;
    if (state.windowStart > state.windowEnd) {
      var tmp = state.windowStart;
      state.windowStart = state.windowEnd;
      state.windowEnd = tmp;
      els.windowStart.value = state.windowStart;
      els.windowEnd.value = state.windowEnd;
    }
  }

  function bindChrome() {
    els.axisMode.addEventListener("change", function () {
      applyControlsFromDom();
      renderAll(true);
    });
    els.zoom.addEventListener("input", function () {
      applyControlsFromDom();
      renderAll(true);
    });
    els.riskFirst.addEventListener("change", function () {
      applyControlsFromDom();
      renderAll(true);
    });
    els.windowApply.addEventListener("click", function () {
      applyControlsFromDom();
      renderAll(false);
    });
    els.windowReset.addEventListener("click", function () {
      state.windowStart = state.defaultStart;
      state.windowEnd = state.defaultEnd;
      els.windowStart.value = state.windowStart;
      els.windowEnd.value = state.windowEnd;
      renderAll(false);
    });

    Array.prototype.forEach.call(document.querySelectorAll(".pj-tab"), function (tab) {
      tab.addEventListener("click", function () {
        state.tab = tab.getAttribute("data-tab");
        setTab(state.tab);
        tab.focus();
      });
      tab.addEventListener("keydown", function (event) {
        var tabs = Array.prototype.slice.call(document.querySelectorAll(".pj-tab"));
        var idx = tabs.indexOf(tab);
        var next = null;
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
          next = tabs[(idx + 1) % tabs.length];
        } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
          next = tabs[(idx - 1 + tabs.length) % tabs.length];
        } else if (event.key === "Home") {
          next = tabs[0];
        } else if (event.key === "End") {
          next = tabs[tabs.length - 1];
        }
        if (next) {
          event.preventDefault();
          state.tab = next.getAttribute("data-tab");
          setTab(state.tab);
          next.focus();
        }
      });
    });

    els.drawerClose.addEventListener("click", closeEvidencePanel);
    els.drawerBackdrop.addEventListener("click", closeEvidencePanel);
    document.addEventListener("keydown", function (event) {
      if ((event.key === "Escape" || event.key === "Esc") && !els.drawerRoot.hidden) {
        event.preventDefault();
        closeEvidencePanel();
        return;
      }
      if (els.drawerRoot.hidden || event.key !== "Tab") return;
      var focusable = getFocusable(els.drawer);
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  function boot() {
    els.error = $("pj-error");
    els.errorBody = $("pj-error-body");
    els.shell = $("pj-shell");
    els.headerMeta = $("pj-header-meta");
    els.disclaimer = $("pj-disclaimer");
    els.axisMode = $("pj-axis-mode");
    els.windowStart = $("pj-window-start");
    els.windowEnd = $("pj-window-end");
    els.windowApply = $("pj-window-apply");
    els.windowReset = $("pj-window-reset");
    els.windowNote = $("pj-window-note");
    els.zoom = $("pj-zoom");
    els.riskFirst = $("pj-risk-first");
    els.panelJourney = $("pj-panel-journey");
    els.panelMetrics = $("pj-panel-metrics");
    els.panelEvents = $("pj-panel-events");
    els.panelRisks = $("pj-panel-risks");
    els.drawerRoot = $("pj-drawer-root");
    els.drawer = $("pj-drawer");
    els.drawerBackdrop = $("pj-drawer-backdrop");
    els.drawerTitle = $("pj-drawer-title");
    els.drawerBody = $("pj-drawer-body");
    els.drawerClose = $("pj-drawer-close");

    var checked = validate();
    if (!checked.ok) {
      showError(checked.reason);
      return;
    }

    state.journey = checked.journey;
    state.slice3 = checked.slice3;
    state.subjectId = checked.journey.default_subject_id;
    state.siteId = checked.journey.subject_journey.site_id || "—";
    var vs = checked.journey.shared_view_state || {};
    state.axisMode = vs.axis_mode || "actual_date";
    state.defaultStart = vs.window_start || "2025-11-20";
    state.defaultEnd = vs.window_end || "2026-02-28";
    state.windowStart = state.defaultStart;
    state.windowEnd = state.defaultEnd;
    state.selectedEventId = vs.selected_event_id || null;
    state.selectedRiskId = vs.selected_risk_id || null;

    els.disclaimer.textContent = audienceCopy(checked.journey.disclaimer) ||
      "合成演示数据，仅用于隔离 R1 受试者医学旅程验收；不是真实受试者记录。";
    els.axisMode.value = state.axisMode;
    els.windowStart.value = state.windowStart;
    els.windowEnd.value = state.windowEnd;

    els.error.hidden = true;
    els.shell.hidden = false;
    bindChrome();
    renderAll(false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
