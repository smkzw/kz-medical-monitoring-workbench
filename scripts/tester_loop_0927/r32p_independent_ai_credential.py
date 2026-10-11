"""independent_ai deepseek档案凭据补录（zhipu摘除的收尾）。

背景：2026-10-09 zhipu-coding-plan摘除时把independent_ai改绑到
independent_ai__deepseek_v4_flash，但该档案在加密凭据仓中无凭据条目
（热运行期间网关按env回退可用，冷启动readiness判configured:False、
missing_capabilities:[independent_ai]、整站blocked）。

动作：用产品自有AiRuntimeSettingsStore给该档案补录DEEPSEEK_API_KEY
（取自共享ai-runtime.env，密钥不落日志）。验证：probe真实往返+readiness ready。
"""
import os, sys
from pathlib import Path
WB = Path("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench")
sys.path.insert(0, str(WB))
from services.api.app.ai_runtime_settings import AiRuntimeSettingsStore

RUNTIME = WB / "runs/tester_loop_iso_20260928/runtime"
TARGET = "independent_ai__deepseek_v4_flash"

def main() -> int:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if len(key) < 10:
        print("FAIL: DEEPSEEK_API_KEY not in env"); return 2
    store = AiRuntimeSettingsStore(RUNTIME / "ai_provider_settings.json")
    prof = store.profile(TARGET)
    print(f"before: {TARGET} rev={prof.revision} provider={prof.provider} model={prof.model} enabled={prof.enabled}")
    store.upsert(prof, api_key=key, activate=False, activate_if_empty=False)
    print("credential upserted (值不落日志)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
