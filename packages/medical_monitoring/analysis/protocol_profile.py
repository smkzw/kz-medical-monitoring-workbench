"""Generic protocol/IB structured profile for the anti-overfit analysis lane.

Extracts a content-addressed profile from the project's registered study
documents (protocol, IB): CTCAE grading version, AE grading policy anchors,
indication/drug-class hints and their expected risk directions. The profile
is project-agnostic — everything is derived from document text with pattern
rules, never from a hard-coded drug or protocol.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from ..intelligence.primitives import content_hash

_CTCAE_PATTERNS = (
    re.compile(r"CTCAE\s*(?:版本|version)?\s*[vV]?\.?\s*([0-9](?:\.[0-9])?)"),
    re.compile(r"不良事件术语认定标准\s*([0-9](?:\.[0-9])?)"),
    re.compile(r"（CTCAE\s*([0-9](?:\.[0-9])?)）"),
)
_MEDDRA_PATTERN = re.compile(r"MedDRA\s*(?:版本|version)?\s*([0-9]{1,2}(?:\.[0-9])?)", re.IGNORECASE)
_INDICATION_HINTS = (
    ("过敏性鼻炎", "过敏性鼻炎", "抗组胺/鼻用糖皮质激素相关嗜睡、鼻部刺激、局部感染风险"),
    ("哮喘", "支气管哮喘", "支气管痉挛、口咽念珠菌感染、声嘶风险（吸入糖皮质激素）"),
    ("特应性皮炎", "特应性皮炎", "皮肤感染、烧灼感、免疫系统抑制风险"),
    ("2型糖尿病", "2型糖尿病", "低血糖、胃肠道反应、体重变化风险"),
    ("高血压", "原发性高血压", "低血压、电解质紊乱、肾功能变化风险"),
    ("类风湿", "类风湿关节炎", "感染、肝功能异常、血液学异常风险"),
    ("实体瘤", "晚期实体瘤", "骨髓抑制、感染、器官毒性风险"),
    ("淋巴瘤", "淋巴瘤", "骨髓抑制、感染、输注反应风险"),
)
_AE_SEVERITY_RULES_HINT = re.compile(r"(?:严重程度|分级|grade).{0,40}(?:CTCAE|毒性)", re.IGNORECASE)


@dataclass(frozen=True)
class ProtocolProfile:
    content_sha256: str
    ctcae_version: str = ""
    meddra_version: str = ""
    indication_zh: str = ""
    risk_direction_zh: str = ""
    anchors: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (quote, where)

    def to_payload(self) -> dict[str, Any]:
        return {
            "content_sha256": self.content_sha256,
            "ctcae_version": self.ctcae_version,
            "meddra_version": self.meddra_version,
            "indication_zh": self.indication_zh,
            "risk_direction_zh": self.risk_direction_zh,
            "anchors": [{"quote": q[:200], "where": w} for q, w in self.anchors[:10]],
            "unknown_visible": not (self.ctcae_version or self.risk_direction_zh),
        }


def _docx_text(path: Path) -> str:
    import docx  # noqa: PLC0415

    parts = []
    for paragraph in docx.Document(str(path)).paragraphs:
        parts.append(paragraph.text)
    try:
        for table in docx.Document(str(path)).tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
    except Exception:
        pass
    return "\n".join(parts)


def _pdf_text(path: Path) -> str:
    from pdfminer.high_level import extract_text  # noqa: PLC0415

    return extract_text(str(path), maxpages=60)


def _document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _docx_text(path)
    if suffix == ".pdf":
        return _pdf_text(path)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def build_protocol_profile(files_dir: Path) -> Optional[ProtocolProfile]:
    """Derive the profile from every registered document; newest wins per field.

    Fields stay empty (and ``unknown_visible`` turns true) when no document
    carries the evidence — coverage gaps are surfaced, never guessed.
    """
    ctcea_candidates: list[str] = []
    meddra_candidates: list[str] = []
    indication = ""
    risk_direction = ""
    anchors: list[tuple[str, str]] = []
    total_chars = 0
    for path in sorted(files_dir.glob("*")):
        if path.suffix.lower() not in (".docx", ".pdf", ".txt"):
            continue
        try:
            text = _document_text(path)
        except Exception:
            continue
        total_chars += len(text)
        where = path.name[:24]
        # 方案（docx）是项目标准版本的权威来源：其匹配权重高于IB等背景资料。
        weight = 3 if path.suffix.lower() == ".docx" else 1
        for pattern in _CTCAE_PATTERNS:
            for match in pattern.finditer(text):
                ctcea_candidates.extend([match.group(1)] * weight)
                anchors.append((match.group(0), where))
        for match in _MEDDRA_PATTERN.finditer(text):
            meddra_candidates.extend([match.group(1)] * weight)
            anchors.append((match.group(0), where))
        for keyword, indication_name, direction in _INDICATION_HINTS:
            if keyword in text:
                indication = indication_name
                risk_direction = direction
                anchors.append((f"适应症：{indication_name}", where))
                break

    def _elect(candidates: list[str]) -> str:
        # 多文档投票：出现最多的版本胜出；平票取数值更高者。
        if not candidates:
            return ""
        counts: dict[str, int] = {}
        for value in candidates:
            counts[value] = counts.get(value, 0) + 1
        return max(
            counts,
            key=lambda v: (counts[v], float(v) if v.replace(".", "").isdigit() else 0),
        )

    ctcae = _elect(ctcea_candidates)
    meddra = _elect(meddra_candidates)
    payload = {
        "ctcae_version": ctcae,
        "meddra_version": meddra,
        "indication_zh": indication,
        "risk_direction_zh": risk_direction,
        "anchors": anchors[:10],
        "total_document_chars": total_chars,
    }
    profile = ProtocolProfile(
        content_sha256=content_hash(payload),
        ctcae_version=ctcae,
        meddra_version=meddra,
        indication_zh=indication,
        risk_direction_zh=risk_direction,
        anchors=tuple(anchors[:10]),
    )
    if total_chars == 0:
        return None
    return profile


def profile_artifact_path(workspace: Path) -> Path:
    return workspace / "runtime" / "artifacts" / "protocol-profile.json"


def load_or_build_profile(workspace: Path) -> Optional[ProtocolProfile]:
    """Load the cached profile; rebuild when documents changed (mtime signature)."""

    files_dir = workspace / "document_authority_candidates" / "files"
    artifact = profile_artifact_path(workspace)
    if not files_dir.is_dir():
        return None
    try:
        signature = max(
            (p.stat().st_mtime_ns, p.name) for p in files_dir.iterdir()
        )
    except (OSError, ValueError):
        return None
    if artifact.is_file():
        try:
            cached = json.loads(artifact.read_text(encoding="utf-8"))
            if cached.get("_signature") == list(signature):
                return ProtocolProfile(
                    content_sha256=cached["content_sha256"],
                    ctcae_version=cached.get("ctcae_version", ""),
                    meddra_version=cached.get("meddra_version", ""),
                    indication_zh=cached.get("indication_zh", ""),
                    risk_direction_zh=cached.get("risk_direction_zh", ""),
                    anchors=tuple(
                        (item.get("quote", ""), item.get("where", ""))
                        for item in cached.get("anchors", [])
                    ),
                )
        except (OSError, ValueError, KeyError):
            pass
    profile = build_protocol_profile(files_dir)
    if profile is not None:
        payload = {
            "_signature": list(signature),
            **{k: v for k, v in profile.to_payload().items()},
        }
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    return profile


__all__ = [
    "ProtocolProfile",
    "build_protocol_profile",
    "load_or_build_profile",
    "profile_artifact_path",
]
