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

// R6-01：resolve既可能返回核对流程载荷（含state/analysis_token），
// 也可能返回readiness快照（只有ready/roles）。旧写法把快照当
// "analyzing"遗留——轮询useEffect因无analysis_token停振，按钮永久
// 挂起「正在核对研究文件…」只能F5。快照态无流程在跑，落ready_snapshot。
function documentPhaseFromPayload(payload) {
  if (!payload || typeof payload !== "object") return "failed";
  if (payload.ready) return "ready";
  const flowState = String(payload.state || "");
  if (flowState) return flowState;
  return payload.analysis_token ? "analyzing" : "ready_snapshot";
}

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

const DOCUMENT_ROLE_LABELS = Object.freeze({
  protocol: "研究方案",
  investigator_brochure: "研究者手册",
  ecrf: "电子病例报告表",
  sap: "统计分析计划",
});

function documentRoleLabel(role) {
  return DOCUMENT_ROLE_LABELS[role] || "研究文件";
}

function DocumentReadinessPanel({ state, onFiles, onRetry, onAdjudicate, onContentConfirm, onIdentityConfirm }) {
  const [choices, setChoices] = useState({});
  const [identityNote, setIdentityNote] = useState("");
  const [identityBusy, setIdentityBusy] = useState(false);
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
  // 身份门人工裁决（R1循环）：双盲核对无法自动建立文件与项目的对应
  // 关系（如项目代号≠方案研究编号、药物命名不一致）时，给出人工确认
  // 入口；确认后系统记录裁决并继续角色核对。未确认前仍不采用该批文件。
  const identityBlocked = ["project_mismatch", "project_identity_incomplete"].includes(state.phase)
    || ["project_mismatch", "project_identity_incomplete"].includes(payload.state);
  const submitIdentityConfirmation = async () => {
    if (identityBusy) return;
    setIdentityBusy(true);
    try {
      await onIdentityConfirm?.({
        confirmed: true,
        reason: identityNote.trim()
          || `人工确认${(payload.files || []).join("、") || "本批研究文件"}属于当前项目并继续核对。`,
      });
    } finally {
      setIdentityBusy(false);
    }
  };
  return (
    <section className="monitoring-admission-documents" aria-label="研究文档准备情况">
      <header>
        <strong>{payload.headline || "正在核对研究文档"}</strong>
        <span>{payload.guidance || "系统会自动识别，无需填写技术信息。"}</span>
      </header>
      {payload.previously_analyzed ? (
        <p className="monitoring-admission-warning" role="status">
          这组文件与此前上传的内容完全一致，系统直接复用已有核对结论；
          如需重新核对，请更换文件版本后上传。
        </p>
      ) : null}
      <ul>
        {(payload.roles || []).map((item) => (
          <li key={item.role}>
            <span><strong>{item.label}</strong><small>{item.status_text}</small></span>
          </li>
        ))}
      </ul>
      {payload.last_check_note && !payload.ready ? (
        <p className="monitoring-admission-warning" role="status">
          {payload.last_check_note}
        </p>
      ) : null}
      {(payload.content_confirmations || []).length ? (
        <fieldset className="monitoring-admission-user-choices">
          <legend>系统发现以下内容差异</legend>
          {(payload.content_confirmations || []).map((entry) => (
            <div key={entry.source_entry_id} role="group" aria-label={`内容核对：${entry.filename}`}>
              <strong>{documentRoleLabel(entry.role)}：{entry.filename}</strong>
              <small>{entry.summary || "文件内容与当前研究信息存在差异。"}</small>
              <ul className="monitoring-admission-content-differences">
                {(entry.checks || []).map((check, index) => (
                  <li key={`${entry.source_entry_id}-${index}`}>
                    <strong>{check.label}</strong>
                    <span>当前项目：{check.expected_value || "未提供"}</span>
                    <span>文件内容：{check.observed_value || "未识别"}</span>
                    {check.evidence_locators?.length ? (
                      <small>依据位置：{check.evidence_locators.join("；")}</small>
                    ) : null}
                  </li>
                ))}
              </ul>
              {entry.can_confirm ? (
                <button
                  type="button"
                  className="monitoring-admission-secondary"
                  disabled={processing}
                  onClick={() => onContentConfirm?.(entry)}
                  title="确认差异不影响本次医学监查，继续使用该文件"
                >
                  差异不影响本次监查，继续使用
                </button>
              ) : (
                <p className="monitoring-admission-warning">
                  该差异不能直接忽略，请更换正确文件后重新上传。
                </p>
              )}
            </div>
          ))}
        </fieldset>
      ) : null}
      {userChoices.length ? (
        <fieldset className="monitoring-admission-user-choices">
          <legend>系统只剩以下文件关系无法确定</legend>
          {userChoices.map((choice) => (
            <div key={choice.role} role="group" aria-label={`文件类型：${documentRoleLabel(choice.role)}`}>
              <strong>哪份是{documentRoleLabel(choice.role)}？</strong>
              {/* R5冲刺（R4-05）：裁决前说明该选择的解析口径与下游影响，
                  以及事后更换路径，避免信息不足时作出不可逆决定。 */}
              <small style={{ display: "block", margin: "2px 0 6px", color: "var(--monitoring-muted, #6b7785)" }}>
                选择后系统将按{documentRoleLabel(choice.role)}的口径解析该文件的全部内容，
                用于后续字段映射与核对；标记缺失表示本研究无此类文件。
                如需更换，可在保存后重新上传文件并重新核对。
              </small>
              {choice.options.map((option) => {
                // R5冲刺（R3-07）：「该角色缺失」选项candidate_id为空串，
                // 原checked表达式未选择时也判true（假选中），而保存按钮
                // 仍禁用——须先切其它项再切回。改为显式键存在性判定。
                // R6-02：不可解析/不可选候选以禁用态可见（附原因），
                // 与「涉及文件」清单一致，不凭空消失。
                const hasChoice = Object.prototype.hasOwnProperty.call(choices, choice.role);
                const optionChecked = hasChoice
                  && (choices[choice.role] || "") === option.candidate_id;
                const optionDisabled = option.selectable === false;
                return (
                  <label
                    key={option.candidate_id || "__missing__"}
                    style={{
                      display: "block",
                      opacity: optionDisabled ? 0.55 : 1,
                    }}
                    title={optionDisabled ? option.unselectable_reason || "该文件不可作为此角色的权威文件" : undefined}
                  >
                    <input
                      type="radio"
                      name={`doc-role-${choice.role}`}
                      checked={optionChecked}
                      disabled={optionDisabled}
                      onChange={() => setChoices((current) => ({
                        ...current,
                        [choice.role]: option.candidate_id,
                      }))}
                    />
                    {" "}
                    {option.candidate_id
                      ? option.filename
                      : `本次未提供${documentRoleLabel(choice.role)}`}
                    {optionDisabled ? (
                      <small style={{ display: "block", marginLeft: 22 }}>
                        {option.unselectable_reason || "不可作为权威文件"}
                      </small>
                    ) : null}
                  </label>
                );
              })}
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
            title={allAnswered ? "保存选择并继续" : "请先完成上方选择"}
          >
            保存选择并继续
          </button>
        </fieldset>
      ) : null}
      {identityBlocked && !processing ? (
        <fieldset className="monitoring-admission-user-choices">
          <legend>资料归属需要人工确认</legend>
          <small style={{ display: "block", marginBottom: "6px" }}>
            系统未能在文件与当前项目信息之间自动建立对应关系。请核对上方文件确属本研究后确认；
            确认将写入项目工作区的裁决档案（identity_overrides，含操作者、时间、理由与系统原判定），
            可由管理员检索复核。若文件不属于本研究，请更换文件后重新上传。
          </small>
          <label style={{ display: "block", marginBottom: "6px" }}>
            <textarea
              aria-label="归属确认说明（可选）"
              value={identityNote}
              placeholder="可补充说明确认依据（如：本项目即RUX-03-002研究，项目代号为管理编号）"
              onChange={(event) => setIdentityNote(event.target.value)}
              disabled={identityBusy}
            />
          </label>
          <button
            type="button"
            className="monitoring-admission-secondary"
            disabled={identityBusy}
            onClick={submitIdentityConfirmation}
            title="确认这组研究文件属于当前项目，继续文件角色核对"
          >
            {identityBusy ? "正在提交确认…" : "确认属于当前项目并继续"}
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
            : state.phase === "failed"
              ? "重新上传研究文件并再次核对"
              : state.phase === "needs_user_input"
                ? "如仍有文件遗漏，可继续补充上传"
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
  // R5冲刺（R2-12）：全字段列表曾一次性渲染上千条DOM（两次CDP截图均
  // 超时）；改为展开才渲染+分批加载。
  // R4-03口径澄清（20260929，数据级核实后修正）：本页「已识别 N 张表」
  // 是已完成识别作业的去重表数，识别未收敛时小于导入概况的全部工作表数
  // ——系统没有任何「代码对照表/名册页」排除规则，勿再按排除口径表述。
  const [fieldsOpen, setFieldsOpen] = useState(false);
  const [fieldBatch, setFieldBatch] = useState(100);
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
  const visibleCandidates = candidates.slice(0, fieldBatch);

  return (
    <div className="monitoring-admission-confirm monitoring-admission-mapping">
      <p className="monitoring-admission-big monitoring-admission-summary">{headline}</p>
      {/* R4-03口径澄清：表数=已产出识别结果的表数（进行中口径），
          与导入概况「全部工作表」口径不同，见上注释。 */}
      <p className="monitoring-admission-minor" style={{ margin: "2px 0 8px" }}>
        口径：下方表数只统计已产出识别结果的数据表，
        {payload?.state === "generating"
          ? "识别仍在生成中，"
          : payload?.state === "needs_attention"
            ? "部分识别任务尚未完成，"
            : ""}
        识别完成前可能小于导入概况的表数；系统不会把代码对照表、名册页等
        辅助表静默排除在识别之外。
      </p>
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
      <details
        className="monitoring-admission-technical"
        open={fieldsOpen}
        onToggle={(event) => setFieldsOpen(event.currentTarget.open)}
      >
        <summary>查看全部字段的识别结果（{candidates.length} 项，按数据域归并列出）</summary>
        <p className="monitoring-admission-minor" style={{ margin: "4px 0 8px" }}>
          注：此处仅列出已产出识别结果的数据表，尚未识别完成的表暂不在列。
          导入概况统计的是文件内全部工作表（含代码对照表、名册页等辅助表），
          识别完成前两处数字可能不同；除有明确忽略原因的工作表外，
          系统不静默排除任何表。
        </p>
        {fieldsOpen ? (
          <>
            <ul className="monitoring-admission-field-digest">
              {visibleCandidates.map((item) => {
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
            {candidates.length > visibleCandidates.length ? (
              <button
                type="button"
                className="monitoring-admission-secondary"
                onClick={() => setFieldBatch((current) => current + 200)}
              >
                继续展示后续 {Math.min(200, candidates.length - visibleCandidates.length)} 项（剩余 {candidates.length - visibleCandidates.length}）
              </button>
            ) : null}
          </>
        ) : null}
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
  onDocumentContentConfirm,
  onDocumentIdentityConfirm,
}) {
  const phase = state?.phase || "input";
  const stepIndex = state?.stepIndex || 0;
  const profile = state?.profile || null;
  const resolvedMappingState = mappingState || createAdmissionMappingConfirmState();
  const resolvedFactState = factState || { phase: "idle", error: null };
  const error = state?.error || resolvedMappingState?.error || resolvedFactState.error || null;
  // R4循环：目录型input收到文件级注入时files.length为0且此前零反馈。
  const [filePickNotice, setFilePickNotice] = useState("");
  const steps = admissionStepView(state);
  const primary = (
    phase === "done" && mappingState?.phase === "confirmed"
      ? resolvedFactState.phase === "ready"
        ? { key: "facts-ready", label: "进入医学监查", disabled: false }
        : resolvedFactState.phase === "failed"
          ? { key: "generate-facts", label: "重试生成监查数据", disabled: false }
          : { key: "generating-facts", label: "正在生成监查数据…", disabled: true }
      : stepIndex === 2 && phase !== "done" && documentState?.payload?.ready !== true
      ? (() => {
        // R1循环：研究文件未就绪时主按钮保持禁用，但文案必须如实
        // 反映当前所处环节（核对中/待人工确认/待补充文件），不再
        // 一律显示「请先添加所需文件」。
        const documentPhase = documentState?.phase || "";
        const processingDocuments = ["uploading", "analyzing", "reviewing", "adjudicating", "cross_checking"].includes(documentPhase);
        const identityBlocked = ["project_mismatch", "project_identity_incomplete"].includes(documentPhase)
          || ["project_mismatch", "project_identity_incomplete"].includes(documentState?.payload?.state);
        if (processingDocuments) {
          return { key: "documents-required", label: "正在核对研究文件…", disabled: true };
        }
        if (identityBlocked) {
          return { key: "documents-required", label: "请先确认资料归属", disabled: true };
        }
        return { key: "documents-required", label: "请先添加所需文件", disabled: true };
      })()
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
                disabled={phase === "creating"}
                onChange={(event) => {
                  // R4循环：目录型控件在webkitdirectory模式下accept无效，
                  //文件级注入不会注册且此前零反馈（四轮测试位
                  //「FileChooser未形成选中」之谜）。空选择必须可见提示。
                  if (!event.target.files?.length) {
                    setFilePickNotice("未形成选择：该入口只接受文件夹。请选择数据文件夹，或改用下方“选择单个数据文件”。");
                    event.target.value = "";
                    return;
                  }
                  setFilePickNotice("");
                  onSourceFilesChange?.(event.target.files);
                }}
              />
              <span>选择数据文件夹</span>
            </label>
            <label className="monitoring-admission-picker" htmlFor="monitoring-admission-data-files">
              <input
                id="monitoring-admission-data-files"
                type="file"
                multiple
                accept=".csv,.xls,.xlsx,.xlsm"
                disabled={phase === "creating"}
                onChange={(event) => {
                  if (!event.target.files?.length) {
                    setFilePickNotice("未形成选择：请重新选择数据文件。");
                    event.target.value = "";
                    return;
                  }
                  setFilePickNotice("");
                  onSourceFilesChange?.(event.target.files);
                }}
              />
              <span>选择单个数据文件</span>
            </label>
            {filePickNotice ? (
              <p className="monitoring-admission-warning" role="alert">{filePickNotice}</p>
            ) : null}
            {state?.selectedFiles?.length ? (
              <p className="monitoring-admission-selection" role="status">
                已选择“{state.selectedFolderName}”，共 {state.selectedFiles.length} 个文件
              </p>
            ) : null}
            <p className="monitoring-admission-hint">
              支持 {ADMISSION_SUPPORTED_SUFFIX_TEXT} 文件；系统会保留一份项目数据副本，原始文件不会修改。
            </p>
            {!state?.selectedFiles?.length && !state?.sourceDir ? (
              <p className="monitoring-admission-prompt">选择文件夹（或数据文件）后即可开始导入。</p>
            ) : null}
            {/* R4循环：手动路径是四轮测试中实际可用的回退入口，从折叠
                区改为常显小节，不再依赖用户发现低可见度的details。 */}
            <div className="monitoring-admission-manual">
              <span className="monitoring-admission-manual-title">无法选择文件夹时，手动填写数据位置</span>
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
            </div>
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
            {/* R4-03口径澄清：本步表数=文件内全部工作表（含辅助表），
                识别阶段逐表处理，两步口径不同由此而来。 */}
            <p className="monitoring-admission-minor" style={{ margin: "2px 0 8px" }}>
              表数按文件内的全部工作表统计，可能包含代码对照表、名册页等
              辅助表；下一步字段识别会逐表进行，不在此处预先剔除任何表。
            </p>
            {(state.profile?.technical?.skipped_non_data_files || []).length ? (
              <p className="monitoring-admission-warning" role="status">
                已忽略 {state.profile.technical.skipped_non_data_files.length}
                个非数据文件（{state.profile.technical.skipped_non_data_files.slice(0, 5).join("、")}
                {state.profile.technical.skipped_non_data_files.length > 5 ? " 等" : ""}）：
                研究方案、eCRF 等文档请在第3步单独上传，不参与数据导入。
              </p>
            ) : null}
            <details className="monitoring-admission-table-details">
              <summary>
                查看 {profile.tables.length} 张表的结构
                <span>仅在需要时展开</span>
              </summary>
              {profile.tables.map((table) => (
                <details
                  key={`${table.name}-${table.sourceFile}`}
                  className="monitoring-admission-table"
                >
                  <summary className="monitoring-admission-table-head">
                    <strong>{table.name}</strong>
                    <span className="monitoring-admission-table-meta">
                      {table.rowsText} · {table.columnCount} 列
                    </span>
                  </summary>
                  <ul className="monitoring-admission-columns">
                    {table.columns.map((column) => (
                      <li key={column.name}>
                        <span className="monitoring-admission-column-name">{column.name}</span>
                        <span className="monitoring-admission-column-meta">
                          {[column.typeText, column.missingText, column.dateRangeText].filter(Boolean).join(" · ")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </details>
              ))}
            </details>
          </div>
        ) : profile && stepIndex === 2 ? (
          <>
            <DocumentReadinessPanel
              key={`${state.attemptId}:${documentState?.payload?.analysis_token || "pending"}`}
              state={documentState}
              onFiles={onDocumentFiles}
              onRetry={onDocumentRetry}
              onAdjudicate={onDocumentAdjudicate}
              onContentConfirm={onDocumentContentConfirm}
              onIdentityConfirm={onDocumentIdentityConfirm}
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
  // R3循环（报告D）：确认请求可长时间pending（后端同步收尾任务47分钟
  // 不返回），布尔防重入会永久卡死。改为{generation, startedAt}并在
  // 超过5分钟后视为陈旧放行，让手动「确认字段对应关系」可以自救。
  const confirmInFlight = useRef(false);
  const CONFIRM_STALE_MS = 5 * 60 * 1000;
  const documentUploadInFlight = useRef(false);
  // R7-01：resolve轮询的在途去重与退避计数。
  const documentResolveInFlight = useRef(false);
  const documentResolveWaitStreak = useRef(0);
  const importRequestGeneration = useRef(0);
  const documentRequestGeneration = useRef(0);
  const mappingRequestGeneration = useRef(0);
  const factsRequestGeneration = useRef(0);
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

  // R5冲刺（R2-10）：导入进行中的已用时秒表（creating态按钮展示）。
  useEffect(() => {
    if (state.phase !== "creating") return undefined;
    const timer = setInterval(() => {
      dispatch({ type: "import-tick" });
    }, 1000);
    return () => clearInterval(timer);
  }, [state.phase]);

  const submitImport = useCallback(async () => {
    const generation = importRequestGeneration.current + 1;
    importRequestGeneration.current = generation;
    documentRequestGeneration.current += 1;
    mappingRequestGeneration.current += 1;
    factsRequestGeneration.current += 1;
    dispatch({ type: "import-start" });
    if (!state.projectId.trim()) return;
    mappingDispatch({ type: "reset" });
    setDocumentState({ phase: "idle", payload: null, error: null });
    setFactState({ phase: "idle", payload: null, error: null });
    adoptInFlight.current = false;
    adjudicationInFlight.current = false;
    confirmInFlight.current = false;
    factsInFlight.current = false;
    try {
      const payload = state.selectedFiles.length
        ? await api.createDataAdmissionUpload(state.projectId, state.selectedFiles)
        : await api.createDataAdmission(state.projectId, { source_dir: state.sourceDir });
      if (importRequestGeneration.current === generation) {
        dispatch({ type: "import-created", payload });
      }
    } catch (error) {
      if (importRequestGeneration.current === generation) {
        dispatch({ type: "error", error });
      }
    }
  }, [api, state.projectId, state.selectedFiles, state.sourceDir]);

  const loadMappingCandidates = useCallback(async () => {
    if (!state.projectId || !state.attemptId) return;
    const generation = mappingRequestGeneration.current + 1;
    mappingRequestGeneration.current = generation;
    mappingDispatch({ type: "load-start" });
    try {
      const payload = await loadOrStartAdmissionMapping(
        api,
        state.projectId,
        state.attemptId,
      );
      if (mappingRequestGeneration.current !== generation) return;
      mappingDispatch({ type: "load-ready", payload });
      if (
        payload?.confirmation_status === "confirmed"
        || payload?.draft?.status === "confirmed"
      ) {
        dispatch({ type: "finish" });
      }
    } catch (error) {
      if (mappingRequestGeneration.current !== generation) return;
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
        {
          userRoleSelections: selections,
          expectedDecisionVersion: documentState.payload?.decision_version,
        },
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({
          phase: documentPhaseFromPayload(payload),
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

  const submitContentConfirmation = useCallback(async (entry) => {
    if (!state.projectId || !entry?.source_entry_id || !entry?.can_confirm) return;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    try {
      await api.confirmContentValidation(state.projectId, entry.source_entry_id, {
        reason: `已核对${entry.filename || "该研究文件"}所列差异，确认不影响本次医学监查并继续使用。`,
        acknowledgedCheckCodes: entry.acknowledged_check_codes || [],
        expectedRevision: entry.revision || 1,
        idempotencyKey: `doc-content-confirm-${entry.source_entry_id}-${entry.revision || 1}`,
      });
      // 确认后重发resolve推进链路
      const payload = await api.resolveStudyDocuments(
        state.projectId,
        state.attemptId,
        documentState.payload?.analysis_token,
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({
          phase: documentPhaseFromPayload(payload),
          payload,
          error: null,
        });
      }
    } catch (error) {
      if (documentRequestGeneration.current === generation) {
        setDocumentState((current) => ({
          ...current,
          error: error?.detail?.message || error?.message || "内容确认失败，请重试。",
        }));
      }
    }
  }, [api, documentState.payload?.analysis_token, state.attemptId, state.projectId]);

  // R2循环：「重新核对研究文件」必须真正重发核对（有analysis_token时
  // 重新resolve推进链路），而不是只重读readiness快照——否则失败态下
  // 点击后仍报同一错误，按钮语义与行为不符（报告C F1）。
  const retryDocumentCheck = useCallback(async () => {
    if (documentState.payload?.analysis_token) {
      const generation = documentRequestGeneration.current + 1;
      documentRequestGeneration.current = generation;
      setDocumentState((current) => ({ ...current, phase: "analyzing", error: null }));
      try {
        const payload = await api.resolveStudyDocuments(
          state.projectId,
          state.attemptId,
          documentState.payload.analysis_token,
        );
        if (documentRequestGeneration.current === generation) {
          setDocumentState({
            phase: documentPhaseFromPayload(payload),
            payload,
            error: null,
          });
        }
        return;
      } catch (error) {
        if (documentRequestGeneration.current === generation) {
          setDocumentState((current) => ({
            ...current,
            phase: "failed",
            error: error?.detail?.message || error?.message || "研究文件核对失败。",
          }));
        }
        return;
      }
    }
    await loadDocumentReadiness();
  }, [api, documentState.payload?.analysis_token, loadDocumentReadiness, state.attemptId, state.projectId]);

  const submitIdentityConfirmation = useCallback(async (confirmation) => {
    if (!state.projectId || !state.attemptId) return;
    if (confirmation?.confirmed !== true) return;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    setDocumentState((current) => ({ ...current, phase: "analyzing", error: null }));
    try {
      const payload = await api.resolveStudyDocuments(
        state.projectId,
        state.attemptId,
        documentState.payload?.analysis_token,
        { identityConfirmation: confirmation },
      );
      if (documentRequestGeneration.current === generation) {
        setDocumentState({
          phase: documentPhaseFromPayload(payload),
          payload,
          error: null,
        });
      }
    } catch (error) {
      if (documentRequestGeneration.current === generation) {
        setDocumentState((current) => ({
          ...current,
          phase: current.payload?.state || "failed",
          error: error?.detail?.message || error?.message || "归属确认提交失败，请重试。",
        }));
      }
    }
  }, [api, documentState.payload?.analysis_token, state.attemptId, state.projectId]);

  const analyzeDocuments = useCallback(async (files) => {
    if (
      !files?.length || !state.projectId || !state.attemptId
      || documentUploadInFlight.current
    ) return;
    const generation = documentRequestGeneration.current + 1;
    documentRequestGeneration.current = generation;
    documentUploadInFlight.current = generation;
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
      if (documentUploadInFlight.current === generation) {
        documentUploadInFlight.current = false;
      }
    }
  }, [api, state.attemptId, state.projectId]);

  useEffect(() => {
    if (
      !["analyzing", "reviewing", "adjudicating", "cross_checking"]
        .includes(documentState.phase)
    ) return undefined;
    if (!documentState.payload?.analysis_token) {
      // R6-01自愈防御：analyzing态但token缺失（历史遗留状态）时主动
      // 拉取一次readiness快照恢复真实状态，而非停振挂死。
      const timer = setTimeout(() => loadDocumentReadiness(), 1500);
      return () => clearTimeout(timer);
    }
    // R7-01：resolve可达20-30秒——固定1.5秒轮询曾无并发去重，在途
    // 请求堆积占满后端同步线程池致整站假死。两层防护：①在途去重
    // （上一次resolve未返回绝不发起新的）；②连续等待退避1.5s→3s→5s
    // （封顶），拿到新状态即复位。
    if (documentResolveInFlight.current) return undefined;
    const backoffMs = Math.min(1500 * 2 ** Math.min(documentResolveWaitStreak.current, 2), 5000);
    const timer = setTimeout(async () => {
      if (documentResolveInFlight.current) return;
      documentResolveInFlight.current = true;
      const generation = documentRequestGeneration.current + 1;
      documentRequestGeneration.current = generation;
      try {
        const payload = await api.resolveStudyDocuments(
          state.projectId,
          state.attemptId,
          documentState.payload.analysis_token,
        );
        if (documentRequestGeneration.current === generation) {
          documentResolveWaitStreak.current = 0;
          setDocumentState({
            phase: documentPhaseFromPayload(payload),
            payload,
            error: null,
          });
        }
      } catch (error) {
        if (documentRequestGeneration.current === generation) {
          if (error?.detail?.code === "document_resolve_in_progress") {
            // 后端在途防重入的引导：保持当前态，退避后再查。
            documentResolveWaitStreak.current = Math.min(
              documentResolveWaitStreak.current + 1, 2,
            );
            setDocumentState((current) => ({ ...current, error: null }));
            return;
          }
          // R2循环：失败分支必须保留payload——user_choices/analysis_token
          // 都取自payload，清空会让「可裁决」提示与裁决控件同时消失，
          // 把用户锁死在第3步（报告C的document_authority_candidate_
          // not_promotable死锁）。
          setDocumentState((current) => ({
            ...current,
            phase: "failed",
            error: error?.detail?.message || error?.message || "研究文件核对失败。",
          }));
        }
      } finally {
        documentResolveInFlight.current = false;
      }
    }, backoffMs);
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

  // R5冲刺（R1-12）：向导步骤位置记忆——进入第3步后写入，回退到第2步
  // 清除；刷新/关标签重进时恢复到用户上次所在步骤，不再总是从第2步
  // （数据摘要）重新开始。
  useEffect(() => {
    if (!state.attemptId) return undefined;
    const key = `admission-step:${state.projectId}:${state.attemptId}`;
    try {
      if (state.stepIndex === 2 && state.phase !== "done") {
        globalThis.localStorage?.setItem(key, "2");
      } else if (state.stepIndex === 1) {
        globalThis.localStorage?.removeItem(key);
      }
    } catch { /* storage unavailable — step just won't be remembered */ }
    return undefined;
  }, [state.attemptId, state.phase, state.projectId, state.stepIndex]);

  useEffect(() => {
    if (state.phase !== "ready" || state.stepIndex !== 1 || !state.attemptId) return undefined;
    let cancelled = false;
    try {
      const remembered = globalThis.localStorage?.getItem(
        `admission-step:${state.projectId}:${state.attemptId}`,
      );
      if (remembered === "2" && !cancelled) {
        dispatch({ type: "advance" });
      }
    } catch { /* ignore */ }
    return () => {
      cancelled = true;
    };
  }, [state.attemptId, state.phase, state.projectId, state.stepIndex]);

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
    // R2循环（报告B）：依赖数组只含state字符串，load-ready后引用不变、
    // effect不重跑，2.5s轮询实际只排程一次——生成中进度永不自动推进，
    // 页内刷新与整页刷新表现不一致。把payload对象纳入依赖：每次拉取
    // 返回新引用即重排下一次轮询，直到state离开generating。
    const timer = setTimeout(loadMappingCandidates, 2500);
    return () => clearTimeout(timer);
  }, [loadMappingCandidates, mappingState.payload, mappingState.payload?.state, mappingState.phase]);

  const advanceAdjudication = useCallback(async (draft, activeGeneration = null) => {
    if (!draft?.draft_id || adjudicationInFlight.current) return;
    const generation = activeGeneration ?? (mappingRequestGeneration.current + 1);
    if (activeGeneration === null) mappingRequestGeneration.current = generation;
    adjudicationInFlight.current = generation;
    try {
      const payload = await api.adjudicateDataAdmissionMappingDraft(
        state.projectId,
        state.attemptId,
        { draft_id: draft.draft_id },
      );
      if (mappingRequestGeneration.current !== generation) return;
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
      if (mappingRequestGeneration.current !== generation) return;
      mappingDispatch({
        type: "adjudication-blocked",
        payload: draft,
        error: {
          serverText: error?.detail?.message || error?.message || "系统复核暂未完成。",
        },
      });
    } finally {
      if (adjudicationInFlight.current === generation) {
        adjudicationInFlight.current = false;
      }
    }
  }, [api, state.attemptId, state.projectId]);

  // The system adopts the basically-correct recognition draft and performs
  // one focused independent pass before showing any residual questions.
  const adoptDraft = useCallback(async () => {
    if (adoptInFlight.current) return;
    const generation = mappingRequestGeneration.current + 1;
    mappingRequestGeneration.current = generation;
    adoptInFlight.current = generation;
    mappingDispatch({ type: "adopt-start" });
    try {
      const draft = await api.adoptDataAdmissionMappingDraft(
        state.projectId,
        state.attemptId,
        { reason: "采用系统字段识别结果，进入医学确认。" },
      );
      if (mappingRequestGeneration.current !== generation) return;
      mappingDispatch({ type: "adjudication-start", payload: draft });
      await advanceAdjudication(draft, generation);
    } catch (error) {
      if (mappingRequestGeneration.current !== generation) return;
      if (adoptInFlight.current === generation) adoptInFlight.current = false;
      mappingDispatch({
        type: "error",
        error: {
          serverText: error?.detail?.message || error?.message || "采用系统识别结果失败。",
          guidance: ["请稍后重试；若持续失败，请确认字段识别已生成完成。"],
        },
      });
    } finally {
      if (adoptInFlight.current === generation) adoptInFlight.current = false;
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
    if (
      !mappingState.draft?.draft_id
      || (
        confirmInFlight.current
        && Date.now() - confirmInFlight.current.startedAt < CONFIRM_STALE_MS
      )
    ) return;
    const generation = mappingRequestGeneration.current + 1;
    mappingRequestGeneration.current = generation;
    confirmInFlight.current = { generation, startedAt: Date.now() };
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
      if (mappingRequestGeneration.current !== generation) return;
      mappingDispatch({ type: "confirm-ready", payload: revision });
      dispatch({ type: "finish" });
    } catch (error) {
      if (mappingRequestGeneration.current !== generation) return;
      if (confirmInFlight.current?.generation === generation) confirmInFlight.current = false;
      mappingDispatch(mappingConfirmationFailureAction(error, mappingState.draft));
    } finally {
      if (confirmInFlight.current?.generation === generation) confirmInFlight.current = false;
    }
  }, [api, mappingState, state.attemptId, state.projectId]);

  const generateFacts = useCallback(async () => {
    if (!state.projectId || !state.attemptId || factsInFlight.current) return;
    const generation = factsRequestGeneration.current + 1;
    factsRequestGeneration.current = generation;
    factsInFlight.current = generation;
    setFactState({ phase: "generating", payload: null, error: null });
    try {
      const payload = await api.generateDataAdmissionFacts(
        state.projectId,
        state.attemptId,
      );
      if (factsRequestGeneration.current === generation) {
        setFactState({ phase: "ready", payload, error: null });
      }
    } catch (error) {
      if (factsRequestGeneration.current !== generation) return;
      if (factsInFlight.current === generation) factsInFlight.current = false;
      setFactState({
        phase: "failed",
        payload: null,
        error: {
          serverText: error?.detail?.message || error?.message || "监查数据生成失败。",
          guidance: ["请点击重试；原始文件不会被修改。"],
        },
      });
    } finally {
      if (factsInFlight.current === generation) factsInFlight.current = false;
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
    const generation = mappingRequestGeneration.current + 1;
    mappingRequestGeneration.current = generation;
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
      if (mappingRequestGeneration.current !== generation) return;
      mappingDispatch({ type: "answer-ready", key: card.key, payload: draft });
    } catch (error) {
      if (mappingRequestGeneration.current !== generation) return;
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
      onDocumentRetry={retryDocumentCheck}
      onDocumentAdjudicate={submitDocumentAdjudication}
      onDocumentContentConfirm={submitContentConfirmation}
      onDocumentIdentityConfirm={submitIdentityConfirmation}
    />
    </>
  );
}

export default MedicalMonitoringAdmissionWizard;
