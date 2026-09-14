// kz-interact.js — 康哲交互层执行资产 v5.1(下钻卡/系列 chip/可编辑表/甘特拖拽/折叠表/导出)
// 用法:echarts → kz-charts.js → 本文件;CSS 同伴 kz-interact.css。合同:design_specs/html_interact.md。
// 页面 NEVER 重写本文件逻辑;只写 data-* 与 JSON 数据岛。
(function () {
  'use strict';
  if (!window.kzCharts) { console.error('[kz-interact] 需先加载 kz-charts.js'); return; }

  var DAY = 86400000;
  function $(s, r) { return (r || document).querySelector(s); }
  function $all(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function el(tag, cls, html) { var d = document.createElement(tag); if (cls) d.className = cls; if (html != null) d.innerHTML = html; return d; }
  function frozen() { return window.kzCharts.frozen(); }
  function readJSON(id) {
    var n = document.getElementById(id); if (!n) return null;
    try { return JSON.parse(n.textContent); } catch (e) { console.warn('[kz-interact] JSON 数据岛解析失败: #' + id); return null; }
  }
  function fmtDate(t) { var d = new Date(t); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function snapDay(t) { return Math.round(t / DAY) * DAY; }
  function findInst(elId) {
    var list = window.kzCharts.instances;
    for (var i = 0; i < list.length; i++) if (list[i].el.id === elId) return list[i];
    return null;
  }

  // ============ 全局状态:脏标记 / 撤销栈 ============
  var dirty = { cells: {}, gantt: {} };
  var undoStack = [];
  function dirtyCount() { return Object.keys(dirty.cells).length + Object.keys(dirty.gantt).length; }

  // ============ 弹层卡(下钻 + 日期编辑共用) ============
  var pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function showPop(x, y, node) {
    closePop();
    pop = el('div', 'kz-pop'); pop.appendChild(node); document.body.appendChild(pop);
    var w = pop.offsetWidth, h = pop.offsetHeight;
    pop.style.left = Math.max(8, Math.min(x, innerWidth - w - 12)) + 'px';
    pop.style.top = Math.max(8, Math.min(y, innerHeight - h - 12)) + 'px';
    return pop;
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closePop(); });
  document.addEventListener('click', function (e) {
    if (pop && !e.target.closest('.kz-pop') && !e.target.closest('canvas') && !e.target.closest('td[data-kz-cell]')) closePop();
  });
  function popShell(title) {
    var box = el('div');
    var head = el('div', 'kz-pop__head');
    head.appendChild(el('div', 'kz-pop__title', title || '详情'));
    var x = el('button', 'kz-pop__close', '×'); x.type = 'button'; x.onclick = closePop;
    head.appendChild(x); box.appendChild(head);
    return box;
  }

  // ============ 下钻(G-INT-01) ============
  // JSON 岛:{title,html,series:{"系列名":{title,html,points:{"类目名":{...}},children:{"子项":{...}}}}}
  function drillLookup(root, seriesName, pointName) {
    var s = root.series && root.series[seriesName];
    var p = s && s.points && s.points[pointName];
    return p || s || (root.title || root.html ? root : null);
  }
  function openDrill(entry, trail, x, y) {
    var wrap = popShell(entry.title || '详情');
    if (trail.length > 1) {
      var crumb = el('div', 'kz-pop__crumb');
      trail.forEach(function (en, i) {
        if (i) crumb.appendChild(document.createTextNode(' › '));
        var b = el('button', null, en.title || '上一层'); b.type = 'button';
        b.onclick = function () { openDrill(en, trail.slice(0, i + 1), x, y); };
        crumb.appendChild(b);
      });
      wrap.appendChild(crumb);
    }
    var body = el('div', 'kz-pop__body'); body.innerHTML = entry.html || '';
    wrap.appendChild(body);
    if (entry.children && Object.keys(entry.children).length) {
      var kids = el('div', 'kz-pop__kids');
      Object.keys(entry.children).forEach(function (k) {
        var b = el('button', null, '▸ ' + k); b.type = 'button';
        b.onclick = function () { openDrill(entry.children[k], trail.concat([entry.children[k]]), x, y); };
        kids.appendChild(b);
      });
      wrap.appendChild(kids);
    }
    showPop(x, y, wrap);
  }

  // ============ 系列显隐 chip(G-INT-03) ============
  function buildChips(inst) {
    if (inst.el.getAttribute('data-kz-chips') === 'off') return;
    var chart = inst.chart, option = inst.option;
    var mains = (option.series || []).filter(function (s) { return !s.kzAux && s.name; });
    var auxNames = (option.series || []).filter(function (s) { return s.kzAux; }).map(function (s) { return s.name; });
    if (mains.length < 2 && !auxNames.length) return;
    // legend 组件保留(供 dispatchAction),视觉由 chip 接管:chip 开启时 NEVER 再显示内置 legend
    chart.setOption({ legend: { show: false, data: mains.map(function (s) { return s.name; }).concat(auxNames) } });
    var row = el('div', 'kz-chips');
    mains.forEach(function (s, i) {
      var c = (s.itemStyle && s.itemStyle.color) || '#E8A33D';
      if (typeof c === 'object') c = '#E8A33D';
      var chip = el('button', 'kz-chip');
      chip.innerHTML = '<i style="background:' + c + '"></i>' + s.name;
      chip.type = 'button'; chip.setAttribute('aria-pressed', 'true'); chip.dataset.name = s.name;
      chip.onclick = function () { chart.dispatchAction({ type: 'legendToggleSelect', name: s.name }); };
      row.appendChild(chip);
    });
    if (auxNames.length) {
      var rc = el('button', 'kz-chip kz-chip--range');
      rc.innerHTML = '<i style="background:#C9B48A"></i>区间(±SD/IQR)';
      rc.type = 'button'; rc.setAttribute('aria-pressed', 'true');
      rc.onclick = function () {
        auxNames.forEach(function (n) { chart.dispatchAction({ type: 'legendToggleSelect', name: n }); });
      };
      row.appendChild(rc);
    }
    chart.on('legendselectchanged', function (e) {
      $all('.kz-chip[data-name]', row).forEach(function (chip) {
        chip.setAttribute('aria-pressed', String(e.selected[chip.dataset.name] !== false));
      });
      var rc2 = row.querySelector('.kz-chip--range');
      if (rc2 && auxNames.length) rc2.setAttribute('aria-pressed', String(e.selected[auxNames[0]] !== false));
    });
    inst.el.parentNode.insertBefore(row, inst.el);
  }

  // ============ 表格编辑(G-INT-04) ============
  // 单元格契约:<td data-kz-cell="elId|系列名|dataIndex" data-type="number">值</td>;系列 id==name(挂载时自动赋)。
  function commitCell(td, val, silent) {
    var parts = td.getAttribute('data-kz-cell').split('|');
    var elId = parts[0], sName = parts[1], di = +parts[2];
    var inst = findInst(elId); if (!inst) return false;
    var src = null;
    (inst.option.series || []).forEach(function (s) { if (!s.kzAux && s.name === sName && !src) src = s; });
    if (!src) return false;
    var nv = (td.getAttribute('data-type') === 'number') ? parseFloat(val) : val;
    if (td.getAttribute('data-type') === 'number' && (val === '' || isNaN(nv))) { shake(td); td.textContent = td.dataset.orig || ''; return false; }
    var data = (src.data || []).slice();
    var cur = data[di];
    if (cur && typeof cur === 'object' && !Array.isArray(cur)) { data[di] = Object.assign({}, cur, { value: nv }); }
    else data[di] = nv;
    inst.chart.setOption({ series: [{ id: src.id || sName, data: data }] }, { lazyUpdate: true, silent: true });
    var oldText = td.dataset.orig !== undefined && !td.classList.contains('kz-dirty') ? td.dataset.orig : td.textContent;
    if (String(oldText) !== String(val) && !silent) undoStack.push({ kind: 'cell', td: td, oldVal: String(oldText), newVal: String(val) });
    td.textContent = val;
    if (String(td.dataset.orig) !== String(val)) { td.classList.add('kz-dirty'); dirty.cells[td.getAttribute('data-kz-cell')] = String(val); }
    else { td.classList.remove('kz-dirty'); delete dirty.cells[td.getAttribute('data-kz-cell')]; }
    afterEdit();
    return true;
  }
  function shake(n) { n.classList.remove('kz-shake'); void n.offsetWidth; n.classList.add('kz-shake'); }
  document.addEventListener('click', function (e) {
    var td = e.target.closest('td[data-kz-cell]');
    if (!td || td.querySelector('input')) return;
    var cur = td.textContent.trim();
    var input = el('input', 'kz-cell-edit'); input.value = cur;
    if (td.getAttribute('data-type') === 'number') { input.type = 'number'; input.step = 'any'; }
    td.textContent = ''; td.appendChild(input); input.focus(); input.select();
    var done = false;
    function commit() { if (done) return; done = true; commitCell(td, input.value.trim()); }
    input.addEventListener('blur', commit);
    input.addEventListener('keydown', function (ev) {
      ev.stopPropagation();
      if (ev.key === 'Enter') { ev.preventDefault(); commit(); }
      if (ev.key === 'Escape') { done = true; td.textContent = cur; }
    });
    e.stopPropagation();
  });

  // 图 → 表反向联动:点击数据点,展开绑定折叠表并闪烁定位行
  function chartToTable(inst, seriesName, dataIndex) {
    var tid = inst.el.getAttribute('data-kz-table'); if (!tid) return;
    var tbl = document.getElementById(tid); if (!tbl) return;
    var fold = tbl.closest('details.kz-fold'); if (fold && !fold.open) fold.open = true;
    var td = $('td[data-kz-cell="' + inst.el.id + '|' + seriesName + '|' + dataIndex + '"]', tbl);
    if (td) {
      var tr = td.closest('tr');
      tr.scrollIntoView({ block: 'nearest', behavior: frozen() ? 'auto' : 'smooth' });
      tr.classList.remove('kz-flash'); void tr.offsetWidth; tr.classList.add('kz-flash');
    }
  }

  // ============ 甘特交互编辑(G-INT-05) ============
  // el 携带 data-kz-gantt-edit(值为数据岛 id,空则默认 'gantt-'+el.id);
  // 数据岛:{axis:{min,max}, projects:[{key,name,start,end,color?}]}
  function enableGantt(inst) {
    var el0 = inst.el, chart = inst.chart;
    var metaId = el0.getAttribute('data-kz-gantt-edit') || ('gantt-' + el0.id);
    var metaNode = document.getElementById(metaId);
    var meta = readJSON(metaId);
    if (!meta || !meta.projects || !meta.axis) { console.warn('[kz-interact] 甘特数据岛缺失: #' + metaId); return; }
    if (metaNode) metaNode._kzMeta = meta;
    var P = meta.projects;
    var axMin = +new Date(meta.axis.min), axMax = +new Date(meta.axis.max);
    P.forEach(function (p) { p._s = +new Date(p.start); p._e = +new Date(p.end); });

    function pxPerDay() {
      var a = chart.convertToPixel({ xAxisIndex: 0 }, axMin);
      var b = chart.convertToPixel({ xAxisIndex: 0 }, axMin + DAY);
      return Math.max(0.01, b - a);
    }
    function renderItem(params, api) {
      var i = api.value(0), s = api.value(1), e2 = api.value(2);
      var c0 = api.coord([s, i]), c1 = api.coord([e2, i]);
      var h = Math.min(22, api.size([0, 1])[1] * 0.55);
      var rect = echarts.graphic.clipRectByRect(
        { x: c0[0], y: c0[1] - h / 2, width: c1[0] - c0[0], height: h },
        { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height });
      if (!rect) return;
      var color = (P[i] && P[i].color) || '#E8A33D';
      // 拖拽不靠 zrender draggable(事件语义在 custom 元素上不稳),name 携带种类,由下方 zr 事件手工驱动
      return {
        type: 'group',
        children: [
          { type: 'rect', name: 'kzg:move:' + i, shape: { x: rect.x, y: rect.y, width: rect.width, height: rect.height, r: rect.height / 2 },
            style: { fill: color, shadowColor: 'rgba(31,41,55,.18)', shadowBlur: 6, shadowOffsetY: 2 }, cursor: 'grab' },
          // 端点 NEVER 画可见圆点(条块本身就是胶囊);伸缩用透明命中区,hover 出 ew-resize 光标
          { type: 'rect', name: 'kzg:left:' + i, shape: { x: rect.x - 5, y: rect.y - 2, width: 10, height: rect.height + 4 },
            style: { fill: 'rgba(0,0,0,0)' }, cursor: 'ew-resize' },
          { type: 'rect', name: 'kzg:right:' + i, shape: { x: rect.x + rect.width - 5, y: rect.y - 2, width: 10, height: rect.height + 4 },
            style: { fill: 'rgba(0,0,0,0)' }, cursor: 'ew-resize' }
        ]
      };
    }
    // 手工拖拽会话:mousedown 命中命名元素 → mousemove 实时改形 → mouseup 换算日期提交
    var drag = null;
    chart.getZr().on('mousedown', function (ev) {
      var t = ev.target;
      if (!t || !t.name || t.name.indexOf('kzg:') !== 0) return;
      var parts = t.name.split(':');
      drag = { kind: parts[1], i: +parts[2], x0: ev.offsetX, target: t, group: t.parent };
    });
    chart.getZr().on('mousemove', function (ev) {
      if (!drag) return;
      var dx = ev.offsetX - drag.x0;
      if (drag.kind === 'move') { drag.group.attr('position', [dx, 0]); return; }
      var rect = null, hL = null, hR = null;
      drag.group.children().forEach(function (c) {
        if (c.name && c.name.indexOf('kzg:move') === 0) rect = c;   // 句柄也是 rect,必须按 name 区分
        if (c.name && c.name.indexOf('kzg:left') === 0) hL = c;
        if (c.name && c.name.indexOf('kzg:right') === 0) hR = c;
      });
      if (!rect) return;
      var sh = rect.shape;
      if (drag.kind === 'left' && sh.width - dx >= pxPerDay()) {
        rect.attr('shape', { x: sh.x + dx, width: sh.width - dx });
        if (hL) hL.attr('shape', { x: hL.shape.x + dx });
      }
      if (drag.kind === 'right' && sh.width + dx >= pxPerDay()) {
        rect.attr('shape', { width: sh.width + dx });
        if (hR) hR.attr('shape', { x: hR.shape.x + dx });
      }
    });
    function endDrag(ev) {
      if (!drag) return;
      var dx = ev && ev.offsetX !== undefined ? ev.offsetX - drag.x0 : 0;
      var proj = P[drag.i], per = pxPerDay(), kind = drag.kind;
      drag = null;
      if (Math.abs(dx) < 2) { commitGantt(el0.id, proj.key, proj._s, proj._e, true); return; } // 视为点击;恒重绘归位
      var ns = proj._s, ne = proj._e;
      if (kind === 'move') { ns = proj._s + dx / per * DAY; ne = proj._e + dx / per * DAY; }
      if (kind === 'left') ns = proj._s + dx / per * DAY;
      if (kind === 'right') ne = proj._e + dx / per * DAY;
      commitGantt(el0.id, proj.key, snapDay(ns), snapDay(ne)); // 内部恒重绘,视觉归位
    }
    chart.getZr().on('mouseup', endDrag);
    chart.getZr().on('globalout', function () { endDrag(null); });
    function dataArr() { return P.map(function (p, i) { return [i, p._s, p._e]; }); }
    chart.setOption({
      animation: false,
      grid: { left: 8, right: 28, top: 10, bottom: 30, containLabel: true },
      xAxis: { type: 'time', min: axMin, max: axMax, axisLabel: { color: '#6B7280' } },
      yAxis: { type: 'category', data: P.map(function (p) { return p.name; }), inverse: true, axisTick: { show: false }, axisLabel: { color: '#374151' } },
      tooltip: { formatter: function (pr) { var p = P[pr.dataIndex]; return '<b>' + p.name + '</b><br>' + fmtDate(p._s) + ' → ' + fmtDate(p._e); } },
      series: [{ id: 'kzg-' + el0.id, name: 'gantt-edit', type: 'custom', renderItem: renderItem, data: dataArr(), z: 3 }]
    }, { notMerge: true });
    var hint = el('div', 'kz-gantt-hint', '可<b>拖动条</b>整体平移 · 拖两端<b>边缘</b>伸缩 · <b>单击</b>条块精确输入日期');
    el0.parentNode.insertBefore(hint, el0);

    function openEditor(proj, x, y) {
      var box = popShell(proj.name + ' · 调整日期');
      box.appendChild(el('label', null, '开始日期'));
      var d1 = el('input'); d1.type = 'date'; d1.value = fmtDate(proj._s); box.appendChild(d1);
      box.appendChild(el('label', null, '结束日期'));
      var d2 = el('input'); d2.type = 'date'; d2.value = fmtDate(proj._e); box.appendChild(d2);
      var row = el('div', 'kz-pop__row');
      var no = el('button', 'kz-pop__cancel', '取消'); no.type = 'button'; no.onclick = closePop;
      var ok = el('button', 'kz-pop__ok', '应用'); ok.type = 'button';
      ok.onclick = function () {
        var s = +new Date(d1.value), e3 = +new Date(d2.value);
        if (isNaN(s) || isNaN(e3) || s >= e3) { shake(box); return; }
        closePop(); commitGantt(el0.id, proj.key, s, e3);
      };
      row.appendChild(no); row.appendChild(ok); box.appendChild(row);
      showPop(x, y, box);
    }
    chart.on('dblclick', function (ev) {
      if (ev.componentType !== 'series') return;
      var proj = P[ev.dataIndex]; if (!proj) return;
      var rect = el0.getBoundingClientRect();
      var oe = ev.event && ev.event.event;
      openEditor(proj, rect.left + (oe && oe.offsetX || 120) + 12, rect.top + (oe && oe.offsetY || 60) - 10);
    });

    inst._gantt = { meta: meta, dataArr: dataArr, openEditor: openEditor, projects: P };
  }
  function serializeMeta(meta) {
    return { axis: meta.axis, projects: meta.projects.map(function (p) { var o = { key: p.key, name: p.name, start: p.start, end: p.end }; if (p.color) o.color = p.color; return o; }) };
  }
  function commitGantt(elId, key, ns, ne, silent) {
    var inst = findInst(elId); if (!inst || !inst._gantt) return;
    var meta = inst._gantt.meta, proj = null;
    meta.projects.forEach(function (p) { if (p.key === key) proj = p; });
    if (!proj) return;
    ns = Math.max(+new Date(meta.axis.min), ns); ne = Math.min(+new Date(meta.axis.max), ne);
    if (ne - ns < DAY) ne = ns + DAY;
    var old = { s: proj._s, e: proj._e };
    proj._s = ns; proj._e = ne; proj.start = fmtDate(ns); proj.end = fmtDate(ne);
    inst.chart.setOption({ series: [{ id: 'kzg-' + elId, data: inst._gantt.dataArr() }] }, { silent: true }); // 恒重绘:归位拖拽元素
    if (old.s === ns && old.e === ne) return;
    if (!silent) undoStack.push({ kind: 'gantt', elId: elId, key: key, old: old, now: { s: ns, e: ne } });
    dirty.gantt[elId + '|' + key] = { start: proj.start, end: proj.end };
    $all('td[data-kz-date^="' + elId + '|' + key + '|"]').forEach(function (td) {
      var which = td.getAttribute('data-kz-date').split('|')[2];
      td.textContent = which === 'start' ? proj.start : proj.end;
      td.classList.add('kz-dirty');
    });
    afterEdit();
  }

  // ============ 撤销 / 工具条 / 导出 / 草稿(G-INT-04/07) ============
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !(e.target instanceof Element && e.target.closest('input,textarea'))) {
      var it = undoStack.pop(); if (!it) return;
      e.preventDefault();
      if (it.kind === 'cell') commitCell(it.td, it.oldVal, true);
      if (it.kind === 'gantt') commitGantt(it.elId, it.key, it.old.s, it.old.e, true);
    }
  });

  var toolbar = null;
  function afterEdit() {
    updateFoldBadges();
    if (!toolbar && !frozen() && ($all('td[data-kz-cell]').length || $all('[data-kz-gantt-edit]').length)) buildToolbar();
    if (toolbar) toolbar.querySelector('.kz-dirty-n').innerHTML = '已修改 <b>' + dirtyCount() + '</b> 项';
    saveDraft();
  }
  function buildToolbar() {
    if (toolbar) return;
    toolbar = el('div', 'kz-toolbar');
    toolbar.appendChild(el('span', 'kz-dirty-n', '已修改 <b>' + dirtyCount() + '</b> 项'));
    var bHTML = el('button', 'kz-primary', '导出修改版 HTML'); bHTML.type = 'button'; bHTML.onclick = exportHTML;
    var bJSON = el('button', null, '导出数据 JSON'); bJSON.type = 'button'; bJSON.onclick = exportJSON;
    var bReset = el('button', null, '还原全部'); bReset.type = 'button'; bReset.onclick = resetAll;
    toolbar.appendChild(bHTML); toolbar.appendChild(bJSON); toolbar.appendChild(bReset);
    document.body.appendChild(toolbar);
  }
  function exportHTML() {
    var clone = document.documentElement.cloneNode(true);
    $all('.kz-toolbar,.kz-toast,.kz-pop,.kz-gantt-hint', clone).forEach(function (n) { n.remove(); });
    $all('td[data-kz-cell]', clone).forEach(function (td) {
      var live = $('td[data-kz-cell="' + td.getAttribute('data-kz-cell') + '"]');
      if (live) td.textContent = live.textContent;
      td.classList.remove('kz-dirty');
    });
    $all('td[data-kz-date]', clone).forEach(function (td) {
      var live = $('td[data-kz-date="' + td.getAttribute('data-kz-date') + '"]');
      if (live) td.textContent = live.textContent;
      td.classList.remove('kz-dirty');
    });
    $all('script[type="application/json"]', clone).forEach(function (sc) {
      var live = sc.id && document.getElementById(sc.id);
      if (live && live._kzMeta) sc.textContent = JSON.stringify(serializeMeta(live._kzMeta));
    });
    var blob = new Blob(['<!DOCTYPE html>\n' + clone.outerHTML], { type: 'text/html;charset=utf-8' });
    dl(blob, (document.title || 'report').replace(/[\\/:*?"<>|]/g, '') + '-已修改.html');
  }
  function exportJSON() {
    dl(new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), cells: dirty.cells, gantt: dirty.gantt }, null, 2)], { type: 'application/json' }), 'kz-修改数据.json');
  }
  function dl(blob, name) {
    var a = el('a'); a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 400);
  }
  function resetAll() {
    while (undoStack.length) {
      var it = undoStack.pop();
      if (it.kind === 'cell') commitCell(it.td, it.oldVal, true);
      else commitGantt(it.elId, it.key, it.old.s, it.old.e, true);
    }
    dirty.cells = {}; dirty.gantt = {};
    $all('td.kz-dirty').forEach(function (td) { td.classList.remove('kz-dirty'); });
    afterEdit(); clearDraft();
  }
  // 草稿:localStorage 全 try/catch(file:// 下 Safari 拒绝时静默降级,G-INT-07)
  function draftKey() { return 'kzDraft:' + location.pathname; }
  function saveDraft() {
    try {
      if (dirtyCount()) localStorage.setItem(draftKey(), JSON.stringify(dirty));
      else localStorage.removeItem(draftKey());
    } catch (e) {}
  }
  function clearDraft() { try { localStorage.removeItem(draftKey()); } catch (e) {} }
  function offerDraft() {
    var d = null;
    try { d = JSON.parse(localStorage.getItem(draftKey()) || 'null'); } catch (e) { return; }
    if (!d || !(Object.keys(d.cells || {}).length + Object.keys(d.gantt || {}).length)) return;
    var n = Object.keys(d.cells || {}).length + Object.keys(d.gantt || {}).length;
    var t = el('div', 'kz-toast');
    t.appendChild(el('span', null, '检测到上次未导出的修改(' + n + ' 项)'));
    var ok = el('button', 'kz-t-ok', '恢复'); ok.type = 'button';
    var no = el('button', 'kz-t-no', '丢弃'); no.type = 'button';
    ok.onclick = function () {
      Object.keys(d.cells || {}).forEach(function (k) { var td = $('td[data-kz-cell="' + k + '"]'); if (td) commitCell(td, d.cells[k], true); });
      Object.keys(d.gantt || {}).forEach(function (k) {
        var g = d.gantt[k], ps = k.split('|');
        commitGantt(ps[0], ps[1], +new Date(g.start), +new Date(g.end), true);
      });
      t.remove();
    };
    no.onclick = function () { clearDraft(); t.remove(); };
    t.appendChild(ok); t.appendChild(no); document.body.appendChild(t);
  }

  // ============ 折叠表徽标(G-INT-06) ============
  function updateFoldBadges() {
    $all('details.kz-fold').forEach(function (f) {
      var sum = f.querySelector('summary'); if (!sum) return;
      var badge = sum.querySelector('.kz-fold-badge');
      if (!badge) { badge = el('span', 'kz-fold-badge'); sum.appendChild(badge); }
      var rows = f.querySelectorAll('tbody tr').length;
      var dn = f.querySelectorAll('td.kz-dirty').length;
      badge.innerHTML = rows ? ('共 ' + rows + ' 行' + (dn ? ' · 已改 <b>' + dn + '</b>' : '')) : '';
    });
  }

  // ============ 图表点击:下钻 / 表格联动 ============
  function wireChart(inst) {
    var el0 = inst.el, chart = inst.chart;
    buildChips(inst);
    if (el0.hasAttribute('data-kz-gantt-edit')) enableGantt(inst);
    var drill = el0.getAttribute('data-kz-drill') ? readJSON(el0.getAttribute('data-kz-drill')) : null;
    chart.on('click', function (params) {
      if (params.componentType !== 'series') return;
      chartToTable(inst, params.seriesName, params.dataIndex);
      if (inst._gantt && !drill) { // 甘特编辑模式无下钻时:单击即开日期编辑器(双击为别名)
        var proj = inst._gantt.projects[params.dataIndex];
        if (proj) {
          var r0 = inst.el.getBoundingClientRect();
          var oe2 = params.event && params.event.event;
          inst._gantt.openEditor(proj, r0.left + (oe2 && oe2.offsetX || 120) + 12, r0.top + (oe2 && oe2.offsetY || 60) - 10);
        }
        return;
      }
      if (!drill) return;
      var entry = drillLookup(drill, params.seriesName, params.name);
      if (!entry) return;
      var x, y, rect = el0.getBoundingClientRect();
      try {
        var v = params.value;
        if (v && typeof v === 'object' && !Array.isArray(v)) v = v.value;
        var px = chart.convertToPixel({ seriesIndex: params.seriesIndex }, [params.name !== undefined ? params.name : params.dataIndex, Array.isArray(v) ? v[1] : v]);
        x = rect.left + px[0] + 14; y = rect.top + px[1] - 10;
      } catch (err) {
        var off = params.event && params.event.event;
        x = rect.left + (off && off.offsetX || 80) + 14; y = rect.top + (off && off.offsetY || 60);
      }
      openDrill(entry, [entry], x, y);
    });
    chart.getZr().on('click', function (ev) { if (!ev.target) closePop(); });
  }

  // ============ 启动 ============
  function boot() {
    $all('td[data-kz-cell]').forEach(function (td) { td.dataset.orig = td.textContent.trim(); });
    updateFoldBadges();
    if ($all('td[data-kz-cell]').length || $all('[data-kz-gantt-edit]').length) afterEdit();
    offerDraft();
    var seen = [];
    function sweep() {
      window.kzCharts.instances.forEach(function (inst) {
        if (seen.indexOf(inst.el) >= 0) return;
        seen.push(inst.el); wireChart(inst);
      });
    }
    sweep();
    document.addEventListener('kz:chart-mounted', sweep);
    setTimeout(sweep, 800); // 兜底:早期挂载未发事件
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.kzInteract = { commitCell: commitCell, commitGantt: commitGantt, closePop: closePop, dirtyCount: dirtyCount };
})();
