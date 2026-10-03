"""R13D 主侧AI路由界内换绑（R12D 同款先例，host 代理故障的隔离实例侧规避）。

背景：R13 重启重建隔离运行时（347M 快照）后，两个主侧角色档案的 base_url
回到本机 omniroute LB 127.0.0.1:20128；LB 上游 Clash Verge 代理 127.0.0.1:7897
不可达（产品 probe 实证 [Proxy Fast-Fail] HTTP 503），主侧作业会连续快速失败。

动作（与 R12D 完全同界）：
  - 用产品自有 AiRuntimeSettingsStore（经隔离 runtime 目录，非 API 亦非直改
    运行库）把两个主侧角色档案 base_url 改为智谱官方直连，extra_headers 清空，
    存储凭据改用隔离实例自有 zhipu coding-plan 直连密钥（取自同库
    independent_ai 档案，密钥不落任何日志/输出）；
  - provider 身份串（cms-router）、模型（glm-5.3-flash）、推理档（high）、
    prompt 版本、全部质量门保持不变；
  - 改前四件配置已备份至 scripts/tester_loop_0927/r13d_provider_config_backup/。

验证：改后用产品 /api/ai-gateway/probe 对两档案各做一次真实往返。
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

WB = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench"
)
sys.path.insert(0, str(WB))

from services.api.app.ai_runtime_settings import (  # noqa: E402
    AiRuntimeSettingsStore,
)

RUNTIME = WB / "runs" / "tester_loop_iso_20260928" / "runtime"
DIRECT_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"
KEY_DONOR = "independent_ai__zhipu_coding_plan_glm_flash"
TARGETS = [
    "medical_monitoring_ai__cms_router_glm53flash",
    "document_authority_primary_ai__medical_monitoring_ai__cms_router_glm53flash",
]


def main() -> int:
    store = AiRuntimeSettingsStore(RUNTIME / "ai_provider_settings.json")
    donor_key = store.credentials.get(KEY_DONOR)
    if not donor_key:
        print("FAIL: donor credential missing")
        return 2
    for pid in TARGETS:
        prof = store.profile(pid)
        print(
            f"before: {pid} rev={prof.revision} base_url={prof.base_url} "
            f"model={prof.model} provider={prof.provider}"
        )
        updated = replace(
            prof,
            base_url=DIRECT_BASE_URL,
            extra_headers_json="",
        )
        store.upsert(updated, api_key=donor_key, activate=False,
                     activate_if_empty=False)
        now = store.profile(pid)
        print(
            f"after:  {pid} rev={now.revision} base_url={now.base_url} "
            f"model={now.model} provider={now.provider} "
            f"extra_headers_json_set={bool(now.extra_headers_json)}"
        )
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
