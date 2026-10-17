"""状态机专项M4：E2E三连从零驱动（02_DESIGN §四-M4）。

底座模式沿 scripts/fullchain_sar_rerun_20260926/（幂等键+state持久化+
evidence journal）；链路按向导用户路径（medicalMonitoringProductApi.mjs
同源端点）：建项→上传(listing+方案+eCRF)→核对(分析/复核AI链)→识别→
映射确认(答题+复核收敛)→事实→运行→发布→结果。

幂等：每round独立state.json逐stage落盘；重跑跳过已完成stage（同幂等键
重放由服务端ledger兜底）。付费AI作业只发生在识别/核对/事实阶段，重跑
不重复触发（服务端按attempt/batch幂等）。

用法： .venv/bin/python e2e_round.py round1 [--until STAGE]
退出码：0=全链通；2=阻断（state.journal含原因）。
"""

from __future__ import annotations

import json
import mimetypes
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench"
)
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
RUNTIME = WORKBENCH / "runs/tester_loop_iso_20260928/runtime"

SM1 = RUNTIME / "medical_monitoring_r7/proj_user_e282a7e982b0"
LISTING = (
    SM1
    / "admissions/staging/stg-2e4c7ee780914ac28146f40d3856fa9e"
    / "MG-K10-CSU-001_合成测试数据_V1.0.xlsx"
)
PROTOCOL = (
    SM1
    / "document_authority_candidates/files"
    / "73024713c28382ca8fca7c9338d7151256b2765d78d512876731156a9a504199.docx"
)
ECRF = (
    SM1
    / "document_authority_candidates/files"
    / "8109d25aef67771c84aae42e78cb0613af9b5f032290675d21d92e6bede15289.docx"
)

BASE = "http://127.0.0.1:8911"
R7 = f"{BASE}/api/projects/{{pid}}/modules/medical-monitoring/r7"

# 时序预算（识别/复核为真实AI分钟级链路）
POLL_ANALYZE_S = 90 * 60       # 核对（2分析+2复核AI作业；多轮并行时排队竞争）
POLL_MAPPING_S = 150 * 60      # 识别（约60分片×双队列，并行2）
POLL_ADJUDICATE_S = 180 * 60   # 双盲复核收敛（含分歧字段adjudication AI作业，实测两波18作业）
POLL_FACTS_S = 90 * 60         # 事实物化（8-10主题AI）
POLL_RUN_S = 150 * 60          # 监查运行
POLL_INTERVAL_S = 15.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Round:
    def __init__(self, name: str) -> None:
        self.name = name
        self.dir = HERE / "rounds" / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.journal_path = self.dir / "journal.jsonl"
        self.state: dict = {}
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())

    def log(self, event: str, **fields) -> None:
        record = {"ts": now_iso(), "round": self.name, "event": event, **fields}
        with self.journal_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{self.name}] {event}: " + json.dumps(fields, ensure_ascii=False)[:400], flush=True)

    def save(self) -> None:
        self.state_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    def done(self, stage: str) -> bool:
        return self.state.get("stages", {}).get(stage) == "done"

    def mark(self, stage: str, **fields) -> None:
        self.state.setdefault("stages", {})[stage] = "done"
        self.state.update({k: v for k, v in fields.items()})
        self.save()


def request(method: str, url: str, *, body: bytes | None = None,
            headers: dict | None = None, timeout: float = 120.0):
    req = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw or "{}")
        except Exception:
            return exc.code, {"_raw": raw[:500]}


def get_json(url: str, timeout: float = 120.0):
    return request("GET", url, timeout=timeout)


def post_json(url: str, payload=None, timeout: float = 300.0):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    return request("POST", url, body=data,
                   headers={"Content-Type": "application/json"}, timeout=timeout)


def multipart(files: list[tuple[str, bytes, str]], fields: dict[str, str] | None = None) -> tuple[bytes, str]:
    boundary = f"----m4{uuid.uuid4().hex}"
    out = bytearray()
    for name, data, filename in files:
        out += f"--{boundary}\r\n".encode()
        out += (
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {mimetypes.guess_type(filename)[0] or 'application/octet-stream'}\r\n\r\n"
        ).encode()
        out += data + b"\r\n"
    for name, value in (fields or {}).items():
        out += f"--{boundary}\r\n".encode()
        out += (
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        ).encode()
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), boundary


def post_multipart(url: str, files, fields=None, timeout: float = 300.0):
    body, boundary = multipart(files, fields)
    return request("POST", url, body=body,
                   headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                   timeout=timeout)


def poll(name: str, fn, *, max_s: float, interval: float = POLL_INTERVAL_S,
         ready, desc: str = ""):
    """轮询直到ready(...)为真或超时；返回最后载荷。"""

    deadline = time.monotonic() + max_s
    last = None
    n = 0
    while time.monotonic() < deadline:
        last = fn()
        n += 1
        verdict = ready(last)
        if verdict is True:
            return last
        if isinstance(verdict, str):  # 阻断码直接抛
            raise RuntimeError(f"{name} blocked: {verdict}")
        if n % 8 == 1:
            print(f"  poll {name} #{n}: {json.dumps(last, ensure_ascii=False)[:300]}", flush=True)
        time.sleep(interval)
    raise TimeoutError(f"{name} timeout after {max_s}s: {json.dumps(last, ensure_ascii=False)[:400]}")


# ---------------------------------------------------------------- stages

def stage_create(r: Round) -> None:
    if r.done("create"):
        return
    nonce = r.state.get("idem") or f"m4-{r.name}-{uuid.uuid4().hex[:12]}"
    r.state["idem"] = nonce
    r.save()
    # 覆盖面：round1用自拟代号名（命中身份门→用户确认归属分支）；
    # round2/3用与方案一致的研究名（覆盖身份门自动匹配分支）。
    project_names = {
        "round2": "MG-K10-CSU-001用于治疗慢性自发性荨麻疹的III期临床研究（M4-R2）",
        "round3": "MG-K10-CSU-001用于治疗慢性自发性荨麻疹的III期临床研究（M4-R3）",
    }
    payload = {
        "project_code": "",
        "project_name": project_names.get(r.name, f"MX循M4-{r.name.upper()}-CSU"),
        "indication": "慢性自发性荨麻疹",
        "product_name": "MG-K10人源化单抗注射液",
        "study_phase": "III",
        "protocol_id": "MG-K10-CSU-001",
        "protocol_version": "V1.3",
        "protocol_date": "2025-09-19",
        "entry_mode": "from_zero",
        "modules": ["medical_monitoring"],
        "actor": "m4_e2e_driver",
        "idempotency_key": f"{nonce}-create",
    }
    code, body = post_json(f"{BASE}/api/projects", payload, timeout=180)
    r.log("create_project", code=code, keys=sorted(body)[:12])
    if code != 201:
        raise RuntimeError(f"create failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")
    pid = body["project"]["project_id"]
    r.state["project_id"] = pid
    code2, body2 = post_json(R7.format(pid=pid) + "/workspace/bootstrap", {}, timeout=180)
    r.log("bootstrap", code=code2)
    if code2 not in (200, 201):
        raise RuntimeError(f"bootstrap failed {code2}: {json.dumps(body2, ensure_ascii=False)[:300]}")
    r.mark("create", project_id=pid)


def stage_upload(r: Round) -> None:
    if r.done("upload"):
        return
    pid = r.state["project_id"]
    listing_bytes = LISTING.read_bytes()
    url = R7.format(pid=pid) + "/data-admissions/upload"
    code, body = post_multipart(
        url,
        [
            ("files", listing_bytes, LISTING.name),
        ],
        fields={"relative_paths": LISTING.name},
        timeout=900,
    )
    r.log("upload_listing", code=code, attempt=body.get("attempt_id"), state=body.get("state"))
    if code not in (200, 201):
        raise RuntimeError(f"upload failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")
    r.mark("upload", attempt_id=body["attempt_id"])


def stage_documents(r: Round) -> None:
    """上传方案+eCRF→analyze→resolve轮询直到两角色current（真实AI核对链）。"""

    if r.done("documents"):
        return
    pid = r.state["project_id"]
    aid = r.state["attempt_id"]
    base = R7.format(pid=pid)
    analyze_url = f"{base}/data-admissions/{aid}/study-documents/analyze"
    resolve_url = f"{base}/data-admissions/{aid}/study-documents/resolve"
    code, body = post_multipart(
        analyze_url,
        [
            ("files", PROTOCOL.read_bytes(), "MG-K10-CSU-001_临床研究方案_V1.3.docx"),
            ("files", ECRF.read_bytes(), "MG-K10-CSU-001_eCRF填写指南_V1.0.docx"),
        ],
        timeout=600,
    )
    r.log("analyze", code=code, state=body.get("state"), token=str(body.get("analysis_token"))[:40])
    if code not in (200, 201, 202):
        raise RuntimeError(f"analyze failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")
    token = body.get("analysis_token")

    def _resolve(extra: dict | None = None):
        payload = {"batch_id": token}
        if extra:
            payload.update(extra)
        code_r, body_r = post_json(resolve_url, payload, timeout=600)
        body_r = dict(body_r)
        body_r["_code"] = code_r
        return body_r

    def _ready(p):
        if p.get("ready") is True:
            return True
        state = str(p.get("state") or "")
        if state in ("promoted", "ready", "current"):
            return True
        if state in ("failed",):
            roles = p.get("roles") or p.get("decisions") or []
            return f"blocked:{state}:{json.dumps(roles, ensure_ascii=False)[:200]}"
        if p.get("_code") not in (200, 201, 202, 409):
            return f"blocked:http_{p.get('_code')}"
        return False

    identity = {"confirmed": False}

    def _resolve_step():
        """轮询一步；首次见到project_mismatch即走用户「确认归属」分支。

        R1身份门的人工裁决出口（同向导「确认属于当前项目并继续」按钮同一
        载荷）：三件套取自同研究留存文件，确认归属并放行角色核对。
        """

        p = _resolve()
        if str(p.get("state") or "") == "project_mismatch" and not identity["confirmed"]:
            identity["confirmed"] = True
            r.log("identity_gate_hit", note="resolve返回project_mismatch，走用户确认归属分支")
            p = _resolve({
                "identity_confirmation": {
                    "confirmed": True,
                    "reason": "M4从零验收：方案/eCRF/listing三件套取自MG-K10-CSU-001同研究留存文件，确认归属当前项目并继续。",
                }
            })
        if str(p.get("state") or "") == "needs_user_input" and p.get("user_choices"):
            # 角色裁决卡（§1.2 documents needs_user_input/role）：双模型链对
            # 文件角色未收敛→用户选该角色对应的真实文件（candidate_id非空
            # =真实文件；空=标记缺失）。三件套真实在位，选对应文件。
            selections = []
            for choice in p.get("user_choices") or []:
                real = [o for o in (choice.get("options") or [])
                        if o.get("selectable") and str(o.get("candidate_id") or "")]
                if real:
                    selections.append({"role": str(choice.get("role")),
                                       "candidate_id": str(real[0]["candidate_id"])})
            if selections:
                r.log("role_adjudication", selections=selections)
                extra = {"user_role_selections": selections}
                if isinstance(p.get("decision_version"), int):
                    extra["expected_decision_version"] = p["decision_version"]
                p = _resolve(extra)
        return p

    final = poll("documents", _resolve_step, max_s=POLL_ANALYZE_S, ready=_ready)
    r.log("documents_resolved", state=final.get("state"))
    r.mark("documents")


def stage_mapping(r: Round) -> None:
    """启动识别→轮询到candidates_ready/needs_attention（真实AI识别链）。"""

    if r.done("mapping"):
        return
    pid = r.state["project_id"]
    aid = r.state["attempt_id"]
    base = R7.format(pid=pid)
    code, body = post_json(f"{base}/data-admissions/{aid}/mapping-candidates", {}, timeout=600)
    r.log("mapping_start", code=code, state=body.get("state"))
    if code not in (200, 201, 202, 409):
        raise RuntimeError(f"mapping start failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")

    def _status():
        code_s, body_s = get_json(
            f"{base}/data-admissions/{aid}/mapping-candidates",
            timeout=300,
        )
        return {"_code": code_s, **body_s}

    def _ready(p):
        state = str(p.get("state") or "")
        if state in ("candidates_ready", "needs_attention"):
            return True
        if p.get("_code") not in (200, 409):
            return f"blocked:http_{p.get('_code')}:{json.dumps(p)[:200]}"
        return False

    final = poll("mapping", _status, max_s=POLL_MAPPING_S, ready=_ready)
    # 正确用户流（R32-04）：needs_attention且有终态失败分片→先「重跑失败
    # 分片」用尽重试预算，再终态后才采纳——部分采纳虽能过确认，事实门
    # 按已确认修订字段判全域覆盖，整域缺口到事实必卡（round1实测，
    # 已确认草稿不可变+重新采纳409 conflict）。
    retries = 0
    while str(final.get("state") or "") == "needs_attention" and retries < 2:
        failures = final.get("table_failures") or []
        if not failures:
            break
        code_r, body_r = post_json(
            f"{base}/data-admissions/{aid}/mapping-candidates/retry-failed",
            {}, timeout=600,
        )
        requeued = int(body_r.get("requeued_count") or 0)
        r.log("retry_failed_shards", code=code_r, requeued=requeued,
              skipped=body_r.get("skipped_count"), tables=[t.get("table_name") for t in failures])
        retries += 1
        if code_r not in (200, 202) or requeued == 0:
            break
        time.sleep(30.0)
        final = poll("mapping-after-retry", _status, max_s=POLL_MAPPING_S, ready=_ready)
    r.log("mapping_ready", state=final.get("state"),
          critical=(final.get("summary") or {}).get("critical_count"),
          pending=(final.get("summary") or {}).get("pending_confirmation_count"),
          table_failures=len(final.get("table_failures") or []))
    r.mark("mapping", mapping_state=final.get("state"))


def stage_confirm(r: Round) -> None:
    """采纳→答题→确认（复核不收敛超预算后知情降级，如实留痕）。"""

    if r.done("confirm"):
        return
    pid = r.state["project_id"]
    aid = r.state["attempt_id"]
    base = R7.format(pid=pid)
    draft_url = f"{base}/data-admissions/{aid}/mapping-draft"
    field_url = f"{draft_url}/field"
    adjudicate_url = f"{draft_url}/adjudicate"
    confirm_url = f"{draft_url}/confirm"

    code, body = post_json(draft_url, {
        "reason": "M4从零验收：识别完成后采纳已识别字段进入医学确认。",
        "actor": "m4_e2e_driver",
    }, timeout=600)
    r.log("adopt", code=code, draft=body.get("draft", {}).get("draft_id") if isinstance(body.get("draft"), dict) else str(body.get("draft_id")))
    if code not in (200, 201):
        raise RuntimeError(f"adopt failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")
    draft = body.get("draft") or body
    draft_id = draft.get("draft_id")
    version = int(draft.get("version") or 1)
    fields = draft.get("fields") or []

    def _answer_open_questions(fields, version: int) -> int:
        """未决判定与confirm侧同源：user_decision_required且user_action未以
        「用户已确认：/用户已核对：」开头（双盲分歧卡的问题文本就写在
        user_action里——不能把「有文本」当「已作答」）。答案如实取主分析
        侧结论并留验收注记。返回新version。"""

        answered = 0
        for item in fields or []:
            action = str(item.get("user_action") or "").strip()
            if action.startswith(("用户已确认：", "用户已核对：")):
                continue
            if not item.get("user_decision_required"):
                continue
            code_a, body_a = request("PATCH", field_url, body=json.dumps({
                "draft_id": draft_id,
                "domain": item.get("domain"),
                "source_field": item.get("source_field"),
                "patch": {"user_action": "用户已核对：M4从零验收裁决——采纳主分析侧结论（问题文本所见两轮结论一致或择主分析侧），详见运行证据。"},
                "expected_version": version,
                "actor": "m4_e2e_driver",
                "idempotency_key": f"m4-answer-{r.name}-{uuid.uuid4().hex[:8]}",
            }).encode(), headers={"Content-Type": "application/json"}, timeout=300)
            if code_a in (200, 201):
                answered += 1
                version = int((body_a.get("draft") or body_a).get("version") or version + 1)
            else:
                r.log("answer_skip", code=code_a, domain=item.get("domain"),
                      field=item.get("source_field"),
                      err=json.dumps(body_a, ensure_ascii=False)[:200])
        if answered:
            r.log("answered", count=answered, version=version)
        return version

    version = _answer_open_questions(fields, version)

    # 向导同款状态机：adjudicate轮询（R36-01在途防重入，返回诚实快照）
    # →complete后confirm一次；confirm 409（对账/盲核未完）回到轮询。
    # 超预算→知情降级确认（allow_unverified_dual_review，如实留痕）。
    degraded = False
    deadline = time.monotonic() + POLL_ADJUDICATE_S
    attempt = 0
    adjudicate_calls = 0
    blocked_streak = 0
    while True:
        # --- adjudicate 轮询到 complete ---
        while True:
            adjudicate_calls += 1
            code_j, body_j = post_json(adjudicate_url, {"draft_id": draft_id}, timeout=2400)
            adj = body_j.get("adjudication") if isinstance(body_j.get("adjudication"), dict) else {}
            adj_state = str(adj.get("state") or body_j.get("state") or "")
            if code_j not in (200, 201):
                err_j = str(body_j.get("code") or "")
                r.log("adjudicate_err", code=code_j, err=err_j, calls=adjudicate_calls)
                if err_j in ("mapping_verifier_incomplete", "mapping_reconciliation_required"):
                    pass
                elif time.monotonic() > deadline:
                    break
            elif adjudicate_calls % 5 == 1 or adj_state != "running":
                r.log("adjudicate", state=adj_state, calls=adjudicate_calls,
                      remaining=adj.get("remaining_system_review_count"),
                      detail=json.dumps(adj, ensure_ascii=False)[:160])
            if adj_state == "complete":
                draft_now = body_j.get("draft") if isinstance(body_j.get("draft"), dict) else {}
                version = int(draft_now.get("version") or version)
                version = _answer_open_questions(draft_now.get("fields") or [], version)
                break
            if adj_state == "blocked":
                draft_now = body_j.get("draft") if isinstance(body_j.get("draft"), dict) else {}
                new_version = _answer_open_questions(draft_now.get("fields") or [], int(draft_now.get("version") or version))
                if new_version != version:
                    version = new_version
                    blocked_streak = 0
                    continue
                blocked_streak += 1
                # 用户已作答完毕（无可答题）且复核连续blocked（分片预算耗尽/
                # 内容级终态失败不再自愈）→进入confirm；常规confirm 409则按
                # R36-01唯一非重入出路转知情降级（降级事实由确认层留痕）。
                if blocked_streak >= 2:
                    r.log("adjudicate_blocked_terminal", calls=adjudicate_calls,
                          note="无可答题+连续blocked，转confirm（409→知情降级）")
                    break
            else:
                blocked_streak = 0
            if time.monotonic() > deadline:
                break
            time.sleep(60.0)

        # --- confirm 前：重拉权威草稿字段并答完双盲分歧卡（adjudicate响应
        #     不一定带draft.fields；confirm侧按草稿行判题，必须同源） ---
        code_g, body_g = get_json(f"{base}/data-admissions/{aid}/mapping-candidates", timeout=600)
        if code_g == 200 and isinstance(body_g.get("draft"), dict):
            d_now = body_g["draft"]
            version = _answer_open_questions(d_now.get("fields") or [], int(d_now.get("version") or version))

        # --- confirm 一次 ---
        attempt += 1
        payload = {
            "draft_id": draft_id,
            "expected_version": version,
            "confirmed_by": "m4_e2e_driver",
            "confirmation_reason": "M4从零验收：字段映射医学确认，作答完毕后确认。",
            "idempotency_key": f"m4-confirm-{r.name}-{attempt}-{uuid.uuid4().hex[:6]}",
            "automatic": False,
            "allow_unverified_dual_review": degraded,
        }
        code_c, body_c = post_json(confirm_url, payload, timeout=2400)
        if code_c in (200, 201):
            r.log("confirmed", attempt=attempt, degraded=degraded,
                  revision=str(body_c.get("mapping_revision") or "")[:40])
            break
        err = str(body_c.get("code") or body_c.get("detail", {}).get("code") or "")
        r.log("confirm_retry", code=code_c, err=err, attempt=attempt, degraded=degraded)
        if err == "mapping_draft_conflict":
            # 版本漂移：重读草稿version后再试
            code_g, body_g = get_json(f"{base}/data-admissions/{aid}/mapping-candidates", timeout=300)
            d = body_g.get("draft") if isinstance(body_g.get("draft"), dict) else {}
            version = int(d.get("version") or version)
        # blocked_streak=复核已终态不收敛（无可答题、分片预算耗尽）→常规
        # confirm 409后立即按R36-01出口转知情降级，不再空等预算。
        terminal_block = blocked_streak >= 2 and err in (
            "mapping_verifier_job_failed", "mapping_reconciliation_required",
            "mapping_verifier_incomplete",
        )
        if time.monotonic() > deadline or terminal_block:
            if degraded:
                raise RuntimeError(f"confirm failed persistently: {err}")
            degraded = True
            r.log("confirm_degrade", err=err,
                  note="复核终态不收敛（分片预算耗尽），转知情降级确认（R36-01出口，如实留痕）")
            continue
        time.sleep(30.0)
    r.mark("confirm", degraded=degraded)


def stage_facts(r: Round) -> None:
    if r.done("facts"):
        return
    pid = r.state["project_id"]
    aid = r.state["attempt_id"]
    base = R7.format(pid=pid)
    code, body = post_json(f"{base}/data-admissions/{aid}/facts", {}, timeout=1800)
    r.log("facts_start", code=code, state=body.get("state") or body.get("facts_state"))
    if code not in (200, 201, 202, 409):
        raise RuntimeError(f"facts start failed {code}: {json.dumps(body, ensure_ascii=False)[:300]}")

    def _status():
        code_s, body_s = get_json(f"{base}/data-admissions/{aid}/facts", timeout=300)
        return {"_code": code_s, **body_s}

    def _ready(p):
        if bool(p.get("facts_generated")) or str(p.get("state") or "") == "ready":
            return True
        if str(p.get("state") or "") == "failed":
            return "blocked:facts_failed"
        return False

    final = poll("facts", _status, max_s=POLL_FACTS_S, ready=_ready)
    r.log("facts_ready", generated=final.get("facts_generated"))
    r.mark("facts")


def stage_run(r: Round) -> None:
    if r.done("run"):
        return
    pid = r.state["project_id"]
    base = R7.format(pid=pid)
    code, opts = get_json(f"{base}/run-setup/options", timeout=600)
    if code != 200:
        raise RuntimeError(f"run-setup/options {code}: {json.dumps(opts)[:300]}")
    # 载荷形状（run-setup/options实测 mm-r7-slice07c1-run-setup-v1）：
    # data_batches[0].snapshot_token / modes[].available+execution_basis_options
    # / recommended_mode / rule_revisions（新项目可为空=特殊关注0项）。
    batches = opts.get("data_batches") or []
    token = str((batches[0] if batches else {}).get("snapshot_token") or opts.get("current_snapshot_token") or "")
    modes = [m for m in (opts.get("modes") or []) if m.get("available")]
    if not token or not modes:
        raise RuntimeError(f"options not runnable: {json.dumps(opts, ensure_ascii=False)[:300]}")
    recommended = str(opts.get("recommended_mode") or "")
    chosen = next((m for m in modes if m.get("mode") == recommended), modes[0])
    mode = chosen["mode"]
    basis_opts = [b for b in (chosen.get("execution_basis_options") or []) if b.get("available")]
    basis = str(chosen.get("default_execution_basis") or "")
    if basis_opts and basis not in {b.get("value") for b in basis_opts}:
        basis = str(basis_opts[0].get("value") or "")
    rules = [
        item.get("revision_token") or item.get("token")
        for item in (opts.get("rule_revisions") or [])
        if item.get("selectable") and (item.get("revision_token") or item.get("token"))
    ]
    payload = {
        "current_snapshot_token": token,
        "mode": mode,
        "execution_basis": basis or "full",
        "baseline_token": None,
        "risk_rule_tokens": rules,
        "idempotency_key": f"m4-run-{r.name}-{uuid.uuid4().hex[:10]}",
    }
    r.log("run_start_attempt", mode=mode, basis=payload["execution_basis"],
          rules=len(rules))
    code_r, body_r = post_json(f"{base}/runs/prepare-and-start", payload, timeout=1800)
    r.log("run_started", code=code_r, keys=sorted(body_r)[:12])
    if code_r not in (200, 201, 202):
        raise RuntimeError(f"prepare-and-start {code_r}: {json.dumps(body_r, ensure_ascii=False)[:400]}")
    run_token = (
        body_r.get("public_run_token")
        or body_r.get("run", {}).get("public_run_token")
        or ""
    )
    if not run_token:
        raise RuntimeError(f"no public_run_token: {json.dumps(body_r)[:300]}")
    r.state["public_run_token"] = run_token
    r.save()

    def _progress():
        code_p, body_p = get_json(f"{base}/runs/{run_token}/progress", timeout=300)
        return {"_code": code_p, **body_p}

    def _ready(p):
        state = str(p.get("run_state") or p.get("state") or "")
        if state == "completed":
            return True
        if state in ("failed", "cancelled"):
            return f"blocked:run_{state}"
        return False

    poll("run", _progress, max_s=POLL_RUN_S, ready=_ready)
    r.mark("run", public_run_token=run_token)


def stage_publish(r: Round) -> None:
    if r.done("publish"):
        return
    pid = r.state["project_id"]
    base = R7.format(pid=pid)
    token = r.state["public_run_token"]
    code, body = post_json(
        f"{base}/runs/{token}/publication",
        {"idempotency_key": f"result-publication:{token}"},
        timeout=1800,
    )
    r.log("publish", code=code, keys=sorted(body)[:12])
    if code not in (200, 201, 409):
        raise RuntimeError(f"publish {code}: {json.dumps(body, ensure_ascii=False)[:400]}")
    code_e, entry = get_json(f"{base}/runs/{token}/result-entry", timeout=300)
    r.log("result_entry", code=code_e)
    ctx = str(entry.get("result_context_token") or "")
    if not ctx:
        raise RuntimeError(f"no result_context_token: {json.dumps(entry)[:300]}")
    code_o, overview = get_json(f"{base}/results/{ctx}/overview", timeout=600)
    r.log("result_overview", code=code_o,
          subjects=(overview.get("summary") or {}).get("subject_count")
          if isinstance(overview.get("summary"), dict) else None)
    if code_o != 200:
        raise RuntimeError(f"overview {code}: {json.dumps(overview)[:300]}")
    r.mark("publish", result_context_token=ctx)


def stage_evidence(r: Round) -> None:
    """导出stage-state事件流证据（M4验收面：卡在哪一步可从事件史回答）。"""

    pid = r.state.get("project_id")
    aid = r.state.get("attempt_id")
    if not pid:
        return
    db = RUNTIME / "medical_monitoring_ai.sqlite3"
    import sqlite3
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT stage, event_type, reason_code, created_at "
            "FROM monitoring_admission_stage_events "
            "WHERE project_id=? ORDER BY created_at",
            (pid,),
        ).fetchall()
    finally:
        conn.close()
    out_path = r.dir / "stage_events_export.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(
                {"stage": row[0], "event_type": row[1],
                 "reason_code": row[2], "created_at": row[3]},
                ensure_ascii=False) + "\n")
    counts: dict = {}
    for row in rows:
        counts[f"{row[0]}/{row[1]}"] = counts.get(f"{row[0]}/{row[1]}", 0) + 1
    r.log("evidence_exported", events=len(rows), counts=counts,
          path=str(out_path))


STAGES = [
    ("create", stage_create),
    ("upload", stage_upload),
    ("documents", stage_documents),
    ("mapping", stage_mapping),
    ("confirm", stage_confirm),
    ("facts", stage_facts),
    ("run", stage_run),
    ("publish", stage_publish),
    ("evidence", stage_evidence),
]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "round1"
    until = sys.argv[3] if len(sys.argv) > 3 else None
    if len(sys.argv) > 2 and sys.argv[2] != "--until":
        until = sys.argv[2]
    r = Round(name)
    r.log("round_begin", assets_exist=all(p.is_file() for p in (LISTING, PROTOCOL, ECRF)))
    try:
        for stage_name, fn in STAGES:
            if not r.done(stage_name):
                fn(r)
            if until and stage_name == until:
                r.log("until_reached", stage=stage_name)
                break
        r.log("round_complete", project=r.state.get("project_id"),
              attempt=r.state.get("attempt_id"),
              run=r.state.get("public_run_token"))
        return 0
    except Exception as exc:
        r.log("round_blocked", error=f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
