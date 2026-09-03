import { renderToStaticMarkup } from "react-dom/server";
import { MedicalMonitoringAdmissionWizardView } from "./MedicalMonitoringAdmissionWizard.jsx";
import {
  admissionWizardReducer,
  createAdmissionWizardState,
} from "./medicalMonitoringAdmissionWizardState.mjs";
import {
  admissionMappingConfirmReducer,
  createAdmissionMappingConfirmState,
} from "./medicalMonitoringAdmissionMappingConfirmState.mjs";

// Generated C1 admission payloads (fixtures, never real project data).
function hex(seed, length = 64) {
  let out = "";
  for (let index = 0; index < length; index += 1) {
    out += String.fromCharCode(97 + ((seed + index * 7) % 26));
  }
  return out;
}

function generatedTableFixture({ name, sourceFile, rowCount, withRoles }) {
  const column = (extra = {}) => ({
    name: extra.name,
    inferred_type: extra.inferred_type,
    missing_count: extra.missing ?? 0,
    distinct_count: 12,
    samples: ["示例值"],
    date_range: extra.date_range ?? null,
    suggested_roles: extra.roles ?? [],
  });
  return {
    name,
    source_file: sourceFile,
    row_count: rowCount,
    column_count: 4,
    needs_confirmation: withRoles ? 2 : 0,
    columns: [
      column({ name: "受试者编号", inferred_type: "text", roles: withRoles ? ["受试者标识"] : [] }),
      column({ name: "访视", inferred_type: "text", roles: withRoles ? ["访视"] : [] }),
      column({
        name: "访视日期",
        inferred_type: "date",
        missing: 2,
        roles: withRoles ? ["日期"] : [],
        date_range: { min: "2026-01-12", max: "2026-08-30", parsed_count: rowCount - 2 },
      }),
      column({ name: "实验室结果", inferred_type: "number" }),
    ],
  };
}

export function generatedAdmissionFixture({ withRoles = true } = {}) {
  return {
    schema_version: "mm-c1-data-admission-v1",
    project_id: "proj-e2e-check",
    attempt_id: "adm-20260902-0001",
    state: "profile_ready",
    summary: { files: 2, tables: 2, rows: 164 },
    tables: [
      generatedTableFixture({ name: "访视列表", sourceFile: "visit_listings.csv", rowCount: 128, withRoles }),
      generatedTableFixture({ name: "不良事件", sourceFile: "adverse_events.csv", rowCount: 36, withRoles }),
    ],
    technical_details: {
      manifest_hash: hex(3),
      files: [
        { path: "visit_listings.csv", size: 1536, sha256: hex(5) },
        { path: "adverse_events.csv", size: 20480, sha256: hex(9) },
      ],
      revision_ids: ["srcc1_" + hex(11, 24)],
      snapshot_ids: ["lsnap_" + hex(13, 24)],
      locator_index_ids: ["lsnap_" + hex(15, 24)],
      profile_ids: ["prof_" + hex(17, 24)],
    },
  };
}

function wizardState(transitions) {
  let state = createAdmissionWizardState({ projectId: "proj-e2e-check" });
  for (const transition of transitions) {
    state = admissionWizardReducer(state, transition);
  }
  return state;
}

function readyWizardState() {
  const payload = generatedAdmissionFixture();
  return wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload },
    { type: "profile-loaded", payload },
    { type: "advance" },
  ]);
}

function mappingFrom(transitions) {
  let mapping = createAdmissionMappingConfirmState();
  for (const transition of transitions) {
    mapping = admissionMappingConfirmReducer(mapping, transition);
  }
  return mapping;
}

function render(state, mappingState, factState, documentState) {
  return renderToStaticMarkup(
    <MedicalMonitoringAdmissionWizardView
      state={state}
      documentState={documentState}
      mappingState={mappingState || createAdmissionMappingConfirmState()}
      factState={factState || { phase: "idle", payload: null, error: null }}
      onSourceDirChange={() => {}}
      onSourceFilesChange={() => {}}
      onPrimaryAction={() => {}}
      onSecondaryAction={() => {}}
      onAnswerCard={() => {}}
    />,
  );
}

const profilePayload = generatedAdmissionFixture();
const noRolePayload = generatedAdmissionFixture({ withRoles: false });

// C3 candidates payload: the system auto-adopts the clear recognitions and
// only the substantive ambiguities become question cards.
function candidatesPayload({ withQuestions = true } = {}) {
  return {
    state: "candidates_ready",
    confirmation_status: "pending_confirmation",
    facts_generated: false,
    summary: {
      candidate_count: 2,
      critical_count: withQuestions ? 1 : 0,
      displayed_count: 2,
    },
    candidates: [
      {
        domain: "访视列表",
        source_field: "访视日期",
        recommended_role: "visit_date",
        field_kind: "source_collected",
        confidence: 0.7,
        uncertainty: "需确认实际日期语义。",
        user_action: "请确认这一列是否为实际访视日期。",
        attention_reason: "低置信度",
        needs_attention: withQuestions,
        evidence_summary: [{
          inferred_type: "date",
          total_rows: 128,
          non_empty_count: 126,
          sample_count: 2,
          samples_hidden: true,
        }],
      },
      {
        domain: "访视列表",
        source_field: "受试者编号",
        recommended_role: "subject_id",
        field_kind: "source_collected",
        confidence: 0.99,
        uncertainty: "",
        user_action: "系统已自动对应。",
        attention_reason: "",
        needs_attention: false,
        evidence_summary: [{
          inferred_type: "text",
          total_rows: 128,
          non_empty_count: 128,
          sample_count: 1,
          samples_hidden: true,
        }],
      },
    ],
  };
}

const draftPayload = {
  draft_id: "draft-1",
  version: 1,
  fields: [
    {
      domain: "访视列表",
      source_field: "访视日期",
      recommended_role: "visit_date",
      field_kind: "source_collected",
      confidence: 0.7,
      attention_reason: "低置信度",
      uncertainty: "需确认实际日期语义。",
      user_action: "请确认这一列是否为实际访视日期。",
    },
    {
      domain: "访视列表",
      source_field: "受试者编号",
      recommended_role: "subject_id",
      field_kind: "source_collected",
      confidence: 0.99,
      attention_reason: "",
      uncertainty: "",
      user_action: "系统已自动对应。",
    },
  ],
};

export const renders = {
  input: render(wizardState([])),
  inputWarning: render(wizardState([{ type: "source-dir-change", value: " /data/listings " }])),
  typed: render(wizardState([{ type: "source-dir-change", value: "/data/listings/2026-08" }])),
  creating: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
  ])),
  reading: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
  ])),
  review: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
    { type: "profile-loaded", payload: profilePayload },
  ])),
  confirm: render(readyWizardState(), mappingFrom([
    { type: "load-ready", payload: candidatesPayload() },
  ])),
  documentsMissing: render(
    readyWizardState(),
    createAdmissionMappingConfirmState(),
    null,
    {
      phase: "ready",
      error: null,
      payload: {
        ready: false,
        headline: "还需要 2 份研究文件",
        guidance: "添加后，系统会自动理解表格各列含义；通常不需要您逐列核对。",
        roles: [
          { role: "protocol", label: "当前研究方案", required_now: true, status: "missing", status_text: "尚未添加" },
          { role: "ecrf", label: "当前 eCRF", required_now: true, status: "missing", status_text: "尚未添加" },
          { role: "ib", label: "研究者手册", required_now: false, status: "missing", status_text: "可稍后添加" },
        ],
      },
    },
  ),
  documentsReady: render(
    readyWizardState(),
    mappingFrom([{ type: "load-ready", payload: candidatesPayload() }]),
    null,
    {
      phase: "ready",
      error: null,
      payload: {
        ready: true,
        headline: "研究文件已准备好",
        guidance: "系统正在结合研究方案和 eCRF 理解数据。",
        roles: [
          { role: "protocol", label: "当前研究方案", required_now: true, status: "current", status_text: "已识别" },
          { role: "ecrf", label: "当前 eCRF", required_now: true, status: "current", status_text: "已识别" },
        ],
      },
    },
  ),
  documentsFailed: render(
    readyWizardState(),
    createAdmissionMappingConfirmState(),
    null,
    {
      phase: "failed",
      error: "研究文档核对暂未完成，请重试。",
      payload: {
        ready: false,
        headline: "还需补充研究文件",
        guidance: "已添加的文件会保留。",
        roles: [
          { role: "protocol", label: "当前研究方案", required_now: true, status: "current", status_text: "已识别" },
          { role: "ecrf", label: "当前 eCRF", required_now: true, status: "missing", status_text: "尚未添加" },
        ],
      },
    },
  ),
  confirmDrafting: render(readyWizardState(), mappingFrom([
    { type: "load-ready", payload: candidatesPayload() },
    { type: "adopt-ready", payload: draftPayload },
  ])),
  confirmDraftingAnswered: render(readyWizardState(), mappingFrom([
    { type: "load-ready", payload: candidatesPayload() },
    { type: "adopt-ready", payload: draftPayload },
    {
      type: "answer-ready",
      key: "访视列表::访视日期",
      payload: { ...draftPayload, version: 2 },
    },
  ])),
  confirmNoQuestions: render(readyWizardState(), mappingFrom([
    { type: "load-ready", payload: candidatesPayload({ withQuestions: false }) },
    { type: "adopt-ready", payload: draftPayload },
  ])),
  done: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
    { type: "profile-loaded", payload: profilePayload },
    { type: "advance" },
    { type: "finish" },
  ]), mappingFrom([
    { type: "confirm-ready", payload: { mapping_revision: "rev-1", facts_generated: false } },
  ]), { phase: "generating", payload: null, error: null }),
  doneReady: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
    { type: "profile-loaded", payload: profilePayload },
    { type: "advance" },
    { type: "finish" },
  ]), mappingFrom([
    { type: "confirm-ready", payload: { mapping_revision: "rev-1", facts_generated: false } },
  ]), { phase: "ready", payload: { facts_generated: true }, error: null }),
  failedRetry: render(wizardState([
    {
      type: "error",
      error: {
        status: 422,
        message: "未找到可导入的数据目录。请确认所选数据位置存在且包含数据文件后重试。",
        detail: { code: "admission_source_invalid" },
      },
    },
  ])),
  failedBlocked: render(wizardState([
    {
      type: "error",
      error: {
        status: 409,
        message: "当前为演示项目，不能接入本机数据。请在实际研究项目中使用数据接入。",
        detail: { code: "admission_project_identity_conflict" },
      },
    },
  ])),
};
