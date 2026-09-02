# Phase C Technical Design

## Boundary

Phase C extends the existing workbench and `packages/medical_monitoring/`; it does not create another importer, runtime, database authority, or application shell. Original study directories are read-only inputs. Every copied byte, profile, mapping decision, fact, index, cache and log belongs under a project-specific isolated workspace.

Medical-writing routes, frontend components and assets are outside this design. Security features are also outside scope; source write-protection checks exist only to prevent accidental mutation of clinical source material.

## Existing Authorities To Reuse

- `domain.entities.SourceRevision.from_bytes` binds source bytes to project/version identity.
- `domain.entities.ListingSnapshot.from_content` binds a complete listing snapshot and structure.
- `graph.Store` persists source revisions, listing content, snapshot acceptance and canonical facts.
- `intelligence.normalization` provides deterministic value normalization while preserving raw values and uncertainty.
- Existing mapping/fact entities preserve candidate/fact separation, identity algorithm binding and provenance.
- The R7 product router and current medical-monitoring frontend remain the only backend and frontend product surfaces.

## C1 Data Flow

```text
原始 listing（只读）
  → 流式 SHA-256 + 文件清单
  → 临时隔离目录中的逐文件复制
  → 副本 SHA-256 复核
  → 原子切换为该批次的隔离输入
  → SourceRevision
  → 工作簿/表结构画像
  → ListingSnapshot（完整快照）
  → 用户预览
```

Copy failure, hash mismatch or unsupported structure leaves no accepted snapshot. A retry creates a new staging attempt; it never edits the original or silently reuses a partial copy.

## Structure Profile

The deterministic profile is format-neutral and data-driven. It records source file, table/sheet, row and column counts, headers, bounded sample values, inferred primitive types, date range candidates, missingness, and candidate subject/visit/date keys. Project-specific semantic meaning is not inferred in the deterministic layer.

The public projection translates this into four user questions: what was read, how much, what was recognized, and what still needs confirmation. Paths, hashes and internal identities are available only in a collapsed technical-detail view.

## Mapping And Fact Boundary

Deterministic hints and optional model output both create mapping candidates. Critical ambiguity prevents the affected facts from being generated. User confirmation produces a versioned `MappingDefinition`; only the deterministic service may materialize `MappingResult` and `CanonicalFact` from the confirmed definition and the accepted full snapshot.

Every fact retains an evidence locator containing project, source revision, snapshot, source file, table/sheet, row, column and raw value. The UI opens a bounded neighboring-row context rather than exposing an opaque internal identifier.

## Product Integration

The project-level medical-monitoring landing page adds one compact admission status card and one primary action. The three-step wizard is implemented inside the existing feature route:

1. 选择数据；
2. 查看系统识别结果；
3. 确认需要人工判断的字段。

The five-project overview uses status and counts, not engineering labels. Wide-screen is the only visual acceptance viewport for this phase. Browser validation uses ego(lite), not Playwright.

## Rollback Shape

Before a batch is accepted, deleting its isolated staging attempt is safe and does not affect any project source or accepted snapshot. After acceptance, rollback means selecting the previous accepted snapshot; no source or accepted record is overwritten. Broad deletion of historical isolated data remains user-confirmed work for Phase F.
