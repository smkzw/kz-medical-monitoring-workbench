# RUX Subject Timeline Dose-Adjustment Interaction Research - 2026-07-08

## Scope

This note supports the narrow frontend slice for RUX 医学监查: how to render `dose_adjustment` events in the existing Subject Timeline / Patient Profile drill-down without redesigning the whole workbench.

## Source Scan

- Veeva Vault Safety Help, "Perform Medical Review" / Medical Review Timeline, accessed 2026-07-08: `https://safety.veevavault.help/en/gr/01172/`. Describes a medical review timeline as a visual, interactive context for adverse events, product usage, dosage regimens, test results, drug history, and medical history.
- Veeva Vault Safety Help, "Enable the Medical Review Timeline", accessed 2026-07-08: `https://safety.veevavault.help/en/gr/01414/`. Confirms the timeline displays study information including adverse events, product usage, dosages, test results, drug history, and medical history.
- JMP Clinical data analysis page, accessed 2026-07-08: `https://www.jmp.com/en/software/clinical-data-analysis-software`. Frames medical review around interactive reports for adverse events, concomitant medications, labs, vital signs, and drill-down patient profiles/narratives.
- JMP Clinical "Patient Profiles", accessed 2026-07-08: `https://www.jmp.com/support/downloads/JMPC170_documentation/Content/JMPCUserGuide/PatientProfiles.htm`. Describes patient profiling as a way to view a subject's entire history and investigate unexpected events or findings.
- `patientProfilesVis` CRAN/OpenAnalytics, accessed 2026-07-08: `https://cran.r-project.org/package=patientProfilesVis`; `https://openanalytics.r-universe.dev/patientProfilesVis`. Describes patient-specific clinical-trial visualizations for labs, ECG/vitals, adverse events, treatment exposure, metadata, and concomitant medication.
- "Interactive medical and safety monitoring in clinical trials with graphical patient profiles", PMC, accessed 2026-07-08: `https://pmc.ncbi.nlm.nih.gov/articles/PMC11271019/`. Describes patient profile reports spanning demography, treatment exposure, adverse events, concomitant medication, medical history, laboratory, ECG, vital signs, and other assessments.
- GitHub `agstn/PatientProfiler`, accessed 2026-07-08: `https://github.com/agstn/PatientProfiler`. Open-source proof-of-concept for combining multiple clinical trial data sources in a visual patient listing/profile.
- FDA ICH E3 guidance PDF, accessed 2026-07-08: `https://www.fda.gov/media/71271/download`. Safety conclusions should pay attention to events resulting in dose changes, need for concomitant medication, serious adverse events, withdrawals, and deaths.

## Design Implications For Current Slice

- `dose_adjustment` should not default to LAB/efficacy. It belongs to a trial-drug treatment/exposure/dose-management lane so medical reviewers can relate it to AE/LB/MH and protocol rules without mistaking it for a lab finding.
- User correction on 2026-07-08: `dose_adjustment` and other investigational-product changes must be shown as a separate lane. CM is reserved for non-investigational concomitant medications/treatments. Therefore, do not place `dose_adjustment` in the CM lane.
- The timeline should keep compact numbered event blocks on the visit axis and put full wording in hover/detail rows. Long Chinese strings should not be placed inside the lane graph.
- Chinese label should be clinically neutral: use `给药调整` or `给药/治疗调整`, not `PD`, not `违背`, and not a risk tone by default. It becomes high-risk only when linked to a risk prompt.
- Detail summaries should keep source trace and protocol context visible; this frontend slice should not claim full RUX monitoring coverage.

## Decision Candidate For Hermes Review

- Add an independent trial-drug lane. Candidate label: `试验药物变更` or `试验药物/给药调整`; CM remains `合并用药/治疗` for non-investigational medications/treatments.
- Map `dose_adjustment` short event labels to `DA1`, `DA2`, ...; compact English-like prefixes match current `AE/CM/MH/LB/QS/PD/Q` visual density.
- Tone should be `warning` when a linked risk exists; otherwise `normal`/source-neutral. Do not classify all dose adjustment as critical.
