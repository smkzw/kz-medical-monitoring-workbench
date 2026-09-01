# 医学监查 source-revision/source-token 严格形状边界（2026-08-02）

## 发现

与 B6 blocker `legacy_source_revision_token_missing_revalidation_required` 直接相关的
`monitoring_source_revision_compatibility.py` 原先会对若干非字符串输入调用 `str()`，并可能把 scalar
candidate ID 迭代成字符。source-revision、record/project identity 和 candidate source revision IDs
属于证据身份，不应由兼容转换补造。

## 修订

- revision、record/project identity、meaning/source token 和 comparison reason 只接受字符串；空值、
  数字、布尔和不合规字符 fail-closed。
- candidate source revision IDs 必须是非空字符串数组；不接受 scalar、数字或布尔成员。
- public identity/comparison dataclass 的直接构造也复用同一边界，不能绕过 parser/adapter 接受布尔
  source token 或非字符串 reason。
- 保持既有 legacy missing-token → explicit source-content revalidation 关系判定，不推断 candidate
  source bytes，也不授予 migration/approval authority。

## 验证

- `tests/test_monitoring_source_revision_compatibility.py`：**15 passed**。
- 排除会读取本机真实 RUX/MY009 文件的全量目录测试后，source-revision unit/compatibility：**19 passed，3 deselected**。
- disposition-chain、B6 activation、release-gate 相邻回归：**33 passed**。
- `py_compile` 与 Ruff 通过。
- 源/test SHA-256：
  - `services/api/app/monitoring_source_revision_compatibility.py`：`796e4f4408b0ef0ef4d9e784b491ea0de54021894e8f7255c86e0c91d805acc5`
  - `tests/test_monitoring_source_revision_compatibility.py`：`56796d3fd5cab86f6ba1acf1f98c815e4556dead48a43705c47a6b83b4de4184`

## 运行边界与失败路径

- 初次组合命令误触发 `test_monitoring_source_revision.py` 的本机 RUX/MY009 全量目录测试；发现后已
  终止精确 pytest 进程，未接受该命令结果，也未启动服务、provider、8911/5174 或写入权威 SQLite。
- 后续使用 `-k` 明确排除真实目录测试完成合约回归；未运行三个真实项目 LOOP，医学写作未触碰，
  18911/PID 43191 未触碰。
- 本修订只提高 lineage 输入完整性，不能替代真实 source-content revalidation、B6 reviewer outcome、
  aggregate/CAS replay 或商业发布证据。
