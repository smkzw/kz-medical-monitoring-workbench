# 医学经理工作台 runs 磁盘清理分诊

日期：2026-07-30  
范围：`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runs/`  
方式：只读；未删除、移动或压缩任何文件；未读取浏览器 profile、凭据或秘密内容。

## 结论

- `runs/` 当前约 `14G`；其中 `runs/execution/` 约 `14G`，`mw_final_5x3_harness_20260728/` 约 `12G`。
- 七个重点轮次合计约 `10.54GiB`。最大占用不是状态文本，而是 A1 运行时的 `writing_reference_artifacts` 和 SQLite 运行时数据库。
- r11/r15/r20/r38/r39/r40 都已冻结为 BLOCKED/FAIL 或未完成，并被后续修复/重测轮次取代；它们的证据包仍被 `context/`、`records/`、`reviews/` 或后续门禁引用，不能整轮直接删除。
- r42 是当前恢复边界：`BLOCKED_ON_OCR_ROUTE_SWITCH`，已完成 `66/91`，必须保留其运行时数据库、引用产物、截图、`A1_HANDOFF.md`、`DEFECTS.md`、`FIX_RETEST_LEDGER.md` 和恢复状态。
- 第一批可执行候选：仅在完成下文验证后，删除旧六轮（r11/r15/r20/r38/r39/r40）的 `writing_reference_artifacts`，预计释放约 `7,329,912KB = 6.99GiB`。r42 不在此候选中。
- 更大批量的旧轮次整轮离线归档理论可释放约 `9.09GiB`，但归档必须保留原目录结构和证据校验值；本次未执行归档。

## 状态与取代关系

| 轮次 | A1 关键状态 | 当前引用/恢复判断 | 建议 |
|---|---|---|---|
| `release-r11-20260729` | `COMPLETION_STATUS=BLOCKED`；候选投影在确认后消失；文档验证未完成 | `context/mw_final_5x3_release_r11_20260729_context.md` 明确要求冻结证据、不得继续复用；已被后续轮次取代 | 状态、截图、证据、DB：`ARCHIVE`；缓存：按下表再生删除 |
| `release-r15-20260729` | `BLOCKED`；结构锚点缺失；要求修复后新 clean project 重跑 | `context/mw_final_5x3_release_r15_20260729_context.md` 与 A1 `BLOCKED.md` 保留新 clean round 边界 | 同上 |
| `release-r20-20260729` | 首个实质性 P0：候选研究与文档源身份不一致；冻结 | `records/execution/mw_final_5x3_release_r20_20260729/A1_codex_luna_high_e2e_record.md` 明确不复用 r19 浏览器/DB 状态；r20 作为缺陷证据仍有审计价值 | 状态、截图、缺陷证据：`ARCHIVE`；缓存：按下表再生删除 |
| `release-r38-20260729` | `blocked`；11 份文档未形成可确认 M11 锚点；`HANDOFF.md` 存在 | `records/execution/mw_final_5x3_release_r38_20260729/ROUND_STATUS.md` 为 `BLOCKED_EVIDENCE_PRESERVED / SERVICES_STOPPED`；保留浏览器 trace zip | 状态、截图、trace、前端快照：`ARCHIVE`；缓存：按下表再生删除 |
| `release-r39-20260730` | `not_reached_blocked`；99/99 后停在 `等待处理文件核验` | `context/mw_r39_release_gate_context.md` 及 r39 A1 证据仍被 r40/r42 复核引用 | 证据 `ARCHIVE`；缓存：按下表再生删除 |
| `release-r40-20260730` | `INCOMPLETE_NOT_PASS`；99/100 后出现明确终端失败 | `context/mw-final-5x3-r40-A1-lazy_context.md` 与 r40 `DEFECTS.md` 是 r39 修复未验证的证据 | 证据 `ARCHIVE`；缓存：按下表再生删除 |
| `release-r42-20260730` | `BLOCKED_ON_OCR_ROUTE_SWITCH`；`66/91`，当前对象 `NCT03930732 / SAP_001.pdf` | `context/mw_r42_a1_release_retest_context.md`、`A1_HANDOFF.md` 给出当前恢复边界；不能被后续清理动作破坏 | 全部恢复资产 `KEEP` |

注：各轮 `ROUND_MANIFEST.json` 的 `PREPARED_NOT_EXECUTED` 是 harness 编排层状态；实际 A1 结果以轮次 A1 目录中的 `COMPLETION_*`、`BLOCKED.md`、`DEFECTS.md`、`HANDOFF.md`、截图和状态 JSON 为准。

## 大目录分诊

路径均相对于 `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/`。

| 路径模式 | 已观测大小 | 用途/引用状态 | 建议 | 预计释放 |
|---|---:|---|---|---:|
| `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts` | `1,354,388KB` | 下载的公开 Protocol/SAP、OCR/解析结果；r11 已冻结，来源与状态记录在同轮 evidence packet | `DELETE_REGENERABLE`，只在验证通过后执行 | `1,354,388KB / 1.29GiB` |
| 同路径 `release-r15-20260729` | `1,088,444KB` | r15 明确要求新 clean project，不得恢复半成品 | `DELETE_REGENERABLE` | `1,088,444KB / 1.04GiB` |
| 同路径 `release-r20-20260729` | `1,088,444KB` | r20 的源身份错配证据在小型状态文件、截图和 service evidence 中；缓存不是唯一证据 | `DELETE_REGENERABLE` | `1,088,444KB / 1.04GiB` |
| 同路径 `release-r38-20260729` | `1,088,444KB` | r38 的 `HANDOFF.md`、截图、trace zip、DB 保留审计链；引用缓存可重建 | `DELETE_REGENERABLE` | `1,088,444KB / 1.04GiB` |
| 同路径 `release-r39-20260730` | `1,354,388KB` | r39 被 r40/r42 后续重测取代；A1 状态与三张原分辨率截图保留 | `DELETE_REGENERABLE` | `1,354,388KB / 1.29GiB` |
| 同路径 `release-r40-20260730` | `1,355,804KB` | r40 终端失败和重测 ledger 仍是失败证据；缓存可由新 clean round 重建 | `DELETE_REGENERABLE` | `1,355,804KB / 1.29GiB` |
| 同路径 `release-r42-20260730` | `1,222,972KB` | 当前 66/91 恢复边界；`A1_HANDOFF.md` 要求保留已完成 OCR 结果 | `KEEP` | `0` |
| 以上旧六轮 `writing_reference_artifacts` 合计 | `7,329,912KB` | 六轮均非当前恢复轮；不能据此删除其状态证据 | `DELETE_REGENERABLE`，分轮执行 | 约 `6.99GiB` |

### 运行时数据库与 WAL/SHM

路径模式：`rounds/release-r{11,15,20,38,39,40,42}-*/slots/A1/lazy_medical_writer/runtime/*.sqlite3*`。

- `writing_reference.sqlite3` 单轮约 `211–342MB`；七轮合计约 `1.86GiB`。它承载 source preparation、文档验证、任务和运行时状态，不等同于缓存。
- 其余 `medical_writing_*`, `source_content_validations.sqlite3`, `user_projects.sqlite3`, `workbench_runtime.sqlite3` 以及对应 `-wal/-shm` 也是恢复/审计状态。每轮 `clean_state/READ_ONLY_INVENTORY.json` 标记为 `READ_ONLY_INVENTORY_ONLY`，`SNAPSHOT_DELETE_PLAN.json` 也只是 `PLAN_ONLY / REVIEW_ONLY_AFTER_VERIFIED_SNAPSHOT`。
- r42 全部 `KEEP`。旧六轮建议 `ARCHIVE`，不要直接 `DELETE_REGENERABLE`；如果需要释放约 `1.63GiB` 的旧轮运行时空间，应先做只读 SQLite 完整性检查、快照和哈希，再离线归档原目录。

### 截图、PASS/FAIL、hand-off、源身份和测试证据

- `.../slots/A1/lazy_medical_writer/screenshots/`：七轮约 `40MiB`（约 `41.8MB`），包含原分辨率界面、阻塞点、PASS gate 前后状态；`KEEP`。若已完成离线证据归档，可 `ARCHIVE`，不建议删除。
- `.../slots/A1/lazy_medical_writer/{BLOCKED.md,DEFECTS.md,FIX_RETEST_LEDGER.md,HANDOFF.md,A1_HANDOFF.md,COMPLETION_*.json,source_receipts.json,pipeline_lineage.json,document_validation_and_resume.json,quality_scorecard.json,browser_qc.json}`：`KEEP`。这些文件是状态、源身份、失败原因、恢复边界和测试证据，不是再生缓存。
- `release-r38-20260729/slots/A1/lazy_medical_writer/a1_*_browser_trace.zip`：约 `129MB`，属于浏览器测试证据；`ARCHIVE`，不删除。
- `.../frontend_snapshot/`：r38/r39/r40/r42 各约 `2MB`，属于构建/前端证据；`ARCHIVE`（r42 `KEEP`），释放空间很小，不作为第一批删除对象。
- `.../node_modules/`：在本次扫描的整个 `runs/` 下未发现目录，大小 `0`；无候选。
- `release-r11-20260729/.../browser_profile/`：约 `302,628KB / 296MB`，只出现在 r11。目录含浏览器会话/缓存类文件，并存在敏感命名文件；本次未读取内容。`HOLD`，需单独的秘密/会话审查后才可决定归档或删除，不纳入安全删除估算。

## 删除前验证命令（仅建议，不要照此执行清理）

以下命令只做验证；把 `ROOT` 设为工作台 implementation 根目录。执行删除前必须确认没有服务/浏览器进程打开目标轮次。

```bash
ROOT="/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench"
HARNESS="$ROOT/runs/execution/mw_final_5x3_harness_20260728"

# 1. 确认旧轮仍是冻结证据，且 r42 仍存在恢复资产
for r in r11-20260729 r15-20260729 r20-20260729 r38-20260729 r39-20260730 r40-20260730; do
  A1="$HARNESS/rounds/release-$r/slots/A1/lazy_medical_writer"
  test -s "$A1/DEFECTS.md" && test -s "$A1/FIX_RETEST_LEDGER.md"
  test -s "$A1/BLOCKED.md" -o -s "$A1/COMPLETION_BLOCKED.json" -o -s "$A1/document_validation_and_resume.json"
  test -s "$A1/source_receipts.json" -o -s "$A1/pipeline_lineage.json"
  lsof +D "$A1" 2>/dev/null || true
done
test -s "$HARNESS/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/A1_HANDOFF.md"
test -s "$HARNESS/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/document_validation_and_resume.json"

# 2. 仅验证 JSON 可读性和关键恢复/缺陷文件的哈希，绝不打开 browser_profile
find "$HARNESS/rounds" -path '*/browser_profile/*' -prune -o \
  -type f \( -name 'ROUND_MANIFEST.json' -o -name 'BLOCKED.md' -o -name 'DEFECTS.md' \
  -o -name 'FIX_RETEST_LEDGER.md' -o -name 'HANDOFF.md' -o -name 'A1_HANDOFF.md' \
  -o -name 'COMPLETION_STATUS.json' -o -name 'COMPLETION_BLOCKED.json' \
  -o -name 'source_receipts.json' -o -name 'pipeline_lineage.json' \
  -o -name 'document_validation_and_resume.json' \) -print0 | \
  xargs -0 -r shasum -a 256

# 3. 对拟归档的旧轮运行时数据库做只读完整性检查
for r in r11-20260729 r15-20260729 r20-20260729 r38-20260729 r39-20260730 r40-20260730; do
  RUNTIME="$HARNESS/rounds/release-$r/slots/A1/lazy_medical_writer/runtime"
  for db in "$RUNTIME"/*.sqlite3; do
    test -f "$db" || continue
    sqlite3 "file:$db?mode=ro" 'PRAGMA integrity_check;' | grep -qx ok
  done
done

# 4. 确认第一批候选只包含旧六轮 writing_reference_artifacts
find "$HARNESS/rounds" -path '*/browser_profile/*' -prune -o \
  -type d -name writing_reference_artifacts -print
```

## 删除/归档方案、回滚与再生

### 第一批：仅删除旧六轮可再生缓存

验证通过、且确认没有外部记录指向缓存内部文件后，目标只能是上表六个精确的 `writing_reference_artifacts` 目录。不要用 `rm -rf rounds/release-r*` 这样的整轮命令。建议先把清单和哈希输出保存到任务外部的受控审计位置，再由人工执行精确删除；本次没有执行。

```bash
# 示例：人工复核后才可执行；本次未执行
rm -rf -- "$HARNESS/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
rm -rf -- "$HARNESS/rounds/release-r15-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
rm -rf -- "$HARNESS/rounds/release-r20-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
rm -rf -- "$HARNESS/rounds/release-r38-20260729/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
rm -rf -- "$HARNESS/rounds/release-r39-20260730/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
rm -rf -- "$HARNESS/rounds/release-r40-20260730/slots/A1/lazy_medical_writer/runtime/writing_reference_artifacts"
```

回滚：删除本身没有本地回滚；只能从事先制作的原目录归档恢复，或开新的 clean round 重新下载、提取、OCR、验证公开 Protocol/SAP。不要把 r11/r15/r20/r38/r39/r40 的半成品项目恢复为 PASS，也不要用旧缓存绕过 r42 的 OCR 路由门禁。

### 第二批：旧轮次离线归档

把旧六轮整轮（约 `9.09GiB`）保留为只读归档，可以释放工作盘空间，但归档必须包含原目录结构、状态文件、SQLite、截图、trace、源身份和哈希清单。归档前后用 `du -sk`、文件数和哈希复核；r42 不参与整轮归档。

### r42 再生/恢复

r42 不能通过删除缓存来“再生”。应先修复可见的 PaddleOCR-VL-1.6 official jobs-API primary、GLM-OCR fallback、DeepSeek V4 Flash cross-OCR consistency 和 pause/switch-at-next-document 能力；然后从 `A1_HANDOFF.md` 给出的现有项目和已完成 checkpoint 恢复，保留已完成 OCR 结果，不新建项目、不重跑已 terminal 文档。

## 本次动作边界

- 只执行了目录大小、文件名、文件计数、状态文件的受限文本/JSON 摘要和引用路径扫描。
- 未读取 `browser_profile` 内容，未读取凭据、环境变量、会话秘密或 `passwords.txt` 等敏感命名文件内容。
- 未删除、移动、压缩、改写、重命名任何 `runs/` 文件。
- 报告本身写入：`context/mw_disk_cleanup_triage_20260730.md`。

## Codex 执行记录

- 2026-07-30 11:19：逐目录完成存在性、打开句柄和 r42 恢复资产检查。
- 精确删除 r11/r15/r20/r38/r39/r40 六轮的
  `runtime/writing_reference_artifacts`；未删除整轮目录、数据库、截图、
  trace、缺陷记录、handoff 或前端快照。
- 删除前合计 `7,329,912 KiB`；删除后 `runs/` 总占用
  `7,711,052 KiB`，约释放 `6.99 GiB`。
- r42 的 `A1_HANDOFF.md` 与
  `runtime/writing_reference_artifacts` 均在删除后复核存在。
- 未处理 r11 `browser_profile`，未读取或删除任何可能含会话信息的文件。
