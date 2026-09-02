import { renderToStaticMarkup } from "react-dom/server";
import { MedicalMonitoringAdmissionWizardView } from "./MedicalMonitoringAdmissionWizard.jsx";
import {
  admissionWizardReducer,
  createAdmissionWizardState,
} from "./medicalMonitoringAdmissionWizardState.mjs";

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

function render(state) {
  return renderToStaticMarkup(
    <MedicalMonitoringAdmissionWizardView
      state={state}
      onSourceDirChange={() => {}}
      onSourceFilesChange={() => {}}
      onPrimaryAction={() => {}}
      onSecondaryAction={() => {}}
    />,
  );
}

const profilePayload = generatedAdmissionFixture();
const noRolePayload = generatedAdmissionFixture({ withRoles: false });

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
  confirm: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
    { type: "profile-loaded", payload: profilePayload },
    { type: "advance" },
  ])),
  confirmNoPending: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: noRolePayload },
    { type: "profile-loaded", payload: noRolePayload },
    { type: "advance" },
  ])),
  done: render(wizardState([
    { type: "source-dir-change", value: "/data/listings/2026-08" },
    { type: "import-start" },
    { type: "import-created", payload: profilePayload },
    { type: "profile-loaded", payload: profilePayload },
    { type: "advance" },
    { type: "finish" },
  ])),
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
