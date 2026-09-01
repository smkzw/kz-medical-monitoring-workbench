# R7 Slice-08C-3 Patient Journey 变化与详情抽屉接受记录

日期：2026-08-30  
决定：`ACCEPT_R7_SLICE_08C3_SYNTHETIC_OFFLINE`

## 已接受结果

- 保留唯一横向访视/实际日期轴；七类本轮变化以闭集 Lucide 图标、中文标签和五类语义色叠加在既有事件/风险节点，不新建第二条历史。
- continuity 行严格按项目结果、中心、受试者、spine 与时间窗筛选；event、risk anchor、risk instance 按冻结优先级绑定，未绑定行不制造虚拟日期。
- R7 product route 才启用变化标记和详情抽屉；legacy R5 保留原内联详情与现有数据/几何/路由。共享时间轴的左右方向键记录为有意的非破坏性可访问性增量。
- overlay/push 详情抽屉按冻结阈值选择；push 使用 420 px 检查列并保留至少 760 px Journey；九段内容顺序、缺值文案、等级和八域标签均为中文医学监查表达。
- 抽屉逐条切换精确维持 `row_ref`，不重取/卸载受试者工作区；risk 入口聚合该风险全部变化，event 入口只显示该事件变化。
- 直接风险/事件/视图点击清除旧本地行；直接事件点击清除陈旧 risk context；行切换替换/清空 event、risk anchor、risk instance、visit 四个选择键。
- continuity 加载或失败不阻塞既有 Journey；关闭只清除抽屉选择，保留项目/结果/中心/受试者/spine/轴窗/视图。

## 决定性证据

- 聚焦 R5/R7：23/23 test files passed；JourneyDrawerRender 671 checks。
- 全量医学监查前端：61/61 test files passed；项目/路径中性契约扫描 92 个生产文件。
- Vite production build passed：1981 modules transformed；仅既有 bundle-size advisory。
- 独立代码会商复用同一 `deepseek-v4-flash:max` session `089ae578-2a2e-464d-8386-d69de40d49a8`：Round 1 P2×2、Round 2 P2×1、Round 3 P0-P2=0 并 `ACCEPT`。
- 执行主路由 `glm-5.3-flash:max` 三项均因结构化 429 quota 终止，按声明链切到 `deepseek-v4-flash:max` 完成；无静默换模。执行 audit、会商 validate 与 review gate 均通过。
- 8911/5174 无监听；未启动服务、浏览器或真实项目。

## 医学写作保护

08C-3 产品写入限于 `frontend/src/features/medical-monitoring/r5/` 与 `r7/`。按任务开始时间 `2026-08-30 00:06:44 CST` 检查医学写作/写作参考前后端与测试保护面（250 个非缓存文件），无任务时段内新 mtime；未修改医学写作产品源码。既有 445 文件聚合属于前一切片口径，本记录不伪称已按无法从记录复原的旧聚合算法重新证明该 hash。

## 接受边界与下一阶段

本记录只接受 synthetic/offline 08C-3。以下尚未接受：真实 DOM 焦点循环/归还、body 滚动锁、实际 resize、1280 overlay、1440/1920 push、整页横向溢出、中文信息密度、动效/阴影/图标视觉质量、真实项目/模型医学质量、R7 总体、生产或商业化。

下一阶段为 08C-4 专项运行时与视觉验收：先冻结 ego(lite) 三视口任务合同和参考图对照方法，再启动隔离服务，按 1280/1440/1920 完成 overlay/push、键盘/焦点、无横溢、信息密度和专项美化 LOOP；必须将参考与产品同视口截图并列比较，不能以截图存在代替视觉接受。
