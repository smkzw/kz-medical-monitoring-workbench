# Codex 主会场复核：医学写作文件内容核验与确认沿用

日期：2026-07-12  
结论：`accepted_with_verified_changes`

## 参与产物

- `aishuo/MiniMax-M3`：同会话三轮完成，纳入。
- `opencode-go/qwen3.7-plus`：同会话三轮完成，纳入。
- `buddy/kimi-k2.7-code`：1800秒硬等待后仍无可恢复实质产物；排除。
- `opencode-go/mimo-v2.5`：按备用路由启动，但读取截图时 provider HTTP 400，未建立可用会话；排除。
- Codex：负责最终源码判断、真实Chrome验收、异常分支运行和生产写入。

## 采纳与修正

1. 采纳Qwen关于异常状态视觉层级不足的意见：新增 `.writing-reference-validation.requires-review`，使用橙色左边框和浅色背景。
2. 采纳确认后理由过弱的意见：改为“已确认沿用”状态标签加正式“医学确认理由”审计摘要。
3. 在会商意见基础上进一步收紧交互：每个当前 warning/mismatch 必须由用户逐项勾选；仅填写理由时按钮保持禁用。
4. 后端再次核对提示代码全集、当前修订和状态；`confirmed`、已确认沿用或不存在提示项的记录不能被 override。
5. 长URL继续保留完整 `title`，核验值允许任意断行，文档行提供“公开原文”链接。当前不增加第二个重复来源链接。
6. 暂不折叠五项固定核验结果。真实异常状态在1600x1000下可通过AI rail内部滚动完成操作；规则数扩展后再基于实测决定分组或折叠。

## Codex 验证

- 正常RUX：453项候选、真实NCT05014438 Protocol/SAP、164页/2081 spans、内容匹配、翻译v2待医学审核，桌面QC无失败。
- 正常PNH：49项候选、真实NCT06578949 Protocol、89页/1754 spans、内容匹配、翻译v1待医学审核，桌面QC无失败。
- 异常分支：在临时运行库副本中将真实RUX文件类型设为 `Publication / Journal Article`。未填理由、仅填理由、未逐项确认三种状态均不能提交；勾选全部提示并填写理由后API返回200，生成revision 4和 `user_overridden` 当前状态。
- 异常状态截图显示提醒、逐项勾选、理由和按钮均在AI rail中可达；确认后原“不一致”检查仍保留，理由可见，无横向溢出。
- 全仓库 `638 passed`；前端生产构建通过，仅保留既有大chunk告警。

## 剩余边界

- 外部语义为“已确认沿用/confirmed after warning”，不是“内容匹配”。当前SQLite v2内部枚举仍为 `user_overridden`，后续统一跨子系统契约迁移时改名，不在本轮破坏既有运行库约束。
- PNH竞品语料链可用，但项目级医学写作文档会话尚未建立；不能把证据面板通过解释为完整PNH方案编辑闭环完成。
- 客户端actor仍为 `unverified_client_claim`，不是电子签名或身份认证后的正式批准。
