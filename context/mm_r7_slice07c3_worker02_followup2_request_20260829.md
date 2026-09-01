# Worker 02 same-session correction 2: close final registry P2 findings

Continue in original Worker 02 session and registry-only boundary. Independent read-only acceptance found two
registry P2 gaps. Fix both without broadening scope:

1. `publication_fingerprint_payload` must normalize setup manifest to the canonical sorted
   `work_unit_id -> mandatory` mapping (and denominator if contractually included), so semantically identical
   accepted input shapes yield the same fingerprint. Add equality tests across compact mapping/work_units/list forms
   and a real semantic-drift inequality test.
2. `reserve_publication` must reject completion-dependent/pre-bound runtime/receipt/R5/S4 fields. The accepted
   product path reserves with runtime manifest fields unbound and later calls `bind_publication_runtime_manifest`;
   make this invariant explicit. Reject partial or fully pre-bound completion metadata at reserve. Preserve v1→v2
   migration of historical launch rows and existing publication replay behavior.

Run registry focused tests, py_compile and report exact counts. Do not edit router/R5/frontend/medical-writing or
start services, models or real projects. Return complete updated Worker 02 report; no final acceptance.
