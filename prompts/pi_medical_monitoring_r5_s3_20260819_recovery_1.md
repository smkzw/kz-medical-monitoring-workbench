# R5-S3 contract same-session recovery

Your previous turn ended with a planning/reasoning dump and made zero filesystem edits. Resume the same session and execute now. Do not produce another plan-only response.

Workspace: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Read the current filesystem and the prior follow-up prompt:
`prompts/pi_medical_monitoring_r5_s3_20260818_followup_2.md`.

Apply every requested correction to the existing R5-S3 v0.2 contract artifacts, generator, verifier, and focused tests. In particular:

1. Move all acceptance-critical semantic recipes, source paths, hash DAG edges, hash algorithms, receipt recipe, and packet-id grammar into verifier-owned or externally pinned constants so coordinated artifact re-signing cannot alter them and still pass.
2. Add and enforce a typed `R5S3ClinicalDomainAuthority`; current-risk domain and severity must not come from untrusted member fields.
3. Strengthen the packet oracle to cross-check current references, marker/handoff identities, severity/action/member expansion, domain authority, center cells, and the separation of current versus resolved planes.
4. Replace all no-op challenge mutations, especially R5S3C-026..033 and R5S3C-057..060, with genuinely different mutations and exact expected projection/hash assertions.
5. Normalize the packet-id descriptor to the single-colon grammar everywhere.
6. Add negative tests reproducing all four previously accepted coordinated attacks: typed member domain substitution, typed member monitoring_priority substitution, audience hash self-edge, and sha256-to-sha1 receipt change. Add packet-negative tests for raw member high-risk refs and lifecycle domain/severity drift.

Run and report actual outputs for:
- generator `--check`
- verifier normal and `PYTHONOPTIMIZE=2`
- focused S3 contract pytest
- Ruff on changed Python files
- compileall on changed Python files
- a read-only check that port 8911 is not listening

Do not edit R4, frontend, services, medical-writing paths, real project data, or any product runtime. Do not start 8911. Return a compact final handoff listing exact changed paths, exact commands/results, residual uncertainty, and SHA256 values of all frozen contract files. If any gate fails, fix it in this same session before returning.
