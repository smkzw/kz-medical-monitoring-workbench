# Codex Main-Venue Plan: mw_study_schema_scale_docx_20260720

Date: 2026-07-20
Objective: 基于康哲设计规范与真实中外临床试验方案，审阅并改进医学写作子系统研究流程图/研究流程表的AI预填与模块化编辑体验，验证SVG矢量和图片型量表附件在Word中的准确可读嵌入；输出可执行设计、边缘场景和验收标准

## Task Decomposition

1. Preserve the already working semantic model, API lifecycle and SVG/PNG DOCX
   package path; identify only observed product or rendering gaps.
2. Compare real phase I/II/III research-flow figures and Schedule of Activities
   structures against the current AI proposal and editor.
3. Define a desktop-first interaction contract where AI proposes the complete
   flow/table and the medical writer revises, adds, removes or confirms.
4. Add a governed image-attachment contract for scale appendices, distinct from
   editable body tables and from the research-flow SVG.
5. Implement the accepted bounded changes, run deterministic tests, exercise a
   real project through the live API/UI, export DOCX, update fields in Word,
   render PDF at 200 DPI and inspect every affected page.

## Source Packet

Use the current implementation, real Word acceptance artifact and read-only
reference packet listed in
`context/mw_study_schema_scale_docx_20260720_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_grok45` (user-overridden slot) | visible `qodercli` | `qwen3.8-max-preview` | `runs/conference/mw_study_schema_scale_docx_20260720/visual_grok45.md` |
| `visual_kimi_code` | `kimi-code` | `kimi-code/k3` | `runs/conference/mw_study_schema_scale_docx_20260720/visual_kimi_code.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Do not poll participants conversationally during the hard wait.
- Record start/end, process/session state, output completion marker, any
  terminal failure and whether a single targeted same-session follow-up was
  required.

## Codex Verification Checklist

- Current editor inspected in the live maximized desktop runtime.
- AI proposal, user edit, confirmation, layout and section projection exercised.
- SAD+MAD, parallel randomised, treatment-switch/extension and wide-layout cases
  covered.
- SVG and PNG fallback both exist in the DOCX package and render in Word.
- Image-based IBDQ attachment appears as readable appendix pages without
  clipping, stretching or accidental figure-list pollution.
- Word-native TOC/figure list updates; Open XML SDK has zero errors.
- Word-native PDF rendered at 200 DPI and affected pages visually accepted by
  Codex.
