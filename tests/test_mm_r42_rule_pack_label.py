"""R42轮（R42-07）回归：历史运行行携带规则修订版本标注。

R42实测：同一数据、同全量、同项目规则的两次运行（a7cfb1df与f03eca30）
发现构成不同（75 vs 74），而历史行/概览无任何规则版本标注，监查结论
的可重复性无法向QA交代。运行登记表本就持久化每次运行绑定的规则修订
令牌（r7_launch_registry.rule_tokens_json），本回归钉住其公开投影：

1. 未绑定规则修订（record_applicability等）→ 如实留空，不编造；
2. 单修订 → ``rule-revision:<12位短标识>``；
3. 多修订 → 首项短标识 + 修订计数。
"""

from __future__ import annotations

from packages.medical_monitoring.runtime.launch_registry_contracts import (
    LaunchRecord,
)

_RECORD_DEFAULTS = dict(
    sequence=1,
    project_id="proj_rule_label",
    idempotency_key="idem-1",
    run_id="run:rule-label",
    public_run_token="run:public-rule-label",
    request_fingerprint="fp:rule-label",
    mode="daily",
    execution_basis="full",
    current_snapshot_token="snapshot:current",
    baseline_token=None,
    data_cutoff="2026-08-19",
    comparison_range_text="当前完整数据",
    run_state="completed",
    result_available=True,
    main_action="查看本次结果",
    manifest_digest=None,
    created_at="2026-10-14T00:00:00+00:00",
    updated_at="2026-10-14T00:10:00+00:00",
)


def _record(rule_tokens: tuple[str, ...]) -> LaunchRecord:
    return LaunchRecord(rule_tokens=rule_tokens, **_RECORD_DEFAULTS)


def test_rule_pack_text_empty_without_tokens() -> None:
    record = _record(())
    assert record.public_projection()["rule_pack_text"] == ""


def test_rule_pack_text_short_token_for_single_revision() -> None:
    token = "rule-revision:0123456789abcdef0123456789"
    record = _record((token,))
    projection = record.public_projection()
    assert projection["rule_pack_text"] == "rule-revision:0123456789ab"
    # 短标识必须是完整令牌的前缀截断——同规则两次运行的标注逐字一致。
    assert token.startswith(projection["rule_pack_text"])


def test_rule_pack_text_counts_multiple_revisions() -> None:
    record = _record((
        "rule-revision:0123456789abcdef0123456789",
        "rule-revision:fedcba9876543210fedcba9876",
    ))
    assert (
        record.public_projection()["rule_pack_text"]
        == "rule-revision:0123456789ab 等2项规则修订"
    )
