# M0 合规止血 · 计划（2026-10-18）

## 目标
公开仓库（github.com/smkzw/kz-medical-monitoring-workbench）不含 PII/申办方保密内容（B01/B16）。

## 盘点结果（2026-10-18 实测）
| 项目 | 数量 | 说明 |
|---|---|---|
| git历史中的非fixture xlsx/pdf/docx | 19个 | protocol-corpus/raw/（5个PDF）+ fullchain_sar_rerun workspace（14个） |
| 工作区中的敏感文件（B01核心） | scripts/fullchain_sar_rerun_20260926/workspace_backup_stage4_20260927/ | 已备份到 ~/mm_private/b01_backup/（378M） |
| 疑似受试者号（S0xxxx形态） | 25个唯一编号，38个文件 | packages/services/tests/scripts |
| /Users/smkzw 绝对路径 | 239个文件（源码10+测试24+scripts 205） | tests/的24个已改为环境变量+local_only标记 |

## 改动文件
- 不改产品代码（M0只做删除/历史改写/.gitignore/pre-commit/CI）

## 步骤
1. ✅ 本地备份 B01 敏感文件（~/mm_private/b01_backup/）
2. ✅ tests/ 绝对路径→环境变量 + local_only标记（已完成，属M1范围但先做了）
3. ⏳ .gitignore 追加规则（xlsx/pdf/docx白名单外拒绝、backups/、runtime/*.log、*_evidence.jsonl）
4. ⏳ scripts/ci/pii_scan.py（pre-commit + CI钩子）
5. ⏳ **不可逆**：git filter-repo 改写历史 + 强推（等用户授权）
6. ⏳ B16 受试者号替换（在filter-repo的--replace-text中一并做）
7. ⏳ gitleaks扫描（有则轮换key）

## 风险
- filter-repo 改变所有 SHA → 并行子系统需重克隆
- GitHub 缓存视图需手动清除请求
- 如有 fork 仍含旧历史

## DoD
- [ ] 新克隆 `git log --all -- '*Data Listing*' '*.xlsx' '*.pdf' '*.docx'` 仅剩合成 fixture
- [ ] PII 扫描器在 CI 通过
- [ ] B16 的 25 个编号逐一核实并替换为合成格式
