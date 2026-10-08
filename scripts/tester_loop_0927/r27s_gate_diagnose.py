"""R27 攻坚诊断：在沙箱里逐步执行 _r7_protocol_version_gate 的自愈逻辑，
钉住 409 protocol_version_required 的静默失败点（main.py 的 gate 用
except Exception: pass 吞异常，这里逐步打印 traceback）。

只读 live runtime 的 source_registry.jsonl / source_content_validations.sqlite3；
register 写入的是 monitoring_protocol_rules.sqlite3 的临时拷贝，不碰 live。
"""
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

WORKBENCH = Path("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench")
RT = WORKBENCH / "runs/tester_loop_iso_20260928/runtime"
PROJECT = "proj_user_6ef58ac151e1"
ENTRY = "src_proj_user_6ef58ac151e1_protocol_docx_b6e1bceb269c"

sys.path.insert(0, str(WORKBENCH))

from services.api.app.source_content_validation import (  # noqa: E402
    SourceContentValidationService,
    SourceContentValidationStore,
)
from services.api.app.source_intake import (  # noqa: E402
    SourceRegistryService,
    SourceRegistryStore,
)
from services.api.app.monitoring_protocol_rule_repository import (  # noqa: E402
    MonitoringProtocolRuleRepository,
)
from services.api.app.monitoring_rule_authoring_service import (  # noqa: E402
    MonitoringRuleAuthoringService,
)

# 1) 复刻 main.py:971-972 的 content validation service
validation_service = SourceContentValidationService(
    SourceContentValidationStore(RT / "source_content_validations.sqlite3")
)

# 2) 复刻 main.py:1068-1082 的 source registry（只读用途）
registry = SourceRegistryService(
    SourceRegistryStore(RT / "source_registry.jsonl"),
    allowed_roots=[
        WORKBENCH.parent,
        Path("/Users/smkzw/Documents/康哲项目资料"),
    ],
    artifact_root=RT / "source_artifacts",
    content_validation_service=validation_service,
)

# 3) 沙箱化 protocol rules 库（register 写拷贝，不碰 live）
sandbox = Path(tempfile.mkdtemp(prefix="r27s_gate_"))
for suffix in ("", "-wal", "-shm"):
    src = RT / f"monitoring_protocol_rules.sqlite3{suffix}"
    if src.exists():
        shutil.copy2(src, sandbox / f"monitoring_protocol_rules.sqlite3{suffix}")
repo = MonitoringProtocolRuleRepository(sandbox / "monitoring_protocol_rules.sqlite3")


class _Stub:
    def __getattr__(self, name):
        raise RuntimeError(f"stub.{name} should not be called in this path")


authoring = MonitoringRuleAuthoringService(
    repository=repo,
    lifecycle_service=_Stub(),
    protocol_rule_service=_Stub(),
    ai_repository=_Stub(),
    source_registry=registry,
)

# ===== gate 逐步复刻（services/api/app/main.py:1204-1266） =====
print("== step1: source_registry.list_entries 过滤")
try:
    entries = [
        item
        for item in registry.list_entries(PROJECT)
        if item.module == "medical_monitoring"
        and item.source_kind == "protocol_docx"
        and item.parser_status == "parsed"
    ]
    print(f"   entries={[(e.entry_id, e.source_kind, e.parser_status) for e in entries]}")
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("== step2: current_content_validation")
try:
    latest = max(entries, key=lambda item: item.entry_id)
    validation = registry.current_content_validation(PROJECT, latest.entry_id)
    print(f"   validation={validation}")
    ok = (
        validation is not None
        and validation.technical_status == "ready"
        and validation.use_status in {"allowed", "confirmed_after_warning"}
    )
    print(f"   self-heal precondition ok={ok}")
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("== step3: authoring.register_protocol_version（写沙箱库）")
try:
    version, reused = authoring.register_protocol_version(
        project_id=PROJECT,
        source_entry_id=latest.entry_id,
        protocol_code=str(latest.entry_id)[:80],
        version_label=str(latest.public_title or latest.entry_id)[:200],
        version_date=str(getattr(latest, "registered_at", "") or "")[:10]
        or "1970-01-01",
        applicability_status="active",
        operational_effective_from=str(
            getattr(latest, "registered_at", "") or ""
        )[:10]
        or "1970-01-01",
    )
    print(f"   OK version_id={version.protocol_version_id} reused={reused} "
          f"status={version.status}")
except Exception:
    print("   *** register RAISED: ***")
    traceback.print_exc()
    sys.exit(2)

print("== 全链自愈逻辑在沙箱复刻下无异常——gate 静默失败另有其因（进程内状态差异）")
