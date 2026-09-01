from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional


MEDICAL_MODULE_LABELS: Mapping[str, str] = {
    "dashboard": "项目总看板",
    "evidence_design": "证据调研与方案设计",
    "eligibility_review": "入排审核",
    "medical_monitoring": "医学监查",
    "data_analysis_tfl": "数据分析与TFL",
    "medical_writing": "医学写作",
    "safety_pv": "安全信号与PV协同",
    "approvals": "审批中心",
}


@dataclass(frozen=True)
class ProjectHeader:
    project_id: str
    project_code: str
    project_name: str
    indication: str
    product_name: str
    study_phase: str
    protocol_id: str
    protocol_version: str
    protocol_date: str
    status: str = "active"

    def public_dict(self) -> Dict[str, str]:
        return {
            "project_id": self.project_id,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "indication": self.indication,
            "product_name": self.product_name,
            "study_phase": self.study_phase,
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "protocol_date": self.protocol_date,
            "status": self.status,
        }


@dataclass(frozen=True)
class ProjectSourceRef:
    source_id: str
    source_role: str
    module_keys: List[str]
    source_kind: str
    public_title: str
    source_scope: str = "real_raw_source"
    boundary_label: str = ""
    current_version: str = ""
    parser_status: str = "not_started"
    notes: List[str] = field(default_factory=list)
    internal_path: Optional[Path] = None

    @property
    def exists(self) -> bool:
        return self.internal_path.exists() if self.internal_path is not None else True

    def public_dict(self) -> Dict[str, object]:
        return {
            "source_id": self.source_id,
            "source_role": self.source_role,
            "module_keys": list(self.module_keys),
            "source_kind": self.source_kind,
            "public_title": self.public_title,
            "source_scope": self.source_scope,
            "boundary_label": self.boundary_label,
            "current_version": self.current_version,
            "parser_status": self.parser_status,
            "availability": "available" if self.exists else "missing",
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ModuleSourceBinding:
    module: str
    label: str
    route_project_id: str
    primary_source_ids: List[str] = field(default_factory=list)
    supplemental_source_ids: List[str] = field(default_factory=list)
    display_batch_label: str = ""
    display_extract_date: str = ""
    ai_task_types: List[str] = field(default_factory=list)
    ai_capabilities: List[str] = field(default_factory=list)
    implementation_status: str = "planned"
    notes: List[str] = field(default_factory=list)

    def public_dict(self) -> Dict[str, object]:
        return {
            "module": self.module,
            "label": self.label,
            "route_project_id": self.route_project_id,
            "primary_source_ids": list(self.primary_source_ids),
            "supplemental_source_ids": list(self.supplemental_source_ids),
            "display_batch": {
                "batch_label": self.display_batch_label,
                "extract_date": self.display_extract_date,
            },
            "ai_task_types": list(self.ai_task_types),
            "ai_capabilities": list(self.ai_capabilities),
            "implementation_status": self.implementation_status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ProjectSourceManifest:
    project_id: str
    aliases: List[str]
    source_mode: str
    header_project: ProjectHeader
    modules: List[ModuleSourceBinding]
    sources: List[ProjectSourceRef]

    def module_binding(self, module: str) -> ModuleSourceBinding:
        for binding in self.modules:
            if binding.module == module:
                return binding
        raise KeyError(f"module not configured for project source manifest: {self.project_id}/{module}")

    def public_dict(self) -> Dict[str, object]:
        return {
            "project_id": self.project_id,
            "aliases": list(self.aliases),
            "source_mode": self.source_mode,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "header_project": self.header_project.public_dict(),
            "modules": [binding.public_dict() for binding in self.modules],
            "route_bindings": {
                binding.module: binding.public_dict()
                for binding in self.modules
            },
            "sources": [source.public_dict() for source in self.sources],
        }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


class ProjectSourceManifestService:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or _project_root()
        self._manifest_builders = {
            "proj_mgk10_sar_demo": self._mgk10_demo_manifest,
            "proj_rux_03_002": self._rux_manifest,
            "d001_raw_intake": self._d001_manifest,
            "proj_d001_raw_intake": self._d001_manifest,
            "my009_uc": self._my009_manifest,
            "my009_uc_raw_intake": self._my009_manifest,
            "my009_uc_monitoring_raw": self._my009_manifest,
        }

    def build_manifest(self, project_id: str) -> ProjectSourceManifest:
        builder = self._manifest_builders.get(project_id)
        if builder is None:
            raise KeyError(project_id)
        return builder()

    def public_manifest(self, project_id: str) -> Dict[str, object]:
        return self.build_manifest(project_id).public_dict()

    def module_binding(self, project_id: str, module: str) -> ModuleSourceBinding:
        return self.build_manifest(project_id).module_binding(module)

    def _binding(
        self,
        module: str,
        route_project_id: str,
        primary: Iterable[str] = (),
        supplemental: Iterable[str] = (),
        display_batch_label: str = "",
        display_extract_date: str = "",
        ai_task_types: Iterable[str] = (),
        ai_capabilities: Iterable[str] = (),
        implementation_status: str = "planned",
        notes: Iterable[str] = (),
    ) -> ModuleSourceBinding:
        return ModuleSourceBinding(
            module=module,
            label=MEDICAL_MODULE_LABELS[module],
            route_project_id=route_project_id,
            primary_source_ids=list(primary),
            supplemental_source_ids=list(supplemental),
            display_batch_label=display_batch_label,
            display_extract_date=display_extract_date,
            ai_task_types=list(ai_task_types),
            ai_capabilities=list(ai_capabilities),
            implementation_status=implementation_status,
            notes=list(notes),
        )

    def _mgk10_demo_manifest(self) -> ProjectSourceManifest:
        project_id = "proj_mgk10_sar_demo"
        sources = [
            ProjectSourceRef(
                source_id="mgk10_demo_repository",
                source_role="demo_repository",
                module_keys=list(MEDICAL_MODULE_LABELS),
                source_kind="demo_json",
                public_title="MG-K10 SAR 工作台演示数据仓",
                source_scope="demo_seed",
                parser_status="parsed",
                internal_path=self.project_root / "demo_data" / "workbench_demo_v0_1.json",
            ),
            ProjectSourceRef(
                source_id="mgk10_legacy_eligibility_adapter",
                source_role="legacy_eligibility_adapter",
                module_keys=["eligibility_review"],
                source_kind="legacy_adapter",
                public_title="MG-K10 SAR 入排审核 legacy adapter",
                source_scope="legacy_workflow",
                parser_status="available",
                notes=["用于演示和对照，不作为其他真实项目的原始资料输入。"],
            ),
        ]
        return ProjectSourceManifest(
            project_id=project_id,
            aliases=[project_id],
            source_mode="demo_and_legacy",
            header_project=ProjectHeader(
                project_id=project_id,
                project_code="MG-K10-SAR-DEMO",
                project_name="MG-K10 SAR 医学经理工作台演示项目",
                indication="季节性过敏性鼻炎",
                product_name="MG-K10",
                study_phase="III",
                protocol_id="MG-K10-SAR-III",
                protocol_version="V2.1",
                protocol_date="2026-06-01",
            ),
            modules=[
                self._binding("dashboard", project_id, ["mgk10_demo_repository"], display_batch_label="原始数据 listing Batch 003", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("evidence_design", project_id, ["mgk10_demo_repository"], display_batch_label="MG-K10 demo evidence pack", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("eligibility_review", project_id, ["mgk10_legacy_eligibility_adapter"], display_batch_label="MG-K10 legacy 入排对照", display_extract_date="2026-06-28", implementation_status="legacy_available"),
                self._binding("medical_monitoring", project_id, ["mgk10_demo_repository"], display_batch_label="原始数据 listing Batch 003", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("data_analysis_tfl", project_id, ["mgk10_demo_repository"], display_batch_label="MG-K10 demo TFL pack", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("medical_writing", project_id, ["mgk10_demo_repository"], display_batch_label="MG-K10 demo writing pack", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("safety_pv", project_id, ["mgk10_demo_repository"], display_batch_label="MG-K10 demo safety pack", display_extract_date="2026-06-28", implementation_status="demo_available"),
                self._binding("approvals", project_id, ["mgk10_demo_repository"], display_batch_label="MG-K10 demo approval queue", display_extract_date="2026-06-28", implementation_status="demo_available"),
            ],
            sources=sources,
        )

    def _rux_manifest(self) -> ProjectSourceManifest:
        project_id = "proj_rux_03_002"
        rux_base = Path("/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD")
        sources = [
            ProjectSourceRef(
                source_id="rux_listing_20250612",
                source_role="monitoring_listing",
                module_keys=["medical_monitoring", "data_analysis_tfl", "safety_pv"],
                source_kind="local_file_excel",
                public_title="RUX-03-002 列表数据集 Excel 2025-06-12",
                current_version="2025-06-12",
                parser_status="parsed_raw_intake",
                internal_path=rux_base / "CFDI Inspection" / "准备阶段" / "RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx",
            ),
            ProjectSourceRef(
                source_id="rux_subject_report_20250613",
                source_role="monitoring_subject_report",
                module_keys=["medical_monitoring"],
                source_kind="local_file_excel",
                public_title="RUX-03-002 受试者报表 2025-06-13",
                current_version="2025-06-13",
                parser_status="queued",
                internal_path=rux_base / "CFDI Inspection" / "准备阶段" / "RUX-03-002_受试者报表_20250613.xls",
            ),
            ProjectSourceRef(
                source_id="rux_protocol_v1_3",
                source_role="protocol_docx",
                module_keys=["medical_monitoring", "data_analysis_tfl", "medical_writing"],
                source_kind="local_file_docx",
                public_title="RUX-03-002 临床研究方案 V1.3",
                current_version="V1.3 / 2024-08-14",
                parser_status="parsed_raw_intake",
                internal_path=(
                    rux_base
                    / "CFDI Inspection"
                    / "RUX-03-002-自查文件包-20260107"
                    / "10-临床试验重要文件"
                    / "1-临床试验方案"
                    / "V1.3版-2024.8.14"
                    / "磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx"
                ),
            ),
            ProjectSourceRef(
                source_id="rux_cm_domain",
                source_role="concomitant_medication_domain",
                module_keys=["medical_monitoring", "safety_pv"],
                source_kind="derived_listing_domain",
                public_title="CM/CM1 非试验用合并用药 domain",
                source_scope="derived_from_monitoring_listing",
                boundary_label="非试验用合并用药",
                parser_status="parsed_raw_intake",
            ),
            ProjectSourceRef(
                source_id="rux_study_drug_change_domain",
                source_role="study_drug_change_domain",
                module_keys=["medical_monitoring"],
                source_kind="derived_listing_domain",
                public_title="ECB/ECA/DA/EX 试验药物给药、暂停、重启、剂量调整 domain",
                source_scope="derived_from_monitoring_listing",
                boundary_label="试验药物变更/剂量调整",
                parser_status="parsed_raw_intake",
            ),
            ProjectSourceRef(
                source_id="rux_sdtm_package",
                source_role="sdtm_package",
                module_keys=["data_analysis_tfl"],
                source_kind="local_directory",
                public_title="RUX-03-002 SDTM package inventory",
                parser_status="inventory_available",
                internal_path=rux_base / "DM&SA" / "国内外共4项研究数据库" / "rux-03-002" / "tabulations" / "sdtm",
            ),
            ProjectSourceRef(
                source_id="rux_final_tfl_package",
                source_role="tfl_output_package",
                module_keys=["data_analysis_tfl", "medical_writing"],
                source_kind="local_directory",
                public_title="RUX-03-002 SAR/TFL 输出包",
                parser_status="inventory_available",
                internal_path=rux_base / "2-RUX-03-002-现场核查项目层面文件目录-20260424" / "38.SAR&TFLs",
            ),
            ProjectSourceRef(
                source_id="rux_pv_plan_package",
                source_role="pv_plan_package",
                module_keys=["safety_pv"],
                source_kind="local_directory",
                public_title="RUX-03-002 PV 计划包",
                parser_status="inventory_available",
                internal_path=rux_base / "2-RUX-03-002-现场核查项目层面文件目录-20260424" / "22.PV计划",
            ),
        ]
        return ProjectSourceManifest(
            project_id=project_id,
            aliases=[project_id, "rux_03_002_monitoring_raw"],
            source_mode="real_project",
            header_project=ProjectHeader(
                project_id=project_id,
                project_code="RUX-03-002",
                project_name="磷酸芦可替尼乳膏 RUX-03-002",
                indication="特应性皮炎",
                product_name="磷酸芦可替尼乳膏",
                study_phase="III",
                protocol_id="RUX-03-002",
                protocol_version="V1.3",
                protocol_date="2024-08-14",
            ),
            modules=[
                self._binding("dashboard", project_id, ["rux_listing_20250612", "rux_protocol_v1_3"], display_batch_label="RUX listing 2025-06-12", display_extract_date="2025-06-12", implementation_status="real_source_slice"),
                self._binding(
                    "medical_monitoring",
                    project_id,
                    ["rux_listing_20250612", "rux_protocol_v1_3"],
                    ["rux_subject_report_20250613", "rux_cm_domain", "rux_study_drug_change_domain"],
                    "RUX listing 2025-06-12",
                    "2025-06-12",
                    ["listing_semantic_mapping", "protocol_rule_extraction", "monitoring_risk_interpretation", "subject_timeline_derivation", "patient_profile_derivation"],
                    ["llm:deepseek-v4-pro", "ocr:glm-ocr-bf16|paddleocr-vl-1.6", "vlm:minimax-m3"],
                    "real_source_slice",
                ),
                self._binding("data_analysis_tfl", project_id, ["rux_sdtm_package", "rux_final_tfl_package"], ["rux_listing_20250612"], "RUX SDTM/TFL 包", "2025-06-12", implementation_status="source_inventory_slice"),
                self._binding("medical_writing", project_id, ["rux_protocol_v1_3", "rux_final_tfl_package"], display_batch_label="RUX 方案 V1.3 + SAR/TFL", display_extract_date="2024-08-14", ai_task_types=["medical_writing_revision"], ai_capabilities=["llm:deepseek-v4-pro"], implementation_status="source_inventory_slice"),
                self._binding("safety_pv", project_id, ["rux_listing_20250612", "rux_pv_plan_package"], ["rux_cm_domain"], "RUX PV/Listing 包", "2025-06-12", implementation_status="source_inventory_slice"),
                self._binding("approvals", project_id, ["rux_listing_20250612"], display_batch_label="RUX 医学处置审批队列", display_extract_date="2025-06-12", implementation_status="real_source_slice"),
            ],
            sources=sources,
        )

    def _d001_manifest(self) -> ProjectSourceManifest:
        project_id = "d001_raw_intake"
        d001_base = Path("/Users/smkzw/Documents/康哲项目资料/AI/入排/test-D001项目")
        sources = [
            ProjectSourceRef(
                source_id="d001_protocol_v1_0",
                source_role="eligibility_protocol_docx",
                module_keys=["eligibility_review", "medical_writing"],
                source_kind="local_file_docx",
                public_title="CMS-D001 银屑病 2/3 期临床方案 V1.0",
                current_version="V1.0 / 2025-12-21",
                parser_status="parsed_raw_intake",
                internal_path=d001_base / "CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx",
            ),
            ProjectSourceRef(
                source_id="d001_raw_subject_bundle",
                source_role="eligibility_raw_subject_bundle",
                module_keys=["eligibility_review"],
                source_kind="local_directory",
                public_title="CMS-D001 全量入组原始资料包",
                parser_status="parsed_raw_intake_pending_ocr_vlm",
                internal_path=d001_base / "全量-入组",
            ),
            ProjectSourceRef(
                source_id="d001_legacy_enrollment_review_app",
                source_role="legacy_eligibility_adapter",
                module_keys=["eligibility_review"],
                source_kind="legacy_app",
                public_title="既有入排审核系统对照结果",
                source_scope="legacy_comparison",
                parser_status="available_for_comparison",
                notes=["只能用于 UI/逻辑对照和迁移验证，不能代替原始方案与原始受试者资料。"],
                internal_path=Path("/Users/smkzw/Documents/康哲项目资料/AI/入排/enrollment-review-app"),
            ),
        ]
        return ProjectSourceManifest(
            project_id=project_id,
            aliases=[project_id, "proj_d001_raw_intake"],
            source_mode="real_project",
            header_project=ProjectHeader(
                project_id=project_id,
                project_code="CMS-D001",
                project_name="CMS-D001 银屑病 2/3 期临床研究",
                indication="银屑病",
                product_name="CMS-D001",
                study_phase="II/III",
                protocol_id="CMS-D001",
                protocol_version="V1.0",
                protocol_date="2025-12-21",
            ),
            modules=[
                self._binding("dashboard", project_id, ["d001_protocol_v1_0"], display_batch_label="D001 方案 V1.0", display_extract_date="2025-12-21", implementation_status="source_manifest_only"),
                self._binding(
                    "eligibility_review",
                    project_id,
                    ["d001_protocol_v1_0", "d001_raw_subject_bundle"],
                    ["d001_legacy_enrollment_review_app"],
                    "D001 全量入组资料",
                    "2025-12-21",
                    ["protocol_rule_extraction", "eligibility_rule_review"],
                    ["llm:deepseek-v4-pro", "ocr:glm-ocr-bf16|paddleocr-vl-1.6", "vlm:minimax-m3"],
                    "real_source_slice",
                ),
                self._binding("medical_writing", project_id, ["d001_protocol_v1_0"], display_batch_label="D001 方案 V1.0", display_extract_date="2025-12-21", ai_task_types=["medical_writing_revision"], ai_capabilities=["llm:deepseek-v4-pro"], implementation_status="source_inventory_slice"),
                self._binding("approvals", project_id, ["d001_protocol_v1_0"], display_batch_label="D001 审批占位", display_extract_date="2025-12-21", implementation_status="planned"),
            ],
            sources=sources,
        )

    def _my009_manifest(self) -> ProjectSourceManifest:
        project_id = "my009_uc"
        my009_base = Path("/Users/smkzw/Documents/朗来项目资料/MY009治疗UC")
        sources = [
            ProjectSourceRef(
                source_id="my009_protocol_v3_0",
                source_role="protocol_docx",
                module_keys=["eligibility_review", "medical_monitoring", "medical_writing"],
                source_kind="local_file_docx",
                public_title="MY009 UC IIa 期临床研究方案 V3.0",
                current_version="V3.0 / 2025-09-26",
                parser_status="parsed_raw_intake",
                internal_path=my009_base / "方案及配套资料" / "3.0" / "MY009-UC-Ⅱa期-临床研究方案-V3.0 20250926-clean (1).docx",
            ),
            ProjectSourceRef(
                source_id="my009_evf_subject_bundle",
                source_role="eligibility_raw_subject_bundle",
                module_keys=["eligibility_review"],
                source_kind="local_directory",
                public_title="MY009 UC EVF 审核原始资料包",
                parser_status="parsed_raw_intake_pending_ocr_vlm",
                internal_path=my009_base / "EVF审核",
            ),
            ProjectSourceRef(
                source_id="my009_mm_listing_20260408",
                source_role="monitoring_listing",
                module_keys=["medical_monitoring", "safety_pv"],
                source_kind="local_file_excel",
                public_title="MY009 UC MM Listing 2026-04-08",
                current_version="2026-04-08",
                parser_status="parsed_raw_intake",
                internal_path=my009_base / "S1安全性评价-202604" / "MY009-UC-2-01-MM Listing_20260408(已自动还原).xlsx",
            ),
            ProjectSourceRef(
                source_id="my009_cm_domain",
                source_role="concomitant_medication_domain",
                module_keys=["medical_monitoring", "safety_pv"],
                source_kind="derived_listing_domain",
                public_title="MY009 CM 非试验用合并用药 domain",
                source_scope="derived_from_monitoring_listing",
                boundary_label="非试验用合并用药",
                parser_status="parsed_raw_intake",
            ),
            ProjectSourceRef(
                source_id="my009_study_drug_change_domain",
                source_role="study_drug_change_domain",
                module_keys=["medical_monitoring"],
                source_kind="derived_listing_domain",
                public_title="MY009 DA/EX 试验药物给药、暂停、重启、剂量调整 domain",
                source_scope="derived_from_monitoring_listing",
                boundary_label="试验药物变更/剂量调整",
                parser_status="parsed_raw_intake",
            ),
            ProjectSourceRef(
                source_id="my009_safety_package_202604",
                source_role="safety_pv_package",
                module_keys=["safety_pv"],
                source_kind="local_directory",
                public_title="MY009 UC S1 安全性评价资料包",
                parser_status="inventory_available",
                internal_path=my009_base / "S1安全性评价-202604",
            ),
            ProjectSourceRef(
                source_id="my009_dsur4_source",
                source_role="dsur_source",
                module_keys=["safety_pv", "medical_writing"],
                source_kind="local_file_docx",
                public_title="MY009 DSUR #4 资料收集包",
                parser_status="inventory_available",
                internal_path=my009_base / "DSUR" / "附件1：MY009_DSUR#4_资料收集 to CPM、RA、医学-MM.docx",
            ),
        ]
        return ProjectSourceManifest(
            project_id=project_id,
            aliases=[project_id, "my009_uc_raw_intake", "my009_uc_monitoring_raw"],
            source_mode="real_project",
            header_project=ProjectHeader(
                project_id=project_id,
                project_code="MY009-UC",
                project_name="MY009 溃疡性结肠炎 IIa 期临床研究",
                indication="溃疡性结肠炎",
                product_name="MY009",
                study_phase="IIa",
                protocol_id="MY009-UC",
                protocol_version="V3.0",
                protocol_date="2025-09-26",
            ),
            modules=[
                self._binding("dashboard", project_id, ["my009_protocol_v3_0", "my009_mm_listing_20260408"], display_batch_label="MY009 MM Listing 2026-04-08", display_extract_date="2026-04-08", implementation_status="source_manifest_only"),
                self._binding(
                    "eligibility_review",
                    "my009_uc_raw_intake",
                    ["my009_protocol_v3_0", "my009_evf_subject_bundle"],
                    (),
                    "MY009 EVF 审核资料",
                    "2025-09-26",
                    ai_task_types=["protocol_rule_extraction", "eligibility_rule_review"],
                    ai_capabilities=["llm:deepseek-v4-pro", "ocr:glm-ocr-bf16|paddleocr-vl-1.6", "vlm:minimax-m3"],
                    implementation_status="real_source_slice",
                ),
                self._binding(
                    "medical_monitoring",
                    "my009_uc_monitoring_raw",
                    ["my009_mm_listing_20260408", "my009_protocol_v3_0"],
                    ["my009_cm_domain", "my009_study_drug_change_domain"],
                    "MY009 MM Listing 2026-04-08",
                    "2026-04-08",
                    ["listing_semantic_mapping", "protocol_rule_extraction", "monitoring_risk_interpretation"],
                    ["llm:deepseek-v4-pro", "ocr:glm-ocr-bf16|paddleocr-vl-1.6", "vlm:minimax-m3"],
                    "real_source_slice",
                ),
                self._binding("medical_writing", project_id, ["my009_protocol_v3_0", "my009_dsur4_source"], display_batch_label="MY009 方案 V3.0 + DSUR", display_extract_date="2025-09-26", ai_task_types=["medical_writing_revision"], ai_capabilities=["llm:deepseek-v4-pro"], implementation_status="source_inventory_slice"),
                self._binding("safety_pv", project_id, ["my009_mm_listing_20260408", "my009_safety_package_202604", "my009_dsur4_source"], ["my009_cm_domain"], "MY009 S1/PV 2026-04", "2026-04-08", implementation_status="source_inventory_slice"),
                self._binding("approvals", project_id, ["my009_protocol_v3_0"], display_batch_label="MY009 审批占位", display_extract_date="2025-09-26", implementation_status="planned"),
            ],
            sources=sources,
        )
