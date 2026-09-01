# Commercial And Open-Source Research Notes

Date: 2026-07-08 CST

Purpose: Capture external product, standards, and open-source references that shape the commercialization roadmap for the AI medical manager workbench. These references are product/technical design inputs, not clinical or regulatory conclusions.

## Commercial Product Patterns To Evaluate

### Clinical Data Review / Medical Monitoring

- Medidata: clinical data management and review platforms emphasize unified clinical data, query workflows, data review, and operational scale. Design implication: 医学监查 must treat EDC listing upload as one data-ingestion route today, but the API contract should stay ready for direct EDC/clinical data platform ingestion later.
  - Source: https://www.medidata.com/
- Veeva Vault Clinical / Vault EDC: product positioning emphasizes integrated clinical operations/data workflows, auditability, and site/sponsor collaboration. Design implication: project overview, approvals, source registry, and subsystem states should be treated as one workbench flow, not isolated demos.
  - Source: https://www.veeva.com/products/clinical-data-management/
- Saama: AI-enabled clinical data review and automation patterns point toward explainable review queues, role-based review, and traceable AI suggestions. Design implication: every AI output should carry source refs, validation status, model/provider status, and human disposition.
  - Source: https://www.saama.com/
- CluePoints: RBQM/RBQM analytics focus on risk indicators, central monitoring, issue prioritization, and documented quality oversight. Design implication: 医学监查 should separate rule-generated KRI/QTL, medical interpretation, issue ownership, and approval/closure evidence.
  - Source: https://www.cluepoints.com/

### Medical Writing / Structured Protocol

- ICH M11: structured protocol direction supports separating reusable protocol structure, source-derived design decisions, and downstream writing. Design implication: 证据调研与方案设计 should generate PICOS decisions and structured handoff objects, not free-form final protocol text.
  - Source: https://www.ich.org/page/multidisciplinary-guidelines
- TransCelerate Clinical Template Suite: industry template approach supports structured protocol/IB/ICF/CSR content models and controlled text reuse. Design implication: 医学写作 should maintain section inventory, source-bound candidates, revision threads, and quality gates.
  - Source: https://www.transceleratebiopharmainc.com/
- Certara / Synchrogenix-style regulatory writing services and platforms indicate that writing support must include evidence traceability, medical review, versioning, and submission-readiness workflow rather than pure text generation.
  - Source: https://www.certara.com/

### Safety / PV Collaboration

- ArisGlobal LifeSphere Safety, Oracle Argus Safety, and Veeva Vault Safety represent mature PV-system boundaries. Design implication: 安全信号与PV协同 must not replace the PV system; it should prepare medically reviewed candidate narratives, signal context, cross-document consistency checks, and PV handoff packets.
  - Sources:
    - https://www.arisglobal.com/lifesphere-safety/
    - https://www.oracle.com/industries/life-sciences/argus-safety/
    - https://www.veeva.com/products/vault-safety/

## Standards And Official Data Interfaces

- ICH E6(R3): reinforces quality-by-design, proportionate risk management, data governance, and documented oversight. Design implication: dashboard and approval center should make quality gates and unresolved risks first-class objects.
  - Source: https://www.ich.org/page/efficacy-guidelines
- CDISC SDTM, ADaM, and Define-XML: support the 数据分析与TFL module contract and later regulatory-grade dataset ingestion. Design implication: daily monitoring should use data listing; TFL should use SDTM/ADaM/define.xml only when available.
  - Source: https://www.cdisc.org/standards
- ClinicalTrials.gov API v2: official registry API for protocol/result metadata refresh. Design implication: 证据调研与方案设计 needs registry adapters, source snapshots, and update diff tracking.
  - Source: https://clinicaltrials.gov/data-api/about-api
- PubMed / NCBI E-utilities: official publication search/retrieval route. Design implication: publication-derived evidence must be source-indexed and periodically refreshable.
  - Source: https://www.ncbi.nlm.nih.gov/books/NBK25501/

## Open-Source Technical Patterns

- pharmaverse/admiral: ADaM derivation package family for clinical trials. Design implication: 数据分析与TFL should not hand-roll every derivation; use established ADaM derivation concepts and explicit metadata-driven transformation where possible.
  - Source: https://github.com/pharmaverse/admiral
- pharmaverse/rtables: production-style clinical tables. Design implication: TFL should expose table shells, analysis population, denominator rules, and reproducible generation metadata.
  - Source: https://github.com/insightsengineering/rtables
- pharmaverse/tern: common statistical tables/graphs/listings tooling. Design implication: TFL generation should preserve code, inputs, output table specs, and reviewer-facing interpretation.
  - Source: https://github.com/insightsengineering/tern
- safetyGraphics: interactive clinical safety graphics. Design implication: Patient Profile and safety trend views should support linked charts, filters, patient drilldown, and traceable outliers.
  - Source: https://github.com/SafetyGraphics/safetyGraphics
- Teal / Shiny clinical review apps: modular clinical review dashboards show a pattern of dataset ingestion, interactive filtering, and traceable tables/plots. Design implication: front-end components should stay modular and reusable across TFL, safety, and patient profile views.
  - Source: https://github.com/insightsengineering/teal

## Productization Constraints Derived From Research

1. Data lineage is a product feature: every table, risk, AI suggestion, and writing candidate needs source refs, parser version, model/provider state, validation status, and audit trail.
2. Human confirmation is non-negotiable: the system may produce `待医学批准的正式内容候选`, but it must not claim automatic final approval or regulatory readiness.
3. Daily monitoring and lock-database analysis are different ingestion modes: daily monitoring starts from EDC exported listings; TFL/regulatory analysis starts from SDTM/ADaM/define.xml when available.
4. Mature clinical platforms optimize for review queues and exception handling, not static dashboards alone. Each subsystem needs task queues, unresolved blockers, disposition actions, and review history.
5. The architecture must support private deployment: local filesystem ingestion now, later object storage/database/message queue/role-based auth without changing public contracts.

## Current Workbench Implications

- Highest commercial gap: move modules from static manifests to executable task workflows with durable stores and real raw-source tests.
- Highest near-term slice: complete a shared `Real Project Validation Matrix` and bind each subsystem to 3-5 real raw inputs, then implement one missing workflow end to end instead of adding more mock cards.
- Likely P0 candidates:
  - 数据分析与TFL: ingest real Ruxolitinib AD SDTM/ADaM/define/TFL inventory and render reproducible TFL review workbench.
  - 安全信号与PV协同: ingest real safety listing / PV plan / DSUR or safety section sources and create PV handoff candidate workflow.
  - 医学写作: expand protocol-first writing to IB/ICF/M2.5/M2.7.3/M2.7.4 with source-bound section manifests and revision queues.

## 2026-07-08 Down-Half Research Refresh

Scope: quick external refresh before resuming commercialization build. This is a source map for later deeper subsystem research; it is not a claim that the current workbench already matches these products.

- Clinical data review / workbench products reinforce the need for multi-source ingestion, review queues, audit trails, and source lineage before UI polish.
  - Veeva Clinical Data Management: https://www.veeva.com/products/clinical-data-management/
  - Medidata Rave EDC: https://www.medidata.com/en/clinical-cloud/rave-edc/
  - CluePoints RBQM / Central Statistical Monitoring: https://cluepoints.com/solutions/rbqm/
  - Saama clinical AI platform: https://www.saama.com/
- Open-source and standards-aligned clinical analysis tooling reinforces that TFL/ADaM/CDISC derivations should be metadata-driven and source-reproducible.
  - pharmaverse admiral: https://github.com/pharmaverse/admiral
  - rtables: https://github.com/insightsengineering/rtables
  - tern: https://github.com/insightsengineering/tern
  - CDISC standards: https://www.cdisc.org/standards
- Medical-writing and rich-text implementation references reinforce that writing modules need structured sections, revision threads, evidence binding, and human approval rather than free-form generation.
  - ICH M11: https://www.ich.org/page/multidisciplinary-guidelines
  - TransCelerate Clinical Template Suite: https://www.transceleratebiopharmainc.com/
  - ProseMirror: https://prosemirror.net/
  - Tiptap: https://tiptap.dev/

Immediate product implication for the RUX monitoring slice: build the backend source/event/rule layer first, then wire route/inbox/frontend around real source locators. This matches the external pattern that clinical review products are exception-management systems with provenance, not static dashboards.
