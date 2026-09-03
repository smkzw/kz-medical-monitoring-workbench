import assert from "node:assert/strict";
import test from "node:test";

import {
  MAPPING_FOCUS_ALL,
  admissionMappingConfirmReducer,
  admissionMappingPrimaryAction,
  createAdmissionMappingConfirmState,
  mappingConfirmationReason,
  mappingEvidenceText,
  mappingQuestionCards,
  mappingUnansweredCount,
  projectMappingCandidates,
} from "./medicalMonitoringAdmissionMappingConfirmState.mjs";

function candidatesPayload({ withQuestions = true, serverTriage = false } = {}) {
  return {
    state: "candidates_ready",
    confirmation_status: "pending_confirmation",
    facts_generated: false,
    summary: {
      candidate_count: 10,
      critical_count: 2,
      displayed_count: 10,
      ...(serverTriage ? { field_count: 10, user_question_count: 2, system_adopted_count: 8 } : {}),
    },
    candidates: [
      {
        domain: "AE",
        source_field: "AETERM",
        recommended_role: "ae_term",
        confidence: 0.5,
        attention_reason: "低置信度",
        needs_attention: true,
        user_action: "请确认这一列是否为不良事件名称。",
        ...(serverTriage ? { question_text: "「AE·AETERM」的识别把握不足，请核对原始数据。" } : {}),
        evidence_summary: [{
          inferred_type: "text",
          total_rows: 128,
          non_empty_count: 126,
          sample_count: 2,
          samples_hidden: true,
        }],
      },
      {
        domain: "AE",
        source_field: "AESTDT",
        recommended_role: "ae_start_date",
        confidence: 0.4,
        attention_reason: "用药边界",
        needs_attention: true,
        user_action: "",
      },
      {
        domain: "AE",
        source_field: "AESER",
        recommended_role: "ae_serious",
        confidence: 0.99,
        attention_reason: "",
        needs_attention: false,
      },
    ],
  };
}

test("server triage question text and summary keys take precedence", () => {
  const projected = projectMappingCandidates(candidatesPayload({ serverTriage: true }));
  assert.match(projected.questions[0].question, /识别把握不足/);
  assert.equal(projected.fieldCount, 10);
  assert.equal(projected.questionCount, 2);
});

test("projection keeps Chinese summary, question cards and table summaries", () => {
  const projected = projectMappingCandidates(candidatesPayload());
  assert.match(projected.headline, /10 个字段/);
  assert.match(projected.headline, /2 个需要您确认/);
  assert.equal(projected.factsGenerated, false);
  assert.equal(projected.fieldCount, 10);
  assert.equal(projected.questionCount, 2);
  assert.equal(projected.questions.length, 2);
  assert.deepEqual(
    projected.questions.map((card) => card.sourceField),
    ["AETERM", "AESTDT"],
  );
  assert.match(projected.questions[0].question, /不良事件名称/);
  assert.equal(projected.questions[1].attentionReason, "用药边界");
  assert.match(projected.questions[1].question, /AESTDT/);
  assert.deepEqual(projected.tableSummaries, [
    { name: "AE", fieldCount: 3, questionCount: 2 },
  ]);
});

test("question cards stay hidden for candidates the system adopts itself", () => {
  const projected = projectMappingCandidates({
    state: "candidates_ready",
    summary: { candidate_count: 3, critical_count: 0 },
    candidates: [
      { domain: "SV", source_field: "VISIT", confidence: 0.99, needs_attention: false },
      { domain: "SV", source_field: "VISITDT", confidence: 0.95, needs_attention: false },
    ],
  });

  assert.equal(projected.questions.length, 0);
  assert.match(projected.headline, /无需您补充判断/);
});

test("evidence text keeps counts and hides sample values", () => {
  assert.equal(
    mappingEvidenceText([{
      inferred_type: "date",
      total_rows: 128,
      non_empty_count: 126,
      sample_count: 3,
    }]),
    "126/128 条非空 · 日期 · 3 个样例默认隐藏",
  );
  assert.equal(mappingEvidenceText([]), "");
});

test("confirm waits until every question card is answered", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: candidatesPayload(),
  });
  assert.equal(state.phase, "ready");
  assert.equal(admissionMappingPrimaryAction(state).key, "adopt");

  state = admissionMappingConfirmReducer(state, {
    type: "adopt-ready",
    payload: { draft_id: "d1", version: 1, fields: [] },
  });
  assert.equal(admissionMappingPrimaryAction(state).key, "confirm");
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);
  assert.equal(mappingUnansweredCount(state), 2);

  state = admissionMappingConfirmReducer(state, {
    type: "answer-ready",
    key: "AE::AETERM",
    payload: { draft_id: "d1", version: 2, fields: [] },
  });
  assert.equal(mappingUnansweredCount(state), 1);
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);

  state = admissionMappingConfirmReducer(state, {
    type: "answer-ready",
    key: "AE::AESTDT",
    payload: { draft_id: "d1", version: 3, fields: [] },
  });
  assert.equal(mappingUnansweredCount(state), 0);
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);
  assert.match(admissionMappingPrimaryAction(state).label, /系统正在完成/);
});

test("adopted draft replaces stale candidate questions after system normalization", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: candidatesPayload(),
  });
  state = admissionMappingConfirmReducer(state, {
    type: "adopt-ready",
    payload: {
      draft_id: "d1",
      version: 1,
      fields: [],
      user_questions: [{
        domain: "AE",
        source_field: "AETERM",
        attention_reason: "需医学确认",
        question_text: "请确认不良事件术语。",
        evidence_summary: [],
      }],
    },
  });
  assert.equal(state.payload.questionCount, 1);
  assert.equal(state.payload.headline, "系统已自动识别 10 个字段，其中 1 个需要您确认");
  assert.deepEqual(mappingQuestionCards(state).map((item) => item.key), ["AE::AETERM"]);
});

test("second pass stays automatic and exposes only residual questions", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: candidatesPayload(),
  });
  const draft = {
    draft_id: "d1",
    version: 1,
    user_questions: [
      { domain: "AE", source_field: "AETERM", question_text: "问题1" },
      { domain: "AE", source_field: "AESTDT", question_text: "问题2" },
    ],
  };
  state = admissionMappingConfirmReducer(state, {
    type: "adjudication-start",
    payload: draft,
  });
  assert.equal(state.phase, "adjudicating");
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);

  state = admissionMappingConfirmReducer(state, {
    type: "adjudication-ready",
    payload: {
      ...draft,
      version: 2,
      adjudication: { state: "complete", resolved_count: 1 },
      user_questions: [
        { domain: "AE", source_field: "AESTDT", question_text: "问题2" },
      ],
    },
  });
  assert.equal(state.phase, "drafting");
  assert.equal(state.payload.questionCount, 1);
  assert.deepEqual(mappingQuestionCards(state).map((item) => item.key), ["AE::AESTDT"]);
  assert.match(state.message, /自动完成了 1 项/);
});

test("blocked blind review never falls through to automatic confirmation", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: candidatesPayload(),
  });
  state = admissionMappingConfirmReducer(state, {
    type: "adjudication-start",
    payload: { draft_id: "d1", version: 1, user_questions: [] },
  });
  state = admissionMappingConfirmReducer(state, {
    type: "adjudication-blocked",
    payload: {
      draft_id: "d1",
      version: 1,
      adjudication: { state: "blocked", resolved_count: 0 },
      user_questions: [],
    },
  });

  assert.equal(state.phase, "failed");
  assert.match(state.error.serverText, /复核暂未完成/);
  assert.equal(admissionMappingPrimaryAction(state).key, "reload");
});

test("confirmation reason names the answered questions and clears the server minimum", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: candidatesPayload(),
  });
  for (const key of ["AE::AETERM", "AE::AESTDT"]) {
    state = admissionMappingConfirmReducer(state, {
      type: "answer-ready",
      key,
      payload: { draft_id: "d1", version: 2, fields: [] },
    });
  }
  const reason = mappingConfirmationReason(state);
  assert.ok(reason.length >= 10, "reason clears the 10-character server minimum");
  assert.match(reason, /2 个医学确认问题/);

  const noQuestions = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "adopt-ready",
    payload: { draft_id: "d1", version: 1, fields: [] },
  });
  assert.match(mappingConfirmationReason(noQuestions), /无实质歧义/);
});

test("semantic blocker keeps overall confirmation disabled", () => {
  const state = {
    ...createAdmissionMappingConfirmState(),
    phase: "drafting",
    draft: {
      draft_id: "d1",
      semantic_quality: {
        status: "blocked",
        activation_disposition: "reject",
        global_blocker_count: 1,
        capability_blocker_count: 0,
        warning_count: 0,
        finding_groups: [],
        capability_states: [],
      },
    },
  };

  assert.equal(admissionMappingPrimaryAction(state).disabled, true);
});

test("generating state offers refresh instead of adoption", () => {
  const state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: {
      state: "generating",
      summary: { candidate_count: 0, critical_count: 0 },
      candidates: [],
    },
  });

  assert.equal(admissionMappingPrimaryAction(state).key, "reload");
  assert.match(state.message, /生成中/);
});

test("failed load waits for an explicit retry", () => {
  const state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "error",
    error: { serverText: "暂时无法加载" },
  });

  assert.equal(state.phase, "failed");
  assert.equal(admissionMappingPrimaryAction(state).key, "reload");
});

test("confirmed mapping resumes as complete without adopting another draft", () => {
  const state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: {
      state: "candidates_ready",
      confirmation_status: "confirmed",
      summary: { field_count: 1495, user_question_count: 0 },
      candidates: [],
      draft: { draft_id: "d1", version: 1, status: "confirmed" },
    },
  });

  assert.equal(state.phase, "confirmed");
  assert.equal(admissionMappingPrimaryAction(state).key, "finish");
  assert.match(state.message, /无需您逐项核对/);
});

test("draft error keeps the draft and the confirmation gate", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "adopt-ready",
    payload: {
      draft_id: "d1",
      version: 1,
      fields: [
        { domain: "AE", source_field: "AESER", user_action: "系统已自动对应。" },
      ],
    },
  });
  state = admissionMappingConfirmReducer(state, {
    type: "draft-error",
    error: { serverText: "确认冲突" },
  });

  assert.equal(state.phase, "drafting");
  assert.equal(state.draft.draft_id, "d1");
  assert.equal(admissionMappingPrimaryAction(state).key, "confirm");
  assert.equal(admissionMappingPrimaryAction(state).disabled, false);
});

test("confirm-ready blocks fact generation and finishes", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "adopt-ready",
    payload: { draft_id: "d1", version: 1, fields: [] },
  });
  state = admissionMappingConfirmReducer(state, {
    type: "confirm-ready",
    payload: { mapping_revision: "r1", facts_generated: false },
  });

  assert.equal(state.phase, "confirmed");
  assert.equal(admissionMappingPrimaryAction(state).key, "finish");
  assert.match(state.message, /尚未生成/);
  assert.equal(mappingQuestionCards(state).length, 0);
});

test("transport focus stays on the full candidate list", () => {
  assert.equal(MAPPING_FOCUS_ALL, "all");
});
