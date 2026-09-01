# 医学作者选择即确认：Codex 组合验收

日期：2026-07-25

## 结论

接受本轮“医学作者选择即确认”状态机切片，尚不等同于整套医学写作系统发布放行。

## 已验收语义

- PICOS 选择候选即形成域级作者确认；保存理由表示修订并采用，不再另设“确认当前域”。
- 理由缺失只作为内容完整性门阻断版本快照，不撤销用户已经作出的选择，也不制造第二次医学批准。
- 全部域完成后，用户只执行“生成版本快照与撰写交接”技术动作。
- 历史 `in_medical_review` 和 `returned_for_revision` 可经当前 UI 使用的接口迁移，原快照、审批绑定和审计历史保留，审批中心待办清除。
- handoff 按业务身份幂等；不同客户端 key、重复点击、并发、刷新、进程重建均返回同一当前 handoff，新 revision 使用新的 snapshot/handoff。
- 历史 `approved + not_admitted` 译文可由当前作者一次确认并原子准入。
- 来源、解析、hash 或 revision 变化后，历史确认保留为历史，不计入当前 `author_confirmed_count`。
- 非当前 translation revision 的退回或拒绝明确返回 stale，不写假成功 review。
- 两个项目使用相同 batch/translation ID 时，确认、失效、brief、统计和审计互相隔离。

## Codex 验证

组合运行以下 15 个测试模块：

```text
tests.test_evidence_picos_workflow
tests.test_evidence_picos_approval_api
tests.test_writing_reference_admission_repository
tests.test_writing_reference_translation_batch
tests.test_writing_reference_translation_service
tests.test_writing_reference_repository
tests.test_writing_reference_api
tests.test_medical_writing_revision_application
tests.test_medical_writing_author_freeze_backend
tests.test_frontend_evidence_design_contract
tests.test_frontend_medical_writing_translation_batch_contract
tests.test_frontend_medical_writing_contract
tests.test_sqlite_evidence_design_store
tests.test_medical_writing_protocol_assembly_plan
tests.test_medical_writing_working_copy_persistence
```

结果：`233 tests`，全部通过。

独立审阅报告中的 P1-1 至 P1-5、P2-1、P2-2 均已通过源码复核和隔离 SQLite 回归。P1-6 的 5174/8911 build 不一致仍属于统一重启后的运行态发布门。

## 发布边界

全仓 `2728 tests` 当前仍有与本切片不同原因的医学写作失败，正在独立修复；在这些失败处理完、前后端统一重启并完成浏览器真实路径验收前，不宣称医学写作子系统已上线。
