# Resume release-r5 A1 engineer after tester-tool cancellation

Resume the same A1 engineer session and current isolated product state. This
is a continuation of
`A1_engineer_pi_alibaba_release_r5.md`, not a new scenario.

Your prior 15-minute shell polling loop was automatically cancelled by the
tester runtime. That cancellation is not evidence that the product pipeline
failed. Do not repeat a long polling loop, do not restart the project, and do
not modify product source.

Continue through real visual browser interaction from the current product
state. Use short, bounded checks no longer than five minutes when waiting is
unavoidable, then return to the browser. Distinguish product defects from
tester-tool limits. Preserve all evidence already observed.

Complete every required evidence file that can be supported. If a genuine
product blocker prevents complete protocol/DOCX/PDF/Word acceptance, record
the exact visible state, source/API/job lineage and bounded reproduction,
then finish the remaining structured evidence as BLOCKED rather than leaving
the run without a report. Do not create `PASS.md`.

Maintain `EXTERNAL_TESTER_REPORT.md` and end it with exactly:

- `A1_ENGINEER_EXTERNAL_TEST_COMPLETE`, or
- `A1_ENGINEER_EXTERNAL_TEST_BLOCKED:<short reason>`.
