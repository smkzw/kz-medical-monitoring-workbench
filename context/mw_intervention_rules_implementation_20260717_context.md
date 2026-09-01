# Medical Writing Intervention Rules Implementation Context

## Objective

Implement the frozen M11 6.4/6.9/6.10 structured intervention-rules contract without creating a second fact store. Preserve backward compatibility, keep IP disposition separate from CM/non-IP treatment, and make section entry routes open the correct desktop editor.

## Source Of Truth

- `records/active_slices/medical_writing_intervention_rules_runtime_20260717/TASK_RECORD.md`
- `runs/execution/mw_intervention_rules_discovery_20260717/manager_resume.md`
- `runs/execution/mw_intervention_rules_discovery_20260717/worker_02.md`
- Current product code and tests in the explicit role read/write lists.

## Frozen JSON Contract

Add `picos.intervention_rules` as the additive canonical structured block:

```json
{
  "schema_version": "medical_writing_intervention_rules_v1",
  "authority": "legacy|structured",
  "ip_regimens": [{
    "regimen_id": "stable id",
    "product_name": "",
    "product_role": "investigational_product|active_comparator|placebo|other",
    "dose_and_frequency": "",
    "route": "",
    "treatment_period": "",
    "adherence_notes": "",
    "source_location": ""
  }],
  "ip_adjustment_policy": "unspecified|no_planned_adjustment|protocol_defined",
  "no_planned_adjustment_statement": "",
  "ip_action_rules": [{
    "rule_id": "stable id",
    "action_kind": "planned_on_off|temporary_interruption|resume|permanent_discontinuation|discontinuation_taper|post_discontinuation_follow_up|other",
    "trigger": "",
    "severity_or_threshold": "",
    "confirmation_required": "",
    "exceptions": [],
    "study_product_action": "",
    "retest_recovery": "",
    "approvers": [],
    "wait_period": "",
    "permanent_discontinuation_condition": "",
    "taper_steps": [],
    "linked_non_ip_rule_ids": [],
    "source_location": "",
    "notes": ""
  }],
  "non_ip_treatment_rules": [{
    "rule_id": "stable id",
    "rule_class": "background|allowed_cm|prohibited_cm|rescue|other_non_investigational",
    "policy": "allowed|allowed_if_stable|allowed_with_approval|allowed_with_timing|prohibited|rescue_policy",
    "agent_or_category": "",
    "collection_window": "",
    "timing_restrictions": [],
    "washout_or_window": "",
    "cm_dose_rule": "",
    "phase_applicability": "",
    "exceptions": [],
    "source_location": "",
    "notes": ""
  }],
  "cross_object_links": [{
    "link_id": "stable id",
    "source_rule_id": "",
    "source_kind": "rescue|cm|background|other_non_ip",
    "target_kind": "ip",
    "target_rule_id": "",
    "action": "hold|stop|no_auto_ip_action|resume",
    "resume_condition": "",
    "notes": "",
    "source_location": ""
  }]
}
```

## Authority And Validation

- Default authority is `legacy`; all existing payloads must round-trip unchanged.
- When authority is `structured`, structured objects are canonical. Legacy `intervention_dose_regimen`, `required_background_rules`, `allowed_concomitant_rules`, and `prohibited_concomitant_rules` are deterministic compatibility projections, not independent editable truth.
- `no_planned_adjustment` requires a nonblank statement. It may coexist with safety interruption, permanent discontinuation, taper, and follow-up rules because it means no planned routine adjustment.
- `protocol_defined` requires at least one IP action rule.
- All IDs are present and unique. Links must reference an existing non-IP source rule; a nonblank target rule id must reference an existing IP action rule.
- CM dose rules remain only in `non_ip_treatment_rules[].cm_dose_rule`.
- Do not hardcode RUX, D001, or PNH facts into production defaults.

## Impact Routing

- `picos.intervention_rules.ip_regimens` -> intervention_sections, protocol_synopsis, study_schema.
- `picos.intervention_rules.ip_adjustment_policy`, `no_planned_adjustment_statement`, `ip_action_rules` -> dose_modification_rules.
- background/rescue/other non-IP -> non_investigational_interventions.
- allowed/prohibited CM -> concomitant_therapy_rules.
- links -> dose_modification_rules + non_investigational_interventions + concomitant_therapy_rules.
- Keep existing legacy maps during migration.

## Frontend Routing

- 6.4 `dose_modification_rule_builder` -> panel `ip_actions`, label/button `试验药物剂量调整`.
- 6.9 `non_investigational_intervention_builder` -> panel `non_ip`, label/button `非试验用药与补救治疗`.
- 6.10 `concomitant_therapy_rule_builder` -> panel `cm`, label/button `合并用药规则`.
- Existing broad PICOS intervention entry opens `regimen`.
- Editor uses compact desktop segmented navigation: 试验药物与给药 / 剂量调整 / 非试验用药与补救 / 合并用药. Do not add persistent log cards.
- Each rule is a dense editable row/card with add/remove; long rationale/source details may expand inline. No nested decorative cards.
- The section-specific route lands on the relevant panel and uses the same journey impact-preview/commit/CAS path.

## Risk Boundaries

- Do not touch stable runtime SQLite or original DOCX files.
- Do not call product AI.
- Tests use isolated service databases/fixtures.
- Do not implement the deterministic working-copy/DOCX projection in the frontend worker. Backend worker may prepare model/validation only. Projection is a separate Codex-controlled follow-up after both implementations pass.
- Preserve all user edits; no destructive commands.

## Success Criteria

- Model validation covers no-planned-adjustment, protocol-defined rules, unique IDs, link references, and legacy round-trip.
- Existing authoring journey tests remain green.
- 6.4/6.9/6.10 no longer collapse to one frontend target.
- Frontend builds and focused contract tests pass.
- No IP/CM label or field cross-contamination.

