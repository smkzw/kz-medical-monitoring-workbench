# MY008 3-02 current-source visit mapping review — 2026-08-02

The canonical MY008 3-02 listing is the `原始数据/【3-02初治锁库后数据集】...xlsx`
copy with SHA `152b8c2eb4d398ca2cfd861ee7932942eb753d6494ae7c93a5806734d5ced106`
and size 15,149,424 bytes. It matches the earlier parser/precheck anchor and
freshly replays to 59 sheets, 82,583 rows, no warnings, and an empty PC3 sheet.
An alternate same-study copy under `NDA相关/SAE病例叙述-20250925/` has SHA
`c91193f290c4c7d7a568a0f94a9189e672c788aeac62176f46d105f51fc29703`; it is not
merged or approved as the baseline.

Direct read-only inspection shows that the current observation records carry
`表单集名称` and `表单集OID` visit metadata. `SUBJ` is a non-visit identity table.
This corrects the broad earlier wording that most event domains lacked an
explicit visit field. It does not clear mapping: protocol table 10 schedules
treatment-specific D70/D98 visits and V17/提前退出, while the listing uses V10
for D84, V12 for D126, V15 for D168, plus WITHDRAW, and has no observed D70/D98
labels. Listing OID ordinal therefore cannot stand in for protocol V-number.

The safe state is **record-level visit metadata observed; protocol-normalized
crosswalk blocked**. Keep the current source out of onboarding/AI/runtime until
an authorized review answers the arm-specific coverage and withdrawal/unplanned
questions, then replays the precheck using the current source hashes. B6 remains
pending review, C13/C14 remain blocked, and 8911/5174 must remain stopped.

Detailed evidence: `records/active_slices/medical_monitoring_my008_mapping_review_20260802/`.
