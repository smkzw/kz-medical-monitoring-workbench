// kz-charts.js — 康哲 ECharts 品牌主题与动效合同执行层 v5.0
// 用法:必须先加载 vendor/echarts.min.js(3D 图再加载 echarts-gl.min.js),再加载本文件。
// 模块化版相对路径引用;单文件版按 echarts → echarts-gl(可选) → kz-charts 顺序内联。
// 合同见 design_specs/html_charts.md;本文件是封闭执行层,业务页面 NEVER 重写其中逻辑。
(function () {
  if (!window.echarts) { console.error('[kz-charts] echarts 未加载'); return; }

  // ---- 1. 品牌主题(色序固定,部门映射固定,与 design token 同源) ----
  var KZ = {
    color: ['#FF9900', '#407AAA', '#587B3B', '#A85F34', '#FFCC00', '#AAA6A1', '#C00000'],
    textStyle: { fontFamily: '"Microsoft YaHei","微软雅黑","PingFang SC","Noto Sans SC","Helvetica Neue",Arial,sans-serif' },
    backgroundColor: 'transparent',
    title: { textStyle: { color: '#0F1115', fontWeight: 700 }, subtextStyle: { color: '#808080' } },
    grid: { top: 40, right: 24, bottom: 36, left: 48, containLabel: true },
    categoryAxis: {
      axisLine: { lineStyle: { color: '#D1D5DB' } }, axisTick: { show: false },
      axisLabel: { color: '#404040', fontSize: 13 },
      splitLine: { show: false }
    },
    valueAxis: {
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#404040', fontSize: 13, fontVariantNumeric: 'tabular-nums' },
      splitLine: { lineStyle: { color: '#EEF0F2', width: 1 } },
      nameTextStyle: { color: '#808080', fontSize: 12 }
    },
    legend: { textStyle: { color: '#404040', fontSize: 13 }, itemWidth: 14, itemHeight: 8, icon: 'roundRect' },
    tooltip: {
      backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', borderWidth: 1, padding: [8, 12],
      textStyle: { color: '#0F1115', fontSize: 13 },
      extraCssText: 'box-shadow:0 6px 18px rgba(15,17,21,.10);border-radius:8px;'
    }
  };
  KZ.bar = { itemStyle: { borderRadius: [6, 6, 0, 0] }, barMaxWidth: 44 };
  KZ.line = { smooth: false, symbol: 'circle', symbolSize: 7, lineStyle: { width: 2.5 } };
  KZ.pie = { radius: ['42%', '68%'], itemStyle: { borderColor: '#FFFFFF', borderWidth: 2 }, label: { color: '#404040', fontSize: 13 } };
  echarts.registerTheme('kz', KZ);

  // ---- 2. 动效合同(html_charts.md §4 的可执行默认值) ----
  // 读数区白名单:cubicOut(默认)/backOut(单次过冲轻果冻)。NEVER elasticOut/bounceOut(多次回弹)。
  var MOTION = {
    read:  { duration: 520, easing: 'cubicOut', stagger: 55,  maxTotal: 1200 },
    jelly: { duration: 580, easing: 'backOut',  stagger: 55,  maxTotal: 1200 }, // 需 data-kz-jelly 显式开启
    hero:  { duration: 700, easing: 'elasticOut', stagger: 70, maxTotal: 1400 }  // 仅非读数装饰图
  };
  function motionFor(el) {
    if (!el || !el.closest) return MOTION.read;
    if (el.closest('[data-kz-chart-motion="hero"]')) return MOTION.hero;
    if (el.closest('[data-kz-chart-motion="jelly"]')) return MOTION.jelly;
    return MOTION.read;
  }

  // 冻结态判定:reduced-motion / export / qc / print
  function frozen() {
    var h = document.documentElement;
    return (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)
      || h.hasAttribute('data-export') || h.hasAttribute('data-qc')
      || (window.matchMedia && matchMedia('print').matches);
  }

  // ---- 2.5 实例注册表 + 统计区间引擎(html_interact.md G-INT-02 执行层) ----
  // 注册表:kz-interact.js 与页面脚本经 kzCharts.instances 反查 chart,NEVER 自建全局变量。
  var INSTANCES = [];
  function register(el, chart, option) { INSTANCES.push({ el: el, chart: chart, option: option }); return chart; }
  function findByEl(el) { for (var i = 0; i < INSTANCES.length; i++) { if (INSTANCES[i].el === el) return INSTANCES[i]; } return null; }

  // 数据点可携带 {value, low, high, stat:'mean±SD'|'median±IQR'};mount 时自动注入区间辅助系列(kzAux)。
  // 柱图 → 果冻虚化胶囊影条:aux 用原生 bar + barGap:'-100%' 与主柱同槽重叠,布局引擎天然居中
  //   (NEVER 手工算分组偏移——barWidth/barMaxWidth/barGap 任意组合下手算必然跑偏,2026-09-08 用户实证);
  // 折线 → 堆叠差值虚化区间带。辅助系列 animation:false(直出终态,NEVER 手工动画)。
  function normPoint(d) { return (d && typeof d === 'object' && !Array.isArray(d) && d.value !== undefined) ? d : { value: d }; }
  function applyRange(option, chart) {
    var series = option.series || [];
    var out = [];
    var hasAux = false;
    series.forEach(function (s, si) {
      var pts = (s.data || []).map(normPoint);
      var hasRange = s.type !== 'pie' && pts.some(function (p) { return p.low !== undefined && p.high !== undefined; });
      out.push(s);
      if (!hasRange) { if (s.type === 'bar' || s.type === 'line') s.data = pts.map(function (p) { return p.low !== undefined ? p : p.value; }); return; }
      hasAux = true;
      var baseColor = s.kzBaseColor || (s.itemStyle && typeof s.itemStyle.color === 'string' ? s.itemStyle.color : null) || '#B98218';
      function tip() {
        if (!s.tooltip || !s.tooltip.formatter) {
          s.tooltip = { formatter: function (p) {
            var d = normPoint((s.data || [])[p.dataIndex]);
            var t = p.marker + ' ' + p.seriesName + ' ' + p.name + ':<b>' + (d && d.value !== undefined ? d.value : p.value) + '</b>';
            if (d && d.low !== undefined) t += '<br><span style="opacity:.75">' + (d.stat || '区间') + ' ' + d.low + ' – ' + d.high + '</span>';
            return t;
          } };
        }
      }
      if (s.type === 'bar' && !s.stack) {
        var horiz = (option.xAxis && (Array.isArray(option.xAxis) ? option.xAxis[0] : option.xAxis).type === 'value');
        var wdata = [];
        pts.forEach(function (p, ci) { if (p.low !== undefined) wdata.push(horiz ? [p.value, ci, p.low, p.high] : [ci, p.value, p.low, p.high]); });
        var mainOrdinal = series.slice(0, si + 1).filter(function (x) { return x.type === 'bar' && !x.stack; }).length - 1;
        var mainSlot = out.length - 1; // 主系列在最终 out 数组的真实下标(实测换算必须用它,NEVER 用相对序号)
        var measured = { cx: null }; // 两遍定位:首帧公式位,finished 后实测柱中心回填(任何 barWidth/barGap/封顶组合皆居中)
        function fallbackX(api, ci, n) {
          var W = horiz ? api.size([0, 1])[1] : api.size([1, 0])[0];
          var bw = Math.min(typeof s.barWidth === 'number' ? s.barWidth : 44, W * 0.6);
          var band = horiz ? api.coord([api.value(0), ci])[1] : api.coord([ci, api.value(0)])[1];
          return band + (mainOrdinal - (n - 1) / 2) * bw * 1.1;
        }
        var auxId = (s.id || s.name || ('s' + si)) + '·区间';
        // 果冻须线(NEVER 胶囊光晕):主干 low→high + 两端 T 帽,圆头粗线贴合果冻柱语言;
        // 帽宽跟随实测柱粗(横条自动压宽时比例不变),中心由校正器实测回填。
        var ghostRender = function (params, api) {
            var ci = horiz ? api.value(1) : api.value(0);
            var lo = api.value(2), hi = api.value(3);
            var mc = measured.cx && measured.cx[ci];
            var n = series.filter(function (x) { return x.type === 'bar' && !x.stack; }).length;
            var center = mc !== undefined && mc !== null ? mc : fallbackX(api, ci, n);
            var W = horiz ? api.size([0, 1])[1] : api.size([1, 0])[0];
            var bw = Math.min(typeof s.barWidth === 'number' ? s.barWidth : 44, W * 0.6);
            var mw = measured.w && measured.w[ci];
            var capW = Math.max(10, Math.min((mw || bw) * 0.62, 26));
            var ink = rgba(baseColor, 0.9);
            var pen = { stroke: ink, lineWidth: 3, lineCap: 'round',
              shadowColor: rgba(baseColor, 0.35), shadowBlur: 4, shadowOffsetY: 1 };
            var box = { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height };
            function clx(x) { return Math.max(box.x, Math.min(box.x + box.width, x)); }
            function cly(y) { return Math.max(box.y, Math.min(box.y + box.height, y)); }
            var kids;
            if (!horiz) {
              var yH = cly(api.coord([ci, hi])[1]), yL = cly(api.coord([ci, lo])[1]);
              kids = [
                { type: 'line', shape: { x1: center, y1: yH, x2: center, y2: yL }, style: pen },
                { type: 'line', shape: { x1: center - capW / 2, y1: yH, x2: center + capW / 2, y2: yH }, style: pen },
                { type: 'line', shape: { x1: center - capW / 2, y1: yL, x2: center + capW / 2, y2: yL }, style: pen }
              ];
            } else {
              var xL = clx(api.coord([lo, ci])[0]), xH = clx(api.coord([hi, ci])[0]);
              kids = [
                { type: 'line', shape: { x1: xL, y1: center, x2: xH, y2: center }, style: pen },
                { type: 'line', shape: { x1: xL, y1: center - capW / 2, x2: xL, y2: center + capW / 2 }, style: pen },
                { type: 'line', shape: { x1: xH, y1: center - capW / 2, x2: xH, y2: center + capW / 2 }, style: pen }
              ];
            }
            return { type: 'group', children: kids };
        };
        function auxSeries(data) {
          return { name: s.name + '·区间', id: auxId, type: 'custom', kzAux: true, z: 6, silent: true, animation: false,
            tooltip: { show: false }, legendHoverLink: false, renderItem: ghostRender, data: data };
        }
        out.push(auxSeries(wdata));
        (option.__kzRangeJobs = option.__kzRangeJobs || []).push({
          aux: auxSeries, wdata: wdata, horiz: horiz, mainOrdinal: mainOrdinal, mainSlot: mainSlot, measured: measured
        });
        tip();
      } else if (s.type === 'line') {
        var lower = [], delta = [];
        pts.forEach(function (p) {
          if (p.low !== undefined) { lower.push(p.low); delta.push(+(p.high - p.low).toFixed(4)); }
          else { lower.push(null); delta.push(null); }
        });
        var stackId = 'kzband-' + si;
        out.push(
          { name: s.name + '·区间下轨', type: 'line', kzAux: true, stack: stackId, data: lower, silent: true, animation: false,
            lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, symbol: 'none', tooltip: { show: false }, emphasis: { disabled: true } },
          { name: s.name + '·区间', type: 'line', kzAux: true, stack: stackId, data: delta, silent: true, animation: false,
            lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, symbol: 'none', tooltip: { show: false }, emphasis: { disabled: true },
            areaStyle: { color: baseColor, opacity: 0.12 } }
        );
        tip();
      }
      s.data = pts.map(function (p) { return p.low !== undefined ? p : p.value; });
    });
    if (hasAux) {
      option.series = out;
      option.legend = option.legend || {};
      if (option.legend.show !== false && !option.legend.data) {
        option.legend.data = series.map(function (s) { return s.name; }).filter(Boolean);
      }
    }
    return option;
  }

  // ---- 2.6 柱区间实测校正器(每图单一 finished 监听,一次扫描全部区间 job,最后一次 setOption) ----
  function attachRangeCorrector(chart, jobs) {
    if (!jobs || !jobs.length || !chart || !chart.on) return;
    var seriesList = jobs.__series || [];
    function correct() {
      var dl = chart.getZr().storage.getDisplayList(false, true);
      var barsRect = [];
      for (var di = 0; di < dl.length; di++) {
        var d = dl[di];
        if (d.type === 'rect' && d.style && d.style.fill && d.style.fill.colorStops && !d.style.stroke) barsRect.push(d);
      }
      if (!barsRect.length) return;
      var corrList = [];
      jobs.forEach(function (job) {
        var next = {}, nextW = {};
        job.wdata.forEach(function (row) {
          var ci = job.horiz ? row[1] : row[0], val = job.horiz ? row[0] : row[1];
          var bandC = chart.convertToPixel({ seriesIndex: job.mainSlot }, job.horiz ? [val, ci] : [ci, val]);
          var bcx = job.horiz ? bandC[1] : bandC[0];
          var bandW = null;
          try {
            var a = chart.convertToPixel({ seriesIndex: job.mainSlot }, job.horiz ? [val, ci] : [ci, val]);
            var b2 = chart.convertToPixel({ seriesIndex: job.mainSlot }, job.horiz ? [val, ci + 1] : [ci + 1, val]);
            bandW = Math.abs(job.horiz ? b2[1] - a[1] : b2[0] - a[0]);
          } catch (e) {}
          if (!bandW) bandW = 200;
          var inBand = barsRect.filter(function (r) {
            var c = job.horiz ? (r.shape.y + r.shape.height / 2) : (r.shape.x + r.shape.width / 2);
            return Math.abs(c - bcx) < bandW / 2;
          }).sort(function (r1, r2) { return job.horiz ? (r1.shape.y - r2.shape.y) : (r1.shape.x - r2.shape.x); });
          var pick = inBand[job.mainOrdinal] || inBand[0];
          if (pick) {
            next[ci] = job.horiz ? (pick.shape.y + pick.shape.height / 2) : (pick.shape.x + pick.shape.width / 2);
            nextW[ci] = job.horiz ? pick.shape.height : pick.shape.width;
          }
        });
        var changed = !job.measured.cx || Object.keys(next).some(function (k) { return Math.abs((job.measured.cx[k] || -9999) - next[k]) > 0.5; });
        if (changed) {
          job.measured.cx = next; job.measured.w = nextW;
          job.measured.tick = (job.measured.tick || 0) + 1;
          var c = job.aux(job.wdata.map(function (r) { return r.slice(); }));
          c.z = 6 + job.measured.tick * 1e-4; // 微差强制判脏(行引用全同会被跳过重渲,实证)
          corrList.push(c);
        }
      });
      if (corrList.length) {
        chart.setOption({ series: corrList }, { silent: true });
        return true;
      }
      return false;
    }
    var retries = 0;
    function tick() { // 动画期几何是瞬态值:有变更就 350ms 后复校,直至连续两次静止(封顶 8 次防振荡)
      if (correct()) { if (++retries < 8) setTimeout(tick, 350); }
      else retries = 0; // 静止后清零,后续交互(chip/编辑)触发的重排仍可自愈
    }
    chart.on('finished', tick);
    setTimeout(tick, 900);   // MOTION.maxTotal=1200:延迟校正兜底
    setTimeout(tick, 1800);
  }

  // ---- 3. 统一创建入口:kzCharts.mount(el, option, opts?) ----
  // opts.motion: 'read'|'jelly'|'hero' 覆盖; opts.lazy:false 关闭 IO 延迟(默认滚动入场)
  function mount(el, option, opts) {
    opts = opts || {};
    var m = opts.motion ? MOTION[opts.motion] : motionFor(el);
    var useAnim = !frozen() && !opts.static;
    var base = {
      animation: useAnim,
      animationDuration: m.duration,
      animationEasing: m.easing,
      animationDelay: function (idx) { return Math.min(idx * m.stagger, m.maxTotal - m.duration); },
      animationDurationUpdate: 300,
      animationEasingUpdate: 'cubicOut',
      universalTransition: true
    };
    var chart = echarts.init(el, 'kz', { renderer: 'canvas' });
    (option.series || []).forEach(function (s) { if (s && s.name && !s.id) s.id = s.name; }); // 交互层按 id 局部更新
    var finalOption = applyRange(Object.assign({}, base, option), chart);
    function render() {
      if (render.done) return; render.done = true;
      chart.setOption(finalOption);
    }
    if (opts.lazy === false || frozen() || !('IntersectionObserver' in window)) { render(); }
    else {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { io.disconnect(); render(); } });
      }, { threshold: 0.25 });
      io.observe(el);
    }
    // 冻结态下若已渲染过动画,重设为静态终态
    if (frozen()) { /* animation:false 已保证直出终态 */ }
    if (window.ResizeObserver) {
      new ResizeObserver(function () { chart.resize(); }).observe(el);
    } else {
      window.addEventListener('resize', function () { chart.resize(); });
    }
    var __rangeJobs = finalOption.__kzRangeJobs;        // 摘下再 setOption:job 含闭包/引用,深拷贝会循环爆炸
    if (__rangeJobs) delete finalOption.__kzRangeJobs;
    attachRangeCorrector(chart, __rangeJobs);
    register(el, chart, finalOption);
    if (typeof window.CustomEvent === 'function') {
      try { document.dispatchEvent(new CustomEvent('kz:chart-mounted', { detail: { el: el } })); } catch (e) {}
    }
    return chart;
  }

  // ---- 4. 3D 合规断言(html_charts.md §5 / G-CHART-04) ----
  // 3D 系列 MUST 数字直标;NEVER pie3D。
  function assert3D(option) {
    var warn = [];
    (option.series || []).forEach(function (s) {
      if (s.type === 'pie3D' || s.type === 'pie' && s.label && s.label.show && s.itemStyle && s.itemStyle.opacity === undefined && false) { /* noop */ }
      if (/3D$/.test(s.type || '')) {
        if (s.type === 'pie3D') warn.push('pie3D 被禁止(G-CHART-04)');
        if (!s.label || s.label.show !== true) warn.push(s.type + ' 缺数字直标 label.show:true(G-CHART-04)');
      }
    });
    warn.forEach(function (w) { console.warn('[kz-charts] ' + w); });
    return warn.length === 0;
  }


  // ---- 5. 果冻质感皮肤(html_charts.md §5 执行层;微微立体+果冻柔边,NEVER 棱角科学图表风) ----
  function shade(hex, ratio) { // ratio>0 提亮,<0 压暗(柔和幅度)
    var n = parseInt(hex.slice(1), 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
    var t = ratio > 0 ? 255 : 0, a = Math.abs(ratio);
    r = Math.round(r + (t - r) * a); g = Math.round(g + (t - g) * a); b = Math.round(b + (t - b) * a);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }
  function rgba(hex, a) {
    var n = parseInt(hex.slice(1), 16);
    return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a + ')';
  }
  // 果冻纵向光泽:顶部高光带 -> 主体 -> 底部微深(柔和,不发黑)
  function jellyGrad(base) {
    var g = new echarts.graphic.LinearGradient(0, 0, 0, 1);
    g.addColorStop(0, shade(base, 0.62));
    g.addColorStop(0.16, shade(base, 0.34));
    g.addColorStop(0.52, base);
    g.addColorStop(1, shade(base, -0.10));
    return g;
  }
  // 果冻柱:jzCharts.jellyBar({name, data, color, motion?}) —— 原生 bar 系列,全圆角胶囊+光泽渐变+柔影。
  // 用原生 bar 保证 ECharts 入场动画(含 backOut 单次过冲)与 resize 重排天然可靠。
  function jellyBar(cfg) {
    var c = cfg.color || '#FF9900';
    return {
      type: 'bar',
      name: cfg.name,
      data: cfg.data,
      barMaxWidth: cfg.barMaxWidth || 44,
      itemStyle: {
        borderRadius: cfg.radius || [16, 16, 12, 12],
        color: jellyGrad(c),
        shadowColor: rgba(c, 0.26), shadowBlur: 16, shadowOffsetY: 6
      },
      emphasis: {
        itemStyle: { shadowColor: rgba(c, 0.40), shadowBlur: 26, shadowOffsetY: 8 }
      },
      kzBaseColor: c,
      label: { show: true, position: 'top', fontWeight: 700, fontSize: 13, color: '#0F1115' }
    };
  }
  // 折线果冻肤:圆润曲线+渐变面积+节点微光
  function lineSkin(series) {
    series.type = series.type || 'line';
    var c = series.color || '#FF9900';
    series.kzBaseColor = c;
    series.smooth = true;
    series.symbol = series.symbol || 'circle';
    series.symbolSize = series.symbolSize || 8;
    series.lineStyle = Object.assign({ width: 3, cap: 'round', join: 'round', shadowColor: rgba(c, 0.25), shadowBlur: 8, shadowOffsetY: 3 }, series.lineStyle || {});
    series.itemStyle = Object.assign({ color: c, borderColor: '#FFFFFF', borderWidth: 2, shadowColor: rgba(c, 0.35), shadowBlur: 10 }, series.itemStyle || {});
    if (series.areaStyle !== false) {
      var g = new echarts.graphic.LinearGradient(0, 0, 0, 1);
      g.addColorStop(0, rgba(c, 0.22)); g.addColorStop(1, rgba(c, 0.02));
      series.areaStyle = Object.assign({ color: g }, series.areaStyle || {});
    }
    return series;
  }
  // 环/饼质感皮肤:渐变扇区+柔和投影+悬浮偏移(原生动画保留)
  function pieSkin(series) {
    series.itemStyle = Object.assign({
      borderColor: '#FFFFFF', borderWidth: 3, borderRadius: 10,
      shadowBlur: 14, shadowColor: 'rgba(15,17,21,.14)', shadowOffsetY: 4
    }, series.itemStyle || {});
    series.emphasis = Object.assign({ scale: true, scaleSize: 6, itemStyle: { shadowBlur: 22, shadowColor: 'rgba(15,17,21,.2)' } }, series.emphasis || {});
    return series;
  }

  window.kzCharts = { mount: mount, assert3D: assert3D, MOTION: MOTION, frozen: frozen, jellyBar: jellyBar, lineSkin: lineSkin, pieSkin: pieSkin, shade: shade, rgba: rgba, applyRange: applyRange, instances: INSTANCES, findByEl: findByEl };
})();
