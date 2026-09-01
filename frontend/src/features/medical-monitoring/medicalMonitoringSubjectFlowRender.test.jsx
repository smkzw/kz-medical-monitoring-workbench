import { renderToStaticMarkup } from "react-dom/server";
import {
  normalizeSubjectFlowView,
  SubjectFlowSection,
  subjectFlowSelectionFromRoute,
  selectSubjectFlowRows,
} from "./MedicalMonitoringWorkspace.jsx";
import {
  R5_SYNTHETIC_SUBJECT_FLOW,
  R5_SYNTHETIC_SUBJECT_FLOW_BLOCKED,
  R5_SYNTHETIC_SUBJECT_FLOW_EMPTY,
  R5_SYNTHETIC_SUBJECT_FLOW_NOT_PROVIDED,
} from "./medicalMonitoringProductFixtures.mjs";

function flowProjection(subjectFlow) {
  return subjectFlow === undefined ? {} : { subject_flow: subjectFlow };
}

function normalizedFlowProjection(subjectFlow) {
  return {
    subjectFlow: {
      ...subjectFlow,
      stages: subjectFlow.stages.map((stage) => ({
        stageRef: stage.stage_ref,
        stageLabelZh: stage.stage_label_zh || stage.stage_label,
        columnOrder: stage.column_order,
        rowOrder: stage.row_order,
        stageKind: stage.stage_kind,
        isEntry: stage.is_entry,
        isTerminal: stage.is_terminal,
        reachedCount: stage.reached_count,
        currentCount: stage.current_count,
        currentMidHighRiskCount: stage.mid_high_risk_count,
      })),
      links: subjectFlow.links.map((link) => ({
        linkRef: link.link_ref,
        fromStageRef: link.from_stage_ref,
        toStageRef: link.to_stage_ref,
        count: link.count,
        currentMidHighRiskCount: link.mid_high_risk_count,
      })),
      subjects: subjectFlow.subjects.map((subject) => ({
        subjectRef: subject.subject_ref,
        subjectLabel: subject.subject_label,
        siteRef: subject.site_ref,
        siteLabel: subject.site_label,
        spineRef: subject.spine_ref,
        currentStageRef: subject.current_stage_ref,
        priorStageRef: subject.prior_stage_ref,
        pathStageRefs: subject.path_stage_refs,
        pathLinkRefs: subject.path_link_refs,
        enteredDate: subject.entered_date,
        basisDate: subject.basis_date,
        dateState: subject.date_state,
        transitionReasonZh: subject.transition_reason_zh,
        stageChangeKind: subject.stage_change_kind,
        riskChangeKind: subject.risk_change_kind,
        riskSummaryZh: subject.risk_summary_zh,
        currentMidHighRisk: subject.mid_high_risk,
        pathState: subject.path_state,
        jumpWindowStart: subject.jump_window_start,
        jumpWindowEnd: subject.jump_window_end,
      })),
    },
  };
}

function renderFlow(subjectFlow, routeOverrides = {}, sectionOverrides = {}) {
  const flow = normalizeSubjectFlowView(flowProjection(subjectFlow));
  const selection = subjectFlowSelectionFromRoute(routeOverrides);
  return renderToStaticMarkup(
    <SubjectFlowSection
      flow={flow}
      selection={selection}
      onStageSelect={() => {}}
      onLinkSelect={() => {}}
      onMetricSelect={() => {}}
      onRiskToggle={() => {}}
      onClear={() => {}}
      onSubjectJump={() => {}}
      {...sectionOverrides}
    />,
  );
}

function countOccurrences(html, marker) {
  return html.split(marker).length - 1;
}

export const renders = {
  ready: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW),
  readyTableOpen: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, {}, { initialTableOpen: true }),
  currentTreatment: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, { flow_stage_ref: "flow-stage-treatment", flow_node_metric: "current" }, { initialTableOpen: true }),
  reachedScreening: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, { flow_stage_ref: "flow-stage-screening", flow_node_metric: "reached" }, { initialTableOpen: true }),
  linkCompleted: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, { flow_link_ref: "flow-link-05" }, { initialTableOpen: true }),
  riskBandWithStage: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, { flow_stage_ref: "flow-stage-treatment", flow_node_metric: "current", flow_risk_band: "mid_high" }, { initialTableOpen: true }),
  riskBandAlone: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW, { flow_risk_band: "mid_high" }, { initialTableOpen: true }),
  notProvided: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW_NOT_PROVIDED),
  legacyAbsent: renderFlow(undefined),
  blocked: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW_BLOCKED),
  empty: renderFlow(R5_SYNTHETIC_SUBJECT_FLOW_EMPTY),
};

export const selectors = {
  ready: normalizeSubjectFlowView(flowProjection(R5_SYNTHETIC_SUBJECT_FLOW)),
  selection: subjectFlowSelectionFromRoute({ flow_stage_ref: "flow-stage-treatment", flow_node_metric: "current", flow_risk_band: "mid_high" }),
  linkSelection: subjectFlowSelectionFromRoute({ flow_link_ref: "flow-link-02" }),
  flow: R5_SYNTHETIC_SUBJECT_FLOW,
  normalizedReady: normalizeSubjectFlowView(normalizedFlowProjection(R5_SYNTHETIC_SUBJECT_FLOW)),
  selectRows: (flowView, selection) => selectSubjectFlowRows(flowView, selection),
};
