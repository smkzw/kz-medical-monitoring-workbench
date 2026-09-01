# 阶段 C：真实数据确定性接入

## Goal

五项目只读隔离副本准入、结构画像、mapping 与 canonical facts。

## Requirements

- Provide project registration, read-only isolated-copy import, source hash/read-only verification, and structure-profile preview.
- For each of the five projects, produce SourceRevision, ListingSnapshot, mapping candidates, user-confirmed critical mappings, and canonical facts.
- Run a snapshot diff where compatible real dual snapshots exist.
- Keep model-assisted semantic mapping configurable and evidence-bound.

## Acceptance Criteria

- [ ] All five projects parse into canonical facts from isolated copies.
- [ ] User spot checks map facts back to the exact original listing cells.
- [ ] Shared-core grep contains no project, proprietary column, drug, or disease constants.
- [ ] Independent review and user confirmation complete.

## Constraints

- Original project directories remain read-only; all outputs are isolated.
