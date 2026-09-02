import { useCallback, useEffect, useMemo, useReducer } from "react";
import { createMedicalMonitoringProductApi } from "./medicalMonitoringProductApi.mjs";
import {
  ADMISSION_SUPPORTED_SUFFIX_TEXT,
  admissionPrimaryAction,
  admissionSecondaryActions,
  admissionStepView,
  admissionTechnicalRows,
  admissionWizardReducer,
  createAdmissionWizardState,
  readAdmissionProfile,
  validateAdmissionSourceDir,
} from "./medicalMonitoringAdmissionWizardState.mjs";
import "./medicalMonitoringAdmissionWizard.css";

function TechnicalRows({ rows }) {
  if (!rows) return null;
  return (
    <dl className="monitoring-admission-tech-list">
      {rows.map((row) => (
        <div className="monitoring-admission-tech-row" key={row.label}>
          <dt>{row.label}</dt>
          <dd>
            {row.files ? (
              <ul className="monitoring-admission-tech-files">
                {row.files.map((file) => (
                  <li key={file.name}>
                    {file.name}
                    {file.sizeText ? ` · ${file.sizeText}` : ""}
                    {file.digest ? ` · 校验值 ${file.digest}` : ""}
                  </li>
                ))}
              </ul>
            ) : (
              row.value
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function MedicalMonitoringAdmissionWizardView({
  state,
  onSourceDirChange,
  onSourceFilesChange,
  onPrimaryAction,
  onSecondaryAction,
}) {
  const phase = state?.phase || "input";
  const stepIndex = state?.stepIndex || 0;
  const profile = state?.profile || null;
  const error = state?.error || null;
  const steps = admissionStepView(state);
  const primary = admissionPrimaryAction(state);
  const secondary = admissionSecondaryActions(state);
  const validation = validateAdmissionSourceDir(state?.sourceDir);
  const technical = profile ? admissionTechnicalRows(profile.technical) : null;

  return (
    <section
      className="monitoring-admission"
      data-admission-phase={phase}
      aria-label="数据接入向导"
    >
      <header className="monitoring-admission-head">
        <h2>数据接入</h2>
        <p>
          分三步把本地数据文件接入当前项目：系统先保留副本再识别结构，原始文件保持不变。
        </p>
      </header>

      <ol className="monitoring-admission-steps" aria-label="接入步骤">
        {steps.map((step) => (
          <li
            key={step.key}
            className={`monitoring-admission-step is-${step.kind}`}
            aria-current={step.kind === "current" ? "step" : undefined}
          >
            <span className="monitoring-admission-step-index">{step.indexText}</span>
            <span className="monitoring-admission-step-title">{step.title}</span>
          </li>
        ))}
      </ol>

      <div className="monitoring-admission-body">
        {phase === "done" ? (
          <div className="monitoring-admission-done" role="status">
            <p className="monitoring-admission-done-title">数据已完成接入</p>
            <p className="monitoring-admission-big">{profile?.summaryText || ""}</p>
            <p className="monitoring-admission-minor">
              如需替换本批数据，请重新发起导入；已接入的数据版本不会被覆盖。
            </p>
          </div>
        ) : stepIndex === 0 ? (
          <div className="monitoring-admission-field">
            <span className="monitoring-admission-field-label">选择本机数据文件夹</span>
            <label className="monitoring-admission-picker" htmlFor="monitoring-admission-files">
              <input
                id="monitoring-admission-files"
                type="file"
                multiple
                webkitdirectory=""
                accept=".csv,.xls,.xlsx,.xlsm"
                disabled={phase === "creating"}
                onChange={(event) => onSourceFilesChange?.(event.target.files)}
              />
              <span>选择数据文件夹</span>
            </label>
            {state?.selectedFiles?.length ? (
              <p className="monitoring-admission-selection" role="status">
                已选择“{state.selectedFolderName}”，共 {state.selectedFiles.length} 个文件
              </p>
            ) : null}
            <p className="monitoring-admission-hint">
              支持 {ADMISSION_SUPPORTED_SUFFIX_TEXT} 文件；系统会保留一份项目数据副本，原始文件不会修改。
            </p>
            {!state?.selectedFiles?.length && !state?.sourceDir ? (
              <p className="monitoring-admission-prompt">选择文件夹后即可开始导入。</p>
            ) : null}
            <details className="monitoring-admission-manual">
              <summary>无法选择文件夹时，手动填写数据位置</summary>
              <label htmlFor="monitoring-admission-source">数据位置</label>
              <input
                id="monitoring-admission-source"
                type="text"
                value={state?.sourceDir || ""}
                placeholder="填写数据文件所在的目录位置"
                disabled={phase === "creating"}
                onChange={(event) => onSourceDirChange?.(event.target.value)}
              />
              {state?.sourceDir && !validation.ok ? (
                <p className="monitoring-admission-warning">{validation.text}</p>
              ) : null}
            </details>
          </div>
        ) : phase === "reading" && !profile ? (
          <p className="monitoring-admission-loading" role="status">
            正在识别数据结构，请稍候…
          </p>
        ) : profile && stepIndex === 1 ? (
          <div className="monitoring-admission-review">
            <p className="monitoring-admission-big monitoring-admission-summary">
              {profile.summaryText}
            </p>
            {profile.tables.map((table) => (
              <section
                key={`${table.name}-${table.sourceFile}`}
                className="monitoring-admission-table"
                aria-label={`数据表 ${table.name}`}
              >
                <header className="monitoring-admission-table-head">
                  <h3>{table.name}</h3>
                  <span className="monitoring-admission-table-meta">
                    {table.rowsText} · {table.columnCount} 列{table.sourceFile ? ` · 来源 ${table.sourceFile}` : ""}
                  </span>
                </header>
                <ul className="monitoring-admission-columns">
                  {table.columns.map((column) => (
                    <li key={column.name}>
                      <span className="monitoring-admission-column-name">{column.name}</span>
                      <span className="monitoring-admission-column-meta">
                        {[column.typeText, column.missingText, column.dateRangeText].filter(Boolean).join(" · ")}
                      </span>
                      {column.roles.length > 0 ? (
                        <span className="monitoring-admission-roles">{column.roles.join("、")}</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
            <details className="monitoring-admission-technical">
              <summary>技术详情</summary>
              <TechnicalRows rows={technical} />
            </details>
          </div>
        ) : profile && stepIndex === 2 ? (
          <div className="monitoring-admission-confirm">
            {profile.pendingColumns.length > 0 ? (
              <>
                <p className="monitoring-admission-pending-note">
                  系统为以下 {profile.pendingColumns.length} 列识别出可能的数据含义，供后续字段核对时参考；本步骤不会修改任何数据。
                </p>
                <ul className="monitoring-admission-pending">
                  {profile.pendingColumns.map((item) => (
                    <li key={`${item.tableName}-${item.columnName}`}>
                      <span className="monitoring-admission-pending-field">
                        {item.tableName} · {item.columnName}
                      </span>
                      <span className="monitoring-admission-roles">{item.roles.join("、")}</span>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="monitoring-admission-pending-note">
                本批数据没有需要人工判断的字段，可直接完成接入。
              </p>
            )}
            <p className="monitoring-admission-minor">
              完成接入后，系统会保存本次识别结果；在后续字段对应关系核对完成前，不会用于监查分析。
            </p>
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="monitoring-admission-alert" role="alert">
          <p className="monitoring-admission-alert-text">{error.serverText}</p>
          {error.guidance?.length ? (
            <ul className="monitoring-admission-alert-guide">
              {error.guidance.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <footer className="monitoring-admission-actions">
        {secondary.map((action) => (
          <button
            key={action.key}
            type="button"
            className="monitoring-admission-secondary"
            onClick={() => onSecondaryAction?.(action.key)}
          >
            {action.label}
          </button>
        ))}
        <button
          type="button"
          className="monitoring-admission-primary"
          disabled={primary.disabled}
          aria-disabled={Boolean(primary.disabled)}
          onClick={() => onPrimaryAction?.(primary.key)}
        >
          {primary.label}
        </button>
      </footer>
    </section>
  );
}

export function MedicalMonitoringAdmissionWizard({ projectId, api: providedApi, onAdmitted }) {
  const api = useMemo(
    () => providedApi || createMedicalMonitoringProductApi(),
    [providedApi],
  );
  const [state, dispatch] = useReducer(
    admissionWizardReducer,
    projectId,
    (pid) => createAdmissionWizardState({ projectId: pid }),
  );

  const submitImport = useCallback(async () => {
    dispatch({ type: "import-start" });
    if (!state.projectId.trim()) return;
    try {
      const payload = state.selectedFiles.length
        ? await api.createDataAdmissionUpload(state.projectId, state.selectedFiles)
        : await api.createDataAdmission(state.projectId, { source_dir: state.sourceDir });
      dispatch({ type: "import-created", payload });
    } catch (error) {
      dispatch({ type: "error", error });
    }
  }, [api, state.projectId, state.selectedFiles, state.sourceDir]);

  useEffect(() => {
    if (state.phase !== "reading" || !state.attemptId) return undefined;
    let cancelled = false;
    readAdmissionProfile({
      api,
      projectId: state.projectId,
      attemptId: state.attemptId,
    }).then((result) => {
      if (cancelled) return;
      if (!result.ok) {
        dispatch({ type: "error", recovery: result.recovery });
        return;
      }
      dispatch({ type: "profile-loaded", payload: result.payload });
      onAdmitted?.(result.status);
    });
    return () => {
      cancelled = true;
    };
  }, [api, state.phase, state.attemptId, state.projectId, onAdmitted]);

  const onPrimaryAction = useCallback((key) => {
    if (key === "import") {
      submitImport();
      return;
    }
    if (key === "retry") {
      // A create failure reruns the import flow; a read failure re-enters the
      // reading phase, which the effect below observes.
      if ((state.retryTarget || "create") === "create") {
        submitImport();
      } else {
        dispatch({ type: "retry" });
      }
      return;
    }
    dispatch({ type: key });
  }, [submitImport, state.retryTarget]);

  const onSecondaryAction = useCallback((key) => {
    dispatch({ type: key });
  }, []);

  return (
    <MedicalMonitoringAdmissionWizardView
      state={state}
      onSourceDirChange={(value) => dispatch({ type: "source-dir-change", value })}
      onSourceFilesChange={(files) => dispatch({ type: "source-files-change", files })}
      onPrimaryAction={onPrimaryAction}
      onSecondaryAction={onSecondaryAction}
    />
  );
}

export default MedicalMonitoringAdmissionWizard;
