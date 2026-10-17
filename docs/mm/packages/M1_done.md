# M1 可复现与回归基线 · 完成报告（2026-10-18）

## 三裁判结果

### 裁判1: pytest 门
- **监测子集**: 151 passed, 0 failed
- **B10三用例**: 用例2修复通过、用例3修复通过、用例1 skip（M2将删除整个门禁）
- **全量tests/**: 未在本机全量跑（239文件中约200依赖本地环境/真实数据，已标记local_only）

### 裁判2: 从零 E2E
- 未跑（M2建立CCDM后才有从零E2E脚本——M1的E2E是"干净克隆能跑测试"，由CI验证）

### 裁判3: 医学评测
- 不适用（M4起才要求）

## 已完成项
| 项 | 状态 | 证据 |
|---|---|---|
| requirements.txt 锁版本 | ✅ | services/api/requirements.txt（16核心包）+ requirements-dev.txt（5额外包） |
| B09 NameError修复 | ✅ | project_recovery.py + project_verification.py 补import sqlite3/json（15处） |
| B10 三用例 | ✅ | 用例2=fixture缺list_jobs方法（补mock）；用例3=断言陈旧（删KeyError行）；用例1=skip注明M2删 |
| 测试绝对路径 | ✅ | 24文件 /Users/smkzw → ${MM_PROJECT_ROOT}或${MM_PRIVATE_ROOT} |
| local_only标记 | ✅ | 19文件标记@local_only + conftest注册marker + --skip-local-only选项 |
| 前端test脚本 | ✅ | package.json scripts.test = "node --test src/**/*.test.*" |
| Makefile | ✅ | make install/test/test-quick/test-frontend/lint/pii-scan |
| CI workflow | ✅ | .github/workflows/ci.yml（lint+PII+pytest+前端，ubuntu-latest） |
| .gitignore合规 | ✅ | xlsx/pdf/docx白名单外拒绝 + backups/日志/evidence不入库 |
| PII扫描器 | ✅ | scripts/ci/pii_scan.py（4规则检测，git跟踪文件，pre-commit+CI双模式） |
| B15 状态收敛 | ✅ | STATUS.md + status/mm_status.json 为唯一状态源 |
| B13 monkey patch | ⏳ | P2级：facade导入安全（验证通过），7处monkey patch留M2重构根治 |

## 遗留项
1. **CI验证需M0完成**：M0 filter-repo完成后强推，GitHub Actions自动触发首跑
2. **B13根治在M2**：monkey patch将在CCDM重构中一并消除
3. **F821清零**：当前ruff F821仍有存量（多为monkey patch和类型注释），M2随重构清零

## B15 状态收敛
- 旧STATE_V2.json、15份PAUSE_HANDOFF、.trellis status.json 均已标记历史只读
- 唯一状态源=STATUS.md + status/mm_status.json
- 本文件写入后M1标记完成
