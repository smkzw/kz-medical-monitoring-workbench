Implement the bounded truthful-progress slice described in
`context/mw_truthful_pipeline_progress_20260729_context.md`.

Read the complete context and source/test paths it names before editing. Edit
only:

- `services/api/app/medical_writing_research_pipeline.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- focused tests under `tests/`

The concrete defect is that fixed anchors leave preparation at 50% while real
child work advances from 14/99 to 66/99, and translation at 68% while critical
anchors complete. Introduce a backward-compatible persisted projection in
`ResearchPipelineState`, derive parent percent from real completed/total child
counters and declared stage ranges, and display the specific current substep in
the existing compact banner.

Hard rules:

1. No elapsed-time interpolation, simulated timer, fabricated counts, or fake
   ETA.
2. Parent percent is 0-100 and monotonic. Use triage 22-35, preparation 50-58,
   and translation 68-85. Waiting/terminal anchors remain authoritative.
3. Persist child phase, completed, total, child percent, and concise
   user-facing label so reload does not reset the display.
4. Preparation uses its real callback and current NCT/document where available.
5. Translation uses real batch item state and critical-anchor readiness; use
   item counts for progress when available.
6. Keep technical IDs/logs hidden. Do not add cards or increase information
   density; reuse the existing banner.
7. Preserve cancellation, retry, resume, waiting, error, and corpus-gate
   semantics.
8. Do not touch forbidden paths listed in the context; another worker is
   modifying AI role/settings concurrently.

Run focused and adjacent pytest plus `npm run build`. Return a compact handoff
with files changed, exact formula/data source, tests, residual risks, and live
recheck targets. Codex owns final acceptance.
