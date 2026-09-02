import { useCallback, useEffect, useMemo, useReducer, useState } from "react";
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
import {
  MAPPING_FOCUS_ALL,
  MAPPING_FOCUS_CRITICAL,
  admissionMappingConfirmReducer,
  admissionMappingPrimaryAction,
  confidencePercent,
  createAdmissionMappingConfirmState,
  mappingCandidateKey,
  mappingDraftMissingAdviceCount,
} from "./medicalMonitoringAdmissionMappingConfirmState.mjs";
import { semanticQualityPresentation } from "./medicalMonitoringFieldMappingState.mjs";
import "./medicalMonitoringAdmissionWizard.css";

function requestKey(prefix) {
  const random = globalThis.crypto?.randomUUID?.()
    || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${random}`;
}

function mappingTypeText(value) {
  return ({
    string: "文本",
    text: "文本",
    decimal: "数值",
    number: "数值",
    date: "日期",
    mixed: "混合内容",
    empty: "空列",
  })[value] || "类型待定";
}

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

function MappingConfirmPanel({
  mappingState,
  onFocusChange,
  onSelectField,
  onFieldFormChange,
  onSaveField,
  onReasonChange,
}) {
  const [activeDomain, setActiveDomain] = useState("all");
  const [search, setSearch] = useState("");
  const candidates = mappingState.payload?.candidates || [];
  const candidateByKey = new Map(candidates.map((item) => [
    mappingCandidateKey({ domain: item.domain, source_field: item.sourceField }),
    item,
  ]));
  const draftFields = Array.isArray(mappingState.draft?.fields)
    ? mappingState.draft.fields
    : [];
  const rows = draftFields.length
    ? draftFields.map((field) => {
      const candidate = candidateByKey.get(mappingCandidateKey(field)) || {};
      return {
        domain: String(field.domain || ""),
        sourceField: String(field.source_field || ""),
        recommendedRole: String(field.recommended_role || ""),
        fieldKind: String(field.field_kind || ""),
        confidence: field.confidence,
        uncertainty: String(field.uncertainty || ""),
        userAction: String(field.user_action || ""),
        attentionReason: String(field.attention_reason || ""),
        evidenceSummary: candidate.evidenceSummary || [],
      };
    }).filter((field) => (
      mappingState.focus === MAPPING_FOCUS_ALL || field.attentionReason
    ))
    : candidates;
  const quality = semanticQualityPresentation(mappingState.draft?.semantic_quality);
  const missingAdviceCount = mappingDraftMissingAdviceCount(mappingState.draft);
  const domains = [...new Set(rows.map((item) => item.domain))].sort();
  const needle = search.trim().toLocaleLowerCase("zh-CN");
  const displayedRows = rows.filter((item) => (
    (activeDomain === "all" || item.domain === activeDomain)
    && (
      !needle
      || item.domain.toLocaleLowerCase("zh-CN").includes(needle)
      || item.sourceField.toLocaleLowerCase("zh-CN").includes(needle)
      || item.userAction.toLocaleLowerCase("zh-CN").includes(needle)
      || item.uncertainty.toLocaleLowerCase("zh-CN").includes(needle)
    )
  ));
  const draftSummary = mappingState.draft
    ? `共 ${draftFields.length} 条字段对应建议 · 重点关注 ${rows.length} 条 · 当前显示 ${displayedRows.length} 条`
    : "";

  return (
    <div className="monitoring-admission-confirm monitoring-admission-mapping">
      <p className="monitoring-admission-pending-note">
        {draftSummary || mappingState.payload?.summaryText
          || "加载字段对应建议后，可按重点优先核对并整体确认。"}
      </p>
      <p className="monitoring-admission-minor">
        确认前不会生成可用于监查的数据；确认后也只保存字段对应关系。
      </p>
      <div className="monitoring-admission-mapping-filters" role="group" aria-label="建议筛选">
        <button
          type="button"
          className={mappingState.focus === MAPPING_FOCUS_CRITICAL ? "is-active" : ""}
          aria-pressed={mappingState.focus === MAPPING_FOCUS_CRITICAL}
          onClick={() => onFocusChange?.(MAPPING_FOCUS_CRITICAL)}
        >
          重点优先
        </button>
        <button
          type="button"
          className={mappingState.focus === MAPPING_FOCUS_ALL ? "is-active" : ""}
          aria-pressed={mappingState.focus === MAPPING_FOCUS_ALL}
          onClick={() => onFocusChange?.(MAPPING_FOCUS_ALL)}
        >
          全部建议
        </button>
        <select
          aria-label="按数据表筛选"
          value={activeDomain}
          onChange={(event) => setActiveDomain(event.target.value)}
        >
          <option value="all">全部数据表</option>
          {domains.map((domain) => <option key={domain} value={domain}>{domain}</option>)}
        </select>
        <input
          aria-label="搜索字段"
          value={search}
          placeholder="搜索原始字段或核对事项"
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>
      {mappingState.message ? (
        <p className="monitoring-admission-mapping-message" role="status">{mappingState.message}</p>
      ) : null}
      {mappingState.phase === "drafting" && quality.title ? (
        <div
          className={`monitoring-admission-quality is-${quality.level}`}
          role={quality.blocksConfirmation ? "alert" : "status"}
        >
          <strong>{quality.title}</strong>
          {quality.detail ? <span>{quality.detail}</span> : null}
        </div>
      ) : null}
      {mappingState.phase === "drafting" && missingAdviceCount ? (
        <div className="monitoring-admission-quality is-blocked" role="alert">
          <strong>还有 {missingAdviceCount} 条建议需要补充</strong>
          <span>请打开标记为“建议不完整”的字段，填写具体的中文核对事项后再整体确认。</span>
        </div>
      ) : null}
      {mappingState.phase === "drafting" ? (
        <label className="monitoring-admission-field monitoring-admission-confirmation-note">
          <span className="monitoring-admission-field-label">整体确认说明</span>
          <textarea
            value={mappingState.confirmationReason}
            placeholder="请简要说明已核对的重点内容（至少 10 个字）"
            onChange={(event) => onReasonChange?.(event.target.value)}
          />
        </label>
      ) : null}
      <div className={`monitoring-admission-mapping-workspace ${mappingState.fieldForm ? "has-editor" : ""}`}>
        <div className="monitoring-admission-mapping-list">
          <ul className="monitoring-admission-pending">
        {displayedRows.map((item) => {
          const key = mappingCandidateKey({
            domain: item.domain,
            source_field: item.sourceField,
          });
          return (
            <li key={key}>
              <button
                type="button"
                className={`monitoring-admission-mapping-row ${mappingState.selectedKey === key ? "is-selected" : ""}`}
                aria-pressed={mappingState.selectedKey === key}
                disabled={mappingState.phase !== "drafting"}
                onClick={() => onSelectField?.(item)}
              >
                <span className="monitoring-admission-mapping-source">
                  <small>原始字段</small>
                  <strong>{item.domain} · {item.sourceField}</strong>
                  {(item.evidenceSummary || []).slice(0, 1).map((evidence) => (
                    <span key={`${key}-evidence`}>
                      {evidence.non_empty_count}/{evidence.total_rows} 条非空
                      {` · ${mappingTypeText(evidence.inferred_type)}`}
                      {evidence.sample_count
                        ? ` · ${evidence.sample_count} 个样例默认隐藏`
                        : ""}
                    </span>
                  ))}
                </span>
                <span className="monitoring-admission-mapping-advice">
                  <small>建议核对</small>
                  <strong>{item.userAction || "尚未形成具体核对建议，请先补充。"}</strong>
                  {item.uncertainty ? <span>{item.uncertainty}</span> : null}
                  <span>
                    <b className="monitoring-admission-attention-chip">
                      {item.attentionReason || "常规核对"}
                    </b>
                    {` · 置信度 ${confidencePercent(item.confidence)}`}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
          </ul>
          {!displayedRows.length ? (
            <p className="monitoring-admission-pending-note">
              当前筛选下没有需要展示的字段对应建议。
            </p>
          ) : null}
        </div>
        {mappingState.fieldForm ? (
          <aside className="monitoring-admission-field-editor">
          <p className="monitoring-admission-field-label">
            修订 {mappingState.fieldForm.domain} · {mappingState.fieldForm.source_field}
          </p>
          <label>
            不确定说明
            <textarea
              value={mappingState.fieldForm.uncertainty || ""}
              onChange={(event) => onFieldFormChange?.({
                uncertainty: event.target.value,
              })}
            />
          </label>
          <label>
            建议操作
            <textarea
              value={mappingState.fieldForm.user_action || ""}
              onChange={(event) => onFieldFormChange?.({
                user_action: event.target.value,
              })}
            />
          </label>
          <details className="monitoring-admission-technical">
            <summary>字段对应技术值</summary>
            <label>
              字段对应值
              <input
                type="text"
                value={mappingState.fieldForm.recommended_role || ""}
                onChange={(event) => onFieldFormChange?.({
                  recommended_role: event.target.value,
                })}
              />
            </label>
          </details>
          <button type="button" className="monitoring-admission-secondary" onClick={onSaveField}>
            保存本字段修订
          </button>
          </aside>
        ) : null}
      </div>
    </div>
  );
}

export function MedicalMonitoringAdmissionWizardView({
  state,
  mappingState = null,
  onSourceDirChange,
  onSourceFilesChange,
  onPrimaryAction,
  onSecondaryAction,
  onMappingFocusChange,
  onSelectMappingField,
  onMappingFieldFormChange,
  onSaveMappingField,
  onMappingReasonChange,
}) {
  const phase = state?.phase || "input";
  const stepIndex = state?.stepIndex || 0;
  const profile = state?.profile || null;
  const resolvedMappingState = mappingState || createAdmissionMappingConfirmState();
  const error = state?.error || resolvedMappingState?.error || null;
  const steps = admissionStepView(state);
  const primary = (
    phase === "done" && mappingState?.phase === "confirmed"
      ? { key: "noop", label: "下一步：生成可用于监查的数据", disabled: true }
      : stepIndex === 2 && phase !== "done"
      ? admissionMappingPrimaryAction(resolvedMappingState)
      : admissionPrimaryAction(state)
  );
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
            <p className="monitoring-admission-done-title">
              {mappingState?.phase === "confirmed" ? "字段对应已确认" : "数据已完成接入"}
            </p>
            <p className="monitoring-admission-big">{profile?.summaryText || ""}</p>
            <p className="monitoring-admission-minor">
              {mappingState?.phase === "confirmed"
                ? "可用于监查的数据尚未生成，当前还不能开始监查。"
                : "如需替换本批数据，请重新发起导入；已接入的数据版本不会被覆盖。"}
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
          <MappingConfirmPanel
            mappingState={resolvedMappingState}
            onFocusChange={onMappingFocusChange}
            onSelectField={onSelectMappingField}
            onFieldFormChange={onMappingFieldFormChange}
            onSaveField={onSaveMappingField}
            onReasonChange={onMappingReasonChange}
          />
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
  const [mappingState, mappingDispatch] = useReducer(
    admissionMappingConfirmReducer,
    undefined,
    createAdmissionMappingConfirmState,
  );

  const submitImport = useCallback(async () => {
    dispatch({ type: "import-start" });
    if (!state.projectId.trim()) return;
    try {
      const payload = state.selectedFiles.length
        ? await api.createDataAdmissionUpload(state.projectId, state.selectedFiles)
        : await api.createDataAdmission(state.projectId, { source_dir: state.sourceDir });
      dispatch({ type: "import-created", payload });
      mappingDispatch({ type: "reset" });
    } catch (error) {
      dispatch({ type: "error", error });
    }
  }, [api, state.projectId, state.selectedFiles, state.sourceDir]);

  const loadMappingCandidates = useCallback(async (focus = mappingState.focus) => {
    if (!state.projectId || !state.attemptId) return;
    mappingDispatch({ type: "load-start" });
    try {
      const payload = await api.listDataAdmissionMappingCandidates(
        state.projectId,
        state.attemptId,
        { focus },
      );
      mappingDispatch({ type: "load-ready", payload });
    } catch (error) {
      mappingDispatch({
        type: "error",
        error: {
          serverText: error?.detail?.message || error?.message || "字段对应建议加载失败。",
          guidance: ["请稍后重试；若持续失败，请确认字段对应建议已生成完成。"],
        },
      });
    }
  }, [api, mappingState.focus, state.attemptId, state.projectId]);

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

  useEffect(() => {
    if (state.phase !== "ready" || state.stepIndex !== 2) return undefined;
    if (mappingState.phase !== "idle") return undefined;
    loadMappingCandidates(mappingState.focus);
    return undefined;
  }, [loadMappingCandidates, mappingState.focus, mappingState.phase, state.phase, state.stepIndex]);

  const onPrimaryAction = useCallback(async (key) => {
    if (key === "import") {
      submitImport();
      return;
    }
    if (key === "retry") {
      if ((state.retryTarget || "create") === "create") {
        submitImport();
      } else {
        dispatch({ type: "retry" });
      }
      return;
    }
    if (key === "reload") {
      await loadMappingCandidates(mappingState.focus);
      return;
    }
    if (key === "show-all") {
      mappingDispatch({ type: "focus-change", focus: MAPPING_FOCUS_ALL });
      await loadMappingCandidates(MAPPING_FOCUS_ALL);
      return;
    }
    if (key === "adopt") {
      mappingDispatch({ type: "adopt-start" });
      try {
        const candidatePayload = mappingState.focus === MAPPING_FOCUS_ALL
          ? mappingState.payload?.raw
          : await api.listDataAdmissionMappingCandidates(
            state.projectId,
            state.attemptId,
            { focus: MAPPING_FOCUS_ALL },
          );
        const draft = await api.adoptDataAdmissionMappingDraft(
          state.projectId,
          state.attemptId,
          { reason: "采用本次完整字段对应建议进入重点修订。" },
        );
        mappingDispatch({ type: "adopt-ready", payload: draft, candidatePayload });
      } catch (error) {
        mappingDispatch({
          type: "error",
          error: {
            serverText: error?.detail?.message || error?.message || "采用字段建议失败。",
            guidance: ["请确认全部建议已生成完成后再试。"],
          },
        });
      }
      return;
    }
    if (key === "confirm") {
      if (!mappingState.draft?.draft_id) return;
      mappingDispatch({ type: "confirm-start" });
      try {
        const revision = await api.confirmDataAdmissionMappingDraft(
          state.projectId,
          state.attemptId,
          {
            draft_id: mappingState.draft.draft_id,
            expected_version: mappingState.draft.version,
            confirmation_reason: mappingState.confirmationReason,
            idempotency_key: requestKey("admission-mapping-confirm"),
          },
        );
        mappingDispatch({ type: "confirm-ready", payload: revision });
        dispatch({ type: "finish" });
      } catch (error) {
        mappingDispatch({
          type: "draft-error",
          error: {
            serverText: error?.detail?.message || error?.message || "整体确认失败。",
            guidance: ["请刷新后重试；确认前不会生成可用于监查的数据。"],
          },
        });
      }
      return;
    }
    dispatch({ type: key });
  }, [
    api,
    loadMappingCandidates,
    mappingState.confirmationReason,
    mappingState.draft,
    mappingState.focus,
    state.attemptId,
    state.projectId,
    state.retryTarget,
    submitImport,
  ]);

  const onSecondaryAction = useCallback((key) => {
    dispatch({ type: key });
  }, []);

  const onSelectMappingField = useCallback((item) => {
    if (mappingState.phase !== "drafting") return;
    mappingDispatch({
      type: "select-field",
      key: mappingCandidateKey({
        domain: item.domain,
        source_field: item.sourceField,
      }),
      form: {
        domain: item.domain,
        source_field: item.sourceField,
        recommended_role: item.recommendedRole || "",
        uncertainty: item.uncertainty || "",
        user_action: item.userAction || "",
        field_kind: item.fieldKind || "source_collected",
      },
    });
  }, [mappingState.phase]);

  const onSaveMappingField = useCallback(async () => {
    if (!mappingState.draft || !mappingState.fieldForm) return;
    try {
      const draft = await api.editDataAdmissionMappingDraftField(
        state.projectId,
        state.attemptId,
        {
          draft_id: mappingState.draft.draft_id,
          domain: mappingState.fieldForm.domain,
          source_field: mappingState.fieldForm.source_field,
          patch: {
            recommended_role: String(mappingState.fieldForm.recommended_role || "").trim(),
            uncertainty: String(mappingState.fieldForm.uncertainty || "").trim(),
            user_action: String(mappingState.fieldForm.user_action || "").trim(),
            field_kind: mappingState.fieldForm.field_kind || "source_collected",
          },
          expected_version: mappingState.draft.version,
          idempotency_key: requestKey("admission-mapping-field"),
        },
      );
      mappingDispatch({ type: "save-field-ready", payload: draft });
    } catch (error) {
      mappingDispatch({
        type: "draft-error",
        error: {
          serverText: error?.detail?.message || error?.message || "字段修订保存失败。",
          guidance: ["请检查填写内容后重试。"],
        },
      });
    }
  }, [api, mappingState.draft, mappingState.fieldForm, state.attemptId, state.projectId]);

  return (
    <MedicalMonitoringAdmissionWizardView
      state={state}
      mappingState={mappingState}
      onSourceDirChange={(value) => dispatch({ type: "source-dir-change", value })}
      onSourceFilesChange={(files) => dispatch({ type: "source-files-change", files })}
      onPrimaryAction={onPrimaryAction}
      onSecondaryAction={onSecondaryAction}
      onMappingFocusChange={(focus) => {
        mappingDispatch({ type: "focus-change", focus });
        if (!mappingState.draft) loadMappingCandidates(focus);
      }}
      onSelectMappingField={onSelectMappingField}
      onMappingFieldFormChange={(patch) => mappingDispatch({ type: "field-form-change", patch })}
      onSaveMappingField={onSaveMappingField}
      onMappingReasonChange={(value) => mappingDispatch({ type: "reason-change", value })}
    />
  );
}

export default MedicalMonitoringAdmissionWizard;
