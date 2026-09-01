# OCR 证据与 Flash→Pro 设计 Codex 验收

日期：2026-07-25  
状态：技术增量路线接受；两处交互/状态机建议修正后实施

## 接受的技术结论

- OCR 选中页以不可变 PNG sidecar 持久化，不写 SQLite BLOB；extraction 中记录页码、200 DPI、尺寸、字节数、PNG hash、模型、profile、OCR 文本 hash、字符数、selection reason、状态和 span。
- OCR 返回空文本也必须留下 `empty_text` 页级证据，但不创建正文 span。
- 旧 extraction 不回写，解析为 `legacy_metadata_only`；需要完整证据时显式 re-extract。
- 图片只通过 project/artifact/extraction/page 绑定的只读 API 返回，客户端不能提交文件路径。
- 上层阶段路由必须显式记录 provider、requested/response model、deployment profile、prompt、输入/输出 hash、父运行、失败分类和恢复 lineage。
- 正文翻译白名单始终只有 Hy-MT2。Pro 仅能重跑章节规划、译后整合/QC；译后整合仍须逐字保留 Hy-MT2 target map。
- `corpus_selection_support` 当前没有真实模型调用和 lineage，应诚实标为 `not_implemented`，不能用状态声明代替实现。
- Flash/Pro route-specific integration 必须有独立 fingerprint，不能覆盖同一章节既有结果。

## 修正一：Pro 升级不增加用户操作

医学经理不需要另行点击“升级到 Pro”。服务端按确定性状态自动执行：

1. Flash 的 provider timeout、429、5xx 或连接失败只走同模型有界重试，不升级。
2. Flash 结构输出在一次纠正后仍失败，且确定性 fallback 不能形成合法完整结果时，标记 `failed_escalatable` 并自动创建一次 Pro 子运行。
3. Flash 译后整合形成 `completed_degraded` 且 Hy-MT2 target map 完整时，可自动创建一次 Pro 上层 QC 子运行；Pro 只做结构/QC，不得改写正文。
4. Pro 成功则采用其结构/QC结果并保留 Flash 父运行；Pro 失败则保留 Hy-MT2 或确定性 fallback，异常进入用户处置。
5. 用户界面显示“Flash 已完成/重试/已升级 Pro/需处理”，但不要求用户选择模型。
6. 仍保留面向异常恢复的“重试上层分析”操作；请求不能携带 provider、model 或 base URL。

## 修正二：OCR 不做逐页人工审批

- 不要求医学经理对每个 OCR 页提交额外确认，也不新增“待医学批准”。
- 系统自动检查：PNG/hash/DPI、OCR 是否为空、页序连续、章节归属、图表页是否有结构结果、关键数字/单位/否定/时间窗的确定性保真。
- 全部自动门通过后，extraction 可继续进入章节规划和翻译；异常页集中进入一次批次处置。
- 医学经理可查看 200 DPI 原图、OCR 文本和问题原因，并在充分提醒后对内容校验进行 override。
- extraction review 可记录抽查/异常页的处置，但不把“所有 OCR 页各有一条人工 confirmed”设为批准条件。

## 实施顺序

1. Additive contracts。
2. OCR core、上层阶段持久层、translation orchestration 三个互斥写集并行。
3. API/状态接线串行合并。
4. 先跑单元、迁移、重启恢复和路由身份回归。
5. 再运行 CRSwNP `NCT02898454` 与 UC `NCT02819635` 两个真实产品批次。

