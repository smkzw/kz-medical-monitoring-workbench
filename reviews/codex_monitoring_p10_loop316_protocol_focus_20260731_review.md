# Codex Review: monitoring_p10_loop316_protocol_focus_20260731

Date: 2026-07-31 CST  
Delegated-agent output: `runs/pi_monitoring_p10_loop316_protocol_focus_20260731.md`

## Verdict

**Pass after bounded Codex remediation.**

The finite-code route correctly implemented a provider-only structural evidence view,
an explicit 50 structured-evidence-ID budget and repair-envelope reuse without changing
the persisted frozen input or relaxing an existing clinical/structural gate. Independent
conference review then reproduced one pre-existing but newly consequential defect:
item-only list matches could lose a preceding list title. Codex repaired that defect,
added an expander-to-focus closure test, bumped the protocol prompt contract to v4 and
kept terminal v3 jobs status-compatible when the source revision is unchanged.

## Boundary Check

- The execution route was `Pi/deepseek/deepseek-v4-flash`, effort `max`, one session,
  no fallback.
- The runner report records edits only in the authorized source/test set and no service,
  real-provider, runtime-database or full-suite activity by the delegated role.
- Runner-owned output remained under `runs/`; Codex performed the later bounded
  remediation directly in the current workspace.
- No candidate was accepted/rejected, no mapping was adopted/assembled/confirmed/
  activated, and no medical-writing business file was modified by this slice.

## Codex Verification

- Frozen RUX projections retained structural closure:
  visit `200→91`, study treatment `200→139`, safety `200→148`,
  efficacy `95→68`, early withdrawal `169→70`, data quality `53→33`.
- All retained primary table roots preserved their same-row/header bundles:
  `bad_table_roots=0`.
- Frozen conflict sets were small and satisfiable under the current budget:
  visit and study treatment each had one 3-ID conflict; the other four had none.
- The new backward-title regression and expander→focus closure test passed.
- Final focused three-file result after prompt-v4/status-compatibility remediation:
  `189 passed`.
- Full medical-monitoring regression after the structural remediation:
  `1144 passed, 4291 deselected, 27 warnings, 0 failed`.
- The final prompt-v4/status-compatibility patch was covered by the 189-test focused
  suite. A second full-suite run was deliberately not repeated because it changed no
  clinical validator, packet-construction algorithm or shared downstream contract.

Final SHA-256:

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_source_packet.py` | `f23be40c5e55bc6156f7f44252657cad15752c250bd3f1f327033dfc0a2d9745` |
| `services/api/app/monitoring_ai_service.py` | `210d90a19f72fdda307236f378083478222f14fe6cfa9e34983c4f2cdb47e80e` |
| `services/api/app/monitoring_protocol_preparation_service.py` | `96e55916cd136617a2c152eb7877376dcdf41c95a984e9f3f54ae1738c2b8be5` |
| `tests/test_monitoring_ai_source_packet.py` | `b2db87dea0cb4343e6bd946a2db996130b85ab5615d71617413eaf648b73adca` |
| `tests/test_monitoring_ai_service.py` | `67576b1e6943e86206eff261ef2b47c982e0ff68fbc509b3705b5211c30e5e47` |
| `tests/test_monitoring_protocol_preparation.py` | `67c916a4a5eab2a8218a520687420bf2155d8e58acd1310e5e62871869db2024` |

## Delegated-Agent Output Review

The handoff was traceable and technically useful. Its original statement that no prompt
version migration was needed became stale after Codex determined that provider-visible
prompt semantics had materially changed. Codex therefore introduced v4 rather than
silently reusing the v3 contract. Its original list-closure confidence also depended on
correct upstream role assignment; conference challenge exposed the backward-title gap,
which Codex closed before real RUX execution.

## Hermes Execution Review

The runner-owned Hermes execution handoff was accepted as bounded implementation
evidence, not as final authority. Codex independently checked its source claims, real
frozen RUX projections and test results, then revised the two material gaps described
above. No unsupported clinical or release conclusion from the delegated output was
carried forward.

## Residual Risk

- Legacy/mixed packets that cannot be structurally focused still use passthrough; the
  metadata label could be made more precise, but this does not remove evidence or relax
  validation.
- Counting mandatory conflict evidence inside the 50-ID union can become unsatisfiable
  for future large conflicts. The six current RUX topics have at most three conflict IDs,
  so this is not a blocker for this run.
- Real v4 RUX topic outcomes are runtime evidence and are recorded separately from this
  code-review verdict. They cannot be inferred from passing tests.
