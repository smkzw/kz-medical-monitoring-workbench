# R7 Slice-08B 权威与产物桥接实现接受记录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08B_IMPLEMENTATION`

## 接受对象

本记录接受已冻结 v0.1+v0.2 合同下的 synthetic/offline 后端纵切：

- R5 `R5AuthorityPacket`、R6 四类 `ModeOutput` 与 R1 `ArtifactEnvelope` 的唯一权威桥接；
- R6 固定子项抽取、五类原子项、canonical 摘要及真实成员/文件字节复核；
- LaunchRegistry v3→v4 additive migration、四成员发布闭包、同事务 CAS 与读写双重防篡改；
- 产品路由的最小发布接线、错误分层、三模式 synthetic provider 正向/失败关闭路径。

主要实现文件：

- `poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity_bridge.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/__init__.py`
- `services/api/app/medical_monitoring_r7_product_router.py`
- 对应 R7 与产品路由测试。

## Codex 纠偏与确定结论

1. canonical digest 直接复用 `launch_registry.content_digest`；R5 包通过其冻结 dataclass 自校验，不调用私有 digest helper。
2. 非 mapping 输出 payload fail closed；R1 project/source/run 绑定失败不再被宽泛异常吞掉，既有 run 的项目、模式、截止点、修订和执行依据必须一致。
3. 新发布首次转为 available 时必须恰好 4 个成员、64 位 output-set digest 且成员集摘要一致；available v4 行读取时再次复核。迁移前全空 legacy available 行仅保留只读兼容。
4. 产品路由未知异常映射为不可恢复 `internal_error`；已知 registry/runtime/setup 错误保留各自稳定分层。
5. 调用方提供的“已验证”布尔值不是权威；结果开放仍由 R1 真实成员与字节、R5/R6 冻结身份及 R7 CAS 共同决定。

## 治理与独立验收

- Execution：`mm_r7_slice08b_authority_artifact_bridge_implementation_20260829`。三个工作项完成；Cursor 主路由健康检查失败后使用声明的 Gemini 3.7 Flash high fallback；`audit-execution` 与 execution review-gate 通过。
- Conference：`mm_r7_slice08b_implementation_acceptance_20260829`，同一 session `01a04cc9-08c0-7000-834e-3a7b7adc6cd9` 三轮复核；最终报告 `ACCEPT`，conference review-gate 通过。
- 独立验收推动关闭 Registry 四成员硬闸、available 读时成员摘要复核和未知异常不可恢复分层三项缺口。

## 确定性验证

- continuity bridge + continuity registry + launch registry：`74 passed`。
- 产品医学监查路由：`61 passed`。
- 全 R7 + 产品路由：`320 passed in 40.91s`。
- 74 项核心矩阵在 `PYTHONHASHSEED=0/1/42 × normal/-O/-OO` 九格均通过。
- R1 相邻：`56 passed`。
- 8911/5174 无监听；未运行真实项目、真实模型或产品服务。

## 外部漂移与残余边界

- R5 选定相邻测试有 12 个功能测试通过，但 readonly gate 对 `mm_r5/__init__.py` 的旧固定哈希失败；本 Slice 未修改 R5。
- R6 有 350 个功能测试通过，但医学写作聚合计数旧基线为 542、当前为 445；本 Slice 未修改医学写作。这两项作为并行工作区漂移保留，不能被本次接受覆盖或改写。
- R1 内容寻址提交中断可留下不属于 publication 闭包的 1–3 个 orphan；按现有 R1 协议它们不具权威性，后续由 orphan sweep 审计处理。
- synthetic `knowledge_package`、`input_authority` 等默认值只允许存在于显式注入 provider 的离线接线。真实 provider 切换时必须移除或改为必填，且本记录不得表述为真实项目贯通。

## 接受边界

本接受不包括 08C 中文跨轮投影、ego(lite) 视觉验收、08D 三模式综合回归、真实项目/模型医学质量、R7 总体、R8、商业化或监管结论。医学写作子系统未修改。

## 下一安全动作

进入 Slice-08C：先冻结中文跨轮连续性投影与视觉交互合同，再接入已接受的 08B 后端事实；重点验证项目→中心→风险→Patient Journey→来源的同一身份语境、前后轮变化与中高风险优先。随后使用 synthetic 数据在 ego(lite) 的 1280/1440/1920 宽屏完成实际交互和视觉验收。08C 完成前不得进入 08D；8911/5174 与真实项目保持停止，医学写作边界不变。
