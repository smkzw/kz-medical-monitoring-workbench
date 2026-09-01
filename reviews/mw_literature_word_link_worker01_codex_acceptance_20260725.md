# 文献重索引 worker_01 Codex 验收

日期：2026-07-25  
结论：后端切片接受；Qoder 三轮报告不作为验收依据

## 执行模型结果

- R01 将所有非 `apply` 状态阻断正式终稿，并包含无效测试。
- R02 修正了状态矩阵，但未删除旧测试，新增测试又错误调用 greenfield exporter。
- R03 仍未修改 RUX 正式终稿测试和 API header 测试，并新引入错误模块导入；报告明确把两项必做工作标记为 pending，却输出完成标记。
- 三轮后触发 no-progress breaker，停止继续向同一 worker 返修。

## Codex 最小修正

- `applied`、`preserved`、`not_applicable` 允许正式终稿，且
  `user_action_required=false`。
- 只有 `blocked` 阻断正式终稿；草稿保留原内容并返回非空处置提示。
- 外部文献管理器提示为：在 Word 临时工作副本中刷新或重新绑定引用，保存后重新导入。
- 未知 action 失败关闭为 `blocked`。
- RUX 原方案草稿保持原文、字段和字体，但明确返回 blocked；正式终稿在重绑定前失败关闭。
- greenfield 真实 200 导出响应稳定返回三个文献重索引 header。

## 决定性验证

```text
python3 -m pytest -q \
  tests/test_medical_writing_citation_export.py \
  tests/test_medical_writing_source_preserving_export.py \
  tests/test_medical_writing_document_export_api.py
```

结果：`44 passed, 8 warnings`。

```text
python3 -m pytest -q \
  tests/test_medical_writing_source_reference_reindex.py \
  tests/test_medical_writing_source_reference_reindex_real_projects.py
```

结果：`28 passed`。

`py_compile` 对 exporter、main 和三个聚焦测试文件通过。8 条 warning 均为既有
FastAPI `on_event` 弃用提示，与本切片无关。

## 未完成

- 稳定服务尚未重启，当前运行进程仍是旧构建。
- 前端处置提示与 Microsoft Word 原生跳转/更新域验收仍待 worker_02/03 和 Codex终验。

