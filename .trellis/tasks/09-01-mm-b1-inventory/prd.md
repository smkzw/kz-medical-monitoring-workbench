# B1 迁移盘点

## Goal

按产品真实 import 图盘点 R7 骨架及 R4/R5/R6 依赖，先形成 journal 迁移顺序。

## Requirements

- Trace every product import from the R7 medical-monitoring router into R7 and recursively into R4/R5/R6.
- Classify each module by target layer, owning tests, runtime consumers, and duplicate/obsolete status.
- Record the dependency-safe migration order in the Trellis journal, not in `context/`.

## Acceptance Criteria

- [ ] Inventory covers every direct POC import from the product router and all transitive local dependencies.
- [ ] Each source module has one target/disposition and test mapping.
- [ ] The next migration slice is small, dependency-safe, and explicitly named.

## Constraints

- Read-only reconnaissance only; do not move code during B1.
