# Codex Conference Review: medical_writing_word_table_visual_20260714

Date: 2026-07-14

## Verdict

PASS for this draft iteration's Word table visual fidelity. No production exporter change is justified. A separate source-content anomaly (`<0}` in RUX p70) is verified and must enter the medical-writing content-quality backlog; it is not a rendering defect.

## Boundary Compliance

- All three assigned provider/model routes completed three rounds in the same session with no fallback.
- No participant modified production files, browsed the web, ran browser acceptance or claimed Codex authority.
- Kimi and MiniMax explicitly disclosed incomplete original-resolution image coverage. Their visual-pass recommendations are therefore not accepted as independent full visual gates.
- Qwen inspected the assigned packet but overgeneralized sampled pages to all portrait tables and described every schedule as a 15-column table. Codex accepts only its page-cited observations and the RUX p70 anomaly, not those corpus-wide formulations.
- Runner shutdown emitted non-fatal MCP event-loop warnings after successful return code 0. They did not truncate the persisted round outputs or change the three-round/session evidence.

## Participant Outputs Reviewed

| Role | Session | Accepted contribution | Rejected or bounded contribution |
|---|---|---|---|
| MiniMax-M3 | `20260714_081443_c1d7ad` | RUX sampled-page observations; explicit disclosure that D001/PNH original pages were not inspected | No independent full visual pass; several table labels were inferred incorrectly; `<0}` was incorrectly suspected to be a renderer encoding loss |
| Kimi-K2.7-Code | `20260714_081443_2048fa` | Correct structural totals and explicit incomplete-visual warning | No independent full visual pass; reported output path does not match the runner-owned path |
| Qwen3.7-Plus | `20260714_081443_c946aa` | Full assigned packet inspection; no sampled table-layout defect; RUX p70 `<0}` observation | Corpus-wide claims exceed the 24 original-page sample; all-schedule `15 columns` statement is false for D001; original per-project page totals were inconsistent in intermediate output |

## Hermes Sub-Venue Review

This was a Codex-led visual panel with no sub-venue chair. No chair synthesis is expected or used.

## Main-Venue Codex Review

- The controlled font experiment isolates missing CJK glyphs to the default LibreOffice fontconfig discovery path. The same DOCX renders correctly with explicit verified fontconfig, so production OOXML was not changed.
- The CJK-aware rerender contains 259 pages, 68 tables and 26 landscape pages. The automatic report has zero failures and confirms embedded STSongti/STHeiti-family fonts.
- Codex reviewed all 17 contact sheets and the 24 named original-resolution pages. The post-conference challenge re-opened RUX p70, D001 p25 and PNH p22/p23 directly.
- D001's 20-column phase III schedule fits the landscape printable area; PNH's 15-column schedule and repeated header band are visible without clipping. The black region shown by the PNG viewer around PNH p22 is transparency padding, not page background.
- The string `对于研究中具有生育能力的女性受试者：<0}` is present verbatim in original source DOCX table 11, row 3, cell 1 and in the unchanged export. It is a source content-quality problem, not a font/rendering error. Original source remains immutable.

## Codex Independent Verification

- Export SHA-256 remained unchanged after rerender:
  - RUX `48ff3112e78dc03441184e13b3d158a7ea7b82a5f2289dfbad3a5b0fe28bde82`
  - D001 `48a7fd3d07d2778e15302bf4592ebe29603e7e954ffa9f5e480039a97199ed46`
  - PNH `98be5798b5f87c1dd32380f017a12e5a3c69978cedc351d937fbb5447d872067`
- Re-executed `analyze_word_table_fidelity.py` with `renders_cjk`: `projects=3`, `pages=259`, `tables=68`, `landscape_pages=26`, `failures=[]`.
- `py_compile` passed for the font probe, verified-fontconfig renderer and table-fidelity analyzer.
- Study schedules retain repeat-header OOXML rows: RUX 4, D001 5/5, PNH 4.
- API `8911` and frontend `5174` were healthy before the visual gate. No product source was modified in this slice, so a full 880-test rerun would not add evidence beyond the previously passed repository gate.

## Final Decision

Accept Word table rendering for the current RUX, D001 and PNH draft-preview exports. Persist explicit CJK font embedding as a QA/private-deployment renderer readiness check. Open the verified RUX `<0}` source anomaly as the next medical-writing content-quality slice; do not silently rewrite the original protocol or conflate source correction with visual fidelity.
