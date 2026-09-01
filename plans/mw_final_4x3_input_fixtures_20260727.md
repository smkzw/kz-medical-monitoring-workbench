# Final 4x3 Test Input Fixture Contract

Date: 2026-07-27
Status: PREPARED_NOT_BUILT

## Purpose

Six final-matrix slots use the `synopsis_import` entry route. Each requires a
new, realistic sponsor-input DOCX and a minimal fact pack. These files are test
inputs, not product outputs. They must exercise extraction, table rendering,
reference reindexing, conflict clarification and AI-led design completion
without pre-answering the protocol-writing task.

## Global Rules

- Every fixture is newly built for this matrix and has its own SHA-256 receipt.
- Do not reuse a prior protocol, synopsis, parsed extract, generated protocol,
  corpus result or competitor basket.
- Use fictional product codes and no patient or confidential project data.
- The synopsis is 3-5 substantive pages, with company-like Chinese formatting,
  one study-summary table and at least one deliberately incomplete design
  decision.
- Include only sponsor-known facts: modality/formulation, intended indication,
  phase, broad objective, supported dose/route constraints, known safety or PK
  facts, and the intended design pressure.
- Do not include fabricated effect sizes, sample sizes, endpoint thresholds,
  competitor conclusions, complete eligibility criteria, complete SoA,
  statistical solution, or final protocol prose.
- Each ambiguity is explicit enough for the product to ask one concise
  clarification or provide evidence-bounded options. The fixture does not
  contain the answer.
- Source citations in a fixture are real and retrievable or omitted. Imported
  references must be deliberately nonsequential in at least D3 so the product
  must reindex them.
- DOCX text uses Chinese SimSun and English/numerals Times New Roman. Visible
  tables use black text and editable Word table objects.

## A2 - AATD Phase I Oral Small Molecule

Input:

- Fictional oral small-molecule chemical chaperone, immediate-release tablet.
- Healthy-volunteer SAD and MAD are intended; food-effect may be embedded.
- Known half-life range, nonclinical target-organ summary, NOAEL exposure
  margin and provisional maximum exposure ceiling are supplied.
- The synopsis states sentinel dosing and SRC review are required.

Deliberate gaps:

- Cohort count, escalation increments, observation window and stopping rule
  thresholds are not fixed.
- One sentence mentions exploratory biomarker work without specifying whether
  it is target engagement or pharmacodynamic activity.
- No patient efficacy endpoint and no first-patient cohort are supplied.

## B1 - Type 2 Diabetes Phase III Active Control

Input:

- Fictional oral once-daily small molecule added to stable metformin.
- Active comparator and double-dummy intent are stated.
- Broad noninferiority-first, superiority-if-supported objective is stated.
- Known hypoglycaemia, hepatic and renal monitoring facts are supplied.

Deliberate gaps:

- Comparator, metformin background, rescue therapy and estimand information
  are distributed across different sections and must be reconciled.
- Noninferiority margin, multiplicity sequence and rescue threshold are not
  supplied.
- The synopsis does not decide whether a placebo calibration arm exists; the
  product must not invent one.

## B3 - Allergic Conjunctivitis Phase II Eye Drops

Input:

- Fictional ophthalmic solution with concentration range and maximum daily
  instillation facts.
- Environmental exposure-chamber concept and bilateral-eye observations are
  stated.
- A visible editable table lists candidate ocular signs/symptoms and repeated
  post-challenge time points.

Deliberate gaps:

- Parallel, crossover, contralateral-eye and hybrid designs remain open.
- Primary eye/unit-of-analysis, period washout and multiplicity are not fixed.
- The product must distinguish local ocular safety from systemic drug logic.

## C2 - C3 Glomerulopathy Phase II Complement Inhibitor

Input:

- Fictional oral factor-B inhibitor and a placebo-controlled main period with
  optional open-label extension.
- Proteinuria, eGFR and renal histology are listed as candidate endpoint
  domains.
- Known infection/AESI, vaccination and renal-biopsy operational facts are
  supplied.

Deliberate gaps:

- Endpoint hierarchy, assessment time, effect size and sample size are absent.
- Repeat-biopsy feasibility and central-read adjudication remain open.
- The synopsis contains no basis for claiming one endpoint as registrationally
  validated.

## D1 - Parkinson Disease Phase III Interim Analysis And Transition

Input:

- Fictional oral extended-release small molecule on optimized levodopa.
- Placebo-controlled main period, blinded transition and extension intent are
  stated.
- Interim futility/sample-size re-estimation purpose and independent DMC are
  stated.
- Known orthostatic hypotension, impulse-control and drug-interaction facts
  are supplied.

Deliberate gaps:

- Alpha-spending method, information fraction, firewall details and post-
  transition estimand are not supplied.
- Rescue rules and motor-fluctuation endpoint hierarchy remain open.
- No single source is claimed to support all design components.

## D3 - Rosacea Phase I Topical Cream

Input:

- Fictional topical cream with concentration range, application frequency,
  maximum treated area and provisional exposure limits.
- First-patient multiple-dose intent, local/systemic PK, local tolerability,
  standardized photography and optional biopsy are stated.
- A visible table contains concentration, treated-area and sampling concepts.
- Three real background references are inserted with deliberately nonsequential
  in-text numbers so import must reindex them.

Deliberate gaps:

- Cohort sequence, concentration escalation, biopsy subset and inflammatory
  biomarker panel are not fixed.
- The product must not borrow acne, AD or psoriasis scales without supported
  mapping.

## Required Build Evidence

For each slot:

- source DOCX;
- optional minimal fact-pack DOCX/XLSX where useful;
- fixture manifest with slot, filename, byte count and SHA-256;
- extracted text/table inventory;
- rendered PDF or page images proving 3-5 pages and visible table fidelity;
- assertion list distinguishing supplied facts from deliberately open
  decisions;
- no `PASS.md`.
