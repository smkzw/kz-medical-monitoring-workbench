# Codex Execution Review: mm_r7_slice07b_subject_flow_implementation_20260828

## Verdict

`ACCEPT_AFTER_CODEX_REMEDIATION_SYNTHETIC_LIMITED`

接受范围仅为 R7 Slice-07B 的合成数据纵切：项目/中心受试者阶段流向、同源明细、风险叠加、
筛选路由和 Patient Journey 跳转。不得外推为真实项目、医学正确性、R7 总体或商业使用验收。

## Boundary And Hermes Governance

未读取或运行五个真实项目，未修改医学写作子系统，未设计或测试安全功能，未启动 8911。
Hermes execution packet、runner stdout、route identity 与最终 audit 均保留；两个 429 worker
输出被明确降级为局部实现线索，未被当作完成声明。

## Worker Outputs

- `worker_01`：CodeBuddy 会话在已产生局部后端改动后命中 429，runner 报告只保留终端限流文本；
  其代码不能作为独立完成证据。
- `worker_02`：完成前端 adapter/route-state 及测试，runner 记录 57 次工具调用、1228.125 秒，
  输出完整且可复核。
- `worker_03`：CodeBuddy 会话在已产生局部页面/CSS/fixture 改动后命中 429，runner 报告只保留
  终端限流文本；其代码不能作为独立完成证据。

执行审计最终通过，表示三个声明节点均有可审计终态；它不把两个限流报告提升为独立验收。

## Manager Assessment

该包按冻结计划没有单独 manager 节点。Codex 负责合并和处置：对照 v0.2 与 v0.3 §9 统一
后端字段、前端 camelCase 映射、路由互斥与三态；发现并修复了页面首次接线时空 SVG、同列
终点重叠、空节点顺序误导、中心空主阶段覆盖终点、首屏密度和两行中文基线等问题。

## Codex Independent Verification

- Python：`tests/test_medical_monitoring_r5*.py` 加 synthetic fixture，最终 `69 passed`；此前更宽
  R5/R7 与 fixture 组合 `103 passed` 仍作为本切实现过程证据。
- 前端：49 个医学监查 `*.test.mjs` 文件全部通过，其中 adapter 68、route-state 55、
  Subject Flow render 99、R7 API 25、controller 82、render 61、projection 74。
- 构建：Vite `1968 modules transformed`，构建成功；只保留既有大于 500 kB bundle 提示。
- ego(lite)：项目与中心、等待与活动详情布局、1280×800 与 1920×800、空态与未提供态均
  无页面横向溢出；项目图为 7 节点/5 连线，中心图为 7 节点/2 连线；节点、连线、风险、
  明细展开和 Journey 跳转均实际操作。原生 `累计到达` select 的自动化操作结果不确定，
  因此该模式只由确定性 route/render 测试证明。
- 独立视觉会商 Round 1 的三个阻断项均已纠偏；同一 Grok Build 会话 Round 2 给出 `accept`。

## Cleanup Decision

保留冻结合同、runner 输出、会商报告和最终截图作为接受证据。移除 synthetic fixture 的
Python 字节码缓存和不再代表当前界面的早期截图；归档临时 Grok 会话。8978/5176 仅为本切
隔离验收服务，收口时停止；8911 始终不得启动。
