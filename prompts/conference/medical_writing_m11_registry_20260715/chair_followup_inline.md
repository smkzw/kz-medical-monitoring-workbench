Continue the SAME GPT-5.5 chair session. Do not restart. Your first pass was incomplete because file reads did not occur. This follow-up supplies the evidence inline; produce the complete chair package now without tools.

Participant convergence:
- MiniMax, Flash, Grok and two Codex SubAgent audits independently reject copying the 14-section client array to the server and calling it M11.
- P0 consensus: client must not control chapters, headings, parents, anchors, initial prose, source fact IDs or initial approval decisions; new documents must pin an immutable template version and definition digest; StudyDefinition and template binding must be revalidated around the creation reservation; old 14-section greenfield and source-DOCX projects must not be silently migrated or have IDs/hashes/working copies/approval snapshots changed.
- P0 semantic boundaries: investigational-product dose modification is separate from concomitant medication; background/rescue/non-investigational interventions are separate from ordinary concomitant medication; routing by Chinese title regex is unsafe.
- The authoritative local draft tree has front matter plus 158 numbered L1-L4 nodes: chapters 1-14, including L4 9.1.3.1, 9.2.3.1, 10.4.1.1-1.5 and 10.5.1.1-1.5. It is a 2025-01-14 stage-3 Chinese draft, not proof of current Step-4/CDE-2026 identity.
- Dedicated object boundaries: 1.1 ProtocolSynopsis; 1.2 StudySchema/vector diagram; 1.3 ScheduleOfActivities; eligibility rules; dose modification; non-investigational interventions; concomitant therapy; AESI; analysis sets; sample size; laboratory panel; regional differences; amendment history; glossary; references. TOC/table list/figure list/cross-references are generated objects, not rich text.
- Frontend consensus: keep the existing dual-entry journey and convergence point; remove client scaffold; carry template metadata through documentSections; future SectionInteractionRouter must fail closed for unknown profiles. A full M11 tree needs hierarchical/virtualized desktop navigation and a save/discard/cancel guard when switching a dirty section.
- Migration consensus: current legacy documents remain byte/semantic stable. Any later upgrade is an explicit derived document with lineage and renewed approval, never an in-place rewrite.

Implementation now present for review:
- Added a deterministic server registry with front matter plus all 158 numbered nodes, stable IDs, parent/level, Chinese titles, conditional/repeatable/title-lock flags, interaction types, template version and SHA-256.
- New registry requests reject client sections and client approval decisions. Server derives all 159 section seeds, synopsis/design projections and uncertainty blockers from the bound StudyDefinition.
- ProtocolDocument/ProtocolSection carry template identity and interaction metadata; the old model fields have backward-compatible defaults.
- Existing documents are not migrated. New frontend create request sends exact template ID/version and no section seeds/fact IDs/initial text/decisions.
- A post-reservation StudyDefinition binding check was added to close the observed validation/reservation race.
- Focused result at this point: 90 contract/greenfield/journey/frontend tests passed; all 128 medical-writing tests passed; Vite build passed with only the existing large-chunk warning.

Open issues that must be classified:
1. Registry authority is the user-provided stage-3 Chinese draft; do not overclaim Step-4 conformance.
2. Full interaction router, hierarchical navigation, dirty-section switch guard, dedicated synopsis/schema/scale/index objects and Word fields are later slices, not yet complete.
3. Decide whether the immediate server registry slice is acceptable as an additive foundation or must be blocked until those later editors exist.

Produce the complete corrected chair synthesis with: inputs reviewed; evidence vs inference; accepted/rejected proposals; P0/P1 gaps; whether current incremental implementation is GO/NO-GO for merge as a foundation (not subsystem completion); exact verification gates; recommended next slice. Codex remains final authority.
