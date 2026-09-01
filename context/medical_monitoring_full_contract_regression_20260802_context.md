# Context: medical_monitoring_full_contract_regression_20260802

## Goal

Obtain one current, reproducible regression signal for the complete Python
medical-monitoring test surface before moving to controlled runtime work.

## Source of truth

- current product `.venv`;
- all `tests/test_monitoring*.py` files;
- current product and workspace `AGENTS.md` files;
- protected frontend source hashes and 8911/5174 listener state.

## Coverage

The 89-file collection spans source classification/intake, immutable batch and
diff behavior, protocol facts/rules, AI contracts and recovery, mapping,
clinical event/projection contracts, risk/disposition/CAS, assurance/daily-run,
release gates, and the current real-LOOP readiness/execution contracts.

## Interpretation

The 1,640 passing tests prove current deterministic and isolated contracts only.
They do not prove that the product can ingest the three original source sets in
the controlled runtime, that an independent provider returns acceptable output,
or that a senior medical monitor accepts the browser/scientific behavior.

## Next action

Keep the full regression as a release prerequisite. Resolve the real B6/source
and CAS gates first; then execute the three-project LOOP and consume its
scenario evidence with the execution validator.
