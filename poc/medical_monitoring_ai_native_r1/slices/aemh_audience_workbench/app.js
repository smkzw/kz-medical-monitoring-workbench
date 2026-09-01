/**
 * R1 AE/MH audience workbench — file:// interactive viewer.
 * Consumes window.MM_R1_DATA only. No embedded audience mock data.
 */
(function () {
  "use strict";

  var PAGE_SIZE = 8;
  var SEVERITY_RANK = { severe: 4, high: 3, medium: 2, moderate: 2, mild: 1, low: 1 };
  var MEANINGFUL_LIFE = {
    established: 1,
    escalated: 1,
    reopened: 1,
    not_evaluable: 1,
    de_escalated: 1
  };
  var MEANINGFUL_DELTA = {
    current: 1,
    new: 1,
    escalated: 1,
    carry_forward: 1,
    reopened: 1,
    not_evaluable: 1
  };
  var LIFE_LABEL = {
    established: "已建立",
    escalated: "已升级",
    reopened: "重新出现",
    de_escalated: "已降级",
    not_evaluable: "暂不可评估",
    resolved_by_data: "数据已确认解决",
    superseded: "已被新风险替代",
    closed: "已关闭"
  };
  var DELTA_LABEL = {
    current: "当前",
    new: "新增",
    escalated: "升级",
    carry_forward: "结转",
    resolved: "已解决",
    not_evaluable: "不可评估",
    reopened: "重开",
    de_escalated: "降级"
  };
  var SEVERITY_LABEL = {
    severe: "严重",
    high: "高",
    medium: "中",
    moderate: "中",
    mild: "轻微",
    low: "低"
  };
  var RISK_TYPE_LABEL = {
    potential_unreported_ae: "疑似 AE 漏报",
    potential_unreported_mh: "疑似 MH 漏报"
  };
  var CONCEPT_LABEL = {
    "unplanned admission": "非计划住院",
    "skin rash": "皮疹",
    "alt elevation": "ALT 升高",
    hypertension: "高血压",
    headache: "头痛",
    fatigue: "疲乏",
    nausea: "恶心",
    dizziness: "头晕"
  };
  var EVENT_TYPE_LABEL = {
    ae: "不良事件",
    mh: "既往病史",
    symptom: "症状",
    cm_indication: "合并用药适应证",
    laboratory: "实验室检查",
    hospitalization: "住院记录",
    serious_event: "严重事件",
    procedure: "操作或手术",
    dosing: "研究药物给药"
  };
  var TABLE_LABEL = {
    ae: "不良事件表",
    mh: "既往病史表",
    symptoms: "症状表",
    concomitant_medications: "合并用药表",
    labs: "实验室检查表",
    examinations: "体格检查表",
    hospitalizations: "住院记录表",
    serious_events: "严重事件表",
    procedures: "操作或手术表",
    dosing: "研究药物给药表"
  };
  var POLARITY_LABEL = {
    formal_fact: "已记录 AE/MH",
    counterevidence: "反证",
    supporting: "支持风险判断",
    context: "背景信息"
  };
  var STATUS_LABEL = {
    passed: "已完成",
    complete: "已完成",
    done: "已完成",
    running: "处理中",
    failed: "失败",
    pending: "等待中"
  };

  var state = {
    data: null,
    view: "project",
    siteId: null,
    subjectId: null,
    subjectTab: "profile",
    filters: {
      severity: "all",
      lifecycle: "all",
      riskType: "all",
      site: "all",
      q: "",
      changeFirst: true
    },
    timeWindow: { start: "", end: "" },
    page: 1,
    drawer: null,
    focusBeforeDrawer: null
  };

  var els = {};

  function $(id) {
    return document.getElementById(id);
  }

  function text(value) {
    return value == null ? "" : String(value);
  }

  function escapeHtml(value) {
    return text(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function mappedLabel(map, value, fallback) {
    var raw = text(value);
    return map[raw.toLowerCase()] || fallback || raw || "—";
  }

  function conceptLabel(value) {
    return mappedLabel(CONCEPT_LABEL, value);
  }

  function riskTypeLabel(value) {
    return mappedLabel(RISK_TYPE_LABEL, value, "其他医学风险");
  }

  function severityLabel(value) {
    return mappedLabel(SEVERITY_LABEL, value, "未分级");
  }

  function eventTypeLabel(value) {
    return mappedLabel(EVENT_TYPE_LABEL, value, "其他时间事件");
  }

  function factTypeLabel(value) {
    if (value === "reported_ae") return "已报告 AE";
    if (value === "reported_mh") return "已报告 MH";
    return "已报告 AE/MH";
  }

  function tableLabel(value) {
    return mappedLabel(TABLE_LABEL, value, "其他数据表");
  }

  function snapshotLabel(value) {
    var raw = text(value).toUpperCase();
    if (raw.indexOf("N1") >= 0 || raw.indexOf("N+1") >= 0) return "本次全量数据";
    if (raw.indexOf("N") >= 0) return "上次全量数据";
    return "当前数据批次";
  }

  function reasonLabel(value) {
    var raw = text(value).toLowerCase();
    if (raw === "signal matches an existing reported mh record") return "该信号已匹配现有 MH 记录";
    if (raw === "signal matches an existing reported ae record") return "该信号已匹配现有 AE 记录";
    return value || "—";
  }

  function medicalSummaryLabel(value) {
    if (text(value) === "SYNTHETIC AE/MH evidence and risk summary") {
      return "AE/MH 证据与风险摘要（合成演示数据）";
    }
    return value || "暂无医学摘要";
  }

  function severityRank(value) {
    return SEVERITY_RANK[String(value || "").toLowerCase()] || 0;
  }

  function isHighSignal(card) {
    return severityRank(card.severity) >= 2;
  }

  function linkRef(link) {
    if (!link) return "";
    if (typeof link === "string") return link;
    return text(link.source_ref || link.locator || "");
  }

  function asLinkList(links) {
    if (!links) return [];
    if (!Array.isArray(links)) return [];
    return links.map(function (link) {
      if (typeof link === "string") {
        return { source_ref: link, historical: false };
      }
      return {
        source_ref: linkRef(link),
        historical: !!link.historical,
        fixture_marker: link.fixture_marker || "SYNTHETIC"
      };
    }).filter(function (l) { return !!l.source_ref; });
  }

  function parseLocator(locator) {
    var out = { locator: locator, snapshot: "", table: "", row: "" };
    var parts = String(locator || "").split("|");
    parts.forEach(function (part) {
      if (part.indexOf("snapshot=") === 0) out.snapshot = part.slice(9);
      if (part.indexOf("table=") === 0) out.table = part.slice(6);
      if (part.indexOf("row=") === 0) out.row = part.slice(4);
    });
    return out;
  }

  function sourceLocatorLabel(locator) {
    var parsed = parseLocator(locator);
    return snapshotLabel(parsed.snapshot) + " · " + tableLabel(parsed.table) + " · 记录 " + (parsed.row || "—");
  }

  function showError(message) {
    els.error.hidden = false;
    els.shell.hidden = true;
    els.errorBody.textContent = message;
  }

  function validateData(raw) {
    if (!raw || typeof raw !== "object") {
      return { ok: false, reason: "window.MM_R1_DATA 缺失或不是对象。" };
    }
    if (text(raw.fixture_marker) !== "SYNTHETIC" && text(raw.marker) !== "SYNTHETIC") {
      var dash = raw.project_dashboard || {};
      if (text(dash.fixture_marker) !== "SYNTHETIC") {
        return { ok: false, reason: "缺少 SYNTHETIC fixture_marker；拒绝非合成或未知载荷。" };
      }
    }
    if (!raw.project_dashboard || typeof raw.project_dashboard !== "object") {
      return { ok: false, reason: "缺少 project_dashboard。" };
    }
    if (!raw.site_dashboards || typeof raw.site_dashboards !== "object") {
      return { ok: false, reason: "缺少 site_dashboards。" };
    }
    if (!raw.subject_profiles || typeof raw.subject_profiles !== "object") {
      return { ok: false, reason: "缺少 subject_profiles。" };
    }
    if (!raw.subject_timelines || typeof raw.subject_timelines !== "object") {
      return { ok: false, reason: "缺少 subject_timelines。" };
    }
    if (!raw.source_rows || typeof raw.source_rows !== "object") {
      return { ok: false, reason: "缺少 source_rows 索引（按 SYNTHETIC|snapshot=...|table=...|row=... 定位）。" };
    }
    if (!raw.delta_groups || typeof raw.delta_groups !== "object") {
      return { ok: false, reason: "缺少 delta_groups（current/new/escalated/carry_forward/resolved/not_evaluable）。" };
    }
    var groupMap = extractDeltaGroupMap(raw.delta_groups);
    var requiredGroups = ["current", "new", "escalated", "carry_forward", "resolved", "not_evaluable"];
    for (var i = 0; i < requiredGroups.length; i += 1) {
      if (!Object.prototype.hasOwnProperty.call(groupMap, requiredGroups[i])) {
        return {
          ok: false,
          reason: "delta_groups 缺少分组键 " + requiredGroups[i] + "（期望 groups.* 或顶层同名数组）。"
        };
      }
    }
    return { ok: true };
  }

  function extractDeltaGroupMap(deltaGroups) {
    if (!deltaGroups || typeof deltaGroups !== "object") return {};
    if (deltaGroups.groups && typeof deltaGroups.groups === "object") {
      return deltaGroups.groups;
    }
    var flat = {};
    ["current", "new", "escalated", "carry_forward", "resolved", "not_evaluable"].forEach(function (key) {
      if (Array.isArray(deltaGroups[key])) flat[key] = deltaGroups[key];
    });
    return flat;
  }

  function normalizeData(raw) {
    var project = raw.project_dashboard;
    var groupMap = extractDeltaGroupMap(raw.delta_groups);
    var deltaIndex = {};
    Object.keys(groupMap).forEach(function (group) {
      var items = groupMap[group] || [];
      (Array.isArray(items) ? items : []).forEach(function (item) {
        var key = typeof item === "string" ? item : (item && (item.identity_key || item.instance_id));
        if (!key) return;
        if (!deltaIndex[key]) deltaIndex[key] = [];
        if (deltaIndex[key].indexOf(group) < 0) deltaIndex[key].push(group);
      });
    });

    var riskCards = (project.risk_cards || []).map(function (card) {
      var copy = Object.assign({}, card);
      copy.evidence_links = asLinkList(card.evidence_links);
      copy.delta_groups = deltaIndex[card.identity_key] || deltaIndex[card.instance_id] || inferDelta(card);
      return copy;
    });

    var runLineage = raw.run_lineage || {};
    var snapLineage = raw.snapshot_lineage || {};
    var runN1 = runLineage.run_n1 || {};
    var runN = runLineage.run_n || {};
    var snapN1 = snapLineage.snapshot_n1 || {};
    var snapN = snapLineage.snapshot_n || {};

    return {
      fixture_marker: raw.fixture_marker || raw.marker || project.fixture_marker || "SYNTHETIC",
      disclaimer: raw.disclaimer || raw.synthetic_disclaimer ||
        "全部标识符与行均为 SYNTHETIC 合成数据；不代表真实项目、中心、受试者或临床结论。",
      ai_boundary: raw.ai_boundary || "AI辅助定位证据与风险，医学经理终审",
      lineage: {
        project_id: snapLineage.project_id || project.project_id,
        run_id: runN1.run_id || project.run_id,
        snapshot_version: runN1.snapshot_version || snapN1.snapshot_version || project.snapshot_version,
        prior_run_id: runN1.prior_run_id || runN.run_id || null,
        prior_snapshot_version: snapN.snapshot_version || runN.snapshot_version || null,
        snapshot_lineage: snapLineage,
        run_lineage: runLineage
      },
      progress: normalizeProgress(raw.progress),
      project_dashboard: Object.assign({}, project, { risk_cards: riskCards }),
      site_dashboards: raw.site_dashboards,
      subject_profiles: raw.subject_profiles,
      subject_timelines: raw.subject_timelines,
      source_rows: raw.source_rows,
      delta_groups: raw.delta_groups,
      delta_group_map: groupMap,
      delta_counts: (raw.delta_groups && raw.delta_groups.counts) || {},
      delta_semantics: (raw.delta_groups && raw.delta_groups.semantics) || {},
      queries: Array.isArray(raw.queries) ? raw.queries : (project.queries || []),
      counterevidence: Array.isArray(raw.counterevidence)
        ? raw.counterevidence
        : (project.counterevidence || []),
      coverage: raw.coverage != null ? raw.coverage : project.coverage
    };
  }

  function inferDelta(card) {
    var kinds = card.transition_kinds || [];
    var out = [];
    kinds.forEach(function (kind) {
      var k = String(kind || "");
      if (k.indexOf("carry_forward") >= 0) out.push("carry_forward");
      else if (k.indexOf("escalat") >= 0) out.push("escalated");
      else if (k.indexOf("reopen") >= 0) out.push("reopened");
      else if (k.indexOf("new") >= 0 || k === "establish" || k === "create") out.push("new");
      else if (k.indexOf("resolv") >= 0) out.push("resolved");
      else if (k.indexOf("not_evaluable") >= 0) out.push("not_evaluable");
    });
    if (!out.length) {
      if (card.lifecycle_state === "not_evaluable") out.push("not_evaluable");
      else if (card.lifecycle_state === "resolved_by_data" || card.lifecycle_state === "closed") out.push("resolved");
      else if (card.lifecycle_state === "escalated") out.push("escalated");
      else if (card.lifecycle_state === "reopened") out.push("reopened");
      else out.push("current");
    }
    return out;
  }

  function normalizeProgress(progress) {
    if (!progress || typeof progress !== "object") {
      return {
        completed: 0,
        total: 0,
        current_work: "等待 worker 01 载荷中的 progress 节点",
        nodes: []
      };
    }
    var nodes = progress.nodes || progress.detail_nodes || progress.by_node || [];
    if (!Array.isArray(nodes) && nodes && typeof nodes === "object") {
      nodes = Object.keys(nodes).map(function (key) {
        var node = nodes[key];
        if (typeof node === "string") return { id: key, label: key, status: node };
        return Object.assign({ id: key, label: key }, node);
      });
    }
    nodes = (Array.isArray(nodes) ? nodes : []).map(function (node) {
      var status = node.status || node.state || "complete";
      if (status === "complete" || status === "passed" || status === "done") status = "passed";
      return Object.assign({}, node, { status: status });
    });
    return {
      completed: Number(progress.completed != null ? progress.completed : progress.done) || 0,
      total: Number(progress.total != null ? progress.total : nodes.length) || 0,
      current_work: text(progress.current_work || progress.rolling_text || progress.message || "合成运行已完成（静态 POC）"),
      nodes: nodes
    };
  }

  function riskSort(a, b) {
    var sa = severityRank(a.severity);
    var sb = severityRank(b.severity);
    if (sa !== sb) return sb - sa;
    var la = MEANINGFUL_LIFE[a.lifecycle_state] || 0;
    var lb = MEANINGFUL_LIFE[b.lifecycle_state] || 0;
    if (la !== lb) return lb - la;
    return text(a.identity_key).localeCompare(text(b.identity_key));
  }

  function isChangeFirstCard(card) {
    if (isHighSignal(card)) return true;
    if (MEANINGFUL_LIFE[card.lifecycle_state]) return true;
    var deltas = card.delta_groups || [];
    for (var i = 0; i < deltas.length; i += 1) {
      if (MEANINGFUL_DELTA[deltas[i]]) return true;
    }
    return false;
  }

  function currentRiskUniverse() {
    var data = state.data;
    if (state.view === "site" && state.siteId && data.site_dashboards[state.siteId]) {
      return (data.site_dashboards[state.siteId].risk_cards || []).map(enrichFromProject);
    }
    if (state.view === "subject" && state.subjectId && data.subject_profiles[state.subjectId]) {
      return (data.subject_profiles[state.subjectId].risk_cards || []).map(enrichFromProject);
    }
    return data.project_dashboard.risk_cards || [];
  }

  function enrichFromProject(card) {
    var projectCards = state.data.project_dashboard.risk_cards || [];
    for (var i = 0; i < projectCards.length; i += 1) {
      if (projectCards[i].identity_key === card.identity_key || projectCards[i].instance_id === card.instance_id) {
        return Object.assign({}, projectCards[i], card, {
          evidence_links: asLinkList(card.evidence_links && card.evidence_links.length
            ? card.evidence_links
            : projectCards[i].evidence_links),
          delta_groups: projectCards[i].delta_groups || inferDelta(card)
        });
      }
    }
    var copy = Object.assign({}, card);
    copy.evidence_links = asLinkList(card.evidence_links);
    copy.delta_groups = inferDelta(card);
    return copy;
  }

  function applyFilters(cards) {
    var f = state.filters;
    var q = f.q.trim().toLowerCase();
    return cards.filter(function (card) {
      if (f.severity !== "all" && String(card.severity).toLowerCase() !== f.severity) return false;
      if (f.lifecycle !== "all" && card.lifecycle_state !== f.lifecycle) return false;
      if (f.riskType !== "all" && card.risk_type !== f.riskType) return false;
      if (f.site !== "all" && card.site_id !== f.site) return false;
      if (state.view === "project" && state.filters.site !== "all" && card.site_id !== state.filters.site) return false;
      if (q) {
        var hay = [
          card.subject_id, card.site_id, card.concept, card.identity_key,
          card.risk_type, card.lifecycle_state, card.severity
        ].join(" ").toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      if (f.changeFirst && !isChangeFirstCard(card)) return false;
      return true;
    }).sort(riskSort);
  }

  function pageSlice(items) {
    var total = items.length;
    var pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (state.page > pages) state.page = pages;
    if (state.page < 1) state.page = 1;
    var start = (state.page - 1) * PAGE_SIZE;
    return {
      items: items.slice(start, start + PAGE_SIZE),
      total: total,
      page: state.page,
      pages: pages,
      start: total ? start + 1 : 0,
      end: Math.min(total, start + PAGE_SIZE)
    };
  }

  function fillFilterOptions() {
    var cards = state.data.project_dashboard.risk_cards || [];
    var types = {};
    var sites = {};
    cards.forEach(function (card) {
      if (card.risk_type) types[card.risk_type] = 1;
      if (card.site_id) sites[card.site_id] = 1;
    });
    (state.data.project_dashboard.site_ids || Object.keys(state.data.site_dashboards)).forEach(function (site) {
      sites[site] = 1;
    });
    populateSelect(els.filterRiskType, Object.keys(types).sort(), "全部", riskTypeLabel);
    populateSelect(els.filterSite, Object.keys(sites).sort(), "全部");
  }

  function populateSelect(select, values, allLabel, labeler) {
    var current = select.value || "all";
    select.innerHTML = "";
    var optAll = document.createElement("option");
    optAll.value = "all";
    optAll.textContent = allLabel;
    select.appendChild(optAll);
    values.forEach(function (value) {
      var opt = document.createElement("option");
      opt.value = value;
      opt.textContent = labeler ? labeler(value) : value;
      select.appendChild(opt);
    });
    select.value = values.indexOf(current) >= 0 || current === "all" ? current : "all";
  }

  function renderLineage() {
    var lineage = state.data.lineage || {};
    els.lineage.innerHTML =
      "<div><strong>项目</strong> " + escapeHtml(lineage.project_id || state.data.project_dashboard.project_id) + "</div>" +
      "<div><strong>数据范围</strong> 本次全量数据</div>" +
      (lineage.prior_run_id ? "<div><strong>变化基线</strong> 上次全量数据</div>" : "");
    els.disclaimer.textContent = state.data.disclaimer;
    var boundaryStrong = document.querySelector(".kz-boundary strong");
    if (boundaryStrong && state.data.ai_boundary) {
      boundaryStrong.textContent = state.data.ai_boundary;
    }
  }

  function renderProgress() {
    var progress = state.data.progress;
    if (!progress || (!progress.total && !(progress.nodes || []).length)) {
      els.progress.hidden = true;
      return;
    }
    els.progress.hidden = false;
    els.progressRatio.textContent = progress.completed + " / " + progress.total;
    els.progressCurrent.textContent = "当前工作：" + progress.current_work;
    els.progressSummary.textContent = "查看 " + progress.total + " 个处理步骤";
    els.progressDetail.open = progress.completed < progress.total;
    els.progressNodes.innerHTML = (progress.nodes || []).map(function (node) {
      var label = node.label || node.name || node.id || "节点";
      var status = node.status || node.state || "passed";
      var detail = node.detail ? " — " + text(node.detail) : "";
      return "<li data-status=\"" + escapeHtml(status) + "\">" +
        escapeHtml(label) + "（" + escapeHtml(STATUS_LABEL[status] || "状态未知") + "）" + escapeHtml(detail) + "</li>";
    }).join("");
  }

  function renderCrumb() {
    var parts = [{ id: "project", label: "项目总览", action: function () { goProject(); } }];
    if (state.view === "site" || state.view === "subject") {
      if (state.siteId) {
        parts.push({
          id: "site",
          label: "中心 " + state.siteId,
          action: function () { goSite(state.siteId); }
        });
      }
    }
    if (state.view === "subject" && state.subjectId) {
      parts.push({
        id: "subject",
        label: "受试者 " + state.subjectId,
        action: null
      });
    }
    els.crumb.innerHTML = parts.map(function (part, index) {
      var current = index === parts.length - 1;
      if (current || !part.action) {
        return "<li><span aria-current=\"page\">" + escapeHtml(part.label) + "</span></li>";
      }
      return "<li><button type=\"button\" data-crumb=\"" + escapeHtml(part.id) + "\">" +
        escapeHtml(part.label) + "</button></li>";
    }).join("");
    Array.prototype.forEach.call(els.crumb.querySelectorAll("button[data-crumb]"), function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-crumb");
        if (id === "project") goProject();
        if (id === "site") goSite(state.siteId);
      });
    });
    els.back.hidden = state.view === "project";
  }

  function countsForView() {
    if (state.view === "site" && state.siteId && state.data.site_dashboards[state.siteId]) {
      return state.data.site_dashboards[state.siteId].counts || {};
    }
    if (state.view === "subject" && state.subjectId && state.data.subject_profiles[state.subjectId]) {
      return state.data.subject_profiles[state.subjectId].counts || {};
    }
    return state.data.project_dashboard.counts || {};
  }

  function renderSummary(filteredCount) {
    var counts = countsForView();
    var candidate = counts.candidate_count != null ? counts.candidate_count : "—";
    var reported = counts.reported_ae_mh_count != null ? counts.reported_ae_mh_count : "—";
    var asReported = counts.candidates_counted_as_reported != null ? counts.candidates_counted_as_reported : 0;
    els.summary.innerHTML =
      statHtml("筛选可见风险", filteredCount, "") +
      statHtml("待核实风险", candidate, "sep") +
      statHtml("已记录 AE/MH", reported, "ok") +
      statHtml("待核实项误计入 AE/MH", asReported, asReported ? "risk" : "ok") +
      statHtml("反证条数", (counts.counterevidence_count != null
        ? counts.counterevidence_count
        : (state.data.counterevidence || []).length), "sep");
  }

  function statHtml(label, value, tone) {
    return "<div class=\"kz-stat" + (tone ? " kz-stat--" + tone : "") + "\">" +
      "<p class=\"kz-stat__label\">" + escapeHtml(label) + "</p>" +
      "<p class=\"kz-stat__value\">" + escapeHtml(value) + "</p></div>";
  }

  function legendHtml() {
    return "<div class=\"kz-legend\" role=\"list\">" +
      "<div class=\"kz-legend__item\" role=\"listitem\"><span class=\"kz-swatch kz-swatch--fact\" aria-hidden=\"true\"></span>实线方块 = 已记录 AE/MH</div>" +
      "<div class=\"kz-legend__item\" role=\"listitem\"><span class=\"kz-swatch kz-swatch--candidate\" aria-hidden=\"true\"></span>虚线圆 = 疑似 AE/MH 漏报</div>" +
      "<div class=\"kz-legend__item\" role=\"listitem\"><span class=\"kz-swatch kz-swatch--risk\" aria-hidden=\"true\"></span>菱形强调 = 风险/缺口语义</div>" +
      "<div class=\"kz-legend__item\" role=\"listitem\"><span class=\"kz-swatch kz-swatch--hist\" aria-hidden=\"true\"></span>点线框 = 历史证据引用</div>" +
      "</div>";
  }

  function riskCardHtml(card) {
    var boundQuery = findQuery(card.identity_key, card.subject_id);
    var deltas = (card.delta_groups || []).map(function (d) {
      return "<span class=\"kz-pill kz-pill--delta\">" + escapeHtml(DELTA_LABEL[d] || d) + "</span>";
    }).join("");
    var shapePill = card.is_formal_ae_mh_fact
      ? "<span class=\"kz-pill kz-pill--fact\">已记录 AE/MH</span>"
      : "<span class=\"kz-pill kz-pill--candidate\">疑似 AE/MH 漏报</span>";
    var sev = String(card.severity || "").toLowerCase();
    return "<article class=\"kz-risk-card\" data-severity=\"" + escapeHtml(sev) + "\" data-identity=\"" +
      escapeHtml(card.identity_key || "") + "\">" +
      "<div class=\"kz-risk-card__band\">" +
      "<span class=\"kz-pill kz-pill--" + escapeHtml(sev === "moderate" ? "medium" : sev) + "\">严重程度 " +
      escapeHtml(severityLabel(card.severity)) + "</span>" +
      "<span class=\"kz-pill kz-pill--life\">生命周期 " +
      escapeHtml(LIFE_LABEL[card.lifecycle_state] || card.lifecycle_state || "—") + "</span>" +
      shapePill + deltas +
      "</div>" +
      "<div class=\"kz-risk-card__body\">" +
      "<h3 class=\"kz-risk-card__concept\">" + escapeHtml(conceptLabel(card.concept || "（无概念）")) + "</h3>" +
      "<p class=\"kz-risk-card__meta\">" +
      "<span>风险类型 " + escapeHtml(riskTypeLabel(card.risk_type)) + "</span>" +
      "<span>中心 " + escapeHtml(card.site_id || "—") + "</span>" +
      "<span>受试者 " + escapeHtml(card.subject_id || "—") + "</span>" +
      "<span>本次待核实 " + escapeHtml(card.candidate_count != null ? card.candidate_count : "—") + "</span>" +
      "</p>" +
      "<p class=\"kz-risk-card__meta\">关联证据 " + escapeHtml((card.evidence_links || []).length) +
      " 条 · " + (boundQuery ? "已有 Query 草稿" : "当前无 Query 草稿") + "</p>" +
      "<div class=\"kz-risk-card__actions\">" +
      "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"evidence\" data-identity=\"" +
      escapeHtml(card.identity_key || "") + "\">打开证据</button>" +
      (boundQuery
        ? "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"query\" data-identity=\"" +
          escapeHtml(card.identity_key || "") + "\" data-subject=\"" + escapeHtml(card.subject_id || "") +
          "\">查看 Query 草稿</button>"
        : "") +
      (card.site_id
        ? "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"site\" data-site=\"" +
          escapeHtml(card.site_id) + "\">进入中心</button>"
        : "") +
      (card.subject_id
        ? "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"subject\" data-subject=\"" +
          escapeHtml(card.subject_id) + "\" data-site=\"" + escapeHtml(card.site_id || "") +
          "\">查看受试者概览/历时轨迹</button>"
        : "") +
      "</div></div></article>";
  }

  function renderRiskPanel(title, subtitle, cards) {
    var paged = pageSlice(cards);
    var body;
    if (!paged.total) {
      return "";
    }
    body = "<div class=\"kz-risk-list\">" + paged.items.map(riskCardHtml).join("") + "</div>" +
      "<div class=\"kz-pager\">" +
      "<span>显示 " + paged.start + "–" + paged.end + " / 共 " + paged.total + " 条（每页 " + PAGE_SIZE + "）</span>" +
      "<div class=\"kz-pager__controls\">" +
      "<button type=\"button\" class=\"kz-btn\" data-page=\"prev\"" + (paged.page <= 1 ? " disabled" : "") +
      ">上一页</button>" +
      "<button type=\"button\" class=\"kz-btn\" data-page=\"next\"" + (paged.page >= paged.pages ? " disabled" : "") +
      ">下一页</button>" +
      "</div></div>";
    return "<section class=\"kz-panel\">" +
      "<div class=\"kz-panel__head\"><h2 class=\"kz-panel__title\">" + escapeHtml(title) +
      "</h2><p class=\"kz-panel__sub\">" + escapeHtml(subtitle) + "</p></div>" +
      "<div class=\"kz-panel__body\">" + legendHtml() + body + "</div></section>";
  }

  function bindRiskActions(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-action]"), function (btn) {
      btn.addEventListener("click", function (event) {
        var trigger = event.currentTarget || btn;
        var action = trigger.getAttribute("data-action");
        if (action === "evidence") {
          openEvidenceDrawer(trigger.getAttribute("data-identity"), trigger);
        }
        if (action === "query") {
          openQueryDrawer(
            trigger.getAttribute("data-identity"),
            trigger.getAttribute("data-subject"),
            trigger
          );
        }
        if (action === "site") goSite(trigger.getAttribute("data-site"));
        if (action === "subject") {
          goSubject(trigger.getAttribute("data-subject"), trigger.getAttribute("data-site") || null);
        }
      });
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-page]"), function (btn) {
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        if (btn.getAttribute("data-page") === "prev") state.page -= 1;
        if (btn.getAttribute("data-page") === "next") state.page += 1;
        render();
      });
    });
  }

  function renderProject() {
    var sites = state.data.project_dashboard.site_ids || Object.keys(state.data.site_dashboards);
    var siteHtml = "<section class=\"kz-panel\"><div class=\"kz-panel__head\">" +
      "<h2 class=\"kz-panel__title\">中心入口</h2>" +
      "<p class=\"kz-panel__sub\">先看变化与高风险，再下钻中心与受试者</p></div>" +
      "<div class=\"kz-panel__body\"><div class=\"kz-sites\">" +
      sites.map(function (siteId) {
        var site = state.data.site_dashboards[siteId] || {};
        var counts = site.counts || {};
        return "<button type=\"button\" class=\"kz-site-card\" data-action=\"site\" data-site=\"" +
          escapeHtml(siteId) + "\">" +
          "<p class=\"kz-site-card__id\">" + escapeHtml(siteId) + "</p>" +
          "<p class=\"kz-site-card__meta\">风险 " + escapeHtml((site.risk_cards || []).length) +
          " · 待核实 " + escapeHtml(counts.candidate_count != null ? counts.candidate_count : "—") +
          " · 已记录 AE/MH " + escapeHtml(counts.reported_ae_mh_count != null ? counts.reported_ae_mh_count : "—") +
          " · 受试者 " + escapeHtml(counts.affected_subject_count != null ? counts.affected_subject_count : (site.subjects || []).length) +
          "</p></button>";
      }).join("") +
      "</div></div></section>";

    var filtered = applyFilters(currentRiskUniverse());
    var riskHtml = renderRiskPanel(
      "变化优先风险列表",
      state.filters.changeFirst
        ? "默认展示中高严重度与有意义生命周期变化；低风险细节可通过关闭“变化优先”查看"
        : "已关闭变化优先，显示当前筛选下全部风险",
      filtered
    );
    els.viewProject.innerHTML = siteHtml + (riskHtml || "") + deltaPanelHtml();
    bindRiskActions(els.viewProject);
    return filtered.length;
  }

  function deltaPanelHtml() {
    var groups = state.data.delta_group_map || extractDeltaGroupMap(state.data.delta_groups);
    var counts = state.data.delta_counts || {};
    var semantics = state.data.delta_semantics || {};
    var order = ["new", "escalated", "carry_forward", "current", "not_evaluable", "resolved"];
    var blocks = order.map(function (key) {
      var items = groups[key] || [];
      var n = counts[key] != null ? counts[key] : (Array.isArray(items) ? items.length : 0);
      var meaning = semantics[key] || "与“缺席/不可评估”语义分离；计数为生命周期分组，不等于正式 AE/MH 分母。";
      return "<div class=\"kz-info-block\"><h3>" + escapeHtml(DELTA_LABEL[key] || key) +
        "（" + n + "）</h3><p style=\"margin:0;font-size:15px;color:var(--kz-body)\">" +
        escapeHtml(meaning) + "</p></div>";
    }).join("");
    var absenceNote = semantics.absence_is_not_resolution
      ? "<p class=\"kz-section-label\">判断原则：高危风险未出现在本次数据中，不得据此自动结案</p>"
      : "";
    return "<section class=\"kz-panel\"><div class=\"kz-panel__head\">" +
      "<h2 class=\"kz-panel__title\">风险变化分组</h2>" +
      "<p class=\"kz-panel__sub\">当前、新增、升级、延续、已解决与暂不可评估</p></div>" +
      "<div class=\"kz-panel__body\">" + absenceNote + "<div class=\"kz-profile-grid\">" + blocks +
      "</div></div></section>";
  }

  function renderSite() {
    var site = state.data.site_dashboards[state.siteId];
    if (!site) {
      els.viewSite.innerHTML = "<div class=\"kz-empty\"><h2 class=\"kz-empty__title\">中心不存在</h2>" +
        "<p class=\"kz-empty__body\">未找到中心 " + escapeHtml(state.siteId) + "。</p></div>";
      return 0;
    }
    var subjects = site.subjects || [];
    var subjectHtml = "<section class=\"kz-panel\"><div class=\"kz-panel__head\">" +
      "<h2 class=\"kz-panel__title\">中心受试者</h2>" +
      "<p class=\"kz-panel__sub\">" + escapeHtml(state.siteId) + "</p></div>" +
      "<div class=\"kz-panel__body\"><div class=\"kz-sites\">" +
      subjects.map(function (subjectId) {
        return "<button type=\"button\" class=\"kz-site-card\" data-action=\"subject\" data-subject=\"" +
          escapeHtml(subjectId) + "\" data-site=\"" + escapeHtml(state.siteId) + "\">" +
          "<p class=\"kz-site-card__id\">" + escapeHtml(subjectId) + "</p>" +
          "<p class=\"kz-site-card__meta\">查看受试者概览与历时轨迹</p></button>";
      }).join("") +
      "</div></div></section>";
    var filtered = applyFilters(currentRiskUniverse());
    var riskHtml = renderRiskPanel("中心风险（变化优先）", state.siteId, filtered);
    els.viewSite.innerHTML = subjectHtml + (riskHtml || "");
    bindRiskActions(els.viewSite);
    return filtered.length;
  }

  function sharedSpine(subjectId) {
    var profile = state.data.subject_profiles[subjectId] || {};
    var timeline = state.data.subject_timelines[subjectId] || {};
    return {
      profile: profile,
      timeline: timeline,
      spineId: profile.temporal_spine_id || timeline.temporal_spine_id || "",
      spine: profile.temporal_spine || timeline.temporal_spine || { events: [] }
    };
  }

  function inTimeWindow(dateStr) {
    if (!dateStr) return true;
    var start = state.timeWindow.start;
    var end = state.timeWindow.end;
    if (start && dateStr < start) return false;
    if (end && dateStr > end) return false;
    return true;
  }

  function renderSubject() {
    var pack = sharedSpine(state.subjectId);
    if (!pack.profile.subject_id && !pack.timeline.subject_id) {
      els.viewSubject.innerHTML = "<div class=\"kz-empty\"><h2 class=\"kz-empty__title\">受试者不存在</h2>" +
        "<p class=\"kz-empty__body\">未找到受试者 " + escapeHtml(state.subjectId) + "。</p></div>";
      return 0;
    }
    var profileSpineId = pack.profile.temporal_spine_id;
    var timelineSpineId = pack.timeline.temporal_spine_id;
    var spineMatch = profileSpineId && timelineSpineId && profileSpineId === timelineSpineId;
    var filtered = applyFilters(currentRiskUniverse());

    var tablist =
      "<div class=\"kz-tabs\" role=\"tablist\" aria-label=\"受试者共轴视图\">" +
      "<button type=\"button\" class=\"kz-tab\" role=\"tab\" id=\"kz-tab-profile\" aria-controls=\"kz-tabpanel\" data-tab=\"profile\" aria-selected=\"" +
      (state.subjectTab === "profile") + "\">受试者概览</button>" +
      "<button type=\"button\" class=\"kz-tab\" role=\"tab\" id=\"kz-tab-timeline\" aria-controls=\"kz-tabpanel\" data-tab=\"timeline\" aria-selected=\"" +
      (state.subjectTab === "timeline") + "\">历时轨迹</button>" +
      "</div>";

    var windowHtml =
      "<div class=\"kz-window\">" +
      "<label class=\"kz-field\"><span class=\"kz-field__label\">时间窗起</span>" +
      "<input class=\"kz-input\" id=\"kz-window-start\" type=\"date\" value=\"" + escapeHtml(state.timeWindow.start) + "\"></label>" +
      "<label class=\"kz-field\"><span class=\"kz-field__label\">时间窗止</span>" +
      "<input class=\"kz-input\" id=\"kz-window-end\" type=\"date\" value=\"" + escapeHtml(state.timeWindow.end) + "\"></label>" +
      "<button type=\"button\" class=\"kz-btn\" id=\"kz-window-apply\">应用时间窗</button>" +
      "<button type=\"button\" class=\"kz-btn kz-btn--ghost\" id=\"kz-window-clear\">清除时间窗</button>" +
      "<p class=\"kz-window__note\">受试者概览与历时轨迹共用同一访视与时间轴" +
      (spineMatch ? "（已对齐）" : "（当前数据未能确认两侧完全对齐）") +
      "；疑似 AE/MH 漏报以虚线圆叠加，已记录 AE/MH 以实线方块区分，颜色不单独承担语义。</p></div>";

    var panel = state.subjectTab === "timeline"
      ? renderTimelinePanel(pack)
      : renderProfilePanel(pack);

    var riskHtml = renderRiskPanel("受试者风险", state.subjectId, filtered);
    els.viewSubject.innerHTML =
      "<section class=\"kz-panel\"><div class=\"kz-panel__head\">" +
      "<h2 class=\"kz-panel__title\">受试者 " + escapeHtml(state.subjectId) + "</h2>" +
      "<p class=\"kz-panel__sub\">受试者概览与历时轨迹共用访视与时间轴</p></div>" +
      "<div class=\"kz-panel__body\" id=\"kz-tabpanel\" role=\"tabpanel\">" +
      tablist + windowHtml + legendHtml() + panel + "</div></section>" +
      (riskHtml || "");

    Array.prototype.forEach.call(els.viewSubject.querySelectorAll(".kz-tab"), function (tab) {
      tab.addEventListener("click", function () {
        state.subjectTab = tab.getAttribute("data-tab");
        render();
        focusSelectedTab();
      });
    });
    var startInput = $("kz-window-start");
    var endInput = $("kz-window-end");
    $("kz-window-apply").addEventListener("click", function () {
      state.timeWindow.start = startInput.value || "";
      state.timeWindow.end = endInput.value || "";
      render();
    });
    $("kz-window-clear").addEventListener("click", function () {
      state.timeWindow.start = "";
      state.timeWindow.end = "";
      render();
    });
    bindRiskActions(els.viewSubject);
    bindTabKeys();
    return filtered.length;
  }

  function renderProfilePanel(pack) {
    var events = ((pack.spine && pack.spine.events) || []).filter(function (ev) {
      return inTimeWindow(ev.actual_date);
    });
    var facts = (pack.profile.reported_ae_mh || []).slice();
    var candidates = (pack.profile.under_reporting_candidates || []).slice();
    var queries = (pack.profile.queries || []).slice();
    var counter = (pack.profile.counterevidence || []).slice();

    return "<div class=\"kz-profile-grid\">" +
      "<div class=\"kz-info-block\"><h3>医学摘要（合成）</h3><p style=\"margin:0\">" +
      escapeHtml(medicalSummaryLabel(pack.profile.medical_summary)) +
      "</p></div>" +
      "<div class=\"kz-info-block\"><h3>已记录 AE/MH（实线方块）</h3><ul>" +
      (facts.length ? facts.map(function (fact) {
        return "<li><strong>" + escapeHtml(factTypeLabel(fact.fact_type)) + "</strong> · " +
          escapeHtml(conceptLabel(fact.body && fact.body.concept)) + " · 待核实风险线索不计入此列</li>";
      }).join("") : "<li>当前无已记录 AE/MH</li>") +
      "</ul></div>" +
      "<div class=\"kz-info-block\"><h3>疑似 AE/MH 漏报（虚线圆）</h3><ul>" +
      (candidates.length ? candidates.map(function (c) {
        return "<li><strong>" + escapeHtml(riskTypeLabel(c.risk_type)) + "</strong> · 严重程度 " +
          escapeHtml(severityLabel(c.severity)) + "</li>";
      }).join("") : "<li>当前时间窗无疑似 AE/MH 漏报</li>") +
      "</ul></div>" +
      "<div class=\"kz-info-block\"><h3>反证</h3><ul>" +
      (counter.length ? counter.map(function (item) {
        return "<li>" + escapeHtml(conceptLabel(item.concept || item.kind)) +
          " — " + escapeHtml(reasonLabel(item.reason)) + "</li>";
      }).join("") : "<li>无反证条目</li>") +
      "</ul></div>" +
      "</div>" +
      "<h3 class=\"kz-section-label\" style=\"margin-top:16px\">共轴时间事件（" + events.length + "）</h3>" +
      renderEventList(events, pack) +
      (queries.length
        ? "<h3 class=\"kz-section-label\">受试者 Query</h3><div class=\"kz-risk-list\">" +
          queries.map(function (q) {
            return "<article class=\"kz-risk-card\"><div class=\"kz-risk-card__body\">" +
              "<h3 class=\"kz-risk-card__concept\">Query 草稿</h3>" +
              "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"open-query-id\" data-query=\"" +
              escapeHtml(q.query_id) + "\">查看草稿</button></div></article>";
          }).join("") + "</div>"
        : "");
  }

  function renderTimelinePanel(pack) {
    var events = ((pack.spine && pack.spine.events) || []).filter(function (ev) {
      return inTimeWindow(ev.actual_date);
    });
    var overlays = (pack.timeline.candidate_overlays || []).filter(function (item) {
      return inTimeWindow(item.actual_date);
    });
    var reported = pack.timeline.reported_event_overlays || [];
    var factsById = {};
    (pack.profile.reported_ae_mh || []).forEach(function (fact) {
      factsById[fact.fact_id] = fact;
    });
    return "<p class=\"kz-section-label\">历时轨迹叠加：已记录 AE/MH=实线方块；疑似 AE/MH 漏报=虚线圆</p>" +
      "<div class=\"kz-profile-grid\" style=\"margin-bottom:14px\">" +
      "<div class=\"kz-info-block\"><h3>已记录 AE/MH 叠加</h3><ul>" +
      (reported.length ? reported.map(function (item) {
        var fact = factsById[item.fact_id] || {};
        return "<li class=\"kz-id-line\"><span class=\"kz-id-line__label\">" +
          escapeHtml(factTypeLabel(fact.fact_type)) + " · " +
          escapeHtml(conceptLabel(fact.body && fact.body.concept)) +
          "（已记录）</span></li>";
      }).join("") : "<li>无</li>") +
      "</ul></div>" +
      "<div class=\"kz-info-block\"><h3>疑似 AE/MH 漏报（不计入已记录 AE/MH）</h3><ul>" +
      (overlays.length ? overlays.map(function (item) {
        var risk = findRiskByIdentity(item.identity_key) || {};
        return "<li class=\"kz-id-line\">" +
          "<span class=\"kz-id-line__label\">" + escapeHtml(riskTypeLabel(risk.risk_type)) +
          " · " + escapeHtml(conceptLabel(risk.concept)) +
          " · " + escapeHtml(item.actual_date || "日期未知") + "（待核实）</span>" +
          "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"evidence\" data-identity=\"" +
          escapeHtml(item.identity_key || "") + "\">查看完整证据</button></li>";
      }).join("") : "<li>当前时间窗无</li>") +
      "</ul></div></div>" +
      renderEventList(events, pack, overlays);
  }

  function renderEventList(events, pack, overlays) {
    overlays = overlays || pack.timeline.candidate_overlays || [];
    if (!events.length) {
      return "<p style=\"margin:0;color:var(--kz-meta)\">当前共轴时间窗内无事件。</p>";
    }
    var overlayByDate = {};
    overlays.forEach(function (item) {
      var key = item.actual_date || "";
      if (!overlayByDate[key]) overlayByDate[key] = [];
      overlayByDate[key].push(item);
    });
    return "<div class=\"kz-timeline\">" + events.map(function (ev) {
      var isFact = String(ev.event_type || "").toLowerCase() === "ae" ||
        String(ev.event_type || "").toLowerCase() === "mh";
      var hasCandidate = (overlayByDate[ev.actual_date || ""] || []).length > 0 && !isFact;
      var kind = isFact ? "fact" : (hasCandidate ? "candidate" : "event");
      var label = isFact ? "已记录 AE/MH" : (hasCandidate ? "疑似 AE/MH 漏报" : "时间轴事件");
      var refs = (ev.source_refs || []).map(function (ref) {
        return "<button type=\"button\" class=\"kz-btn kz-btn--link\" data-action=\"locator\" data-locator=\"" +
          escapeHtml(ref) + "\">查看原始记录</button>";
      }).join(" ");
      return "<div class=\"kz-timeline__item\" data-kind=\"" + kind + "\">" +
        "<span class=\"kz-timeline__marker\" title=\"" + escapeHtml(label) + "\"></span>" +
        "<p class=\"kz-timeline__date\">" + escapeHtml(ev.actual_date || "日期未知") +
        " · 研究第 " + escapeHtml(ev.study_day != null ? ev.study_day : "—") + " 天</p>" +
        "<p class=\"kz-timeline__title\">" + escapeHtml(label) + " · " + escapeHtml(eventTypeLabel(ev.event_type)) + "</p>" +
        "<p class=\"kz-timeline__detail\">" + escapeHtml(sourceLocatorLabel((ev.source_refs || [])[0])) + "</p>" +
        "<div>" + refs + "</div></div>";
    }).join("") + "</div>";
  }

  function findRiskByIdentity(identity) {
    var cards = state.data.project_dashboard.risk_cards || [];
    for (var i = 0; i < cards.length; i += 1) {
      if (cards[i].identity_key === identity || cards[i].instance_id === identity) return cards[i];
    }
    return null;
  }

  function findQuery(identity, subjectId) {
    var queries = state.data.queries || [];
    var subjectQueries = queries.filter(function (q) {
      return !subjectId || q.subject_id === subjectId;
    });
    if (!identity) return subjectQueries.length === 1 ? subjectQueries[0] : null;

    var card = findRiskByIdentity(identity);
    if (!card) return null;
    var cardRefs = asLinkList(card.evidence_links).map(linkRef);
    var matched = subjectQueries.filter(function (q) {
      var identities = Array.isArray(q.risk_identity_keys) ? q.risk_identity_keys : [];
      if (identities.indexOf(identity) >= 0) return true;
      var refs = q.evidence_links || q.evidence_refs || [];
      return refs.some(function (ref) {
        return cardRefs.indexOf(linkRef(ref)) >= 0;
      });
    });
    return matched.length ? matched[0] : null;
  }

  function openEvidenceDrawer(identity, opener) {
    var card = findRiskByIdentity(identity);
    if (!card) return;
    var links = asLinkList(card.evidence_links);
    var rowsHtml = links.map(function (link) {
      return sourceRowHtml(link.source_ref, link.historical);
    }).join("") || "<p>无证据链接。</p>";
    openDrawer(
      "证据下钻 · " + conceptLabel(card.concept || "医学风险"),
      "<p>以下原始记录与本风险卡建立了可追溯关联；待核实风险线索不计入已记录 AE/MH。</p>" +
      "<h3>证据条目</h3>" + rowsHtml,
      opener
    );
  }

  function openQueryDrawer(identity, subjectId, opener) {
    var query = findQuery(identity, subjectId);
    if (!query) {
      openDrawer(
        "Query 草稿",
        "<p>当前风险未关联 Query 草稿；页面不会自行补造内容或提交任务。</p>",
        opener
      );
      return;
    }
    renderQueryDrawer(query, opener);
  }

  function renderQueryDrawer(query, opener) {
    openDrawer(
      "Query 草稿",
      "<div class=\"kz-query-parts\">" +
      queryPart("依据", query.basis) +
      queryPart("发现", query.finding) +
      queryPart("行动项", query.action) +
      "</div>" +
      "<h3>完整草稿</h3><pre class=\"kz-raw\">" + escapeHtml(query.three_part_text || "") + "</pre>" +
      "<h3>关联原始记录</h3>" +
      (query.evidence_links || query.evidence_refs || []).map(function (ref) {
        return sourceRowHtml(linkRef(ref), false);
      }).join(""),
      opener
    );
  }

  function openQueryById(queryId, opener) {
    var query = null;
    (state.data.queries || []).forEach(function (q) {
      if (q.query_id === queryId) query = q;
    });
    if (!query) return;
    renderQueryDrawer(query, opener);
  }

  function queryPart(label, body) {
    return "<div class=\"kz-query-part\"><p class=\"kz-query-part__label\">" + escapeHtml(label) +
      "</p><p class=\"kz-query-part__text\">" + escapeHtml(body || "—") + "</p></div>";
  }

  function audienceRawValues(values) {
    var hiddenInternalFields = {
      fixture_marker: 1,
      candidate_signal: 1,
      potential_unreported: 1,
      possible_ae: 1,
      possible_mh: 1,
      counterevidence_for: 1
    };
    var out = {};
    if (!values || typeof values !== "object" || Array.isArray(values)) return values;
    Object.keys(values).forEach(function (key) {
      if (!hiddenInternalFields[key]) out[key] = values[key];
    });
    return out;
  }

  function sourceRowHtml(locator, historical) {
    var parsed = parseLocator(locator);
    var row = state.data.source_rows[locator] || state.data.source_rows[parsed.locator] || null;
    var values = row && (row.raw_values || row.values || row.raw || row.fields || row.row || row);
    var dl =
      "<dl>" +
      "<dt>数据批次</dt><dd>" + escapeHtml(snapshotLabel((row && row.snapshot_version) || parsed.snapshot)) +
      (historical ? " <span class=\"kz-pill\">历史证据</span>" : "") + "</dd>" +
      "<dt>数据表</dt><dd>" + escapeHtml(tableLabel((row && row.table) || parsed.table)) + "</dd>" +
      "<dt>记录编号</dt><dd>" + escapeHtml((row && (row.record_id || row.row_id)) || parsed.row || "—") + "</dd>" +
      "<dt>受试者</dt><dd>" + escapeHtml((row && row.subject_id) || "—") + "</dd>" +
      "<dt>中心</dt><dd>" + escapeHtml((row && row.site_id) || "—") + "</dd>" +
      "<dt>日期</dt><dd>" + escapeHtml((row && (row.actual_date || row.date || row.onset)) || "—") + "</dd>" +
      "<dt>证据作用</dt><dd>" + escapeHtml(POLARITY_LABEL[(row && row.polarity)] || "背景信息") + "</dd>" +
      "<dt>记录类型</dt><dd>" + escapeHtml(
        row
          ? (row.is_formal_ae_mh_fact ? "已记录 AE/MH" : (row.is_candidate_signal ? "待核实风险线索" : "其他原始记录"))
          : "—"
      ) + "</dd>" +
      "</dl>" +
      "<h3>原始数据行（保留源字段）</h3>" +
      (row
        ? "<pre class=\"kz-raw\">" + escapeHtml(JSON.stringify(audienceRawValues(values), null, 2)) + "</pre>"
        : "<p>source_rows 未解析到该定位符；请检查 worker 01 索引完整性。</p>");
    return "<article class=\"kz-info-block\" style=\"margin-bottom:12px\">" + dl + "</article>";
  }

  function openDrawer(title, bodyHtml, opener) {
    var drawerWasHidden = !!els.drawerRoot.hidden;
    if (drawerWasHidden) {
      // Capture the real trigger; WebKit may already have blurred to BODY.
      if (opener && typeof opener.focus === "function") {
        state.focusBeforeDrawer = opener;
      } else {
        state.focusBeforeDrawer = document.activeElement;
      }
    }
    // Nested open (e.g. locator inside an open drawer): keep the original
    // external opener; do not replace it with an in-drawer control.
    state.drawer = { title: title };
    els.drawerRoot.hidden = false;
    els.drawerTitle.textContent = title;
    els.drawerBody.innerHTML = bodyHtml;
    Array.prototype.forEach.call(els.drawerBody.querySelectorAll("[data-action='locator']"), function (btn) {
      btn.addEventListener("click", function (event) {
        var trigger = event.currentTarget || btn;
        openLocator(trigger.getAttribute("data-locator"), trigger);
      });
    });
    window.setTimeout(function () {
      els.drawerClose.focus();
    }, 0);
  }

  function openLocator(locator, opener) {
    openDrawer("原始记录 · " + sourceLocatorLabel(locator), sourceRowHtml(locator, false), opener);
  }

  function focusWithoutScroll(el) {
    if (!el || typeof el.focus !== "function") return false;
    try {
      el.focus({ preventScroll: true });
    } catch (err) {
      el.focus();
    }
    // Do not treat a late document.activeElement update as focus failure
    // (WebKit may not sync activeElement synchronously).
    return true;
  }

  function openerIsUsable(opener) {
    return !!(opener && opener.isConnected && typeof opener.focus === "function");
  }

  function restoreDrawerOpenerFocus(opener) {
    var main = document.getElementById("kz-main");
    if (!openerIsUsable(opener)) {
      if (main) focusWithoutScroll(main);
      return;
    }
    focusWithoutScroll(opener);
    function verifyOrRetry() {
      if (!openerIsUsable(opener)) {
        if (main) focusWithoutScroll(main);
        return;
      }
      if (document.activeElement === opener) return;
      // Second no-options focus on the exact same connected opener.
      try {
        opener.focus();
      } catch (err) {
        /* ignore */
      }
      // Connected opener: never fall back to #kz-main merely because
      // activeElement has not yet caught up.
    }
    if (typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(function () {
        window.setTimeout(verifyOrRetry, 0);
      });
    } else {
      window.setTimeout(verifyOrRetry, 0);
    }
  }

  function closeDrawer(options) {
    options = options || {};
    if (els.drawerRoot.hidden) return;
    var opener = state.focusBeforeDrawer;
    state.focusBeforeDrawer = null;
    els.drawerRoot.hidden = true;
    els.drawerBody.innerHTML = "";
    state.drawer = null;
    function restore() {
      restoreDrawerOpenerFocus(opener);
    }
    if (options.deferFocus) {
      window.setTimeout(restore, 0);
    } else {
      restore();
    }
  }

  function getFocusable(container) {
    return Array.prototype.slice.call(
      container.querySelectorAll(
        "a[href], button:not([disabled]), textarea, input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])"
      )
    ).filter(function (el) {
      return !el.hasAttribute("disabled") && el.offsetParent !== null;
    });
  }

  function trapFocus(event) {
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
  }

  function bindTabKeys() {
    var tabs = Array.prototype.slice.call(els.viewSubject.querySelectorAll(".kz-tab"));
    tabs.forEach(function (tab, index) {
      tab.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        var next = event.key === "ArrowRight"
          ? tabs[(index + 1) % tabs.length]
          : tabs[(index - 1 + tabs.length) % tabs.length];
        state.subjectTab = next.getAttribute("data-tab");
        render();
        focusSelectedTab();
      });
    });
  }

  function focusSelectedTab() {
    var selected = els.viewSubject.querySelector(".kz-tab[aria-selected='true']");
    if (selected) selected.focus();
  }

  function goProject() {
    state.view = "project";
    state.siteId = null;
    state.subjectId = null;
    state.subjectTab = "profile";
    state.page = 1;
    render();
  }

  function goSite(siteId) {
    state.view = "site";
    state.siteId = siteId;
    state.subjectId = null;
    state.subjectTab = "profile";
    state.page = 1;
    render();
  }

  function goSubject(subjectId, siteId) {
    state.view = "subject";
    state.subjectId = subjectId;
    if (siteId) state.siteId = siteId;
    if (!state.siteId) {
      var profile = state.data.subject_profiles[subjectId] || {};
      var risks = profile.risk_cards || [];
      if (risks[0] && risks[0].site_id) state.siteId = risks[0].site_id;
    }
    state.page = 1;
    render();
  }

  function resetFilters() {
    state.filters = {
      severity: "all",
      lifecycle: "all",
      riskType: "all",
      site: "all",
      q: "",
      changeFirst: true
    };
    els.filterSeverity.value = "all";
    els.filterLifecycle.value = "all";
    els.filterRiskType.value = "all";
    els.filterSite.value = "all";
    els.filterQ.value = "";
    els.filterChangeFirst.checked = true;
    state.page = 1;
    render();
  }

  function readFiltersFromDom() {
    state.filters.severity = els.filterSeverity.value;
    state.filters.lifecycle = els.filterLifecycle.value;
    state.filters.riskType = els.filterRiskType.value;
    state.filters.site = els.filterSite.value;
    state.filters.q = els.filterQ.value || "";
    state.filters.changeFirst = !!els.filterChangeFirst.checked;
    state.page = 1;
  }

  function render() {
    renderCrumb();
    els.viewProject.hidden = true;
    els.viewSite.hidden = true;
    els.viewSubject.hidden = true;
    els.empty.hidden = true;

    var count = 0;
    if (state.view === "project") {
      els.viewProject.hidden = false;
      count = renderProject();
    } else if (state.view === "site") {
      els.viewSite.hidden = false;
      count = renderSite();
    } else {
      els.viewSubject.hidden = false;
      count = renderSubject();
      Array.prototype.forEach.call(els.viewSubject.querySelectorAll("[data-action='locator']"), function (btn) {
        btn.addEventListener("click", function (event) {
          var trigger = event.currentTarget || btn;
          openLocator(trigger.getAttribute("data-locator"), trigger);
        });
      });
      Array.prototype.forEach.call(els.viewSubject.querySelectorAll("[data-action='open-query-id']"), function (btn) {
        btn.addEventListener("click", function (event) {
          var trigger = event.currentTarget || btn;
          openQueryById(trigger.getAttribute("data-query"), trigger);
        });
      });
    }

    renderSummary(count);
    if (count === 0 && state.view !== "subject") {
      // subject view may still show profile/timeline with zero filtered risks
      var hasStructural = state.view === "site" && state.data.site_dashboards[state.siteId];
      if (!hasStructural) {
        els.viewProject.hidden = true;
        els.viewSite.hidden = true;
        els.empty.hidden = false;
        els.emptyBody.textContent = "当前筛选组合没有可显示的风险卡。可重置筛选，或关闭“变化优先”以查看低风险细节。";
      }
    }
    if (state.view === "subject" && count === 0) {
      // keep subject panels visible; empty filter only hides risk panel which already omitted
    }
  }

  function bindGlobal() {
    els.back.addEventListener("click", function () {
      if (state.view === "subject") {
        if (state.siteId) goSite(state.siteId);
        else goProject();
      } else if (state.view === "site") {
        goProject();
      }
    });
    els.filterReset.addEventListener("click", resetFilters);
    els.emptyReset.addEventListener("click", resetFilters);
    ["change", "input"].forEach(function (evt) {
      els.filterSeverity.addEventListener(evt, function () { readFiltersFromDom(); render(); });
      els.filterLifecycle.addEventListener(evt, function () { readFiltersFromDom(); render(); });
      els.filterRiskType.addEventListener(evt, function () { readFiltersFromDom(); render(); });
      els.filterSite.addEventListener(evt, function () { readFiltersFromDom(); render(); });
      els.filterChangeFirst.addEventListener(evt, function () { readFiltersFromDom(); render(); });
    });
    els.filterQ.addEventListener("input", function () {
      readFiltersFromDom();
      render();
    });
    els.drawerClose.addEventListener("click", function () {
      closeDrawer();
    });
    els.drawerBackdrop.addEventListener("click", function () {
      closeDrawer();
    });
    document.addEventListener("keydown", function (event) {
      if ((event.key === "Escape" || event.key === "Esc") && !els.drawerRoot.hidden) {
        event.preventDefault();
        if (typeof event.stopPropagation === "function") event.stopPropagation();
        closeDrawer({ deferFocus: true });
        return;
      }
      trapFocus(event);
    });
  }

  function cacheEls() {
    els.error = $("kz-error");
    els.errorBody = $("kz-error-body");
    els.shell = $("kz-shell");
    els.lineage = $("kz-lineage");
    els.disclaimer = $("kz-disclaimer");
    els.progress = $("kz-progress");
    els.progressRatio = $("kz-progress-ratio");
    els.progressCurrent = $("kz-progress-current");
    els.progressDetail = $("kz-progress-detail");
    els.progressSummary = $("kz-progress-summary");
    els.progressNodes = $("kz-progress-nodes");
    els.crumb = $("kz-crumb");
    els.back = $("kz-back");
    els.filterSeverity = $("kz-filter-severity");
    els.filterLifecycle = $("kz-filter-lifecycle");
    els.filterRiskType = $("kz-filter-risk-type");
    els.filterSite = $("kz-filter-site");
    els.filterQ = $("kz-filter-q");
    els.filterChangeFirst = $("kz-filter-change-first");
    els.filterReset = $("kz-filter-reset");
    els.summary = $("kz-summary");
    els.viewProject = $("kz-view-project");
    els.viewSite = $("kz-view-site");
    els.viewSubject = $("kz-view-subject");
    els.empty = $("kz-empty");
    els.emptyBody = $("kz-empty-body");
    els.emptyReset = $("kz-empty-reset");
    els.drawerRoot = $("kz-drawer-root");
    els.drawer = $("kz-drawer");
    els.drawerBackdrop = $("kz-drawer-backdrop");
    els.drawerTitle = $("kz-drawer-title");
    els.drawerBody = $("kz-drawer-body");
    els.drawerClose = $("kz-drawer-close");
  }

  function boot() {
    cacheEls();
    var raw = window.MM_R1_DATA;
    var check = validateData(raw);
    if (!check.ok) {
      showError(check.reason);
      return;
    }
    state.data = normalizeData(raw);
    els.error.hidden = true;
    els.shell.hidden = false;
    fillFilterOptions();
    renderLineage();
    renderProgress();
    bindGlobal();
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
