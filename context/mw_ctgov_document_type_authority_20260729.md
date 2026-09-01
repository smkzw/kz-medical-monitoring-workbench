# ClinicalTrials.gov Document-Type Authority Decision

## Problem

Frozen r11 preparation marked 45 public documents as document-type mismatch.
Most were ClinicalTrials.gov files declared by the registry as SAP or
Protocol+SAP, but the local validator reclassified them as Protocol because an
SAP naturally repeats protocol title, objectives, endpoints, and design
language.

## Primary Evidence

1. ClinicalTrials.gov Results Data Element Definitions:
   <https://clinicaltrials.gov/policy/results-definitions#documentUploadInformation>
   defines mutually explicit upload types: Study Protocol, Statistical
   Analysis Plan, ICF, and Study Protocol with SAP and/or ICF. It instructs the
   responsible party to select the combined type when a protocol includes an
   SAP.
2. ClinicalTrials.gov Study Data Structure:
   <https://clinicaltrials.gov/data-api/about-api/study-data-structure>
   exposes `largeDocs.typeAbbrev`, `largeDocs.hasProtocol`, and
   `largeDocs.hasSap` as first-class document metadata.
3. ClinicalTrials.gov Results QC Review Criteria:
   <https://clinicaltrials.gov/submit-studies/prs-help/results-quality-control-review-criteria>
   explicitly reviews whether the registry Document Type accurately reflects
   the uploaded document, including combined Protocol+SAP.
4. Real official SAP examples such as
   <https://cdn.clinicaltrials.gov/large-docs/88/NCT04157088/SAP_001.pdf>
   and
   <https://cdn.clinicaltrials.gov/large-docs/92/NCT05619692/SAP_001.pdf>
   refer repeatedly to the governing protocol and reproduce objectives/design
   context. Therefore protocol-language presence is not positive proof that an
   SAP was mislabeled.

## Decision

- For an immutable ClinicalTrials.gov ProvidedDocs artifact whose source
  document is bound to the same snapshot, treat the registry's
  `hasProtocol`/`hasSap`-derived type as the primary document identity.
- Content checks still detect a clear publication/article substitution for
  manual or non-registry sources and continue to validate study identity,
  indication, source URL, and date for every source. Protocols commonly include
  abstracts and reference lists, so those cues do not override an official
  registry document type.
- Absence of a short SAP title or presence of protocol anchors is not
  contradictory evidence against a registry-declared SAP.
- Manual uploads remain content-classified because no registry document-type
  authority exists. An ambiguous manual file remains reviewable and
  user-overridable with a concise warning.
- A later independent-AI classifier should be used only for genuinely
  ambiguous manual/external files or positive metadata/content conflicts. It
  must return a structured role plus evidence locators and may not downgrade a
  registry-declared document solely because protocol language is present.
- For the same official binding, absence of an exact indication string or
  citation of another NCT in background text is retained as observed trace, not
  converted into a per-document approval task. Manual/non-registry sources keep
  the stricter content-based behavior.

## Rejected Approach

Increasing the number of SAP keywords was rejected. It would continue
overfitting specific templates and indications, and would still treat
registry metadata as weaker than an unstable text heuristic.

## Acceptance

- Public registry-declared SAP and Protocol+SAP examples with protocol
  references pass document-type validation.
- A manual/non-registry file that is clearly a publication remains mismatch.
- Manual Protocol/SAP boundary tests remain strict.
- Fresh r12 preparation must materially reduce the 45 false mismatches without
  any override or database mutation.
