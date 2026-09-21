import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { createMedicalMonitoringProductApi } from "./medicalMonitoringProductApi.mjs";
import MedicalMonitoringQueueControl from "./MedicalMonitoringQueueControl.jsx";
import {
  ADMISSION_SUPPORTED_SUFFIX_TEXT,
  admissionPrimaryAction,
  admissionSecondaryActions,
  admissionStepView,
  admissionWizardReducer,
  createAdmissionWizardState,
  readAdmissionProfile,
  validateAdmissionSourceDir,
} from "./medicalMonitoringAdmissionWizardState.mjs";
import {
  MAPPING_FOCUS_ALL,
  admissionMappingConfirmReducer,
  admissionMappingPrimaryAction,
  createAdmissionMappingConfirmState,
  mappingCandidateKey,
  mappingConfirmationReason,
  mappingConfirmationFailureAction,
  mappingQuestionCards,
  mappingUnansweredCount,
} from "./medicalMonitoringAdmissionMappingConfirmState.mjs";
import { semanticQualityPresentation } from "./medicalMonitoringFieldMappingState.mjs";
import "./medicalMonitoringAdmissionWizard.css";

function requestKey(prefix) {
  const random = globalThis.crypto?.randomUUID?.()
    || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${random}`;
}

export async function loadOrStartAdmissionMapping(api, projectId, attemptId) {
  try {
    return await api.listDataAdmissionMappingCandidates(
      projectId,
      attemptId,
      { focus: MAPPING_FOCUS_ALL },
    );
  } catch (error) {
    if (error?.detail?.code !== "mapping_candidates_not_found") throw error;
    return api.startDataAdmissionMappingCandidates(projectId, attemptId);
  }
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

function DocumentReadinessPanel({ state, onFiles, onRetry, onAdjudicate }) {
  const [choices, setChoices] = useState({});
  if (!state || (state.phase === "loading" && !state.payload)) {
    return <p className="monitoring-admission-loading" role="status">正在核对研究文档…</p>;
  }
  const payload = state.payload || {};
  const processing = [
    "uploading", "analyzing", "reviewing", "adjudicating", "cross_checking",
  ]
    .includes(state.phase);
  const userChoices = Array.isArray(payload.user_choices) ? payload.user_choices : [];
  const allAnswered = userChoices.every(
    (choice) => typeof choices[choice.role] === "string",
  );
  return (
    <section className="monitoring-admission-documents" aria-label="研究文档准备情况">
      <header>
        <strong>{payload.headline || "正在核对研究文档"}</strong>
        <span>{payload.guidance || "系统会自动识别，无需填写技术信息。"}</span>
      </header>
      <ul>
        {(payload.roles || []).map((item) => (
          <li key={item.role}>
            <span><strong>{item.label}</strong><small>{item.status_text}</small></span>
          </li>
        ))}
      </ul>
      {userChoices.length ? (
        <fieldset className="monitoring-admission-user-choices">
          <legend>请确认每个文件角色对应的文件（医学判断以您为准）</legend>
          {userChoices.map((choice) => (
            <div key={choice.role} role="group" aria-label={`文件角色：${choice.role}`}>
              <strong>角色：{choice.role}</strong>
              {choice.options.map((option) => (
                <label key={option.candidate_id || "__missing__"} style={{ display: "block" }}>
                  <input
                    type="radio"
                    name={`doc-role-${choice.role}`}
                    checked={(choices[choice.role] || "") === option.candidate_id}
                    onChange={() => setChoices((current) => ({
                      ...current,
                      [choice.role]: option.candidate_id,
                    }))}
                  />
                  {" "}
                  {option.candidate_id
                    ? `这是${choice.role}文件：${option.filename}`
                    : `没有${choice.role}文件（该角色缺失）`}
                </label>
              ))}
            </div>
          ))}
          <button
            type="button"
            className="monitoring-admission-secondary"
            disabled={!allAnswered || processing}
            onClick={() => onAdjudicate?.(
              userChoices.map((choice) => ({
                role: choice.role,
                candidate_id: choices[choice.role] || "",
              })),
            )}
            title={allAnswered ? "提交裁决并继续核对" : "请先为每个角色作出选择"}
          >
            提交裁决并继续
          </button>
        </fieldset>
      ) : null}
      {payload.files?.length ? (
        <p className="monitoring-admission-warning">
          涉及文件：{payload.files.join("、")}
        </p>
      ) : null}
      {!payload.ready && !userChoices.length ? (
        <label className="monitoring-admission-document-picker">
          <input
            type="file"
            multiple
            accept=".docx,.pdf,.xlsx"
            disabled={processing}
            onChange={(event) => onFiles?.(event.target.files)}
          />
          {processing
            ? "系统正在识别并交叉核对…"
            : state.phase === "needs_user_input"
              ? "重新选择完整研究文件"
              : "一次选择研究文件"}
        </label>
      ) : null}
      {state.error ? <p className="monitoring-admission-warning" role="alert">{state.error}</p> : null}
      {state.phase === "failed" && !userChoices.length ? (
        <button type="button" className="monitoring-admission-secondary" onClick={onRetry}>
          重新核对研究文件
        </button>
      ) : null}
    </section>
  );
}

// Step three: a plain summary of what the system recognized plus one card per
// medically substantive ambiguity. The per-field engineering list stays
// collapsed; the user only meets the questions that change medical analysis.
export function MappingConfirmPanel({ mappingState, onAnswerCard }) {
  const [noteKey, setNoteKey] = useState("");
  const [noteText, setNoteText] = useState("");
  const candidates = mappingState.payload?.candidates || [];
  const questions = mappingQuestionCards(mappingState);
  const answeredKeys = mappingState.answeredKeys || {};
  const answeredCount = questions.length - mappingUnansweredCount(mappingState);
  const currentQuestion = questions.find((card) => !answeredKeys[card.key]);
  const drafting = mappingState.phase === "drafting";
  const quality = drafting ? semanticQualityPresentation(mappingState.draft?.semantic_quality) : null;
  const payload = mappingState.payload;
  const headline = mappingState.phase === "adjudicating"
    ? "系统正在进一步核对少量疑点"
    : payload?.headline || "正在读取系统识别结果…";
  const tables = payload?.tableSummaries || [];
  const questionTableCount = tables.filter((table) => table.questionCount > 0).length;

  return (
    <div className="monitoring-admission-confirm monitoring-admission-mapping">
      <p className="monitoring-admission-big monitoring-admission-summary">{headline}</p>
      {tables.length ? (
        <details className="monitoring-admission-table-details">
          <summary>
            已识别 {tables.length} 张数据表
            {questionTableCount ? `，其中 ${questionTableCount} 张有待确认信息` : ""}
            <span>查看各表概况</span>
          </summary>
          <ul className="monitoring-admission-table-summary" aria-label="数据表识别摘要">
            {tables.map((table) => (
              <li key={table.name}>
                <strong>{table.name}</strong>
                <span>
                  {table.fieldCount} 个字段
                  {table.questionCount ? ` · ${table.questionCount} 个待确认` : ""}
                </span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      <p className="monitoring-admission-minor">
        确认前不会生成可用于监查的数据；确认后也只保存字段对应关系。
      </p>
      {mappingState.message ? (
        <p className="monitoring-admission-mapping-message" role="status">{mappingState.message}</p>
      ) : null}
      {drafting && quality?.title ? (
        <div
          className={`monitoring-admission-quality is-${quality.level}`}
          role={quality.blocksConfirmation ? "alert" : "status"}
        >
          <strong>{quality.title}</strong>
          {quality.detail ? <span>{quality.detail}</span> : null}
        </div>
      ) : null}
      {drafting && questions.length ? (
        <div className="monitoring-admission-questions">
          <p className="monitoring-admission-questions-head">
            只需确认会改变医学分析的疑点（已完成 {answeredCount}/{questions.length}）
          </p>
          <ul className="monitoring-admission-question-list">
            {(currentQuestion ? [currentQuestion] : []).map((card) => (
              <li
                key={card.key}
                className={`monitoring-admission-question${answeredKeys[card.key] ? " is-answered" : ""}`}
              >
                <div className="monitoring-admission-question-head">
                  <strong>请做一个医学选择</strong>
                </div>
                <p className="monitoring-admission-question-text">{card.question}</p>
                {card.priorUserAction ? (
                  <details className="monitoring-admission-question-evidence">
                    <summary>查看上次确认</summary>
                    <p>资料已更新，这是您此前的回答：</p>
                    <p>{card.priorUserAction.replace(/^用户已(?:确认|核对)：/, "")}</p>
                  </details>
                ) : null}
                {card.evidenceText ? (
                  <details className="monitoring-admission-question-evidence">
                    <summary>查看系统判断依据</summary>
                    <p>{card.evidenceText}</p>
                  </details>
                ) : null}
                {answeredKeys[card.key] ? (
                  <p className="monitoring-admission-question-done" role="status">已完成确认</p>
                ) : drafting ? (
                  <div className="monitoring-admission-question-actions">
                    {card.suggestedAnswer || card.reusablePriorAnswer ? <button
                      type="button"
                      className="monitoring-admission-secondary"
                      onClick={() => onAnswerCard?.(card, card.suggestedAnswer ? null : card.reusablePriorAnswer)}
                    >
                      {card.suggestedAnswer ? `确认：${card.suggestedAnswer}` : `仍是：${card.reusablePriorAnswer}`}
                    </button> : <button
                      type="button"
                      className="monitoring-admission-secondary"
                      onClick={() => onAnswerCard?.(card, null)}
                    >
                      系统判断正确
                    </button>}
                    {noteKey === card.key ? (
                      <span className="monitoring-admission-question-note">
                        <textarea
                          aria-label="补充实际医学含义"
                          value={noteText}
                          placeholder="请用一句话说明实际情况"
                          onChange={(event) => setNoteText(event.target.value)}
                        />
                        <button
                          type="button"
                          className="monitoring-admission-secondary"
                          disabled={noteText.trim().length < 2}
                          onClick={() => onAnswerCard?.(card, noteText.trim())}
                        >
                          保存说明
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="monitoring-admission-secondary"
                        onClick={() => {
                          setNoteKey(card.key);
                          setNoteText("");
                        }}
                      >
                        {card.suggestedAnswer || card.reusablePriorAnswer ? "不是，说明实际含义" : "说明实际含义"}
                      </button>
                    )}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {drafting && !questions.length ? (
        <p className="monitoring-admission-pending-note" role="status">
          系统已完成判断，正在自动保存字段对应关系，无需您逐项核对。
        </p>
      ) : null}
      <details className="monitoring-admission-technical">
        <summary>查看全部字段的识别结果</summary>
        <ul className="monitoring-admission-field-digest">
          {candidates.map((item) => {
            const evidence = (item.evidenceSummary || [])[0];
            return (
              <li
                key={mappingCandidateKey({ domain: item.domain, source_field: item.sourceField })}
              >
                <span className="monitoring-admission-column-name">
                  {item.domain} · {item.sourceField}
                </span>
                <span className="monitoring-admission-column-meta">
                  {evidence ? mappingTypeText(evidence.inferred_type) : "系统已识别"}
                </span>
              </li>
            );
          })}
        </ul>
      </details>
    </div>
  );
}

export function MedicalMonitoringAdmissionWizardView({
  state,
  documentState = { phase: "ready", payload: { ready: true, roles: [] }, error: null },
  mappingState = null,
  factState = null,
  onSourceDirChange,
  onSourceFilesChange,
  onPrimaryAction,
  onSecondaryAction,
  onAnswerCard,
  onDocumentFiles,
  onDocumentRetry,
  onDocumentAdjudicate,
}) {
  const phase = state?.phase || "input";
  const stepIndex = state?.stepIndex || 0;
  const profile = state?.profile || null;
  const resolvedMappingState = mappingState || createAdmissionMappingConfirmState();
  const resolvedFactState = factState || { phase: "idle", error: null };
  const error = state?.error || resolvedMappingState?.error || resolvedFactState.error || null;
  const steps = admissionStepView(state);
  const primary = (
    phase === "done" && mappingState?.phase === "confirmed"
      ? resolvedFactState.phase === "ready"
        ? { key: "facts-ready", label: "进入医学监查", disabled: false }
        : resolvedFactState.phase === "failed"
          ? { key: "generate-facts", label: "重试生成监查数据", disabled: false }
          : { key: "generating-facts", label: "正在生成监查数据…", disabled: true }
      : stepIndex === 2 && phase !== "done" && documentState?.payload?.ready !== true
      ? { key: "documents-required", label: "请先添加所需文件", disabled: true }
      : stepIndex === 2 && phase !== "done"
      ? admissionMappingPrimaryAction(resolvedMappingState)
      : admissionPrimaryAction(state)
  );
  const secondary = admissionSecondaryActions(state);
  const validation = validateAdmissionSourceDir(state?.sourceDir);

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
              {resolvedFactState.phase === "ready"
                ? "监查数据已准备完成"
                : mappingState?.phase === "confirmed" ? "系统已完成字段识别" : "数据已完成接入"}
            </p>
            <p className="monitoring-admission-big">{profile?.summaryText || ""}</p>
            {resolvedFactState.phase === "ready" && resolvedFactState.payload?.summary ? (
              <p className="monitoring-admission-fact-summary">
                已整理 {resolvedFactState.payload.summary.tables || 0} 张数据表、
                {resolvedFactState.payload.summary.rows || 0} 条记录、
                {resolvedFactState.payload.summary.values || 0} 个数据项；
                {Number.isInteger(resolvedFactState.payload.summary.source_values_verified)
                  && resolvedFactState.payload.summary.source_values_verified >= 0
                  ? `已核对 ${resolvedFactState.payload.summary.source_values_verified} 个原始数据位置`
                  : "原始数据位置的核对数量尚未记录"}
              </p>
            ) : null}
            <p className="monitoring-admission-minor">
              {mappingState?.phase === "confirmed"
                ? resolvedFactState.phase === "ready"
                  ? "无需逐项检查，可以直接开始医学监查。"
                  : resolvedFactState.phase === "failed"
                    ? "本次未生成监查数据，原始文件未受影响。"
                    : "正在自动生成可用于监查的数据，无需逐项确认。"
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
          </div>
        ) : profile && stepIndex === 2 ? (
          <>
            <DocumentReadinessPanel
              state={documentState}
              onFiles={onDocumentFiles}
              onRetry={onDocumentRetry}
              onAdjudicate={onDocumentAdjudicate}
            />
            {documentState?.payload?.ready ? (
              <MappingConfirmPanel
                mappingState={resolvedMappingState}
                onAnswerCard={onAnswerCard}
              />
            ) : null}
          </>
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
  const [documentState, setDocumentState] = useState({
    phase: "idle",
    payload: null,
    error: null,
  });
  const adoptInFlight = useRef(false);
  const adjudicationInFlight = useRef(false);
  const confirmInFlight = useRef(false);
  const documentUploadInFlight = useRef(false);
  const documentRequestGeneration = useRef(0);
  const factsInFlight = useRef(false);
  const [factState, setFactState] = useState({ phase: "idle", payload: null, error: null });

  useEffect(() => {
    if (!state.projectId || state.attemptId || state.phase !== "input") return undefined;
    const controller = new AbortController();
    let cancelled = false;
    api.getLatestDataAdmission(state.projectId, { signal: controller.signal })
      .then((payload) => {
        if (!cancelled) dispatch({ type: "resume-created", payload });
      })
      .catch((error) => {
        const code = error?.detail?.code || error?.code || "";
        if (!cancelled && code !== "admission_attempt_not_found" && error?.name !== "AbortError") {
          dispatch({ type: "error", error });
        }
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [api, state.attemptId, state.phase, state.projectId]);

  const submitImport = useCallback(async () => {
    dispatch({ type: "import-start" });
    if (!state.projectId.trim()) return;
    try {
      const payload = state.selectedFiles.length
        ? await api.createDataAdmissionUpload(state.projectId, state.selectedFiles)
        : await api.createDataAdmission(state.projectId, { source_dir: state.sourceDir });
      dispatch({ type: "import-created", payload });
      mappingDispatch({ type: "reset" });
      setDocumentState({ phase: "idle", payload: null, error: null });
      adoptInFlight.current = false;
      adjudicationInFlight.current = false;
    } catch (error) {
      dispatch({ type: "error", error });
    }
  }, [api, state.projectId, state.selectedFiles, state.sourceDir]);

  const loadMappingCandidates = useCallback(async () => {
    if (!state.projectId || !state.attemptId) return;
    mappingDispatch({ type: "load-start" });
    try {
      const payload = await loadOrStartAdmissionMapping(
        api,
        state.projectId,
        state.attemptId,
      );
      mappingDispatch({ type: "load-ready", payload });
      if (
        payload?.confirmation_status === "confirmed"
        || payload?.draft?.status === "confirmed"
      ) {
        dispatch({ type: "finish" });
      }
    } catch (error) {
      mappingDispatch({
        type: "error",
        error: {
          serverText: error?.detail?.message || error?.message || "系统识别结果加载失败。",
          guidance: ["请稍后重试；若持续失败，请确认字段识别已生成完成。"],
        },
      });
    }
  }, [api, state.attemptId, state.projectId]);

  const loadDocumentReadiness = useCallback(async () => {
    if (!state.projectId || !state.attemptId) return;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    setDocumentState((current) => ({ ...current, phase: "loading", error: null }));
    try {
      const payload = await api.getDataAdmissionDocumentReadiness(
        state.projectId,
        state.attemptId,
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({ phase: "ready", payload, error: null });
      }
    } catch (error) {
      if (documentRequestGeneration.current === generation) {
        setDocumentState((current) => ({
          ...current,
          phase: "failed",
          error: error?.detail?.message || error?.message || "研究文档核对失败。",
        }));
      }
    }
  }, [api, state.attemptId, state.projectId]);

  const submitDocumentAdjudication = useCallback(async (selections) => {
    if (!state.projectId || !state.attemptId) return;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    setDocumentState((current) => ({ ...current, phase: "cross_checking", error: null }));
    try {
      const payload = await api.resolveStudyDocuments(
        state.projectId,
        state.attemptId,
        documentState.payload?.analysis_token,
        { userRoleSelections: selections },
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({
          phase: payload.ready ? "ready" : (payload.state || "analyzing"),
          payload,
          error: null,
        });
      }
    } catch (error) {
      if (documentRequestGeneration.current === generation) {
        setDocumentState((current) => ({
          ...current,
          phase: "failed",
          error: error?.detail?.message || error?.message || "裁决提交失败，请重试。",
        }));
      }
    }
  }, [api, documentState.payload?.analysis_token, state.attemptId, state.projectId]);

  const analyzeDocuments = useCallback(async (files) => {
    if (
      !files?.length || !state.projectId || !state.attemptId
      || documentUploadInFlight.current
    ) return;
    documentUploadInFlight.current = true;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    setDocumentState((current) => ({ ...current, phase: "uploading", error: null }));
    try {
      const payload = await api.analyzeStudyDocuments(
        state.projectId,
        state.attemptId,
        files,
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({ phase: payload.state || "analyzing", payload, error: null });
      }
    } catch (error) {
      if (documentRequestGeneration.current === generation) {
        setDocumentState((current) => ({
          ...current,
          phase: "failed",
          error: error?.detail?.message || error?.message || "文件识别失败。",
        }));
      }
    } finally {
      documentUploadInFlight.current = false;
    }
  }, [api, state.attemptId, state.projectId]);

  useEffect(() => {
    if (
      !["analyzing", "reviewing", "adjudicating", "cross_checking"]
        .includes(documentState.phase)
      || !documentState.payload?.analysis_token
    ) return undefined;
    const timer = setTimeout(async () => {
      try {
        const payload = await api.resolveStudyDocuments(
          state.projectId,
          state.attemptId,
          documentState.payload.analysis_token,
        );
        setDocumentState({
          phase: payload.ready ? "ready" : (payload.state || "analyzing"),
          payload,
          error: null,
        });
      } catch (error) {
        setDocumentState({
          phase: "failed",
          payload: null,
          error: error?.detail?.message || error?.message || "研究文件核对失败。",
        });
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [api, documentState, state.attemptId, state.projectId]);

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
      // Structural preview belongs to this wizard. Notify the parent only
      // after facts are ready; its reload otherwise unmounts this preview.
    });
    return () => {
      cancelled = true;
    };
  }, [api, state.phase, state.attemptId, state.projectId]);

  useEffect(() => {
    if (state.phase !== "ready" || state.stepIndex !== 2) return undefined;
    if (documentState.phase === "idle") loadDocumentReadiness();
    if (documentState.payload?.ready && mappingState.phase === "idle") loadMappingCandidates();
    return undefined;
  }, [
    documentState.payload,
    documentState.phase,
    loadDocumentReadiness,
    loadMappingCandidates,
    mappingState.phase,
    state.phase,
    state.stepIndex,
  ]);

  useEffect(() => {
    if (
      mappingState.phase !== "ready"
      || mappingState.payload?.state !== "generating"
    ) return undefined;
    const timer = setTimeout(loadMappingCandidates, 2500);
    return () => clearTimeout(timer);
  }, [loadMappingCandidates, mappingState.payload?.state, mappingState.phase]);

  const advanceAdjudication = useCallback(async (draft) => {
    if (!draft?.draft_id || adjudicationInFlight.current) return;
    adjudicationInFlight.current = true;
    try {
      const payload = await api.adjudicateDataAdmissionMappingDraft(
        state.projectId,
        state.attemptId,
        { draft_id: draft.draft_id },
      );
      const adjudicationState = payload?.adjudication?.state;
      mappingDispatch({
        type: adjudicationState === "running"
          ? "adjudication-running"
          : adjudicationState === "blocked"
            ? "adjudication-blocked"
            : "adjudication-ready",
        payload,
      });
    } catch (error) {
      mappingDispatch({
        type: "adjudication-blocked",
        payload: draft,
        error: {
          serverText: error?.detail?.message || error?.message || "系统复核暂未完成。",
        },
      });
    } finally {
      adjudicationInFlight.current = false;
    }
  }, [api, state.attemptId, state.projectId]);

  // The system adopts the basically-correct recognition draft and performs
  // one focused independent pass before showing any residual questions.
  const adoptDraft = useCallback(async () => {
    if (adoptInFlight.current) return;
    adoptInFlight.current = true;
    mappingDispatch({ type: "adopt-start" });
    try {
      const draft = await api.adoptDataAdmissionMappingDraft(
        state.projectId,
        state.attemptId,
        { reason: "采用系统字段识别结果，进入医学确认。" },
      );
      mappingDispatch({ type: "adjudication-start", payload: draft });
      await advanceAdjudication(draft);
    } catch (error) {
      adoptInFlight.current = false;
      mappingDispatch({
        type: "error",
        error: {
          serverText: error?.detail?.message || error?.message || "采用系统识别结果失败。",
          guidance: ["请稍后重试；若持续失败，请确认字段识别已生成完成。"],
        },
      });
    }
  }, [advanceAdjudication, api, state.attemptId, state.projectId]);

  useEffect(() => {
    if (mappingState.phase !== "adjudicating" || !mappingState.draft) {
      return undefined;
    }
    const timer = setTimeout(
      () => advanceAdjudication(mappingState.draft),
      1500,
    );
    return () => clearTimeout(timer);
  }, [advanceAdjudication, mappingState.draft, mappingState.phase]);

  useEffect(() => {
    if (mappingState.phase !== "ready") return undefined;
    if (mappingState.payload?.state !== "candidates_ready" || !mappingState.payload.fieldCount) {
      return undefined;
    }
    adoptDraft();
    return undefined;
  }, [adoptDraft, mappingState.phase, mappingState.payload]);

  const confirmDraft = useCallback(async () => {
    if (!mappingState.draft?.draft_id || confirmInFlight.current) return;
    confirmInFlight.current = true;
    mappingDispatch({ type: "confirm-start" });
    try {
      const questionCount = mappingState.payload?.questionCount || 0;
      const revision = await api.confirmDataAdmissionMappingDraft(
        state.projectId,
        state.attemptId,
        {
          draft_id: mappingState.draft.draft_id,
          expected_version: mappingState.draft.version,
          confirmation_reason: mappingConfirmationReason(mappingState),
          idempotency_key: requestKey("admission-mapping-confirm"),
          automatic: questionCount === 0,
        },
      );
      mappingDispatch({ type: "confirm-ready", payload: revision });
      dispatch({ type: "finish" });
    } catch (error) {
      confirmInFlight.current = false;
      mappingDispatch(mappingConfirmationFailureAction(error, mappingState.draft));
    }
  }, [api, mappingState, state.attemptId, state.projectId]);

  const generateFacts = useCallback(async () => {
    if (!state.projectId || !state.attemptId || factsInFlight.current) return;
    factsInFlight.current = true;
    setFactState({ phase: "generating", payload: null, error: null });
    try {
      const payload = await api.generateDataAdmissionFacts(
        state.projectId,
        state.attemptId,
      );
      setFactState({ phase: "ready", payload, error: null });
    } catch (error) {
      factsInFlight.current = false;
      setFactState({
        phase: "failed",
        payload: null,
        error: {
          serverText: error?.detail?.message || error?.message || "监查数据生成失败。",
          guidance: ["请点击重试；原始文件不会被修改。"],
        },
      });
    }
  }, [api, state.attemptId, state.projectId]);

  useEffect(() => {
    if (
      state.phase === "done"
      && mappingState.phase === "confirmed"
      && factState.phase === "idle"
    ) {
      generateFacts();
    }
  }, [factState.phase, generateFacts, mappingState.phase, state.phase]);

  useEffect(() => {
    if (mappingState.phase !== "drafting" || mappingState.error) return undefined;
    const quality = semanticQualityPresentation(mappingState.draft?.semantic_quality);
    if (!mappingState.draft || quality.blocksConfirmation || mappingUnansweredCount(mappingState)) {
      return undefined;
    }
    confirmDraft();
    return undefined;
  }, [confirmDraft, mappingState]);

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
      await loadMappingCandidates();
      return;
    }
    if (key === "adopt") {
      await adoptDraft();
      return;
    }
    if (key === "confirm") {
      await confirmDraft();
      return;
    }
    if (key === "generate-facts") {
      await generateFacts();
      return;
    }
    if (key === "facts-ready") {
      onAdmitted?.(factState.payload);
      return;
    }
    dispatch({ type: key });
  }, [
    adoptDraft,
    api,
    confirmDraft,
    generateFacts,
    loadMappingCandidates,
    mappingState,
    onAdmitted,
    factState.payload,
    state.attemptId,
    state.projectId,
    state.retryTarget,
    submitImport,
  ]);

  const onSecondaryAction = useCallback((key) => {
    dispatch({ type: key });
  }, []);

  const onAnswerCard = useCallback(async (card, note) => {
    if (!mappingState.draft || mappingState.phase !== "drafting") return;
    try {
      const draft = await api.editDataAdmissionMappingDraftField(
        state.projectId,
        state.attemptId,
        {
          draft_id: mappingState.draft.draft_id,
          domain: card.domain,
          source_field: card.sourceField,
          patch: {
            // The server atomically binds this answer to the question's
            // evidence generation using the draft version below.
            user_action: note === null
              ? "用户已确认：采用系统判断，无需修改。"
              : `用户已核对：${note}`,
          },
          expected_version: mappingState.draft.version,
          idempotency_key: requestKey("admission-mapping-answer"),
        },
      );
      mappingDispatch({ type: "answer-ready", key: card.key, payload: draft });
    } catch (error) {
      mappingDispatch({
        type: "draft-error",
        error: {
          serverText: error?.detail?.message || error?.message || "确认结果保存失败。",
          guidance: ["请稍后重试；确认前不会生成可用于监查的数据。"],
        },
      });
    }
  }, [api, mappingState.draft, mappingState.phase, state.attemptId, state.projectId]);

  return (
    <>
    {state.projectId && typeof api.getQueueState === "function" ? (
      <MedicalMonitoringQueueControl key={state.projectId} api={api} projectId={state.projectId} />
    ) : null}
    <MedicalMonitoringAdmissionWizardView
      state={state}
      documentState={documentState}
      mappingState={mappingState}
      factState={factState}
      onSourceDirChange={(value) => dispatch({ type: "source-dir-change", value })}
      onSourceFilesChange={(files) => dispatch({ type: "source-files-change", files })}
      onPrimaryAction={onPrimaryAction}
      onSecondaryAction={onSecondaryAction}
      onAnswerCard={onAnswerCard}
      onDocumentFiles={analyzeDocuments}
      onDocumentRetry={loadDocumentReadiness}
      onDocumentAdjudicate={submitDocumentAdjudication}
    />
    </>
  );
}

export default MedicalMonitoringAdmissionWizard;
