# Codex Conference Review: mm_r7_slice_04_progress_contract_20260828

Date: 2026-08-28

## Verdict

**PASS AFTER REVISION — 合同已冻结。**

冻结文件：`context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`  
冻结标识：`FROZEN_R7_SLICE_04_PROGRESS_CONTRACT_V0_2`  
SHA-256：`a5033b871ffd025cc5dd6345fb9a1bd214e41f01e3893ef2f94ca7ac6d830745`

## Boundary Compliance

- 两席均在 runner 绑定工作台内只读审阅，没有编辑源码、启动 8911/5174、调用任务内模型、
  运行真实项目、访问前端或医学写作子系统。
- 两席均使用 guard 生成的 provider/model/effort，单轮完整返回，无 fallback、timeout、retry 或
  替代会话。
- Grok 报告开头含 runner 汇集的工具进度句，不影响其后完整 schema；其证据与结论由 Codex
  按源码独立复核，不把模型自述视为接受证据。

## Participant Outputs Reviewed

- Pi/google-antigravity `gemini-3.7-flash` high：完整输出，识别 R1 外键前置实体、未准备 GET
  隐式 SQLite 创建、中文字段预检与直接复用 R1 Store 的必要性。
- Grok Build `grok-4.6` medium：完整输出，识别 A→B→A 的历史 revision replay、R1 Store
  constructor 技术写入、`create_run`/source revision 身份弱重放、post-lock 固定范围、产品包装
  字段及 source packet 错误路径。

## Conference Panel Review

两席独立结论在核心边界上相互印证，但建议并非全部照收：

- 采纳：prepare 前置实体时序、runtime 文件存在检查、产品/R1 身份逐项对照、显式非空工作
  清单、内部单 node、中文 allowlist、账本对账 fail closed、同一 runtime 向 Slice-05 演进。
- 采纳并收紧：相同**当前**定义在产品层直接重放；历史非当前定义在本切拒绝，避免 R1 全局
  内容幂等返回旧 revision；核查前模式首次准备后冻结范围。
- 不采纳 Pi 的“允许省略工作清单并生成默认 synthetic 清单”，因为它会在编排计划缺失时伪造
  分母；合同改为必须显式提供非空清单。
- 不采纳 Pi 对已准备 GET 的“mtime 完全不变”主张；当前 R1 Store 构造包含 schema/WAL 技术
  初始化。合同如实限定为不改变业务事实，并保留未准备 GET 的物理零写入。
- 不修改 R1 已接受源码；历史范围重新采用与跨进程并发留待 Slice-05/08 明确设计。

## Main-Venue Codex Review

Codex 以当前源码为事实完成复核并修订 v0.2：

1. R1 `Store.__init__` 会 mkdir artifacts、打开 WAL、执行 schema 与 meta 初始化，证实原草案的
   已准备 GET “物理零写入”不可诚实验收。
2. R1 `set_manifest` 默认 idempotency key 含全局 definition hash，证实 A→B→A 会重放 revision
   1 而当前仍为 revision 2。
3. R1 `create_run` 与 `add_source_revision` 的同 ID 重放不比对完整身份，证实产品层必须逐项校验。
4. R1 `project_audience_progress` 只返回受众计数/阶段/动态；范围版本、模式、basis、截止点必须由
   产品包装层从绑定补充并再次扫描。
5. 实际 R7 产品表面为 `services/api/app/medical_monitoring_r7_product_router.py`；会商 context 中
   不存在的 `product_api.py` 已纠正为只作对照的 `mm_r7/api.py`。

没有运行实现测试，因为本会商只冻结合同且明确禁止源码实现。文件结构与合同 SHA 已核对。

## Codex Independent Verification

- 两份 participant 输出均存在且 schema 完整；runner 记录了 session、duration、usage、route 与
  fallback=null。
- 冻结合同包含明确路由、权限、runtime 路径、身份映射、请求/响应、revision 语义、中文投影、
  停止线和 11 项验收矩阵。
- 截图新增的受试者流向看板已单独记录，明确不进入 Slice-04；本合同无视觉交付，因此无需
  ego(lite) 验收。
- 本会商未使用 Hermes；有效 guard route 是 Pi 与 Grok Build 两席，故不存在 Hermes 输出缺失。

## Final Decision

允许进入 Slice-04 实现执行包。实现必须限制在 R7 POC/产品路由/聚焦测试和证据文件；保持
R1 源码、前端、真实项目、8911/5174、真实模型和医学写作不变。合同接受不等于实现或 R7 接受。
