Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09d_implementation_20260831`, role `worker_02`.

Stay inside `artifacts/mm_r7_slice09d_implementation_20260831/`; do not modify product source, real projects, services, browser/model paths, medical writing, or runner-managed reports.

Implement only the non-Git copied-workspace source revision evidence required before the full accepted-seam run:

1. Add a stdlib-only versioned source-copy identity builder/validator. Pin every relevant accepted R1/R7 product source file actually imported by the adapter, all 09D implementation/schema/test files, frozen contract bytes, corpus manifest/oracle and generator/guard sources. Record relative path, bytes, SHA-256, deterministic inventory SHA, Python/SQLite/arch/physical-memory facts, creation status, and exact scope. No timestamps or temp paths in identity.
2. Define `source_copy_sha256` as the deterministic inventory identity. `source_copy_unchanged=true` only after a second independent re-hash equals the frozen entries. Expose a measurement-runner input that consumes the identity file and independently validates it immediately before and after the run; only then set source revision to `copy:<sha>` and dirty_tree=false. Any mismatch/missing file must remain `environment_comparable=false` and fail closed; do not trust user-supplied `--source-dirty-tree false` alone.
3. Record the contract interpretation explicitly in the artifact: for this non-Git copied workspace, content-addressed source identity plus pre/post unchanged verification is the revision/clean evidence; it is not a Git commit.
4. Re-run a bounded C01 cold/warm accepted-seam smoke using this identity. Expected: adapter-readiness only, `environment_comparable=true` if all hashes remain unchanged, but `bounded_proof_incomplete=true` and accepted product capacity false.
5. Add focused mutation tests for changed bytes, missing file, forged inventory SHA, and post-run drift; regenerate consolidated manifest. Do not launch the full 30-cell run.

Return exact files, tests, source identity, bounded status/counts, and the final full-run command using the identity-file flag. Do not claim §3/§4 closure.
