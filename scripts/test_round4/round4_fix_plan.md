# 测试轮4会商决议与修复计划（round4_fix_plan）

日期：2026-09-22；基线：3cf5fa7。三份报告：/tmp/kz_test_round4/report_[ABC]_*.md。

## 轮4结论

与轮1R相比大幅前进：建项勾选→监查工作区→Listing接入→结构识别（54表/18万行、20表、10表全部识别正确且秒级）全通。**新阻断点收敛到一处**：研究文档核对（方案/eCRF → 文档权威 → 角色裁决）永远无法收敛——

- A（RUX，仅方案）：卡"补齐少量文件内容">25分钟，重传3次无效
- B（CSU，方案+eCRF）：到"还差一项关键信息"却渲染**空`<ul></ul>`**，无选项无按钮，死循环
- C（PSO，多组合9+次）：4秒失败到9.5分钟静止不等；readiness四角色全missing

## 根因（代码实证）

`resolve` 接口的 needs_user_input 分支返回 `headline="还差一项关键信息"` + `files=attention_files`（空），但：

1. **后端无选项结构**：reconcile 的未决角色（如 protocol 两侧分歧）没有生成"每个角色可选哪些文件"的结构化选项
2. **无提交路径**：`DocumentAuthorityPromotionRequest` 只收 `batch_id`，用户裁决无处提交——问句是死胡同
3. **evidence_incomplete 措辞歧义**：未决角色两侧都没绑定候选时（如只有eCRF的批次缺protocol），reconcile 返回"补齐内容"，实际是"缺文件/请上传或接受缺失"
4. **向导第3步状态不持久**：文件选择是组件本地state，导航即丢（A/B/C均报）

## 修复计划（F7垂直切片）

**F7a 后端选项结构**：needs_user_input 分支返回 `user_choices: [{role, options: [{candidate_id, filename, primary_decision, verifier_decision, confidence}]}]`——数据在 reconcile 内部已有（left/right selections）。

**F7b 用户裁决提交**：resolve 请求扩展 `user_role_selections: [{role, candidate_id}]`（extra=forbid保持）；workflow advance 接受用户裁决作为最终tie-breaker（审计记 user_adjudicated=true），未决角色有用户裁决即收敛。

**F7c 前端确认UI**：第3步渲染 user_choices 为单选（每角色一行：候选文件列表+「该角色缺失」选项）；提交时随 resolve 发送。替换空ul。

**F7d 措辞修正**：evidence_incomplete 且 unresolved 角色两侧均无绑定时，文案改为"未在已上传文件中识别到{角色}文件——请上传或确认该角色缺失"。

**F7e 向导状态持久**：第3步已选文件列表从后端 study-documents GET 恢复（该接口已存在），不依赖组件state。

**F7f 台账接线**（A-P0-2）：Listing 识别完成后写来源台账登记行（现仅在facts物化后写？核实后补）。

## 非缺陷确认（诚实行为）

- A报"IB/SAP可稍后添加"：设计如此（非四角色强制）
- C报"映射接口500/422"：发生于文档核对未完成时的预期拒绝（mapping前置不满足），文案需在F7d中一并指引

## 验证路径

修复后：清洁空间→派发单测试者（glm最弱通道）走通 建项→三类文件→裁决UI作答→promoted→mapping→facts→监查就绪 全链；通过后再全员重派。
