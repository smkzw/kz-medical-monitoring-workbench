# 医学监查子系统 R8 G4 合成通知与 §15.4 实施合同 v0.1

状态：`IMPLEMENTATION_CONTRACT_FROZEN_READY_FOR_GOVERNED_EXECUTION`  
日期：2026-08-31  
上位依据：R8 G3 通知决策合同 v0.3、R8-0 联合准入合同 §8.3、System Design v1.1 §15.4  
范围：仅 synthetic/offline；不启动服务、浏览器或模型，不读取真实项目，不修改医学写作子系统

## 1. 目标与完成证据

G4 交付两条相互独立、可组合重放的合成证据链：

1. 通知 seam：消费既有运行终态，形成唯一通知事实、幂等 outbox、应用内持久记录、合成系统通道证据和只导航意图；通知不得创建或改变运行。
2. §15.4 程序：编排并验证已接受的 R7 09A/09B/09E 备份、恢复、迁移、回滚和卸载原语；不得复制这些原语或建立第二套状态机。

完成必须有：新代码和聚焦测试、十三项逐项结果、canonical manifest/digest 与独立 replay、相邻 R7/G2 回归、发布清单更新、医学写作目录前后摘要一致、端口保持停止，以及独立审阅关闭 P0/P1。G4 通过不等于 G5/G6、真实通知、真实 §15.4、真实项目、真实模型或医学质量通过。

## 2. 工作包

### WI-1：通知 seam

新增 `deploy/medical_monitoring_local/synthetic_notification.py` 及聚焦测试。最小对象为：

- `TerminalEvent`：完整绑定 `project_ref + admission_id + run_id + terminal_status + terminal_revision`，保留上游终态；
- `NotificationStore`：内存合成 store，按完整身份+revision 幂等保存唯一事实、outbox 与应用内记录；
- `SyntheticNotificationAdapter`：能力状态仅为 `authorized|denied|unavailable|unknown`，通道证据仅为 `queued|accepted_by_platform|presented|unknown`；
- `build_navigation_intent`：只返回已有运行目标，重复点击无副作用；身份、admission、binding、版本、revision 或目标不一致时失败关闭。

硬门：非终态不生成事实；`complete` 仅在结果可访问时投影为 `analysis_complete`；其他冻结终态按 G3 中文模板原样投影；`revoked|re_admission_required` 不新建事实；系统通知不含项目、药物、疾病、受试者、风险、路径、模型、hash 或内部码；通道失败不得改写运行终态。

### WI-2：§15.4 合成编排与 replay

新增 `deploy/medical_monitoring_local/synthetic_15_4.py` 及聚焦测试。它只能调用或验证已接受的 09A/09B/09E 公共入口，并输出一份固定顺序、canonical digest 的 evidence manifest。十三项不得合并或省略：

| 序号 | 项目 | 程序证据 |
|---|---|---|
| 1 | 导出/导入 | 09A 确定性备份包导出并恢复到干净合成根 |
| 2 | manifest/identity/lineage | 包 manifest、项目 identity、来源与恢复 lineage 精确重放 |
| 3 | 备份损坏 | 成员或 manifest 损坏被拒绝且 live workspace 不切换 |
| 4 | 干净恢复 | 干净根恢复后由既有 verifier/manifest 证明一致 |
| 5 | 升级前保护 | 09E prepare-upgrade 先生成可验证保护备份 |
| 6 | 迁移成功 | 09B 支持的 legacy 合成 workspace 迁移到 current |
| 7 | 关键边界失败 | 在已冻结 fault point 注入失败并保留明确终态 |
| 8 | 原版本保持可用 | 迁移边界失败后旧 workspace 仍可打开或被完整回滚 |
| 9 | 实际 rollback | 09B 实际目录切换失败触发 rollback，非仅计划标记 |
| 10 | 凭据不明文导出 | 普通包成员与 manifest 扫描禁止凭据字段/值及 `.env` |
| 11 | 默认卸载保留数据 | 09E 默认 uninstall plan 明确保留项目数据、备份、导出与审计 |
| 12 | 显式清除预览/确认/取消 | preview、显式 confirm、cancel 三态均有证据；G4 只在临时合成根演练 |
| 13 | 混合版本与迟到回调 | 09B mixed-version/late-callback fence 阻断陈旧提交且不污染 current |

每项结果必须为 `passed|failed|not_evaluable`，包含公共原语/测试证据引用和不含真实路径的摘要。任一项非 `passed` 时总状态不通过。Replay 必须拒绝排序、内容、摘要、identity 或 lineage 被篡改的 manifest。

### WI-3：CLI、发布清单与相邻验证

在 `manage.py`/`manage.zsh` 增加一个明确标注“合成离线”的 G4 演练入口；更新 README 和 `release_sources.json`。CLI 只能操作临时 synthetic root，不允许用户传入真实项目路径，不启动端口。聚焦测试覆盖正常、失败关闭、中文用户文案、确定性和发布清单排除项。

## 3. 设计边界

- 产品实现不得出现真实项目名、疾病、药物、量表、风险类别、固定列名、Sheet、坐标或路径专有分支。
- 不调用独立 harness/LLM；G4 仅验证本地基础设施程序。后续真实语义提取仍必须由产品内独立 harness/LLM 执行，Codex 只负责 prompt/schema/validator/coverage/failure 边界。
- 不修改 `deploy/medical_writing_local`、产品服务/API/UI 或 R7 已接受原语；若公共入口不足，先记录缺口，不复制实现。
- 不把合成 adapter、组件测试或 manifest 结果称为真实用户可见、真实通知送达或真实项目验证。
- 不新增签名、密钥、鉴权、安全专项、移动端或商业化能力。

## 4. 验证顺序

1. 每个工作包先跑最小聚焦测试；
2. 联合运行 G4 聚焦套件，并对 canonical digest 做 normal/`-O`/`-OO` 与多 `PYTHONHASHSEED` 重放；
3. 运行相关 G2 分发与 R7 09A/09B/09E 相邻回归；
4. 静态扫描产品范围的真实项目/药物/疾病/量表/列名硬编码；
5. 核对 8911/5174/8984 停止及医学写作目录摘要未变；
6. fresh-context 独立审阅。只有全部硬门通过才可写 G4 接受记录并解锁 G5。
