# 医学监查子系统 · 状态

## 待用户决定

### 1. M0 git历史改写（不可逆，需明确授权）
- **问题**：公开仓库 git 历史中含真实锁库 Data Listing（受试者级）、IB/方案/eCRF 等申办方保密文件（B01），以及疑似真实受试者号散布（B16）。
- **拟执行命令**（已在本地备份后执行）：
  ```bash
  # 1. 本地备份（先做，不改历史）
  mkdir -p ~/mm_private/b01_backup && cp -r scripts/fullchain_sar_rerun_20260926/workspace_backup_stage4_20260927 ~/mm_private/b01_backup/

  # 2. 改写历史（filter-repo，删除敏感文件路径）
  git filter-repo --path scripts/fullchain_sar_rerun_20260926 --invert-paths --force
  # （后续按 B01 工单补充 --path-glob 清理 *.xlsx/*.pdf/*.docx、--replace-text 替换受试者号）

  # 3. 强制推送
  git push --force origin main
  ```
- **影响**：
  - 所有 commit SHA 变化；并行子系统（医学写作）的 worktree 需重新克隆或 rebase
  - GitHub 上的缓存视图需向 GitHub Support 提交清除请求
  - 已有 fork（如有）仍含旧历史
- **默认选项**：待你审阅后明确说"执行"再动
- **等待期间**：M1 可复现工作不依赖历史改写，正在并行推进

## 当前包
M0 合规止血（准备阶段）+ M1 可复现与回归基线（并行推进中）

## 已完成
- [x] Review包入库（.trellis/tasks/10-18-mm-medical-core/）
- [x] STATUS.md + status/mm_status.json 建立（B15 状态收敛）
- [x] 旧循环/专项冻结（STATE_V2/PAUSE_HANDOFF标记历史只读）

## 三裁判最近结果
| 裁判 | 结果 | 报告路径 |
|---|---|---|
| pytest 门 | 未跑（M1 进行中） | — |
| 从零 E2E | 未跑 | — |
| 医学评测 | 未跑（M9 并行准备中） | — |

## 阻塞项
- M0 filter-repo 需用户授权（不可逆）

## 下一步
1. M0 准备：敏感文件盘点→备份→写命令清单→等授权
2. M1 并行：requirements 锁版本→去绝对路径→修 B09→判定 B10→前端 test 脚本→CI
