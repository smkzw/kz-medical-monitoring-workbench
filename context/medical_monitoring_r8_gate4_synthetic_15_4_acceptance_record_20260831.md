# 医学监查 R8 G4 synthetic 通知与 §15.4 程序接受记录

日期：2026-08-31  
状态：`REVISED_CANDIDATE_PENDING_G5_INDEPENDENT_REVIEW`  
范围：只接受 synthetic/offline 通知 seam 与 System Design §15.4 十三项程序准备；不接受真实通知送达、真实项目/模型/浏览器、医学质量、G5/G6 或 R8 总体

## 接受对象

- 实施合同：`context/medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1_20260831.md`
  SHA-256 `b55d263a499b424cd755a64998acbd4b1491ab1214fa54967e960be27133723c`
- 通知 seam：`deploy/medical_monitoring_local/synthetic_notification.py`
  SHA-256 `8d616a412e4a452b3a8beb03a50be0c5bbddf439bd331ef34145a27843e3f9fb`
- §15.4 编排/replay：`deploy/medical_monitoring_local/synthetic_15_4.py`
  SHA-256 `3b9a705c06013d602bed030eb8c686ccbf9fac7e923866b4cf79b5b85cd2d1a3`
- CLI：`deploy/medical_monitoring_local/manage.py`
  SHA-256 `4b7a646d306e92bdd098470371fb3b7da8cc7cba4d12e5c8357da3d0d4d96658`
- 说明：`deploy/medical_monitoring_local/README.md`
  SHA-256 `a04df4f8aeebfde84ed38cf78eb3840597ba94703fb643183cdef602aa0e93cc`
- 发布清单定义：`deploy/medical_monitoring_local/release_sources.json`
  SHA-256 `e5803a43ccaff6b33ed035d28d20275456f3a94862c1adf8927557aae9a26bec`

## 已关闭的阻断

1. 通知事实绑定 `project_ref + admission_id + run_id + terminal_revision`，保留原始终态，只对可访问结果作用户呈现投影。
2. 非权威/未冻结终态、无效 binding/capability、被撤销 admission、目标不可访问及身份/版本/revision 冲突均 fail closed。
3. outbox 只做一次系统通道尝试；重放不重复送达，通道异常不改写上游运行终态。
4. 应用内记录仅为 Path A 降级/对账面；点击只导航到已有运行，不启动、重试、续跑或取消分析。
5. §15.4 十三项固定顺序全部经已接受 09A/09B/09E 公共原语证明；显式清除真实演练只能发生在系统临时子目录，并分别证明预览、取消和确认。
6. 非临时根、临时根本身、路径逃逸和不安全合成 project id 均在写入前拒绝。
7. canonical manifest 对顺序、内容、摘要、identity、lineage 及单项结果篡改均拒绝重放。
8. G5 第 1 轮发现的旧 revision/失效目标问题已纠偏：事件消费绑定当前 revision、binding、
   source/output manifest 与目标存在性；同一 run 的另一 revision 冲突关闭；点击前重新核对当前目标。
9. 发布清单改为纳入 R1-R7 Python 运行包闭包，并从仅含发布 manifest 文件的隔离副本完整运行
   §15.4 十三项，禁止隐式回落到原工作台源码。

## 决定性证据

- G4 聚焦套件：`73 passed`。
- G2/R7 相邻套件：`210 passed, 3 non-failing warnings`。
- normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42`：9/9 同一 digest
  `aec859cf59e4d3bac812f45293dff6175f4117df1f7b985fffc9f8e28d659475`。
- 当前发布 manifest：157 文件，digest
  `33fa98a46b8b0306839fd8dc7b6e86e628b002c01e4903c756a6f2db273a3263`；
  其中 154 个 Python 源文件、1 个 JSON、1 个 Markdown、1 个 zsh，无 `__pycache__`。
- 09E 合同 SHA、09A 冻结版本、09B schema manifest digest 与当前权威记录一致；两个 migration fault point 在当前 `FAILURE_HOOK_POINTS` 可追溯。
- 额外新鲜 §15.4 运行总体 `passed`，条目 8/9 分别证明旧版本可打开与实际 rollback。
- 纠偏复核时医学写作目录当前观测指纹
  `ba4975e20315482607bee43693d5c775c415fc2547df2f1a403348f205e5a018`；本纠偏未在该目录写入产物，
  不把并行开发造成的历史指纹变化归因于医学监查。
- 8911/5174/8984 均保持停止。

## 独立审阅与治理状态

- governed execution：`mm_r8_gate4_synthetic_15_4_20260831`，三个声明 worker 输出齐全，execution audit 与 review gate 均通过。
- fresh-context conference：`mm_r8_gate4_acceptance_20260831`，路由 `Pi/cms-router/minimax-m3:xhigh`，session `01a05651-0ea0-7000-978b-dacc04056b18`，无 fallback。
- 原 G4 会商曾未发现 P0/P1，但 G5 fresh-context 第 1 轮随后发现两项 P1；原接受结论据此失效，
  详见 `reviews/medical_monitoring_r8_gate5_pre_real_independent_review_round1_20260831.md`。
- 当前源码与证据是纠偏候选，不得在同一独立审阅会话复核前恢复 G4/G5 接受声明。

## 非阻断改进项

- 统一扩展系统通知内部词的大小写防护模式。
- 后续 schema 升级时，显式管理通知事实的严格字段集合与向前兼容。
- 在 G5/G6 复核中保留单项 digest、清除演练中文留痕和更广反过拟合扫描作为可选加固，不改写 G4 通过语义。

## 下一安全动作

重建 G5 evidence manifest 后，交回同一 fresh-context 独立审阅会话复核两项 P1。只有复核明确
接受，才可恢复 G4 synthetic/offline 接受并写 G5 `PRE_REAL_INDEPENDENT_ACCEPTED`；此前 G6
保持关闭，不访问真实项目、不调用真实模型、不启动浏览器或服务。
