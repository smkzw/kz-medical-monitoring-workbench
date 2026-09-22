"""0922V2: selected source logic transcribed from GitHub HEAD 07b6a09.
NOT a copy of the full application. Imports/hash and external dependencies are
local test scaffolding. Function bodies preserve the reviewed control flow.
No production runtime, credentials, model requests, or user data are loaded.
See evidence/source_index.json for scope and original locations.
"""
from __future__ import annotations
import json, hashlib, re
from pathlib import Path
from typing import Any, Mapping, Sequence

# Local scaffold mirrors the canonical JSON digest used in repository primitives.
def content_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()

FACTS_SOURCE_DIGEST_VERSION = 'facts-source-digest-v2'
def facts_table_source_digest(table: str, rows: Sequence[Mapping[str, Any]]) -> str:
    return content_hash({
        "digest_version": FACTS_SOURCE_DIGEST_VERSION,
        "table": table,
        "rows": [content_hash(dict(row)) for row in rows],
    })

def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, bool):
        return "true" if value else "false"
    return " ".join(str(value).split())

_POSITIVE_DIRECTION_RE = re.compile(
    r"存在|有|记录了|提示|不一致|矛盾|漏报|缺如|异常|升高|降低|超出|"
    "超出正常|需核查|需关注|值得关注|风险信号"
)
_NEGATIVE_DIRECTION_RE = re.compile(
    r"未见|未记录|未提及|无异常|正常|一致|相符|不存在|无明显|"
    "未见明显|未见异常|无特殊|排除"
)

def _clue_direction_text(candidate: Any) -> str:
    payload = getattr(candidate, "structured_payload", {}) or {}
    parts = [str(getattr(candidate, "title", "") or ""),
             str(getattr(candidate, "text", "") or "")]
    for claim in payload.get("claims", []) or []:
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    return " ".join(parts)

def _clue_stance(candidate: Any) -> str:
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

_GRADE_RE = re.compile(r"(?:^|[^0-9])([1-5])\s*级|grade\s*([1-5])", re.IGNORECASE)
def _grade_terms(candidate: Any) -> set[str]:
    text = _clue_direction_text(candidate)
    if not text:
        return set()
    grades = set()
    for first, second in _GRADE_RE.findall(text):
        grades.add(first or second)
    return grades

# External pairing dependencies replaced with controlled fixture accessors.
def _clue_fingerprint(candidate): return frozenset(candidate.evidence_ids)
def _clue_domain_pair(candidate): return frozenset(candidate.structured_payload.get('domains', []))
def _clue_entities(candidate): return frozenset()

def _clues_agree(primary: Any, verifier: Any) -> bool:
    shared_evidence = _clue_fingerprint(primary) & _clue_fingerprint(verifier)
    domains = _clue_domain_pair(primary) & _clue_domain_pair(verifier)
    shared_entities = _clue_entities(primary) & _clue_entities(verifier)
    has_evidence_overlap = bool(shared_evidence)
    has_entity_match = bool(domains) and len(shared_entities) >= 2
    if not has_evidence_overlap and not has_entity_match:
        return False
    primary_stance = _clue_stance(primary)
    verifier_stance = _clue_stance(verifier)
    if primary_stance != "positive" or verifier_stance != "positive":
        return False
    primary_grades = _grade_terms(primary)
    verifier_grades = _grade_terms(verifier)
    if primary_grades and verifier_grades and not (primary_grades & verifier_grades):
        return False
    return True

_AI_FINDINGS_ARTIFACT = 'aemh-findings-facts-snapshot-001.dualvlm-full1.json'
class FindingsReader:
    # Constructor and daily fallback below are scaffolding; reader method bodies
    # follow the current FactsModeOutputProvider implementation.
    def __init__(self, root: Path, project_ref=''):
        self._artifacts_dir, self._project_ref = root, project_ref
    _FINDINGS_BINDING = "aemh-findings.active.json"
    def _read_findings_binding(self) -> dict[str, Any]:
        if self._artifacts_dir is None:
            return {}
        try:
            value = json.loads((Path(self._artifacts_dir) / self._FINDINGS_BINDING).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(value, dict):
            return {}
        artifact = str(value.get("artifact", "")).strip()
        digest = str(value.get("content_sha256", "")).strip()
        if not artifact or "/" in artifact or ".." in artifact or len(digest) != 64:
            return {}
        return value
    def _read_ai_findings(self) -> dict[str, Any]:
        if self._artifacts_dir is None:
            return {"state": "missing", "findings": None, "artifact": None, "error": "artifacts_dir未配置"}
        binding = self._read_findings_binding()
        if binding:
            artifact_name = str(binding["artifact"])
            expected_digest = str(binding["content_sha256"])
            project_id = str(binding.get("project_id", "")).strip()
            if self._project_ref and project_id and project_id != str(self._project_ref):
                return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": "binding_project_mismatch"}
            artifact_path = Path(self._artifacts_dir) / artifact_name
        else:
            artifact_name = _AI_FINDINGS_ARTIFACT
            expected_digest = ""
            artifact_path = Path(self._artifacts_dir) / artifact_name
        if not artifact_path.is_file():
            return {"state": "missing", "findings": None, "artifact": artifact_name, "error": None}
        try:
            with open(artifact_path, encoding="utf-8") as handle:
                artifact = json.load(handle)
        except (OSError, ValueError) as exc:
            return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": f"json_decode: {exc}"}
        if not isinstance(artifact, dict):
            return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": "not_object"}
        declared = str(artifact.get("content_sha256", "")).strip()
        verify = {k: v for k, v in artifact.items() if k != "content_sha256"}
        recomputed = content_hash(verify)
        if declared and recomputed != declared:
            return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": "content_sha256_mismatch"}
        if expected_digest and recomputed != expected_digest:
            return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": "binding_digest_mismatch"}
        findings = artifact.get("findings")
        if not isinstance(findings, list):
            return {"state": "read_failed", "findings": None, "artifact": artifact_name, "error": "findings_not_list"}
        state = "completed_with_findings" if findings else "completed_no_findings"
        result = {"state": state, "findings": findings, "artifact": artifact_name,
                  "content_sha256": declared, "error": None}
        if binding:
            result["binding"] = {"snapshot_digest": str(binding.get("snapshot_digest", "")), "project_id": str(binding.get("project_id", ""))}
        return result
    def _daily_findings(self, binding, r5_packet):
        read = self._read_ai_findings()
        if read["state"] == "completed_with_findings":
            return self._findings_from_artifact(read["findings"], r5_packet)
        if read["state"] == "completed_no_findings":
            return []
        if read["state"] == "read_failed":
            return []
        return self._deterministic_fallback_findings(binding, r5_packet)
    def _findings_from_artifact(self, rows, packet): return rows
    def _deterministic_fallback_findings(self, binding, packet): return [{'kind':'DETERMINISTIC_FALLBACK_FIXTURE'}]

class DocumentAuthorityError(ValueError): pass

def _apply_user_role_selections(resolved, user_role_selections, candidate_batch):
    selections = list(user_role_selections or ())
    if not selections:
        return resolved
    unresolved = list(resolved.get("unresolved_roles", ()))
    resolved_roles = [{**item} for item in resolved.get("resolved_roles", ())]
    candidate_ids = {str(item.get("candidate_id")) for item in candidate_batch.get("candidates", ())}
    adjudicated = []
    for selection in selections:
        role = str(selection.get("role") if isinstance(selection, Mapping) else "").strip()
        candidate_id = str(selection.get("candidate_id") if isinstance(selection, Mapping) else "").strip()
        if candidate_id and candidate_id not in candidate_ids:
            raise DocumentAuthorityError("document_authority_user_selection_invalid")
        if role not in unresolved:
            continue
        resolved_roles.append({"role":role,"status":"selected" if candidate_id else "missing",
            "candidate_id":candidate_id,"supplementary_candidate_ids":[],"user_adjudicated":True})
        unresolved.remove(role)
        adjudicated.append(role)
    state = "resolved" if not unresolved else str(resolved.get("state"))
    return {**resolved,"resolved_roles":resolved_roles,"unresolved_roles":unresolved,
            "state":state,"user_adjudicated_roles":adjudicated}

class SelectionStore:
    _USER_SELECTIONS_SCHEMA = "monitoring-document-authority-user-selections-v1"
    @staticmethod
    def _candidate_root(workspace_dir): return Path(workspace_dir) / 'document_authority_candidates'
    @classmethod
    def _selections_path(cls, workspace_dir, batch_id):
        return cls._candidate_root(workspace_dir)/'user_selections'/f'{batch_id}.json'
    @classmethod
    def _load_user_selections(cls, workspace_dir, batch_id):
        try:
            value=json.loads(cls._selections_path(workspace_dir,batch_id).read_text(encoding='utf-8'))
        except (OSError, ValueError): return []
        if not isinstance(value,dict) or value.get('schema_version')!=cls._USER_SELECTIONS_SCHEMA or value.get('batch_id')!=batch_id: return []
        return [dict(item) for item in value.get('selections',()) if isinstance(item,dict) and str(item.get('role','')).strip()]
    @classmethod
    def _save_user_selections(cls, workspace_dir, batch_id, project_id, selections):
        if not selections: return
        path=cls._selections_path(workspace_dir,batch_id)
        merged={str(item['role']):dict(item) for item in cls._load_user_selections(workspace_dir,batch_id)}
        from datetime import datetime as _datetime
        now=_datetime.now().isoformat()
        for item in selections:
            record=dict(item); record.setdefault('actor','medical_manager'); record['decided_at']=now
            merged[str(item['role'])]=record
        payload={'schema_version':cls._USER_SELECTIONS_SCHEMA,'batch_id':batch_id,'project_id':project_id,
                 'selections':sorted(merged.values(),key=lambda item:str(item['role'])),'updated_at':now}
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=1),encoding='utf-8')
        temporary.replace(path)
    def _effective_user_selections(self, *, project_id, workspace_dir, batch_id, user_role_selections):
        persisted=self._load_user_selections(workspace_dir,batch_id)
        merged={str(item['role']):dict(item) for item in persisted}
        incoming=[dict(item) for item in (user_role_selections or ()) if isinstance(item,dict) and str(item.get('role','')).strip()]
        if incoming:
            for item in incoming: merged[str(item['role'])]=item
            self._save_user_selections(workspace_dir,batch_id,project_id,incoming)
        return list(merged.values())
