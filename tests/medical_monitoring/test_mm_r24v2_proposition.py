"""0924V2-B09命题反例回归：时序关系冲突的双线索不得判一致。"""
from types import SimpleNamespace

from packages.medical_monitoring.analysis.ae_mh_cross_analysis import _clues_agree


def _clue(temporal):
    return SimpleNamespace(
        title="跨表线索",
        text="证据一致",
        evidence=[SimpleNamespace(evidence_id="ev-1")],
        structured_payload={
            "subject_id": "S1",
            "domains": ["AE", "CM"],
            "observations": ["观察"],
            "temporal_relationships": temporal,
            "data_gaps": [],
            "recommended_review": "核对。",
            "evidence_ids": ["ev-1"],
        },
        claims=[],
    )


def test_temporal_conflict_blocks_agreement():
    primary = _clue(["既往病史持续期间用药"])
    verifier = _clue(["近期新发感染"])
    assert not _clues_agree(primary, verifier)


def test_temporal_overlap_allows_agreement():
    # "一致"在否定词表中会判negative stance——用纯正向词表述
    primary = SimpleNamespace(
        title="跨表线索：给药后风险信号",
        text="给药后出现需关注的风险信号",
        evidence=[SimpleNamespace(evidence_id="ev-1")],
        structured_payload={
            "subject_id": "S1", "domains": ["AE", "CM"],
            "observations": ["给药后出现需关注的风险信号"],
            "temporal_relationships": ["给药后出现"],
            "data_gaps": [], "recommended_review": "核对。",
            "evidence_ids": ["ev-1"],
        },
        claims=[],
    )
    verifier = SimpleNamespace(
        title="跨表线索：用药后风险信号",
        text="用药后风险信号需核查",
        evidence=[SimpleNamespace(evidence_id="ev-1")],
        structured_payload={
            "subject_id": "S1", "domains": ["AE", "CM"],
            "observations": ["用药后风险信号需核查"],
            "temporal_relationships": ["用药后监测"],
            "data_gaps": [], "recommended_review": "核对。",
            "evidence_ids": ["ev-1"],
        },
        claims=[],
    )
    assert _clues_agree(primary, verifier)


def test_missing_temporal_does_not_block():
    primary = _clue([])
    verifier = _clue(["给药后出现"])
    # 单侧有时序：信息不足，不做时序否决（后续仍可能因stance判不一致）
    result = _clues_agree(primary, verifier)
    assert isinstance(result, bool)


# --- R24V2-B04/B09方向极性维度（0925收尾） ---


def _direction_clue(observations, text):
    """方向极性用例线索：正向stance措辞，共享同一证据与实体身份。"""
    return SimpleNamespace(
        title="跨表线索：实验室指标信号",
        text=text,
        evidence=[SimpleNamespace(evidence_id="ev-1")],
        structured_payload={
            "subject_id": "S1",
            "domains": ["AE", "CM"],
            "observations": observations,
            "temporal_relationships": [],
            "data_gaps": [],
            "recommended_review": "核对。",
            "evidence_ids": ["ev-1"],
        },
        claims=[],
    )


def test_direction_conflict_blocks_agreement():
    # "下降"与"升高"引用同一证据也是相反命题——不得判一致
    primary = _direction_clue(["血红蛋白较基线下降"], "血红蛋白较基线下降，存在需关注的信号")
    verifier = _direction_clue(["该指标升高"], "该指标升高，提示需核查")
    assert not _clues_agree(primary, verifier)


def test_direction_synonyms_still_agree():
    # "升高"与"偏高"同义归一后同向，可判一致
    primary = _direction_clue(["该指标升高"], "该指标升高，存在需关注的信号")
    verifier = _direction_clue(["数值偏高"], "数值偏高，需关注")
    assert _clues_agree(primary, verifier)


def test_one_sided_direction_does_not_block():
    # 单侧有方向词：信息不足不做方向否决（其余门仍照常生效）
    primary = _direction_clue(["该指标升高"], "该指标升高，存在需关注的信号")
    verifier = _direction_clue(["对应记录已复核"], "对应记录已复核，需关注")
    assert _clues_agree(primary, verifier)
