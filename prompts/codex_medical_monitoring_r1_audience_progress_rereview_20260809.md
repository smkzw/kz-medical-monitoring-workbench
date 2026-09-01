请在同一只读验收 Session 中复核当前文件系统，仍不得修改任何文件。

上一轮 VETO 后仅修改：

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_audience_progress.py`

请重新读取当前版本，不能依赖上一轮缓存。修复声明仅作复现索引，不是结论：

1. audience 英文内部词识别覆盖 `_id`、`_url` 等后缀，并增加 hash/node/runtime/endpoint 等；
2. 任意协议地址、绝对/相对技术路径、常见文件后缀、localhost/IP:port、反斜线均拒绝；
3. known scope 的 target 统一校验，unknown scope 直接失败关闭；
4. retry/begin 事件仅允许 running，重复 running 记录失败关闭；
5. 新增 provider_id、backend_url、hash、node、路径、ssh、IP、unknown scope、
   retry 状态错配与重复 running 对抗测试。

Codex 主进程已运行但不能代替你的复核：

- focused audience：21 passed；
- audience + authoritative progress：58 passed；
- R1 core：212 passed；
- scoped Ruff 与 compileall：pass。

请重新执行上一轮 P1/P2 的全部 probe，并扩展检查明显变体。输出新的 ACCEPT/VETO、P0-P4、
实测命令/结果、无问题范围和残余风险。若接受，明确这是 isolated synthetic/offline R1
audience-progress 切片接受，不是 R1 总体、产品集成或真实项目接受。
