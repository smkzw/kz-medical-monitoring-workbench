// Pure helpers for C3 admission mapping confirmation inside the wizard.
// The system adopts basically-correct field recognitions by itself and only
// the medically substantive ambiguities become Chinese question cards.
// Keeps Chinese product copy and candidate/fact separation outside transport.

import { semanticQualityPresentation, semanticQualityBlockedGroups } from "./medicalMonitoringFieldMappingState.mjs";

// Transport-only filter: the wizard always reads the full candidate list and
// derives question cards client-side, so no focus toggle is exposed.
export const MAPPING_FOCUS_CRITICAL = "critical";
export const MAPPING_FOCUS_ALL = "all";

// R25轮（R25-01）：识别生成中的「无进展阈值」。证据：健康推进时字段数
// 数分钟一跳（0→136约20分钟），而单作业极端可到25-40分钟；阈值取30分
// 钟仅在显著超出健康节奏后提示停滞，不轻易误报（提示只如实陈述「无
// 新进展」并提供重读入口，不冒充失败结论）。
export const MAPPING_STALL_THRESHOLD_MS = 30 * 60 * 1000;

// R34轮（R33-B-F1）：复核（adjudicating）阶段的「无出口阈值」。实测
// （report_B.md F1）：确认触发双盲复核后「系统正在复核少量疑点…」占据
// 主按钮位20分钟零变化，页面无任何可点控件。复核单次查询本身可达数分
// 钟（健康推进节奏），阈值取15分钟——显著超出单次查询时长且早于测试
// 者放弃的20分钟；超时后主按钮放行「重新加载识别结果」自救入口。
export const ADJUDICATION_STALL_THRESHOLD_MS = 15 * 60 * 1000;

// R36轮（R36-01）：复核轮询退避。固定1.5秒轮询打在后端持项目写许可的
// 复核推进端点上，叠加页面刷新后在途请求即成雪崩（C位实测 /api/projects
// 11.5s、study-documents/mapping-candidates >15s超时）。等待1分钟内保持
// 1.5秒（复核收敛时快速衔接确认）；此后按等待时长放宽到5秒/15秒——
// 复核健康推进以分钟计，高频轮询不改变收敛时刻，只放大服务端负载。
export const ADJUDICATION_POLL_FAST_MS = 1500;
export const ADJUDICATION_POLL_SLOW_MS = 15000;

export function adjudicationPollDelayMs(state, now = Date.now()) {
  const waited = adjudicationStalledMs(state, now);
  if (waited <= 60_000) return ADJUDICATION_POLL_FAST_MS;
  if (waited <= 5 * 60_000) return 5_000;
  return ADJUDICATION_POLL_SLOW_MS;
}

export function createAdmissionMappingConfirmState() {
  return {
    phase: "idle", // idle | loading | ready | adopting | adjudicating | drafting | confirming | confirmed | failed
    payload: null,
    draft: null,
    revision: null,
    answeredKeys: {}, // question key -> true once the user's answer is saved
    message: "",
    error: null,
    // R25轮（R25-01）：generating期间最近一次字段数变化的时间戳，用于
    // 无进展检测（见mappingStalledMs）。
    progress: { fieldCount: null, since: 0 },
  };
}

// R25轮（R25-01）：识别仍在生成中且超过阈值无新字段——如实暴露停滞，
// 让界面不再无限「识别仍在生成中」（R25A实测136字段处36分钟零变化，
// 无超时无失败提示无重试入口）。
export function mappingStalledMs(state, now = Date.now()) {
  const payload = state?.payload;
  if (!payload) return 0;
  const generating = payload.state === "generating"
    || payload.confirmationStatus === "generating";
  if (!generating) return 0;
  const since = Number(state?.progress?.since) || 0;
  if (!since) return 0;
  return Math.max(0, now - since);
}

// R34轮（R33-B-F1）：复核阶段的已等待时长——自最近一次复核实际进展
// （adjudication-ready载荷变化）起累计；adjudication-running（仍在等
// 待，无新进展）不重置计时，故停滞跨轮询真实累加。
export function adjudicationStalledMs(state, now = Date.now()) {
  if (state?.phase !== "adjudicating") return 0;
  const since = Number(state?.progress?.since) || 0;
  if (!since) return 0;
  return Math.max(0, now - since);
}

export function confidencePercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number * 100)}%`;
}

export function mappingCandidateKey(item) {
  return `${item?.domain || ""}::${item?.source_field || ""}`;
}

// R34轮（R34-02）：研究文件证据链缺失族错误码。报错文案要求「补充上传
// 缺失的研究文件并重新核对」，但错误态此前只有「重新加载识别结果」
// （重载同一422）与「返回上一步」，无任何上传入口或跳转——承诺了不
// 存在的纠错路径。命中这些码时错误区直接内联研究文件补传入口。
export const DOCUMENT_EVIDENCE_ERROR_CODES = Object.freeze([
  "mapping_document_evidence_roles_unmet",
  "mapping_document_evidence_missing",
  "mapping_document_evidence_incomplete",
]);

export function isDocumentEvidenceError(code) {
  return DOCUMENT_EVIDENCE_ERROR_CODES.includes(String(code || ""));
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
// R15轮（R13-02）：AI生成的question偶有残句（如「请确认：而…——」
// 开头即断）。无法修复模型原文本身，但可以：①剥掉悬空的引导词让残句
// 以事实部分呈现；②在卡上展示系统判断详情（见buildSystemJudgment），
// 使确认动作不依赖问题文案的完整性。
function sanitizeQuestionText(text) {
  let value = String(text || "").trim();
  // 引导词后紧跟转折/引用（说明句子主体被截断）时剥掉引导词。
  value = value.replace(/^请确认[：:]?\s*(?=[而但是]|“|")/, "");
  // 结尾悬空的破折号/冒号
  value = value.replace(/[——：:]\s*$/, "");
  return value.trim();
}

function buildSystemJudgment(item) {
  const parts = [];
  if (item.sourceField) parts.push(`字段：${item.domain}·${item.sourceField}`);
  if (item.recommendedRole) parts.push(`系统归类：${item.recommendedRole}`);
  if (item.fieldKind) parts.push(`字段性质：${item.fieldKind}`);
  const doseLabel = item.suggestedAnswer
    || DOSE_SEMANTICS_TEXTS[String(item.doseSemantics || item.dose_semantics || "")] || "";
  if (doseLabel) parts.push(`剂量语义：${doseLabel}`);
  if (Number.isFinite(Number(item.confidence))) {
    parts.push(`置信度：${Math.round(Number(item.confidence) * 100)}%`);
  }
  const evidence = Array.isArray(item.evidenceSummary) ? item.evidenceSummary[0] : null;
  if (evidence) {
    parts.push(`证据覆盖：${Number(evidence.non_empty_count) || 0}/${Number(evidence.total_rows) || 0} 条非空`);
  }
  return parts.join(" · ");
}

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

export function mappingHeadline(payload, { stalledMs = 0, blockedGroupCount = 0 } = {}) {
  if (!payload) return "正在读取系统识别结果…";
  // R2循环：识别未完成（generating）或尚未识别到任何字段时，禁止
  // 「全部对应关系清晰/无需您补充判断」类定论表述——0字段阶段给出
  // 该结论与同屏「仍在生成中」自相矛盾，且会被当作最终结论引用。
  // R3循环：needs_attention（部分识别任务失败）同样禁用定论表述，
  // 如实说明结果来自已完成的任务子集。
  const generating = payload.state === "generating"
    || payload.confirmation_status === "generating";
  if (generating) {
    // R25轮（R25-01）：生成中且超阈值无新字段时，不再恒显「识别仍在
    // 生成中」——如实提示停滞时长与可执行动作（重读/等待失败终态后
    // 的部分结果采纳入口）。
    if (stalledMs >= MAPPING_STALL_THRESHOLD_MS) {
      const minutes = Math.floor(stalledMs / 60000);
      // R35轮（R35-01）：入口承诺改为已兑现的事实——停滞且已有已识别
      // 字段时，「采用已识别字段继续」降级入口即在本页呈现（此前仅在
      // 全部作业落终态失败后出现，大队列场景用户等不到）。
      return `已识别 ${payload.fieldCount} 个字段，但已约 ${minutes} 分钟没有新进展`
        + "——识别可能仍在排队或已停滞。可重新读取识别进度继续等待；"
        + "也可使用下方「采用已识别字段继续」入口，先行采纳已识别的"
        + "字段（停滞分片覆盖的字段不在本批结果中）。";
    }
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
  if (payload.questionCount > 0) {
    return `系统已自动识别 ${payload.fieldCount} 个字段，其中 ${payload.questionCount} 个需要您确认`;
  }
  // R34轮（R33-A-03）：「全部对应关系清晰，无需您补充判断」必须派生自
  // 阻断组计数——语义质量门存在待处理组时（global_blocker_count>0 或
  // 质量门阻断），该定论与同屏「还有N组字段关系需要处理」+禁用按钮
  // 自相矛盾（A位实测1032字段时同屏两组矛盾文案）。如实改为「待处理」
  // 口径，与阻断横幅、按钮态同源。
  if (blockedGroupCount > 0) {
    return `系统已自动识别 ${payload.fieldCount} 个字段；字段质量核对仍有 ${blockedGroupCount} 组字段关系待处理，处理前不能确认`;
  }
  return `系统已自动识别 ${payload.fieldCount} 个字段，全部对应关系清晰，无需您补充判断`;
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
      question: sanitizeQuestionText(questionText(item)),
      evidenceText: mappingEvidenceText(item.evidenceSummary),
      confidence: item.confidence,
      suggestedAnswer: DOSE_SEMANTICS_TEXTS[item.doseSemantics] || "",
      // R13-02：系统判断的具体内容与依据——字段、推荐角色、类型、
      // 置信度、剂量语义、证据覆盖率，全部同屏可核实。
      systemJudgment: buildSystemJudgment(item),
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
  // R32-04：后端按表聚合的识别失败清单（table_failures）——此前界面
  // 只笼统说「部分识别任务已终态失败」，用户须自行心算失败表下落。
  const failedTables = (Array.isArray(payload?.table_failures) ? payload.table_failures : [])
    .map((item) => ({
      tableName: String(item?.table_name || ""),
      failedChunks: Number(item?.failed_chunks || 0),
      failureCodes: Array.isArray(item?.failure_codes) ? item.failure_codes.map(String) : [],
      chunks: Array.isArray(item?.chunks) ? item.chunks.map((chunk) => ({
        chunkIndex: String(chunk?.chunk_index || ""),
        status: String(chunk?.status || ""),
        failureCode: String(chunk?.failure_code || ""),
        attemptCount: Number(chunk?.attempt_count || 0),
        maxAttempts: Number(chunk?.max_attempts || 0),
      })) : [],
    }));
  return {
    state: String(payload?.state || ""),
    confirmationStatus: String(payload?.confirmation_status || "pending_confirmation"),
    factsGenerated: Boolean(payload?.facts_generated),
    fieldCount,
    questionCount,
    failedTables,
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
    question: sanitizeQuestionText(questionText(item)),
    systemJudgment: buildSystemJudgment({
      domain: String(item?.domain || ""),
      sourceField: String(item?.source_field || ""),
      recommendedRole: String(item?.recommended_role || ""),
      fieldKind: String(item?.field_kind || ""),
      suggestedAnswer: DOSE_SEMANTICS_TEXTS[String(item?.dose_semantics || "")] || "",
      confidence: item?.confidence,
      evidenceSummary: Array.isArray(item?.evidence_summary) ? item.evidence_summary : [],
    }),
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

// R32-02：阻断确认的「待处理字段关系」组（标题/摘要/涉及字段当前角色）。
// 数据一直随草稿下发，此前界面从不渲染——B位实测「还有1组字段关系需要
// 处理」横幅下页面零控件、确认按钮永久disabled（report_B.md:33-34）。
export function mappingBlockedRelationGroups(mappingState) {
  return semanticQualityBlockedGroups(mappingState?.draft?.semantic_quality);
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
  // R34轮（R33-A-03）：headline必须携带阻断组计数——语义质量门的待处理
  // 组来自 draft.semantic_quality，若headline只看问题卡数，0问题+有阻断
  // 时会渲染「全部对应关系清晰」与同屏阻断横幅/禁用按钮互相矛盾。
  const blockedGroupCount = Number(draft?.semantic_quality?.global_blocker_count)
    || semanticQualityBlockedGroups(draft?.semantic_quality).length;
  const payload = questions === null ? state.payload : {
    ...state.payload,
    questionCount: questions.length,
    blockedGroupCount,
    headline: mappingHeadline({
      fieldCount: state.payload?.fieldCount || 0,
      questionCount: questions.length,
    }, { blockedGroupCount }),
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
  // R34轮（R33-B-F1）：双盲复核尚未完成时，确认被拒是「等待」而非
  // 「失败」——此前该409落入draft-error，主按钮变「重试完成字段识别」，
  // 用户被迫手动重试5+次（每次2-3.5分钟）且失败文案零环节信息。改走
  // adjudication-start：界面进入自动轮询的复核等待，复核收敛后确认
  // 自动继续，无需人工重试循环。
  if (error?.detail?.code === "mapping_verifier_incomplete") {
    return { type: "adjudication-start", payload: draft };
  }
  return {
    type: "draft-error",
    error: {
      // R34轮（R33-B-F1）：错误码随失败透出——此前只留serverText，
      // 测试5+次失败循环无一给出错误码（report_B.md F1「零错误信息」）。
      code: error?.detail?.code || error?.code || "",
      serverText: error?.detail?.message || error?.message || "字段识别结果保存失败。",
      guidance: ["请点击重试；系统不会要求您重新逐项核对。"],
    },
  };
}

export function admissionMappingConfirmReducer(state, action) {
  switch (action?.type) {
    case "load-start":
      // R31轮（R31-03）：后台自动刷新（2.5s轮询）不得把已就绪面板打回
      // 「正在读取系统识别结果…」灰置态——此前每次轮询都load-start翻转
      // phase，服务端慢时按钮长期停在灰置文案，停滞承诺的「重新读取
      // 识别进度」入口被遮蔽（R31B实测70+分钟用户看不到任何可点入口）。
      // 已有payload时保持phase只清错误；无payload或失败重载才进loading。
      if (state.payload && state.phase !== "failed") {
        return { ...state, error: null };
      }
      return { ...state, phase: "loading", error: null, message: "正在读取系统识别结果…" };
    case "load-ready":
      {
        const payload = projectMappingCandidates(action.payload);
        // R25轮（R25-01）：generating期间记录最近一次字段数变化时间——
        // 字段数前进即重置计时；不变则保留原计时（停滞时长跨轮询累计）。
        const generating = payload.state === "generating"
          || payload.confirmationStatus === "generating";
        const previousCount = state.progress?.fieldCount ?? null;
        const unchanged = previousCount !== null
          && Number(previousCount) === payload.fieldCount
          && Boolean(state.progress?.since);
        const progress = generating
          ? (unchanged
            ? state.progress
            : { fieldCount: payload.fieldCount, since: Date.now() })
          : { fieldCount: null, since: 0 };
        const loaded = {
        ...state,
        phase: "ready",
        payload,
        progress,
        message: action.payload?.state === "generating"
          ? "字段识别仍在生成中，请稍后刷新进度。"
          : action.payload?.state === "needs_attention"
            ? "部分字段识别任务已终态失败；已完成的识别结果可采纳继续，缺失字段如实列示。"
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
            message: "系统已保存全部字段映射确认结果，无需您逐项核对。",
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
        // R34轮（R33-B-F1）：复核停滞计时起点——adjudication-running
        // 不重置（无进展持续累计），adjudication-ready（真实进展）重置。
        // R36轮（R36-01）：verifiedCount记录服务端复核分片已完成数，
        // 分片数前进同样是真实进展（复位停滞计时）。
        progress: { fieldCount: null, since: Date.now(), verifiedCount: null },
        error: null,
      };
    case "adjudication-running": {
      // R34轮（R33-B-F1）：running=仍在等待、无新进展——保留计时起点，
      // 停滞时长跨轮询累计；超阈值后主按钮放行自救入口。
      // R36轮（R36-01）：服务端聚合进度（复核分片已完成数）前进即真实
      // 进展——重置停滞计时，不再把验证队列正常收尾误判为卡死（C位实测
      // 复核期队列以分钟级推进，界面零展示致15分钟误判停滞并重入）。
      const completed = Number(action.payload?.adjudication?.completed_job_count);
      const previousVerified = state.progress?.verifiedCount;
      const verifiedAdvanced = Number.isFinite(completed)
        && Number.isFinite(previousVerified)
        && completed > previousVerified;
      return {
        ...state,
        phase: "adjudicating",
        draft: action.payload,
        message: "系统正在复核少量疑点，尽量减少需要您判断的内容…",
        progress: verifiedAdvanced
          ? { fieldCount: null, since: Date.now(), verifiedCount: completed }
          : {
            fieldCount: null,
            since: state.progress?.since || Date.now(),
            verifiedCount: Number.isFinite(completed) && !Number.isFinite(previousVerified)
              ? completed
              : previousVerified ?? null,
          },
        error: null,
      };
    }
    case "adjudication-ready": {
      const resolved = Number(action.payload?.adjudication?.resolved_count) || 0;
      return projectDraftState(
        {
          ...state,
          // R34轮（R33-B-F1）：复核有真实进展，重置停滞计时（进入
          // drafting后计时不再参与判定；保留干净状态供下轮复核使用）。
          progress: { fieldCount: null, since: Date.now() },
        },
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
        // R36轮（R36-01）：降级确认的回执如实区分，不冒充双盲复核已
        // 收敛的常规确认。
        message: action.degraded
          ? "已按您的选择在不等待复核的情况下确认字段对应关系（降级确认已留痕）。可用于监查的数据尚未生成，需在后续步骤单独生成。"
          : "字段对应关系已确认。可用于监查的数据尚未生成，需在后续步骤单独生成。",
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
    || state.phase === "confirming"
  ) {
    return { key: "busy", label: state.message || "处理中…", disabled: true };
  }
  if (state.phase === "adjudicating") {
    // R34轮（R33-B-F1）：复核超过无出口阈值时放行自救入口——实测
    // 「系统正在复核少量疑点…」busy按钮20分钟零变化零控件（report_B
    // .md F1末态）。reload重读识别结果：复核已收敛时会自然回到确认
    // 门，未收敛则回到可重试状态，用户不再被锁死。
    if (adjudicationStalledMs(state) >= ADJUDICATION_STALL_THRESHOLD_MS) {
      return {
        key: "reload",
        label: "复核长时间无结果，重新加载识别结果",
        disabled: false,
      };
    }
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
          : quality.blocksConfirmation
            // R32-02：阻断时按钮文案如实反映阻断（横幅同口径），不再
            // 显示可点语义的「确认字段对应关系」却永远禁用。
            ? (quality.title || "字段关系需要处理后才能确认")
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
      // R25轮（R25-01）例外：无进展超过阈值（R25A实测136字段处36分钟
      // 零变化、无任何恢复入口）时，按钮切换为可点击的重读入口——
      // 停滞态不会闪换（只有跨过阈值那一刻变化一次），且这是用户在
      // 界面上唯一的主动恢复手段。
      if (mappingStalledMs(state) >= MAPPING_STALL_THRESHOLD_MS) {
        return {
          key: "reload",
          label: "识别长时间无新进展，重新读取识别结果",
          disabled: false,
        };
      }
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
