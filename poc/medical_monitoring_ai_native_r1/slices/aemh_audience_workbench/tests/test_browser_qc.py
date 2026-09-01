"""Playwright browser + §16.4 visual QC for Slice 3 AE/MH audience workbench.

Authorized worker-03 artifact. Opens the dashboard via absolute ``file://`` only.
Does not start a server and does not install packages.

Run with:
    .venv/bin/python -m pytest -q \\
      poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/tests/test_browser_qc.py

Evidence root (authorized):
    output/playwright/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/
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
# aemh_audience_workbench -> slices -> medical_monitoring_ai_native_r1 -> poc -> workbench
WORKSPACE_ROOT = SLICE_ROOT.parents[3]
assert (WORKSPACE_ROOT / "poc").is_dir(), f"workspace root misdetected: {WORKSPACE_ROOT}"
EVIDENCE_ROOT = (
    WORKSPACE_ROOT
    / "output"
    / "playwright"
    / "medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809"
)
QC_SUMMARY_PATH = EVIDENCE_ROOT / "qc_summary.json"

VIEWPORTS: Sequence[Tuple[str, int, int]] = (
    ("1280x800", 1280, 800),
    ("1440x900", 1440, 900),
    ("1920x1080", 1920, 1080),
    ("2048x1024", 2048, 1024),
)
REQUIRED_BROWSERS = ("chromium", "webkit")
OPTIONAL_BROWSERS = ("firefox",)

FORBIDDEN_VISIBLE = (
    "&&",
    "@@",
    "${",
    "AI自动判断",
    "AI替代医学判断",
    "passed",
    "potential_unreported_",
    "temporal_spine_id",
    "shape=",
    "line=",
    "file://",
    "worker 01",
    "build_data.py",
    "正式事实",
    "正式 AE/MH 事实",
    "候选信号",
    "漏报候选",
    "非正式候选",
    "只读",
    "Profile",
    "Timeline",
)
FORBIDDEN_ID_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\bNCT\d{8}\b", re.I),
    re.compile(r"\b(?:fact|candidate|query|risk)_[0-9a-f]{16,}\b", re.I),
    re.compile(r"\b[0-9a-f]{40,64}\b", re.I),
)

BARE_SHAPE_LABEL = re.compile(
    r"^(红色?菱形|蓝色?圆|方块|圆形|菱形|red diamond|blue circle|square)$",
    re.I,
)

TEXT_OVERFLOW_JS = r"""
() => {
  const selectors = [
    'p','li','h1','h2','h3','h4','h5','h6','span','td','th','label','button',
    'a','dt','dd','pre','code','.kz-pill','.kz-stat__label','.kz-stat__value',
    '.kz-risk-card__concept','.kz-risk-card__meta','.kz-legend__item',
    '.kz-timeline__title','.kz-timeline__detail','.kz-timeline__date',
    '.kz-chrome__title','.kz-chrome__eyebrow','.kz-section-label',
    '.kz-empty__title','.kz-empty__body','.kz-panel__title','.kz-panel__sub'
  ].join(',');
  const out = [];
  const seen = new Set();
  for (const el of document.querySelectorAll(selectors)) {
    if (seen.has(el)) continue;
    seen.add(el);
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
    if (el.closest('[hidden]')) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) continue;
    const text = (el.innerText || el.textContent || '').trim();
    if (!text) continue;
    const sw = el.scrollWidth;
    const cw = el.clientWidth;
    const sh = el.scrollHeight;
    const ch = el.clientHeight;
    if (sw > cw + 1 || sh > ch + 1) {
      out.push({
        tag: el.tagName.toLowerCase(),
        className: String(el.className || '').slice(0, 120),
        id: el.id || '',
        scrollWidth: sw,
        clientWidth: cw,
        scrollHeight: sh,
        clientHeight: ch,
        overflowX: sw - cw,
        overflowY: sh - ch,
        text: text.slice(0, 80),
      });
    }
  }
  for (const textEl of document.querySelectorAll('svg text')) {
    try {
      const svg = textEl.ownerSVGElement;
      if (!svg) continue;
      const vb = svg.viewBox && svg.viewBox.baseVal;
      const bbox = textEl.getBBox();
      if (vb && vb.width > 0 && bbox.x + bbox.width > vb.width + 0.5) {
        out.push({
          tag: 'svg>text',
          className: '',
          id: textEl.id || '',
          scrollWidth: bbox.width,
          clientWidth: vb.width,
          scrollHeight: bbox.height,
          clientHeight: vb.height,
          overflowX: bbox.x + bbox.width - vb.width,
          overflowY: 0,
          text: (textEl.textContent || '').slice(0, 80),
        });
      }
    } catch (e) { /* ignore detached */ }
  }
  return out;
}
"""

SVG_QC_JS = r"""
() => {
  const svgs = Array.from(document.querySelectorAll('svg')).filter((svg) => {
    if (svg.closest('[hidden]')) return false;
    const cs = getComputedStyle(svg);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = svg.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
  const overlaps = [];
  const markerIssues = [];
  const textSvgOverlaps = [];
  const shapeSel = 'rect,circle,ellipse,polygon,path';
  for (const svg of svgs) {
    const nodes = [];
    for (const el of svg.querySelectorAll('text,' + shapeSel)) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      try {
        const b = el.getBBox();
        if (b.width <= 0 && b.height <= 0) continue;
        nodes.push({ el, tag: el.tagName.toLowerCase(), bbox: b });
      } catch (e) { /* skip */ }
    }
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        // Exempt line-like paths and background/containment heuristics lightly:
        if (a.tag === 'path' || b.tag === 'path') continue;
        const x1 = Math.max(a.bbox.x, b.bbox.x);
        const y1 = Math.max(a.bbox.y, b.bbox.y);
        const x2 = Math.min(a.bbox.x + a.bbox.width, b.bbox.x + b.bbox.width);
        const y2 = Math.min(a.bbox.y + a.bbox.height, b.bbox.y + b.bbox.height);
        const area = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
        if (area > 0.5) {
          overlaps.push({
            area,
            a: a.tag,
            b: b.tag,
            aText: (a.el.textContent || '').slice(0, 40),
            bText: (b.el.textContent || '').slice(0, 40),
          });
        }
      }
    }
    const vb = svg.viewBox && svg.viewBox.baseVal;
    for (const n of nodes) {
      if (!['circle', 'polygon', 'ellipse'].includes(n.tag) && !(n.tag === 'path' && /diamond|marker/i.test(n.el.getAttribute('class') || ''))) {
        continue;
      }
      if (!vb) continue;
      const cx = n.bbox.x + n.bbox.width / 2;
      const cy = n.bbox.y + n.bbox.height / 2;
      if (cx < -0.5 || cy < -0.5 || cx > vb.width + 0.5 || cy > vb.height + 0.5) {
        markerIssues.push({ reason: 'outside_viewBox', tag: n.tag, cx, cy });
      }
    }
  }

  // Text block vs SVG element bbox (screen space)
  const textBlocks = Array.from(document.querySelectorAll(
    'h1,h2,h3,.kz-panel__title,.kz-risk-card__concept,.content-conclusion,caption,figcaption'
  )).filter((el) => !el.closest('svg') && !el.closest('[hidden]') && el.getBoundingClientRect().width > 0);
  for (const svg of svgs) {
    const svgRect = svg.getBoundingClientRect();
    for (const tel of svg.querySelectorAll('text')) {
      let tb;
      try { tb = tel.getBoundingClientRect(); } catch (e) { continue; }
      for (const block of textBlocks) {
        // Skip if the text block is the SVG host container's title outside overlap intent:
        const br = block.getBoundingClientRect();
        // Ignore title that is ancestor/sibling chrome far from svg
        const x1 = Math.max(br.left, tb.left);
        const y1 = Math.max(br.top, tb.top);
        const x2 = Math.min(br.right, tb.right);
        const y2 = Math.min(br.bottom, tb.bottom);
        const area = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
        if (area > 0.5) {
          textSvgOverlaps.push({
            area,
            text: (block.innerText || '').slice(0, 60),
            svgText: (tel.textContent || '').slice(0, 60),
          });
        }
      }
    }
  }
  return {
    svg_count: svgs.length,
    svg_internal_overlaps: overlaps.slice(0, 40),
    marker_anchor_issues: markerIssues.slice(0, 40),
    text_vs_svg_overlaps: textSvgOverlaps.slice(0, 40),
  };
}
"""

LEGEND_QC_JS = r"""
() => {
  const legends = Array.from(document.querySelectorAll('.kz-legend'));
  const items = [];
  const failures = [];
  for (const legend of legends) {
    if (legend.closest('[hidden]')) continue;
    const entries = legend.querySelectorAll('.kz-legend__item, [role="listitem"], li');
    const nodes = entries.length ? entries : [legend];
    for (const node of nodes) {
      const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
      if (!text) continue;
      items.push(text);
      const bare = /^(红色?菱形|蓝色?圆|方块|圆形|菱形|red diamond|blue circle|square)$/i.test(text);
      const hasSemantic = /=|：|:|事实|候选|风险|缺口|里程碑|红线|正式|非正式|历史/.test(text);
      if (bare || !hasSemantic) {
        failures.push({ text, reason: bare ? 'bare_shape_name' : 'missing_semantic_equation' });
      }
    }
  }
  return { legend_count: legends.length, items, failures };
}
"""

HTML_MARKER_QC_JS = r"""
() => {
  // Non-SVG decorative markers used by this dashboard (timeline dots / swatches).
  const markers = Array.from(document.querySelectorAll('.kz-timeline__marker, .kz-swatch'));
  const issues = [];
  for (const m of markers) {
    if (m.closest('[hidden]')) continue;
    const cs = getComputedStyle(m);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = m.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) {
      issues.push({ reason: 'zero_size_marker', className: String(m.className || '') });
      continue;
    }
    // Timeline markers anchor to the shared rail (.kz-timeline), not the padded item text box.
    // Legend swatches anchor to their legend row.
    const host = m.classList.contains('kz-timeline__marker')
      ? m.closest('.kz-timeline')
      : m.closest('.kz-legend__item, .kz-legend');
    if (!host) {
      issues.push({ reason: 'marker_without_host', className: String(m.className || '') });
      continue;
    }
    const hr = host.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    // Allow 2px float tolerance (design.md marker snap).
    if (cx < hr.left - 2 || cx > hr.right + 2 || cy < hr.top - 2 || cy > hr.bottom + 2) {
      issues.push({
        reason: 'marker_outside_host',
        className: String(m.className || ''),
        cx, cy,
        host: { left: hr.left, right: hr.right, top: hr.top, bottom: hr.bottom },
      });
    }
  }
  return { marker_count: markers.length, issues: issues.slice(0, 40) };
}
"""

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
    """Probe local Playwright browser executables without installing."""
    out: Dict[str, Any] = {}
    for name in list(REQUIRED_BROWSERS) + list(OPTIONAL_BROWSERS):
        browser_type = getattr(pw, name)
        exe = browser_type.executable_path
        out[name] = {
            "executable_path": exe,
            "exists": Path(exe).exists(),
        }
    return out


def _launch(pw: Any, name: str) -> Browser:
    browser_type = getattr(pw, name)
    return browser_type.launch(headless=True)


def _new_page(browser: Browser, width: int, height: int, collector: Collector) -> Page:
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        reduced_motion="no-preference",
    )
    page = context.new_page()
    collector.attach(page)
    page.goto(_file_url(), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(250)
    return page


def _shot(page: Page, name: str) -> Path:
    path = EVIDENCE_ROOT / "screenshots" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=True, type="png")
    return path


def _visible(page: Page, selector: str):
    return page.locator(f"{selector} >> visible=true")


def _assert_shell_ready(page: Page) -> None:
    assert page.locator("#kz-shell").is_visible(), "kz-shell not visible"
    assert not page.locator("#kz-error").is_visible(), page.locator("#kz-error-body").inner_text()
    assert page.locator(".kz-boundary strong").inner_text().strip() == "AI辅助定位证据与风险，医学经理终审"
    assert "SYNTHETIC" in page.locator("body").inner_text()
    assert not page.locator("#kz-progress-detail").get_attribute("open")
    assert "已完成" in page.locator("#kz-progress-current").inner_text()


def _open_evidence_drawer(page: Page) -> None:
    btn = _visible(page, "#kz-view-project [data-action='evidence']").first
    assert btn.count() >= 1 or _visible(page, "[data-action='evidence']").count() >= 1
    target = btn if btn.count() else _visible(page, "[data-action='evidence']").first
    target.scroll_into_view_if_needed()
    target.click(timeout=10000)
    page.wait_for_timeout(150)
    assert page.locator("#kz-drawer-root").is_visible(), "evidence drawer did not open"
    body = page.locator("#kz-drawer-body").inner_text()
    assert "SYNTHETIC|" in body or "来源" in body or "locator" in body.lower() or "source" in body.lower() or "表" in body
    for token in ("fixture_marker", "candidate_signal", "potential_unreported", "risk identity"):
        assert token not in body


def _close_drawer_escape(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(120)
    assert not page.locator("#kz-drawer-root").is_visible(), "Escape did not close drawer"


def _check_focus_trap(page: Page) -> Dict[str, Any]:
    """Open drawer and verify Tab cycles inside dialog; Escape restores opener focus.

    ``restore_ok`` requires the active element after Escape to be the exact
    evidence opener (``data-action=evidence`` and matching ``data-identity``).
    Landing on ``#kz-main`` or any other non-opener is a fail.
    """
    opener = _visible(page, "#kz-view-project [data-action='evidence']").first
    opener.focus()
    opener_handle = opener.evaluate("el => el.getAttribute('data-identity') || ''")
    assert opener_handle, "evidence opener missing data-identity"
    opener.click()
    page.wait_for_timeout(150)
    close_btn = page.locator("#kz-drawer-close")
    assert close_btn.is_visible()
    # Focus should move into drawer (close button is default focus target)
    focused = page.evaluate("() => document.activeElement && document.activeElement.id")
    page.keyboard.press("Tab")
    page.wait_for_timeout(50)
    after_tab = page.evaluate(
        """() => {
          const el = document.activeElement;
          const drawer = document.getElementById('kz-drawer');
          return {
            id: el && el.id,
            tag: el && el.tagName,
            inside: !!(el && drawer && drawer.contains(el)),
          };
        }"""
    )
    page.keyboard.press("Escape")
    # Escape uses deferred focus restore (setTimeout 0); wait past that tick.
    page.wait_for_timeout(200)
    restored = page.evaluate(
        """() => {
          const el = document.activeElement;
          const drawer = document.getElementById('kz-drawer');
          const drawerRoot = document.getElementById('kz-drawer-root');
          return {
            id: el && el.id,
            tag: el && el.tagName,
            action: el && el.getAttribute('data-action'),
            identity: el && el.getAttribute('data-identity'),
            inside_drawer: !!(el && drawer && drawer.contains(el)),
            drawer_hidden: !!(drawerRoot && drawerRoot.hidden),
            is_kz_main: !!(el && el.id === 'kz-main'),
          };
        }"""
    )
    exact_opener = (
        restored.get("action") == "evidence"
        and restored.get("identity") == opener_handle
        and not restored.get("inside_drawer")
        and not restored.get("is_kz_main")
    )
    return {
        "opener": opener_handle,
        "initial_focus_id": focused,
        "after_tab": after_tab,
        "restored": restored,
        "trap_ok": bool(after_tab.get("inside")),
        "restore_ok": bool(exact_opener),
        "restore_landed_on_kz_main": bool(restored.get("is_kz_main")),
    }


def _measure_disclaimer_font(page: Page) -> Dict[str, Any]:
    """Assert `.kz-boundary__disclaimer` computed font-size is at least 16px."""
    measured = page.evaluate(
        """() => {
          const el = document.querySelector('.kz-boundary__disclaimer');
          if (!el) return { found: false };
          const cs = getComputedStyle(el);
          const px = parseFloat(cs.fontSize);
          return {
            found: true,
            font_size_px: px,
            font_size_css: cs.fontSize,
            text_sample: (el.textContent || '').trim().slice(0, 80),
          };
        }"""
    )
    font_px = float(measured.get("font_size_px") or 0) if measured.get("found") else 0.0
    return {
        **measured,
        "min_required_px": 16,
        "pass": bool(measured.get("found")) and font_px >= 16.0 - 1e-6,
    }


def _drill_site_subject(page: Page) -> Dict[str, Any]:
    site_btn = _visible(page, ".kz-site-card[data-action='site']").first
    site_id = site_btn.get_attribute("data-site")
    site_btn.click()
    page.wait_for_timeout(150)
    assert page.locator("#kz-view-site").is_visible(), "site view not visible"
    subject_btn = _visible(page, "#kz-view-site .kz-site-card[data-action='subject']").first
    subject_id = subject_btn.get_attribute("data-subject")
    subject_btn.click()
    page.wait_for_timeout(180)
    assert page.locator("#kz-view-subject").is_visible(), "subject view not visible"
    assert page.locator("#kz-tab-profile").get_attribute("aria-selected") == "true"
    spine_note = page.locator(".kz-window__note").inner_text()
    assert "访视" in spine_note and "时间轴" in spine_note
    subject_text = page.locator("#kz-view-subject").inner_text()
    for token in ("temporal_spine_id", "shape=", "line=", "potential_unreported_"):
        assert token not in subject_text

    # Keyboard tab switch Profile -> Timeline
    page.locator("#kz-tab-profile").focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(150)
    assert page.locator("#kz-tab-timeline").get_attribute("aria-selected") == "true"
    assert page.locator(".kz-timeline, .kz-timeline__item, .kz-section-label").count() >= 1

    # Shared time window apply / clear
    start = page.locator("#kz-window-start")
    end = page.locator("#kz-window-end")
    if start.count() and end.count():
        start.fill("2000-01-01")
        end.fill("2099-12-31")
        page.locator("#kz-window-apply").click()
        page.wait_for_timeout(120)
        page.locator("#kz-window-clear").click()
        page.wait_for_timeout(120)

    # Locator / source drill from timeline when present
    locator_btn = page.locator("#kz-view-subject [data-action='locator']")
    locator_opened = False
    if locator_btn.count():
        vis = page.locator("#kz-view-subject [data-action='locator'] >> visible=true")
        if vis.count():
            vis.first.click()
            page.wait_for_timeout(150)
            locator_opened = page.locator("#kz-drawer-root").is_visible()
            if locator_opened:
                page.keyboard.press("Escape")
                page.wait_for_timeout(100)

    # Query from subject risk cards
    query_opened = False
    qbtn = page.locator("#kz-view-subject [data-action='query'] >> visible=true")
    if qbtn.count():
        qbtn.first.scroll_into_view_if_needed()
        qbtn.first.click()
        page.wait_for_timeout(150)
        query_opened = page.locator("#kz-drawer-root").is_visible()
        if query_opened:
            text = page.locator("#kz-drawer-body").inner_text()
            assert "依据" in text or "发现" in text or "行动" in text or page.locator(".kz-query-part").count() >= 1
            page.keyboard.press("Escape")
            page.wait_for_timeout(100)

    # Context-preserving back: subject -> site -> project
    page.locator("#kz-back").click()
    page.wait_for_timeout(120)
    assert page.locator("#kz-view-site").is_visible(), "back from subject did not restore site"
    crumb = page.locator("#kz-crumb").inner_text()
    assert site_id in crumb or "中心" in crumb
    page.locator("#kz-back").click()
    page.wait_for_timeout(120)
    assert page.locator("#kz-view-project").is_visible(), "back from site did not restore project"

    return {
        "site_id": site_id,
        "subject_id": subject_id,
        "locator_opened": locator_opened,
        "query_opened": query_opened,
    }


def _empty_state_reset(page: Page) -> None:
    page.select_option("#kz-filter-severity", "severe")
    page.fill("#kz-filter-q", "ZZZ-NO-MATCH-WORKER03")
    page.wait_for_timeout(150)
    assert page.locator("#kz-empty").is_visible(), "empty state not shown for impossible filter"
    page.locator("#kz-empty-reset").click()
    page.wait_for_timeout(150)
    assert not page.locator("#kz-empty").is_visible(), "empty reset failed"
    assert page.locator("#kz-view-project").is_visible()
    assert page.locator("#kz-filter-q").input_value() == ""
    assert page.locator("#kz-filter-severity").input_value() == "all"


def _forbidden_text_scan(page: Page) -> List[str]:
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
    hits: List[str] = []
    for token in FORBIDDEN_VISIBLE:
        if token in visible:
            hits.append(f"forbidden_token:{token}")
    for pat in FORBIDDEN_ID_PATTERNS:
        if pat.search(visible):
            hits.append(f"forbidden_pattern:{pat.pattern}")
    return hits


def _reduced_motion_check(page: Page) -> Dict[str, Any]:
    page.emulate_media(reduced_motion="reduce")
    page.evaluate("() => { document.documentElement.setAttribute('data-qc','true'); }")
    page.wait_for_timeout(80)
    sample = page.evaluate(
        """() => {
          const els = Array.from(document.querySelectorAll('body, .kz-btn, .kz-site-card, .kz-drawer'))
            .slice(0, 12);
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
    return {"sample": sample, "data_qc": page.evaluate("() => document.documentElement.getAttribute('data-qc')")}


def _run_section16_4(page: Page) -> Dict[str, Any]:
    text_overflows = page.evaluate(TEXT_OVERFLOW_JS)
    svg_qc = page.evaluate(SVG_QC_JS)
    legend_qc = page.evaluate(LEGEND_QC_JS)
    html_markers = page.evaluate(HTML_MARKER_QC_JS)
    page_overflow = page.evaluate(PAGE_OVERFLOW_JS)

    svg_count = int(svg_qc.get("svg_count") or 0)
    checks = {
        "text_overflow_per_node": {
            "pass": len(text_overflows) == 0,
            "failure_count": len(text_overflows),
            "samples": text_overflows[:15],
        },
        "svg_internal_no_overlap": {
            "pass": (svg_count == 0) or (len(svg_qc.get("svg_internal_overlaps") or []) == 0),
            "svg_count": svg_count,
            "zero_svg_observation": svg_count == 0,
            "failure_count": len(svg_qc.get("svg_internal_overlaps") or []),
            "samples": (svg_qc.get("svg_internal_overlaps") or [])[:10],
            "note": "explicit zero-SVG observation; HTML CSS markers used instead"
            if svg_count == 0
            else "",
        },
        "marker_snapped_to_anchor": {
            "pass": (
                len(svg_qc.get("marker_anchor_issues") or []) == 0
                and len(html_markers.get("issues") or []) == 0
            ),
            "svg_marker_issues": svg_qc.get("marker_anchor_issues") or [],
            "html_marker_count": html_markers.get("marker_count"),
            "html_marker_issues": html_markers.get("issues") or [],
            "zero_svg_observation": svg_count == 0,
        },
        "legend_semantic_labels": {
            "pass": len(legend_qc.get("failures") or []) == 0 and int(legend_qc.get("legend_count") or 0) >= 1,
            "legend_count": legend_qc.get("legend_count"),
            "items": legend_qc.get("items") or [],
            "failures": legend_qc.get("failures") or [],
        },
        "text_vs_svg_overlap": {
            "pass": (svg_count == 0) or (len(svg_qc.get("text_vs_svg_overlaps") or []) == 0),
            "svg_count": svg_count,
            "zero_svg_observation": svg_count == 0,
            "failure_count": len(svg_qc.get("text_vs_svg_overlaps") or []),
            "samples": (svg_qc.get("text_vs_svg_overlaps") or [])[:10],
        },
    }
    return {
        "page_overflow": page_overflow,
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks.values())
        and int(page_overflow.get("horizontal_overflow") or 0) <= 0,
    }


def _merge_section_results(
    project: Dict[str, Any], timeline: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """AND-merge project and timeline §16.4 observations into one gate result."""
    if not timeline:
        return project
    merged_checks: Dict[str, Any] = {}
    for name, proj_check in project["checks"].items():
        tl_check = timeline["checks"][name]
        merged = {
            "pass": bool(proj_check.get("pass")) and bool(tl_check.get("pass")),
            "project": proj_check,
            "timeline": tl_check,
        }
        # Prefer timeline marker/svg counts when present.
        for key in (
            "svg_count",
            "zero_svg_observation",
            "html_marker_count",
            "failure_count",
            "legend_count",
            "note",
        ):
            if key in tl_check:
                merged[key] = tl_check[key]
            elif key in proj_check:
                merged[key] = proj_check[key]
        if not merged["pass"]:
            merged["samples"] = (proj_check.get("samples") or [])[:8] + (tl_check.get("samples") or [])[:8]
            merged["failures"] = (proj_check.get("failures") or []) + (tl_check.get("failures") or [])
            merged["html_marker_issues"] = (proj_check.get("html_marker_issues") or []) + (
                tl_check.get("html_marker_issues") or []
            )
        merged_checks[name] = merged
    overflow = {
        "project": project.get("page_overflow"),
        "timeline": timeline.get("page_overflow"),
        "horizontal_overflow": max(
            int((project.get("page_overflow") or {}).get("horizontal_overflow") or 0),
            int((timeline.get("page_overflow") or {}).get("horizontal_overflow") or 0),
        ),
    }
    return {
        "page_overflow": overflow,
        "checks": merged_checks,
        "all_pass": all(c["pass"] for c in merged_checks.values())
        and overflow["horizontal_overflow"] <= 0,
    }


def _capture_state_screenshots(page: Page, browser_name: str, vp_name: str) -> Dict[str, str]:
    paths: Dict[str, str] = {}
    # Ensure project default
    if not page.locator("#kz-view-project").is_visible():
        crumb_home = page.locator("#kz-crumb button[data-crumb='project']")
        if crumb_home.count():
            crumb_home.click()
            page.wait_for_timeout(120)
        elif page.locator("#kz-back").is_visible():
            while page.locator("#kz-back").is_visible():
                page.locator("#kz-back").click()
                page.wait_for_timeout(80)
    paths["project_default"] = str(
        _shot(page, f"{browser_name}_{vp_name}_project_default").relative_to(WORKSPACE_ROOT)
    )

    # Evidence drawer
    ev = _visible(page, "#kz-view-project [data-action='evidence']")
    if ev.count():
        ev.first.click()
        page.wait_for_timeout(150)
        assert page.locator("#kz-drawer-root").is_visible()
        paths["evidence_drawer"] = str(
            _shot(page, f"{browser_name}_{vp_name}_evidence_drawer").relative_to(WORKSPACE_ROOT)
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)

    # Site drill-down
    site = _visible(page, ".kz-site-card[data-action='site']")
    if site.count():
        site.first.click()
        page.wait_for_timeout(150)
        assert page.locator("#kz-view-site").is_visible()
        paths["site_drilldown"] = str(
            _shot(page, f"{browser_name}_{vp_name}_site_drilldown").relative_to(WORKSPACE_ROOT)
        )
        subj = _visible(page, "#kz-view-site .kz-site-card[data-action='subject']")
        if subj.count():
            subj.first.click()
            page.wait_for_timeout(200)
            assert page.locator("#kz-view-subject").is_visible()
            page.locator("#kz-tab-profile").click()
            page.wait_for_timeout(150)
            assert page.locator("#kz-tab-profile").get_attribute("aria-selected") == "true"
            profile_path = _shot(page, f"{browser_name}_{vp_name}_subject_profile")
            paths["subject_profile"] = str(profile_path.relative_to(WORKSPACE_ROOT))

            page.locator("#kz-tab-timeline").click()
            page.wait_for_timeout(200)
            assert page.locator("#kz-tab-timeline").get_attribute("aria-selected") == "true"
            # 历时轨迹面板应显示时间轴标记或明确的叠加说明。
            assert (
                page.locator(".kz-timeline__item, .kz-timeline__marker").count() >= 1
                or "历时轨迹" in page.locator("#kz-view-subject").inner_text()
            )
            timeline_path = _shot(page, f"{browser_name}_{vp_name}_subject_timeline")
            paths["subject_timeline"] = str(timeline_path.relative_to(WORKSPACE_ROOT))
            if profile_path.read_bytes() == timeline_path.read_bytes():
                raise AssertionError(
                    f"subject_profile and subject_timeline screenshots are byte-identical at {vp_name}"
                )
    return paths


def run_browser_matrix() -> Dict[str, Any]:
    """Execute Chromium+WebKit matrix, write QC JSON, return structured summary."""
    _ensure_evidence_dirs()
    summary: Dict[str, Any] = {
        "task_id": "medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809",
        "role_id": "worker_03",
        "generated_at": _utc_now(),
        "index_url": _file_url(),
        "playwright": "1.59.0",
        "browsers_required": list(REQUIRED_BROWSERS),
        "viewports": [name for name, _, _ in VIEWPORTS],
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
                                f"`playwright install {name}` "
                                "(or `.venv/bin/python -m playwright install "
                                f"{name}`). No other package install required. "
                                "Re-run this test file after the browser appears."
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
                        _assert_shell_ready(page)
                        # Interaction suite primarily on primary viewport to keep runtime bounded;
                        # QC + screenshots run on every viewport.
                        if vp_name == "1280x800":
                            _open_evidence_drawer(page)
                            _close_drawer_escape(page)
                            focus_info = _check_focus_trap(page)
                            result["focus_trap"] = focus_info
                            if not focus_info.get("trap_ok"):
                                result["failures"].append("drawer_focus_trap_failed")
                            if focus_info.get("restore_landed_on_kz_main"):
                                result["failures"].append("drawer_focus_restore_landed_on_kz_main")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:focus_restore_kz_main",
                                        "browser": browser_name,
                                        "viewport": vp_name,
                                        "check": "drawer_focus_restore_exact_opener",
                                        "detail": focus_info,
                                    }
                                )
                            elif not focus_info.get("restore_ok"):
                                result["failures"].append("drawer_focus_restore_failed")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:focus_restore_not_opener",
                                        "browser": browser_name,
                                        "viewport": vp_name,
                                        "check": "drawer_focus_restore_exact_opener",
                                        "detail": focus_info,
                                    }
                                )
                            disclaimer = _measure_disclaimer_font(page)
                            result["disclaimer_font"] = disclaimer
                            if not disclaimer.get("pass"):
                                result["failures"].append("disclaimer_font_below_16px")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:disclaimer_font",
                                        "browser": browser_name,
                                        "viewport": vp_name,
                                        "check": "kz_boundary_disclaimer_font_size",
                                        "detail": disclaimer,
                                    }
                                )
                            drill = _drill_site_subject(page)
                            result["drill"] = drill
                            if not drill.get("query_opened"):
                                # Query may be absent for some subjects; try project-level visible query
                                q = _visible(page, "#kz-view-project [data-action='query']")
                                if q.count():
                                    q.first.click()
                                    page.wait_for_timeout(150)
                                    if page.locator("#kz-drawer-root").is_visible():
                                        body = page.locator("#kz-drawer-body").inner_text()
                                        if not (
                                            "依据" in body
                                            or "发现" in body
                                            or "行动" in body
                                            or page.locator(".kz-query-part").count() >= 1
                                        ):
                                            result["failures"].append("query_drawer_missing_three_part")
                                        page.keyboard.press("Escape")
                                        page.wait_for_timeout(80)
                                        drill["query_opened"] = True
                                    else:
                                        result["failures"].append("query_drawer_did_not_open")
                                else:
                                    result["failures"].append("no_visible_query_control")
                            _empty_state_reset(page)
                            result["reduced_motion"] = _reduced_motion_check(page)

                        shots = _capture_state_screenshots(page, browser_name, vp_name)
                        result["screenshots"] = shots

                        # §16.4 on project default + subject timeline (markers live there).
                        while page.locator("#kz-back").is_visible():
                            page.locator("#kz-back").click()
                            page.wait_for_timeout(60)
                        if page.locator("#kz-drawer-root").is_visible():
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(60)

                        section_project = _run_section16_4(page)

                        # Navigate to subject timeline for marker/legend applicability.
                        site = _visible(page, ".kz-site-card[data-action='site']")
                        section_timeline = None
                        if site.count():
                            site.first.click()
                            page.wait_for_timeout(100)
                            subj = _visible(page, "#kz-view-site .kz-site-card[data-action='subject']")
                            if subj.count():
                                subj.first.click()
                                page.wait_for_timeout(120)
                                page.locator("#kz-tab-timeline").click()
                                page.wait_for_timeout(150)
                                section_timeline = _run_section16_4(page)

                        section = _merge_section_results(section_project, section_timeline)
                        result["section_16_4"] = section
                        result["section_16_4_project"] = section_project
                        result["section_16_4_timeline"] = section_timeline
                        if not section.get("all_pass"):
                            for name, check in section["checks"].items():
                                if not check.get("pass"):
                                    result["failures"].append(f"section16_4:{name}")
                                    summary["defects"].append(
                                        {
                                            "id": f"{key}:{name}",
                                            "browser": browser_name,
                                            "viewport": vp_name,
                                            "check": name,
                                            "detail": check,
                                        }
                                    )
                            if int(section["page_overflow"].get("horizontal_overflow") or 0) > 0:
                                result["failures"].append("horizontal_page_overflow")
                                summary["defects"].append(
                                    {
                                        "id": f"{key}:horizontal_page_overflow",
                                        "browser": browser_name,
                                        "viewport": vp_name,
                                        "check": "horizontal_page_overflow",
                                        "detail": section["page_overflow"],
                                    }
                                )

                        # Forbidden text on the current (timeline or project) DOM.
                        if not page.locator("#kz-view-project").is_visible():
                            while page.locator("#kz-back").is_visible():
                                page.locator("#kz-back").click()
                                page.wait_for_timeout(60)
                        forbidden = _forbidden_text_scan(page)
                        result["forbidden_text_hits"] = forbidden
                        if forbidden:
                            result["failures"].append("forbidden_visible_text")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:forbidden_text",
                                    "browser": browser_name,
                                    "viewport": vp_name,
                                    "check": "forbidden_visible_text",
                                    "detail": forbidden,
                                }
                            )

                        if collector.page_errors:
                            result["failures"].append("page_errors")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:page_errors",
                                    "detail": collector.page_errors,
                                }
                            )
                        if collector.console_errors:
                            result["failures"].append("console_errors")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:console_errors",
                                    "detail": collector.console_errors,
                                }
                            )
                        if collector.http_requests:
                            result["failures"].append("http_requests")
                            summary["defects"].append(
                                {
                                    "id": f"{key}:http_requests",
                                    "detail": collector.http_requests,
                                }
                            )

                        result["telemetry"] = {
                            "page_errors": collector.page_errors,
                            "console_errors": collector.console_errors,
                            "http_requests": collector.http_requests,
                        }
                    except Exception as exc:  # noqa: BLE001 - record exact interaction defect
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
        "smallest_setup": "playwright install webkit  # authorized one-time browser download only",
    }


def test_browser_qc_matrix_writes_summary(qc_summary: Dict[str, Any]):
    assert QC_SUMMARY_PATH.is_file(), f"missing QC summary: {QC_SUMMARY_PATH}"
    assert "results" in qc_summary
    runnable = (qc_summary.get("environment") or {}).get("runnable_browsers") or []
    assert runnable, "no required browser executable available to run matrix"
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
    required_states = (
        "project_default",
        "evidence_drawer",
        "site_drilldown",
        "subject_profile",
        "subject_timeline",
    )
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
    assert not missing, missing


def test_section_16_4_applicable_checks(qc_summary: Dict[str, Any]):
    """Fail the suite when any applicable §16.4 check fails (first-pass defect report)."""
    failed = []
    for key, result in qc_summary["results"].items():
        section = result.get("section_16_4") or {}
        checks = section.get("checks") or {}
        for name, check in checks.items():
            if not check.get("pass"):
                failed.append({"cell": key, "check": name, "detail": check})
        overflow = (section.get("page_overflow") or {}).get("horizontal_overflow")
        if overflow and int(overflow) > 0:
            failed.append({"cell": key, "check": "horizontal_page_overflow", "detail": section.get("page_overflow")})
    assert not failed, json.dumps(failed, ensure_ascii=False, indent=2)[:8000]


def test_interactions_and_a11y_gates(qc_summary: Dict[str, Any]):
    failed = []
    for key, result in qc_summary["results"].items():
        if not key.endswith(":1280x800"):
            continue
        for token in result.get("failures") or []:
            if token.startswith("section16_4:") or token in {
                "forbidden_visible_text",
                "horizontal_page_overflow",
            }:
                continue
            failed.append({"cell": key, "failure": token, "focus": result.get("focus_trap"), "drill": result.get("drill")})
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
    print(json.dumps({"overall_pass": summary["overall_pass"], "defect_count": len(summary["defects"]), "path": str(QC_SUMMARY_PATH)}, ensure_ascii=False, indent=2))
