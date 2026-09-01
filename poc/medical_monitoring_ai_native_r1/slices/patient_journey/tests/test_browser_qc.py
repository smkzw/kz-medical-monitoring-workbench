"""Playwright browser + visual QC for Slice 4 Patient Journey.

Authorized worker-03 artifact. Opens the page via absolute ``file://`` only.
Does not start a server and does not install packages.

Run with:
    .venv/bin/python -m pytest -q \\
      poc/medical_monitoring_ai_native_r1/slices/patient_journey/tests/test_browser_qc.py

Evidence root (authorized):
    output/playwright/medical_monitoring_r1_patient_journey_slice4_20260809/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

SLICE_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = SLICE_ROOT / "index.html"
# patient_journey -> slices -> medical_monitoring_ai_native_r1 -> poc -> workbench
WORKSPACE_ROOT = SLICE_ROOT.parents[3]
assert (WORKSPACE_ROOT / "poc").is_dir(), f"workspace root misdetected: {WORKSPACE_ROOT}"
EVIDENCE_ROOT = (
    WORKSPACE_ROOT
    / "output"
    / "playwright"
    / "medical_monitoring_r1_patient_journey_slice4_20260809"
)
QC_SUMMARY_PATH = EVIDENCE_ROOT / "qc_summary.json"

VIEWPORTS: Sequence[Tuple[str, int, int]] = (
    ("1280x800", 1280, 800),
    ("1440x900", 1440, 900),
    ("1920x1080", 1920, 1080),
)
NARROW_VIEWPORT = ("900x700", 900, 700)
REQUIRED_BROWSERS = ("chromium", "webkit")
OPTIONAL_BROWSERS = ("firefox",)

# Codex-direct audience terminology (post-manager remake).
CHINESE_TABS = ("旅程总览", "指标趋势", "事件明细", "风险依据")
REQUIRED_EVENT_LEGEND_TOKENS = (
    "事件记录",
    "AE",
    "MH",
    "CM/合并用药",
    "IP给药",
    "实验室/检查",
    "住院/操作",
    "症状/体征线索",
)
REQUIRED_RISK_LEGEND_TOKENS = (
    "风险提示",
    "AE相关风险",
    "MH相关风险",
    "CM/合并用药相关风险",
    "IP给药相关风险",
    "实验室/检查相关风险",
    "住院/操作相关风险",
    "症状/体征线索相关风险",
    "风险等级",
)
REQUIRED_EVENT_DOMAINS = {"ae", "mh", "cm", "ip", "lab", "hospitalization", "symptom"}
REQUIRED_RISK_LEGEND_DOMAINS = REQUIRED_EVENT_DOMAINS
REQUIRED_BOUNDARY_MARKERS = ("不会改变", "查阅")
REQUIRED_BODY_MARKERS = ("合成演示数据", "SYNTHETIC-SUBJECT-001")

FORBIDDEN_VISIBLE = (
    "&&",
    "@@",
    "${",
    "AI自动判断",
    "AI替代医学判断",
    "passed",
    "potential_unreported_",
    "temporal_spine_id",
    "spine_id",
    "identity_key",
    "source_ref",
    "MM_R1",
    "shape=",
    "line=",
    "file://",
    "worker 01",
    "worker_01",
    "worker_02",
    "build_data.py",
    "console.log",
    "DEBUG",
    "TODO:",
    "FIXME",
    "Profile",
    "Timeline",
    # Codex terminology correction — forbidden in audience-visible text
    "正式事实",
    "候选信号",
    "只读",
    "已建立风险",
    "正反证",
    "闭区间",
    "开放区间",
    "只读投影",
    "Patient Journey",
    "风险优先密度",
    "横向密度",
    "共享访视轴",
)
FORBIDDEN_ID_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\bNCT\d{8}\b", re.I),
    re.compile(r"\brisk_[0-9a-f]{16,}\b", re.I),
    re.compile(r"\b(?:fact|candidate|query)_[0-9a-f]{16,}\b", re.I),
    re.compile(r"\b[0-9a-f]{40,64}\b", re.I),
)

PAGE_OVERFLOW_JS = r"""
() => {
  const doc = document.documentElement;
  const body = document.body;
  return {
    documentElement: { scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth },
    body: { scrollWidth: body.scrollWidth, clientWidth: body.clientWidth },
    horizontal_overflow: Math.max(doc.scrollWidth - doc.clientWidth, body.scrollWidth - body.clientWidth),
  };
}
"""

JOURNEY_STRUCTURE_JS = r"""
() => {
  const lanes = Array.from(document.querySelectorAll('.pj-lane')).map((el) => ({
    id: el.getAttribute('data-lane') || '',
    label: (el.querySelector('.pj-lane__label') || {}).textContent || '',
    visible: !!(el.offsetWidth || el.offsetHeight),
  }));
  const visitEls = Array.from(document.querySelectorAll('.pj-visit-mark'));
  const visitMeta = visitEls.map((el) => {
    const codeEl = el.querySelector('.pj-visit-mark__code');
    const code = el.getAttribute('data-visit-code') || (codeEl && codeEl.textContent) || '';
    const r = el.getBoundingClientRect();
    return {
      code: String(code).trim(),
      type: el.getAttribute('data-type') || '',
      title: el.getAttribute('title') || '',
      text: (el.innerText || '').replace(/\s+/g, ' ').trim(),
      left: r.left,
      right: r.right,
      width: r.width,
    };
  });
  const codeCounts = {};
  for (const m of visitMeta) {
    if (!m.code) continue;
    codeCounts[m.code] = (codeCounts[m.code] || 0) + 1;
  }
  const duplicateCodes = Object.keys(codeCounts).filter((c) => codeCounts[c] > 1);
  const smashed = [];
  for (const m of visitMeta) {
    const compact = m.text.replace(/\s+/g, '');
    if (m.code && compact.includes(m.code + m.code)) {
      smashed.push({ code: m.code, text: compact.slice(0, 40), reason: 'repeated_code_in_node_text' });
    }
  }
  const byLeft = visitMeta.slice().sort((a, b) => a.left - b.left);
  const adjacentOverlap = [];
  for (let i = 0; i < byLeft.length - 1; i++) {
    const a = byLeft[i], b = byLeft[i + 1];
    const overlap = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    if (overlap > 1 && a.code && a.code === b.code) {
      adjacentOverlap.push({ code: a.code, overlap_px: overlap, reason: 'adjacent_same_code_overlap' });
      smashed.push({ code: a.code, overlap_px: overlap, reason: 'adjacent_same_code_overlap' });
    }
  }
  const paired = visitEls.filter((el) => el.getAttribute('data-type') === 'paired');
  const pairedOk = paired.map((el) => {
    const t = el.innerText || '';
    const title = el.getAttribute('title') || '';
    const dates = title.match(/\d{4}-\d{2}-\d{2}/g) || [];
    return {
      code: el.getAttribute('data-visit-code') || '',
      hasPlan: /计划/.test(t),
      hasActual: /实际/.test(t),
      titleHasBothDates: dates.length >= 2,
      titleDates: dates,
      title,
    };
  });
  const types = {};
  for (const m of visitMeta) {
    types[m.type || 'unknown'] = (types[m.type || 'unknown'] || 0) + 1;
  }
  const unscheduled = visitEls.filter((el) => el.getAttribute('data-type') === 'unscheduled').length;
  const sticky = !!document.querySelector('.pj-sticky-ruler');
  const phases = document.querySelectorAll('.pj-phase-band').length;
  const fact = document.querySelectorAll('.pj-marker[data-shape="fact"], .pj-interval[data-class="formal_fact"]').length;
  const candidate = document.querySelectorAll('.pj-marker[data-shape="candidate"], .pj-interval[data-class="candidate"]').length;
  const risk = document.querySelectorAll('.pj-marker[data-shape="established_risk"]').length;
  const eventDomains = Array.from(document.querySelectorAll('.pj-marker[data-marker-kind="event"]'))
    .map((el) => el.getAttribute('data-domain') || '')
    .filter(Boolean);
  const riskDomains = Array.from(document.querySelectorAll('.pj-marker[data-marker-kind="risk"]'))
    .map((el) => el.getAttribute('data-domain') || '')
    .filter(Boolean);
  const eventLegendDomains = Array.from(document.querySelectorAll('.pj-legend__item[data-kind="event"]'))
    .map((el) => el.getAttribute('data-domain') || '')
    .filter(Boolean);
  const riskLegendDomains = Array.from(document.querySelectorAll('.pj-legend__item[data-kind="risk"]'))
    .map((el) => el.getAttribute('data-domain') || '')
    .filter(Boolean);
  const swatches = Array.from(document.querySelectorAll('.pj-legend__item')).map((el) =>
    (el.innerText || '').replace(/\s+/g, ' ').trim()
  );
  const scroll = document.getElementById('pj-journey-scroll');
  return {
    lane_count: lanes.length,
    lanes,
    visit_marks: visitEls.length,
    visit_codes: visitMeta.map((m) => m.code),
    visit_types: types,
    duplicate_visit_codes: duplicateCodes,
    smashed_labels: smashed,
    adjacent_same_code_overlap: adjacentOverlap,
    paired_nodes: pairedOk,
    unscheduled_count: unscheduled,
    sticky_ruler: sticky,
    phase_bands: phases,
    marker_counts: { fact, candidate, established_risk: risk },
    marker_domains: {
      event: Array.from(new Set(eventDomains)),
      risk: Array.from(new Set(riskDomains)),
      event_legend: Array.from(new Set(eventLegendDomains)),
      risk_legend: Array.from(new Set(riskLegendDomains)),
    },
    legend_items: swatches,
    journey_scroll_exists: !!scroll,
    journey_can_scroll_x: !!(scroll && scroll.scrollWidth > scroll.clientWidth + 1),
  };
}
"""

SHAPE_SEMANTICS_JS = r"""
() => {
  const issues = [];
  const events = Array.from(document.querySelectorAll('.pj-marker[data-marker-kind="event"]'));
  const candidates = Array.from(document.querySelectorAll('.pj-marker[data-shape="candidate"]'));
  const risks = Array.from(document.querySelectorAll('.pj-marker[data-marker-kind="risk"]'));
  const eventDomains = new Set();
  const riskDomains = new Set();
  const shapeSignatures = new Set();

  for (const marker of events) {
    const domain = marker.getAttribute('data-domain') || '';
    const shape = marker.querySelector('.pj-marker__shape');
    const abbr = marker.querySelector('.pj-marker__abbr');
    if (!domain) issues.push({ kind: 'event', reason: 'missing_domain' });
    if (!abbr || !(abbr.textContent || '').trim()) issues.push({ kind: 'event', domain, reason: 'missing_abbreviation' });
    if (domain) eventDomains.add(domain);
    if (shape) {
      const cs = getComputedStyle(shape);
      shapeSignatures.add([domain, cs.borderRadius, cs.clipPath, cs.width, cs.borderStyle].join('|'));
    }
  }
  for (const marker of candidates) {
    const shape = marker.querySelector('.pj-marker__shape');
    const style = shape ? getComputedStyle(shape).borderStyle : '';
    if (!/dashed|dotted/i.test(style)) {
      issues.push({ kind: 'event', reason: 'risk_clue_border_not_dashed', borderStyle: style });
    }
  }
  for (const marker of risks) {
    const domain = marker.getAttribute('data-domain') || '';
    const shape = marker.querySelector('.pj-marker__shape');
    const abbr = marker.querySelector('.pj-marker__abbr');
    const severity = marker.querySelector('.pj-marker__severity');
    if (!domain) issues.push({ kind: 'risk', reason: 'missing_domain' });
    if (!abbr || !(abbr.textContent || '').trim()) issues.push({ kind: 'risk', domain, reason: 'missing_abbreviation' });
    if (!severity || !(severity.textContent || '').trim()) issues.push({ kind: 'risk', domain, reason: 'missing_visible_severity' });
    if (domain) riskDomains.add(domain);
    const clip = shape ? getComputedStyle(shape).clipPath || '' : '';
    if (!clip || clip === 'none') issues.push({ kind: 'risk', domain, reason: 'risk_not_diamond', clipPath: clip });
  }
  return {
    event_count: events.length,
    candidate_count: candidates.length,
    risk_count: risks.length,
    event_domains: Array.from(eventDomains),
    risk_domains: Array.from(riskDomains),
    event_shape_signature_count: shapeSignatures.size,
    risk_severity_labels: risks.map((marker) => (marker.querySelector('.pj-marker__severity') || {}).textContent || ''),
    issues: issues.slice(0, 20),
  };
}
"""


@dataclass
class Collector:
    page_errors: List[str] = field(default_factory=list)
    console_errors: List[Dict[str, str]] = field(default_factory=list)
    http_requests: List[str] = field(default_factory=list)

    def attach(self, page: Page) -> None:
        page.on("pageerror", lambda exc: self.page_errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: self.console_errors.append({"type": msg.type, "text": msg.text})
            if msg.type == "error"
            else None,
        )
        page.on(
            "request",
            lambda req: self.http_requests.append(req.url)
            if req.url.startswith(("http://", "https://"))
            else None,
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_url() -> str:
    assert INDEX_HTML.is_file(), f"missing dashboard: {INDEX_HTML}"
    return INDEX_HTML.resolve().as_uri()


def _ensure_evidence_dirs() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / "screenshots").mkdir(parents=True, exist_ok=True)


def _browser_availability(pw: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name in list(REQUIRED_BROWSERS) + list(OPTIONAL_BROWSERS):
        browser_type = getattr(pw, name)
        exe = browser_type.executable_path
        out[name] = {"executable_path": exe, "exists": Path(exe).exists()}
    return out


def _launch(pw: Any, name: str) -> Browser:
    return getattr(pw, name).launch(headless=True)


def _new_page(browser: Browser, width: int, height: int, collector: Collector) -> Page:
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        reduced_motion="no-preference",
        locale="zh-CN",
    )
    page = context.new_page()
    collector.attach(page)
    page.goto(_file_url(), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(300)
    return page


def _shot(page: Page, name: str) -> Path:
    path = EVIDENCE_ROOT / "screenshots" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=True, type="png")
    return path


def _assert_shell_ready(page: Page) -> Dict[str, Any]:
    assert page.locator("#pj-shell").is_visible(), "pj-shell not visible"
    assert not page.locator("#pj-error").is_visible(), page.locator("#pj-error-body").inner_text()
    boundary = page.locator(".pj-boundary").inner_text()
    for token in REQUIRED_BOUNDARY_MARKERS:
        assert token in boundary, f"boundary missing read-only marker: {token}"
    body = page.locator("body").inner_text()
    for token in REQUIRED_BODY_MARKERS:
        assert token in body, f"body missing marker: {token}"
    for label in CHINESE_TABS:
        assert label in body, f"missing Chinese tab label: {label}"
    tab_texts = [t.strip() for t in page.locator(".pj-tab").all_inner_texts()]
    assert tab_texts == list(CHINESE_TABS), tab_texts
    return {
        "boundary": boundary,
        "tabs": tab_texts,
    }


def _journey_structure(page: Page) -> Dict[str, Any]:
    data = page.evaluate(JOURNEY_STRUCTURE_JS)
    paired = data.get("paired_nodes") or []
    paired_pass = bool(paired) and all(
        p.get("hasPlan") and p.get("hasActual") and p.get("titleHasBothDates") for p in paired
    )
    data["paired_pass"] = paired_pass
    data["pass"] = (
        int(data.get("lane_count") or 0) >= 4
        and bool(data.get("sticky_ruler"))
        and int(data.get("visit_marks") or 0) >= 1
        and len(data.get("duplicate_visit_codes") or []) == 0
        and len(data.get("smashed_labels") or []) == 0
        and len(data.get("adjacent_same_code_overlap") or []) == 0
        and paired_pass
        and int(data.get("unscheduled_count") or 0) >= 1
        and int((data.get("marker_counts") or {}).get("established_risk") or 0) >= 1
        and int((data.get("marker_counts") or {}).get("fact") or 0) >= 1
        and int((data.get("marker_counts") or {}).get("candidate") or 0) >= 1
        and REQUIRED_EVENT_DOMAINS.issubset(set((data.get("marker_domains") or {}).get("event") or []))
        and REQUIRED_EVENT_DOMAINS.issubset(set((data.get("marker_domains") or {}).get("event_legend") or []))
        and REQUIRED_RISK_LEGEND_DOMAINS.issubset(
            set((data.get("marker_domains") or {}).get("risk_legend") or [])
        )
        and "ae" in set((data.get("marker_domains") or {}).get("risk") or [])
        and len(data.get("legend_items") or []) >= 14
    )
    return data


def _shape_semantics(page: Page) -> Dict[str, Any]:
    data = page.evaluate(SHAPE_SEMANTICS_JS)
    legend = page.locator(".pj-legend-panel").inner_text()
    has_semantic_copy = all(
        tok in legend for tok in REQUIRED_EVENT_LEGEND_TOKENS + REQUIRED_RISK_LEGEND_TOKENS
    )
    leaked_backend_terms = [
        t
        for t in (
            "正式事实",
            "候选信号",
            "已建立风险",
            "正反证",
            "闭区间",
            "开放区间",
            "formal_fact",
            "established_risk",
        )
        if t in legend
    ]
    data["legend_text"] = legend
    data["legend_has_semantic_copy"] = has_semantic_copy
    data["legend_backend_term_leaks"] = leaked_backend_terms
    data["pass"] = (
        has_semantic_copy
        and len(leaked_backend_terms) == 0
        and int(data.get("event_count") or 0) >= 6
        and int(data.get("candidate_count") or 0) >= 1
        and int(data.get("risk_count") or 0) >= 1
        and REQUIRED_EVENT_DOMAINS.issubset(set(data.get("event_domains") or []))
        and "ae" in set(data.get("risk_domains") or [])
        and int(data.get("event_shape_signature_count") or 0) >= 6
        and all(str(label).strip() for label in (data.get("risk_severity_labels") or []))
        and len(data.get("issues") or []) == 0
    )
    return data


def _open_risk_evidence(page: Page) -> Dict[str, Any]:
    risk_marker = page.locator('.pj-marker[data-shape="established_risk"]').first
    assert risk_marker.count() >= 1, "no established_risk spatial marker"
    risk_id = risk_marker.get_attribute("data-risk") or ""
    event_id = risk_marker.get_attribute("data-event") or ""
    assert risk_id, "risk marker missing data-risk"
    risk_marker.scroll_into_view_if_needed()
    risk_marker.focus()
    risk_marker.click(timeout=10000)
    page.wait_for_timeout(200)
    assert page.locator("#pj-drawer-root").is_visible(), "evidence drawer did not open"
    body = page.locator("#pj-drawer-body").inner_text()
    assert "依据" in body or "发现" in body or "行动项" in body or "来源定位" in body
    for token in ("fixture_marker", "potential_unreported_", "spine_id", "identity_key", "MM_R1"):
        assert token not in body, f"drawer leaked {token}"
    # Cross-highlight on journey
    selected = page.locator(".pj-marker.is-selected, .pj-interval.is-selected, .pj-event-card.is-selected, .pj-risk-card.is-selected")
    return {
        "risk_id": risk_id,
        "event_id": event_id,
        "drawer_open": True,
        "drawer_has_query_or_locator": ("依据" in body or "来源定位" in body),
        "selected_count": selected.count(),
        "title": page.locator("#pj-drawer-title").inner_text(),
    }


def _check_focus_and_keyboard(page: Page) -> Dict[str, Any]:
    """Tablist arrows, Enter open, Escape close + focus restore, Tab trap."""
    # Arrow keys across Chinese tabs
    page.locator("#pj-tab-journey").focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(120)
    assert page.locator("#pj-tab-metrics").get_attribute("aria-selected") == "true"
    assert page.locator("#pj-panel-metrics").is_visible()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(100)
    assert page.locator("#pj-tab-events").get_attribute("aria-selected") == "true"
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(100)
    assert page.locator("#pj-tab-journey").get_attribute("aria-selected") == "true"

    # Enter opens evidence from risk diamond
    risk = page.locator('.pj-marker[data-shape="established_risk"]').first
    risk.focus()
    opener_risk = risk.get_attribute("data-risk") or ""
    opener_shape = risk.get_attribute("data-shape") or ""
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    assert page.locator("#pj-drawer-root").is_visible(), "Enter did not open drawer"

    close_btn = page.locator("#pj-drawer-close")
    assert close_btn.is_visible()
    page.wait_for_timeout(50)
    focused_id = page.evaluate("() => document.activeElement && document.activeElement.id")
    page.keyboard.press("Tab")
    page.wait_for_timeout(50)
    after_tab = page.evaluate(
        """() => {
          const el = document.activeElement;
          const drawer = document.getElementById('pj-drawer');
          return {
            id: el && el.id,
            inside: !!(el && drawer && drawer.contains(el)),
          };
        }"""
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(220)
    restored = page.evaluate(
        """() => {
          const el = document.activeElement;
          const drawerRoot = document.getElementById('pj-drawer-root');
          return {
            id: el && el.id,
            tag: el && el.tagName,
            action: el && el.getAttribute('data-action'),
            risk: el && el.getAttribute('data-risk'),
            shape: el && el.getAttribute('data-shape'),
            drawer_hidden: !!(drawerRoot && drawerRoot.hidden),
            is_pj_main: !!(el && el.id === 'pj-main'),
          };
        }"""
    )
    exact_opener = (
        restored.get("action") == "select-open"
        and restored.get("risk") == opener_risk
        and restored.get("shape") == opener_shape
        and restored.get("drawer_hidden")
        and not restored.get("is_pj_main")
    )
    return {
        "tab_arrows_ok": True,
        "enter_opened": True,
        "initial_focus_id": focused_id,
        "after_tab": after_tab,
        "trap_ok": bool(after_tab.get("inside")),
        "restored": restored,
        "restore_ok": bool(exact_opener),
        "opener_risk": opener_risk,
        "opener_shape": opener_shape,
    }


def _sync_time_window_and_selection(page: Page) -> Dict[str, Any]:
    """Shared spine selection + time window.

    Modal drawer backdrop intercepts pointer events on chrome/tabs (expected for
    ``aria-modal``). Selection sync is verified after Escape; window-filter
    survival uses forced control activation while the drawer remains open so the
    check targets app state, not overlay hit-testing.
    """
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(100)
    risk = page.locator('.pj-marker[data-shape="established_risk"]').first
    risk_id = risk.get_attribute("data-risk") or ""
    risk.click()
    page.wait_for_timeout(150)
    assert page.locator("#pj-drawer-root").is_visible()
    note_before = page.locator("#pj-window-note").inner_text()

    # Close drawer so tabs are pointer-reachable; selection must persist.
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    assert not page.locator("#pj-drawer-root").is_visible()

    page.locator("#pj-tab-metrics").click()
    page.wait_for_timeout(120)
    metrics_selected = page.locator("#pj-panel-metrics .is-selected").count()
    page.locator("#pj-tab-events").click()
    page.wait_for_timeout(120)
    events_selected = page.locator("#pj-panel-events .pj-event-card.is-selected").count()
    page.locator("#pj-tab-risks").click()
    page.wait_for_timeout(120)
    risks_selected = page.locator("#pj-panel-risks .pj-risk-card.is-selected").count()

    # Re-open evidence, then narrow window without auto-closing drawer.
    # Do not force-click chrome under the modal backdrop (that hits the
    # backdrop and closes the drawer). Drive controls via the DOM API.
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(80)
    page.locator('.pj-marker[data-shape="established_risk"]').first.click()
    page.wait_for_timeout(150)
    assert page.locator("#pj-drawer-root").is_visible()
    page.evaluate(
        """() => {
          const start = document.getElementById('pj-window-start');
          const end = document.getElementById('pj-window-end');
          const apply = document.getElementById('pj-window-apply');
          start.value = '2025-11-20';
          end.value = '2025-12-01';
          apply.click();
        }"""
    )
    page.wait_for_timeout(180)
    note_after = page.locator("#pj-window-note").inner_text()
    drawer_still = page.locator("#pj-drawer-root").is_visible()

    page.evaluate("() => document.getElementById('pj-window-reset').click()")
    page.wait_for_timeout(120)
    note_reset = page.locator("#pj-window-note").inner_text()

    page.evaluate(
        """() => {
          const axis = document.getElementById('pj-axis-mode');
          axis.value = 'study_day';
          axis.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(100)
    note_study = page.locator("#pj-window-note").inner_text()
    page.evaluate(
        """() => {
          const axis = document.getElementById('pj-axis-mode');
          axis.value = 'actual_date';
          axis.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(80)

    if page.locator("#pj-drawer-root").is_visible():
        page.keyboard.press("Escape")
        page.wait_for_timeout(120)
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(80)

    return {
        "risk_id": risk_id,
        "metrics_selected": metrics_selected,
        "events_selected": events_selected,
        "risks_selected": risks_selected,
        "selection_synced": metrics_selected >= 1 and events_selected >= 1 and risks_selected >= 1,
        "note_before": note_before,
        "note_after_narrow": note_after,
        "drawer_survived_window_filter": drawer_still,
        "note_mentions_not_closed": (
            "风险状态不受影响" in note_after
            or "风险状态不受影响" in note_before
            or "不会被自动结案" in note_after
            or "不会被自动结案" in note_before
        ),
        "note_reset": note_reset,
        "axis_study_day_note": note_study,
        "axis_switched": "研究日" in note_study,
        "modal_backdrop_blocks_tabs": True,
    }


def _forbidden_text_scan(page: Page) -> List[str]:
    """Scan visible text across all four Chinese tabs (audience surface)."""
    hits: List[str] = []
    for tab_id in ("pj-tab-journey", "pj-tab-metrics", "pj-tab-events", "pj-tab-risks"):
        page.locator(f"#{tab_id}").click()
        page.wait_for_timeout(80)
        visible = page.evaluate(
            """() => {
              const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              const parts = [];
              let n;
              while ((n = walker.nextNode())) {
                const parent = n.parentElement;
                if (!parent) continue;
                const tag = parent.tagName;
                if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') continue;
                if (parent.closest('[hidden]')) continue;
                const t = (n.textContent || '').trim();
                if (t) parts.push(t);
              }
              return parts.join('\\n');
            }"""
        )
        for token in FORBIDDEN_VISIBLE:
            key = f"forbidden_token:{token}"
            if token in visible and key not in hits:
                hits.append(key)
        for pat in FORBIDDEN_ID_PATTERNS:
            key = f"forbidden_pattern:{pat.pattern}"
            if pat.search(visible) and key not in hits:
                hits.append(key)
        if re.search(r"(?m)^(Profile|Timeline)$", visible):
            key = "forbidden_token:English_only_Profile_or_Timeline_tab"
            if key not in hits:
                hits.append(key)
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(60)
    return hits


def _reduced_motion_check(page: Page) -> Dict[str, Any]:
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(80)
    sample = page.evaluate(
        """() => {
          const els = Array.from(document.querySelectorAll('body, .pj-btn, .pj-tab, .pj-drawer, .pj-marker'))
            .slice(0, 14);
          return els.map((el) => {
            const cs = getComputedStyle(el);
            return {
              tag: el.tagName,
              className: String(el.className || '').slice(0, 60),
              animation: cs.animationName,
              transitionDuration: cs.transitionDuration,
            };
          });
        }"""
    )
    # Under prefers-reduced-motion, CSS sets animation:none and transition:none
    bad = [
        s
        for s in sample
        if (s.get("animation") and s["animation"] not in ("none",) and s["animation"] != "none")
        or (
            s.get("transitionDuration")
            and s["transitionDuration"] not in ("0s", "0s, 0s", "")
            and any(float(x.replace("s", "") or 0) > 0 for x in str(s["transitionDuration"]).split(","))
        )
    ]
    return {"sample": sample, "non_zero_motion": bad[:8], "pass": len(bad) == 0}


def _page_overflow(page: Page) -> Dict[str, Any]:
    data = page.evaluate(PAGE_OVERFLOW_JS)
    data["pass"] = int(data.get("horizontal_overflow") or 0) <= 0
    return data


def _capture_state_screenshots(page: Page, browser_name: str, vp_name: str) -> Dict[str, str]:
    paths: Dict[str, str] = {}
    # Journey overview (default)
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(120)
    if page.locator("#pj-drawer-root").is_visible():
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)
    paths["journey_overview"] = str(
        _shot(page, f"{browser_name}_{vp_name}_journey_overview").relative_to(WORKSPACE_ROOT)
    )

    # Risk / evidence panel
    risk = page.locator('.pj-marker[data-shape="established_risk"]').first
    if risk.count():
        risk.scroll_into_view_if_needed()
        risk.click()
        page.wait_for_timeout(180)
        assert page.locator("#pj-drawer-root").is_visible()
        paths["risk_evidence"] = str(
            _shot(page, f"{browser_name}_{vp_name}_risk_evidence").relative_to(WORKSPACE_ROOT)
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)

    # Metrics
    page.locator("#pj-tab-metrics").click()
    page.wait_for_timeout(150)
    paths["metrics"] = str(_shot(page, f"{browser_name}_{vp_name}_metrics").relative_to(WORKSPACE_ROOT))

    # Event details
    page.locator("#pj-tab-events").click()
    page.wait_for_timeout(150)
    paths["events"] = str(_shot(page, f"{browser_name}_{vp_name}_events").relative_to(WORKSPACE_ROOT))

    # Risks tab
    page.locator("#pj-tab-risks").click()
    page.wait_for_timeout(150)
    paths["risks_tab"] = str(_shot(page, f"{browser_name}_{vp_name}_risks_tab").relative_to(WORKSPACE_ROOT))

    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(80)
    return paths


def _capture_narrow(page: Page, browser_name: str) -> str:
    page.set_viewport_size({"width": NARROW_VIEWPORT[1], "height": NARROW_VIEWPORT[2]})
    page.wait_for_timeout(200)
    page.locator("#pj-tab-journey").click()
    page.wait_for_timeout(100)
    if page.locator("#pj-drawer-root").is_visible():
        page.keyboard.press("Escape")
        page.wait_for_timeout(80)
    path = _shot(page, f"{browser_name}_{NARROW_VIEWPORT[0]}_narrow")
    return str(path.relative_to(WORKSPACE_ROOT))


def run_browser_matrix() -> Dict[str, Any]:
    _ensure_evidence_dirs()
    summary: Dict[str, Any] = {
        "task_id": "medical_monitoring_r1_patient_journey_slice4_20260809",
        "role_id": "worker_03_round2",
        "pass_label": "post_visit_ruler_remediation",
        "generated_at": _utc_now(),
        "index_url": _file_url(),
        "playwright": "1.59.0",
        "browsers_required": list(REQUIRED_BROWSERS),
        "viewports": [name for name, _, _ in VIEWPORTS],
        "narrow_viewport": NARROW_VIEWPORT[0],
        "results": {},
        "defects": [],
        "environment": {},
        "overall_pass": True,
    }

    with sync_playwright() as pw:
        availability = _browser_availability(pw)
        summary["environment"]["browser_availability"] = availability
        runnable = [name for name in REQUIRED_BROWSERS if availability[name]["exists"]]
        missing_required = [name for name in REQUIRED_BROWSERS if not availability[name]["exists"]]
        summary["environment"]["runnable_browsers"] = runnable
        summary["environment"]["missing_required_browsers"] = missing_required
        if missing_required:
            summary["overall_pass"] = False
            for name in missing_required:
                summary["defects"].append(
                    {
                        "id": f"environment:missing_browser:{name}",
                        "check": "required_browser_executable",
                        "detail": {
                            "browser": name,
                            "executable_path": availability[name]["executable_path"],
                            "exists": False,
                            "smallest_setup": (
                                "From workspace root, with existing Playwright 1.59.0 only: "
                                f"`.venv/bin/python -m playwright install {name}`. "
                                "No other package install. Re-run this test file after."
                            ),
                        },
                    }
                )

        for browser_name in runnable:
            browser = _launch(pw, browser_name)
            try:
                for vp_name, width, height in VIEWPORTS:
                    key = f"{browser_name}:{vp_name}"
                    collector = Collector()
                    page = _new_page(browser, width, height, collector)
                    result: Dict[str, Any] = {
                        "browser": browser_name,
                        "viewport": {"name": vp_name, "width": width, "height": height},
                        "pass": True,
                        "failures": [],
                    }
                    try:
                        shell_info = _assert_shell_ready(page)
                        result["shell"] = shell_info
                        structure = _journey_structure(page)
                        result["journey_structure"] = structure
                        if not structure.get("pass"):
                            result["failures"].append("journey_structure")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:journey_structure",
                                    "browser": browser_name,
                                    "viewport": vp_name,
                                    "check": "shared_visit_axis_lanes_markers",
                                    "detail": structure,
                                }
                            )

                        shapes = _shape_semantics(page)
                        result["shape_semantics"] = shapes
                        if not shapes.get("pass"):
                            result["failures"].append("shape_semantics")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:shape_semantics",
                                    "browser": browser_name,
                                    "viewport": vp_name,
                                    "check": "non_color_only_marker_semantics",
                                    "detail": shapes,
                                }
                            )

                        if vp_name == "1280x800":
                            focus_info = _check_focus_and_keyboard(page)
                            result["keyboard_focus"] = focus_info
                            if not focus_info.get("trap_ok"):
                                result["failures"].append("drawer_focus_trap_failed")
                            if not focus_info.get("restore_ok"):
                                result["failures"].append("drawer_focus_restore_failed")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:focus_restore",
                                        "browser": browser_name,
                                        "viewport": vp_name,
                                        "check": "escape_restores_opener",
                                        "detail": focus_info,
                                    }
                                )

                            sync = _sync_time_window_and_selection(page)
                            result["sync_state"] = sync
                            if not sync.get("selection_synced"):
                                result["failures"].append("selection_not_synced_across_tabs")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:selection_sync",
                                        "check": "shared_selection_across_tabs",
                                        "detail": sync,
                                    }
                                )
                            if not sync.get("drawer_survived_window_filter"):
                                result["failures"].append("window_filter_closed_drawer")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:window_filter_drawer",
                                        "check": "window_filter_must_not_close_drawer",
                                        "detail": sync,
                                    }
                                )
                            if not sync.get("axis_switched"):
                                result["failures"].append("axis_mode_note_not_updated")

                            evidence = _open_risk_evidence(page)
                            result["risk_evidence"] = evidence
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(120)

                            result["reduced_motion"] = _reduced_motion_check(page)
                            if not result["reduced_motion"].get("pass"):
                                result["failures"].append("reduced_motion_not_honored")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:reduced_motion",
                                        "check": "prefers_reduced_motion",
                                        "detail": result["reduced_motion"],
                                    }
                                )

                            # Narrow state screenshot once per browser
                            result["narrow_screenshot"] = _capture_narrow(page, browser_name)
                            # Restore viewport for remaining checks
                            page.set_viewport_size({"width": width, "height": height})
                            page.wait_for_timeout(120)

                        shots = _capture_state_screenshots(page, browser_name, vp_name)
                        result["screenshots"] = shots

                        overflow = _page_overflow(page)
                        result["page_overflow"] = overflow
                        if not overflow.get("pass"):
                            result["failures"].append("horizontal_page_overflow")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:horizontal_page_overflow",
                                    "browser": browser_name,
                                    "viewport": vp_name,
                                    "check": "horizontal_page_overflow",
                                    "detail": overflow,
                                }
                            )

                        forbidden = _forbidden_text_scan(page)
                        result["forbidden_text_hits"] = forbidden
                        if forbidden:
                            result["failures"].append("forbidden_visible_text")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:forbidden_text",
                                    "browser": browser_name,
                                    "viewport": vp_name,
                                    "check": "audience_language_scan",
                                    "detail": forbidden,
                                }
                            )

                        if collector.page_errors:
                            result["failures"].append("page_errors")
                            summary["defects"].append(
                                {"id": f"{key}:page_errors", "detail": collector.page_errors}
                            )
                        if collector.console_errors:
                            result["failures"].append("console_errors")
                            summary["defects"].append(
                                {"id": f"{key}:console_errors", "detail": collector.console_errors}
                            )
                        if collector.http_requests:
                            result["failures"].append("http_requests")
                            summary["defects"].append(
                                {"id": f"{key}:http_requests", "detail": collector.http_requests}
                            )

                        result["telemetry"] = {
                            "page_errors": collector.page_errors,
                            "console_errors": collector.console_errors,
                            "http_requests": collector.http_requests,
                        }
                    except Exception as exc:  # noqa: BLE001
                        result["failures"].append(f"exception:{type(exc).__name__}:{exc}")
                        summary["defects"].append(
                            {
                                "id": f"{key}:exception",
                                "browser": browser_name,
                                "viewport": vp_name,
                                "check": "interaction_or_runtime",
                                "detail": str(exc),
                            }
                        )
                    finally:
                        result["pass"] = len(result["failures"]) == 0
                        if not result["pass"]:
                            summary["overall_pass"] = False
                        summary["results"][key] = result
                        page.context.close()
            finally:
                browser.close()

    QC_SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


@pytest.fixture(scope="module")
def qc_summary() -> Dict[str, Any]:
    return run_browser_matrix()


def test_required_browsers_available(qc_summary: Dict[str, Any]):
    missing = (qc_summary.get("environment") or {}).get("missing_required_browsers") or []
    assert not missing, {
        "missing_required_browsers": missing,
        "availability": (qc_summary.get("environment") or {}).get("browser_availability"),
        "smallest_setup": ".venv/bin/python -m playwright install webkit",
    }


def test_browser_qc_matrix_writes_summary(qc_summary: Dict[str, Any]):
    assert QC_SUMMARY_PATH.is_file(), f"missing QC summary: {QC_SUMMARY_PATH}"
    runnable = (qc_summary.get("environment") or {}).get("runnable_browsers") or []
    assert runnable, "no required browser executable available"
    for browser in runnable:
        for vp_name, _, _ in VIEWPORTS:
            key = f"{browser}:{vp_name}"
            assert key in qc_summary["results"], f"missing matrix cell {key}"


def test_no_page_console_http_errors(qc_summary: Dict[str, Any]):
    failures = []
    for key, result in qc_summary["results"].items():
        tel = result.get("telemetry") or {}
        if tel.get("page_errors"):
            failures.append((key, "page_errors", tel["page_errors"]))
        if tel.get("console_errors"):
            failures.append((key, "console_errors", tel["console_errors"]))
        if tel.get("http_requests"):
            failures.append((key, "http_requests", tel["http_requests"]))
    assert not failures, failures


def test_required_screenshots_exist(qc_summary: Dict[str, Any]):
    required_states = ("journey_overview", "risk_evidence", "metrics", "events")
    missing = []
    for key, result in qc_summary["results"].items():
        shots = result.get("screenshots") or {}
        for state in required_states:
            rel = shots.get(state)
            if not rel:
                missing.append((key, state, "missing_key"))
                continue
            path = WORKSPACE_ROOT / rel
            if not path.is_file() or path.stat().st_size < 1000:
                missing.append((key, state, str(path)))
        if key.endswith(":1280x800"):
            narrow = result.get("narrow_screenshot")
            if not narrow or not (WORKSPACE_ROOT / narrow).is_file():
                missing.append((key, "narrow", narrow or "missing"))
    assert not missing, missing


def test_journey_structure_and_semantics(qc_summary: Dict[str, Any]):
    failed = []
    for key, result in qc_summary["results"].items():
        struct = result.get("journey_structure") or {}
        if not struct.get("pass"):
            failed.append({"cell": key, "check": "journey_structure", "detail": struct})
        shapes = result.get("shape_semantics") or {}
        if not shapes.get("pass"):
            failed.append({"cell": key, "check": "shape_semantics", "detail": shapes})
        overflow = result.get("page_overflow") or {}
        if overflow and not overflow.get("pass"):
            failed.append({"cell": key, "check": "horizontal_page_overflow", "detail": overflow})
        if result.get("forbidden_text_hits"):
            failed.append(
                {
                    "cell": key,
                    "check": "audience_language",
                    "detail": result.get("forbidden_text_hits"),
                }
            )
    assert not failed, json.dumps(failed, ensure_ascii=False, indent=2)[:8000]


def test_interactions_and_a11y_gates(qc_summary: Dict[str, Any]):
    failed = []
    for key, result in qc_summary["results"].items():
        if not key.endswith(":1280x800"):
            continue
        for token in result.get("failures") or []:
            if token in {
                "journey_structure",
                "shape_semantics",
                "horizontal_page_overflow",
                "forbidden_visible_text",
            }:
                continue
            failed.append(
                {
                    "cell": key,
                    "failure": token,
                    "keyboard": result.get("keyboard_focus"),
                    "sync": result.get("sync_state"),
                    "reduced_motion": result.get("reduced_motion"),
                }
            )
    assert not failed, failed


def test_overall_browser_qc_pass(qc_summary: Dict[str, Any]):
    assert qc_summary.get("overall_pass") is True, {
        "defects": qc_summary.get("defects"),
        "failure_cells": {
            k: v.get("failures") for k, v in qc_summary.get("results", {}).items() if not v.get("pass")
        },
    }


if __name__ == "__main__":
    summary = run_browser_matrix()
    print(
        json.dumps(
            {
                "overall_pass": summary["overall_pass"],
                "defect_count": len(summary["defects"]),
                "path": str(QC_SUMMARY_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
