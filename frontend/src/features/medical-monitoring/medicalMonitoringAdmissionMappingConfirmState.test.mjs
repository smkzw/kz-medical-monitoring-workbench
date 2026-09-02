import assert from "node:assert/strict";
import test from "node:test";

import {
  MAPPING_FOCUS_CRITICAL,
  admissionMappingConfirmReducer,
  admissionMappingPrimaryAction,
  createAdmissionMappingConfirmState,
  projectMappingCandidates,
} from "./medicalMonitoringAdmissionMappingConfirmState.mjs";

test("projectMappingCandidates keeps Chinese summary and facts blocked", () => {
  const projected = projectMappingCandidates({
    state: "candidates_ready",
    confirmation_status: "pending_confirmation",
    facts_generated: false,
    summary: {
      candidate_count: 10,
      critical_count: 3,
      displayed_count: 3,
    },
    candidates: [
      {
        domain: "AE",
        source_field: "AETERM",
        recommended_role: "ae_term",
        confidence: 0.5,
        attention_reason: "低置信度",
        needs_attention: true,
      },
    ],
  });
  assert.match(projected.summaryText, /重点关注 3 条/);
  assert.equal(projected.factsGenerated, false);
  assert.equal(projected.candidates[0].attentionReason, "低置信度");
});

test("confirm primary stays disabled without reason and finish after confirm", () => {
  let state = createAdmissionMappingConfirmState();
  state = admissionMappingConfirmReducer(state, {
    type: "adopt-ready",
    payload: { draft_id: "d1", version: 1, fields: [] },
  });
  state = { ...state, confirmationReason: "" };
  assert.equal(admissionMappingPrimaryAction(state).key, "confirm");
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);

  state = admissionMappingConfirmReducer(state, {
    type: "confirm-ready",
    payload: { mapping_revision: "r1", facts_generated: false },
  });
  assert.equal(admissionMappingPrimaryAction(state).key, "finish");
  assert.match(state.message, /尚未生成/);
  assert.equal(state.focus, MAPPING_FOCUS_CRITICAL);
});

test("failed load waits for an explicit retry", () => {
  const state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "error",
    error: { serverText: "暂时无法加载" },
  });

  assert.equal(state.phase, "failed");
  assert.equal(admissionMappingPrimaryAction(state).key, "reload");
});

test("draft error keeps the editable draft and explicit confirmation gate", () => {
  let state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "adopt-ready",
    payload: { draft_id: "d1", version: 1, fields: [] },
  });
  state = admissionMappingConfirmReducer(state, {
    type: "draft-error",
    error: { serverText: "修订冲突" },
  });

  assert.equal(state.phase, "drafting");
  assert.equal(state.draft.draft_id, "d1");
  assert.equal(admissionMappingPrimaryAction(state).key, "confirm");
  assert.equal(admissionMappingPrimaryAction(state).disabled, true);
});

test("semantic blocker keeps overall confirmation disabled", () => {
  const state = {
    ...createAdmissionMappingConfirmState(),
    phase: "drafting",
    confirmationReason: "已完成重点核对",
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

test("missing Chinese review advice blocks overall confirmation", () => {
  const state = {
    ...createAdmissionMappingConfirmState(),
    phase: "drafting",
    confirmationReason: "已核对全部重点字段并确认",
    draft: {
      draft_id: "d1",
      fields: [{ domain: "SV", source_field: "VISIT", user_action: "" }],
    },
  };

  assert.equal(admissionMappingPrimaryAction(state).disabled, true);
});

test("confirmation note requires ten characters", () => {
  const base = {
    ...createAdmissionMappingConfirmState(),
    phase: "drafting",
    draft: { draft_id: "d1" },
  };
  assert.equal(admissionMappingPrimaryAction({ ...base, confirmationReason: "已核对" }).disabled, true);
  assert.equal(admissionMappingPrimaryAction({ ...base, confirmationReason: "已核对全部重点字段并确认" }).disabled, false);
});

test("empty critical view routes to all suggestions instead of blind adoption", () => {
  const state = admissionMappingConfirmReducer(createAdmissionMappingConfirmState(), {
    type: "load-ready",
    payload: {
      state: "candidates_ready",
      summary: { candidate_count: 4, critical_count: 0, displayed_count: 0 },
      candidates: [],
    },
  });

  assert.equal(admissionMappingPrimaryAction(state).key, "show-all");
});
