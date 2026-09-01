# 08C-4 worker_03 same-session visual follow-up

Continue the same bounded execution session. Codex opened the actual combined/original images after worker_04 and found one residual visible issue that `FINDINGS_revised` did not capture:

- At 1280 Journey, the right-side `检查依据` risk cards have title/domain/severity/change badges competing in one narrow row. The third item visibly overlaps/clips (`检验检查 · 中风险` and adjacent badges), reducing rapid scan quality. This is an open P2 under the frozen contract despite structured `p0_to_p4_clear=true`.

Perform a targeted user-visible repair using the existing design system: establish a stable compact card grid/row hierarchy so title/domain, subject/meta, severity and change each remain readable at 1280 without ellipsis hiding the clinical identity. Do not reduce below the frozen 12/14px hierarchy or introduce new assets/dependencies. Preserve 1440/1920 and current navigation.

Then:

1. rebuild;
2. temporarily restart only the isolated 8984 fixture if needed (8911/5174 stay stopped);
3. reuse ego(lite), capture revised 1280 Journey and affected risk drawer state, plus structured bounding-box/overflow evidence;
4. re-open and inspect the revised original image;
5. regenerate affected side-by-side collage and add the missing `1920_drawer_push_side_by_side.png` from already-preserved baseline/revised pairs;
6. update `FINDINGS_revised.json` only if the visual P2 is truly closed;
7. stop 8984 and complete any temporary ego task space before returning.

Return exact changed files, screenshots opened, measurements, tests/build, and residual P0-P4. Do not claim final Codex or visual-conference acceptance.
