// Pure helpers for C3 admission mapping confirmation inside the wizard.
// The system adopts basically-correct field recognitions by itself and only
// the medically substantive ambiguities become Chinese question cards.
// Keeps Chinese product copy and candidate/fact separation outside transport.

import { semanticQualityPresentation } from "./medicalMonitoringFieldMappingState.mjs";

// Transport-only filter: the wizard always reads the full candidate list and
// derives question cards client-side, so no focus toggle is exposed.
export const MAPPING_FOCUS_CRITICAL = "critical";
export const MAPPING_FOCUS_ALL = "all";

export function createAdmissionMappingConfirmState() {
  return {
    phase: "idle", // idle | loading | ready | adopting | adjudicating | drafting | confirming | confirmed | failed
    payload: null,
    draft: null,
    revision: null,
    answeredKeys: {}, // question key -> true once the user's answer is saved
    message: "",
    error: null,
  };
}

export function confidencePercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number * 100)}%`;
}

export function mappingCandidateKey(item) {
  return `${item?.domain || ""}::${item?.source_field || ""}`;
}

const QUESTION_TYPE_TEXTS = Object.freeze({
  string: "文本",
  text: "文本",
  decimal: "数值",
  number: "数值",
  date: "日期",
  mixed: "混合内容",
  empty: "空列",
});

const DOSE_SEMANTICS_TEXTS = Object.freeze({
  planned: "计划剂量",
  prescribed: "处方剂量",
  actual_administered: "实际给药剂量",
  dispensed: "发放量",
  returned: "回收量",
  duplicate_or_derived: "重复或派生剂量",
});

function questionTypeText(value) {
  return QUESTION_TYPE_TEXTS[value] || "类型待定";
}

export function mappingEvidenceText(evidenceSummary) {
  const evidence = Array.isArray(evidenceSummary) ? evidenceSummary[0] : null;
  if (!evidence) return "";
  const parts = [
    `${Number(evidence.non_empty_count) || 0}/${Number(evidence.total_rows) || 0} 条非空`,
    questionTypeText(evidence.inferred_type),
  ];
  if (Number(evidence.sample_count) > 0) {
    parts.push(`${Number(evidence.sample_count)} 个样例默认隐藏`);
  }
  return parts.join(" · ");
}

// Card question copy: the backend triage writes the authoritative Chinese
// question (question_text); the harness question and a plain-language
// template are the fallbacks for older payloads.
function questionText(item) {
  const serverQuestion = String(item?.questionText || item?.question_text || "").trim();
  if (serverQuestion) return serverQuestion;
  const action = String(item?.userAction || item?.user_action || "").trim();
  if (action) return action;
  const field = String(item?.sourceField || item?.source_field || "该列");
  const reason = String(item?.attentionReason || item?.attention_reason || "");
  if (reason === "暂未映射") return `系统未能识别「${field}」这一列的用途，请说明它记录的内容。`;
  if (reason === "用药边界") return `「${field}」可能涉及用药信息，请确认这一列的实际用途。`;
  if (reason === "建议缺失") return `系统对「${field}」还没有形成完整判断，请补充说明。`;
  return `请确认「${field}」这一列的识别结果是否符合实际。`;
}

export function mappingHeadline(payload) {
  if (!payload) return "正在读取系统识别结果…";
  // R2循环：识别未完成（generating）或尚未识别到任何字段时，禁止
  // 「全部对应关系清晰/无需您补充判断」类定论表述——0字段阶段给出
  // 该结论与同屏「仍在生成中」自相矛盾，且会被当作最终结论引用。
  // R3循环：needs_attention（部分识别任务失败）同样禁用定论表述，
  // 如实说明结果来自已完成的任务子集。
  const generating = payload.state === "generating"
    || payload.confirmation_status === "generating";
  if (generating) {
    return payload.questionCount > 0
      ? `已识别 ${payload.fieldCount} 个字段（其中 ${payload.questionCount} 个待确认），识别仍在生成中…`
      : `已识别 ${payload.fieldCount} 个字段，识别仍在生成中，完成后会显示结论…`;
  }
  if (payload.state === "needs_attention") {
    return payload.fieldCount > 0
      ? `已识别 ${payload.fieldCount} 个字段（部分识别任务未完成），可采纳当前结果继续`
      : "字段识别任务未能完成，请重试或重新发起识别";
  }
  if (!Number(payload.fieldCount)) {
    return "尚未识别到字段，识别结果为空，请确认数据文件是否包含数据列。";
  }
  return payload.questionCount > 0
    ? `系统已自动识别 ${payload.fieldCount} 个字段，其中 ${payload.questionCount} 个需要您确认`
    : `系统已自动识别 ${payload.fieldCount} 个字段，全部对应关系清晰，无需您补充判断`;
}

function summaryCount(...values) {
  for (const value of values) {
    const parsed = Number(value);
    if (Number.isFinite(parsed) && parsed >= 0) return parsed;
  }
  return 0;
}

export function projectMappingCandidates(payload) {
  const summary = payload?.summary || {};
  const candidates = Array.isArray(payload?.candidates) ? payload.candidates : [];
  const projected = candidates.map((item) => ({
    domain: String(item.domain || ""),
    sourceField: String(item.source_field || ""),
    recommendedRole: String(item.recommended_role || ""),
    fieldKind: String(item.field_kind || ""),
    confidence: item.confidence,
    doseSemantics: String(item.dose_semantics || ""),
    uncertainty: String(item.uncertainty || ""),
    userAction: String(item.user_action || ""),
    questionText: String(item.question_text || ""),
    attentionReason: String(item.attention_reason || ""),
    needsAttention: Boolean(item.needs_attention),
    evidenceSummary: Array.isArray(item.evidence_summary) ? item.evidence_summary : [],
    confirmationStatus: String(item.confirmation_status || "pending_confirmation"),
  }));
  const questionCards = projected
    .filter((item) => item.needsAttention)
    .map((item) => ({
      key: mappingCandidateKey({ domain: item.domain, source_field: item.sourceField }),
      domain: item.domain,
      sourceField: item.sourceField,
      attentionReason: item.attentionReason || "需要确认",
      question: questionText(item),
      evidenceText: mappingEvidenceText(item.evidenceSummary),
      confidence: item.confidence,
      suggestedAnswer: DOSE_SEMANTICS_TEXTS[item.doseSemantics] || "",
    }));
  const byDomain = new Map();
  for (const item of projected) {
    const entry = byDomain.get(item.domain) || { name: item.domain, fieldCount: 0, questionCount: 0 };
    entry.fieldCount += 1;
    if (item.needsAttention) entry.questionCount += 1;
    byDomain.set(item.domain, entry);
  }
  const fieldCount = summaryCount(summary.field_count, summary.candidate_count, projected.length);
  const questionCount = summaryCount(summary.user_question_count, summary.critical_count, questionCards.length);
  return {
    state: String(payload?.state || ""),
    confirmationStatus: String(payload?.confirmation_status || "pending_confirmation"),
    factsGenerated: Boolean(payload?.facts_generated),
    fieldCount,
    questionCount,
    headline: mappingHeadline({
      fieldCount,
      questionCount,
      state: payload?.state,
      confirmation_status: payload?.confirmation_status,
    }),
    questions: questionCards,
    tableSummaries: [...byDomain.values()].sort((a, b) => a.name.localeCompare(b.name, "zh-CN")),
    candidates: projected,
    raw: payload,
  };
}

export function mappingQuestionCards(mappingState) {
  return Array.isArray(mappingState?.payload?.questions) ? mappingState.payload.questions : [];
}

function draftQuestionCards(draft) {
  if (!Array.isArray(draft?.user_questions)) return null;
  return draft.user_questions.map((item) => ({
    key: mappingCandidateKey(item),
    domain: String(item?.domain || ""),
    sourceField: String(item?.source_field || ""),
    attentionReason: String(item?.attention_reason || "需要确认"),
    question: questionText(item),
    priorUserAction: String(item?.prior_user_action || ""),
    reusablePriorAnswer: (() => {
      const answer = String(item?.prior_user_action || "").replace(/^用户已(?:确认|核对)：/, "").trim();
      return answer && answer.length <= 80 && answer !== "采用系统判断，无需修改。" ? answer : "";
    })(),
    evidenceText: mappingEvidenceText(item?.evidence_summary),
    confidence: item?.confidence,
    suggestedAnswer: DOSE_SEMANTICS_TEXTS[String(item?.dose_semantics || "")] || "",
  }));
}

export function mappingUnansweredCount(mappingState) {
  const answered = mappingState?.answeredKeys || {};
  return mappingQuestionCards(mappingState).filter((card) => !answered[card.key]).length;
}

// Durable audit line for the confirm call; always longer than the server's
// 10-character minimum and reflects what the user actually answered.
export function mappingConfirmationReason(mappingState) {
  const total = mappingQuestionCards(mappingState).length;
  const answered = total - mappingUnansweredCount(mappingState);
  const adjudicated = Number(
    mappingState?.draft?.review_summary?.system_adjudicated_count,
  ) || 0;
  return total > 0
    ? `系统独立复核 ${adjudicated} 项；用户逐条回答 ${total} 个医学确认问题（${answered}/${total} 已确认）。`
    : adjudicated > 0
      ? `系统独立复核并自动处理 ${adjudicated} 项，当前无须用户补充判断。`
      : "系统字段识别结果无实质歧义，全部字段已自动对应。";
}

function projectDraftState(state, draft, message = "") {
  const questions = draftQuestionCards(draft);
  const answeredKeys = { ...state.answeredKeys };
  // A server question is unresolved for this draft, even if the same field
  // was answered against an earlier evidence generation.
  for (const question of questions || []) delete answeredKeys[question.key];
  const payload = questions === null ? state.payload : {
    ...state.payload,
    questionCount: questions.length,
    headline: mappingHeadline({
      fieldCount: state.payload?.fieldCount || 0,
      questionCount: questions.length,
    }),
    questions,
    tableSummaries: (state.payload?.tableSummaries || []).map((table) => ({
      ...table,
      questionCount: questions.filter((item) => item.domain === table.name).length,
    })),
  };
  return {
    ...state,
    phase: "drafting",
    payload,
    draft,
    answeredKeys,
    message: message || ((payload?.questionCount || 0) > 0
      ? "系统识别结果已就绪，请回答下方需要您确认的问题。"
      : ""),
    error: null,
  };
}

export function mappingConfirmationFailureAction(error, draft) {
  if (error?.detail?.code === "mapping_reconciliation_required") {
    return { type: "adjudication-start", payload: draft };
  }
  return {
    type: "draft-error",
    error: {
      serverText: error?.detail?.message || error?.message || "字段识别结果保存失败。",
      guidance: ["请点击重试；系统不会要求您重新逐项核对。"],
    },
  };
}

export function admissionMappingConfirmReducer(state, action) {
  switch (action?.type) {
    case "load-start":
      return { ...state, phase: "loading", error: null, message: "正在读取系统识别结果…" };
    case "load-ready":
      {
        const payload = projectMappingCandidates(action.payload);
        const loaded = {
        ...state,
        phase: "ready",
        payload,
        message: action.payload?.state === "generating"
          ? "字段识别仍在生成中，请稍后刷新进度。"
          : action.payload?.state === "needs_attention"
            ? "部分字段识别尚未完成，请先刷新等待生成结束。"
            : "",
        error: null,
        };
        if (
          action.payload?.confirmation_status === "confirmed"
          || action.payload?.draft?.status === "confirmed"
        ) {
          return {
            ...loaded,
            phase: "confirmed",
            draft: action.payload?.draft || null,
            message: "系统已保存全部字段对应关系，无需您逐项核对。",
          };
        }
        if (action.payload?.draft?.draft_id) {
          return projectDraftState(loaded, action.payload.draft);
        }
        return loaded;
      }
    case "adopt-start":
      return { ...state, phase: "adopting", error: null, message: "正在采用系统识别结果…" };
    case "adopt-ready":
      return projectDraftState(state, action.payload);
    case "adjudication-start":
      return {
        ...state,
        phase: "adjudicating",
        draft: action.payload,
        message: "系统正在复核少量疑点，尽量减少需要您判断的内容…",
        error: null,
      };
    case "adjudication-running":
      return {
        ...state,
        phase: "adjudicating",
        draft: action.payload,
        message: "系统正在复核少量疑点，尽量减少需要您判断的内容…",
        error: null,
      };
    case "adjudication-ready": {
      const resolved = Number(action.payload?.adjudication?.resolved_count) || 0;
      return projectDraftState(
        state,
        action.payload,
        resolved > 0 ? `系统又自动完成了 ${resolved} 项判断。` : "",
      );
    }
    case "adjudication-blocked":
      return {
        ...state,
        phase: "failed",
        draft: action.payload?.draft_id ? action.payload : state.draft,
        message: "",
        error: action.error || {
          serverText: "系统复核暂未完成，请稍后重试。原始数据不会受到影响。",
        },
      };
    case "adjudication-fallback":
      return projectDraftState(
        state,
        action.payload,
        "系统没有足够依据继续自动判断，仅保留确实需要核对的问题。",
      );
    case "answer-ready":
      return {
        ...state,
        phase: "drafting",
        draft: action.payload,
        answeredKeys: { ...state.answeredKeys, [action.key]: true },
        message: "已记录您的确认。",
        error: null,
      };
    case "confirm-start":
      return { ...state, phase: "confirming", error: null, message: "正在确认字段对应关系…" };
    case "confirm-ready":
      return {
        ...state,
        phase: "confirmed",
        revision: action.payload,
        message: "字段对应关系已确认。可用于监查的数据尚未生成，需在后续步骤单独生成。",
        error: null,
      };
    case "draft-error":
      return {
        ...state,
        phase: "drafting",
        error: action.error || { serverText: "本次确认未能保存。" },
        message: "",
      };
    case "error":
      return {
        ...state,
        phase: "failed",
        error: action.error || { serverText: "字段识别结果未能读取。" },
        message: "",
      };
    case "reset":
      return createAdmissionMappingConfirmState();
    default:
      return state;
  }
}

export function admissionMappingPrimaryAction(state) {
  if (!state) return { key: "noop", label: "请稍候", disabled: true };
  if (
    state.phase === "loading"
    || state.phase === "adopting"
    || state.phase === "adjudicating"
    || state.phase === "confirming"
  ) {
    return { key: "busy", label: state.message || "处理中…", disabled: true };
  }
  if (state.phase === "confirmed") {
    return { key: "finish", label: "完成接入", disabled: false };
  }
  if (state.phase === "drafting" && state.draft) {
    const quality = semanticQualityPresentation(state.draft.semantic_quality);
    const unanswered = mappingUnansweredCount(state);
    // R3循环修正：原disabled含「!state.error ||」——无错误时恒为true，
    // 确认按钮永远禁用（报告D：60字段全部清晰后47分钟无法确认）。
    // 正确语义：仅有未回答问题或质量门阻断时禁用；出错时按钮是
    // 「重试」；无错且无疑点时按钮是手动兜底确认入口（自动确认
    // 卡在长请求时用户可自救），均可点击。
    return {
      key: "confirm",
      label: state.error
        ? "重试完成字段识别"
        : unanswered > 0
          ? `请先回答 ${unanswered} 个问题`
          : "确认字段对应关系",
      disabled: quality.blocksConfirmation || unanswered > 0,
    };
  }
  if (state.phase === "ready") {
    const payloadState = state.payload?.state;
    const fieldCount = state.payload?.fieldCount;
    if (payloadState === "candidates_ready") {
      if (!fieldCount) {
        return { key: "noop", label: "暂无字段识别结果", disabled: true };
      }
      return { key: "adopt", label: "采用系统识别结果", disabled: false };
    }
    if (payloadState === "needs_attention") {
      // R3循环修正（报告C）：部分识别任务失败时原实现落入默认分支，
      // 主按钮变成「加载识别结果」点击循环——已完成任务的字段结果
      // 应可被知情采纳；无任何完成结果时如实报告。
      if (fieldCount) {
        return { key: "adopt", label: `采用已识别的 ${fieldCount} 个字段并继续`, disabled: false };
      }
      return { key: "reload", label: "识别任务未成功，重新加载", disabled: false };
    }
    if (payloadState === "generating") {
      // R9轮（R5-05）：识别生成期间按钮曾在禁用/启用间每数秒闪换
      // （轮询load-start→ready→…循环改写主按钮），点击瞬间被禁用。
      // 自动轮询已持续拉取（R2-05修复），按钮保持单一稳定禁用文案，
      // 不再提供会闪换的手动刷新入口。
      return {
        key: "busy",
        label: "正在生成字段识别结果…（自动刷新进度，无需手动刷新）",
        disabled: true,
      };
    }
  }
  if (state.phase === "failed") {
    return { key: "reload", label: "重新加载识别结果", disabled: false };
  }
  return { key: "reload", label: "加载识别结果", disabled: false };
}
