# Codex Final Review: Real IBDQ Word Gate

Date: 2026-07-24 CST

## Scope

This is a split acceptance of the narrow Word fixture generated from the
current production exporter. It is not acceptance of a complete production
protocol layout.

## Evidence Reviewed

- All 13 original 200 DPI rendered pages.
- Word-native PDF and round-trip DOCX.
- Pre/post OOXML package checks and media hashes.
- Grok first-line execution report.
- Kimi Code/k3 independent page-by-page visual manager review.

## Final Gates

### IBDQ_PAGINATION_GATE: PASS

Pages 5-13 contain source pages 1/9-9/9 in order. Each appendix title remains
with its corresponding page image. No missing, duplicate, isolated-title,
overflow, blank-separator, header/footer collision, or unreadable page was
observed.

### WORD_NATIVE_ROUNDTRIP_GATE: PASS

Microsoft Word 16.111.1 preserved the SVG part, SVG relationship, `svgBlip`,
ten PNG media parts and nine unique IBDQ appendix titles. The SVG hash is
unchanged. The nine IBDQ PNG hashes are unchanged. Word clearing
`updateFields` after updating and saving fields is expected and is not a
content defect.

### FLOWCHART_VISUAL_GATE: FAIL

On page 3, the condition label intended as `240 mg BID安全性不佳` renders as
`ng BID安全性不佳`. Source geometry confirms the label is wider than the
76-pixel corridor between its endpoint nodes and is drawn before the nodes;
the source node masks the label prefix. This is a generic study-schema
edge-label layout defect, not a Word media round-trip defect.

## Boundaries

- Page 4 contains fixture-only meta language and must never enter a production
  export.
- Sparse TOC/list-of-figures pages 1-2 prove field updates only; they do not
  prove full protocol typography or pagination quality.
- The flowchart gate must be rerun after a generic renderer fix and 200 DPI
  visual inspection. Project-specific label or coordinate exceptions are not
  acceptable.
