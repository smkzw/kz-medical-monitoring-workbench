# R5-S5 Public Authority Producers v0.1 Acceptance Record

Decision: `ACCEPT_R5_S5_PUBLIC_AUTHORITY_PRODUCERS_V0_1`

Accepted scope: exactly the eleven create-only producer paths frozen by the
accepted public-authority implementation contract v0.4.2. This record freezes the
accepted producer bytes:

- `4767e28ab7e54a4fbc89e3e30a12448467597cdadfc06833f11158bc2aa54b4c`  
  `poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py`
- `0a519d6b93dee9bc06930707eed7f6b7f2be180fe2b35dc25d23ccf8ce918be7`  
  `poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py`
- `3463eedf0bad35596f9b1f28c9479c76fb0cffaf5977766e812839e342bd3243`  
  `poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py`
- `a4b9a2d681ca280ea344d36591eb7875e032dcf7e4b9209be34ba7bf5972c794`  
  `poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py`
- `eeffbcf0c07c130e3cb05f3ac19ba3f2698de6461344812c18c1c083234b0aa3`  
  `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py`
- `2aa3b626cfd0feda9a70a7416f564955a9c7378e66e26a8c2b2682bd9a20bb8c`  
  `poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py`
- `c8b3afefc49d3fc62eecf072f23b7a82d9bab2c5ae35852f482a19b9b618702d`  
  `poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py`
- `15a3de48c22e7417dd0b1159f5d696d90730c080856b3dda04a8ea552ef99e64`  
  `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py`
- `e5c9cdb5ff9989b1e8057a1624c618a4cdc93715275f3fd51a992ae395ef6299`  
  `poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py`
- `f6bee54e92820e48cd8a3b3111261308e639a3f61609b1c4b24073f8ef6e61b2`  
  `poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py`
- `8a0d0935a21e569cef078a08ff084367aa401c2e188f50d9ada7e77c9b734058`  
  `poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json`

Decisive verification:

- focused producer tests: `60 passed` in normal, `-O`, and `-OO` modes;
- exact accepted graph replay: `10/10`, covering `R5C-109`, `R5C-110`,
  `R5C-116`, and `R5C-157` through `R5C-163`;
- frozen source/input evidence: `29/29` SHA-256 values match;
- producer path surface: exactly `11/11`, with no missing or extra path;
- protected medical-writing boundary: `542` files with the accepted aggregate;
- port 8911: stopped, with no listening process;
- isolated conference: both participants returned the exact decision token above.

Known adjacent debt is not accepted or silently repaired here. The existing S4
artifact suite has five pre-existing failures: four arise from the 2026-08-19 S4
execution-context pin drift, and one is the superseded no-S4-runtime assertion.
The existing `mm_r5/__init__.py` to `mm_r4` import coupling also remains outside
the eleven-path boundary. Full R5 tests excluding the known stale S4 artifact file
reported `1349 passed`.

This acceptance does not accept S5 orchestration/runtime integration, UI,
browser/visual behavior, real-project execution, or model-mediated clinical
outputs. It does not start 8911 and does not modify or accept the protected
medical-writing subsystem.
