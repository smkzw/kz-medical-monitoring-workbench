from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional

from fastapi import FastAPI, HTTPException, Query, Request

from packages.contracts.workbench_contracts import (
    ApprovalAction,
    ApprovalActionRequest,
    DashboardSummary,
    DataBatch,
    AiTaskFromRegistryRequest,
    AiTaskRequest,
    EvidencePicosActionRequest,
    MedicalWritingRevisionRequest,
    ModuleStatus,
    Project,
    MonitoringIntakeRequest,
    RevisionActionRequest,
    RiskStatus,
    RuxRiskDispositionActionRequest,
    SafetyReviewActionRequest,
    TflReviewActionRequest,
    WorkbenchItemActionRequest,
)

from .ai_gateway import ai_gateway_status_from_env
from .ai_task_runner import AiTaskRunner, AiTaskStore
from .demo_repository import DemoRepository
from .evidence_design_manifest import EvidenceDesignManifestService
from .evidence_picos_workflow import EvidencePicosDecisionStore, EvidencePicosWorkflowService
from .eligibility import adapter as eligibility_adapter
from .eligibility import router as eligibility_router
from .listing_file_parser import parse_listing_file
from .medical_writing import MedicalWritingRevisionService
from .medical_writing_manifest import MedicalWritingManifestService
from .monitoring_raw_intake import MonitoringRawProjectConfig, MonitoringRawProjectIntakeService
from .monitoring_intake import MonitoringIntakeService
from .project_source_manifest import ProjectSourceManifestService
from .rux_monitoring_service import RuxMonitoringService
from .safety_pv_manifest import SafetyPvManifestService
from .safety_pv_review_workbench import SafetyReviewStore, SafetyReviewWorkbenchService
from .source_intake import SourceRegistryService, SourceRegistryStore
from .tfl_manifest import TflManifestService
from .tfl_review_workbench import TflReviewStore, TflReviewWorkbenchService
from .tfl_writing_handoff import TflWritingHandoffService
from .workbench_inbox import (
    RUX_P0_SUBJECT_IDS,
    RUX_PROJECT_ID,
    RuxRiskDispositionStore,
    WorkbenchInboxService,
    WorkbenchInboxStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_DATA = PROJECT_ROOT / "demo_data" / "workbench_demo_v0_1.json"
RUX_LISTING_PATH = Path(
    "/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/"
    "RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx"
)
RUX_PROTOCOL_PATH = Path(
    "/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/"
    "10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/"
    "磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx"
)
MY009_MONITORING_LISTING_PATH = Path(
    "/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604/"
    "MY009-UC-2-01-MM Listing_20260408(已自动还原).xlsx"
)
MY009_PROTOCOL_PATH = Path(
    "/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/方案及配套资料/3.0/"
    "MY009-UC-Ⅱa期-临床研究方案-V3.0 20250926-clean (1).docx"
)

app = FastAPI(title="AI Medical Manager Workbench", version="0.1.0")
app.include_router(eligibility_router)
repo = DemoRepository(DEFAULT_DATA)
rux_monitoring_service = RuxMonitoringService(RUX_LISTING_PATH, RUX_PROTOCOL_PATH)
monitoring_intake = MonitoringIntakeService(repo)
monitoring_raw_intake_service = MonitoringRawProjectIntakeService()
MONITORING_RAW_PROJECTS = {
    RUX_PROJECT_ID: MonitoringRawProjectConfig(
        project_id=RUX_PROJECT_ID,
        project_label="RUX-03-002 AD",
        listing_path=RUX_LISTING_PATH,
        protocol_path=RUX_PROTOCOL_PATH,
    ),
    "rux_03_002_monitoring_raw": MonitoringRawProjectConfig(
        project_id="rux_03_002_monitoring_raw",
        project_label="RUX-03-002 AD",
        listing_path=RUX_LISTING_PATH,
        protocol_path=RUX_PROTOCOL_PATH,
    ),
    "my009_uc_monitoring_raw": MonitoringRawProjectConfig(
        project_id="my009_uc_monitoring_raw",
        project_label="MY009 UC",
        listing_path=MY009_MONITORING_LISTING_PATH,
        protocol_path=MY009_PROTOCOL_PATH,
    ),
}
ai_task_runner = AiTaskRunner(repo, AiTaskStore(PROJECT_ROOT / "runtime" / "ai_task_runs.jsonl"))
medical_writing_revision = MedicalWritingRevisionService(repo, ai_task_runner)
medical_writing_manifest_service = MedicalWritingManifestService()
project_source_manifest_service = ProjectSourceManifestService(PROJECT_ROOT)
evidence_design_manifest_service = EvidenceDesignManifestService()
evidence_picos_workflow_service = EvidencePicosWorkflowService(
    evidence_design_manifest_service,
    EvidencePicosDecisionStore(PROJECT_ROOT / "runtime" / "picos_decisions.jsonl"),
)
tfl_manifest_service = TflManifestService()
tfl_review_store = TflReviewStore(PROJECT_ROOT / "runtime" / "tfl_review_actions.jsonl")
tfl_review_workbench_service = TflReviewWorkbenchService(
    tfl_manifest_service,
    tfl_review_store,
)
tfl_writing_handoff_service = TflWritingHandoffService(tfl_manifest_service, tfl_review_store)
safety_pv_manifest_service = SafetyPvManifestService()
safety_review_store = SafetyReviewStore(PROJECT_ROOT / "runtime" / "safety_review_actions.jsonl")
safety_review_workbench_service = SafetyReviewWorkbenchService(safety_pv_manifest_service, safety_review_store)
source_registry = SourceRegistryService(
    SourceRegistryStore(PROJECT_ROOT / "runtime" / "source_registry.jsonl"),
    allowed_roots=[
        path
        for path in [
            PROJECT_ROOT,
            Path("/Users/smkzw/Documents/康哲项目资料"),
            Path("/Users/smkzw/Documents/朗来项目资料"),
            Path("/Users/smkzw/Documents/AI Cache/Codex x Hermes"),
        ]
        if path.exists()
    ],
)


def _rux_dashboard_summary() -> DashboardSummary:
    generated_at = datetime.now(timezone.utc)
    project = Project(
        project_id=RUX_PROJECT_ID,
        project_code="RUX-03-002",
        project_name="磷酸芦可替尼乳膏 RUX-03-002 医学监查项目",
        indication="特应性皮炎",
        product_name="磷酸芦可替尼乳膏",
        study_phase="III",
        protocol_id="RUX-03-002",
        protocol_version="V1.3",
        protocol_date="2024-08-14",
        status="active",
        created_at=datetime(2024, 8, 14, tzinfo=timezone.utc),
        updated_at=generated_at,
    )
    risks = [
        risk
        for subject_id in RUX_P0_SUBJECT_IDS
        for risk in rux_monitoring_service.evaluate_subject_risks(RUX_PROJECT_ID, subject_id)
    ]
    open_risks = [risk for risk in risks if risk.status not in {RiskStatus.CLOSED, RiskStatus.SUPERSEDED}]
    severity_counts = Counter(risk.severity.value for risk in open_risks)
    latest_batch = DataBatch(
        batch_id="rux_03_002_listing_20250612",
        project_id=RUX_PROJECT_ID,
        batch_label="RUX-03-002 原始数据 listing 2025-06-12",
        extract_date="2025-06-12",
        uploaded_by="medical_manager",
        status="real_source_qc_slice",
        source_file_ids=["tfl-rux-listing"],
        row_count=rux_monitoring_service.listing_row_count(),
        subject_count=len(rux_monitoring_service.subject_ids()),
        site_count=len(rux_monitoring_service.site_ids()),
        created_at=datetime(2025, 6, 12, tzinfo=timezone.utc),
    )
    modules = [
        ModuleStatus(
            module="dashboard",
            label="项目总看板",
            status="active_real_source_slice",
            completion_rate=0.2,
            open_risk_count=len(open_risks),
            pending_task_count=len(open_risks),
            pending_approval_count=0,
        ),
        ModuleStatus(
            module="medical_monitoring",
            label="医学监查",
            status="active_real_source_slice",
            completion_rate=0.35,
            open_risk_count=len(open_risks),
            pending_task_count=len(open_risks),
            pending_approval_count=0,
        ),
    ]
    pending_approvals = [
        item
        for item in repo.approvals(RUX_PROJECT_ID)
        if item.state.value in {"ai_draft", "in_medical_review", "returned_for_revision"}
    ]
    modules = [
        module.model_copy(update={"pending_approval_count": len(pending_approvals) if module.module == "medical_monitoring" else module.pending_approval_count})
        for module in modules
    ]
    return DashboardSummary(
        project=project,
        modules=modules,
        latest_batch=latest_batch,
        risk_counts_by_severity=dict(severity_counts),
        pending_approvals=pending_approvals,
        recent_risks=sorted(open_risks, key=lambda item: item.created_at, reverse=True)[:10],
    )

SOURCE_REGISTRY_CANDIDATES: Mapping[str, Mapping[str, object]] = {
    "ev-crs-trial-design": {
        "kind": "local-file",
        "module": "evidence_design",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/00_Master_Database/Trial_Design.csv"),
    },
    "ev-crs-efficacy": {
        "kind": "local-file",
        "module": "evidence_design",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/00_Master_Database/Efficacy_Result.csv"),
    },
    "ev-crs-safety": {
        "kind": "local-file",
        "module": "evidence_design",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/00_Master_Database/Safety_Result.csv"),
    },
    "ev-crs-document-index": {
        "kind": "local-file",
        "module": "evidence_design",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/00_Master_Database/Document_Index.csv"),
    },
    "tfl-rux-listing": {
        "kind": "local-file",
        "module": "data_analysis_tfl",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx"),
    },
    "tfl-rux-sdtm-package": {
        "kind": "local-directory",
        "module": "data_analysis_tfl",
        "source_kind": "tfl_dataset_package_inventory",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/DM&SA/国内外共4项研究数据库/rux-03-002/tabulations/sdtm"),
    },
    "tfl-rux-final-tfl": {
        "kind": "local-directory",
        "module": "data_analysis_tfl",
        "source_kind": "tfl_output_package_inventory",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/38.SAR&TFLs"),
    },
    "pv-my009-mm-listing": {
        "kind": "local-file",
        "module": "safety_pv",
        "path": Path("/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604/MY009-UC-2-01-MM Listing_20260408(已自动还原).xlsx"),
    },
    "pv-my009-safety-package": {
        "kind": "local-directory",
        "module": "safety_pv",
        "source_kind": "safety_signal_package_inventory",
        "path": Path("/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604"),
    },
    "pv-my009-dsur": {
        "kind": "local-file",
        "module": "safety_pv",
        "path": Path("/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/DSUR/附件1：MY009_DSUR#4_资料收集 to CPM、RA、医学-MM.docx"),
    },
    "pv-rux-pv-plan": {
        "kind": "local-directory",
        "module": "safety_pv",
        "source_kind": "pv_safety_package_inventory",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/22.PV计划"),
    },
    "pv-rux-274": {
        "kind": "local-directory",
        "module": "safety_pv",
        "source_kind": "clinical_safety_summary_inventory",
        "path": Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/RA/2.7.4/2-7-4临床安全性总结"),
    },
}
workbench_inbox_service = WorkbenchInboxService(
    repo,
    ai_task_runner,
    evidence_picos_workflow_service,
    tfl_writing_handoff_service,
    safety_review_workbench_service,
    medical_writing_manifest_service,
    source_registry,
    eligibility_adapter,
    WorkbenchInboxStore(PROJECT_ROOT / "runtime" / "workbench_inbox_actions.jsonl"),
    rux_monitoring_service=rux_monitoring_service,
    rux_disposition_store=RuxRiskDispositionStore(PROJECT_ROOT / "runtime" / "rux_risk_disposition_actions.jsonl"),
)


@app.get("/api/health")
def health():
    return {"status": "ok", "data_exists": DEFAULT_DATA.exists()}


@app.get("/api/ai-gateway/status")
def ai_gateway_status():
    return ai_gateway_status_from_env()


@app.get("/api/projects")
def list_projects():
    return [project.model_dump(mode="json") for project in repo.projects()]


@app.get("/api/projects/{project_id}/dashboard")
def get_dashboard(project_id: str):
    if project_id == RUX_PROJECT_ID:
        if not RUX_LISTING_PATH.exists() or not RUX_PROTOCOL_PATH.exists():
            raise HTTPException(status_code=404, detail="RUX source files are not available in the configured local source registry")
        return _rux_dashboard_summary().model_dump(mode="json")
    try:
        return repo.dashboard(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/module-catalog")
def get_module_catalog(project_id: str):
    try:
        return repo.module_catalog(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/source-manifest")
def get_project_source_manifest(project_id: str):
    try:
        return project_source_manifest_service.public_manifest(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project source manifest not found: {project_id}")


@app.get("/api/projects/{project_id}/workbench-inbox")
def get_workbench_inbox(project_id: str, actor: str = Query("medical_manager"), limit: int = Query(80, ge=1, le=200)):
    try:
        return workbench_inbox_service.inbox(project_id, actor=actor, limit=limit).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/monitoring/subjects")
def get_monitoring_subjects(project_id: str):
    if project_id == RUX_PROJECT_ID:
        if not RUX_LISTING_PATH.exists() or not RUX_PROTOCOL_PATH.exists():
            raise HTTPException(status_code=404, detail="RUX source files are not available in the configured local source registry")
        return rux_monitoring_service.subject_catalog(project_id)
    try:
        profiles = repo.subject_monitoring_profiles(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    subjects = [
        {
            "id": profile.subject_id,
            "site": profile.subject.site_id,
            "site_name": "",
            "status": profile.subject.enrollment_status,
            "screening_number": profile.subject.screening_number,
            "profile": " | ".join(
                value
                for value in [
                    f"中心 {profile.subject.site_id}" if profile.subject.site_id else "",
                    profile.subject.screening_number,
                    profile.subject.enrollment_status,
                ]
                if value
            ),
            "source_locator": "demo:subject_monitoring_profiles",
        }
        for profile in profiles
    ]
    return {
        "project_id": project_id,
        "source_batch_id": "demo_subject_monitoring_profiles",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject_count": len(subjects),
        "subjects": subjects,
    }


@app.get("/api/projects/{project_id}/monitoring/raw-intake")
def get_monitoring_raw_intake(project_id: str):
    config = MONITORING_RAW_PROJECTS.get(project_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"raw monitoring project not configured: {project_id}")
    try:
        return monitoring_raw_intake_service.discover_project(config).public_dict()
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/projects/{project_id}/workbench-inbox/{item_id}/actions")
def apply_workbench_inbox_action(project_id: str, item_id: str, request: WorkbenchItemActionRequest):
    try:
        return workbench_inbox_service.apply_action(project_id, item_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"workbench item not found: {project_id}/{item_id}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/workbench-inbox/{item_id}/rux-risk-disposition")
def apply_rux_risk_disposition(project_id: str, item_id: str, request: RuxRiskDispositionActionRequest):
    try:
        return workbench_inbox_service.apply_rux_risk_disposition(project_id, item_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"RUX risk item not found: {project_id}/{item_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/api/projects/{project_id}/ai-runs")
def submit_ai_run(project_id: str, request: AiTaskRequest):
    try:
        return ai_task_runner.submit(project_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/ai-runs/from-sources")
def submit_ai_run_from_registered_sources(project_id: str, request: AiTaskFromRegistryRequest):
    try:
        ai_request = source_registry.ai_task_request_from_registry(project_id, request)
        return ai_task_runner.submit(project_id, ai_request).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _public_source_span(span):
    payload = span.model_dump(mode="json", exclude={"preview_hash"})
    text_preview = payload.get("text_preview") or ""
    if len(text_preview) > 600:
        payload["text_preview"] = text_preview[:600] + "...[truncated]"
    return payload


def _public_source_entry(entry):
    return entry.model_dump(mode="json", exclude={"content_hash", "storage_key", "server_path"})


def _public_source_registration(result):
    return {
        "entry": _public_source_entry(result.entry),
        "spans": [_public_source_span(span) for span in result.spans],
    }


@app.get("/api/projects/{project_id}/ai-runs")
def list_ai_runs(project_id: str):
    try:
        return [run.model_dump(mode="json") for run in ai_task_runner.list_runs(project_id)]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/ai-runs/{run_id}")
def get_ai_run(project_id: str, run_id: str):
    try:
        return ai_task_runner.get(project_id, run_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"AI run not found: {project_id}/{run_id}")


@app.get("/api/projects/{project_id}/ai-runs/{run_id}/artifacts")
def get_ai_run_artifacts(project_id: str, run_id: str):
    try:
        return [artifact.model_dump(mode="json") for artifact in ai_task_runner.artifacts(project_id, run_id)]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"AI run not found: {project_id}/{run_id}")


@app.get("/api/projects/{project_id}/sources")
def list_registered_sources(project_id: str):
    try:
        repo.project(project_id)
        return {
            "entries": [_public_source_entry(entry) for entry in source_registry.list_entries(project_id)],
            "spans": [_public_source_span(span) for span in source_registry.list_spans(project_id)],
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.post("/api/projects/{project_id}/sources/protocol-docx")
async def register_protocol_docx_source(
    project_id: str,
    request: Request,
    filename: str = Query(...),
    module: str = Query("eligibility_review"),
):
    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="protocol docx file is empty")
    try:
        repo.project(project_id)
        return _public_source_registration(source_registry.register_protocol_docx(project_id, filename, content, module=module))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/sources/listing-file")
async def register_listing_file_source(
    project_id: str,
    request: Request,
    filename: str = Query(...),
    module: str = Query("medical_monitoring"),
):
    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="listing file is empty")
    try:
        repo.project(project_id)
        return _public_source_registration(source_registry.register_listing_file(project_id, filename, content, module=module))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/sources/raw-subject-bundle")
def register_raw_subject_bundle_source(
    project_id: str,
    root_path: str = Query(...),
    module: str = Query("eligibility_review"),
):
    try:
        repo.project(project_id)
        return _public_source_registration(source_registry.register_raw_subject_bundle(project_id, root_path, module=module))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/sources/local-file")
def register_local_file_source(
    project_id: str,
    file_path: str = Query(...),
    module: str = Query(...),
):
    try:
        repo.project(project_id)
        return _public_source_registration(source_registry.register_local_file(project_id, file_path, module=module))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/sources/local-directory")
def register_local_directory_source(
    project_id: str,
    root_path: str = Query(...),
    module: str = Query(...),
    source_kind: str = Query("file_bundle_inventory"),
):
    try:
        repo.project(project_id)
        return _public_source_registration(source_registry.register_local_directory(
            project_id,
            root_path,
            module=module,
            source_kind=source_kind,
        ))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/projects/{project_id}/sources/local-candidate")
def register_local_candidate_source(
    project_id: str,
    candidate_id: str = Query(...),
    module: str = Query(...),
):
    try:
        repo.project(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")

    candidate = SOURCE_REGISTRY_CANDIDATES.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"source candidate not found: {candidate_id}")

    try:
        expected_module = str(candidate["module"])
        if module != expected_module:
            raise ValueError(f"source candidate {candidate_id} does not belong to module {module}")
        candidate_path = candidate["path"]
        if candidate["kind"] == "local-file":
            return _public_source_registration(source_registry.register_local_file(project_id, candidate_path, module=expected_module))
        return _public_source_registration(source_registry.register_local_directory(
            project_id,
            candidate_path,
            module=expected_module,
            source_kind=str(candidate.get("source_kind") or "file_bundle_inventory"),
        ))
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/projects/{project_id}/risks")
def get_risks(project_id: str):
    return [risk.model_dump(mode="json") for risk in repo.risks(project_id)]


@app.get("/api/projects/{project_id}/data-batches")
def get_data_batches(project_id: str):
    return [batch.model_dump(mode="json") for batch in repo.batches(project_id)]


@app.get("/api/projects/{project_id}/evidence-design/manifest")
def get_evidence_design_manifest(project_id: str):
    try:
        repo.project(project_id)
        return evidence_design_manifest_service.build_manifest(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/evidence-design/picos-workflow")
def get_evidence_picos_workflow(project_id: str, package_id: Optional[str] = Query(None)):
    try:
        repo.project(project_id)
        return evidence_picos_workflow_service.workflow(project_id, package_id=package_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project or evidence package not found: {project_id}")


@app.post("/api/projects/{project_id}/evidence-design/picos-workflow/{package_id}/questions/{question_id}/actions")
def apply_evidence_picos_action(
    project_id: str,
    package_id: str,
    question_id: str,
    request: EvidencePicosActionRequest,
):
    try:
        repo.project(project_id)
        return evidence_picos_workflow_service.apply_action(project_id, package_id, question_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project, evidence package, or PICOS question not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/api/projects/{project_id}/medical-writing/manifest")
def get_medical_writing_manifest(project_id: str):
    try:
        repo.project(project_id)
        return medical_writing_manifest_service.build_manifest(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/medical-writing/tfl-citation-candidates")
def get_medical_writing_tfl_citation_candidates(project_id: str):
    try:
        repo.project(project_id)
        return tfl_writing_handoff_service.citation_manifest(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/tfl/manifest")
def get_tfl_manifest(project_id: str, force_refresh: bool = Query(False)):
    try:
        repo.project(project_id)
        return tfl_manifest_service.build_manifest(project_id, force_refresh=force_refresh).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/tfl/review-workbench")
def get_tfl_review_workbench(
    project_id: str,
    package_id: Optional[str] = Query(None),
    output_id: Optional[str] = Query(None),
):
    try:
        repo.project(project_id)
        return tfl_review_workbench_service.workbench(project_id, package_id=package_id, output_id=output_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project or TFL output not found: {project_id}")


@app.post("/api/projects/{project_id}/tfl/review-workbench/{package_id}/outputs/{output_id}/actions")
def apply_tfl_review_action(
    project_id: str,
    package_id: str,
    output_id: str,
    request: TflReviewActionRequest,
):
    try:
        repo.project(project_id)
        return tfl_review_workbench_service.apply_action(project_id, package_id, output_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project, TFL package, or TFL output not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/api/projects/{project_id}/safety-pv/manifest")
def get_safety_pv_manifest(project_id: str):
    try:
        repo.project(project_id)
        return safety_pv_manifest_service.build_manifest(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/safety-pv/review-workbench")
def get_safety_review_workbench(
    project_id: str,
    package_id: Optional[str] = Query(None),
    signal_id: Optional[str] = Query(None),
):
    try:
        repo.project(project_id)
        return safety_review_workbench_service.workbench(project_id, package_id=package_id, signal_id=signal_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project, safety package, or safety signal not found: {project_id}")


@app.post("/api/projects/{project_id}/safety-pv/review-workbench/{package_id}/signals/{signal_id}/actions")
def apply_safety_review_action(
    project_id: str,
    package_id: str,
    signal_id: str,
    request: SafetyReviewActionRequest,
):
    try:
        repo.project(project_id)
        return safety_review_workbench_service.apply_action(project_id, package_id, signal_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project, safety package, or safety signal not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/api/projects/{project_id}/safety-pv/handoff-candidates")
def get_safety_pv_handoff_candidates(project_id: str):
    try:
        repo.project(project_id)
        return safety_review_workbench_service.handoff_candidates(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.get("/api/projects/{project_id}/protocol")
def get_protocol(project_id: str):
    try:
        return repo.protocol(project_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"protocol not found for project: {project_id}")


@app.get("/api/projects/{project_id}/revision-threads")
def get_revision_threads(project_id: str):
    try:
        repo.project(project_id)
        return [thread.model_dump(mode="json") for thread in repo.revision_threads(project_id)]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.post("/api/projects/{project_id}/revision-threads")
def submit_revision_thread(project_id: str, request: MedicalWritingRevisionRequest):
    try:
        return medical_writing_revision.submit_revision(project_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project, document, or section not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/api/projects/{project_id}/revision-threads/{thread_id}/actions")
def apply_revision_action(project_id: str, thread_id: str, request: RevisionActionRequest):
    try:
        return medical_writing_revision.apply_action(project_id, thread_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"revision thread or suggestion not found: {project_id}/{thread_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/api/projects/{project_id}/approvals/{approval_id}/actions")
def apply_approval_action(project_id: str, approval_id: str, request: ApprovalActionRequest):
    try:
        result = repo.record_approval_action(project_id, approval_id, request)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"approval not found: {project_id}/{approval_id}")
    if request.action == ApprovalAction.APPROVE and result.decision.blocked:
        raise HTTPException(status_code=409, detail=result.model_dump(mode="json"))
    return result.model_dump(mode="json")


@app.get("/api/projects/{project_id}/subjects/{subject_id}/monitoring")
def get_subject_monitoring(project_id: str, subject_id: str):
    if project_id == "proj_rux_03_002":
        if not RUX_LISTING_PATH.exists() or not RUX_PROTOCOL_PATH.exists():
            raise HTTPException(status_code=404, detail="RUX source files are not available in the configured local source registry")
        return rux_monitoring_service.subject_monitoring(project_id, subject_id).model_dump(mode="json")
    try:
        return repo.subject_monitoring(project_id, subject_id).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"subject monitoring not found: {project_id}/{subject_id}")


@app.post("/api/projects/{project_id}/monitoring/intake")
def submit_monitoring_intake(project_id: str, request: MonitoringIntakeRequest):
    try:
        return monitoring_intake.submit(project_id, request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")


@app.post("/api/projects/{project_id}/monitoring/intake/file")
async def submit_monitoring_intake_file(
    project_id: str,
    request: Request,
    filename: str = Query(...),
    extract_date: str = Query(...),
    batch_label: str = Query("原始数据 listing Batch 004"),
    previous_batch_id: Optional[str] = Query(None),
    uploaded_by: str = Query("medical_manager"),
    confirm_aesi_flag: bool = Query(False),
):
    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="uploaded listing file is empty")
    try:
        sheets = parse_listing_file(filename, content)
        intake_request = MonitoringIntakeRequest(
            batch_label=batch_label,
            extract_date=extract_date,
            previous_batch_id=previous_batch_id,
            uploaded_by=uploaded_by,
            mapping_confirmations={"AESI_FLAG": "safety_interest_flag"} if confirm_aesi_flag else {},
            sheets=sheets,
        )
        return monitoring_intake.submit(project_id, intake_request).model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"project not found: {project_id}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/projects/{project_id}/monitoring/intake/{session_id}")
def get_monitoring_intake(project_id: str, session_id: str):
    try:
        result = monitoring_intake.session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"monitoring intake session not found: {session_id}")
    if result.project_id != project_id:
        raise HTTPException(status_code=404, detail=f"monitoring intake session not found: {project_id}/{session_id}")
    return result.model_dump(mode="json")
