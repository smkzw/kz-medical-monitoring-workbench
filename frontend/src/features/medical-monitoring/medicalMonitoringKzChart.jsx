import { useEffect, useMemo, useRef } from "react";

// kz 图表引擎 React 封装：全部经 kzCharts.mount（'kz' 主题），绝不裸 echarts.init。
// 业务侧只组装 option；果冻皮肤/动画分级/冻结态/resize 由执行层接管。

const KZ_PALETTE = ["#FF9900", "#407AAA", "#587B3B", "#A85F34", "#FFCC00", "#AAA6A1"];
const KZ_RISK_RED = "#C00000";
const SEVERITY_ORDER = ["low", "medium", "high", "critical"];
const SEVERITY_ZH = { low: "低", medium: "中", high: "高", critical: "重" };
const SEVERITY_COLOR = { low: "#587B3B", medium: "#FFCC00", high: "#A85F34", critical: "#C00000" };

function kzChartsApi() {
  return typeof window !== "undefined" ? window.kzCharts : null;
}

function useKzChart(buildOption, { deps = [], onClick, className = "kz-chart", style } = {}) {
  const containerRef = useRef(null);
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  useEffect(() => {
    const el = containerRef.current;
    const kz = kzChartsApi();
    if (!el || !kz) return undefined;
    let chart;
    try {
      chart = kz.mount(el, buildOption(), { lazy: false });
    } catch {
      return undefined;
    }
    if (onClickRef.current) {
      chart.on("click", (params) => onClickRef.current?.(params));
    }
    return () => {
      try { chart.dispose(); } catch { /* el already detached */ }
    };
    // deps 变化＝新数据面：整体重挂载（payload 重载场景，动画重放可接受）
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return containerRef;
}

// —— 受试者流向桑基（知情同意→筛选→治疗→研究状态） ——————————————
// 数值直标在节点（到达/当前/中高）；连线宽度编码人数且带数值标签；
// 节点/连线点击联动阶段与流向筛选。红色仅用于风险语义。
export function KzSubjectFlowSankey({ flow, selection = {}, onStageSelect, onLinkSelect, height = 420 }) {
  const stages = flow?.state === "ready" ? flow.stages : [];
  const links = flow?.state === "ready" ? flow.links : [];
  const labelByRef = useMemo(() => new Map(stages.map((stage) => [stage.ref, stage.label])), [stages]);

  const handleChartClick = useMemo(() => (params) => {
    if (params?.dataType === "node") {
      const stage = stages.find((item) => item.label === params.name);
      if (stage) onStageSelect?.(stage.ref, "current");
    } else if (params?.dataType === "edge") {
      const edge = params.data;
      const link = links.find((item) => labelByRef.get(item.from) === edge.source && labelByRef.get(item.to) === edge.target);
      if (link) onLinkSelect?.(link.ref);
    }
  }, [stages, links, labelByRef, onStageSelect, onLinkSelect]);

  const buildOption = () => {
    const nodes = stages.map((stage) => ({
      name: stage.label,
      itemStyle: {
        color: stage.kind === "branch_terminal" ? KZ_PALETTE[5] : KZ_PALETTE[stage.column % KZ_PALETTE.length],
        borderColor: "transparent",
      },
      label: {
        show: true,
        formatter: () => {
          const lines = [stage.label, `到达 ${stage.reached} · 当前 ${stage.current}`];
          if (stage.risk > 0) lines.push(`中高 {red|${stage.risk}}`);
          if (stage.reached === 0) lines.push("本截止点无人到达");
          return lines.join("\n");
        },
        rich: { red: { color: KZ_RISK_RED, fontWeight: 700 } },
      },
      emphasis: { focus: "adjacency" },
    }));
    const edges = links.map((link) => ({
      source: labelByRef.get(link.from) || link.from,
      target: labelByRef.get(link.to) || link.to,
      value: link.count,
      lineStyle: { color: "gradient", opacity: 0.34 },
      label: { show: true, formatter: () => String(link.count), fontSize: 12, color: "#404040" },
    }));
    return {
      textStyle: { fontFamily: "inherit" },
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          if (params.dataType === "node") {
            const stage = stages.find((item) => item.label === params.name);
            if (!stage) return params.name;
            return `<strong>${stage.label}</strong><br/>累计到达 ${stage.reached} 人 · 当前停留 ${stage.current} 人<br/>当前伴随中高风险 ${stage.risk} 人`;
          }
          const edge = params.data;
          const link = links.find((item) => labelByRef.get(item.from) === edge.source && labelByRef.get(item.to) === edge.target);
          return `<strong>${edge.source} → ${edge.target}</strong><br/>沿此流向 ${edge.value} 人${link && link.risk > 0 ? `<br/>其中当前中高风险 ${link.risk} 人` : ""}`;
        },
      },
      series: [{
        type: "sankey",
        left: 24,
        right: 140,
        top: 18,
        bottom: 18,
        nodeWidth: 18,
        nodeGap: 22,
        animationDuration: 520,
        animationEasing: "cubicOut",
        data: nodes,
        links: edges,
      }],
    };
  };

  const ref = useKzChart(buildOption, { deps: [stages, links], onClick: handleChartClick });
  return <div ref={ref} className="kz-chart mm-kz-chart" data-kz-chart-motion="read" style={{ height }} role="img" aria-label="受试者阶段流向图（知情同意到研究状态）" />;
}

// —— 风险类型果冻条（聚合行：类型×严重度计数） ————————————————————
export function KzRiskTypeBars({ rows = [], height = 320 }) {
  const aggregateRows = rows.filter((row) => row.aggregate);
  const buildOption = () => {
    if (!aggregateRows.length) return { series: [] };
    const types = [...new Set(aggregateRows.map((row) => row.risk_type))];
    const series = SEVERITY_ORDER
      .filter((severity) => aggregateRows.some((row) => row.severity === severity))
      .map((severity) => ({
        type: "bar",
        name: SEVERITY_ZH[severity],
        stack: "count",
        barMaxWidth: 36,
        itemStyle: {
          color: SEVERITY_COLOR[severity],
          borderRadius: severity === "low" ? [0, 8, 8, 0] : 0,
        },
        label: { show: true, position: "insideRight", color: "#FFFFFF", fontSize: 12 },
        data: types.map((type) => {
          const row = aggregateRows.find((item) => item.risk_type === type && item.severity === severity);
          return row ? row.count : 0;
        }),
      }));
    return {
      textStyle: { fontFamily: "inherit" },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: 130, right: 56, top: 30, bottom: 28 },
      xAxis: { type: "value", minInterval: 1 },
      yAxis: { type: "category", data: types, inverse: true },
      series,
    };
  };
  const ref = useKzChart(buildOption, { deps: [aggregateRows] });
  return <div ref={ref} className="kz-chart mm-kz-chart" style={{ height }} role="img" aria-label="风险类型分布（按严重度堆叠）" />;
}

// —— 中心×临床域 热力图（严重度最高值编码；浅色底） ———————————————
const SEVERITY_LEVEL = { low: 1, medium: 2, high: 3, critical: 4 };

export function KzCenterDomainHeatmap({ cells = [], domains = [], height = 560 }) {
  const domainList = domains.map((item) => item.shortLabel || item.labelZh || item.domain).filter(Boolean);
  const buildOption = () => {
    if (!cells.length) return { series: [] };
    const sites = [...new Set(cells.map((cell) => cell.siteRef))];
    const domainKeys = domains.map((item) => item.domain).filter(Boolean);
    const data = [];
    for (const cell of cells) {
      const x = domainKeys.indexOf(cell.domain);
      const y = sites.indexOf(cell.siteRef);
      if (x >= 0 && y >= 0) {
        data.push([x, y, SEVERITY_LEVEL[cell.severity] ?? 0, cell.riskCount ?? (cell.individualRiskCount ?? 0)]);
      }
    }
    return {
      textStyle: { fontFamily: "inherit" },
      tooltip: {
        position: "top",
        formatter: (params) => {
          const [, y, x, level, count] = params.value;
          const site = sites[y];
          const domain = domainList[x];
          const severityZh = { 0: "无记录", 1: "低", 2: "中", 3: "高", 4: "重" }[level] ?? "—";
          return `<strong>中心 ${site.replace(/^site-/, "")} · ${domain}</strong><br/>最高严重度：${severityZh}<br/>风险锚点 ${count ?? 0} 条`;
        },
      },
      grid: { left: 76, right: 24, top: 30, bottom: 64 },
      xAxis: { type: "category", data: domainList, axisLabel: { interval: 0, rotate: 28 }, splitArea: { show: true } },
      yAxis: { type: "category", data: sites.map((site) => site.replace(/^site-/, "")), splitArea: { show: true } },
      visualMap: {
        min: 0,
        max: 4,
        calculable: false,
        orient: "horizontal",
        left: "center",
        bottom: 0,
        itemWidth: 13,
        text: ["重", "无"],
        inRange: { color: ["#FDFBF7", "#FFCC00", "#A85F34", KZ_RISK_RED] },
      },
      series: [{
        type: "heatmap",
        data,
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 8, shadowColor: "rgba(15,17,21,0.24)" } },
      }],
    };
  };
  const ref = useKzChart(buildOption, { deps: [cells, domains] });
  return <div ref={ref} className="kz-chart mm-kz-chart" style={{ height }} role="img" aria-label="各中心各临床域风险严重度热力图" />;
}

export { KZ_PALETTE, KZ_RISK_RED, SEVERITY_ZH, SEVERITY_COLOR };
