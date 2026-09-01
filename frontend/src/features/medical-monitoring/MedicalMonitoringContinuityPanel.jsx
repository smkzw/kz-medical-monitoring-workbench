import { useMemo, useState } from "react";
import {
  MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
} from "./medicalMonitoringContinuityProjection.mjs";
import {
  MONITORING_CONTINUITY_CHANGE_FILTERS,
  MONITORING_CONTINUITY_OBJECT_FILTERS,
  MONITORING_CONTINUITY_SEVERITY_FILTERS,
  createMonitoringContinuityFilterState,
  filterMonitoringContinuityRows,
  monitoringContinuityRowJourneyTarget,
  monitoringContinuityRowSeverityLabel,
  monitoringContinuityRowSourceTarget,
  monitoringContinuityTruncationText,
} from "./medicalMonitoringContinuityFilter.mjs";
import "./medicalMonitoringContinuityPanel.css";

// Five key counts in the frozen display order (contract §4): 新增、升级、
// 重开、需重新判断、中高风险. The last one is the single semantic emphasis.
export const MONITORING_CONTINUITY_KEY_COUNTS = Object.freeze([
  { key: "new", label: "新增" },
  { key: "upgraded", label: "升级" },
  { key: "reopened", label: "重开" },
  { key: "needs_rejudgment", label: "需重新判断" },
  { key: "mid_high_total", label: "中高风险" },
]);

function clean(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value).trim() || fallback;
}

function SeverityChips({ value, onChange }) {
  return (
    <div className="monitoring-continuity-filter-group" role="group" aria-label="风险等级筛选">
      {MONITORING_CONTINUITY_SEVERITY_FILTERS.map((option) => (
        <button
          type="button"
          key={option.value}
          className={`monitoring-continuity-chip${option.value === value ? " is-active" : ""}`}
          aria-pressed={option.value === value}
          data-severity-filter={option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function ChangeChips({ value, onChange }) {
  return (
    <div className="monitoring-continuity-filter-group" role="group" aria-label="变化类型筛选">
      {MONITORING_CONTINUITY_CHANGE_FILTERS.map((option) => (
        <button
          type="button"
          key={option.value}
          className={`monitoring-continuity-chip${option.value === value ? " is-active" : ""}`}
          aria-pressed={option.value === value}
          data-change-filter={option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function ObjectChips({ value, onChange }) {
  return (
    <div className="monitoring-continuity-filter-group" role="group" aria-label="对象类别筛选">
      {MONITORING_CONTINUITY_OBJECT_FILTERS.map((option) => (
        <button
          type="button"
          key={option.value}
          className={`monitoring-continuity-chip${option.value === value ? " is-active" : ""}`}
          aria-pressed={option.value === value}
          data-object-filter={option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function ContinuityRow({
  row,
  journeyTarget,
  sourceTarget,
  onJourney,
  onSource,
}) {
  const severityLabel = monitoringContinuityRowSeverityLabel(row);
  const dateLabel = clean(row.date_label, "日期待确认");
  const note = [
    row.data_change_text,
    row.attention_text,
  ].filter(Boolean).join(" · ");
  return (
    <li className="monitoring-continuity-row" data-object-type={row.object_type} data-change-kind={row.change_kind}>
      <div className="monitoring-continuity-row-head">
        <div className="monitoring-continuity-row-tags">
          <span className="monitoring-continuity-tag is-object">{row.object_type_text}</span>
          <span className="monitoring-continuity-tag is-change">{row.change_text}</span>
          {severityLabel ? <span className="monitoring-continuity-tag is-severity">{severityLabel}</span> : null}
        </div>
        <div className="monitoring-continuity-row-actions" role="group" aria-label="下钻操作">
          {row.object_type === "risk" ? (
            <button
              type="button"
              className="monitoring-product-button is-small"
              disabled={!journeyTarget}
              onClick={() => onJourney?.(row)}
            >
              {journeyTarget ? "进入旅程" : "受试者时间范围待确认"}
            </button>
          ) : null}
          <button
            type="button"
            className="monitoring-product-button is-small"
            disabled={!sourceTarget}
            onClick={() => onSource?.(row)}
          >
            {sourceTarget ? "查看来源" : "原始记录位置待确认"}
          </button>
        </div>
      </div>
      <strong className="monitoring-continuity-row-title">{row.title}</strong>
      <p className="monitoring-continuity-row-meta">{row.site_label} · {row.subject_label} · {dateLabel}</p>
      {note ? <p className="monitoring-continuity-row-note">{note}</p> : null}
      {row.reason_text ? <p className="monitoring-continuity-row-reason">{row.reason_text}</p> : null}
    </li>
  );
}

export function MedicalMonitoringContinuityPanel({
  continuity,
  unavailable = "",
  loading = false,
  resultPayload,
  onJourney,
  onSource,
  omitCounts = false,
}) {
  const [filter, setFilter] = useState(createMonitoringContinuityFilterState);
  const setFilterField = (field, value) => {
    setFilter((current) => ({ ...current, [field]: value }));
  };

  const comparison = continuity?.kind === "continuity" ? continuity.comparison : null;
  const rows = Array.isArray(comparison?.rows) ? comparison.rows : [];
  const filteredRows = useMemo(
    () => filterMonitoringContinuityRows(rows, filter),
    [filter, rows],
  );

  if (loading) {
    return (
      <section className="monitoring-continuity-panel is-placeholder" data-monitoring-continuity data-monitoring-continuity-state="loading" aria-label="本轮变化">
        <span className="monitoring-eyebrow">连续性比较</span>
        <p>本轮变化加载中…</p>
      </section>
    );
  }

  if (unavailable || !comparison) {
    return (
      <section className="monitoring-continuity-panel is-placeholder is-unavailable" data-monitoring-continuity data-monitoring-continuity-state="unavailable" aria-label="本轮变化">
        <span className="monitoring-eyebrow">连续性比较</span>
        <p>{unavailable || MONITORING_CONTINUITY_UNAVAILABLE_TEXT}</p>
      </section>
    );
  }

  const counts = comparison.change_counts || {};
  const truncationText = monitoringContinuityTruncationText(comparison);
  const subjectQuery = filter.subjectQuery || "";

  return (
    <section className="monitoring-continuity-panel" data-monitoring-continuity data-monitoring-continuity-state="ready" aria-label="本轮变化">
      <header className="monitoring-continuity-head">
        <div>
          <span className="monitoring-eyebrow">连续性比较</span>
          <h2>本轮变化</h2>
          <p>{comparison.comparison_text}</p>
        </div>
      </header>
      {omitCounts ? null : (
        <dl className="monitoring-continuity-counts">
          {MONITORING_CONTINUITY_KEY_COUNTS.map((item) => (
            <div key={item.key} className={`monitoring-continuity-count${item.key === "mid_high_total" ? " is-key" : ""}`}>
              <dt>{item.label}</dt>
              <dd data-count-key={item.key}>{counts[item.key] ?? 0}</dd>
            </div>
          ))}
        </dl>
      )}
      <div className="monitoring-continuity-filters">
        <SeverityChips value={filter.severity} onChange={(value) => setFilterField("severity", value)} />
        <ChangeChips value={filter.changeKind} onChange={(value) => setFilterField("changeKind", value)} />
        <div className="monitoring-continuity-filter-row">
          <ObjectChips value={filter.objectType} onChange={(value) => setFilterField("objectType", value)} />
          <div className="monitoring-continuity-filter-extra">
            <label className="monitoring-continuity-toggle">
              <input
                type="checkbox"
                checked={filter.needsRejudgmentOnly}
                onChange={(event) => setFilterField("needsRejudgmentOnly", event.target.checked)}
              />
              <span>仅看需重新判断</span>
            </label>
            <input
              className="monitoring-continuity-subject-search"
              type="search"
              value={subjectQuery}
              placeholder="搜索受试者"
              aria-label="搜索受试者"
              onChange={(event) => setFilterField("subjectQuery", event.target.value)}
            />
          </div>
        </div>
      </div>
      {rows.length === 0 ? (
        <p className="monitoring-continuity-empty">本轮没有变化记录。</p>
      ) : filteredRows.length === 0 ? (
        <p className="monitoring-continuity-empty">当前筛选下没有变化记录。</p>
      ) : (
        <ul className="monitoring-continuity-list">
          {filteredRows.map((row) => (
            <ContinuityRow
              key={row.row_ref}
              row={row}
              journeyTarget={monitoringContinuityRowJourneyTarget(row, resultPayload)}
              sourceTarget={monitoringContinuityRowSourceTarget(row)}
              onJourney={onJourney}
              onSource={onSource}
            />
          ))}
        </ul>
      )}
      {truncationText ? <p className="monitoring-continuity-truncate">{truncationText}</p> : null}
    </section>
  );
}

export default MedicalMonitoringContinuityPanel;
