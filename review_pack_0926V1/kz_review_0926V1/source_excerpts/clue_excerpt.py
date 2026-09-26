"""Selected decision logic from ae_mh_cross_analysis.py at 872a4514.
Not the complete production module; source is tool turn287file0.
"""
import re
from typing import Any, Mapping


def _clue_fingerprint(candidate):
    return frozenset(item.evidence_id for item in getattr(candidate, "evidence", ()))

_ENTITY_RE = re.compile(r"[\u4e00-\u9fa5]{2,8}|[A-Za-z][A-Za-z0-9-]{2,14}")

def _clue_entities(candidate):
    payload = getattr(candidate, "structured_payload", {}) or {}
    parts = [str(getattr(candidate,"title","") or ""),str(getattr(candidate,"text","") or "")]
    for claim in payload.get("claims", []) or []:
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    words = set()
    for part in parts:
        words.update(_ENTITY_RE.findall(part[:1200]))
    return frozenset(words)

def _clue_domain_pair(candidate):
    payload = getattr(candidate, "structured_payload", {}) or {}
    return frozenset(str(d).upper() for d in payload.get("domains", []) or [])

_POSITIVE_DIRECTION_RE = re.compile(r"存在|有|记录了|提示|不一致|矛盾|漏报|缺如|异常|升高|降低|超出|超出正常|需核查|需关注|值得关注|风险信号")
_NEGATIVE_DIRECTION_RE = re.compile(r"未见|未记录|未提及|无异常|正常|一致|相符|不存在|无明显|未见明显|未见异常|无特殊|排除")

def _clue_direction_text(candidate):
    payload = getattr(candidate, "structured_payload", {}) or {}
    parts = [str(getattr(candidate, "title", "") or ""),str(getattr(candidate, "text", "") or "")]
    for claim in payload.get("claims", []) or []:
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    return " ".join(parts)

def _clue_stance(candidate):
    text = _clue_direction_text(candidate)
    if not text:
        return "neutral"
    pos_hits = len(_POSITIVE_DIRECTION_RE.findall(text))
    neg_hits = len(_NEGATIVE_DIRECTION_RE.findall(text))
    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"

_TEMPORAL_TOKEN_RE = re.compile(r"(给药前|给药后|用药前|用药后|治疗前|治疗后|既往|近期|新发|持续|一过性)")
_TEMPORAL_CANONICAL = {"给药前":"pre_administration", "用药前":"pre_administration", "治疗前":"pre_administration", "给药后":"post_administration", "用药后":"post_administration", "治疗后":"post_administration"}
_DIRECTION_TOKEN_RE = re.compile(r"(升高|上升|增高|增多|偏高|高于正常|超出正常|降低|下降|减低|减少|偏低|低于正常|转阳性|转阴性)")
_DIRECTION_CANONICAL = {"升高":"elevated", "上升":"elevated", "增高":"elevated", "增多":"elevated", "偏高":"elevated", "高于正常":"elevated", "超出正常":"elevated", "降低":"decreased", "下降":"decreased", "减低":"decreased", "减少":"decreased", "偏低":"decreased", "低于正常":"decreased", "转阳性":"turned_positive", "转阴性":"turned_negative"}

def _direction_set(candidate):
    payload = getattr(candidate,"structured_payload",{}) or {}
    parts = [str(getattr(candidate,"title","") or ""),str(getattr(candidate,"text","") or "")]
    observations=payload.get("observations")
    if isinstance(observations,(list,tuple)):
        parts.extend(str(item) for item in observations)
    claims=payload.get("claims")
    if isinstance(claims,(list,tuple)):
        for claim in claims:
            parts.append(str(claim.get("text","")) if isinstance(claim,Mapping) else str(claim))
    return frozenset(_DIRECTION_CANONICAL.get(token,token) for token in _DIRECTION_TOKEN_RE.findall(" ".join(parts)))

_GRADE_RE = re.compile(r"(?:^|[^0-9])([1-5])\s*级|grade\s*([1-5])", re.IGNORECASE)

def _grade_terms(candidate):
    text=_clue_direction_text(candidate)
    if not text:
        return set()
    grades=set()
    for first,second in _GRADE_RE.findall(text):
        grades.add(first or second)
    return grades

def _clues_agree(primary,verifier):
    shared_evidence=_clue_fingerprint(primary)&_clue_fingerprint(verifier)
    domains=_clue_domain_pair(primary)&_clue_domain_pair(verifier)
    shared_entities=_clue_entities(primary)&_clue_entities(verifier)
    has_evidence_overlap=bool(shared_evidence)
    has_entity_match=bool(domains) and len(shared_entities)>=2
    if not has_evidence_overlap and not has_entity_match:
        return False
    primary_stance=_clue_stance(primary)
    verifier_stance=_clue_stance(verifier)
    if primary_stance!="positive" or verifier_stance!="positive":
        return False
    primary_grades=_grade_terms(primary)
    verifier_grades=_grade_terms(verifier)
    if primary_grades and verifier_grades and not(primary_grades&verifier_grades):
        return False
    def _temporal_set(candidate):
        payload=getattr(candidate,"structured_payload",{}) or {}
        rels=payload.get("temporal_relationships") or []
        if not isinstance(rels,(list,tuple)):
            return frozenset()
        return frozenset(_TEMPORAL_CANONICAL.get(token,token) for rel in rels for token in _TEMPORAL_TOKEN_RE.findall(str(rel)))
    primary_temporal=_temporal_set(primary)
    verifier_temporal=_temporal_set(verifier)
    if primary_temporal and verifier_temporal and not(primary_temporal&verifier_temporal):
        return False
    primary_direction=_direction_set(primary)
    verifier_direction=_direction_set(verifier)
    if primary_direction and verifier_direction and not(primary_direction&verifier_direction):
        return False
    return True
