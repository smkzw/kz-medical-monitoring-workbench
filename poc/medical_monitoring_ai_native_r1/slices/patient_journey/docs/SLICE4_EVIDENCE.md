# Slice 4 Evidence — 受试者医学旅程浏览器验收（最终纠偏复核）

**Task:** `medical_monitoring_r1_patient_journey_slice4_20260809`  
**Role:** `worker_03_round2` strengthened suite + Codex terminology and clinical-domain correction  
**Generated:** 2026-08-09  
**Executor:** Cursor CLI / `auto` verification suite; Codex final rerun and visual acceptance  
**Playwright:** 1.59.0 via existing `.venv`; absolute `file://` only; no package install; no server

## Supersession

Prior worker_03 evidence before the visit-ruler remake, and the intermediate round-2 failure before the user-language correction, are **superseded** by the current `qc_summary.json` and regenerated screenshots.

## Gate result

| Gate | Result |
|---|---|
| Chromium + WebKit @ 1280×800 / 1440×900 / 1920×1080 + 900×700 | Executed |
| No page / console errors / HTTP(S) | Pass |
| Page-level horizontal overflow ≤ 0 | Pass |
| ≥4 lanes; sticky ruler; domain-specific event/risk markers | Pass |
| Unique visit codes; no smash; paired 计划/实际 + title dates; UNS distinct | Pass |
| Event and risk legends both cover AE/MH/CM/IP/检查/住院/症状；risk also carries grade | Pass |
| Keyboard / focus / sync across 4 Chinese tabs / reduced-motion | Pass |
| Audience forbidden-term scan (Codex terminology list) | Pass; all four tabs, zero visible hits |
| Pytest | **16 passed**（9 data-contract + 7 browser-QC） |
| `qc_summary.json` `overall_pass` | **true**；`defects=[]` |

## Observed visit axis (chromium:1280x800)

| Code | Type |
|---|---|
| V0 | paired |
| V1 | paired |
| V2 | paired |
| UNS | unscheduled |
| V3 | paired |

- `duplicate_visit_codes`: `[]`
- `smashed_labels` / adjacent same-code overlap: `[]`
- All paired nodes show visible `计划` + `实际`; accessible `title` contains ≥2 ISO dates

## Exact commands

```bash
cd /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench

.venv/bin/python -m pytest -q \
  poc/medical_monitoring_ai_native_r1/slices/patient_journey/tests/test_data_contract.py \
  poc/medical_monitoring_ai_native_r1/slices/patient_journey/tests/test_browser_qc.py
# 16 passed in 21.43s
```

Adjacent current-runtime regression (run in each supported test boundary):

- R1 core: `103 passed in 0.73s`
- accepted AE/MH audience workbench: `18 passed in 28.75s`
- Patient Journey: `16 passed in 21.43s`
- current runnable total: **137 passed**

The earlier framework-comparison Spike is not part of that current-runtime total:
its two disposable `/tmp` virtual environments were intentionally removed after
their accepted evidence was recorded, and were not recreated for this UI-only
correction.

## Screenshots (refreshed)

Root: `output/playwright/medical_monitoring_r1_patient_journey_slice4_20260809/screenshots/`

| State | Pattern |
|---|---|
| Journey overview | `{chromium,webkit}_{1280x800,1440x900,1920x1080}_journey_overview.png` |
| Risk / evidence | `..._risk_evidence.png` |
| Metrics | `..._metrics.png` |
| Events | `..._events.png` |
| Risks tab | `..._risks_tab.png` |
| Narrow | `{chromium,webkit}_900x700_narrow.png` |

Codex reopen set:

- `chromium_1920x1080_journey_overview.png`
- `chromium_1440x900_risk_evidence.png`
- `chromium_1280x800_journey_overview.png`
- `chromium_900x700_narrow.png`

Machine summary: `output/playwright/medical_monitoring_r1_patient_journey_slice4_20260809/qc_summary.json`

## Integrity

- Worker_03 did **not** edit `app.js`, `styles.css`, fixture, contract, or Slice 3; Codex made the later bounded audience-terminology and clinical-domain corrections.
- Protected Slice 3 data SHA-256: `b7bb8319968982cca1622b7c6b9ee8182eff856dd95dffac2548518866b52d2c`
- Protected Slice 3 contract/test SHA-256: `3ecd686e805ee9c97cae0194d77c105c5df7450a1a04624904e4d9d4a722d22e`, `de920f44408f062f82fae9b840f1c42e3610e18a55ff45f30f2528486ab3e7b1`

## Final correction and residual observation

1. Projection-layer audience copy now converts the fixture's English slice name and internal risk/event labels to natural Chinese; visible forbidden-term hits are empty in Chromium and WebKit.
2. The former generic “已记录事项/风险提示” legend was rejected after user review. Current browser evidence requires the same seven domains (`ae/mh/cm/ip/lab/hospitalization/symptom`) in both event and risk legends. The visible AE risk marker carries both `AE` and `中`.
3. Domain is encoded by text plus shape plus restrained color; event-vs-risk uses event shapes versus diamond, and severity has an explicit high/medium/low badge.
4. The boundary states the actual product behavior: AI has completed risk collation; browsing, filtering and selection do not change data or risk status. It deliberately does not display the unrelated workflow phrase “人工复核未完成”.
5. At 900×700, later visits remain available through the internal horizontal journey scroller. Page-level overflow is zero; visit codes remain unique and no label smash is detected at the tested default density.

## Explicit non-claims

- Accepted only as an isolated synthetic R1 interaction slice; this is not a product-release, clinical-conclusion or real-project acceptance claim.
- No service, port 8911, product source, medical-writing source, shared runtime or real project was used or modified.
